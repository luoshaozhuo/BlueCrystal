# mypy: disable-error-code="assignment,arg-type,misc"
"""Worker-local fixed-rate polling primitives for source acquisition.

This module provides the production worker-local polling kernel used by
runtime/worker layers. It intentionally keeps a narrow scope:

- run fixed-rate polling jobs on one asyncio event loop;
- apply an optional worker-local concurrency limiter;
- emit result/error events with per-tick timing diagnostics;
- maintain lightweight per-job counters when diagnostics are enabled.

Diagnostic experiment branches that previously lived in this module were
intentionally removed. Profile-only scheduler variants now stay outside the
production polling kernel.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Generic, TypeVar

from pacific.whale.shared.source.scheduling.concurrency import ReadConcurrencyLimiter

T = TypeVar("T")

OverrunPolicy = str
ResultHandler = Callable[["PollingResultEvent[T]"], Awaitable[None]]
ErrorHandler = Callable[["PollingErrorEvent"], Awaitable[None]]
_CallbackFactory = Callable[[], Awaitable[None]]
_EventSink = Callable[[object], None]


@dataclass(frozen=True, slots=True)
class PollingTickDiagnostics:
    """Per-tick internal scheduler timing checkpoints."""

    scheduled_at: float
    sleep_woke_at: float
    limiter_wait_start_at: float
    limiter_acquired_at: float
    operation_start_at: float
    operation_finished_at: float
    callback_enqueue_at: float
    scheduler_mode: str | None = None
    task_name: str | None = None
    scheduler_base_time: float | None = None
    first_run_at: float | None = None
    offset_seconds: float | None = None
    interval_seconds: float | None = None
    tick_index: int | None = None
    task_count: int | None = None
    relevant_task_names: tuple[str, ...] | None = None


@dataclass(frozen=True, slots=True)
class PollingTaskCreationDiagnostics:
    """One-time startup timing diagnostics for one polling job task."""

    job_id: str
    task_name: str
    scheduler_start_called_at: float | None
    scheduler_base_time: float | None
    task_create_start_at: float | None
    per_job_task_created_at: float | None
    all_tasks_created_at: float | None
    run_job_first_entered_at: float | None
    first_run_at: float | None
    first_scheduled_at: float | None
    first_sleep_delay_ms: float | None
    first_sleep_entered_at: float | None
    first_sleep_woke_at: float | None
    first_sleep_wake_lag_ms: float | None


@dataclass(slots=True)
class _MutablePollingTaskCreationDiagnostics:
    """Mutable startup timing accumulator for one polling job task."""

    job_id: str
    task_name: str
    scheduler_start_called_at: float | None = None
    scheduler_base_time: float | None = None
    task_create_start_at: float | None = None
    per_job_task_created_at: float | None = None
    all_tasks_created_at: float | None = None
    run_job_first_entered_at: float | None = None
    first_run_at: float | None = None
    first_scheduled_at: float | None = None
    first_sleep_delay_ms: float | None = None
    first_sleep_entered_at: float | None = None
    first_sleep_woke_at: float | None = None
    first_sleep_wake_lag_ms: float | None = None

    def reset_for_start(self) -> None:
        """Clear one-time task startup fields before a new scheduler start."""

        self.scheduler_start_called_at = None
        self.scheduler_base_time = None
        self.task_create_start_at = None
        self.per_job_task_created_at = None
        self.all_tasks_created_at = None
        self.run_job_first_entered_at = None
        self.first_run_at = None
        self.first_scheduled_at = None
        self.first_sleep_delay_ms = None
        self.first_sleep_entered_at = None
        self.first_sleep_woke_at = None
        self.first_sleep_wake_lag_ms = None

    def snapshot(self) -> PollingTaskCreationDiagnostics:
        """Return an immutable snapshot of one-time startup timing fields."""

        return PollingTaskCreationDiagnostics(
            job_id=self.job_id,
            task_name=self.task_name,
            scheduler_start_called_at=self.scheduler_start_called_at,
            scheduler_base_time=self.scheduler_base_time,
            task_create_start_at=self.task_create_start_at,
            per_job_task_created_at=self.per_job_task_created_at,
            all_tasks_created_at=self.all_tasks_created_at,
            run_job_first_entered_at=self.run_job_first_entered_at,
            first_run_at=self.first_run_at,
            first_scheduled_at=self.first_scheduled_at,
            first_sleep_delay_ms=self.first_sleep_delay_ms,
            first_sleep_entered_at=self.first_sleep_entered_at,
            first_sleep_woke_at=self.first_sleep_woke_at,
            first_sleep_wake_lag_ms=self.first_sleep_wake_lag_ms,
        )


@dataclass(frozen=True, slots=True)
class PollingResultEvent(Generic[T]):
    """Successful polling completion payload."""

    job_id: str
    scheduled_at: float
    started_at: float
    finished_at: float
    duration_ms: float
    scheduled_delay_ms: float
    result: T
    diagnostics: PollingTickDiagnostics | None = None


@dataclass(frozen=True, slots=True)
class PollingErrorEvent:
    """Failed polling completion payload."""

    job_id: str
    scheduled_at: float
    started_at: float
    finished_at: float
    duration_ms: float
    scheduled_delay_ms: float
    error_type: str
    error_message: str
    exception: BaseException
    diagnostics: PollingTickDiagnostics | None = None


@dataclass(frozen=True, slots=True)
class PollingJobSpec(Generic[T]):
    """Configuration for one worker-local polling job."""

    job_id: str
    interval_seconds: float
    operation: Callable[[], Awaitable[T]]
    on_result: ResultHandler[T]
    on_error: ErrorHandler
    offset_seconds: float = 0.0
    timeout_seconds: float | None = None
    overrun_policy: OverrunPolicy = "skip_missed"
    late_threshold_seconds: float = 0.0

    def __post_init__(self) -> None:
        """Validate worker-local polling job configuration."""

        if not self.job_id:
            raise ValueError("job_id must not be empty")
        if self.interval_seconds <= 0:
            raise ValueError("interval_seconds must be greater than 0")
        if self.offset_seconds < 0:
            raise ValueError("offset_seconds must be greater than or equal to 0")
        if self.timeout_seconds is not None and self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be greater than 0 when provided")
        if self.overrun_policy != "skip_missed":
            raise ValueError("overrun_policy must be 'skip_missed'")
        if self.late_threshold_seconds < 0:
            raise ValueError("late_threshold_seconds must be greater than or equal to 0")


@dataclass(frozen=True, slots=True)
class PollingJobStats:
    """Observed runtime counters for one worker-local polling job."""

    job_id: str
    success_count: int
    error_count: int
    timeout_count: int
    skipped_tick_count: int
    late_start_count: int
    overrun_count: int
    last_scheduled_at: float | None
    last_started_at: float | None
    last_finished_at: float | None
    last_duration_ms: float | None
    last_scheduled_delay_ms: float | None
    max_scheduled_delay_ms: float


@dataclass(slots=True)
class _MutablePollingJobStats:
    """Mutable stats accumulator for one worker-local job."""

    job_id: str
    success_count: int = 0
    error_count: int = 0
    timeout_count: int = 0
    skipped_tick_count: int = 0
    late_start_count: int = 0
    overrun_count: int = 0
    last_scheduled_at: float | None = None
    last_started_at: float | None = None
    last_finished_at: float | None = None
    last_duration_ms: float | None = None
    last_scheduled_delay_ms: float | None = None
    max_scheduled_delay_ms: float = 0.0

    def snapshot(self) -> PollingJobStats:
        """Return an immutable snapshot of accumulated job stats."""

        return PollingJobStats(
            job_id=self.job_id,
            success_count=self.success_count,
            error_count=self.error_count,
            timeout_count=self.timeout_count,
            skipped_tick_count=self.skipped_tick_count,
            late_start_count=self.late_start_count,
            overrun_count=self.overrun_count,
            last_scheduled_at=self.last_scheduled_at,
            last_started_at=self.last_started_at,
            last_finished_at=self.last_finished_at,
            last_duration_ms=self.last_duration_ms,
            last_scheduled_delay_ms=self.last_scheduled_delay_ms,
            max_scheduled_delay_ms=self.max_scheduled_delay_ms,
        )


class SourcePollingScheduler(Generic[T]):
    """Run worker-local fixed-rate polling jobs on one asyncio event loop."""

    def __init__(
        self,
        *,
        limiter: ReadConcurrencyLimiter[T] | None = None,
        diagnostics_enabled: bool = False,
    ) -> None:
        self._limiter = limiter
        self._diagnostics_enabled = diagnostics_enabled
        self._jobs: dict[str, PollingJobSpec[T]] = {}
        self._stats: dict[str, _MutablePollingJobStats] = {}
        self._tasks: dict[str, asyncio.Task[None]] = {}
        self._callback_queues: dict[str, asyncio.Queue[_CallbackFactory]] = {}
        self._callback_tasks: dict[str, asyncio.Task[None]] = {}
        self._callback_failures: list[BaseException] = []
        self._task_creation: dict[str, _MutablePollingTaskCreationDiagnostics] = {}
        self._event_sink: _EventSink | None = None
        self._base_time: float | None = None
        self._stop_event: asyncio.Event | None = None
        self._started = False

    def add_job(self, spec: PollingJobSpec[T]) -> None:
        """Register one polling job before the scheduler starts."""

        if self._started:
            raise RuntimeError("cannot add jobs after scheduler start")
        if spec.job_id in self._jobs:
            raise ValueError(f"duplicate job_id: {spec.job_id}")

        self._jobs[spec.job_id] = spec
        self._stats[spec.job_id] = _MutablePollingJobStats(job_id=spec.job_id)
        self._task_creation[spec.job_id] = _MutablePollingTaskCreationDiagnostics(
            job_id=spec.job_id,
            task_name=f"source-polling:{spec.job_id}",
        )

    async def start(self) -> None:
        """Start all registered polling jobs."""

        if self._started:
            return

        self._started = True
        self._stop_event = asyncio.Event()
        self._callback_failures.clear()
        self._callback_queues.clear()
        self._callback_tasks.clear()
        self._tasks.clear()

        loop = asyncio.get_running_loop()
        scheduler_start_called_at = loop.time()
        task_create_start_at = loop.time()
        self._base_time = loop.time()

        for diagnostics in self._task_creation.values():
            diagnostics.reset_for_start()
            diagnostics.scheduler_start_called_at = scheduler_start_called_at
            diagnostics.scheduler_base_time = self._base_time
            diagnostics.task_create_start_at = task_create_start_at

        self._callback_queues = {
            job_id: asyncio.Queue() for job_id in self._jobs
        }
        self._callback_tasks = {
            job_id: asyncio.create_task(
                self._run_callback_worker(job_id),
                name=f"source-polling-callback:{job_id}",
            )
            for job_id in self._jobs
        }

        for job_id, spec in self._jobs.items():
            task = asyncio.create_task(
                self._run_job(spec),
                name=f"source-polling:{job_id}",
            )
            self._tasks[job_id] = task
            self._task_creation[job_id].per_job_task_created_at = loop.time()

        all_tasks_created_at = loop.time()
        for diagnostics in self._task_creation.values():
            diagnostics.all_tasks_created_at = all_tasks_created_at

    async def stop(self) -> None:
        """Stop all running jobs and wait for task cancellation to settle."""

        if not self._started:
            return

        assert self._stop_event is not None
        self._stop_event.set()

        tasks = tuple(self._tasks.values())
        callback_tasks = tuple(self._callback_tasks.values())
        for task in tasks:
            task.cancel()
        for task in callback_tasks:
            task.cancel()

        all_tasks = tasks + callback_tasks
        if all_tasks:
            await asyncio.gather(*all_tasks, return_exceptions=True)

        self._tasks.clear()
        self._callback_tasks.clear()
        self._callback_queues.clear()
        self._base_time = None
        self._stop_event = None
        self._started = False

        if self._callback_failures:
            first_failure = self._callback_failures[0]
            self._callback_failures.clear()
            raise first_failure

    def job_stats(self) -> tuple[PollingJobStats, ...]:
        """Return stats snapshots for all registered jobs."""

        return tuple(self._stats[job_id].snapshot() for job_id in self._jobs)

    def _task_creation_snapshot(self) -> tuple[PollingTaskCreationDiagnostics, ...]:
        """Return startup timing snapshots in job registration order."""

        return tuple(self._task_creation[job_id].snapshot() for job_id in self._jobs)

    async def _run_job(self, spec: PollingJobSpec[T]) -> None:
        """Run one long-lived fixed-rate polling loop for a single job."""

        assert self._base_time is not None
        assert self._stop_event is not None

        loop = asyncio.get_running_loop()
        diagnostics = self._task_creation[spec.job_id]
        if diagnostics.run_job_first_entered_at is None:
            diagnostics.run_job_first_entered_at = loop.time()

        first_run_at = self._base_time + spec.offset_seconds
        tick_index = 0

        try:
            while not self._stop_event.is_set():
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

                await self._execute_job(
                    spec,
                    scheduled_at=scheduled_at,
                    sleep_woke_at=sleep_woke_at,
                    first_run_at=first_run_at,
                    tick_index=tick_index,
                )
                tick_index += 1

                if spec.overrun_policy != "skip_missed":
                    continue

                now = loop.time()
                next_scheduled_at = first_run_at + (tick_index * spec.interval_seconds)
                if next_scheduled_at >= now:
                    continue

                next_tick_index = int((now - first_run_at) // spec.interval_seconds) + 1
                skipped_tick_count = max(0, next_tick_index - tick_index)
                tick_index = max(tick_index, next_tick_index)
                if skipped_tick_count > 0:
                    self._record_skipped_ticks(spec.job_id, skipped_tick_count)
        except asyncio.CancelledError:
            raise

    async def _execute_job(
        self,
        spec: PollingJobSpec[T],
        *,
        scheduled_at: float,
        sleep_woke_at: float,
        first_run_at: float,
        tick_index: int,
    ) -> None:
        """Execute one polling tick and dispatch the appropriate callback."""

        loop = asyncio.get_running_loop()
        started_at: float | None = None
        limiter_wait_start_at: float | None = None
        limiter_acquired_at: float | None = None
        operation_finished_at: float | None = None

        def mark_started(actual_started_at: float) -> None:
            nonlocal started_at
            started_at = actual_started_at

        def mark_limiter_wait_start(started_wait_at: float) -> None:
            nonlocal limiter_wait_start_at
            limiter_wait_start_at = started_wait_at

        def mark_limiter_acquired(acquired_at: float) -> None:
            nonlocal limiter_acquired_at
            limiter_acquired_at = acquired_at

        def mark_operation_finished(finished_at: float) -> None:
            nonlocal operation_finished_at
            operation_finished_at = finished_at

        try:
            result = await self._run_operation(
                spec,
                on_limiter_wait_start=mark_limiter_wait_start,
                on_limiter_acquired=mark_limiter_acquired,
                on_operation_started=mark_started,
                on_operation_finished=mark_operation_finished,
            )
        except Exception as exc:
            actual_started_at = loop.time() if started_at is None else started_at
            finished_at = loop.time()
            actual_limiter_wait_start_at = (
                actual_started_at
                if limiter_wait_start_at is None
                else limiter_wait_start_at
            )
            actual_limiter_acquired_at = (
                actual_started_at
                if limiter_acquired_at is None
                else limiter_acquired_at
            )
            actual_operation_finished_at = (
                finished_at
                if operation_finished_at is None
                else operation_finished_at
            )
            scheduled_delay_ms = max(0.0, (actual_started_at - scheduled_at) * 1000.0)
            duration_ms = max(0.0, (finished_at - actual_started_at) * 1000.0)
            callback_enqueue_at = loop.time()
            diagnostics = self._build_tick_diagnostics(
                spec=spec,
                scheduled_at=scheduled_at,
                sleep_woke_at=sleep_woke_at,
                limiter_wait_start_at=actual_limiter_wait_start_at,
                limiter_acquired_at=actual_limiter_acquired_at,
                operation_start_at=actual_started_at,
                operation_finished_at=actual_operation_finished_at,
                callback_enqueue_at=callback_enqueue_at,
                first_run_at=first_run_at,
                tick_index=tick_index,
            )
            self._record_error(
                spec.job_id,
                scheduled_at=scheduled_at,
                started_at=actual_started_at,
                finished_at=finished_at,
                duration_ms=duration_ms,
                scheduled_delay_ms=scheduled_delay_ms,
                late_threshold_seconds=spec.late_threshold_seconds,
                is_timeout=isinstance(exc, asyncio.TimeoutError),
            )
            event = PollingErrorEvent(
                job_id=spec.job_id,
                scheduled_at=scheduled_at,
                started_at=actual_started_at,
                finished_at=finished_at,
                duration_ms=duration_ms,
                scheduled_delay_ms=scheduled_delay_ms,
                error_type=type(exc).__name__,
                error_message=str(exc),
                exception=exc,
                diagnostics=diagnostics,
            )
            self._emit_event_sink(event)
            await self._dispatch_error_callback(spec.job_id, spec.on_error, event)
            return

        actual_started_at = loop.time() if started_at is None else started_at
        finished_at = loop.time()
        actual_limiter_wait_start_at = (
            actual_started_at
            if limiter_wait_start_at is None
            else limiter_wait_start_at
        )
        actual_limiter_acquired_at = (
            actual_started_at
            if limiter_acquired_at is None
            else limiter_acquired_at
        )
        actual_operation_finished_at = (
            finished_at
            if operation_finished_at is None
            else operation_finished_at
        )
        scheduled_delay_ms = max(0.0, (actual_started_at - scheduled_at) * 1000.0)
        duration_ms = max(0.0, (finished_at - actual_started_at) * 1000.0)
        callback_enqueue_at = loop.time()
        diagnostics = self._build_tick_diagnostics(
            spec=spec,
            scheduled_at=scheduled_at,
            sleep_woke_at=sleep_woke_at,
            limiter_wait_start_at=actual_limiter_wait_start_at,
            limiter_acquired_at=actual_limiter_acquired_at,
            operation_start_at=actual_started_at,
            operation_finished_at=actual_operation_finished_at,
            callback_enqueue_at=callback_enqueue_at,
            first_run_at=first_run_at,
            tick_index=tick_index,
        )
        self._record_success(
            spec.job_id,
            scheduled_at=scheduled_at,
            started_at=actual_started_at,
            finished_at=finished_at,
            duration_ms=duration_ms,
            scheduled_delay_ms=scheduled_delay_ms,
            late_threshold_seconds=spec.late_threshold_seconds,
        )
        event = PollingResultEvent(
            job_id=spec.job_id,
            scheduled_at=scheduled_at,
            started_at=actual_started_at,
            finished_at=finished_at,
            duration_ms=duration_ms,
            scheduled_delay_ms=scheduled_delay_ms,
            result=result,
            diagnostics=diagnostics,
        )
        self._emit_event_sink(event)
        await self._dispatch_result_callback(spec.job_id, spec.on_result, event)

    async def _run_operation(
        self,
        spec: PollingJobSpec[T],
        *,
        on_limiter_wait_start: Callable[[float], None],
        on_limiter_acquired: Callable[[float], None],
        on_operation_started: Callable[[float], None],
        on_operation_finished: Callable[[float], None],
    ) -> T:
        """Run one polling operation with optional worker-local concurrency limiting."""

        loop = asyncio.get_running_loop()

        async def run_once() -> T:
            acquired_at = loop.time()
            on_limiter_acquired(acquired_at)
            operation_started_at = loop.time()
            on_operation_started(operation_started_at)
            try:
                if spec.timeout_seconds is None:
                    return await spec.operation()
                async with asyncio.timeout(spec.timeout_seconds):
                    return await spec.operation()
            finally:
                on_operation_finished(loop.time())

        on_limiter_wait_start(loop.time())
        if self._limiter is None:
            return await run_once()
        return await self._limiter.run(run_once)

    def _schedule_callback(self, job_id: str, callback_factory: _CallbackFactory) -> None:
        """Queue a callback without delaying the next scheduled tick."""

        queue = self._callback_queues[job_id]
        queue.put_nowait(callback_factory)

    def _emit_event_sink(self, event: object) -> None:
        """Publish one event to an optional diagnostics sink."""

        if self._event_sink is None:
            return
        self._event_sink(event)

    def _build_tick_diagnostics(
        self,
        *,
        spec: PollingJobSpec[T],
        scheduled_at: float,
        sleep_woke_at: float,
        limiter_wait_start_at: float,
        limiter_acquired_at: float,
        operation_start_at: float,
        operation_finished_at: float,
        callback_enqueue_at: float,
        first_run_at: float,
        tick_index: int,
    ) -> PollingTickDiagnostics:
        """Build per-tick diagnostics for runtime/profile inspection."""

        current_task = asyncio.current_task()
        return PollingTickDiagnostics(
            scheduled_at=scheduled_at,
            sleep_woke_at=sleep_woke_at,
            limiter_wait_start_at=limiter_wait_start_at,
            limiter_acquired_at=limiter_acquired_at,
            operation_start_at=operation_start_at,
            operation_finished_at=operation_finished_at,
            callback_enqueue_at=callback_enqueue_at,
            task_name=current_task.get_name() if current_task is not None else None,
            scheduler_base_time=self._base_time,
            first_run_at=first_run_at,
            offset_seconds=spec.offset_seconds,
            interval_seconds=spec.interval_seconds,
            tick_index=tick_index,
        )

    async def _dispatch_result_callback(
        self,
        job_id: str,
        callback: ResultHandler[T],
        event: PollingResultEvent[T],
    ) -> None:
        """Dispatch one result callback through the job-local callback queue."""

        self._schedule_callback(job_id, lambda event=event: callback(event))

    async def _dispatch_error_callback(
        self,
        job_id: str,
        callback: ErrorHandler,
        event: PollingErrorEvent,
    ) -> None:
        """Dispatch one error callback through the job-local callback queue."""

        self._schedule_callback(job_id, lambda event=event: callback(event))

    async def _run_callback_worker(self, job_id: str) -> None:
        """Drain one job-local callback queue in order."""

        queue = self._callback_queues[job_id]
        while True:
            callback_factory = await queue.get()
            try:
                await callback_factory()
            except Exception as exc:  # pragma: no cover - surfaced by stop()
                self._callback_failures.append(exc)
            finally:
                queue.task_done()

    def _record_success(
        self,
        job_id: str,
        *,
        scheduled_at: float,
        started_at: float,
        finished_at: float,
        duration_ms: float,
        scheduled_delay_ms: float,
        late_threshold_seconds: float,
    ) -> None:
        """Record timing and counter updates for a successful tick."""

        if not self._diagnostics_enabled:
            return

        stats = self._stats[job_id]
        stats.success_count += 1
        self._update_common_stats(
            stats,
            scheduled_at=scheduled_at,
            started_at=started_at,
            finished_at=finished_at,
            duration_ms=duration_ms,
            scheduled_delay_ms=scheduled_delay_ms,
            late_threshold_seconds=late_threshold_seconds,
        )

    def _record_error(
        self,
        job_id: str,
        *,
        scheduled_at: float,
        started_at: float,
        finished_at: float,
        duration_ms: float,
        scheduled_delay_ms: float,
        late_threshold_seconds: float,
        is_timeout: bool,
    ) -> None:
        """Record timing and counter updates for a failed tick."""

        if not self._diagnostics_enabled:
            return

        stats = self._stats[job_id]
        stats.error_count += 1
        if is_timeout:
            stats.timeout_count += 1
        self._update_common_stats(
            stats,
            scheduled_at=scheduled_at,
            started_at=started_at,
            finished_at=finished_at,
            duration_ms=duration_ms,
            scheduled_delay_ms=scheduled_delay_ms,
            late_threshold_seconds=late_threshold_seconds,
        )

    def _record_skipped_ticks(self, job_id: str, skipped_tick_count: int) -> None:
        """Record a local overrun event caused by missed fixed-rate ticks."""

        if not self._diagnostics_enabled:
            return

        stats = self._stats[job_id]
        stats.skipped_tick_count += skipped_tick_count
        stats.overrun_count += 1

    def _update_common_stats(
        self,
        stats: _MutablePollingJobStats,
        *,
        scheduled_at: float,
        started_at: float,
        finished_at: float,
        duration_ms: float,
        scheduled_delay_ms: float,
        late_threshold_seconds: float,
    ) -> None:
        """Apply shared timing updates for both successful and failed ticks."""

        stats.last_scheduled_at = scheduled_at
        stats.last_started_at = started_at
        stats.last_finished_at = finished_at
        stats.last_duration_ms = duration_ms
        stats.last_scheduled_delay_ms = scheduled_delay_ms
        stats.max_scheduled_delay_ms = max(stats.max_scheduled_delay_ms, scheduled_delay_ms)
        if scheduled_delay_ms > late_threshold_seconds * 1000.0:
            stats.late_start_count += 1
