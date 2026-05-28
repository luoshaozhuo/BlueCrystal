"""Node query routes for ingest runtime API."""

from __future__ import annotations

from typing import Callable

from fastapi import APIRouter, Query, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from whale.ingest.api.audit_middleware import build_audit_event
from whale.ingest.api.errors import denied, not_found
from whale.ingest.api.schemas import NodeResponse, PaginatedResponse
from whale.shared.persistence.orm import IngestRuntimeNode

router = APIRouter(prefix="/api/v1/nodes", tags=["nodes"])


def _open_session(factory):
    return factory() if callable(factory) else factory()


def _authorize(request, action, resource_id=None):
    if not request.app.state.access_evaluator(request, action, "node", resource_id):
        raise denied(action=action, resource_type="node", resource_id=resource_id)


def _response(row) -> NodeResponse:
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
