"""Observation context propagation helpers."""

from __future__ import annotations

from collections.abc import Callable, Generator
from contextlib import contextmanager
from functools import wraps
from typing import TypeVar, cast

from .manager import (
    bind_observation_context,
    get_observation_context,
)
from .models import ObservationContext

T = TypeVar("T")


def capture_observation_context() -> ObservationContext:
    """Capture current observation context."""
    return get_observation_context()


@contextmanager
def restore_observation_context(
    observation: ObservationContext,
) -> Generator[None, None, None]:
    """Temporarily restore observation context."""
    with bind_observation_context(
        runtime=observation.runtime,
        request=observation.request,
        execution=observation.execution,
        trace=observation.trace,
    ):
        yield


def wrap_callable(
    func: Callable[..., T],
) -> Callable[..., T]:
    """Wrap callable with observation context."""
    captured = capture_observation_context()

    @wraps(func)
    def wrapper(*args, **kwargs):
        with restore_observation_context(captured):
            return func(*args, **kwargs)

    return cast(Callable[..., T], wrapper)
