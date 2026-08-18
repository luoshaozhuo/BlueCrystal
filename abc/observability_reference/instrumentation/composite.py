"""多个 Observability capability hook 的组合器."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime

from .hooks import InstrumentationHooks, safe_observe


class CompositeInstrumentationHooks:
    """把一次 Instrumentation 事实 fan-out 给多个 capability."""

    def __init__(self, hooks: Sequence[InstrumentationHooks]) -> None:
        self._hooks = tuple(hooks)

    def http_request_started(self, *, method: str, path: str) -> None:
        self._emit("http_request_started", method=method, path=path)

    def http_request_finished(
        self,
        *,
        method: str,
        path: str,
        status_code: int,
        duration_seconds: float,
    ) -> None:
        self._emit(
            "http_request_finished",
            method=method,
            path=path,
            status_code=status_code,
            duration_seconds=duration_seconds,
        )

    def http_request_failed(
        self,
        *,
        method: str,
        path: str,
        duration_seconds: float,
        exception: Exception,
    ) -> None:
        self._emit(
            "http_request_failed",
            method=method,
            path=path,
            duration_seconds=duration_seconds,
            exception=exception,
        )

    def scheduler_started(self) -> None:
        self._emit("scheduler_started")

    def scheduler_stopped(self) -> None:
        self._emit("scheduler_stopped")

    def scheduler_job_missed(
        self,
        *,
        task_id: int,
        scheduled_run_time: datetime,
    ) -> None:
        self._emit(
            "scheduler_job_missed",
            task_id=task_id,
            scheduled_run_time=scheduled_run_time,
        )

    def scheduler_job_max_instances(
        self,
        *,
        task_id: int,
        scheduled_run_times: tuple[datetime, ...],
    ) -> None:
        self._emit(
            "scheduler_job_max_instances",
            task_id=task_id,
            scheduled_run_times=scheduled_run_times,
        )

    def task_execution_started(self, *, task_id: int) -> None:
        self._emit("task_execution_started", task_id=task_id)

    def task_execution_succeeded(
        self,
        *,
        task_id: int,
        duration_seconds: float,
    ) -> None:
        self._emit(
            "task_execution_succeeded",
            task_id=task_id,
            duration_seconds=duration_seconds,
        )

    def task_execution_failed(
        self,
        *,
        task_id: int,
        duration_seconds: float,
        exception: Exception,
    ) -> None:
        self._emit(
            "task_execution_failed",
            task_id=task_id,
            duration_seconds=duration_seconds,
            exception=exception,
        )

    def task_execution_cancelled(
        self,
        *,
        task_id: int,
        duration_seconds: float,
    ) -> None:
        self._emit(
            "task_execution_cancelled",
            task_id=task_id,
            duration_seconds=duration_seconds,
        )

    def task_scheduled(self, *, task_id: int) -> None:
        self._emit("task_scheduled", task_id=task_id)

    def task_removed(self, *, task_id: int) -> None:
        self._emit("task_removed", task_id=task_id)

    def task_paused(self, *, task_id: int) -> None:
        self._emit("task_paused", task_id=task_id)

    def task_resumed(self, *, task_id: int) -> None:
        self._emit("task_resumed", task_id=task_id)

    def task_run_requested(self, *, task_id: int) -> None:
        self._emit("task_run_requested", task_id=task_id)

    def _emit(self, method_name: str, /, **kwargs: object) -> None:
        for hook in self._hooks:
            callback = getattr(hook, method_name)
            safe_observe(callback, **kwargs)
