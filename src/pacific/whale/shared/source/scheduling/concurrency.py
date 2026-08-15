"""Worker-local read concurrency control for high-frequency source polling.

This module provides protocol-agnostic concurrency limiting for read operations
inside a single worker process and a single asyncio event loop. It is the
worker-local companion to :mod:`whale.shared.source.scheduling.polling` and is
intended to be shared by all source polling jobs owned by one runtime/worker.

Responsibilities:
- limit concurrent read operations within one event loop;
- expose lightweight counters for operational diagnostics;

Out of scope:
- protocol-specific reader behavior such as OPC UA retry logic;
- cross-process coordination or global concurrency control;
- APScheduler integration or any outer lifecycle orchestration.

Implementation notes:
- this limiter is worker-local and single-event-loop only;
- it does not implement cross-process concurrency control;
- to reduce fixed overhead on the high-frequency path, local counters are
  updated without an internal ``asyncio.Lock``;
- ``snapshot()`` and ``reset_counters()`` remain async for API compatibility.

Relationship to outer orchestration:
- APScheduler or another low-frequency orchestrator may start/stop/reload a
  SourceRuntime or worker, but it should not call this limiter directly;
- supervisor/runtime layers may shard work across processes, and each worker
  process can create its own shared limiter instance.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class ConcurrencySnapshot:
    """Current worker-local limiter counters.

    Attributes:
        max_concurrent: Configured maximum concurrent operations.
        active: Number of operations currently holding a slot.
        max_observed_active: Highest observed active count since creation or
            the last counter reset.
        total_started: Total operations that acquired a slot.
        total_finished: Total operations that released a slot.
    """

    max_concurrent: int
    active: int
    max_observed_active: int
    total_started: int
    total_finished: int


class ReadConcurrencyLimiter(Generic[T]):
    """Limit concurrent read operations inside one worker event loop.

    The limiter is protocol-agnostic and should be shared across all high-
    frequency polling jobs in one worker. It must not be owned by a single
    reader instance because that would hide queue contention from the runtime.

    Cross-process concurrency is intentionally out of scope. If a supervisor
    shards sources across multiple worker processes, each worker should create
    and own its own limiter instance. Because the limiter is worker-local and
    only used on one event loop, its local counters are updated directly
    without an internal ``asyncio.Lock`` to keep the hot path lean.

    Args:
        max_concurrent: Maximum number of concurrent operations allowed inside
            the local event loop.

    Raises:
        ValueError: If ``max_concurrent`` is not greater than zero.
    """

    def __init__(self, max_concurrent: int) -> None:
        if max_concurrent <= 0:
            raise ValueError("max_concurrent must be greater than 0")

        self._max_concurrent = max_concurrent
        self._semaphore = asyncio.Semaphore(max_concurrent)

        self._active = 0
        self._max_observed_active = 0
        self._total_started = 0
        self._total_finished = 0

    @property
    def max_concurrent(self) -> int:
        """Return the configured worker-local concurrency ceiling.

        Returns:
            Maximum concurrent operations allowed in this limiter.
        """

        return self._max_concurrent

    async def run(self, operation: Callable[[], Awaitable[T]]) -> T:
        """Run one async operation under the local concurrency limit.

        Args:
            operation: Zero-argument callable that creates the coroutine only
                after a semaphore slot is acquired.

        Returns:
            The operation result.
        """

        async with self._semaphore:
            self._on_acquire()
            try:
                return await operation()
            finally:
                self._on_release()

    async def snapshot(self) -> ConcurrencySnapshot:
        """Return current worker-local limiter counters.

        Returns:
            Immutable snapshot of local limiter counters.
        """
        return ConcurrencySnapshot(
            max_concurrent=self._max_concurrent,
            active=self._active,
            max_observed_active=self._max_observed_active,
            total_started=self._total_started,
            total_finished=self._total_finished,
        )

    async def reset_counters(self) -> None:
        """Reset observed counters while preserving current active slots.

        This method is useful for per-test or per-interval measurements in a
        long-lived worker.
        """
        self._max_observed_active = self._active
        self._total_started = 0
        self._total_finished = 0

    def _on_acquire(self) -> None:
        """Update local counters after one operation acquires a slot."""
        self._active += 1
        self._total_started += 1
        if self._active > self._max_observed_active:
            self._max_observed_active = self._active

    def _on_release(self) -> None:
        """Update local counters after one operation releases a slot."""
        self._active -= 1
        self._total_finished += 1
