"""SubscriptionAcquisitionRole — 启动订阅采集 session。

设计约定：
- 当前协议明确支持订阅时，启动前先 read 一次完整基准状态；
- initial read baseline 用于填充 latest-state cache；
- 当前协议明确不支持订阅时，应在 baseline side effect 前 fail-fast；
- 后续 datachange 只做增量 batch 覆盖；
- reconnect 策略尚未实现到运行态循环；未来恢复时必须 reconnect -> baseline read -> start_subscription；
- 订阅 notification 的 queue / micro-batch 在 source_reader 内处理；
- 本 role 只负责订阅采集策略编排；
- 参数合法性由 SourceAcquisitionUseCase 保证。
"""

from __future__ import annotations

import asyncio
import contextlib
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import cast

from whale.ingest.ports.source.source_acquisition_port import (
    SourceBatchMismatchError,
    SourceReadTimeoutError,
    SourceAcquisitionPort,
    SourceReadError,
    SourceSubscriptionUnsupportedError,
    SourceSubscriptionHandle,
    SubscriptionStateHandler,
)
from whale.ingest.ports.state.source_state_cache_port import (
    SourceStateCachePort,
    SourceStateCacheWriteError,
)
from whale.ingest.ports.metrics import IngestMetricEvent, IngestMetricsPort
from whale.ingest.usecases.dtos.acquired_node_state import AcquiredNodeStateBatch
from whale.ingest.usecases.dtos.source_acquisition_request import (
    SourceAcquisitionRequest,
)
from whale.ingest.usecases.dtos.source_acquisition_start_result import (
    AcquisitionSession,
    SourceAcquisitionStartResult,
)
from whale.ingest.usecases.dtos.source_connection_data import SourceConnectionData


@dataclass(slots=True)
class SubscriptionAcquisitionSession:
    """运行中的订阅采集会话。"""

    handle: SourceSubscriptionHandle
    closed: bool = False

    async def close(self) -> None:
        """关闭订阅采集会话。"""

        if self.closed:
            return

        self.closed = True
        await self.handle.close()


class SubscriptionAcquisitionRole:
    """启动协议订阅，并返回统一启动结果。"""

    def __init__(
        self,
        *,
        acquisition_port: SourceAcquisitionPort,
        state_cache_port: SourceStateCachePort,
        metrics_port: IngestMetricsPort | None = None,
    ) -> None:
        """初始化订阅采集角色。Args: adapter: 采集适配器。state_cache: 状态缓存 port。"""
        self._acquisition_port = acquisition_port
        self._state_cache_port = state_cache_port
        self._metrics_port = metrics_port

    async def start(
        self,
        request: SourceAcquisitionRequest,
    ) -> SourceAcquisitionStartResult:
        """为 request.connections 中的全部 connection 启动订阅。

        Raises:
            SourceSubscriptionUnsupportedError: 当前协议 adapter 不支持订阅时抛出。
        """

        sessions: list[SubscriptionAcquisitionSession] = []
        start_interval_seconds = (
            request.execution.subscription_start_interval_ms / 1000
        )

        for index, connection in enumerate(request.connections):
            if index > 0 and start_interval_seconds > 0:
                await asyncio.sleep(start_interval_seconds)

            try:
                if not self._acquisition_port.supports_subscription(
                    request.execution,
                    connection,
                ):
                    raise SourceSubscriptionUnsupportedError(
                        "subscription_unsupported"
                    )

                handle = await self._start_with_retry(
                    request=request,
                    connection=connection,
                )
                sessions.append(SubscriptionAcquisitionSession(handle=handle))

            except SourceSubscriptionUnsupportedError:
                self._mark_unavailable(
                    ld_name=connection.ld_name,
                    reason="subscription_unsupported",
                )
                await self._close_sessions(sessions)
                raise
            except Exception as exc:
                if not isinstance(exc, SourceStateCacheWriteError):
                    self._mark_unavailable(
                        ld_name=connection.ld_name,
                        reason=_build_failure_reason(exc),
                    )
                await self._close_sessions(sessions)
                raise

        return SourceAcquisitionStartResult(
            request_id=request.request_id,
            task_id=request.task_id,
            mode=request.execution.acquisition_mode.upper(),
            sessions=cast(list[AcquisitionSession], sessions),
        )

    async def _read_initial_baseline(
        self,
        *,
        request: SourceAcquisitionRequest,
        connection: SourceConnectionData,
    ) -> None:
        """订阅启动前读取一次完整基准状态。"""

        batch = await self._acquisition_port.read(
            request.execution,
            connection,
            list(request.items),
        )

        updated_count = self._update_batch(
            ld_name=connection.ld_name,
            batch=batch,
        )

        if updated_count > 0:
            self._state_cache_port.mark_alive(
                ld_name=connection.ld_name,
                observed_at=batch.client_processed_at,
            )
        self._emit_metric(
            operation="subscription_baseline_read",
            source_id=connection.ld_name,
            protocol=request.execution.protocol,
            status="SUCCESS",
            error_code=None,
            started_at=0.0,
        )

    async def _start_with_retry(
        self,
        *,
        request: SourceAcquisitionRequest,
        connection: SourceConnectionData,
    ) -> SourceSubscriptionHandle:
        max_retries = int(request.execution.params.get("subscription_max_retry", 0))
        backoff_ms = int(request.execution.params.get("subscription_backoff_ms", 0))
        attempt = 0
        last_exc: Exception | None = None
        while attempt <= max_retries:
            started_at = time.monotonic()
            try:
                await self._read_initial_baseline(request=request, connection=connection)
                handle = await self._acquisition_port.start_subscription(
                    request.execution,
                    connection,
                    list(request.items),
                    state_received=self._build_state_received_handler(connection=connection),
                )
                self._emit_metric(
                    operation="subscription_start",
                    source_id=connection.ld_name,
                    protocol=request.execution.protocol,
                    status="SUCCESS",
                    error_code=None,
                    started_at=started_at,
                )
                return handle
            except Exception as exc:
                last_exc = exc
                self._emit_metric(
                    operation="subscription_reconnect",
                    source_id=connection.ld_name,
                    protocol=request.execution.protocol,
                    status="FAILED",
                    error_code=type(exc).__name__,
                    started_at=started_at,
                )
                attempt += 1
                if attempt > max_retries:
                    break
                if backoff_ms > 0:
                    await asyncio.sleep(backoff_ms / 1000)
        assert last_exc is not None
        raise last_exc

    def _build_state_received_handler(
        self,
        *,
        connection: SourceConnectionData,
    ) -> SubscriptionStateHandler:
        """构造绑定当前 connection 的订阅回调。"""

        async def _state_received(batch: AcquiredNodeStateBatch) -> None:
            updated_count = self._update_batch(
                ld_name=connection.ld_name,
                batch=batch,
            )
            if updated_count > 0:
                self._state_cache_port.mark_alive(
                    ld_name=connection.ld_name,
                    observed_at=batch.client_processed_at,
                )

        return _state_received

    def _update_batch(
        self,
        *,
        ld_name: str,
        batch: AcquiredNodeStateBatch,
    ) -> int:
        """更新 latest-state cache。"""

        if batch.is_empty():
            return 0

        return self._state_cache_port.update(
            ld_name=ld_name,
            batch=batch,
        )

    def _mark_unavailable(
        self,
        *,
        ld_name: str,
        reason: str,
    ) -> None:
        """尽力标记订阅启动失败为不可用状态。"""

        try:
            self._state_cache_port.mark_unavailable(
                ld_name=ld_name,
                status="ERROR",
                observed_at=_utc_now(),
                reason=reason,
            )
        except SourceStateCacheWriteError:
            return

    @staticmethod
    async def _close_sessions(
        sessions: list[SubscriptionAcquisitionSession],
    ) -> None:
        """启动过程中发生异常时关闭已启动的订阅 session。"""

        for session in reversed(sessions):
            with contextlib.suppress(Exception):
                await session.close()

    def _emit_metric(
        self,
        *,
        operation: str,
        source_id: str | None,
        protocol: str | None,
        status: str,
        error_code: str | None,
        started_at: float,
    ) -> None:
        if self._metrics_port is None:
            return
        duration_ms = 0.0 if started_at == 0.0 else (time.monotonic() - started_at) * 1000.0
        self._metrics_port.emit(
            IngestMetricEvent(
                operation=operation,
                source_id=source_id,
                protocol=protocol,
                duration_ms=duration_ms,
                status=status,
                error_code=error_code,
                timestamp=datetime.now(tz=UTC),
            )
        )


def _utc_now() -> datetime:
    """返回当前 UTC 时间。"""

    return datetime.now(tz=UTC)


def _build_failure_reason(exc: Exception) -> str:
    """将订阅端失败规范化为稳定的原因码。"""

    if isinstance(exc, SourceStateCacheWriteError):
        return f"cache_write_failed:{exc.error_code}"
    if isinstance(exc, SourceSubscriptionUnsupportedError):
        return "subscription_unsupported"
    if isinstance(exc, SourceBatchMismatchError):
        return "batch_mismatch"
    if isinstance(exc, SourceReadTimeoutError):
        return "source_read_timeout"
    if isinstance(exc, SourceReadError):
        lowered = (str(exc) or type(exc).__name__).strip().lower()
        if "protocol_error" in lowered:
            return "protocol_error"
        if "read_failed" in lowered:
            return "source_read_failed"
        if "runner_not_available" in lowered:
            return "runner_not_available"
        return lowered.replace(" ", "_").replace(":", "_") or "source_read_failed"
    return (str(exc) or type(exc).__name__).strip().lower().replace(" ", "_").replace(":", "_")
