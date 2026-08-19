"""APScheduler 3.x 技术事件监听适配."""

from __future__ import annotations

from collections.abc import Callable

from apscheduler.events import (
    EVENT_JOB_MAX_INSTANCES,
    EVENT_JOB_MISSED,
    EVENT_SCHEDULER_SHUTDOWN,
    EVENT_SCHEDULER_STARTED,
    JobExecutionEvent,
    JobSubmissionEvent,
    SchedulerEvent,
)
from apscheduler.schedulers.base import BaseScheduler

from observability_reference.shared import bind_scheduler_event_context

from .hooks import InstrumentationHooks, safe_observe


DEFAULT_TASK_JOB_ID_PREFIX = "task:"
APSCHEDULER_OBSERVABILITY_EVENT_MASK = (
    EVENT_SCHEDULER_STARTED
    | EVENT_SCHEDULER_SHUTDOWN
    | EVENT_JOB_MISSED
    | EVENT_JOB_MAX_INSTANCES
)

APSchedulerListener = Callable[[SchedulerEvent], None]


def create_apscheduler_listener(
    hooks: InstrumentationHooks,
    *,
    task_job_id_prefix: str = DEFAULT_TASK_JOB_ID_PREFIX,
) -> APSchedulerListener:
    """创建 APScheduler -> Observability Listener."""

    def listener(event: SchedulerEvent) -> None:
        if event.code == EVENT_SCHEDULER_STARTED:
            with bind_scheduler_event_context():
                safe_observe(hooks.scheduler_started)
            return

        if event.code == EVENT_SCHEDULER_SHUTDOWN:
            with bind_scheduler_event_context():
                safe_observe(hooks.scheduler_stopped)
            return

        if event.code == EVENT_JOB_MISSED:
            if not isinstance(event, JobExecutionEvent):
                return
            task_id = _parse_task_id(event.job_id, task_job_id_prefix)
            if task_id is None:
                return

            with bind_scheduler_event_context(task_id):
                safe_observe(
                    hooks.scheduler_job_missed,
                    scheduled_run_time=event.scheduled_run_time,
                )
            return

        if event.code == EVENT_JOB_MAX_INSTANCES:
            if not isinstance(event, JobSubmissionEvent):
                return
            task_id = _parse_task_id(event.job_id, task_job_id_prefix)
            if task_id is None:
                return

            with bind_scheduler_event_context(task_id):
                safe_observe(
                    hooks.scheduler_job_max_instances,
                    scheduled_run_times=tuple(event.scheduled_run_times),
                )

    return listener


def install_apscheduler_instrumentation(
    scheduler: BaseScheduler,
    hooks: InstrumentationHooks,
    *,
    task_job_id_prefix: str = DEFAULT_TASK_JOB_ID_PREFIX,
) -> APSchedulerListener:
    listener = create_apscheduler_listener(
        hooks,
        task_job_id_prefix=task_job_id_prefix,
    )
    scheduler.add_listener(listener, APSCHEDULER_OBSERVABILITY_EVENT_MASK)
    return listener


def uninstall_apscheduler_instrumentation(
    scheduler: BaseScheduler,
    listener: APSchedulerListener,
) -> None:
    scheduler.remove_listener(listener)


def _parse_task_id(job_id: str, prefix: str) -> int | None:
    if not job_id.startswith(prefix):
        return None

    try:
        return int(job_id.removeprefix(prefix))
    except ValueError:
        return None
