"""Bundle 元数据查询路由。

提供 Bundle 元数据（IngestBundleMetadata）的只读查询接口：
- 按 bundle_id 查询单个 bundle；
- 分页查询 bundle 列表；
- 每次查询通过 access_evaluator 做权限检查；
- 查询操作本身也通过 audit_sink 记录审计事件；
- 事务边界：每次请求在 try/finally 中管理 session 生命周期。

管理资源：bundle，路由前缀 /api/v1/bundles。
不负责：bundle 的导入/导出/签名/脱敏（由 bundle service 模块负责）。
"""

from __future__ import annotations

from collections.abc import Callable

from fastapi import APIRouter, Query, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from pacific.whale.ingest.api.audit_middleware import build_audit_event
from pacific.whale.ingest.api.errors import denied, not_found
from pacific.whale.ingest.api.schemas import BundleMetadataResponse, PaginatedResponse
from pacific.whale.shared.persistence.orm import IngestBundleMetadata

router = APIRouter(prefix="/api/v1/bundles", tags=["bundles"])


def _open_session(factory: sessionmaker[Session] | Callable[[], Session]) -> Session:
    return factory() if callable(factory) else factory()


def _authorize(request: Request, action: str, resource_id: str | None = None) -> None:
    if not request.app.state.access_evaluator(request, action, "bundle", resource_id):
        raise denied(action=action, resource_type="bundle", resource_id=resource_id)


def _response(row: IngestBundleMetadata) -> BundleMetadataResponse:
    return BundleMetadataResponse(
        bundle_id=row.bundle_id,
        bundle_version=row.bundle_version,
        schema_version=row.schema_version,
        checksum=row.checksum,
        signature_status=row.signature_status,
        source=row.source,
        redacted=row.redacted,
        status=row.status,
        created_at=str(row.created_at),
        imported_at=str(row.imported_at) if row.imported_at else None,
    )


@router.get("/{bundle_id}", response_model=BundleMetadataResponse)
def get_bundle(bundle_id: int, request: Request) -> BundleMetadataResponse:
    """获取指定的资源记录。"""
    _authorize(request, "bundle.read", str(bundle_id))
    session = _open_session(request.app.state.session_factory)
    try:
        row = session.get(IngestBundleMetadata, bundle_id)
        if row is None:
            raise not_found(action="bundle.read", resource_type="bundle", resource_id=str(bundle_id))
        request.app.state.audit_sink.emit(
            build_audit_event(request, action="bundle.read", resource_type="bundle", resource_id=str(bundle_id), decision="ALLOW", result="SUCCESS", http_status=200)
        )
        return _response(row)
    finally:
        session.close()


@router.get("", response_model=PaginatedResponse[BundleMetadataResponse])
def list_bundles(
    request: Request,
    
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> PaginatedResponse[BundleMetadataResponse]:
    """获取bundle的分页列表。支持按字段过滤和分页参数。权限检查后查询。"""
    _authorize(request, "bundle.list")
    session = _open_session(request.app.state.session_factory)
    try:
        total = session.scalar(select(func.count()).select_from(IngestBundleMetadata)) or 0
        rows = list(session.scalars(select(IngestBundleMetadata).order_by(IngestBundleMetadata.bundle_id.desc()).limit(limit).offset(offset)))
        items = [_response(r) for r in rows]
        request.app.state.audit_sink.emit(
            build_audit_event(request, action="bundle.list", resource_type="bundle", resource_id=None, decision="ALLOW", result="SUCCESS", http_status=200, attributes={"count": len(items), "total": total})
        )
        return PaginatedResponse(items=items, total=total, limit=limit, offset=offset)
    finally:
        session.close()
