"""Observability 关联上下文传播."""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, replace
from typing import Final, Generator
from uuid import uuid4


@dataclass(frozen=True, slots=True)
class ObservationContext:
    """一次运行链路中可传播的关联上下文.

    时间戳不属于传播上下文；每条 Log/Audit/Metric/Diagnostic 记录应在
    自己被创建时生成时间戳。
    """

    runtime_id: str | None = None
    request_id: str | None = None
    task_id: int | None = None
    connection_id: str | None = None
    node_id: str | None = None


_EMPTY_CONTEXT: Final = ObservationContext()
_CONTEXT: ContextVar[ObservationContext] = ContextVar(
    "bluecrystal_observation_context",
    default=_EMPTY_CONTEXT,
)
_UNSET: Final = object()


def new_runtime_id() -> str:
    """生成一次 Runtime 实例的唯一标识."""
    return uuid4().hex


def new_request_id() -> str:
    """生成一次 Management HTTP 请求的唯一标识."""
    return uuid4().hex


def get_observation_context() -> ObservationContext:
    """获取当前执行上下文的只读快照."""
    return _CONTEXT.get()


def initialize_runtime_context(
    *,
    runtime_id: str | None = None,
    node_id: str | None = None,
) -> ObservationContext:
    """初始化当前 Runtime 的基础上下文.

    应在 Composition Root / Runtime 启动阶段调用一次。子 asyncio Task 会按
    Python ``contextvars`` 规则继承当时的上下文；Request/Task 等更细粒度
    上下文再使用 ``bind_observation_context()`` 临时覆盖。
    """
    context = ObservationContext(
        runtime_id=runtime_id or new_runtime_id(),
        node_id=node_id,
    )
    _CONTEXT.set(context)
    return context


@contextmanager
def bind_observation_context(
    *,
    runtime_id: str | None | object = _UNSET,
    request_id: str | None | object = _UNSET,
    task_id: int | None | object = _UNSET,
    connection_id: str | None | object = _UNSET,
    node_id: str | None | object = _UNSET,
) -> Generator[ObservationContext, None, None]:
    """在当前调用链中临时绑定一组关联字段.

    未传入的字段保持原值；显式传入 ``None`` 表示在该局部上下文中清空字段。
    离开 ``with`` 作用域后自动恢复原上下文。
    """
    current = get_observation_context()
    updated = replace(
        current,
        runtime_id=current.runtime_id if runtime_id is _UNSET else runtime_id,
        request_id=current.request_id if request_id is _UNSET else request_id,
        task_id=current.task_id if task_id is _UNSET else task_id,
        connection_id=(
            current.connection_id if connection_id is _UNSET else connection_id
        ),
        node_id=current.node_id if node_id is _UNSET else node_id,
    )
    token = _CONTEXT.set(updated)
    try:
        yield updated
    finally:
        _CONTEXT.reset(token)
