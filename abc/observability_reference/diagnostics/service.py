"""Diagnostics 当前状态服务."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone

from abc.observability_reference.shared import get_observation_context

from .models import (
    DiagnosticError,
    RuntimeDiagnostic,
    RuntimeDiagnosticState,
    SchedulerDiagnostic,
    TaskDiagnostic,
    TaskExecutionState,
    TaskScheduleState,
)
from .ports import DiagnosticStore


class DiagnosticService:
    """维护 Runtime/Scheduler/Task 的当前诊断投影."""

    def __init__(self, store: DiagnosticStore) -> None:
        self._store = store

    # Runtime ------------------------------------------------------------
    def runtime_starting(self) -> None:
        context = get_observation_context()
        current = self._store.get_runtime() or RuntimeDiagnostic()
        self._store.set_runtime(
            replace(
                current,
                runtime_id=context.runtime_id,
                node_id=context.node_id,
                state=RuntimeDiagnosticState.STARTING,
                stopped_at=None,
                last_error=None,
            )
        )

    def runtime_started(self) -> None:
        now = _utc_now()
        context = get_observation_context()
        current = self._store.get_runtime() or RuntimeDiagnostic()
        self._store.set_runtime(
            replace(
                current,
                runtime_id=context.runtime_id,
                node_id=context.node_id,
                state=RuntimeDiagnosticState.RUNNING,
                started_at=now,
                stopped_at=None,
                last_error=None,
            )
        )

    def runtime_stopping(self) -> None:
        current = self._store.get_runtime() or RuntimeDiagnostic()
        self._store.set_runtime(
            replace(current, state=RuntimeDiagnosticState.STOPPING)
        )

    def runtime_stopped(self) -> None:
        current = self._store.get_runtime() or RuntimeDiagnostic()
        self._store.set_runtime(
            replace(
                current,
                state=RuntimeDiagnosticState.STOPPED,
                stopped_at=_utc_now(),
            )
        )

    def runtime_failed(self, exception: BaseException) -> None:
        now = _utc_now()
        current = self._store.get_runtime() or RuntimeDiagnostic()
        self._store.set_runtime(
            replace(
                current,
                state=RuntimeDiagnosticState.FAILED,
                last_failure_at=now,
                last_error=DiagnosticError.from_exception(exception),
            )
        )

    # Scheduler ----------------------------------------------------------
    def scheduler_started(self) -> None:
        current = self._store.get_scheduler() or SchedulerDiagnostic()
        self._store.set_scheduler(
            replace(
                current,
                running=True,
                last_started_at=_utc_now(),
            )
        )

    def scheduler_stopped(self) -> None:
        current = self._store.get_scheduler() or SchedulerDiagnostic()
        self._store.set_scheduler(
            replace(
                current,
                running=False,
                last_stopped_at=_utc_now(),
            )
        )

    def scheduler_job_missed(
        self,
        *,
        task_id: int,
        scheduled_run_time: datetime,
    ) -> None:
        now = _utc_now()

        scheduler = self._store.get_scheduler() or SchedulerDiagnostic()
        self._store.set_scheduler(
            replace(
                scheduler,
                misfire_count=scheduler.misfire_count + 1,
                last_issue_at=now,
            )
        )

        task = self._task(task_id)
        self._store.set_task(
            replace(
                task,
                misfire_count=task.misfire_count + 1,
                last_missed_scheduled_at=scheduled_run_time,
            )
        )

    def scheduler_job_max_instances(
        self,
        *,
        task_id: int,
        scheduled_run_times: tuple[datetime, ...],
    ) -> None:
        now = _utc_now()
        skipped = max(1, len(scheduled_run_times))

        scheduler = self._store.get_scheduler() or SchedulerDiagnostic()
        self._store.set_scheduler(
            replace(
                scheduler,
                max_instances_skip_count=(
                    scheduler.max_instances_skip_count + skipped
                ),
                last_issue_at=now,
            )
        )

        task = self._task(task_id)
        self._store.set_task(
            replace(
                task,
                max_instances_skip_count=task.max_instances_skip_count + skipped,
            )
        )

    # Task scheduling ----------------------------------------------------
    def task_scheduled(self, *, task_id: int) -> None:
        task = self._task(task_id)
        self._store.set_task(
            replace(
                task,
                schedule_state=TaskScheduleState.SCHEDULED,
                last_scheduled_at=_utc_now(),
            )
        )

    def task_removed(self, *, task_id: int) -> None:
        task = self._task(task_id)
        self._store.set_task(
            replace(
                task,
                schedule_state=TaskScheduleState.REMOVED,
                last_removed_at=_utc_now(),
            )
        )

    def task_paused(self, *, task_id: int) -> None:
        task = self._task(task_id)
        self._store.set_task(
            replace(
                task,
                schedule_state=TaskScheduleState.PAUSED,
                last_paused_at=_utc_now(),
            )
        )

    def task_resumed(self, *, task_id: int) -> None:
        task = self._task(task_id)
        self._store.set_task(
            replace(
                task,
                schedule_state=TaskScheduleState.SCHEDULED,
                last_resumed_at=_utc_now(),
            )
        )

    def task_run_requested(self, *, task_id: int) -> None:
        task = self._task(task_id)
        self._store.set_task(
            replace(task, last_run_requested_at=_utc_now())
        )

    # Task execution -----------------------------------------------------
    def task_execution_started(self, *, task_id: int) -> None:
        now = _utc_now()
        task = self._task(task_id)
        self._store.set_task(
            replace(
                task,
                execution_state=TaskExecutionState.RUNNING,
                last_started_at=now,
                execution_count=task.execution_count + 1,
            )
        )

    def task_execution_succeeded(
        self,
        *,
        task_id: int,
        duration_seconds: float,
    ) -> None:
        now = _utc_now()
        task = self._task(task_id)
        self._store.set_task(
            replace(
                task,
                execution_state=TaskExecutionState.SUCCEEDED,
                last_finished_at=now,
                last_success_at=now,
                success_count=task.success_count + 1,
                last_duration_seconds=duration_seconds,
                last_error=None,
            )
        )

    def task_execution_failed(
        self,
        *,
        task_id: int,
        duration_seconds: float,
        exception: BaseException,
    ) -> None:
        now = _utc_now()
        task = self._task(task_id)
        self._store.set_task(
            replace(
                task,
                execution_state=TaskExecutionState.FAILED,
                last_finished_at=now,
                last_failure_at=now,
                failure_count=task.failure_count + 1,
                last_duration_seconds=duration_seconds,
                last_error=DiagnosticError.from_exception(exception),
            )
        )

    def task_execution_cancelled(
        self,
        *,
        task_id: int,
        duration_seconds: float,
    ) -> None:
        now = _utc_now()
        task = self._task(task_id)
        self._store.set_task(
            replace(
                task,
                execution_state=TaskExecutionState.CANCELLED,
                last_finished_at=now,
                last_cancelled_at=now,
                cancellation_count=task.cancellation_count + 1,
                last_duration_seconds=duration_seconds,
            )
        )

    # Query --------------------------------------------------------------
    def runtime(self) -> RuntimeDiagnostic | None:
        return self._store.get_runtime()

    def scheduler(self) -> SchedulerDiagnostic | None:
        return self._store.get_scheduler()

    def task(self, task_id: int) -> TaskDiagnostic | None:
        return self._store.get_task(task_id)

    def tasks(self) -> tuple[TaskDiagnostic, ...]:
        return self._store.list_tasks()

    def clear(self) -> None:
        self._store.clear()

    def _task(self, task_id: int) -> TaskDiagnostic:
        return self._store.get_task(task_id) or TaskDiagnostic(task_id=task_id)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)
