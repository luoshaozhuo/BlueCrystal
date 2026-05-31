"""管理 运行时配置 资源的 API 路由。

每个 handler 在请求入口做权限检查（access_evaluator），
变更操作支持 dry_run 模式和乐观并发控制（expected_version），
所有操作通过 audit_sink 记录审计事件，
事务在 try/finally 中管理 Session 生命周期。

不负责：资源的业务逻辑编排（由 use case 层负责）。
"""

from __future__ import annotations

from typing import TypeVar, cast

from fastapi import APIRouter, Query, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.sql import Select

from whale.ingest.api.audit_middleware import build_audit_event
from whale.ingest.api.errors import conflict, denied, not_found
from whale.ingest.api.schemas import (
    ConnectionCreate,
    ConnectionPatch,
    ConnectionResponse,
    PaginatedResponse,
    PointCreate,
    PointPatch,
    PointResponse,
    SignalProfileCreate,
    SignalProfilePatch,
    SignalProfileResponse,
    SourceCreate,
    SourcePatch,
    SourceResponse,
)
from whale.shared.persistence.orm import (
    AssetInstance,
    AssetType,
    CommunicationEndpoint,
    IED,
    ScadaDataType,
    SignalProfile,
    SignalProfileItem,
)

router = APIRouter(prefix="/api/v1", tags=["runtime-config"])

TRuntimeConfigOrm = TypeVar(
    "TRuntimeConfigOrm",
    IED,
    CommunicationEndpoint,
    SignalProfile,
    SignalProfileItem,
)


def _open_session(factory: sessionmaker[Session]) -> Session:
    return factory() if callable(factory) else factory()


def _authorize(request: Request, action: str, resource_type: str, resource_id: str | None = None) -> None:
    if not request.app.state.access_evaluator(request, action, resource_type, resource_id):
        raise denied(action=action, resource_type=resource_type, resource_id=resource_id)


def _emit_success(
    request: Request,
    *,
    action: str,
    resource_type: str,
    resource_id: str | None,
    http_status: int,
    before_version: int | None = None,
    after_version: int | None = None,
    changed_fields: list[str] | None = None,
    attributes: dict[str, object] | None = None,
) -> None:
    request.app.state.audit_sink.emit(
        build_audit_event(
            request,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            decision="ALLOW",
            result="SUCCESS",
            http_status=http_status,
            before_version=before_version,
            after_version=after_version,
            changed_fields=changed_fields,
            attributes=attributes,
        )
    )


def _paginate(
    session: Session,
    stmt: Select[tuple[TRuntimeConfigOrm]],
    model: type[TRuntimeConfigOrm],
    *,
    limit: int,
    offset: int,
) -> tuple[int, list[TRuntimeConfigOrm]]:
    total = session.scalar(select(func.count()).select_from(model)) or 0
    rows = list(session.scalars(stmt.limit(limit).offset(offset)))
    return total, cast(list[TRuntimeConfigOrm], rows)


def _ensure_source_asset(session: Session, *, asset_code: str, asset_name: str) -> AssetInstance:
    asset = session.execute(select(AssetInstance).where(AssetInstance.asset_code == asset_code)).scalar_one_or_none()
    if asset is not None:
        asset.asset_name = asset_name
        return asset

    asset_type = session.execute(select(AssetType).where(AssetType.type_code == "INGEST_SOURCE")).scalar_one_or_none()
    if asset_type is None:
        asset_type = AssetType(type_code="INGEST_SOURCE", type_name="Ingest Source")
        session.add(asset_type)
        session.flush()

    asset = AssetInstance(asset_code=asset_code, asset_name=asset_name, asset_type_id=asset_type.asset_type_id)
    session.add(asset)
    session.flush()
    return asset


def _ensure_data_type(session: Session, type_name: str) -> ScadaDataType:
    row = session.execute(select(ScadaDataType).where(ScadaDataType.type_name == type_name)).scalar_one_or_none()
    if row is not None:
        return row
    row = ScadaDataType(type_name=type_name)
    session.add(row)
    session.flush()
    return row


def _source_response(row: IED, asset: AssetInstance | None) -> SourceResponse:
    return SourceResponse(
        source_id=row.ied_id,
        ied_name=row.ied_name,
        asset_instance_id=row.asset_instance_id,
        asset_code=asset.asset_code if asset else "",
        asset_name=asset.asset_name if asset else "",
        ied_type=row.ied_type,
        standard_family=row.standard_family,
        version=row.record_version,
    )


def _connection_response(row: CommunicationEndpoint) -> ConnectionResponse:
    return ConnectionResponse(
        connection_id=row.endpoint_id,
        source_id=row.ied_id,
        access_point_name=row.access_point_name,
        application_protocol=row.application_protocol,
        transport=row.transport,
        service_type=row.service_type,
        host=row.host,
        port=row.port,
        namespace_uri=row.namespace_uri,
        endpoint_name=row.endpoint_name,
        credential_ref=row.credential_ref,
        service_capabilities_json=dict(row.service_capabilities_json),
        metadata_json=dict(row.metadata_json),
        version=row.record_version,
    )


def _signal_profile_response(row: SignalProfile) -> SignalProfileResponse:
    return SignalProfileResponse(
        signal_profile_id=row.signal_profile_id,
        profile_code=row.profile_code,
        profile_name=row.profile_name,
        standard_family=row.standard_family,
        vendor=row.vendor,
        version_label=row.version,
        description=row.description,
        metadata_json=dict(row.metadata_json),
        version=row.record_version,
    )


def _point_response(row: SignalProfileItem, data_type: ScadaDataType | None) -> PointResponse:
    return PointResponse(
        point_id=row.profile_item_id,
        signal_profile_id=row.signal_profile_id,
        relative_path=row.relative_path,
        do_name=row.do_name,
        data_type_name=data_type.type_name if data_type else "",
        ln_class=row.ln_class,
        ln_name=row.ln_name,
        da_name=row.da_name,
        fc=row.fc,
        cdc=row.cdc,
        default_unit=row.default_unit,
        writable=row.writable,
        display_name=row.display_name,
        description=row.description,
        version=row.record_version,
    )


@router.post("/sources", response_model=SourceResponse, status_code=201)
def create_source(
    request: Request,
    
    payload: SourceCreate,
    dry_run: bool = Query(False),
) -> SourceResponse:
    """创建新数据源。dry_run 为 True 时返回预期结果不实际创建。权限检查、审计记录和乐观并发控制。"""
    _authorize(request, "source.create", "source")
    session = _open_session(request.app.state.session_factory)
    try:
        if session.execute(select(IED).where(IED.ied_name == payload.ied_name)).scalar_one_or_none() is not None:
            raise conflict(action="source.create", resource_type="source", resource_id=payload.ied_name, message="Source already exists.")
        if dry_run:
            return SourceResponse(
                source_id=0,
                ied_name=payload.ied_name,
                asset_instance_id=0,
                asset_code=payload.asset_code,
                asset_name=payload.asset_name,
                ied_type=payload.ied_type,
                standard_family=payload.standard_family,
                version=1,
            )
        asset = _ensure_source_asset(session, asset_code=payload.asset_code, asset_name=payload.asset_name)
        row = IED(
            asset_instance_id=asset.asset_instance_id,
            ied_name=payload.ied_name,
            ied_type=payload.ied_type,
            standard_family=payload.standard_family,
            metadata_json=dict(payload.metadata_json),
            record_version=1,
        )
        session.add(row)
        session.commit()
        session.refresh(row)
        _emit_success(request, action="source.create", resource_type="source", resource_id=str(row.ied_id), http_status=201, after_version=row.record_version, changed_fields=list(payload.model_dump().keys()))
        return _source_response(row, asset)
    finally:
        session.close()


@router.get("/sources/{source_id}", response_model=SourceResponse)
def get_source(source_id: int, request: Request) -> SourceResponse:
    """获取指定的资源记录。"""
    _authorize(request, "source.read", "source", str(source_id))
    session = _open_session(request.app.state.session_factory)
    try:
        row = session.get(IED, source_id)
        if row is None:
            raise not_found(action="source.read", resource_type="source", resource_id=str(source_id))
        asset = session.get(AssetInstance, row.asset_instance_id)
        _emit_success(request, action="source.read", resource_type="source", resource_id=str(source_id), http_status=200, after_version=row.record_version)
        return _source_response(row, asset)
    finally:
        session.close()


@router.get("/sources", response_model=PaginatedResponse[SourceResponse])
def list_sources(request: Request, limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0)) -> PaginatedResponse[SourceResponse]:
    """list_sources 方法。"""
    
    _authorize(request, "source.list", "source")
    session = _open_session(request.app.state.session_factory)
    try:
        """获取数据源的分页列表。支持按字段过滤和分页参数。权限检查后查询。"""
        total, rows = _paginate(session, select(IED).order_by(IED.ied_id), IED, limit=limit, offset=offset)
        items = [_source_response(row, session.get(AssetInstance, row.asset_instance_id)) for row in rows]
        _emit_success(request, action="source.list", resource_type="source", resource_id=None, http_status=200, attributes={"count": len(items), "total": total, "limit": limit, "offset": offset})
        return PaginatedResponse(items=items, total=total, limit=limit, offset=offset)
    finally:
        session.close()


@router.patch("/sources/{source_id}", response_model=SourceResponse)
def patch_source(source_id: int, request: Request, payload: SourcePatch, dry_run: bool = Query(False)) -> SourceResponse:
    """patch_source 方法。"""
    
    _authorize(request, "source.update", "source", str(source_id))
    session = _open_session(request.app.state.session_factory)
    try:
        """部分更新数据源。支持乐观并发控制（版本字段）。权限检查和审计记录。"""
        row = session.get(IED, source_id)
        if row is None:
            raise not_found(action="source.update", resource_type="source", resource_id=str(source_id))
        if row.record_version != payload.expected_version:
            raise conflict(action="source.update", resource_type="source", resource_id=str(source_id), message="Source version conflict.", changed_fields=list(payload.model_dump(exclude_none=True).keys()))
        if dry_run:
            asset = session.get(AssetInstance, row.asset_instance_id)
            return _source_response(row, asset)
        asset = session.get(AssetInstance, row.asset_instance_id)
        changed_fields: list[str] = []
        for field_name, value in payload.model_dump(exclude_none=True).items():
            if field_name == "expected_version":
                continue
            if field_name == "asset_name" and asset is not None:
                asset.asset_name = value
            else:
                setattr(row, field_name, value)
            changed_fields.append(field_name)
        before_version = row.record_version
        row.record_version += 1
        session.commit()
        session.refresh(row)
        _emit_success(request, action="source.update", resource_type="source", resource_id=str(source_id), http_status=200, before_version=before_version, after_version=row.record_version, changed_fields=changed_fields)
        return _source_response(row, asset)
    finally:
        session.close()


@router.delete("/sources/{source_id}", status_code=204)
def delete_source(source_id: int, request: Request, expected_version: int = Query(...), dry_run: bool = Query(False)) -> None:
    """delete_source 方法。"""
    
    _authorize(request, "source.delete", "source", str(source_id))
    session = _open_session(request.app.state.session_factory)
    try:
        """删除数据源。权限检查并记录审计事件。"""
        row = session.get(IED, source_id)
        if row is None:
            raise not_found(action="source.delete", resource_type="source", resource_id=str(source_id))
        if row.record_version != expected_version:
            raise conflict(action="source.delete", resource_type="source", resource_id=str(source_id), message="Source version conflict.")
        if dry_run:
            return None
        before_version = row.record_version
        session.delete(row)
        session.commit()
        _emit_success(request, action="source.delete", resource_type="source", resource_id=str(source_id), http_status=204, before_version=before_version)
    finally:
        session.close()


@router.post("/connections", response_model=ConnectionResponse, status_code=201)
def create_connection(
    request: Request,
    
    payload: ConnectionCreate,
    dry_run: bool = Query(False),
) -> ConnectionResponse:
    """创建新连接配置。dry_run 为 True 时返回预期结果不实际创建。权限检查、审计记录和乐观并发控制。"""
    _authorize(request, "connection.create", "connection")
    session = _open_session(request.app.state.session_factory)
    try:
        if session.get(IED, payload.source_id) is None:
            raise not_found(action="connection.create", resource_type="source", resource_id=str(payload.source_id))
        if dry_run:
            return ConnectionResponse(
                connection_id=0,
                source_id=payload.source_id,
                access_point_name=payload.access_point_name,
                application_protocol=payload.application_protocol,
                transport=payload.transport,
                service_type=payload.service_type,
                host=payload.host,
                port=payload.port,
                namespace_uri=payload.namespace_uri,
                endpoint_name=payload.endpoint_name,
                credential_ref=payload.credential_ref,
                service_capabilities_json=dict(payload.service_capabilities_json),
                metadata_json=dict(payload.metadata_json),
                version=1,
            )
        row = CommunicationEndpoint(
            ied_id=payload.source_id,
            access_point_name=payload.access_point_name,
            endpoint_name=payload.endpoint_name,
            application_protocol=payload.application_protocol,
            service_type=payload.service_type,
            transport=payload.transport,
            host=payload.host,
            port=payload.port,
            namespace_uri=payload.namespace_uri,
            credential_ref=payload.credential_ref,
            service_capabilities_json=dict(payload.service_capabilities_json),
            metadata_json=dict(payload.metadata_json),
            record_version=1,
        )
        session.add(row)
        session.commit()
        session.refresh(row)
        _emit_success(request, action="connection.create", resource_type="connection", resource_id=str(row.endpoint_id), http_status=201, after_version=row.record_version, changed_fields=list(payload.model_dump().keys()))
        return _connection_response(row)
    finally:
        
        session.close()


@router.get("/connections/{connection_id}", response_model=ConnectionResponse)
def get_connection(connection_id: int, request: Request) -> ConnectionResponse:
    """get_connection 方法。"""
    _authorize(request, "connection.read", "connection", str(connection_id))
    session = _open_session(request.app.state.session_factory)
    try:
        """获取指定的连接配置记录。权限检查并记录审计事件。"""
        row = session.get(CommunicationEndpoint, connection_id)
        if row is None:
            raise not_found(action="connection.read", resource_type="connection", resource_id=str(connection_id))
        _emit_success(request, action="connection.read", resource_type="connection", resource_id=str(connection_id), http_status=200, after_version=row.record_version)
        return _connection_response(row)
    finally:
        
        session.close()


@router.get("/connections", response_model=PaginatedResponse[ConnectionResponse])
def list_connections(request: Request, limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0)) -> PaginatedResponse[ConnectionResponse]:
    """list_connections 方法。"""
    _authorize(request, "connection.list", "connection")
    session = _open_session(request.app.state.session_factory)
    try:
        """获取连接配置的分页列表。支持按字段过滤和分页参数。权限检查后查询。"""
        total, rows = _paginate(session, select(CommunicationEndpoint).order_by(CommunicationEndpoint.endpoint_id), CommunicationEndpoint, limit=limit, offset=offset)
        items = [_connection_response(row) for row in rows]
        _emit_success(request, action="connection.list", resource_type="connection", resource_id=None, http_status=200, attributes={"count": len(items), "total": total, "limit": limit, "offset": offset})
        
        return PaginatedResponse(items=items, total=total, limit=limit, offset=offset)
    finally:
        session.close()


@router.patch("/connections/{connection_id}", response_model=ConnectionResponse)
def patch_connection(connection_id: int, request: Request, payload: ConnectionPatch, dry_run: bool = Query(False)) -> ConnectionResponse:
    """patch_connection 方法。"""
    _authorize(request, "connection.update", "connection", str(connection_id))
    session = _open_session(request.app.state.session_factory)
    try:
        """部分更新连接配置。支持乐观并发控制（版本字段）。权限检查和审计记录。"""
        row = session.get(CommunicationEndpoint, connection_id)
        if row is None:
            raise not_found(action="connection.update", resource_type="connection", resource_id=str(connection_id))
        if row.record_version != payload.expected_version:
            raise conflict(action="connection.update", resource_type="connection", resource_id=str(connection_id), message="Connection version conflict.", changed_fields=list(payload.model_dump(exclude_none=True).keys()))
        if dry_run:
            return _connection_response(row)
        changed_fields: list[str] = []
        for field_name, value in payload.model_dump(exclude_none=True).items():
            if field_name == "expected_version":
                continue
            setattr(row, field_name, value)
            changed_fields.append(field_name)
        before_version = row.record_version
        row.record_version += 1
        session.commit()
        session.refresh(row)
        _emit_success(request, action="connection.update", resource_type="connection", resource_id=str(connection_id), http_status=200, before_version=before_version, after_version=row.record_version, changed_fields=changed_fields)
        return _connection_response(row)
    finally:
        
        session.close()


@router.delete("/connections/{connection_id}", status_code=204)
def delete_connection(connection_id: int, request: Request, expected_version: int = Query(...), dry_run: bool = Query(False)) -> None:
    """delete_connection 方法。"""
    _authorize(request, "connection.delete", "connection", str(connection_id))
    session = _open_session(request.app.state.session_factory)
    try:
        """删除连接配置。权限检查并记录审计事件。"""
        row = session.get(CommunicationEndpoint, connection_id)
        if row is None:
            raise not_found(action="connection.delete", resource_type="connection", resource_id=str(connection_id))
        if row.record_version != expected_version:
            raise conflict(action="connection.delete", resource_type="connection", resource_id=str(connection_id), message="Connection version conflict.")
        if dry_run:
            return None
        before_version = row.record_version
        session.delete(row)
        session.commit()
        _emit_success(request, action="connection.delete", resource_type="connection", resource_id=str(connection_id), http_status=204, before_version=before_version)
    finally:
        
        session.close()


@router.post("/signal-profiles", response_model=SignalProfileResponse, status_code=201)
def create_signal_profile(
    request: Request,
    payload: SignalProfileCreate,
    dry_run: bool = Query(False),
) -> SignalProfileResponse:
    """创建新信号模板。dry_run 为 True 时返回预期结果不实际创建。权限检查、审计记录和乐观并发控制。"""
    _authorize(request, "signal_profile.create", "signal_profile")
    session = _open_session(request.app.state.session_factory)
    try:
        if dry_run:
            return SignalProfileResponse(
                signal_profile_id=0,
                profile_code=payload.profile_code,
                profile_name=payload.profile_name,
                standard_family=payload.standard_family,
                vendor=payload.vendor,
                version_label=payload.version_label,
                description=payload.description,
                metadata_json=dict(payload.metadata_json),
                version=1,
            )
        row = SignalProfile(
            profile_code=payload.profile_code,
            profile_name=payload.profile_name,
            standard_family=payload.standard_family,
            vendor=payload.vendor,
            version=payload.version_label,
            description=payload.description,
            metadata_json=dict(payload.metadata_json),
            record_version=1,
        )
        session.add(row)
        session.commit()
        session.refresh(row)
        _emit_success(request, action="signal_profile.create", resource_type="signal_profile", resource_id=str(row.signal_profile_id), http_status=201, after_version=row.record_version, changed_fields=list(payload.model_dump().keys()))
        return _signal_profile_response(row)
    finally:
        
        session.close()


@router.get("/signal-profiles/{signal_profile_id}", response_model=SignalProfileResponse)
def get_signal_profile(signal_profile_id: int, request: Request) -> SignalProfileResponse:
    """get_signal_profile 方法。"""
    _authorize(request, "signal_profile.read", "signal_profile", str(signal_profile_id))
    session = _open_session(request.app.state.session_factory)
    try:
        """获取指定的信号模板记录。权限检查并记录审计事件。"""
        
        row = session.get(SignalProfile, signal_profile_id)
        if row is None:
            raise not_found(action="signal_profile.read", resource_type="signal_profile", resource_id=str(signal_profile_id))
        _emit_success(request, action="signal_profile.read", resource_type="signal_profile", resource_id=str(signal_profile_id), http_status=200, after_version=row.record_version)
        return _signal_profile_response(row)
    finally:
        session.close()


@router.get("/signal-profiles", response_model=PaginatedResponse[SignalProfileResponse])
def list_signal_profiles(request: Request, limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0)) -> PaginatedResponse[SignalProfileResponse]:
    """list_signal_profiles 方法。"""
    _authorize(request, "signal_profile.list", "signal_profile")
    session = _open_session(request.app.state.session_factory)
    try:
        """获取信号模板的分页列表。支持按字段过滤和分页参数。权限检查后查询。"""
        
        total, rows = _paginate(session, select(SignalProfile).order_by(SignalProfile.signal_profile_id), SignalProfile, limit=limit, offset=offset)
        items = [_signal_profile_response(row) for row in rows]
        _emit_success(request, action="signal_profile.list", resource_type="signal_profile", resource_id=None, http_status=200, attributes={"count": len(items), "total": total, "limit": limit, "offset": offset})
        return PaginatedResponse(items=items, total=total, limit=limit, offset=offset)
    finally:
        session.close()


@router.patch("/signal-profiles/{signal_profile_id}", response_model=SignalProfileResponse)
def patch_signal_profile(signal_profile_id: int, request: Request, payload: SignalProfilePatch, dry_run: bool = Query(False)) -> SignalProfileResponse:
    """patch_signal_profile 方法。"""
    _authorize(request, "signal_profile.update", "signal_profile", str(signal_profile_id))
    session = _open_session(request.app.state.session_factory)
    try:
        """部分更新信号模板。支持乐观并发控制（版本字段）。权限检查和审计记录。"""
        row = session.get(SignalProfile, signal_profile_id)
        if row is None:
            raise not_found(action="signal_profile.update", resource_type="signal_profile", resource_id=str(signal_profile_id))
        if row.record_version != payload.expected_version:
            raise conflict(action="signal_profile.update", resource_type="signal_profile", resource_id=str(signal_profile_id), message="Signal profile version conflict.", changed_fields=list(payload.model_dump(exclude_none=True).keys()))
        if dry_run:
            return _signal_profile_response(row)
        changed_fields: list[str] = []
        for field_name, value in payload.model_dump(exclude_none=True).items():
            if field_name == "expected_version":
                continue
            if field_name == "version_label":
                row.version = value
            else:
                setattr(row, field_name, value)
            changed_fields.append(field_name)
        before_version = row.record_version
        row.record_version += 1
        session.commit()
        session.refresh(row)
        _emit_success(request, action="signal_profile.update", resource_type="signal_profile", resource_id=str(signal_profile_id), http_status=200, before_version=before_version, after_version=row.record_version, changed_fields=changed_fields)
        return _signal_profile_response(row)
    finally:
        
        session.close()


@router.delete("/signal-profiles/{signal_profile_id}", status_code=204)
def delete_signal_profile(signal_profile_id: int, request: Request, expected_version: int = Query(...), dry_run: bool = Query(False)) -> None:
    """delete_signal_profile 方法。"""
    _authorize(request, "signal_profile.delete", "signal_profile", str(signal_profile_id))
    session = _open_session(request.app.state.session_factory)
    try:
        """删除信号模板。权限检查并记录审计事件。"""
        row = session.get(SignalProfile, signal_profile_id)
        if row is None:
            raise not_found(action="signal_profile.delete", resource_type="signal_profile", resource_id=str(signal_profile_id))
        if row.record_version != expected_version:
            
            raise conflict(action="signal_profile.delete", resource_type="signal_profile", resource_id=str(signal_profile_id), message="Signal profile version conflict.")
        if dry_run:
            return None
        before_version = row.record_version
        session.delete(row)
        session.commit()
        _emit_success(request, action="signal_profile.delete", resource_type="signal_profile", resource_id=str(signal_profile_id), http_status=204, before_version=before_version)
    finally:
        session.close()


@router.post("/points", response_model=PointResponse, status_code=201)
def create_point(
    request: Request,
    payload: PointCreate,
    dry_run: bool = Query(False),
) -> PointResponse:
    """创建新采集点。dry_run 为 True 时返回预期结果不实际创建。权限检查、审计记录和乐观并发控制。"""
    _authorize(request, "point.create", "point")
    session = _open_session(request.app.state.session_factory)
    try:
        if session.get(SignalProfile, payload.signal_profile_id) is None:
            raise not_found(action="point.create", resource_type="signal_profile", resource_id=str(payload.signal_profile_id))
        if dry_run:
            return PointResponse(
                point_id=0,
                signal_profile_id=payload.signal_profile_id,
                relative_path=payload.relative_path,
                do_name=payload.do_name,
                data_type_name=payload.data_type_name,
                ln_class=payload.ln_class,
                ln_name=payload.ln_name,
                da_name=payload.da_name,
                fc=payload.fc,
                cdc=payload.cdc,
                default_unit=payload.default_unit,
                writable=payload.writable,
                display_name=payload.display_name,
                description=payload.description,
                version=1,
            )
        data_type = _ensure_data_type(session, payload.data_type_name)
        row = SignalProfileItem(
            signal_profile_id=payload.signal_profile_id,
            relative_path=payload.relative_path,
            do_name=payload.do_name,
            data_type_id=data_type.data_type_id,
            ln_class=payload.ln_class,
            ln_name=payload.ln_name,
            da_name=payload.da_name,
            fc=payload.fc,
            cdc=payload.cdc,
            default_unit=payload.default_unit,
            writable=payload.writable,
            display_name=payload.display_name,
            description=payload.description,
            record_version=1,
        )
        session.add(row)
        session.commit()
        session.refresh(row)
        _emit_success(request, action="point.create", resource_type="point", resource_id=str(row.profile_item_id), http_status=201, after_version=row.record_version, changed_fields=list(payload.model_dump().keys()))
        return _point_response(row, data_type)
    finally:
        
        session.close()


@router.get("/points/{point_id}", response_model=PointResponse)
def get_point(point_id: int, request: Request) -> PointResponse:
    """get_point 方法。"""
    
    _authorize(request, "point.read", "point", str(point_id))
    session = _open_session(request.app.state.session_factory)
    try:
        """获取指定的采集点记录。权限检查并记录审计事件。"""
        row = session.get(SignalProfileItem, point_id)
        if row is None:
            raise not_found(action="point.read", resource_type="point", resource_id=str(point_id))
        data_type = session.get(ScadaDataType, row.data_type_id)
        _emit_success(request, action="point.read", resource_type="point", resource_id=str(point_id), http_status=200, after_version=row.record_version)
        return _point_response(row, data_type)
    finally:
        session.close()


@router.get("/points", response_model=PaginatedResponse[PointResponse])
def list_points(request: Request, limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0)) -> PaginatedResponse[PointResponse]:
    """list_points 方法。"""
    
    _authorize(request, "point.list", "point")
    session = _open_session(request.app.state.session_factory)
    try:
        """获取采集点的分页列表。支持按字段过滤和分页参数。权限检查后查询。"""
        total, rows = _paginate(session, select(SignalProfileItem).order_by(SignalProfileItem.profile_item_id), SignalProfileItem, limit=limit, offset=offset)
        items = [_point_response(row, session.get(ScadaDataType, row.data_type_id)) for row in rows]
        _emit_success(request, action="point.list", resource_type="point", resource_id=None, http_status=200, attributes={"count": len(items), "total": total, "limit": limit, "offset": offset})
        return PaginatedResponse(items=items, total=total, limit=limit, offset=offset)
    finally:
        session.close()


@router.patch("/points/{point_id}", response_model=PointResponse)
def patch_point(point_id: int, request: Request, payload: PointPatch, dry_run: bool = Query(False)) -> PointResponse:
    """patch_point 方法。"""
    _authorize(request, "point.update", "point", str(point_id))
    session = _open_session(request.app.state.session_factory)
    try:
        """部分更新采集点。支持乐观并发控制（版本字段）。权限检查和审计记录。"""
        row = session.get(SignalProfileItem, point_id)
        if row is None:
            raise not_found(action="point.update", resource_type="point", resource_id=str(point_id))
        if row.record_version != payload.expected_version:
            raise conflict(action="point.update", resource_type="point", resource_id=str(point_id), message="Point version conflict.", changed_fields=list(payload.model_dump(exclude_none=True).keys()))
        if dry_run:
            data_type = session.get(ScadaDataType, row.data_type_id)
            return _point_response(row, data_type)
        changed_fields: list[str] = []
        for field_name, value in payload.model_dump(exclude_none=True).items():
            if field_name == "expected_version":
                continue
            if field_name == "data_type_name":
                
                data_type = _ensure_data_type(session, value)
                row.data_type_id = data_type.data_type_id
            else:
                setattr(row, field_name, value)
            changed_fields.append(field_name)
        before_version = row.record_version
        row.record_version += 1
        session.commit()
        session.refresh(row)
        data_type = session.get(ScadaDataType, row.data_type_id)
        _emit_success(request, action="point.update", resource_type="point", resource_id=str(point_id), http_status=200, before_version=before_version, after_version=row.record_version, changed_fields=changed_fields)
        return _point_response(row, data_type)
    finally:
        session.close()


@router.delete("/points/{point_id}", status_code=204)
def delete_point(point_id: int, request: Request, expected_version: int = Query(...), dry_run: bool = Query(False)) -> None:
    """delete_point 方法。"""
    _authorize(request, "point.delete", "point", str(point_id))
    session = _open_session(request.app.state.session_factory)
    try:
        """删除采集点。权限检查并记录审计事件。"""
        row = session.get(SignalProfileItem, point_id)
        if row is None:
            raise not_found(action="point.delete", resource_type="point", resource_id=str(point_id))
        if row.record_version != expected_version:
            raise conflict(action="point.delete", resource_type="point", resource_id=str(point_id), message="Point version conflict.")
        if dry_run:
            return None
        before_version = row.record_version
        session.delete(row)
        session.commit()
        _emit_success(request, action="point.delete", resource_type="point", resource_id=str(point_id), http_status=204, before_version=before_version)
    finally:
        session.close()
