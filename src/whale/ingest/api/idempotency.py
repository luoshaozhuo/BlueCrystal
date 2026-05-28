"""Idempotency key support for ingest runtime CRUD API."""

from __future__ import annotations

import hashlib
import json
from typing import Any

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
    """Read Idempotency-Key header from raw ASGI scope without consuming receive."""
    for key, value in scope.get("headers", []):
        if key.lower() == _HEADER_KEY:
            return value.decode().strip()
    return ""


class IdempotencyService:
    """DB-backed idempotency key management."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._factory = session_factory

    def get_cached(self, key: str) -> IngestIdempotencyRecord | None:
        """Look up an existing idempotency record."""
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
        """Atomically claim an idempotency key.

        Returns True if this is the first use (INSERT succeeded).
        Returns False if the key is already taken.
        """
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
        """Store the response for a previously claimed key."""
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
    """Read the full request body from receive while buffering all messages.

    Returns (body, replay_receive) where replay_receive replays all
    buffered messages before falling through to the original receive.
    """
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
    """ASGI middleware that handles Idempotency-Key header for mutating requests.

    - If the key is new: claims it, lets the request proceed, caches the response.
    - If the key exists with matching fingerprint: returns the cached response.
    - If the key exists with different fingerprint: returns 422.
    - 5xx responses are not cached, allowing safe retry.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
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
