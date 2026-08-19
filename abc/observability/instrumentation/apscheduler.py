"""与当前 main 一致：APScheduler 3.x 技术事件 Listener。"""
from __future__ import annotations
from collections.abc import Callable
import structlog
from apscheduler.events import EVENT_JOB_MAX_INSTANCES,EVENT_JOB_MISSED,EVENT_SCHEDULER_SHUTDOWN,EVENT_SCHEDULER_STARTED,JobExecutionEvent,JobSubmissionEvent,SchedulerEvent
from apscheduler.schedulers.base import BaseScheduler
from ..metrics import SCHEDULER_RUNNING,TASK_MAX_INSTANCE_SKIPS,TASK_MISFIRES
from ..status import StatusService
DEFAULT_TASK_JOB_ID_PREFIX="task:"; EVENT_MASK=EVENT_SCHEDULER_STARTED|EVENT_SCHEDULER_SHUTDOWN|EVENT_JOB_MISSED|EVENT_JOB_MAX_INSTANCES
logger=structlog.get_logger(__name__); APSchedulerListener=Callable[[SchedulerEvent],None]
def install_scheduler_observability(scheduler:BaseScheduler,*,status:StatusService,task_job_id_prefix:str=DEFAULT_TASK_JOB_ID_PREFIX)->APSchedulerListener:
    def listener(event:SchedulerEvent)->None:
        if event.code==EVENT_SCHEDULER_STARTED: SCHEDULER_RUNNING.set(1); status.scheduler_started(); logger.info("scheduler_started"); return
        if event.code==EVENT_SCHEDULER_SHUTDOWN: SCHEDULER_RUNNING.set(0); status.scheduler_stopped(); logger.info("scheduler_stopped"); return
        if event.code==EVENT_JOB_MISSED and isinstance(event,JobExecutionEvent):
            task_id=_parse_task_id(event.job_id,task_job_id_prefix)
            if task_id is not None: TASK_MISFIRES.inc(); status.scheduler_job_missed(task_id); logger.warning("scheduler_job_missed",task_id=task_id,scheduled_run_time=event.scheduled_run_time)
            return
        if event.code==EVENT_JOB_MAX_INSTANCES and isinstance(event,JobSubmissionEvent):
            task_id=_parse_task_id(event.job_id,task_job_id_prefix)
            if task_id is not None:
                skipped=max(1,len(event.scheduled_run_times)); TASK_MAX_INSTANCE_SKIPS.inc(skipped); status.scheduler_job_max_instances(task_id,skipped); logger.warning("scheduler_job_max_instances",task_id=task_id,skipped=skipped)
    scheduler.add_listener(listener,EVENT_MASK); return listener
def _parse_task_id(job_id:str,prefix:str)->int|None:
    if not job_id.startswith(prefix): return None
    try: return int(job_id.removeprefix(prefix))
    except ValueError: return None
