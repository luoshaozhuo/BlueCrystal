"""FastAPI 声明式 Audit 适配."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from fastapi import FastAPI, Request, Response
from fastapi.routing import APIRoute

from .context import bind_audit_context, get_audit_context
from .decorators import get_audit_spec
from .models import AuditResult, AuditSpec
from .service import AuditService


ActorResolver = Callable[[Request], str | None]


def default_actor_resolver(
    request: Request,
    *,
    header_name: str = "X-Actor",
) -> str | None:
    """默认从 HTTP Header 读取 actor.

    生产环境通常应替换为认证中间件已经解析出的用户身份。
    """

    return request.headers.get(header_name)


def install_fastapi_audit(
    app: FastAPI,
    audit: AuditService,
    *,
    actor_resolver: ActorResolver | None = None,
    source: str = "http",
) -> None:
    """在 FastAPI 上安装声明式 Audit.

    必须在注册需要 Audit 的 route 之前调用。

    安装后：
    1. Middleware 负责建立 ``AuditContext``；
    2. 自定义 ``APIRoute`` 负责读取 ``@audit_action`` 元数据；
    3. Route 正常返回 -> 自动记录 SUCCESS；
    4. Route 抛异常 -> 自动记录 FAILURE；
    5. 未声明 ``@audit_action`` 的 Route 不产生 Audit。
    """

    resolver = (
        actor_resolver
        if actor_resolver is not None
        else default_actor_resolver
    )

    route_class = _create_audited_route_class(
        audit
    )
    app.router.route_class = route_class

    @app.middleware("http")
    async def audit_context_middleware(
        request: Request,
        call_next,
    ) -> Response:
        actor = resolver(request)

        with bind_audit_context(
            actor=actor,
            source=source,
        ):
            return await call_next(request)


def _create_audited_route_class(
    audit: AuditService,
) -> type[APIRoute]:
    class AuditedAPIRoute(APIRoute):
        """自动执行声明式 Audit 的 Route."""

        def get_route_handler(self):
            original_handler = (
                super().get_route_handler()
            )
            spec = get_audit_spec(
                self.endpoint
            )

            if spec is None:
                return original_handler

            async def audited_handler(
                request: Request,
            ) -> Response:
                target_id = _resolve_target_id(
                    request,
                    spec,
                )
                detail = _resolve_detail(
                    request,
                    spec,
                )
                context = get_audit_context()

                try:
                    response = await original_handler(
                        request
                    )
                except BaseException as exc:
                    audit.record(
                        actor=context.actor,
                        source=context.source,
                        operation=spec.operation,
                        target_type=spec.target_type,
                        target_id=target_id,
                        result=AuditResult.FAILURE,
                        detail=detail,
                        exception=exc,
                    )
                    raise

                if response.status_code >= 400:
                    failure_detail = dict(detail)
                    failure_detail[
                        "status_code"
                    ] = response.status_code

                    audit.record(
                        actor=context.actor,
                        source=context.source,
                        operation=spec.operation,
                        target_type=spec.target_type,
                        target_id=target_id,
                        result=AuditResult.FAILURE,
                        detail=failure_detail,
                    )
                else:
                    success_detail = dict(detail)
                    success_detail[
                        "status_code"
                    ] = response.status_code

                    audit.record(
                        actor=context.actor,
                        source=context.source,
                        operation=spec.operation,
                        target_type=spec.target_type,
                        target_id=target_id,
                        result=AuditResult.SUCCESS,
                        detail=success_detail,
                    )

                return response

            return audited_handler

    AuditedAPIRoute.__name__ = (
        "AuditedAPIRoute"
    )
    return AuditedAPIRoute


def _resolve_target_id(
    request: Request,
    spec: AuditSpec,
) -> str | None:
    if spec.target_arg is None:
        return None

    value: Any = request.path_params.get(
        spec.target_arg
    )

    if value is None:
        value = request.query_params.get(
            spec.target_arg
        )

    if value is None:
        return None

    return str(value)


def _resolve_detail(
    request: Request,
    spec: AuditSpec,
) -> dict[str, object]:
    detail: dict[str, object] = {}

    for name in spec.detail_args:
        value: Any = request.path_params.get(
            name
        )

        if value is None:
            value = request.query_params.get(
                name
            )

        if value is not None:
            detail[name] = value

    return detail
