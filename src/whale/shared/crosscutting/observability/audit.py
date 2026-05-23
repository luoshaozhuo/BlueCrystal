"""Helpers that bridge audit concepts into observability pipelines."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class AuditLogEnvelope:
    """Lightweight log-facing representation of one audit emission."""

    event_name: str
    actor_id: str | None = None
    attributes: dict[str, str] = field(default_factory=dict)

