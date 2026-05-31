"""端口接口定义。

定义调用方契约和实现方责任，相关功能。
"""

from __future__ import annotations

from typing import Protocol

from whale.ingest.domain.audit_event import IngestAuditEvent


class IngestAuditSinkPort(Protocol):
    """持久化或转发一条 ingest 审计事件。"""

    def emit(self, event: IngestAuditEvent) -> None:
        """发送一条脱敏后的审计事件。"""
