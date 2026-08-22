"""asyncio task context propagation instrumentation."""

from __future__ import annotations

import asyncio
from collections.abc import Coroutine

from ..context.propagation import capture_observation_context


def create_observation_task(
    coro: Coroutine,
    *,
    name: str | None = None,
) -> asyncio.Task:
    """Create asyncio Task carrying current observation context.

    This is a lightweight adapter. The actual ContextVar propagation
    remains controlled by Python asyncio task context semantics.
    """
    captured = capture_observation_context()

    async def runner():
        from ..context.manager import bind_observation_context

        with bind_observation_context(
            runtime=captured.runtime,
            request=captured.request,
            execution=captured.execution,
            trace=captured.trace,
        ):
            return await coro

    return asyncio.create_task(
        runner(),
        name=name,
    )
