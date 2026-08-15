"""端口接口定义。

定义调用方契约和实现方责任，相关功能。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass(slots=True)
class SourceCommandAuditEvent:
    """SourceCommandUseCase 发出的一条结构化审计事件。"""

    request_id: str
    command_id: str | None
    trace_id: str | None
    actor: str | None
    protocol: str
    source_id: str | None
    target: str
    result: str
    failure_reason: str | None
    timestamp: datetime
    decision: str = "ALLOW"
    reason_code: str | None = None
    fencing_token: int | None = None


class SourceCommandAuditPort(Protocol):
    """结构化源命令审计事件的 sink。"""

    def emit(self, event: SourceCommandAuditEvent) -> None:
        """发送一条审计事件。"""
