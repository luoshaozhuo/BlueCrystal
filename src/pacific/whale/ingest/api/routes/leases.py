"""管理 租约 资源的 API 路由。

每个 handler 在请求入口做权限检查（access_evaluator），
变更操作支持 dry_run 模式和乐观并发控制（expected_version），
所有操作通过 audit_sink 记录审计事件，
事务在 try/finally 中管理 Session 生命周期。

不负责：资源的业务逻辑编排（由 use case 层负责）。
"""

from __future__ import annotations

from collections.abc import Callable

from fastapi import APIRouter, Query, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from pacific.whale.ingest.api.audit_middleware import build_audit_event
from pacific.whale.ingest.api.errors import denied, not_found
from pacific.whale.ingest.api.schemas import LeaseResponse, PaginatedResponse
from pacific.whale.shared.persistence.orm import IngestJobLease

router = APIRouter(prefix="/api/v1/leases", tags=["leases"])


def _open_session(factory: sessionmaker[Session] | Callable[[], Session]) -> Session:
    return factory() if callable(factory) else factory()


def _authorize(request: Request, action: str, resource_id: str | None = None) -> None:
    if not request.app.state.access_evaluator(request, action, "lease", resource_id):
        raise denied(action=action, resource_type="lease", resource_id=resource_id)


def _response(row: IngestJobLease) -> LeaseResponse:
    return LeaseResponse(
        lease_id=row.lease_id,
        lease_name=row.lease_name,
        lease_scope=row.lease_scope,
        resource_id=row.resource_id,
        holder_key=row.holder_key,
        status=row.status,
        fencing_token=row.fencing_token,
        acquired_at=str(row.acquired_at),
        renewed_at=str(row.renewed_at),
        expires_at=str(row.expires_at),
        released_at=str(row.released_at) if row.released_at else None,
        version=row.version,
    )


@router.get("/{lease_id}", response_model=LeaseResponse)
def get_lease(lease_id: int, request: Request) -> LeaseResponse:
    """获取指定的资源记录。"""
    _authorize(request, "lease.read", str(lease_id))
    session = _open_session(request.app.state.session_factory)
    try:
        row = session.get(IngestJobLease, lease_id)
        if row is None:
            raise not_found(action="lease.read", resource_type="lease", resource_id=str(lease_id))
        request.app.state.audit_sink.emit(
            build_audit_event(request, action="lease.read", resource_type="lease", resource_id=str(lease_id), decision="ALLOW", result="SUCCESS", http_status=200)
        )
        return _response(row)
    finally:
        session.close()


@router.get("", response_model=PaginatedResponse[LeaseResponse])
def list_leases(
    request: Request,
    
    scope: str | None = Query(None),
    status: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> PaginatedResponse[LeaseResponse]:
    """获取租约的分页列表。支持按字段过滤和分页参数。权限检查后查询。"""
    _authorize(request, "lease.list")
    session = _open_session(request.app.state.session_factory)
    try:
        query = select(IngestJobLease).order_by(IngestJobLease.lease_id)
        count_query = select(func.count()).select_from(IngestJobLease)
        if scope:
            query = query.where(IngestJobLease.lease_scope == scope)
            count_query = count_query.where(IngestJobLease.lease_scope == scope)
        if status:
            query = query.where(IngestJobLease.status == status)
            count_query = count_query.where(IngestJobLease.status == status)
        total = session.scalar(count_query) or 0
        rows = list(session.scalars(query.limit(limit).offset(offset)))
        items = [_response(r) for r in rows]
        request.app.state.audit_sink.emit(
            build_audit_event(request, action="lease.list", resource_type="lease", resource_id=None, decision="ALLOW", result="SUCCESS", http_status=200, attributes={"count": len(items), "total": total})
        )
        return PaginatedResponse(items=items, total=total, limit=limit, offset=offset)
    finally:
        session.close()
