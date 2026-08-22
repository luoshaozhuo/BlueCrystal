"""APScheduler 3.x 技术事件可观测性适配。

负责将 Scheduler 生命周期和任务调度异常事件转换为状态、指标和日志。
该模块不承担任务调度策略。
"""

from __future__ import annotations

from collections.abc import Callable

import structlog
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

from ..metrics import (
    SCHEDULER_RUNNING,
    TASK_MAX_INSTANCE_SKIPS,
    TASK_MISFIRES,
)
from ..status import StatusService


DEFAULT_TASK_JOB_ID_PREFIX = "task:"
EVENT_MASK = (
    EVENT_SCHEDULER_STARTED
    | EVENT_SCHEDULER_SHUTDOWN
    | EVENT_JOB_MISSED
    | EVENT_JOB_MAX_INSTANCES
)
APSchedulerListener = Callable[[SchedulerEvent], None]

logger = structlog.get_logger(__name__)


def install_scheduler_observability(
    scheduler: BaseScheduler,
    *,
    status: StatusService,
    task_job_id_prefix: str = DEFAULT_TASK_JOB_ID_PREFIX,
) -> APSchedulerListener:
    """安装 APScheduler 技术事件 Listener。

    Args:
        scheduler: APScheduler 调度器实例。
        status: 当前状态服务。
        task_job_id_prefix: 用于从 Job ID 解析任务 ID 的前缀。

    Returns:
        已安装的 Listener，可用于外部保存或移除。
    """

    def listener(event: SchedulerEvent) -> None:
        if event.code == EVENT_SCHEDULER_STARTED:
            SCHEDULER_RUNNING.set(1)
            status.scheduler_started()
            logger.info("scheduler_started")
            return

        if event.code == EVENT_SCHEDULER_SHUTDOWN:
            SCHEDULER_RUNNING.set(0)
            status.scheduler_stopped()
            logger.info("scheduler_stopped")
            return

        if event.code == EVENT_JOB_MISSED and isinstance(event, JobExecutionEvent):
            task_id = _parse_task_id(event.job_id, task_job_id_prefix)
            if task_id is not None:
                TASK_MISFIRES.inc()
                status.scheduler_job_missed(task_id)
                logger.warning(
                    "scheduler_job_missed",
                    task_id=task_id,
                    scheduled_run_time=event.scheduled_run_time,
                )
            return

        if event.code == EVENT_JOB_MAX_INSTANCES and isinstance(
            event, JobSubmissionEvent
        ):
            task_id = _parse_task_id(event.job_id, task_job_id_prefix)
            if task_id is not None:
                skipped = max(1, len(event.scheduled_run_times))
                TASK_MAX_INSTANCE_SKIPS.inc(skipped)
                status.scheduler_job_max_instances(task_id, skipped)
                logger.warning(
                    "scheduler_job_max_instances",
                    task_id=task_id,
                    skipped=skipped,
                )

    scheduler.add_listener(listener, EVENT_MASK)
    return listener


def _parse_task_id(job_id: str, prefix: str) -> int | None:
    if not job_id.startswith(prefix):
        return None

    try:
        return int(job_id.removeprefix(prefix))
    except ValueError:
        return None


# Design note:
# Scheduler instrumentation observes scheduling events only.
# TaskRunner owns business execution exception handling.
