"""Polling 采集 role。

本模块负责主动采集循环、连接级隔离、状态缓存更新与可靠关闭。
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
import time
from dataclasses import dataclass
from datetime import UTC, datetime

from pacific.whale.ingest.ports.source.source_acquisition_port import (
    SourceAcquisitionError,
    SourceBatchMismatchError,
    SourceAcquisitionPort,
    SourceReadOnceFailedError,
    SourceReadTimeoutError,
)
from pacific.whale.ingest.ports.metrics import IngestMetricEvent, IngestMetricsPort
from pacific.whale.ingest.ports.state.source_state_cache_port import (
    SourceStateCachePort,
    SourceStateCacheWriteError,
)
from pacific.whale.ingest.usecases.dtos.acquired_node_state import AcquiredNodeStateBatch
from pacific.whale.ingest.usecases.dtos.source_acquisition_request import (
    SourceAcquisitionRequest,
)
from pacific.whale.ingest.usecases.dtos.source_acquisition_start_result import (
    SourceAcquisitionStartResult,
)
from pacific.whale.ingest.usecases.dtos.source_connection_data import SourceConnectionData

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class _ConnectionReadOutcome:
    """一轮中单个连接的读取结果。"""

    ld_name: str
    success: bool
    reason: str | None = None


@dataclass(slots=True)
class PollingAcquisitionSession:
    """运行中的 polling 会话。"""

    task: asyncio.Task[None]
    stop_event: asyncio.Event
    closed: bool = False

    async def close(self) -> None:
        """停止后台 task，并保证 close 不悬挂。"""

        if self.closed:
            return

        self.closed = True
        self.stop_event.set()
        self.task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await self.task


class PollingAcquisitionRole:
    """主动采集循环角色。

    Args:
        acquisition_port: 负责一次连接读取的采集端口。
        state_cache_port: latest-state cache 写入端口。
    """

    def __init__(
        self,
        *,
        acquisition_port: SourceAcquisitionPort,
        state_cache_port: SourceStateCachePort,
        metrics_port: IngestMetricsPort | None = None,
    ) -> None:
        """初始化轮询采集角色。Args: adapter: 采集适配器。state_cache: 状态缓存 port。"""
        self._acquisition_port = acquisition_port
        self._state_cache_port = state_cache_port
        self._cycle_overrun_count = 0
        self._metrics_port = metrics_port

    def start(
        self,
        request: SourceAcquisitionRequest,
    ) -> SourceAcquisitionStartResult:
        """启动主动采集循环，并立即返回会话信息。"""

        stop_event = asyncio.Event()
        task = asyncio.create_task(self._run_loop(request=request, stop_event=stop_event))
        return SourceAcquisitionStartResult(
            request_id=request.request_id,
            task_id=request.task_id,
            mode=request.execution.acquisition_mode.upper(),
            sessions=[PollingAcquisitionSession(task=task, stop_event=stop_event)],
        )

    async def _run_loop(
        self,
        *,
        request: SourceAcquisitionRequest,
        stop_event: asyncio.Event,
    ) -> None:
        """后台主动采集循环。"""

        interval_seconds = request.execution.interval_ms / 1000
        remaining_iterations = request.execution.max_iteration

        try:
            while not stop_event.is_set():
                cycle_started_at = time.monotonic()
                outcomes = await self._read_all_connections(request=request, stop_event=stop_event)
                if self._is_read_once_request(request) and not any(
                    outcome.success for outcome in outcomes
                ):
                    reasons = ", ".join(
                        f"{outcome.ld_name}: {outcome.reason or 'unknown_error'}"
                        for outcome in outcomes
                    )
                    raise SourceReadOnceFailedError(
                        f"all connections failed in read_once: {reasons}"
                    )

                if remaining_iterations is not None:
                    remaining_iterations -= 1
                    if remaining_iterations <= 0:
                        return

                wait_seconds = max(0.0, interval_seconds - (time.monotonic() - cycle_started_at))
                if wait_seconds <= 0:
                    self._cycle_overrun_count += 1
                    continue

                with contextlib.suppress(asyncio.TimeoutError):
                    await asyncio.wait_for(stop_event.wait(), timeout=wait_seconds)
        except asyncio.CancelledError:
            raise

    async def _read_all_connections(
        self,
        *,
        request: SourceAcquisitionRequest,
        stop_event: asyncio.Event,
    ) -> list[_ConnectionReadOutcome]:
        """按连接级别控制并发并执行一轮采集。"""

        semaphore = asyncio.Semaphore(request.execution.polling_max_concurrent_connections)
        start_interval_seconds = request.execution.polling_connection_start_interval_ms / 1000

        tasks = [
            asyncio.create_task(
                self._read_connection_with_offset(
                    request=request,
                    connection=connection,
                    start_offset_seconds=index * start_interval_seconds,
                    semaphore=semaphore,
                    stop_event=stop_event,
                )
            )
            for index, connection in enumerate(request.connections)
        ]
        try:
            return list(await asyncio.gather(*tasks))
        finally:
            for task in tasks:
                if not task.done():
                    task.cancel()
            for task in tasks:
                with contextlib.suppress(asyncio.CancelledError):
                    await task

    async def _read_connection_with_offset(
        self,
        *,
        request: SourceAcquisitionRequest,
        connection: SourceConnectionData,
        start_offset_seconds: float,
        semaphore: asyncio.Semaphore,
        stop_event: asyncio.Event,
    ) -> _ConnectionReadOutcome:
        """按连接错峰后执行一次读取。"""

        if start_offset_seconds > 0:
            with contextlib.suppress(asyncio.TimeoutError):
                await asyncio.wait_for(stop_event.wait(), timeout=start_offset_seconds)
            if stop_event.is_set():
                return _ConnectionReadOutcome(ld_name=connection.ld_name, success=False, reason="stopped")

        async with semaphore:
            if stop_event.is_set():
                return _ConnectionReadOutcome(ld_name=connection.ld_name, success=False, reason="stopped")
            return await self._read_connection(request=request, connection=connection)

    async def _read_connection(
        self,
        *,
        request: SourceAcquisitionRequest,
        connection: SourceConnectionData,
    ) -> _ConnectionReadOutcome:
        """读取单个连接并更新 latest-state cache。"""

        try:
            started_at = time.monotonic()
            batch = await self._acquisition_port.read(request.execution, connection, list(request.items))
            updated_count = self._update_batch(ld_name=connection.ld_name, batch=batch)
            if updated_count > 0:
                self._state_cache_port.mark_alive(
                    ld_name=connection.ld_name,
                    observed_at=batch.client_processed_at,
                )
            self._emit_metric(
                operation="polling_read",
                source_id=connection.ld_name,
                protocol=request.execution.protocol,
                status="SUCCESS",
                error_code=None,
                started_at=started_at,
            )
            return _ConnectionReadOutcome(ld_name=connection.ld_name, success=not batch.is_empty())
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            reason = self._build_failure_reason(exc)
            if not isinstance(exc, SourceStateCacheWriteError):
                self._mark_connection_unavailable(
                    ld_name=connection.ld_name,
                    reason=reason,
                )
            LOGGER.warning("Polling read failed for %s: %s", connection.ld_name, reason)
            self._emit_metric(
                operation="polling_read",
                source_id=connection.ld_name,
                protocol=request.execution.protocol,
                status="FAILED",
                error_code=reason,
                started_at=time.monotonic(),
            )
            return _ConnectionReadOutcome(
                ld_name=connection.ld_name,
                success=False,
                reason=reason,
            )

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
        self._metrics_port.emit(
            IngestMetricEvent(
                operation=operation,
                source_id=source_id,
                protocol=protocol,
                duration_ms=max(0.0, (time.monotonic() - started_at) * 1000.0),
                status=status,
                error_code=error_code,
                timestamp=datetime.now(tz=UTC),
            )
        )

    def _update_batch(
        self,
        *,
        ld_name: str,
        batch: AcquiredNodeStateBatch,
    ) -> int:
        """更新 latest-state cache。"""

        if batch.is_empty():
            return 0
        return self._state_cache_port.update(ld_name=ld_name, batch=batch)

    @staticmethod
    def _build_failure_reason(exc: Exception) -> str:
        """构造稳定的连接失败原因。"""

        if isinstance(exc, SourceStateCacheWriteError):
            return f"cache_write_failed:{exc.error_code}"
        if isinstance(exc, SourceReadTimeoutError):
            return "source_read_timeout"
        if isinstance(exc, SourceBatchMismatchError):
            return "batch_mismatch"
        if isinstance(exc, SourceAcquisitionError):
            return _normalize_source_error_code(str(exc) or type(exc).__name__)
        return _normalize_source_error_code(str(exc) or type(exc).__name__)

    def _mark_connection_unavailable(
        self,
        *,
        ld_name: str,
        reason: str,
    ) -> None:
        """尽力标记数据源端失败为不可用状态。"""

        try:
            self._state_cache_port.mark_unavailable(
                ld_name=ld_name,
                status="ERROR",
                observed_at=_utc_now(),
                reason=reason,
            )
        except SourceStateCacheWriteError as cache_exc:
            LOGGER.warning(
                "State cache unavailable mark failed for %s: %s",
                ld_name,
                cache_exc.error_code,
            )

    @staticmethod
    def _is_read_once_request(request: SourceAcquisitionRequest) -> bool:
        """判断当前 polling 请求是否为 one-shot。"""

        mode = request.execution.acquisition_mode.strip().upper()
        return mode in {"READ", "READ_ONCE", "ONCE"} and request.execution.max_iteration == 1


def _utc_now() -> datetime:
    """返回当前 UTC 时间。"""

    return datetime.now(tz=UTC)


def _normalize_source_error_code(value: str) -> str:
    """将源端错误字符串规范化为稳定错误码。"""

    lowered = value.strip().lower()
    if "runner_not_available" in lowered:
        return "runner_not_available"
    if "protocol_error" in lowered:
        return "protocol_error"
    if "batch_mismatch" in lowered:
        return "batch_mismatch"
    if "timeout" in lowered:
        return "source_read_timeout"
    if "subscription" in lowered and "unsupported" in lowered:
        return "subscription_unsupported"
    if "read_failed" in lowered:
        return "source_read_failed"
    return lowered.replace(" ", "_").replace(":", "_") or "source_error"
