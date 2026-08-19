from __future__ import annotations
from dataclasses import replace
from datetime import datetime, timezone
from threading import RLock
from ..shared import get_observation_context
from .models import *
def _utc_now(): return datetime.now(timezone.utc)
class StatusService:
    """只维护当前状态，不承担历史日志和 Metrics。"""
    def __init__(self):
        self._lock=RLock(); self._runtime=RuntimeStatus(); self._scheduler=SchedulerStatus(); self._tasks:dict[int,TaskStatus]={}
    def runtime_started(self):
        ctx=get_observation_context(); now=_utc_now()
        with self._lock: self._runtime=replace(self._runtime,runtime_id=ctx.runtime_id,node_id=ctx.node_id,state=RuntimeState.RUNNING,started_at=now,stopped_at=None,last_error=None)
    def runtime_failed(self,exc:BaseException):
        with self._lock: self._runtime=replace(self._runtime,state=RuntimeState.FAILED,last_failure_at=_utc_now(),last_error=ErrorInfo.from_exception(exc))
    def scheduler_started(self):
        with self._lock: self._scheduler=replace(self._scheduler,running=True,last_started_at=_utc_now())
    def scheduler_stopped(self):
        with self._lock: self._scheduler=replace(self._scheduler,running=False,last_stopped_at=_utc_now())
    def scheduler_job_missed(self,task_id:int):
        with self._lock:
            self._scheduler=replace(self._scheduler,misfire_count=self._scheduler.misfire_count+1,last_issue_at=_utc_now()); t=self._task(task_id); self._tasks[task_id]=replace(t,misfire_count=t.misfire_count+1)
    def scheduler_job_max_instances(self,task_id:int,skipped:int):
        skipped=max(1,skipped)
        with self._lock:
            self._scheduler=replace(self._scheduler,max_instances_skip_count=self._scheduler.max_instances_skip_count+skipped,last_issue_at=_utc_now()); t=self._task(task_id); self._tasks[task_id]=replace(t,max_instances_skip_count=t.max_instances_skip_count+skipped)
    def task_scheduled(self,task_id:int): self._update(task_id,schedule_state=TaskScheduleState.SCHEDULED,last_scheduled_at=_utc_now())
    def task_removed(self,task_id:int): self._update(task_id,schedule_state=TaskScheduleState.REMOVED,last_removed_at=_utc_now())
    def task_paused(self,task_id:int): self._update(task_id,schedule_state=TaskScheduleState.PAUSED,last_paused_at=_utc_now())
    def task_resumed(self,task_id:int): self._update(task_id,schedule_state=TaskScheduleState.SCHEDULED,last_resumed_at=_utc_now())
    def task_run_requested(self,task_id:int): self._update(task_id,last_run_requested_at=_utc_now())
    def task_execution_started(self,task_id:int):
        with self._lock:
            t=self._task(task_id); self._tasks[task_id]=replace(t,execution_state=TaskExecutionState.RUNNING,last_started_at=_utc_now(),execution_count=t.execution_count+1)
    def task_execution_succeeded(self,task_id:int,duration:float):
        now=_utc_now()
        with self._lock:
            t=self._task(task_id); self._tasks[task_id]=replace(t,execution_state=TaskExecutionState.SUCCEEDED,last_finished_at=now,last_success_at=now,success_count=t.success_count+1,last_duration_seconds=duration,last_error=None)
    def task_execution_failed(self,task_id:int,duration:float,exc:BaseException):
        now=_utc_now()
        with self._lock:
            t=self._task(task_id); self._tasks[task_id]=replace(t,execution_state=TaskExecutionState.FAILED,last_finished_at=now,last_failure_at=now,failure_count=t.failure_count+1,last_duration_seconds=duration,last_error=ErrorInfo.from_exception(exc))
    def task_execution_cancelled(self,task_id:int,duration:float):
        now=_utc_now()
        with self._lock:
            t=self._task(task_id); self._tasks[task_id]=replace(t,execution_state=TaskExecutionState.CANCELLED,last_finished_at=now,last_cancelled_at=now,cancellation_count=t.cancellation_count+1,last_duration_seconds=duration)
    def runtime(self): return self._runtime
    def scheduler(self): return self._scheduler
    def task(self,task_id:int): return self._tasks.get(task_id)
    def tasks(self): return tuple(self._tasks.values())
    def _task(self,task_id:int): return self._tasks.get(task_id,TaskStatus(task_id=task_id))
    def _update(self,task_id:int,**changes):
        with self._lock: self._tasks[task_id]=replace(self._task(task_id),**changes)
