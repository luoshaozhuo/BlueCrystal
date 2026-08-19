from __future__ import annotations
from typing import Protocol
import structlog
from ..metrics import SCHEDULER_TASK_OPERATIONS
from ..shared import bind_observation_context
from ..status import StatusService
from ..trace import TraceManager
logger=structlog.get_logger(__name__)
class TaskScheduler(Protocol):
    def schedule(self,task_id:int)->object: ...
    def remove(self,task_id:int)->object: ...
    def pause(self,task_id:int)->object: ...
    def resume(self,task_id:int)->object: ...
    def run_now(self,task_id:int)->object: ...
class ObservedTaskScheduler:
    def __init__(self,scheduler:TaskScheduler,*,status:StatusService,trace:TraceManager): self._scheduler=scheduler; self._status=status; self._trace=trace
    def schedule(self,task_id:int): return self._call(task_id,"schedule",self._scheduler.schedule,self._status.task_scheduled)
    def remove(self,task_id:int): return self._call(task_id,"remove",self._scheduler.remove,self._status.task_removed)
    def pause(self,task_id:int): return self._call(task_id,"pause",self._scheduler.pause,self._status.task_paused)
    def resume(self,task_id:int): return self._call(task_id,"resume",self._scheduler.resume,self._status.task_resumed)
    def run_now(self,task_id:int): return self._call(task_id,"run_now",self._scheduler.run_now,self._status.task_run_requested)
    def _call(self,task_id:int,operation:str,action,update_status):
        with bind_observation_context(task_id=task_id,source="scheduler",operation=f"task.{operation}",target_type="task",target_id=str(task_id)):
            with self._trace.span(f"task_scheduler.{operation}",attributes={"bluecrystal.task.id":task_id}) as span:
                try: result=action(task_id)
                except Exception as exc:
                    logger.exception("scheduler_task_operation_failed",operation=operation,task_id=task_id)
                    if span.is_recording(): self._trace.record_exception(span,exc)
                    else: self._trace.representative_error(exc,operation=f"task_scheduler.{operation}")
                    raise
                update_status(task_id); SCHEDULER_TASK_OPERATIONS.labels(operation=operation).inc(); logger.info("scheduler_task_operation_succeeded",operation=operation,task_id=task_id); return result
def wrap_task_scheduler(scheduler:TaskScheduler,*,status:StatusService,trace:TraceManager)->ObservedTaskScheduler: return ObservedTaskScheduler(scheduler,status=status,trace=trace)
