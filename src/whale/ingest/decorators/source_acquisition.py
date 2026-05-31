"""装饰器模块。

为采集、写入、缓存等横切关注点提供装饰器封装。
"""

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
    """在采集操作前后发送结构化日志。"""

    inner: SourceAcquisitionPort
    logger: logging.Logger = LOGGER
    masker: SensitiveDataMasker = SensitiveDataMasker()

    def supports_subscription(
        self,
        execution: AcquisitionExecutionOptions,
        connection: SourceConnectionData,
    ) -> bool:
        """查询当前适配器是否支持订阅模式。返回布尔值。"""
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
        """带日志的读取操作。记录读取调用点、地址和结果数量。"""
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
        """启动订阅。建立与数据源的订阅连接并注册回调。"""
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
    """在采集操作前后发送审计事件。"""

    inner: SourceAcquisitionPort
    audit_sink: AuditEventSinkPort

    def supports_subscription(
        self,
        execution: AcquisitionExecutionOptions,
        connection: SourceConnectionData,
    ) -> bool:
        """查询当前适配器是否支持订阅模式。返回布尔值。"""
        return self.inner.supports_subscription(execution, connection)

    async def read(
        self,
        execution: AcquisitionExecutionOptions,
        connection: SourceConnectionData,
        items: list[AcquisitionItemData],
    ) -> AcquiredNodeStateBatch:
        """带审计的读取操作。记录读取操作到审计日志后委托底层 port 执行。"""
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
        """启动订阅。建立与数据源的订阅连接并注册回调。"""
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
    """按共享重试策略重试采集操作。

采集失败时有上限退避重试。"""

    inner: SourceAcquisitionPort
    retry_policy: RetryPolicy
    backoff_policy: BackoffPolicy
    error_classifier: ErrorClassifier

    def supports_subscription(
        self,
        execution: AcquisitionExecutionOptions,
        connection: SourceConnectionData,
    ) -> bool:
        """查询当前适配器是否支持订阅模式。返回布尔值。"""
        return self.inner.supports_subscription(execution, connection)

    async def read(
        self,
        execution: AcquisitionExecutionOptions,
        connection: SourceConnectionData,
        items: list[AcquisitionItemData],
    ) -> AcquiredNodeStateBatch:
        """带重试的读取操作。失败时按配置重试，超限后抛出。"""
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
        """启动订阅。建立与数据源的订阅连接并注册回调。"""
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
    """在采集操作前强制执行访问策略检查。

包装内部 SourceAcquisitionPort，委托前先做授权检查。"""

    inner: SourceAcquisitionPort
    principal: Principal
    access_policy: AccessPolicyPort

    def supports_subscription(
        self,
        execution: AcquisitionExecutionOptions,
        connection: SourceConnectionData,
    ) -> bool:
        """查询当前适配器是否支持订阅模式。返回布尔值。"""
        self._require_allowed(connection.ld_name, "supports_subscription")
        return self.inner.supports_subscription(execution, connection)

    async def read(
        self,
        execution: AcquisitionExecutionOptions,
        connection: SourceConnectionData,
        items: list[AcquisitionItemData],
    ) -> AcquiredNodeStateBatch:
        """带授权的读取操作。先校验访问权限，通过后委托底层 port 执行。"""
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
        """启动订阅。建立与数据源的订阅连接并注册回调。"""
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
    """在采集操作前后尽力发送调试追踪事件。"""

    inner: SourceAcquisitionPort
    trace_context: DebugTraceContext
    trace_sink: DebugTraceSinkPort

    def supports_subscription(
        self,
        execution: AcquisitionExecutionOptions,
        connection: SourceConnectionData,
    ) -> bool:
        """查询当前适配器是否支持订阅模式。返回布尔值。"""
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
        """调试模式读取操作。详细记录输入参数和返回内容用于诊断。"""
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
        """启动订阅。建立与数据源的订阅连接并注册回调。"""
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
    """发送审计事件，不中断主流程。"""

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
