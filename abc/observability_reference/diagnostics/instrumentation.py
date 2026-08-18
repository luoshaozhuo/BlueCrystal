"""Instrumentation 技术事实到 Diagnostics 的映射."""

from __future__ import annotations

from datetime import datetime

from .service import DiagnosticService


class DiagnosticInstrumentationHooks:
    """把 InstrumentationHooks 更新为当前诊断投影."""

    def __init__(self, diagnostics: DiagnosticService) -> None:
        self._diagnostics = diagnostics

    def http_request_started(self, *, method: str, path: str) -> None:
        pass

    def http_request_finished(
        self,
        *,
        method: str,
        path: str,
        status_code: int,
        duration_seconds: float,
    ) -> None:
        pass

    def http_request_failed(
        self,
        *,
        method: str,
        path: str,
        duration_seconds: float,
        exception: Exception,
    ) -> None:
        pass

    def scheduler_started(self) -> None:
        self._diagnostics.scheduler_started()

    def scheduler_stopped(self) -> None:
        self._diagnostics.scheduler_stopped()

    def scheduler_job_missed(
        self,
        *,
        task_id: int,
        scheduled_run_time: datetime,
    ) -> None:
        self._diagnostics.scheduler_job_missed(
            task_id=task_id,
            scheduled_run_time=scheduled_run_time,
        )

    def scheduler_job_max_instances(
        self,
        *,
        task_id: int,
        scheduled_run_times: tuple[datetime, ...],
    ) -> None:
        self._diagnostics.scheduler_job_max_instances(
            task_id=task_id,
            scheduled_run_times=scheduled_run_times,
        )

    def task_execution_started(self, *, task_id: int) -> None:
        self._diagnostics.task_execution_started(task_id=task_id)

    def task_execution_succeeded(
        self,
        *,
        task_id: int,
        duration_seconds: float,
    ) -> None:
        self._diagnostics.task_execution_succeeded(
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
        self._diagnostics.task_execution_failed(
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
        self._diagnostics.task_execution_cancelled(
            task_id=task_id,
            duration_seconds=duration_seconds,
        )

    def task_scheduled(self, *, task_id: int) -> None:
        self._diagnostics.task_scheduled(task_id=task_id)

    def task_removed(self, *, task_id: int) -> None:
        self._diagnostics.task_removed(task_id=task_id)

    def task_paused(self, *, task_id: int) -> None:
        self._diagnostics.task_paused(task_id=task_id)

    def task_resumed(self, *, task_id: int) -> None:
        self._diagnostics.task_resumed(task_id=task_id)

    def task_run_requested(self, *, task_id: int) -> None:
        self._diagnostics.task_run_requested(task_id=task_id)
