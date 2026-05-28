"""Decorator objects for SourceStateCachePort crosscutting concerns."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from datetime import datetime

from whale.ingest.ports.state.source_state_cache_port import SourceStateCachePort
from whale.ingest.usecases.dtos.acquired_node_state import AcquiredNodeStateBatch
from whale.shared.crosscutting.compliance import AuditEvent, AuditEventSinkPort, DataClassification
from whale.shared.crosscutting.debug import DebugTraceContext, DebugTraceSinkPort
from whale.shared.crosscutting.observability import MetricsSinkPort

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class LoggingStateCachePort(SourceStateCachePort):
    """Emit logs around state-cache writes."""

    inner: SourceStateCachePort
    logger: logging.Logger = LOGGER

    def update(self, *, ld_name: str, batch: AcquiredNodeStateBatch) -> int:
        started_at = time.monotonic()
        try:
            updated = self.inner.update(ld_name=ld_name, batch=batch)
            self.logger.info(
                "state cache update succeeded",
                extra={
                    "ld_name": ld_name,
                    "value_count": len(batch.values),
                    "updated_count": updated,
                    "duration_seconds": time.monotonic() - started_at,
                },
            )
            return updated
        except Exception as exc:
            self.logger.warning(
                "state cache update failed",
                extra={"ld_name": ld_name, "error": str(exc)},
            )
            raise

    def mark_alive(self, *, ld_name: str, observed_at: datetime) -> None:
        self.inner.mark_alive(ld_name=ld_name, observed_at=observed_at)

    def mark_unavailable(
        self,
        *,
        ld_name: str,
        status: str,
        observed_at: datetime,
        reason: str | None = None,
    ) -> None:
        self.inner.mark_unavailable(
            ld_name=ld_name,
            status=status,
            observed_at=observed_at,
            reason=reason,
        )


@dataclass(frozen=True, slots=True)
class AuditedStateCachePort(SourceStateCachePort):
    """Emit audit events for state-cache writes."""

    inner: SourceStateCachePort
    audit_sink: AuditEventSinkPort

    def update(self, *, ld_name: str, batch: AcquiredNodeStateBatch) -> int:
        try:
            updated = self.inner.update(ld_name=ld_name, batch=batch)
        except Exception as exc:
            _emit_audit_best_effort(
                audit_sink=self.audit_sink,
                event=AuditEvent(
                    event_name="state_cache.update",
                    observed_at=batch.client_processed_at,
                    classification=DataClassification.INTERNAL,
                    resource_id=ld_name,
                    outcome="failure",
                    attributes={"error": type(exc).__name__},
                ),
                logger=LOGGER,
                operation="state_cache.update",
                resource_id=ld_name,
            )
            raise
        _emit_audit_best_effort(
            audit_sink=self.audit_sink,
            event=AuditEvent(
                event_name="state_cache.update",
                observed_at=batch.client_processed_at,
                classification=DataClassification.INTERNAL,
                resource_id=ld_name,
                attributes={"updated_count": str(updated)},
            ),
            logger=LOGGER,
            operation="state_cache.update",
            resource_id=ld_name,
        )
        return updated

    def mark_alive(self, *, ld_name: str, observed_at: datetime) -> None:
        self.inner.mark_alive(ld_name=ld_name, observed_at=observed_at)

    def mark_unavailable(
        self,
        *,
        ld_name: str,
        status: str,
        observed_at: datetime,
        reason: str | None = None,
    ) -> None:
        self.inner.mark_unavailable(
            ld_name=ld_name,
            status=status,
            observed_at=observed_at,
            reason=reason,
        )
        _emit_audit_best_effort(
            audit_sink=self.audit_sink,
            event=AuditEvent(
                event_name="state_cache.mark_unavailable",
                observed_at=observed_at,
                classification=DataClassification.INTERNAL,
                resource_id=ld_name,
                outcome="failure",
                attributes={"status": status, "reason": reason or ""},
            ),
            logger=LOGGER,
            operation="state_cache.mark_unavailable",
            resource_id=ld_name,
        )


@dataclass(frozen=True, slots=True)
class MetricsStateCachePort(SourceStateCachePort):
    """Record counters and latency for cache write operations."""

    inner: SourceStateCachePort
    metrics_sink: MetricsSinkPort

    def update(self, *, ld_name: str, batch: AcquiredNodeStateBatch) -> int:
        started_at = time.monotonic()
        try:
            updated = self.inner.update(ld_name=ld_name, batch=batch)
            self.metrics_sink.increment("ingest_state_cache_update_total", ld_name=ld_name)
            self.metrics_sink.observe_duration(
                "ingest_state_cache_update_duration_seconds",
                time.monotonic() - started_at,
                ld_name=ld_name,
            )
            return updated
        except Exception:
            self.metrics_sink.increment(
                "ingest_state_cache_update_failed_total",
                ld_name=ld_name,
            )
            raise

    def mark_alive(self, *, ld_name: str, observed_at: datetime) -> None:
        self.inner.mark_alive(ld_name=ld_name, observed_at=observed_at)

    def mark_unavailable(
        self,
        *,
        ld_name: str,
        status: str,
        observed_at: datetime,
        reason: str | None = None,
    ) -> None:
        self.inner.mark_unavailable(
            ld_name=ld_name,
            status=status,
            observed_at=observed_at,
            reason=reason,
        )
        self.metrics_sink.increment(
            "ingest_state_cache_unavailable_total",
            ld_name=ld_name,
            status=status,
            reason=reason or "",
        )


@dataclass(frozen=True, slots=True)
class DebugStateCachePort(SourceStateCachePort):
    """Emit best-effort debug trace events for cache operations."""

    inner: SourceStateCachePort
    trace_context: DebugTraceContext
    trace_sink: DebugTraceSinkPort

    def update(self, *, ld_name: str, batch: AcquiredNodeStateBatch) -> int:
        updated = self.inner.update(ld_name=ld_name, batch=batch)
        if self.trace_context.enabled:
            self.trace_sink.emit(
                "state_cache.update",
                self.trace_context,
                ld_name=ld_name,
                updated_count=str(updated),
            )
        return updated

    def mark_alive(self, *, ld_name: str, observed_at: datetime) -> None:
        self.inner.mark_alive(ld_name=ld_name, observed_at=observed_at)
        if self.trace_context.enabled:
            self.trace_sink.emit(
                "state_cache.mark_alive",
                self.trace_context,
                ld_name=ld_name,
                observed_at=observed_at.isoformat(),
            )

    def mark_unavailable(
        self,
        *,
        ld_name: str,
        status: str,
        observed_at: datetime,
        reason: str | None = None,
    ) -> None:
        self.inner.mark_unavailable(
            ld_name=ld_name,
            status=status,
            observed_at=observed_at,
            reason=reason,
        )
        if self.trace_context.enabled:
            self.trace_sink.emit(
                "state_cache.mark_unavailable",
                self.trace_context,
                ld_name=ld_name,
                status=status,
                reason=reason or "",
            )


def _emit_audit_best_effort(
    *,
    audit_sink: AuditEventSinkPort,
    event: AuditEvent,
    logger: logging.Logger,
    operation: str,
    resource_id: str,
) -> None:
    """Emit one audit event without interrupting cache writes."""

    try:
        audit_sink.emit(event)
    except Exception as exc:
        logger.warning(
            "audit sink emit failed",
            extra={
                "operation": operation,
                "resource_id": resource_id,
                "error": str(exc),
            },
        )
