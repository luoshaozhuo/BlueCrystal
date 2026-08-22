"""ContextVar based observation context manager."""

from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import replace
from collections.abc import Generator
from typing import Final

from .models import (
    ObservationContext, RuntimeContext, RequestContext,
    ExecutionContext, TraceContext,
)

_EMPTY_CONTEXT: Final = ObservationContext()
_observation_context_var: ContextVar[ObservationContext] = ContextVar(
    "bluecrystal_observation_context", default=_EMPTY_CONTEXT
)


def get_observation_context() -> ObservationContext:
    return _observation_context_var.get()


def capture_observation_context() -> ObservationContext:
    return get_observation_context()


def initialize_runtime_context(*, runtime_id: str | None = None, node_id: str | None = None) -> ObservationContext:
    observation = replace(
        get_observation_context(),
        runtime=RuntimeContext(runtime_id, node_id),
    )
    _observation_context_var.set(observation)
    return observation


def _apply_changes(current: ObservationContext, changes: dict[str, object]) -> ObservationContext:
    result = current
    mapping = {
        "runtime": RuntimeContext,
        "request": RequestContext,
        "execution": ExecutionContext,
        "trace": TraceContext,
    }
    for key, value in changes.items():
        if key in mapping and isinstance(value, dict):
            nested = replace(getattr(result, key), **value)
            result = replace(result, **{key: nested})
        elif hasattr(result, key):
            result = replace(result, **{key: value})
        else:
            raise TypeError(f"unknown observation field: {key}")
    return result


@contextmanager
def bind_observation_context(**changes: object) -> Generator[ObservationContext, None, None]:
    updated = _apply_changes(get_observation_context(), changes)
    token = _observation_context_var.set(updated)
    try:
        yield updated
    finally:
        _observation_context_var.reset(token)


def bind_runtime_context(
    *,
    runtime_id: str | None = None,
    node_id: str | None = None,
):
    return bind_observation_context(
        runtime={"runtime_id": runtime_id, "node_id": node_id}
    )


def bind_request_context(
    *,
    request_id: str | None = None,
    actor: str | None = None,
):
    return bind_observation_context(
        request={"request_id": request_id, "actor": actor}
    )


def bind_execution_context(
    *,
    task_id: int | None = None,
    connection_id: str | None = None,
):
    return bind_observation_context(
        execution={
            "task_id": task_id,
            "connection_id": connection_id,
        }
    )


def bind_trace_context(
    *,
    force_sample: bool = False,
    trace_tags: dict[str, str] | None = None,
):
    return bind_observation_context(
        trace={
            "force_sample": force_sample,
            "trace_tags": trace_tags or {},
        }
    )
