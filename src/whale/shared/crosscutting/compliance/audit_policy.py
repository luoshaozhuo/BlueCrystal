"""Audit event models and sinks."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol

from whale.shared.crosscutting.compliance.data_classification import DataClassification


@dataclass(frozen=True, slots=True)
class AuditEvent:
    """One audit-grade operational event."""

    event_name: str
    observed_at: datetime
    classification: DataClassification
    actor_id: str | None = None
    resource_id: str | None = None
    outcome: str = "success"
    attributes: dict[str, str] = field(default_factory=dict)


class AuditEventSinkPort(Protocol):
    """Consume audit events without binding callers to one backend."""

    def emit(self, event: AuditEvent) -> None:
        """Persist or forward one audit event."""

