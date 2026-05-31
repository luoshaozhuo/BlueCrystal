"""幂等键支持模块。为 ingest 运行时 CRUD API 提供防重复请求的中间件和服务。"""

from __future__ import annotations

import hashlib
import json
from typing import Any, cast

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from whale.shared.persistence.orm.ingest_runtime import IngestIdempotencyRecord


def _fingerprint(method: str, path: str, query_string: bytes, body: bytes) -> str:
    h = hashlib.sha256()
    h.update(method.encode())
    h.update(path.encode())
    h.update(query_string)
    h.update(body)
    return h.hexdigest()


_MUTATING_METHODS = frozenset({"POST", "PATCH", "DELETE"})

_HEADER_KEY = b"idempotency-key"


def _get_idempotency_key(scope: Scope) -> str:
    """从原始 ASGI scope 读取 Idempotency-Key 头，不消费 receive 流。"""
    headers = scope.get("headers")
    if not isinstance(headers, list):
        return ""
    typed_headers = cast(list[tuple[bytes, bytes]], headers)
    for key, value in typed_headers:
        if key.lower() == _HEADER_KEY:
            return value.decode().strip()
    return ""


class IdempotencyService:
    """基于数据库的幂等键管理服务。使用唯一约束实现幂等键的原子声明和缓存。"""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        """初始化幂等服务。Args: session_factory: 数据库会话工厂。"""
        self._factory = session_factory

    def get_cached(self, key: str) -> IngestIdempotencyRecord | None:
        """查找已有的幂等记录。返回缓存的 HTTP 状态码、头和响应体，或 None 表示未命中。"""
        session: Session = self._factory()
        try:
            from sqlalchemy import select

            return session.scalar(
                select(IngestIdempotencyRecord).where(
                    IngestIdempotencyRecord.idempotency_key == key
                )
            )
        finally:
            session.close()

    def try_claim(self, key: str, fingerprint: str) -> bool:
        """原子性声明幂等键。使用数据库唯一约束确保同一键只被一个请求持有。"""
        session: Session = self._factory()
        try:
            record = IngestIdempotencyRecord(
                idempotency_key=key,
                request_fingerprint=fingerprint,
                response_status=0,
                response_body={},
            )
            session.add(record)
            session.commit()
            return True
        except IntegrityError:
            session.rollback()
            return False
        finally:
            session.close()

    def cache_response(self, key: str, status: int, body: dict[str, Any]) -> None:
        """为已声明的幂等键存储响应。缓存 HTTP 状态码、头部和 body 供后续重试使用。"""
        session: Session = self._factory()
        try:
            from sqlalchemy import select

            record = session.scalar(
                select(IngestIdempotencyRecord).where(
                    IngestIdempotencyRecord.idempotency_key == key
                )
            )
            if record is not None:
                record.response_status = status
                record.response_body = body
                session.commit()
        finally:
            session.close()


async def _read_and_buffer_body(receive: Receive) -> tuple[bytes, Receive]:
    """从 ASGI receive 读取完整请求体并缓存所有消息。确保中间件可重复访问请求体。"""
    messages: list[Message] = []
    body_parts: list[bytes] = []

    reading = True
    while reading:
        msg = await receive()
        messages.append(msg)
        if msg["type"] == "http.request":
            chunk = msg.get("body", b"")
            body_parts.append(chunk)
            if not msg.get("more_body", False):
                reading = False

    body = b"".join(body_parts)
    replay = list(messages)

    async def replay_receive() -> Message:
        if replay:
            return replay.pop(0)
        return await receive()

    return body, replay_receive


class IdempotencyMiddleware:
    """处理变更请求 Idempotency-Key 头的 ASGI 中间件。拦截携带幂等键的写请求并做去重处理。"""

    def __init__(self, app: ASGIApp) -> None:
        """初始化幂等中间件。Args: app: 下游 ASGI 应用。service: 幂等服务实例。"""
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """ASGI 中间件入口。拦截携带幂等键的变更请求并做去重处理。"""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        method = scope.get("method", "GET")
        if method not in _MUTATING_METHODS:
            await self.app(scope, receive, send)
            return

        idempotency_key = _get_idempotency_key(scope)
        if not idempotency_key:
            await self.app(scope, receive, send)
            return

        # Read body and get a replay receive function
        body, replay_receive = await _read_and_buffer_body(receive)
        fp = _fingerprint(method, scope.get("path", ""), scope.get("query_string", b""), body)

        # Access session_factory via app state — need to build a quick request
        from starlette.requests import Request
        req = Request(scope, receive=replay_receive)

        service = IdempotencyService(req.app.state.session_factory)

        # Check for existing record
        existing = service.get_cached(idempotency_key)
        if existing is not None:
            if existing.request_fingerprint != fp:
                response = JSONResponse(
                    status_code=422,
                    content={
                        "error": "IDEMPOTENCY_KEY_REUSE",
                        "message": "Idempotency key used with a different request payload.",
                    },
                )
                await response(scope, receive, send)
                return
            if existing.response_status > 0:
                response = JSONResponse(
                    status_code=existing.response_status,
                    content=existing.response_body,
                )
                await response(scope, receive, send)
                return
            # First request is still being processed
            response = JSONResponse(
                status_code=409,
                content={
                    "error": "CONFLICT",
                    "message": "Request with this idempotency key is still being processed.",
                },
            )
            await response(scope, receive, send)
            return

        # First use: atomically claim the key
        if not service.try_claim(idempotency_key, fp):
            response = JSONResponse(
                status_code=409,
                content={
                    "error": "CONFLICT",
                    "message": "Idempotency key already claimed by concurrent request.",
                },
            )
            await response(scope, receive, send)
            return

        # Capture response body via send wrapper
        captured_status = 200
        captured_body = b""

        async def send_wrapper(message: Message) -> None:
            nonlocal captured_status, captured_body
            if message["type"] == "http.response.start":
                captured_status = message["status"]
            elif message["type"] == "http.response.body":
                captured_body += message.get("body", b"")
            await send(message)

        await self.app(scope, replay_receive, send_wrapper)

        # Cache the response (skip 5xx so clients can retry)
        if captured_status < 500 and captured_body:
            try:
                resp_body: dict[str, Any] = json.loads(captured_body)
            except (ValueError, RuntimeError):
                resp_body = {}
            service.cache_response(idempotency_key, captured_status, resp_body)
