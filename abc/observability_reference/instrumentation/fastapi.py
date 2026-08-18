"""FastAPI HTTP 请求的低侵入观测 Middleware."""

from __future__ import annotations

from time import perf_counter

from fastapi import FastAPI, Request

from abc.observability_reference.shared import bind_observation_context, new_request_id

from .hooks import InstrumentationHooks, safe_observe


DEFAULT_REQUEST_ID_HEADER = "X-Request-ID"
MAX_REQUEST_ID_LENGTH = 128


def install_fastapi_instrumentation(
    app: FastAPI,
    hooks: InstrumentationHooks,
    *,
    request_id_header: str = DEFAULT_REQUEST_ID_HEADER,
) -> None:
    """为 FastAPI 安装统一 Request Context 和 HTTP 观测 Middleware."""

    @app.middleware("http")
    async def observability_middleware(request: Request, call_next):
        method = request.method
        path = request.url.path
        request_id = _request_id_from_header(
            request.headers.get(request_id_header)
        )

        with bind_observation_context(request_id=request_id):
            started_at = perf_counter()
            safe_observe(
                hooks.http_request_started,
                method=method,
                path=path,
            )

            try:
                response = await call_next(request)
            except Exception as exc:
                duration = perf_counter() - started_at
                safe_observe(
                    hooks.http_request_failed,
                    method=method,
                    path=path,
                    duration_seconds=duration,
                    exception=exc,
                )
                raise

            duration = perf_counter() - started_at
            safe_observe(
                hooks.http_request_finished,
                method=method,
                path=path,
                status_code=response.status_code,
                duration_seconds=duration,
            )
            response.headers[request_id_header] = request_id
            return response


def _request_id_from_header(value: str | None) -> str:
    """接收安全的外部 request_id，否则生成新的 ID."""
    if value is None:
        return new_request_id()

    candidate = value.strip()
    if not candidate or len(candidate) > MAX_REQUEST_ID_LENGTH:
        return new_request_id()

    if not all(char.isalnum() or char in "-_.:" for char in candidate):
        return new_request_id()

    return candidate
