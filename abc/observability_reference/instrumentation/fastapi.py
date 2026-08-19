"""FastAPI HTTP 统一 Context 与技术事实 Middleware."""

from __future__ import annotations

from collections.abc import Callable
from time import perf_counter

from fastapi import FastAPI, Request

from observability_reference.shared import bind_request_context, new_request_id

from .hooks import InstrumentationHooks, safe_observe


DEFAULT_REQUEST_ID_HEADER = "X-Request-ID"
MAX_REQUEST_ID_LENGTH = 128
ActorResolver = Callable[[Request], str | None]


def default_actor_resolver(
    request: Request,
    *,
    header_name: str = "X-Actor",
) -> str | None:
    """Reference 默认从 X-Actor 读取；生产环境应读取认证结果."""

    return request.headers.get(header_name)


def install_fastapi_instrumentation(
    app: FastAPI,
    hooks: InstrumentationHooks,
    *,
    request_id_header: str = DEFAULT_REQUEST_ID_HEADER,
    actor_resolver: ActorResolver | None = None,
    source: str = "http",
) -> None:
    """安装一个统一的 HTTP Observability Middleware.

    Middleware 只在入口绑定一次 request/method/path/actor/source。
    后续 Hook 不重复传递这些 Context 字段。
    """

    resolver = actor_resolver or default_actor_resolver

    @app.middleware("http")
    async def observability_middleware(request: Request, call_next):
        request_id = _request_id_from_header(
            request.headers.get(request_id_header)
        )

        with bind_request_context(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            actor=resolver(request),
            source=source,
        ):
            started_at = perf_counter()
            safe_observe(hooks.http_request_started)

            try:
                response = await call_next(request)
            except Exception as exc:
                safe_observe(
                    hooks.http_request_failed,
                    duration_seconds=perf_counter() - started_at,
                    exception=exc,
                )
                raise

            safe_observe(
                hooks.http_request_finished,
                status_code=response.status_code,
                duration_seconds=perf_counter() - started_at,
            )
            response.headers[request_id_header] = request_id
            return response


def _request_id_from_header(value: str | None) -> str:
    if value is None:
        return new_request_id()

    candidate = value.strip()
    if not candidate or len(candidate) > MAX_REQUEST_ID_LENGTH:
        return new_request_id()

    if not all(char.isalnum() or char in "-_.:" for char in candidate):
        return new_request_id()

    return candidate
