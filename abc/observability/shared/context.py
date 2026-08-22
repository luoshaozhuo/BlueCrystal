"""Observability 关联上下文传播。"""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, replace
from typing import Final
from uuid import uuid4


@dataclass(frozen=True, slots=True)
class ObservationContext:
    """一次运行链路中可传播的不可变关联上下文。"""

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
_OBSERVATION_VAR: ContextVar[ObservationContext] = ContextVar(
    "bluecrystal_observation_context",
    default=_EMPTY_CONTEXT,
)


def new_runtime_id() -> str:
    """生成新的运行实例 ID。"""
    return uuid4().hex


def new_request_id() -> str:
    """生成新的请求 ID。"""
    return uuid4().hex


def get_observation_context() -> ObservationContext:
    """获取当前执行上下文中的关联上下文。"""
    return _OBSERVATION_VAR.get()


def initialize_runtime_context(
    *,
    runtime_id: str | None = None,
    node_id: str | None = None,
) -> ObservationContext:
    """初始化当前运行实例的根关联上下文。

    Args:
        runtime_id: 可选运行实例 ID；未提供时自动生成。
        node_id: 可选节点 ID。

    Returns:
        初始化后的关联上下文。
    """
    observation = ObservationContext(
        runtime_id=runtime_id or new_runtime_id(),
        node_id=node_id,
    )
    _OBSERVATION_VAR.set(observation)
    return observation


@contextmanager
def bind_observation_context(
    **changes: object,
) -> Generator[ObservationContext, None, None]:
    """临时覆盖当前关联上下文字段。

    Args:
        **changes: 需要覆盖的 `ObservationContext` 字段。

    Yields:
        更新后的关联上下文。

    Raises:
        TypeError: 传入未知上下文字段时抛出。
    """
    current = get_observation_context()
    allowed = set(ObservationContext.__dataclass_fields__)
    unknown = set(changes) - allowed
    if unknown:
        raise TypeError(
            f"unknown observation context fields: {sorted(unknown)}"
        )

    updated = replace(current, **changes)
    token = _OBSERVATION_VAR.set(updated)
    try:
        yield updated
    finally:
        _OBSERVATION_VAR.reset(token)
