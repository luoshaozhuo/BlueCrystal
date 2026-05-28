"""Audit-event query routes for ingest runtime API."""

from __future__ import annotations

from typing import Callable

from fastapi import APIRouter, Query, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from whale.ingest.api.audit_middleware import build_audit_event
from whale.ingest.api.errors import denied, not_found
from whale.ingest.api.schemas import AuditEventResponse, PaginatedResponse
from whale.shared.persistence.orm import IngestAuditEventOrm

router = APIRouter(prefix="/api/v1/audit-events", tags=["audit-events"])


def _open_session(factory):
    return factory() if callable(factory) else factory()


def _authorize(request, action, resource_id=None):
    if not request.app.state.access_evaluator(request, action, "audit_event", resource_id):
        raise denied(action=action, resource_type="audit_event", resource_id=resource_id)


def _response(row) -> AuditEventResponse:
    return AuditEventResponse(
        audit_id=row.audit_id,
        request_id=row.request_id,
        actor=row.actor,
        action=row.action,
        resource_type=row.resource_type,
        resource_id=row.resource_id,
        decision=row.decision,
        result=row.result,
        reason_code=row.reason_code,
        http_status=row.http_status,
        trace_id=row.trace_id,
        client_ip=row.client_ip,
        node_id=row.node_id,
        event_timestamp=str(row.event_timestamp),
    )


@router.get("/{audit_id}", response_model=AuditEventResponse)
def get_audit_event(audit_id: int, request: Request) -> AuditEventResponse:
    _authorize(request, "audit_event.read", str(audit_id))
    session = _open_session(request.app.state.session_factory)
    try:
        row = session.get(IngestAuditEventOrm, audit_id)
        if row is None:
            raise not_found(action="audit_event.read", resource_type="audit_event", resource_id=str(audit_id))
        request.app.state.audit_sink.emit(
            build_audit_event(request, action="audit_event.read", resource_type="audit_event", resource_id=str(audit_id), decision="ALLOW", result="SUCCESS", http_status=200)
        )
        return _response(row)
    finally:
        session.close()


@router.get("", response_model=PaginatedResponse[AuditEventResponse])
def list_audit_events(
    request: Request,
    action_filter: str | None = Query(None, alias="action"),
    resource_type: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> PaginatedResponse[AuditEventResponse]:
    _authorize(request, "audit_event.list")
    session = _open_session(request.app.state.session_factory)
    try:
        query = select(IngestAuditEventOrm).order_by(IngestAuditEventOrm.event_timestamp.desc())
        count_query = select(func.count()).select_from(IngestAuditEventOrm)
        if action_filter:
            query = query.where(IngestAuditEventOrm.action == action_filter)
            count_query = count_query.where(IngestAuditEventOrm.action == action_filter)
        if resource_type:
            query = query.where(IngestAuditEventOrm.resource_type == resource_type)
            count_query = count_query.where(IngestAuditEventOrm.resource_type == resource_type)
        total = session.scalar(count_query) or 0
        rows = list(session.scalars(query.limit(limit).offset(offset)))
        items = [_response(r) for r in rows]
        request.app.state.audit_sink.emit(
            build_audit_event(request, action="audit_event.list", resource_type="audit_event", resource_id=None, decision="ALLOW", result="SUCCESS", http_status=200, attributes={"count": len(items), "total": total})
        )
        return PaginatedResponse(items=items, total=total, limit=limit, offset=offset)
    finally:
        session.close()
