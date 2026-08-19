from __future__ import annotations
import asyncio
from collections.abc import Awaitable, Callable
from time import perf_counter
import structlog
from ..metrics import TASK_EXECUTION_DURATION,TASK_EXECUTIONS,TASK_EXECUTIONS_IN_FLIGHT
from ..shared import bind_observation_context
from ..status import StatusService
from ..trace import TraceManager
TaskRunner=Callable[[int],Awaitable[None]]; logger=structlog.get_logger(__name__)
class ObservedTaskRunner:
    def __init__(self,runner:TaskRunner,*,status:StatusService,trace:TraceManager): self._runner=runner; self._status=status; self._trace=trace
    async def __call__(self,task_id:int)->None:
        started=perf_counter()
        with bind_observation_context(request_id=None,task_id=task_id,actor=None,source="task",operation=None,target_type=None,target_id=None):
            TASK_EXECUTIONS_IN_FLIGHT.inc(); self._status.task_execution_started(task_id); logger.info("task_execution_started",task_id=task_id)
            result=None; duration=None
            with self._trace.span("task.execute",attributes={"bluecrystal.task.id":task_id}) as span:
                try: await self._runner(task_id)
                except asyncio.CancelledError:
                    duration=perf_counter()-started; result="cancelled"; self._status.task_execution_cancelled(task_id,duration); logger.warning("task_execution_cancelled",task_id=task_id,duration_seconds=duration); raise
                except Exception as exc:
                    duration=perf_counter()-started; result="failure"; self._status.task_execution_failed(task_id,duration,exc); logger.exception("task_execution_failed",task_id=task_id,duration_seconds=duration)
                    if span.is_recording(): self._trace.record_exception(span,exc)
                    else: self._trace.representative_error(exc,operation="task.execute")
                    raise
                else:
                    duration=perf_counter()-started; result="success"; self._status.task_execution_succeeded(task_id,duration); logger.info("task_execution_succeeded",task_id=task_id,duration_seconds=duration)
                finally:
                    TASK_EXECUTIONS_IN_FLIGHT.dec()
                    if result is not None and duration is not None:
                        TASK_EXECUTIONS.labels(result=result).inc(); TASK_EXECUTION_DURATION.labels(result=result).observe(duration)
def wrap_task_runner(runner:TaskRunner,*,status:StatusService,trace:TraceManager)->ObservedTaskRunner: return ObservedTaskRunner(runner,status=status,trace=trace)
