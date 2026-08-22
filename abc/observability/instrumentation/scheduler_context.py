"""Scheduler job context propagation helpers."""

from __future__ import annotations

from collections.abc import Callable

from ..context.propagation import capture_observation_context


def wrap_job(job: Callable):
    """Wrap scheduler job with captured observation context."""
    captured = capture_observation_context()

    def wrapper(*args, **kwargs):
        from ..context.manager import bind_observation_context

        with bind_observation_context(
            runtime=captured.runtime,
            request=captured.request,
            execution=captured.execution,
            trace=captured.trace,
        ):
            return job(*args, **kwargs)

    return wrapper
