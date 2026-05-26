"""Ingest metrics port."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass(slots=True)
class IngestMetricEvent:
    operation: str
    source_id: str | None
    protocol: str | None
    duration_ms: float
    status: str
    error_code: str | None
    timestamp: datetime


class IngestMetricsPort(Protocol):
    def emit(self, event: IngestMetricEvent) -> None:
        """Emit one metrics event."""
