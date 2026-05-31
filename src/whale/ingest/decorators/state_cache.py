"""装饰器模块。

为采集、写入、缓存等横切关注点提供装饰器封装。
"""

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
    """在状态缓存写入时发送日志。"""

    inner: SourceStateCachePort
    logger: logging.Logger = LOGGER

    def update(self, *, ld_name: str, batch: AcquiredNodeStateBatch) -> int:
        """update 方法。"""
        started_at = time.monotonic()
        try:
            """带日志的状态更新。记录更新操作并委托底层 port 执行。"""
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
        """mark_alive 方法。"""
        self.inner.mark_alive(ld_name=ld_name, observed_at=observed_at)

    def mark_unavailable(
        self,
        *,
        ld_name: str,
        status: str,
        observed_at: datetime,
        reason: str | None = None,
    ) -> None:
        """带日志的存活标记。记录源上线事件。"""
        """带日志的不可用标记。记录源离线事件。"""
        self.inner.mark_unavailable(
            ld_name=ld_name,
            status=status,
            observed_at=observed_at,
            reason=reason,
        )


@dataclass(frozen=True, slots=True)
class AuditedStateCachePort(SourceStateCachePort):
    """在状态缓存写入时发送审计事件。"""

    inner: SourceStateCachePort
    audit_sink: AuditEventSinkPort

    def update(self, *, ld_name: str, batch: AcquiredNodeStateBatch) -> int:
        """update 方法。"""
        try:
            """带审计的状态更新。记录审计事件后委托底层 port 执行。"""
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
        """mark_alive 方法。"""
        self.inner.mark_alive(ld_name=ld_name, observed_at=observed_at)

    def mark_unavailable(
        self,
        *,
        ld_name: str,
        status: str,
        observed_at: datetime,
        reason: str | None = None,
    ) -> None:
        """带审计的存活标记。记录审计事件后标记源为在线。"""
        """带审计的不可用标记。记录审计事件后标记源为离线。"""
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
    """记录缓存写入操作的计数器和延迟。"""

    inner: SourceStateCachePort
    metrics_sink: MetricsSinkPort

    def update(self, *, ld_name: str, batch: AcquiredNodeStateBatch) -> int:
        """update 方法。"""
        started_at = time.monotonic()
        try:
            """带指标的状态更新。记录更新耗时和结果计数。"""
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
        """mark_alive 方法。"""
        self.inner.mark_alive(ld_name=ld_name, observed_at=observed_at)

    def mark_unavailable(
        self,
        *,
        ld_name: str,
        status: str,
        observed_at: datetime,
        reason: str | None = None,
    ) -> None:
        """带指标的存活标记。记录上线事件计数器。"""
        """带指标的不可用标记。记录离线事件计数器。"""
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
    """对缓存操作尽力发送调试追踪事件。"""

    inner: SourceStateCachePort
    trace_context: DebugTraceContext
    trace_sink: DebugTraceSinkPort

    def update(self, *, ld_name: str, batch: AcquiredNodeStateBatch) -> int:
        """update 方法。"""
        updated = self.inner.update(ld_name=ld_name, batch=batch)
        if self.trace_context.enabled:
            """调试模式状态更新。详细记录输入参数和缓存内容。"""
            self.trace_sink.emit(
                "state_cache.update",
                self.trace_context,
                ld_name=ld_name,
                updated_count=str(updated),
            )
        return updated

    def mark_alive(self, *, ld_name: str, observed_at: datetime) -> None:
        """mark_alive 方法。"""
        self.inner.mark_alive(ld_name=ld_name, observed_at=observed_at)
        if self.trace_context.enabled:
            """调试模式存活标记。详细记录源标识符和上线时间。"""
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
        """调试模式不可用标记。详细记录源标识符和离线原因。"""
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
    """发送审计事件，不中断缓存写入。"""

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
