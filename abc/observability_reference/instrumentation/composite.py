"""多个 capability 的安全 Hook fan-out."""

from __future__ import annotations

from datetime import datetime
from typing import Sequence

from .hooks import safe_observe


class CompositeInstrumentationHooks:
    """Producer-facing 完整 Hook，实现对 partial consumer 的 fan-out.

    Capability instrumentation 不需要机械实现全部 Hook；只实现自己消费的
    方法即可。Composite 使用 ``getattr`` 进行可选分发。
    """

    def __init__(self, consumers: Sequence[object]) -> None:
        self._consumers = tuple(consumers)

    def _emit(self, name: str, **kwargs) -> None:
        for consumer in self._consumers:
            callback = getattr(consumer, name, None)
            if callback is not None:
                safe_observe(callback, **kwargs)

    def http_request_started(self) -> None:
        self._emit("http_request_started")

    def http_request_finished(
        self, *, status_code: int, duration_seconds: float
    ) -> None:
        self._emit(
            "http_request_finished",
            status_code=status_code,
            duration_seconds=duration_seconds,
        )

    def http_request_failed(
        self, *, duration_seconds: float, exception: Exception
    ) -> None:
        self._emit(
            "http_request_failed",
            duration_seconds=duration_seconds,
            exception=exception,
        )

    def scheduler_started(self) -> None:
        self._emit("scheduler_started")

    def scheduler_stopped(self) -> None:
        self._emit("scheduler_stopped")

    def scheduler_job_missed(self, *, scheduled_run_time: datetime) -> None:
        self._emit(
            "scheduler_job_missed",
            scheduled_run_time=scheduled_run_time,
        )

    def scheduler_job_max_instances(
        self, *, scheduled_run_times: tuple[datetime, ...]
    ) -> None:
        self._emit(
            "scheduler_job_max_instances",
            scheduled_run_times=scheduled_run_times,
        )

    def task_execution_started(self) -> None:
        self._emit("task_execution_started")

    def task_execution_succeeded(self, *, duration_seconds: float) -> None:
        self._emit(
            "task_execution_succeeded",
            duration_seconds=duration_seconds,
        )

    def task_execution_failed(
        self, *, duration_seconds: float, exception: Exception
    ) -> None:
        self._emit(
            "task_execution_failed",
            duration_seconds=duration_seconds,
            exception=exception,
        )

    def task_execution_cancelled(self, *, duration_seconds: float) -> None:
        self._emit(
            "task_execution_cancelled",
            duration_seconds=duration_seconds,
        )

    def task_scheduled(self) -> None:
        self._emit("task_scheduled")

    def task_removed(self) -> None:
        self._emit("task_removed")

    def task_paused(self) -> None:
        self._emit("task_paused")

    def task_resumed(self) -> None:
        self._emit("task_resumed")

    def task_run_requested(self) -> None:
        self._emit("task_run_requested")

    def audit_operation_succeeded(
        self, *, status_code: int | None = None
    ) -> None:
        self._emit(
            "audit_operation_succeeded",
            status_code=status_code,
        )

    def audit_operation_failed(
        self,
        *,
        status_code: int | None = None,
        exception: BaseException | None = None,
    ) -> None:
        self._emit(
            "audit_operation_failed",
            status_code=status_code,
            exception=exception,
        )
