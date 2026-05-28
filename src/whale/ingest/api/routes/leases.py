"""Lease query routes for ingest runtime API."""

from __future__ import annotations

from typing import Callable

from fastapi import APIRouter, Query, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from whale.ingest.api.audit_middleware import build_audit_event
from whale.ingest.api.errors import denied, not_found
from whale.ingest.api.schemas import LeaseResponse, PaginatedResponse
from whale.shared.persistence.orm import IngestJobLease

router = APIRouter(prefix="/api/v1/leases", tags=["leases"])


def _open_session(factory):
    return factory() if callable(factory) else factory()


def _authorize(request, action, resource_id=None):
    if not request.app.state.access_evaluator(request, action, "lease", resource_id):
        raise denied(action=action, resource_type="lease", resource_id=resource_id)


def _response(row) -> LeaseResponse:
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
