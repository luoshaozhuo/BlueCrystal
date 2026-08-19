"""TaskRunner 低侵入执行观测包装."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from time import perf_counter

from observability_reference.shared import bind_task_execution_context

from .hooks import InstrumentationHooks, safe_observe


TaskRunner = Callable[[int], Awaitable[None]]


class ObservedTaskRunner:
    """为真实 TaskRunner 建立 Task Context 并报告执行事实."""

    def __init__(
        self,
        runner: TaskRunner,
        hooks: InstrumentationHooks,
    ) -> None:
        self._runner = runner
        self._hooks = hooks

    async def __call__(self, task_id: int) -> None:
        with bind_task_execution_context(task_id):
            started_at = perf_counter()
            safe_observe(self._hooks.task_execution_started)

            try:
                await self._runner(task_id)
            except asyncio.CancelledError:
                safe_observe(
                    self._hooks.task_execution_cancelled,
                    duration_seconds=perf_counter() - started_at,
                )
                raise
            except Exception as exc:
                safe_observe(
                    self._hooks.task_execution_failed,
                    duration_seconds=perf_counter() - started_at,
                    exception=exc,
                )
                raise
            else:
                safe_observe(
                    self._hooks.task_execution_succeeded,
                    duration_seconds=perf_counter() - started_at,
                )


def instrument_task_runner(
    runner: TaskRunner,
    hooks: InstrumentationHooks,
) -> TaskRunner:
    return ObservedTaskRunner(runner, hooks)
