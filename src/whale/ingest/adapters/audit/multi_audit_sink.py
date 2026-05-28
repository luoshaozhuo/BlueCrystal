"""Composable ingest audit sinks."""

from __future__ import annotations

from whale.ingest.domain.audit_event import IngestAuditEvent
from whale.ingest.ports.audit import IngestAuditSinkPort


class AuditSinkEmitError(RuntimeError):
    """Aggregated audit sink failure that preserves partial-write visibility."""

    def __init__(self, *, primary_error: Exception | None, secondary_error: Exception | None) -> None:
        self.primary_error = primary_error
        self.secondary_error = secondary_error
        parts: list[str] = []
        if primary_error is not None:
            parts.append(f"primary={type(primary_error).__name__}")
        if secondary_error is not None:
            parts.append(f"secondary={type(secondary_error).__name__}")
        super().__init__("dual_audit_sink_emit_failed:" + ",".join(parts))


class DualIngestAuditSink(IngestAuditSinkPort):
    """Emit one audit event into two sinks for DB + JSONL dual write."""

    def __init__(self, primary: IngestAuditSinkPort, secondary: IngestAuditSinkPort) -> None:
        self._primary = primary
        self._secondary = secondary
        self.last_error: AuditSinkEmitError | None = None

    def emit(self, event: IngestAuditEvent) -> None:
        primary_error: Exception | None = None
        secondary_error: Exception | None = None
        self.last_error = None

        try:
            self._primary.emit(event)
        except Exception as exc:  # pragma: no cover - exercised by integration path
            primary_error = exc

        try:
            self._secondary.emit(event)
        except Exception as exc:  # pragma: no cover - exercised by integration path
            secondary_error = exc

        if primary_error is None and secondary_error is None:
            return

        self.last_error = AuditSinkEmitError(
            primary_error=primary_error,
            secondary_error=secondary_error,
        )
        if secondary_error is not None:
            raise self.last_error
