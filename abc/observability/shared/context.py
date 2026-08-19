"""Observability 关联上下文传播。"""
from __future__ import annotations
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, replace
from typing import Final, Generator
from uuid import uuid4

@dataclass(frozen=True, slots=True)
class ObservationContext:
    runtime_id: str | None = None
    request_id: str | None = None
    task_id: int | None = None
    connection_id: str | None = None
    node_id: str | None = None
    actor: str | None = None
    source: str | None = None
    operation: str | None = None
    target_type: str | None = None
    target_id: str | None = None
    force_trace: bool = False

_EMPTY_CONTEXT: Final = ObservationContext()
_CONTEXT: ContextVar[ObservationContext] = ContextVar("bluecrystal_observation_context", default=_EMPTY_CONTEXT)
_UNSET: Final = object()

def new_runtime_id() -> str: return uuid4().hex
def new_request_id() -> str: return uuid4().hex
def get_observation_context() -> ObservationContext: return _CONTEXT.get()

def initialize_runtime_context(*, runtime_id: str | None = None, node_id: str | None = None) -> ObservationContext:
    context = ObservationContext(runtime_id=runtime_id or new_runtime_id(), node_id=node_id)
    _CONTEXT.set(context)
    return context

@contextmanager
def bind_observation_context(**changes) -> Generator[ObservationContext, None, None]:
    current = get_observation_context()
    allowed = set(ObservationContext.__dataclass_fields__)
    unknown = set(changes) - allowed
    if unknown:
        raise TypeError(f"unknown observation context fields: {sorted(unknown)}")
    updated = replace(current, **changes)
    token = _CONTEXT.set(updated)
    try:
        yield updated
    finally:
        _CONTEXT.reset(token)
