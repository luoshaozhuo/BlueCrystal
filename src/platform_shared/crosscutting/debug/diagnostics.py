"""Debug snapshot models for external runner diagnostics."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True, slots=True)
class RunnerDiagnosticsSnapshot:
    """Captured diagnostics for one runner-facing failure."""

    observed_at: datetime
    component: str
    error_code: str
    stdout_tail: tuple[str, ...] = ()
    stderr_tail: tuple[str, ...] = ()
    attributes: dict[str, str] = field(default_factory=dict)
