"""FastAPI 审计路由适配。"""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response
from fastapi.routing import APIRoute

from ..shared import bind_observation_context
from .decorators import get_audit_spec
from .service import AuditService


ActorResolver = Callable[[Request], str | None]
RouteHandler = Callable[[Request], Awaitable[Response]]


def create_audit_route_class(
    audit: AuditService,
    *,
    base_route_class: type[APIRoute] = APIRoute,
    actor_resolver: ActorResolver | None = None,
) -> type[APIRoute]:
    """创建带审计处理的 FastAPI 路由类。

    Args:
        audit: 审计服务。
        base_route_class: 需要包装的基础路由类。
        actor_resolver: 从请求解析操作主体的可选函数。

    Returns:
        包装后的 APIRoute 子类。
    """

    class AuditedRoute(base_route_class):
        def get_route_handler(self) -> RouteHandler:
            original = super().get_route_handler()
            spec = get_audit_spec(self.endpoint)
            if spec is None:
                return original

            async def handler(request: Request) -> Response:
                actor = actor_resolver(request) if actor_resolver else None
                target = None
                if spec.target_arg:
                    value = request.path_params.get(
                        spec.target_arg
                    ) or request.query_params.get(spec.target_arg)
                    target = None if value is None else str(value)

                detail = {
                    name: request.path_params.get(name)
                    or request.query_params.get(name)
                    for name in spec.detail_args
                }
                with bind_observation_context(
                    actor=actor,
                    source="http",
                    operation=spec.operation,
                    target_type=spec.target_type,
                    target_id=target,
                ):
                    try:
                        response = await original(request)
                    except Exception as exc:
                        audit.failure(
                            operation=spec.operation,
                            target_type=spec.target_type,
                            target_id=target,
                            detail=detail,
                            exception=exc,
                        )
                        raise

                    audit.success(
                        operation=spec.operation,
                        target_type=spec.target_type,
                        target_id=target,
                        detail=detail,
                    )
                    return response

            return handler

    AuditedRoute.__name__ = f"Audited{base_route_class.__name__}"
    return AuditedRoute


def install_audit_routes(
    app: FastAPI,
    audit: AuditService,
    *,
    actor_resolver: ActorResolver | None = None,
) -> None:
    """为 FastAPI 应用安装审计路由类。"""
    app.router.route_class = create_audit_route_class(
        audit,
        base_route_class=app.router.route_class,
        actor_resolver=actor_resolver,
    )
