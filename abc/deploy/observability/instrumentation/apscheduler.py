"""APScheduler 3.x 事件监听适配."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime

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
    """创建 APScheduler -> BlueCrystal Observability 的事件监听器.

    Task success/failure/duration 不在这里重复记录，而由 ``ObservedTaskRunner``
    负责。这里仅记录 Scheduler 自己才能可靠判断的事实，例如 misfire 和
    max_instances。
    """

    def listener(event: SchedulerEvent) -> None:
        if event.code == EVENT_SCHEDULER_STARTED:
            safe_observe(hooks.scheduler_started)
            return

        if event.code == EVENT_SCHEDULER_SHUTDOWN:
            safe_observe(hooks.scheduler_stopped)
            return

        if event.code == EVENT_JOB_MISSED:
            if not isinstance(event, JobExecutionEvent):
                return
            task_id = _parse_task_id(event.job_id, task_job_id_prefix)
            if task_id is None:
                return
            safe_observe(
                hooks.scheduler_job_missed,
                task_id=task_id,
                scheduled_run_time=event.scheduled_run_time,
            )
            return

        if event.code == EVENT_JOB_MAX_INSTANCES:
            if not isinstance(event, JobSubmissionEvent):
                return
            task_id = _parse_task_id(event.job_id, task_job_id_prefix)
            if task_id is None:
                return
            safe_observe(
                hooks.scheduler_job_max_instances,
                task_id=task_id,
                scheduled_run_times=tuple(event.scheduled_run_times),
            )

    return listener


def install_apscheduler_instrumentation(
    scheduler: BaseScheduler,
    hooks: InstrumentationHooks,
    *,
    task_job_id_prefix: str = DEFAULT_TASK_JOB_ID_PREFIX,
) -> APSchedulerListener:
    """把 Observability Listener 安装到 APScheduler 3.x 实例.

    返回 listener 便于测试或关闭阶段调用 ``remove_listener()``。
    """
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
    """移除之前安装的 APScheduler Listener."""
    scheduler.remove_listener(listener)


def _parse_task_id(job_id: str, prefix: str) -> int | None:
    """从 BlueCrystal 周期 Job ID 中解析 task_id."""
    if not job_id.startswith(prefix):
        return None

    raw = job_id.removeprefix(prefix)
    try:
        return int(raw)
    except ValueError:
        return None
