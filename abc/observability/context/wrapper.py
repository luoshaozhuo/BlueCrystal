"""Unified callable propagation wrappers."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable

from .propagation_manager import PropagationManager


propagation_manager = PropagationManager()


def wrap_callable(
    func: Callable,
) -> Callable:
    """Wrap callable with captured observation context."""
    captured = propagation_manager.capture()

    def wrapper(*args, **kwargs):
        with propagation_manager.scope(captured):
            return func(*args, **kwargs)

    return wrapper


def create_task(
    coro: Awaitable,
    *,
    name: str | None = None,
) -> asyncio.Task:
    """Create asyncio task with observation propagation."""
    captured = propagation_manager.capture()

    async def runner():
        with propagation_manager.scope(captured):
            return await coro

    return asyncio.create_task(
        runner(),
        name=name,
    )
