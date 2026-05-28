"""FastAPI app factory for ingest runtime CRUD."""

from __future__ import annotations

from collections.abc import Callable

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session, sessionmaker

from whale.ingest.adapters.audit.db_audit_sink import DbIngestAuditSink
from whale.ingest.api.audit_middleware import IngestAuditMiddleware, build_audit_event
from whale.ingest.api.idempotency import IdempotencyMiddleware
from whale.ingest.api.errors import ApiError
from whale.ingest.api.routes import acquisition_tasks as acquisition_tasks_routes
from whale.ingest.api.routes import audit_events as audit_event_routes
from whale.ingest.api.routes import bundles as bundle_routes
from whale.ingest.api.routes import health as health_routes
from whale.ingest.api.routes import leases as lease_routes
from whale.ingest.api.routes import nodes as node_routes
from whale.ingest.api.routes import runtime_config as runtime_config_routes
from whale.ingest.api.routes import scheduler_jobs as scheduler_job_routes
from whale.ingest.api.routes import security_partitions as security_partition_routes
from whale.ingest.framework.persistence.runtime_db import probe_runtime_readiness
from whale.ingest.ports.audit import IngestAuditSinkPort
from whale.ingest.ports.runtime.access_policy_port import AccessPolicyPort


def create_app(
    *,
    session_factory: sessionmaker[Session] | Callable[[], Session],
    audit_sink: IngestAuditSinkPort | None = None,
    access_evaluator: Callable[[Request, str, str | None], bool] | None = None,
    access_policy: AccessPolicyPort | None = None,
    node_id: str = "api-node",
    readiness_probe: Callable[[], bool] | None = None,
) -> FastAPI:
    """Create one FastAPI app without starting a server at import time."""

    app = FastAPI(title="Whale Ingest Runtime API", version="0.1.0")
    app.state.session_factory = session_factory
    app.state.audit_sink = audit_sink or DbIngestAuditSink(session_factory)
    if access_policy is not None:
        app.state.access_evaluator = (
            lambda request, action, resource_type, resource_id=None: access_policy.authorize(
                request,
                action,
                resource_type,
                resource_id,
            )
        )
    else:
        if access_evaluator is not None:
            app.state.access_evaluator = (
                lambda request, action, resource_type, resource_id=None: access_evaluator(
                    request,
                    action,
                    resource_id,
                )
            )
        else:
            app.state.access_evaluator = (
                lambda request, action, resource_type, resource_id=None: True
            )
    app.state.node_id = node_id
    app.state.readiness_probe = readiness_probe or (lambda: probe_runtime_readiness(session_factory.kw["bind"]))  # type: ignore[attr-defined]
    app.add_middleware(IngestAuditMiddleware)
    app.add_middleware(IdempotencyMiddleware)
    app.include_router(health_routes.router)
    app.include_router(acquisition_tasks_routes.router)
    app.include_router(runtime_config_routes.router)
    app.include_router(scheduler_job_routes.router)
    app.include_router(security_partition_routes.router)
    app.include_router(bundle_routes.router)
    app.include_router(node_routes.router)
    app.include_router(lease_routes.router)
    app.include_router(audit_event_routes.router)

    @app.exception_handler(ApiError)
    async def handle_api_error(request: Request, exc: ApiError) -> JSONResponse:
        app.state.audit_sink.emit(
            build_audit_event(
                request,
                action=exc.action,
                resource_type=exc.resource_type,
                resource_id=exc.resource_id,
                decision=exc.decision,
                result=exc.result,
                http_status=exc.http_status,
                reason_code=exc.reason_code or exc.code,
                changed_fields=exc.changed_fields,
            )
        )
        return JSONResponse(status_code=exc.http_status, content=exc.to_payload())

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        app.state.audit_sink.emit(
            build_audit_event(
                request,
                action=f"{request.method.lower()} {request.url.path}",
                resource_type="request",
                resource_id=request.url.path,
                decision="DENY",
                result="VALIDATION_ERROR",
                http_status=422,
                reason_code="VALIDATION_ERROR",
                attributes={"errors": exc.errors()},
            )
        )
        return JSONResponse(
            status_code=422,
            content={"error": "VALIDATION_ERROR", "message": "Request validation failed."},
        )

    return app
