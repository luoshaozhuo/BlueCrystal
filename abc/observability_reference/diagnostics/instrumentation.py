"""Instrumentation 事实 -> Diagnostics current-state projection."""

from __future__ import annotations

from datetime import datetime

from observability_reference.shared import get_observation_context

from .service import DiagnosticService


def _task_id() -> int | None:
    return get_observation_context().task_id


class DiagnosticInstrumentationHooks:
    def __init__(self, diagnostics: DiagnosticService) -> None:
        self._diagnostics = diagnostics

    def scheduler_started(self) -> None:
        self._diagnostics.scheduler_started()

    def scheduler_stopped(self) -> None:
        self._diagnostics.scheduler_stopped()

    def scheduler_job_missed(
        self,
        *,
        scheduled_run_time: datetime,
    ) -> None:
        task_id = _task_id()
        if task_id is not None:
            self._diagnostics.scheduler_job_missed(
                task_id=task_id,
                scheduled_run_time=scheduled_run_time,
            )

    def scheduler_job_max_instances(
        self,
        *,
        scheduled_run_times: tuple[datetime, ...],
    ) -> None:
        task_id = _task_id()
        if task_id is not None:
            self._diagnostics.scheduler_job_max_instances(
                task_id=task_id,
                scheduled_run_times=scheduled_run_times,
            )

    def task_execution_started(self) -> None:
        task_id = _task_id()
        if task_id is not None:
            self._diagnostics.task_execution_started(task_id=task_id)

    def task_execution_succeeded(
        self,
        *,
        duration_seconds: float,
    ) -> None:
        task_id = _task_id()
        if task_id is not None:
            self._diagnostics.task_execution_succeeded(
                task_id=task_id,
                duration_seconds=duration_seconds,
            )

    def task_execution_failed(
        self,
        *,
        duration_seconds: float,
        exception: Exception,
    ) -> None:
        task_id = _task_id()
        if task_id is not None:
            self._diagnostics.task_execution_failed(
                task_id=task_id,
                duration_seconds=duration_seconds,
                exception=exception,
            )

    def task_execution_cancelled(
        self,
        *,
        duration_seconds: float,
    ) -> None:
        task_id = _task_id()
        if task_id is not None:
            self._diagnostics.task_execution_cancelled(
                task_id=task_id,
                duration_seconds=duration_seconds,
            )

    def task_scheduled(self) -> None:
        task_id = _task_id()
        if task_id is not None:
            self._diagnostics.task_scheduled(task_id=task_id)

    def task_removed(self) -> None:
        task_id = _task_id()
        if task_id is not None:
            self._diagnostics.task_removed(task_id=task_id)

    def task_paused(self) -> None:
        task_id = _task_id()
        if task_id is not None:
            self._diagnostics.task_paused(task_id=task_id)

    def task_resumed(self) -> None:
        task_id = _task_id()
        if task_id is not None:
            self._diagnostics.task_resumed(task_id=task_id)

    def task_run_requested(self) -> None:
        task_id = _task_id()
        if task_id is not None:
            self._diagnostics.task_run_requested(task_id=task_id)
