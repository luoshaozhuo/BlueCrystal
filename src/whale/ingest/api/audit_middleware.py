"""Request audit context helpers and middleware."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from whale.ingest.domain.audit_event import IngestAuditEvent


@dataclass(frozen=True, slots=True)
class AuditContext:
    """Request-scoped audit context."""

    request_id: str
    trace_id: str
    actor: str | None
    client_ip: str | None
    node_id: str | None


class IngestAuditMiddleware(BaseHTTPMiddleware):
    """Attach request-scoped audit metadata without starting side effects."""

    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        request_id = request.headers.get("x-request-id") or str(uuid4())
        trace_id = request.headers.get("x-trace-id") or request_id
        actor = request.headers.get("x-actor")
        client = request.client.host if request.client is not None else None
        node_id = getattr(request.app.state, "node_id", None)
        request.state.audit_context = AuditContext(
            request_id=request_id,
            trace_id=trace_id,
            actor=actor,
            client_ip=client,
            node_id=node_id,
        )
        response = await call_next(request)
        response.headers["x-request-id"] = request_id
        return response


def build_audit_event(
    request: Request,
    *,
    action: str,
    resource_type: str,
    resource_id: str | None,
    decision: str,
    result: str,
    http_status: int | None,
    reason_code: str | None = None,
    before_version: int | None = None,
    after_version: int | None = None,
    changed_fields: list[str] | None = None,
    attributes: dict[str, object] | None = None,
) -> IngestAuditEvent:
    """Build one structured audit event from the current request."""

    context: AuditContext = request.state.audit_context
    return IngestAuditEvent(
        request_id=context.request_id,
        actor=context.actor,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        decision=decision,
        result=result,
        reason_code=reason_code,
        http_status=http_status,
        trace_id=context.trace_id,
        client_ip=context.client_ip,
        node_id=context.node_id,
        before_version=before_version,
        after_version=after_version,
        changed_fields=changed_fields or [],
        attributes=attributes or {},
    )
