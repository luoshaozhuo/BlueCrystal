"""审计日志适配器。

实现 AuditSinkPort，将结构化审计事件持久化或转发。
外部依赖：数据库（SQLAlchemy）/ HTTP 客户端。
失败处理：失败不传播到调用方，记录 error 后继续。
"""

from __future__ import annotations

import json
import logging
import threading
import time
from typing import Any

import urllib.request
from urllib.error import URLError
from urllib.request import ProxyHandler, build_opener

from whale.ingest.domain.audit_event import IngestAuditEvent
from whale.ingest.ports.audit import IngestAuditSinkPort

logger = logging.getLogger(__name__)


class HttpIngestAuditSink(IngestAuditSinkPort):
    """将审计事件转发到外部 HTTP 端点。

    Args:
        endpoint_url: 目标 URL（POST）。
        timeout_seconds: HTTP 请求超时秒数。
        batch_size: 批量 flush 前最大事件数（默认 1，即立即发送）。
        retry_count: 失败重试次数（默认 0）。
        retry_backoff_seconds: 重试间隔基数秒数。
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
        """初始化 HTTP 审计 sink。Args: endpoint_url: 目标 HTTP 端点 URL。timeout_seconds: 请求超时秒数。batch_size: 批量大小。retry_count: 重试次数。retry_backoff_seconds: 重试退避基数秒数。"""
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
        """缓存并可选 flush 审计事件到外部端点。按 batch_size 决定立即发送或累积后批量发送。"""
        with self._lock:
            self._buffer.append(event)
            if len(self._buffer) >= self._batch_size:
                self._flush()

    def flush(self) -> None:
        """缓存并可选地 flush 审计事件到外部端点。根据 batch_size 决定立即发送或累积后批量发送。

Never raises on the caller: errors are recorded in last_error."""
        with self._lock:
            self._flush()

    def _flush(self) -> None:
        """将缓冲的审计事件发送到外部端点。

失败记录到 error_count 和 last_error，不传播异常。"""
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
        """将单个审计事件转换为安全的 JSON 可序列化字典。"""
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
