"""HTTP-based audit sink for forwarding events to an external audit platform / SIEM.

Non-blocking on the main business path: failures record last_error but don't
propagate exceptions to the caller.
"""

from __future__ import annotations

import json
import logging
import threading
import time
from collections.abc import Callable
from typing import Any

import urllib.request
from urllib.error import URLError
from urllib.request import ProxyHandler, build_opener

from whale.ingest.domain.audit_event import IngestAuditEvent
from whale.ingest.ports.audit import IngestAuditSinkPort

logger = logging.getLogger(__name__)


class HttpIngestAuditSink(IngestAuditSinkPort):
    """Forward audit events to an external HTTP endpoint.

    Args:
        endpoint_url: Target URL (POST).
        timeout_seconds: HTTP request timeout.
        batch_size: Max events per batch before flush (default 1 = immediate).
        retry_count: How many times to retry on failure (default 0).
        retry_backoff_seconds: Base backoff between retries.
    """

    def __init__(
        self,
        endpoint_url: str,
        *,
        timeout_seconds: float = 5.0,
        batch_size: int = 1,
        retry_count: int = 0,
        retry_backoff_seconds: float = 1.0,
    ) -> None:
        self._endpoint_url = endpoint_url.rstrip("/") + "/events"
        self._timeout = timeout_seconds
        self._opener = build_opener(ProxyHandler({}))
        self._batch_size = batch_size
        self._retry_count = retry_count
        self._retry_backoff = retry_backoff_seconds
        self._buffer: list[IngestAuditEvent] = []
        self._lock = threading.Lock()
        self.last_error: Exception | None = None

    def emit(self, event: IngestAuditEvent) -> None:
        """Buffer and optionally flush the event to the external endpoint.

        Never raises on the caller: errors are recorded in last_error.
        """
        with self._lock:
            self._buffer.append(event)
            if len(self._buffer) >= self._batch_size:
                self._flush()

    def flush(self) -> None:
        """Explicitly flush buffered events."""
        with self._lock:
            self._flush()

    def _flush(self) -> None:
        """Send buffered events to the external endpoint."""
        if not self._buffer:
            return

        batch = self._buffer[:]
        self._buffer.clear()

        payload = [self._serialize(event) for event in batch]
        body = json.dumps(payload).encode("utf-8")

        last_exc: Exception | None = None
        for attempt in range(1 + self._retry_count):
            try:
                req = urllib.request.Request(
                    self._endpoint_url,
                    data=body,
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with self._opener.open(req, timeout=self._timeout) as resp:
                    if resp.status < 300:
                        self.last_error = None
                        return
                    last_exc = OSError(f"HTTP {resp.status}")
            except (URLError, OSError, ValueError) as exc:
                last_exc = exc
                if attempt < self._retry_count:
                    time.sleep(self._retry_backoff * (2**attempt))
                continue

        # All retries exhausted
        self.last_error = last_exc
        logger.warning("External audit sink failed after %d retries: %s", self._retry_count, last_exc)

    @staticmethod
    def _serialize(event: IngestAuditEvent) -> dict[str, Any]:
        """Convert one audit event to a safe JSON-serializable dict."""
        payload = event.sanitized_payload()
        return {
            "request_id": payload["request_id"],
            "actor": payload["actor"],
            "action": payload["action"],
            "resource_type": payload["resource_type"],
            "resource_id": payload["resource_id"],
            "decision": payload["decision"],
            "result": payload["result"],
            "reason_code": payload["reason_code"],
            "http_status": payload["http_status"],
            "trace_id": payload["trace_id"],
            "client_ip": payload["client_ip"],
            "node_id": payload["node_id"],
            "timestamp": payload["timestamp"].isoformat() if hasattr(payload["timestamp"], "isoformat") else str(payload["timestamp"]),
            "attributes": dict(payload["attributes"]),
        }
