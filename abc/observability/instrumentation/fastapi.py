"""FastAPI 第三方 instrumentation 的薄装配 adapter。

OTel 与 Prometheus HTTP 数据由成熟第三方库产生；本模块只补 request ID、
actor 和 correlation context，不重复实现 HTTP span、耗时或状态码指标。
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any, cast

from fastapi import FastAPI, Request, Response
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor as OTelFastAPIInstrumentor
from prometheus_fastapi_instrumentator import Instrumentator

from ..context import bind_request_context, new_request_id

if TYPE_CHECKING:
    from ..runtime import ObservabilityRuntime

ActorResolver = Callable[[Request], str | None]
CallNext = Callable[[Request], Awaitable[Response]]
DEFAULT_ACTOR_RESOLVER = "x-actor"


def x_actor_resolver(request: Request) -> str | None:
    """默认策略：从请求头 ``x-actor`` 读取演示主体。"""
    return request.headers.get("x-actor")


def x_user_or_actor_resolver(request: Request) -> str | None:
    """优先 ``x-user``，回退到 ``x-actor``。"""
    return request.headers.get("x-user") or request.headers.get("x-actor")


def x_forwarded_user_or_actor_resolver(request: Request) -> str | None:
    """优先可信转发用户标识，再回退 ``x-user`` 和 ``x-actor``。"""
    return (
        request.headers.get("x-forwarded-user")
        or request.headers.get("x-user")
        or request.headers.get("x-actor")
    )


BUILTIN_ACTOR_RESOLVERS: dict[str, ActorResolver] = {
    "x-actor": x_actor_resolver,
    "x-user-or-actor": x_user_or_actor_resolver,
    "x-forwarded-user-or-actor": x_forwarded_user_or_actor_resolver,
}


def resolve_actor_resolver(
    value: str | ActorResolver | None,
) -> ActorResolver:
    """把配置字符串解析为 actor resolver callable，默认行为使用 ``x-actor``。"""
    if callable(value):
        return value
    key = (value or DEFAULT_ACTOR_RESOLVER).strip().lower()
    try:
        return BUILTIN_ACTOR_RESOLVERS[key]
    except KeyError as exc:
        raise ValueError(f"unsupported actor resolver: {value!r}") from exc


class FastAPIInstrumentation:
    """组合 OTel FastAPI、Prometheus instrumentator 和关联中间件。"""

    name = "fastapi"

    def __init__(
        self,
        app: object,
        *,
        enabled: bool = True,
        excluded_urls: str = "health,metrics",
        expose_metrics: bool = True,
        metrics_endpoint: str = "/metrics",
        request_id_header: str = "x-request-id",
        actor_resolver: str = "x-actor",
        otel_options: dict[str, object] | None = None,
        metrics_options: dict[str, object] | None = None,
    ) -> None:
        """保存安装目标和透传参数，不在构造阶段修改应用。"""
        if not isinstance(app, FastAPI):
            raise TypeError("fastapi instrumentation target must be FastAPI")
        self._app = app
        self._enabled = enabled
        self._excluded_urls = excluded_urls
        self._expose_metrics = expose_metrics
        self._metrics_endpoint = metrics_endpoint
        self._request_id_header = request_id_header
        self._actor_resolver = resolve_actor_resolver(actor_resolver)
        self._otel_options = dict(otel_options or {})
        self._metrics_options = dict(metrics_options or {})
        self._prometheus_instrumentator: Instrumentator | None = None
        self._otel_installed = False
        self._installed = False
        self._owned_routes: list[object] = []
        self._owned_middleware: list[object] = []

    def install(self, runtime: ObservabilityRuntime) -> None:
        """按已启用 backend 安装第三方 instrumentation 和薄上下文层。"""
        if self._installed or not self._enabled:
            return
        controlled_otel = {"tracer_provider", "excluded_urls"}
        conflict = controlled_otel.intersection(self._otel_options)
        if conflict:
            raise ValueError(
                "instrumentation.fastapi.options.otel_options conflicts with: "
                + ", ".join(sorted(conflict))
            )
        controlled_metrics = {"registry"}
        conflict = controlled_metrics.intersection(self._metrics_options)
        if conflict:
            raise ValueError(
                "instrumentation.fastapi.options.metrics_options conflicts with: "
                + ", ".join(sorted(conflict))
            )

        existing_routes = {id(route) for route in self._app.routes}
        existing_middleware = {id(item) for item in self._app.user_middleware}

        try:
            @self._app.middleware("http")
            async def correlation_middleware(
                request: Request, call_next: CallNext
            ) -> Response:
                """填充http请求关联字段"""
                request_id = request.headers.get(self._request_id_header) or new_request_id()
                correlation_id = request.headers.get("x-correlation-id") or request_id
                actor = self._actor_resolver(request)
                with bind_request_context(
                    request_id=request_id,
                    correlation_id=correlation_id,
                    actor=actor,
                ):
                    response = await call_next(request)
                response.headers[self._request_id_header] = request_id
                return response

            if runtime.metrics is not None:
                self._prometheus_instrumentator = Instrumentator(
                    registry=runtime.metrics.registry,
                    **self._metrics_options,
                ).instrument(self._app)
                if self._expose_metrics:
                    self._prometheus_instrumentator.expose(
                        self._app,
                        endpoint=self._metrics_endpoint,
                        include_in_schema=False,
                    )

            if runtime.tracing is not None:
                OTelFastAPIInstrumentor.instrument_app(
                    self._app,
                    tracer_provider=runtime.tracing.tracer_provider if runtime.tracing else None,
                    excluded_urls=self._excluded_urls,
                    **self._otel_options,
                )
            self._installed = True
        finally:
            # 即使第三方安装中途失败，也记录本 adapter 已产生的对象供回滚。
            self._owned_routes = [
                route for route in self._app.routes if id(route) not in existing_routes
            ]
            self._owned_middleware = [
                item
                for item in self._app.user_middleware
                if id(item) not in existing_middleware
            ]

    def uninstall(self) -> None:
        """卸载 OTel，并按对象身份移除本 adapter 创建的 route/middleware。"""
        if self._otel_installed:
            OTelFastAPIInstrumentor.uninstrument_app(self._app)
            self._otel_installed = False
        owned_route_ids = {id(route) for route in self._owned_routes}
        owned_middleware_ids = {id(item) for item in self._owned_middleware}
        self._app.router.routes[:] = [
            route for route in self._app.router.routes if id(route) not in owned_route_ids
        ]
        self._app.user_middleware[:] = [
            item
            for item in self._app.user_middleware
            if id(item) not in owned_middleware_ids
        ]
        self._app.middleware_stack = None
        self._owned_routes.clear()
        self._owned_middleware.clear()
        self._installed = False

    def start(self) -> None:
        """FastAPI adapter 无独立运行期资源，结构已在应用启动前安装。"""

    def stop(self) -> None:
        """FastAPI adapter 无独立运行期资源。"""
