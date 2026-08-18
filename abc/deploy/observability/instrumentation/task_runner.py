"""TaskRunner 的低侵入观测包装."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from time import perf_counter

from deploy.observability.shared import bind_observation_context

from .hooks import InstrumentationHooks, safe_observe


TaskRunner = Callable[[int], Awaitable[None]]


class ObservedTaskRunner:
    """为真实 TaskRunner 增加执行观测，而不修改真实 Runner."""

    def __init__(
        self,
        runner: TaskRunner,
        hooks: InstrumentationHooks,
    ) -> None:
        self._runner = runner
        self._hooks = hooks

    async def __call__(self, task_id: int) -> None:
        """执行真实 Runner，并报告开始、结果和耗时."""
        with bind_observation_context(task_id=task_id):
            started_at = perf_counter()
            safe_observe(self._hooks.task_execution_started, task_id=task_id)

            try:
                await self._runner(task_id)
            except asyncio.CancelledError:
                duration = perf_counter() - started_at
                safe_observe(
                    self._hooks.task_execution_cancelled,
                    task_id=task_id,
                    duration_seconds=duration,
                )
                raise
            except Exception as exc:
                duration = perf_counter() - started_at
                safe_observe(
                    self._hooks.task_execution_failed,
                    task_id=task_id,
                    duration_seconds=duration,
                    exception=exc,
                )
                raise
            else:
                duration = perf_counter() - started_at
                safe_observe(
                    self._hooks.task_execution_succeeded,
                    task_id=task_id,
                    duration_seconds=duration,
                )


def instrument_task_runner(
    runner: TaskRunner,
    hooks: InstrumentationHooks,
) -> TaskRunner:
    """返回一个可直接交给现有 ``TaskScheduler`` 的观测版 Runner."""
    return ObservedTaskRunner(runner, hooks)
