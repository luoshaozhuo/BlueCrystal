"""管理 节点 资源的 API 路由。

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

from whale.ingest.api.audit_middleware import build_audit_event
from whale.ingest.api.errors import denied, not_found
from whale.ingest.api.schemas import NodeResponse, PaginatedResponse
from whale.shared.persistence.orm import IngestRuntimeNode

router = APIRouter(prefix="/api/v1/nodes", tags=["nodes"])


def _open_session(factory: sessionmaker[Session] | Callable[[], Session]) -> Session:
    return factory() if callable(factory) else factory()


def _authorize(request: Request, action: str, resource_id: str | None = None) -> None:
    if not request.app.state.access_evaluator(request, action, "node", resource_id):
        raise denied(action=action, resource_type="node", resource_id=resource_id)


def _response(row: IngestRuntimeNode) -> NodeResponse:
    return NodeResponse(
        node_key=row.node_key,
        runtime_mode=row.runtime_mode,
        status=row.status,
        hostname=row.hostname,
        heartbeat_at=str(row.heartbeat_at),
        last_seen_at=str(row.last_seen_at),
        created_at=str(row.created_at),
        updated_at=str(row.updated_at),
    )


@router.get("/{node_key}", response_model=NodeResponse)
def get_node(node_key: str, request: Request) -> NodeResponse:
    """获取指定的资源记录。"""
    _authorize(request, "node.read", node_key)
    session = _open_session(request.app.state.session_factory)
    try:
        row = session.get(IngestRuntimeNode, node_key)
        if row is None:
            raise not_found(action="node.read", resource_type="node", resource_id=node_key)
        request.app.state.audit_sink.emit(
            build_audit_event(request, action="node.read", resource_type="node", resource_id=node_key, decision="ALLOW", result="SUCCESS", http_status=200)
        )
        return _response(row)
    finally:
        session.close()


@router.get("", response_model=PaginatedResponse[NodeResponse])
def list_nodes(
    request: Request,
    
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> PaginatedResponse[NodeResponse]:
    """获取节点的分页列表。支持按字段过滤和分页参数。权限检查后查询。"""
    _authorize(request, "node.list")
    session = _open_session(request.app.state.session_factory)
    try:
        total = session.scalar(select(func.count()).select_from(IngestRuntimeNode)) or 0
        rows = list(session.scalars(select(IngestRuntimeNode).order_by(IngestRuntimeNode.node_key).limit(limit).offset(offset)))
        items = [_response(r) for r in rows]
        request.app.state.audit_sink.emit(
            build_audit_event(request, action="node.list", resource_type="node", resource_id=None, decision="ALLOW", result="SUCCESS", http_status=200, attributes={"count": len(items), "total": total})
        )
        return PaginatedResponse(items=items, total=total, limit=limit, offset=offset)
    finally:
        session.close()
