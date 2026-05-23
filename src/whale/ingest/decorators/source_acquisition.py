"""Decorator objects for SourceAcquisitionPort crosscutting concerns."""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from datetime import datetime

from whale.ingest.ports.source.source_acquisition_port import (
    SourceAcquisitionPort,
    SourceSubscriptionHandle,
    SubscriptionStateHandler,
)
from whale.ingest.usecases.dtos.acquired_node_state import AcquiredNodeStateBatch
from whale.ingest.usecases.dtos.source_acquisition_request import (
    AcquisitionExecutionOptions,
    AcquisitionItemData,
)
from whale.ingest.usecases.dtos.source_connection_data import SourceConnectionData
from whale.shared.crosscutting.auth import AccessPolicyPort, Permission, Principal
from whale.shared.crosscutting.compliance import AuditEvent, AuditEventSinkPort, DataClassification
from whale.shared.crosscutting.debug import DebugTraceContext, DebugTraceSinkPort
from whale.shared.crosscutting.observability import SensitiveDataMasker
from whale.shared.crosscutting.resilience import BackoffPolicy, ErrorClassifier, RetryPolicy

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class LoggingSourceAcquisitionPort(SourceAcquisitionPort):
    """Emit structured logs around source acquisition operations."""

    inner: SourceAcquisitionPort
    logger: logging.Logger = LOGGER
    masker: SensitiveDataMasker = SensitiveDataMasker()

    def supports_subscription(
        self,
        execution: AcquisitionExecutionOptions,
        connection: SourceConnectionData,
    ) -> bool:
        supported = self.inner.supports_subscription(execution, connection)
        self.logger.info(
            "supports_subscription resolved",
            extra={
                "ld_name": connection.ld_name,
                "protocol": execution.protocol,
                "supported": supported,
            },
        )
        return supported

    async def read(
        self,
        execution: AcquisitionExecutionOptions,
        connection: SourceConnectionData,
        items: list[AcquisitionItemData],
    ) -> AcquiredNodeStateBatch:
        started_at = time.monotonic()
        try:
            batch = await self.inner.read(execution, connection, items)
            self.logger.info(
                "source read succeeded",
                extra={
                    "ld_name": connection.ld_name,
                    "item_count": len(items),
                    "value_count": len(batch.values),
                    "duration_seconds": time.monotonic() - started_at,
                },
            )
            return batch
        except Exception as exc:
            self.logger.warning(
                "source read failed",
                extra={
                    "ld_name": connection.ld_name,
                    "item_count": len(items),
                    "duration_seconds": time.monotonic() - started_at,
                    "error": str(exc),
                    "connection": self.masker.mask_mapping(connection.params),
                },
            )
            raise

    async def start_subscription(
        self,
        execution: AcquisitionExecutionOptions,
        connection: SourceConnectionData,
        items: list[AcquisitionItemData],
        *,
        state_received: SubscriptionStateHandler,
    ) -> SourceSubscriptionHandle:
        try:
            handle = await self.inner.start_subscription(
                execution,
                connection,
                items,
                state_received=state_received,
            )
            self.logger.info(
                "subscription started",
                extra={"ld_name": connection.ld_name, "item_count": len(items)},
            )
            return handle
        except Exception as exc:
            self.logger.warning(
                "subscription start failed",
                extra={"ld_name": connection.ld_name, "item_count": len(items), "error": str(exc)},
            )
            raise


@dataclass(frozen=True, slots=True)
class AuditedSourceAcquisitionPort(SourceAcquisitionPort):
    """Emit audit events around acquisition operations."""

    inner: SourceAcquisitionPort
    audit_sink: AuditEventSinkPort

    def supports_subscription(
        self,
        execution: AcquisitionExecutionOptions,
        connection: SourceConnectionData,
    ) -> bool:
        return self.inner.supports_subscription(execution, connection)

    async def read(
        self,
        execution: AcquisitionExecutionOptions,
        connection: SourceConnectionData,
        items: list[AcquisitionItemData],
    ) -> AcquiredNodeStateBatch:
        try:
            batch = await self.inner.read(execution, connection, items)
            _emit_audit_best_effort(
                audit_sink=self.audit_sink,
                event=AuditEvent(
                    event_name="source.read",
                    observed_at=batch.client_processed_at,
                    classification=DataClassification.INTERNAL,
                    resource_id=connection.ld_name,
                    attributes={"item_count": str(len(items))},
                ),
                logger=LOGGER,
                operation="source.read",
                resource_id=connection.ld_name,
            )
            return batch
        except Exception:
            _emit_audit_best_effort(
                audit_sink=self.audit_sink,
                event=AuditEvent(
                    event_name="source.read.failed",
                    observed_at=_utc_now(),
                    classification=DataClassification.INTERNAL,
                    resource_id=connection.ld_name,
                    outcome="failure",
                    attributes={"item_count": str(len(items))},
                ),
                logger=LOGGER,
                operation="source.read.failed",
                resource_id=connection.ld_name,
            )
            raise

    async def start_subscription(
        self,
        execution: AcquisitionExecutionOptions,
        connection: SourceConnectionData,
        items: list[AcquisitionItemData],
        *,
        state_received: SubscriptionStateHandler,
    ) -> SourceSubscriptionHandle:
        try:
            handle = await self.inner.start_subscription(
                execution,
                connection,
                items,
                state_received=state_received,
            )
            _emit_audit_best_effort(
                audit_sink=self.audit_sink,
                event=AuditEvent(
                    event_name="source.subscription.start",
                    observed_at=_utc_now(),
                    classification=DataClassification.INTERNAL,
                    resource_id=connection.ld_name,
                    attributes={"item_count": str(len(items))},
                ),
                logger=LOGGER,
                operation="source.subscription.start",
                resource_id=connection.ld_name,
            )
            return handle
        except Exception:
            _emit_audit_best_effort(
                audit_sink=self.audit_sink,
                event=AuditEvent(
                    event_name="source.subscription.start.failed",
                    observed_at=_utc_now(),
                    classification=DataClassification.INTERNAL,
                    resource_id=connection.ld_name,
                    outcome="failure",
                    attributes={"item_count": str(len(items))},
                ),
                logger=LOGGER,
                operation="source.subscription.start.failed",
                resource_id=connection.ld_name,
            )
            raise


@dataclass(frozen=True, slots=True)
class RetryingSourceAcquisitionPort(SourceAcquisitionPort):
    """Retry acquisition operations according to shared retry policies."""

    inner: SourceAcquisitionPort
    retry_policy: RetryPolicy
    backoff_policy: BackoffPolicy
    error_classifier: ErrorClassifier

    def supports_subscription(
        self,
        execution: AcquisitionExecutionOptions,
        connection: SourceConnectionData,
    ) -> bool:
        return self.inner.supports_subscription(execution, connection)

    async def read(
        self,
        execution: AcquisitionExecutionOptions,
        connection: SourceConnectionData,
        items: list[AcquisitionItemData],
    ) -> AcquiredNodeStateBatch:
        attempt = 0
        while True:
            attempt += 1
            try:
                return await self.inner.read(execution, connection, items)
            except Exception as exc:
                classified = self.error_classifier.classify(exc)
                if not self._should_retry(classified.error_code, attempt):
                    raise
                await asyncio.sleep(self.backoff_policy.delay_for(attempt))

    async def start_subscription(
        self,
        execution: AcquisitionExecutionOptions,
        connection: SourceConnectionData,
        items: list[AcquisitionItemData],
        *,
        state_received: SubscriptionStateHandler,
    ) -> SourceSubscriptionHandle:
        attempt = 0
        while True:
            attempt += 1
            try:
                return await self.inner.start_subscription(
                    execution,
                    connection,
                    items,
                    state_received=state_received,
                )
            except Exception as exc:
                classified = self.error_classifier.classify(exc)
                if not self._should_retry(classified.error_code, attempt):
                    raise
                await asyncio.sleep(self.backoff_policy.delay_for(attempt))

    def _should_retry(self, error_code: str, attempt: int) -> bool:
        return (
            attempt < self.retry_policy.max_attempts
            and error_code in self.retry_policy.retryable_error_codes
        )


@dataclass(frozen=True, slots=True)
class AuthorizedSourceAcquisitionPort(SourceAcquisitionPort):
    """Enforce access-policy decisions before acquisition operations."""

    inner: SourceAcquisitionPort
    principal: Principal
    access_policy: AccessPolicyPort

    def supports_subscription(
        self,
        execution: AcquisitionExecutionOptions,
        connection: SourceConnectionData,
    ) -> bool:
        self._require_allowed(connection.ld_name, "supports_subscription")
        return self.inner.supports_subscription(execution, connection)

    async def read(
        self,
        execution: AcquisitionExecutionOptions,
        connection: SourceConnectionData,
        items: list[AcquisitionItemData],
    ) -> AcquiredNodeStateBatch:
        self._require_allowed(connection.ld_name, "read")
        return await self.inner.read(execution, connection, items)

    async def start_subscription(
        self,
        execution: AcquisitionExecutionOptions,
        connection: SourceConnectionData,
        items: list[AcquisitionItemData],
        *,
        state_received: SubscriptionStateHandler,
    ) -> SourceSubscriptionHandle:
        self._require_allowed(connection.ld_name, "subscribe")
        return await self.inner.start_subscription(
            execution,
            connection,
            items,
            state_received=state_received,
        )

    def _require_allowed(self, resource_id: str, action: str) -> None:
        decision = self.access_policy.evaluate(
            self.principal,
            Permission(resource_type="source_connection", resource_id=resource_id, action=action),
        )
        if not decision.allowed:
            raise PermissionError(decision.reason or f"access denied: {action}")


@dataclass(frozen=True, slots=True)
class DebugSourceAcquisitionPort(SourceAcquisitionPort):
    """Emit best-effort debug traces around acquisition operations."""

    inner: SourceAcquisitionPort
    trace_context: DebugTraceContext
    trace_sink: DebugTraceSinkPort

    def supports_subscription(
        self,
        execution: AcquisitionExecutionOptions,
        connection: SourceConnectionData,
    ) -> bool:
        supported = self.inner.supports_subscription(execution, connection)
        if self.trace_context.enabled:
            self.trace_sink.emit(
                "source.supports_subscription",
                self.trace_context,
                ld_name=connection.ld_name,
                supported=str(supported).lower(),
            )
        return supported

    async def read(
        self,
        execution: AcquisitionExecutionOptions,
        connection: SourceConnectionData,
        items: list[AcquisitionItemData],
    ) -> AcquiredNodeStateBatch:
        if self.trace_context.enabled:
            self.trace_sink.emit(
                "source.read.start",
                self.trace_context,
                ld_name=connection.ld_name,
                item_count=str(len(items)),
            )
        try:
            batch = await self.inner.read(execution, connection, items)
            if self.trace_context.enabled:
                self.trace_sink.emit(
                    "source.read.success",
                    self.trace_context,
                    ld_name=connection.ld_name,
                    value_count=str(len(batch.values)),
                )
            return batch
        except Exception as exc:
            if self.trace_context.enabled:
                self.trace_sink.emit(
                    "source.read.failed",
                    self.trace_context,
                    ld_name=connection.ld_name,
                    error=str(exc),
                )
            raise

    async def start_subscription(
        self,
        execution: AcquisitionExecutionOptions,
        connection: SourceConnectionData,
        items: list[AcquisitionItemData],
        *,
        state_received: SubscriptionStateHandler,
    ) -> SourceSubscriptionHandle:
        if self.trace_context.enabled:
            self.trace_sink.emit(
                "source.subscription.start",
                self.trace_context,
                ld_name=connection.ld_name,
                item_count=str(len(items)),
            )
        return await self.inner.start_subscription(
            execution,
            connection,
            items,
            state_received=state_received,
        )


def _utc_now() -> datetime:
    from datetime import UTC, datetime

    return datetime.now(tz=UTC)


def _emit_audit_best_effort(
    *,
    audit_sink: AuditEventSinkPort,
    event: AuditEvent,
    logger: logging.Logger,
    operation: str,
    resource_id: str,
) -> None:
    """Emit one audit event without interrupting the main flow."""

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
