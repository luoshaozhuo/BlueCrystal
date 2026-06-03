"""Debug trace context and sink abstractions."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True, slots=True)
class DebugTraceContext:
    """Optional debug-trace context propagated through wrappers."""

    enabled: bool = False
    trace_id: str | None = None
    attributes: dict[str, str] = field(default_factory=dict)


class DebugTraceSinkPort(Protocol):
    """Receive best-effort debug trace records."""

    def emit(self, event_name: str, context: DebugTraceContext, **payload: str) -> None:
        """Emit one debug trace event."""
