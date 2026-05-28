"""Structured audit port for source write/control commands."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass(slots=True)
class SourceCommandAuditEvent:
    """One structured audit event emitted by SourceCommandUseCase."""

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
    """Sink for structured source-command audit events."""

    def emit(self, event: SourceCommandAuditEvent) -> None:
        """Emit one audit event."""
