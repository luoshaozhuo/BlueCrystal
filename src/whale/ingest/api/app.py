"""Ingest FastAPI 应用工厂。

创建并配置 ingest 的 FastAPI 应用实例，
注册中间件（审计、CORS、错误处理）、路由和依赖状态。
"""

from __future__ import annotations

from collections.abc import Callable
from inspect import signature
from typing import Protocol, cast

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.engine import Engine
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


class AccessEvaluator(Protocol):
    """四参数 access_evaluator 契约。"""

    def __call__(
        self,
        request: Request,
        action: str,
        resource_type: str,
        resource_id: str | None = None,
    ) -> bool: ...


class LegacyAccessEvaluator(Protocol):
    """兼容旧三参数 access_evaluator 契约。"""

    def __call__(
        self,
        request: Request,
        action: str,
        resource_id: str | None = None,
    ) -> bool: ...


AccessEvaluatorLike = AccessEvaluator | LegacyAccessEvaluator


def _build_readiness_probe(
    session_factory: sessionmaker[Session] | Callable[[], Session],
) -> Callable[[], bool]:
    """基于会话工厂构造默认 readiness 探针。"""

    if isinstance(session_factory, sessionmaker):
        bind = session_factory.kw.get("bind")
        if bind is None:
            raise RuntimeError("session_factory is missing a bound engine.")
        return lambda: probe_runtime_readiness(bind)

    def _probe() -> bool:
        session = session_factory()
        try:
            bind = session.get_bind()
            engine = bind if isinstance(bind, Engine) else bind.engine
            return probe_runtime_readiness(engine)
        finally:
            session.close()

    return _probe


def _wrap_access_evaluator(access_evaluator: AccessEvaluatorLike) -> AccessEvaluator:
    """兼容旧三参数与新四参数 access_evaluator。"""

    parameter_count = len(signature(access_evaluator).parameters)
    if parameter_count >= 4:
        evaluator = cast(AccessEvaluator, access_evaluator)
        return evaluator

    legacy_evaluator = cast(LegacyAccessEvaluator, access_evaluator)

    def _wrapped(
        request: Request,
        action: str,
        resource_type: str,
        resource_id: str | None = None,
    ) -> bool:
        _ = resource_type
        return legacy_evaluator(request, action, resource_id)

    return _wrapped


def create_app(
    *,
    session_factory: sessionmaker[Session] | Callable[[], Session],
    audit_sink: IngestAuditSinkPort | None = None,
    access_evaluator: AccessEvaluatorLike | None = None,
    access_policy: AccessPolicyPort | None = None,
    node_id: str = "api-node",
    readiness_probe: Callable[[], bool] | None = None,
) -> FastAPI:
    """创建 FastAPI 应用实例，不在导入时启动服务器。"""

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
            app.state.access_evaluator = _wrap_access_evaluator(access_evaluator)
        else:
            app.state.access_evaluator = (
                lambda request, action, resource_type, resource_id=None: True
            )
    app.state.node_id = node_id
    app.state.readiness_probe = readiness_probe or _build_readiness_probe(session_factory)
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
        """处理异常并返回标准 HTTP 错误响应。"""
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
        """处理 Pydantic 验证错误，返回 422 响应。"""
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
