"""TaskScheduler 管理语义的低侵入 Observability Wrapper."""

from __future__ import annotations

from collections.abc import Protocol

from observability_reference.shared import bind_task_operation_context

from .hooks import InstrumentationHooks, safe_observe


class TaskSchedulerLike(Protocol):
    """BlueCrystal TaskScheduler 的最小公共行为协议."""

    @property
    def running(self) -> bool: ...

    def start(self) -> None: ...

    def stop(self) -> None: ...

    def schedule_interval(self, task_id: int, interval_ms: int): ...

    def remove(self, task_id: int) -> None: ...

    def pause(self, task_id: int): ...

    def resume(self, task_id: int): ...

    def run_now(self, task_id: int) -> None: ...

    def get(self, task_id: int): ...

    def list(self): ...


class ObservedTaskScheduler:
    """包装现有 TaskScheduler，并在动作成功后自动产生 Semantic Hook."""

    def __init__(
        self,
        scheduler: TaskSchedulerLike,
        hooks: InstrumentationHooks,
    ) -> None:
        self._scheduler = scheduler
        self._hooks = hooks

    @property
    def running(self) -> bool:
        return self._scheduler.running

    @property
    def raw_scheduler(self) -> TaskSchedulerLike:
        return self._scheduler

    def start(self) -> None:
        self._scheduler.start()

    def stop(self) -> None:
        self._scheduler.stop()

    def schedule_interval(self, task_id: int, interval_ms: int):
        result = self._scheduler.schedule_interval(task_id, interval_ms)
        with bind_task_operation_context(task_id):
            safe_observe(self._hooks.task_scheduled)
        return result

    def remove(self, task_id: int) -> None:
        self._scheduler.remove(task_id)
        with bind_task_operation_context(task_id):
            safe_observe(self._hooks.task_removed)

    def pause(self, task_id: int):
        result = self._scheduler.pause(task_id)
        with bind_task_operation_context(task_id):
            safe_observe(self._hooks.task_paused)
        return result

    def resume(self, task_id: int):
        result = self._scheduler.resume(task_id)
        with bind_task_operation_context(task_id):
            safe_observe(self._hooks.task_resumed)
        return result

    def run_now(self, task_id: int) -> None:
        self._scheduler.run_now(task_id)
        with bind_task_operation_context(task_id):
            safe_observe(self._hooks.task_run_requested)

    def get(self, task_id: int):
        return self._scheduler.get(task_id)

    def list(self):
        return self._scheduler.list()


def instrument_task_scheduler(
    scheduler: TaskSchedulerLike,
    hooks: InstrumentationHooks,
) -> ObservedTaskScheduler:
    return ObservedTaskScheduler(scheduler, hooks)
