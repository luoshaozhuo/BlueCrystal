"""FastAPI 审计路由适配。"""

from __future__ import annotations

from collections.abc import Callable, Coroutine
from typing import Any, cast

from fastapi import FastAPI, Request, Response
from fastapi.routing import APIRoute

from ..context import bind_observation_context
from .decorators import get_audit_spec
from .service import AuditService


ActorResolver = Callable[[Request], str | None]
RouteHandler = Callable[[Request], Coroutine[Any, Any, Response]]


def create_audit_route_class(
    audit: AuditService,
    *,
    actor_resolver: ActorResolver | None = None,
) -> type[APIRoute]:
    """创建带审计处理的 FastAPI 路由类。

    Args:
        audit: 审计服务。
        actor_resolver: 从请求解析操作主体的可选函数。

    Returns:
        包装后的 APIRoute 子类。
    """

    class AuditedRoute(APIRoute):
        """仅包装带 ``audit_action`` 声明的 FastAPI endpoint。"""

        def get_route_handler(self) -> RouteHandler:
            """返回保留原响应和异常语义的审计 route handler。"""
            original = super().get_route_handler()
            spec = get_audit_spec(self.endpoint)
            if spec is None:
                return cast(RouteHandler, original)

            async def handler(request: Request) -> Response:
                """从请求解析审计主体与目标，并记录成功或失败。"""
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
                    attributes={
                        "audit.operation": spec.operation,
                        "audit.target.type": spec.target_type,
                        "audit.target.id": target or "",
                    },
                ):
                    try:
                        response = cast(Response, await original(request))
                    except Exception as exc:
                        # 审计失败记录完成后必须重新抛出原业务异常。
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

    AuditedRoute.__name__ = "AuditedAPIRoute"
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
        actor_resolver=actor_resolver,
    )
