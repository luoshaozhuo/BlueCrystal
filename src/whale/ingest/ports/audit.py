"""Audit sink port for ingest runtime and API."""

from __future__ import annotations

from typing import Protocol

from whale.ingest.domain.audit_event import IngestAuditEvent


class IngestAuditSinkPort(Protocol):
    """Persist or forward one ingest audit event."""

    def emit(self, event: IngestAuditEvent) -> None:
        """Emit one redacted audit event."""
