"""管理 安全分区 资源的 API 路由。

每个 handler 在请求入口做权限检查（access_evaluator），
变更操作支持 dry_run 模式和乐观并发控制（expected_version），
所有操作通过 audit_sink 记录审计事件，
事务在 try/finally 中管理 Session 生命周期。

不负责：资源的业务逻辑编排（由 use case 层负责）。
"""

from __future__ import annotations

from collections.abc import Callable

from fastapi import APIRouter, Query, Request
from sqlalchemy import JSON, DateTime, Integer, String, func, select
from sqlalchemy.orm import Mapped, Session, mapped_column, sessionmaker

from whale.ingest.api.audit_middleware import build_audit_event
from whale.ingest.api.errors import conflict, denied, not_found
from whale.ingest.api.schemas import (
    PaginatedResponse,
    SecurityPartitionCreate,
    SecurityPartitionPatch,
    SecurityPartitionResponse,
)
from whale.shared.persistence import Base

router = APIRouter(prefix="/api/v1/security-partitions", tags=["security-partitions"])


class SecurityPartitionOrm(Base):
    """用于 CRUD 操作的轻量级安全分区模型。"""

    __tablename__ = "ingest_security_partition"
    __table_args__ = {"extend_existing": True}

    partition_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    partition_code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    partition_name: Mapped[str] = mapped_column(String(255), nullable=False)
    security_zone: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default="UNCLASSIFIED",
    )
    direction: Mapped[str] = mapped_column(String(32), nullable=False, default="READ_ONLY")
    description: Mapped[str | None] = mapped_column(String(512), nullable=True)
    rules_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    record_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[object] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


def _open_session(factory: sessionmaker[Session] | Callable[[], Session]) -> Session:
    return factory() if callable(factory) else factory()


def _authorize(request: Request, action: str, resource_id: str | None = None) -> None:
    if not request.app.state.access_evaluator(request, action, "security_partition", resource_id):
        raise denied(action=action, resource_type="security_partition", resource_id=resource_id)


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


def _response(row: SecurityPartitionOrm) -> SecurityPartitionResponse:
    return SecurityPartitionResponse(
        partition_id=row.partition_id,
        partition_code=row.partition_code,
        partition_name=row.partition_name,
        security_zone=row.security_zone,
        direction=row.direction,
        description=row.description,
        rules_json=dict(row.rules_json),
        version=row.record_version,
    )


@router.post("", response_model=SecurityPartitionResponse, status_code=201)
def create_security_partition(
    request: Request,
    
    payload: SecurityPartitionCreate,
    dry_run: bool = Query(False),
) -> SecurityPartitionResponse:
    """创建新security partition。dry_run 为 True 时返回预期结果不实际创建。权限检查、审计记录和乐观并发控制。"""
    _authorize(request, "security_partition.create")
    session = _open_session(request.app.state.session_factory)
    try:
        if dry_run:
            return SecurityPartitionResponse(
                partition_id=0,
                partition_code=payload.partition_code,
                partition_name=payload.partition_name,
                security_zone=payload.security_zone,
                direction=payload.direction,
                description=payload.description,
                rules_json=dict(payload.rules_json),
                version=1,
            )
        row = SecurityPartitionOrm(
            partition_code=payload.partition_code,
            partition_name=payload.partition_name,
            security_zone=payload.security_zone,
            direction=payload.direction,
            description=payload.description,
            rules_json=dict(payload.rules_json),
            record_version=1,
        )
        session.add(row)
        session.commit()
        session.refresh(row)
        _emit_success(request, action="security_partition.create", resource_type="security_partition", resource_id=row.partition_code, http_status=201)
        return _response(row)
    finally:
        session.close()


@router.get("/{partition_id}", response_model=SecurityPartitionResponse)
def get_security_partition(partition_id: int, request: Request) -> SecurityPartitionResponse:
    """获取指定的资源记录。"""
    _authorize(request, "security_partition.read", str(partition_id))
    session = _open_session(request.app.state.session_factory)
    try:
        row = session.get(SecurityPartitionOrm, partition_id)
        if row is None:
            raise not_found(action="security_partition.read", resource_type="security_partition", resource_id=str(partition_id))
        _emit_success(request, action="security_partition.read", resource_type="security_partition", resource_id=str(partition_id), http_status=200)
        return _response(row)
    finally:
        session.close()


@router.get("", response_model=PaginatedResponse[SecurityPartitionResponse])
def list_security_partitions(
    request: Request,
    
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> PaginatedResponse[SecurityPartitionResponse]:
    """获取安全分区的分页列表。支持按字段过滤和分页参数。权限检查后查询。"""
    _authorize(request, "security_partition.list")
    session = _open_session(request.app.state.session_factory)
    try:
        total = session.scalar(select(func.count()).select_from(SecurityPartitionOrm)) or 0
        rows = list(session.scalars(select(SecurityPartitionOrm).order_by(SecurityPartitionOrm.partition_id).limit(limit).offset(offset)))
        items = [_response(r) for r in rows]
        _emit_success(request, action="security_partition.list", resource_type="security_partition", resource_id=None, http_status=200, attributes={"count": len(items), "total": total})
        return PaginatedResponse(items=items, total=total, limit=limit, offset=offset)
    finally:
        session.close()


@router.patch("/{partition_id}", response_model=SecurityPartitionResponse)
def patch_security_partition(partition_id: int, request: Request, payload: SecurityPartitionPatch, dry_run: bool = Query(False)) -> SecurityPartitionResponse:
    """patch_security_partition 方法。"""
    
    _authorize(request, "security_partition.update", str(partition_id))
    session = _open_session(request.app.state.session_factory)
    try:
        """部分更新security partition。支持乐观并发控制（版本字段）。权限检查和审计记录。"""
        row = session.get(SecurityPartitionOrm, partition_id)
        if row is None:
            raise not_found(action="security_partition.update", resource_type="security_partition", resource_id=str(partition_id))
        if row.record_version != payload.expected_version:
            raise conflict(action="security_partition.update", resource_type="security_partition", resource_id=str(partition_id), message="Version conflict.")
        if dry_run:
            return _response(row)
        changed_fields: list[str] = []
        for field_name, value in payload.model_dump(exclude_none=True).items():
            if field_name == "expected_version":
                continue
            setattr(row, field_name, value)
            changed_fields.append(field_name)
        row.record_version += 1
        session.commit()
        session.refresh(row)
        _emit_success(request, action="security_partition.update", resource_type="security_partition", resource_id=str(partition_id), http_status=200, after_version=row.record_version, changed_fields=changed_fields)
        return _response(row)
    finally:
        session.close()


@router.delete("/{partition_id}", status_code=204)
def delete_security_partition(partition_id: int, request: Request, expected_version: int = Query(...), dry_run: bool = Query(False)) -> None:
    """delete_security_partition 方法。"""
    
    _authorize(request, "security_partition.delete", str(partition_id))
    session = _open_session(request.app.state.session_factory)
    try:
        """删除security partition。权限检查并记录审计事件。"""
        row = session.get(SecurityPartitionOrm, partition_id)
        if row is None:
            raise not_found(action="security_partition.delete", resource_type="security_partition", resource_id=str(partition_id))
        if row.record_version != expected_version:
            raise conflict(action="security_partition.delete", resource_type="security_partition", resource_id=str(partition_id), message="Version conflict.")
        if dry_run:
            return None
        session.delete(row)
        session.commit()
        _emit_success(request, action="security_partition.delete", resource_type="security_partition", resource_id=str(partition_id), http_status=204)
    finally:
        session.close()
