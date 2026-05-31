"""审计中间件。

拦截 HTTP 请求并构造审计事件（IngestAuditEventOrm），
通过 app.state.audit_sink 写入审计日志。
提供 build_audit_event 工具函数供路由 handler 复用。
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from whale.ingest.domain.audit_event import IngestAuditEvent


@dataclass(frozen=True, slots=True)
class AuditContext:
    """请求作用域的审计上下文。"""

    request_id: str
    trace_id: str
    actor: str | None
    client_ip: str | None
    node_id: str | None


class IngestAuditMiddleware(BaseHTTPMiddleware):
    """附加请求作用域的审计元数据，不产生副作用。"""

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        """分发请求到下游 ASGI 应用。"""
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
    """从当前请求构造结构化审计事件。"""

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
