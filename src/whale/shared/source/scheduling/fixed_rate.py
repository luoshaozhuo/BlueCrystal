# mypy: disable-error-code="assignment,union-attr"
"""Diagnostic-only high-frequency fixed-rate scheduler.

This module exists only for historical profile comparisons.
It is not a production scheduler and it must not be used as an acceptance mode.
"""

from __future__ import annotations

import asyncio
import os
from collections.abc import Callable
from dataclasses import dataclass
from typing import Generic, TypeVar

from whale.shared.source.scheduling.concurrency import ReadConcurrencyLimiter
from whale.shared.source.scheduling.polling import (
    PollingErrorEvent,
    PollingJobSpec,
    PollingResultEvent,
    PollingTaskCreationDiagnostics,
    PollingTickDiagnostics,
    _MutablePollingTaskCreationDiagnostics,
)

T = TypeVar("T")
_EventSink = Callable[[object], None]


def _env_flag(name: str, default: bool) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() not in {"0", "false", "no", "off"}


@dataclass(frozen=True, slots=True)
class _FixedRateJob(Generic[T]):
    spec: PollingJobSpec[T]
    index: int


class HighFrequencyFixedRateScheduler(Generic[T]):
    """Run one task per job using a direct absolute fixed-rate loop."""

    def __init__(
        self,
        *,
        limiter: ReadConcurrencyLimiter[T] | None = None,
        base_time: float | None = None,
    ) -> None:
        self._limiter = limiter
        self._base_time = base_time
        self._jobs: list[_FixedRateJob[T]] = []
        self._tasks: dict[str, asyncio.Task[None]] = {}
        self._task_creation: dict[str, _MutablePollingTaskCreationDiagnostics] = {}
        self._event_sink: _EventSink | None = None
        self._structure_diagnostics_enabled = _env_flag(
            "SOURCE_SIM_PROFILE_PRINT_SCHEDULER_STRUCTURE",
            False,
        )
        self._started = False

    def add_job(self, spec: PollingJobSpec[T]) -> None:
        """Register one fixed-rate job before startup."""

        if self._started:
            raise RuntimeError("cannot add jobs after scheduler start")
        if spec.job_id in self._task_creation:
            raise ValueError(f"duplicate job_id: {spec.job_id}")

        self._jobs.append(_FixedRateJob(spec=spec, index=len(self._jobs)))
        self._task_creation[spec.job_id] = _MutablePollingTaskCreationDiagnostics(
            job_id=spec.job_id,
            task_name=f"high-frequency-fixed-rate:{spec.job_id}",
        )

    async def start(self) -> None:
        """Start all registered jobs."""

        if self._started:
            return
        self._started = True

        loop = asyncio.get_running_loop()
        start_called_at = loop.time()
        task_create_start_at = loop.time()
        if self._base_time is None:
            self._base_time = loop.time()

        self._tasks = {}
        for diagnostics in self._task_creation.values():
            diagnostics.reset_for_start()
            diagnostics.scheduler_start_called_at = start_called_at
            diagnostics.scheduler_base_time = self._base_time
            diagnostics.task_create_start_at = task_create_start_at

        for job in self._jobs:
            task = asyncio.create_task(
                self._run_job(job.spec),
                name=f"high-frequency-fixed-rate:{job.spec.job_id}",
            )
            self._tasks[job.spec.job_id] = task
            self._task_creation[job.spec.job_id].per_job_task_created_at = loop.time()

        all_tasks_created_at = loop.time()
        for diagnostics in self._task_creation.values():
            diagnostics.all_tasks_created_at = all_tasks_created_at

    async def stop(self) -> None:
        """Cancel running tasks and wait for cleanup."""

        if not self._started:
            return

        tasks = tuple(self._tasks.values())
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        self._tasks.clear()
        self._started = False

    def task_creation_snapshot(self) -> tuple[PollingTaskCreationDiagnostics, ...]:
        """Return immutable startup timing snapshots in job registration order."""

        return tuple(
            self._task_creation[job.spec.job_id].snapshot()
            for job in self._jobs
        )

    async def _run_job(self, spec: PollingJobSpec[T]) -> None:
        assert self._base_time is not None

        loop = asyncio.get_running_loop()
        diagnostics = self._task_creation[spec.job_id]
        if diagnostics.run_job_first_entered_at is None:
            diagnostics.run_job_first_entered_at = loop.time()

        first_run_at = self._base_time + spec.offset_seconds
        tick_index = 0

        try:
            while True:
                scheduled_at = first_run_at + (tick_index * spec.interval_seconds)
                delay_seconds = scheduled_at - loop.time()
                if tick_index == 0:
                    diagnostics.first_run_at = first_run_at
                    diagnostics.first_scheduled_at = scheduled_at
                    diagnostics.first_sleep_delay_ms = max(0.0, delay_seconds * 1000.0)
                    diagnostics.first_sleep_entered_at = loop.time()
                if delay_seconds > 0:
                    await asyncio.sleep(delay_seconds)
                sleep_woke_at = loop.time()
                if tick_index == 0:
                    diagnostics.first_sleep_woke_at = sleep_woke_at
                    diagnostics.first_sleep_wake_lag_ms = max(
                        0.0,
                        (sleep_woke_at - scheduled_at) * 1000.0,
                    )

                limiter_wait_start_at = loop.time()
                limiter_acquired_at: float | None = None
                operation_start_at: float | None = None
                operation_finished_at: float | None = None

                async def run_once() -> T:
                    nonlocal limiter_acquired_at
                    nonlocal operation_start_at
                    nonlocal operation_finished_at
                    limiter_acquired_at = loop.time()
                    operation_start_at = loop.time()
                    try:
                        if spec.timeout_seconds is None:
                            return await spec.operation()
                        async with asyncio.timeout(spec.timeout_seconds):
                            return await spec.operation()
                    finally:
                        operation_finished_at = loop.time()

                try:
                    if self._limiter is None:
                        result = await run_once()
                    else:
                        result = await self._limiter.run(run_once)
                except Exception as exc:
                    finished_at = loop.time()
                    actual_started_at = (
                        operation_start_at
                        if operation_start_at is not None
                        else (
                            limiter_acquired_at
                            if limiter_acquired_at is not None
                            else limiter_wait_start_at
                        )
                    )
                    event = PollingErrorEvent(
                        job_id=spec.job_id,
                        scheduled_at=scheduled_at,
                        started_at=actual_started_at,
                        finished_at=finished_at,
                        duration_ms=max(0.0, (finished_at - actual_started_at) * 1000.0),
                        scheduled_delay_ms=max(
                            0.0,
                            (actual_started_at - scheduled_at) * 1000.0,
                        ),
                        error_type=type(exc).__name__,
                        error_message=str(exc),
                        exception=exc,
                        diagnostics=self._build_diagnostics(
                            spec=spec,
                            scheduled_at=scheduled_at,
                            sleep_woke_at=sleep_woke_at,
                            limiter_wait_start_at=limiter_wait_start_at,
                            limiter_acquired_at=(
                                actual_started_at
                                if limiter_acquired_at is None
                                else limiter_acquired_at
                            ),
                            operation_start_at=actual_started_at,
                            operation_finished_at=(
                                finished_at
                                if operation_finished_at is None
                                else operation_finished_at
                            ),
                            tick_index=tick_index,
                            first_run_at=first_run_at,
                        ),
                    )
                    self._emit_event(event)
                    tick_index += 1
                    continue

                finished_at = loop.time()
                actual_started_at = (
                    operation_start_at
                    if operation_start_at is not None
                    else (
                        limiter_acquired_at
                        if limiter_acquired_at is not None
                        else limiter_wait_start_at
                    )
                )
                event = PollingResultEvent(
                    job_id=spec.job_id,
                    scheduled_at=scheduled_at,
                    started_at=actual_started_at,
                    finished_at=finished_at,
                    duration_ms=max(0.0, (finished_at - actual_started_at) * 1000.0),
                    scheduled_delay_ms=max(
                        0.0,
                        (actual_started_at - scheduled_at) * 1000.0,
                    ),
                    result=result,
                    diagnostics=self._build_diagnostics(
                        spec=spec,
                        scheduled_at=scheduled_at,
                        sleep_woke_at=sleep_woke_at,
                        limiter_wait_start_at=limiter_wait_start_at,
                        limiter_acquired_at=(
                            actual_started_at
                            if limiter_acquired_at is None
                            else limiter_acquired_at
                        ),
                        operation_start_at=actual_started_at,
                        operation_finished_at=(
                            finished_at
                            if operation_finished_at is None
                            else operation_finished_at
                        ),
                        tick_index=tick_index,
                        first_run_at=first_run_at,
                    ),
                )
                self._emit_event(event)
                tick_index += 1
        except asyncio.CancelledError:
            raise

    def _emit_event(self, event: object) -> None:
        if self._event_sink is None:
            return
        self._event_sink(event)

    def _build_diagnostics(
        self,
        *,
        spec: PollingJobSpec[T],
        scheduled_at: float,
        sleep_woke_at: float,
        limiter_wait_start_at: float,
        limiter_acquired_at: float,
        operation_start_at: float,
        operation_finished_at: float,
        tick_index: int,
        first_run_at: float,
    ) -> PollingTickDiagnostics:
        task_name = asyncio.current_task().get_name() if asyncio.current_task() is not None else None
        task_count: int | None = None
        relevant_task_names: tuple[str, ...] | None = None
        if self._structure_diagnostics_enabled:
            loop = asyncio.get_running_loop()
            all_tasks = asyncio.all_tasks(loop)
            relevant_task_names = tuple(
                sorted(
                    task.get_name()
                    for task in all_tasks
                    if task.get_name().startswith("high-frequency-fixed-rate:")
                )
            )
            task_count = len(all_tasks)
        return PollingTickDiagnostics(
            scheduled_at=scheduled_at,
            sleep_woke_at=sleep_woke_at,
            limiter_wait_start_at=limiter_wait_start_at,
            limiter_acquired_at=limiter_acquired_at,
            operation_start_at=operation_start_at,
            operation_finished_at=operation_finished_at,
            callback_enqueue_at=asyncio.get_running_loop().time(),
            scheduler_mode="high_frequency_fixed_rate",
            task_name=task_name,
            scheduler_base_time=self._base_time,
            first_run_at=first_run_at,
            offset_seconds=spec.offset_seconds,
            interval_seconds=spec.interval_seconds,
            tick_index=tick_index,
            task_count=task_count,
            relevant_task_names=relevant_task_names,
        )
