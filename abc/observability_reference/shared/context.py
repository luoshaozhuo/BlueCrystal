"""Observability 统一关联上下文传播."""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, replace
from typing import Final, Generator
from uuid import uuid4


@dataclass(frozen=True, slots=True)
class ObservationContext:
    """当前执行链路的关联上下文.

    只保存“当前是谁 / 当前处于什么执行边界”这类上下文信息。
    status_code、duration、exception、scheduled_run_time 等一次性事件载荷
    不属于 Context，应继续作为 Hook 参数传递。
    """

    # Runtime
    runtime_id: str | None = None
    node_id: str | None = None

    # HTTP Request
    request_id: str | None = None
    http_method: str | None = None
    http_path: str | None = None

    # Identity / source
    actor: str | None = None
    source: str | None = None

    # BlueCrystal execution subject
    task_id: int | None = None
    connection_id: str | None = None

    # Current management/audit operation
    operation: str | None = None
    target_type: str | None = None
    target_id: str | None = None


_EMPTY_CONTEXT: Final = ObservationContext()
_CONTEXT: ContextVar[ObservationContext] = ContextVar(
    "bluecrystal_observation_context",
    default=_EMPTY_CONTEXT,
)
_UNSET: Final = object()


def new_runtime_id() -> str:
    """生成一次 Runtime 实例标识."""

    return uuid4().hex


def new_request_id() -> str:
    """生成一次 HTTP Request 标识."""

    return uuid4().hex


def get_observation_context() -> ObservationContext:
    """取得当前执行上下文的不可变快照."""

    return _CONTEXT.get()


def initialize_runtime_context(
    *,
    runtime_id: str | None = None,
    node_id: str | None = None,
) -> ObservationContext:
    """初始化 Runtime 基础上下文.

    仅在 Composition Root / Runtime 启动阶段调用一次。
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
    node_id: str | None | object = _UNSET,
    request_id: str | None | object = _UNSET,
    http_method: str | None | object = _UNSET,
    http_path: str | None | object = _UNSET,
    actor: str | None | object = _UNSET,
    source: str | None | object = _UNSET,
    task_id: int | None | object = _UNSET,
    connection_id: str | None | object = _UNSET,
    operation: str | None | object = _UNSET,
    target_type: str | None | object = _UNSET,
    target_id: str | None | object = _UNSET,
) -> Generator[ObservationContext, None, None]:
    """底层通用 Context 绑定器.

    未传入字段保持原值；显式传 ``None`` 表示清空。
    业务代码原则上不直接调用本函数，应优先使用下面的语义化边界绑定器。
    """

    current = get_observation_context()
    updated = replace(
        current,
        runtime_id=current.runtime_id if runtime_id is _UNSET else runtime_id,
        node_id=current.node_id if node_id is _UNSET else node_id,
        request_id=current.request_id if request_id is _UNSET else request_id,
        http_method=current.http_method if http_method is _UNSET else http_method,
        http_path=current.http_path if http_path is _UNSET else http_path,
        actor=current.actor if actor is _UNSET else actor,
        source=current.source if source is _UNSET else source,
        task_id=current.task_id if task_id is _UNSET else task_id,
        connection_id=(
            current.connection_id if connection_id is _UNSET else connection_id
        ),
        operation=current.operation if operation is _UNSET else operation,
        target_type=current.target_type if target_type is _UNSET else target_type,
        target_id=current.target_id if target_id is _UNSET else target_id,
    )

    token = _CONTEXT.set(updated)
    try:
        yield updated
    finally:
        _CONTEXT.reset(token)


@contextmanager
def bind_request_context(
    *,
    request_id: str,
    method: str,
    path: str,
    actor: str | None = None,
    source: str = "http",
) -> Generator[ObservationContext, None, None]:
    """建立 HTTP Request 边界.

    HTTP 请求是新的顶层请求作用域，因此主动清除 Task、Connection 和
    管理操作字段，避免异步 Context 意外继承产生串链。
    """

    with bind_observation_context(
        request_id=request_id,
        http_method=method,
        http_path=path,
        actor=actor,
        source=source,
        task_id=None,
        connection_id=None,
        operation=None,
        target_type=None,
        target_id=None,
    ) as context:
        yield context


@contextmanager
def bind_task_execution_context(
    task_id: int,
) -> Generator[ObservationContext, None, None]:
    """建立真正的 Task Execution 边界.

    Task 的执行生命周期独立于触发它的 HTTP 请求，因此清除 Request、
    actor/source 与 Audit operation，只保留 Runtime / Node。
    """

    with bind_observation_context(
        request_id=None,
        http_method=None,
        http_path=None,
        actor=None,
        source="scheduler",
        task_id=task_id,
        connection_id=None,
        operation=None,
        target_type=None,
        target_id=None,
    ) as context:
        yield context


@contextmanager
def bind_task_operation_context(
    task_id: int,
) -> Generator[ObservationContext, None, None]:
    """在当前上层作用域中临时指定被操作的 Task.

    该函数用于 pause/resume/run_now 等管理语义，保留当前 request_id、
    actor/source，以便 Log/Audit 与原 HTTP 请求关联。
    """

    with bind_observation_context(
        task_id=task_id,
    ) as context:
        yield context


@contextmanager
def bind_scheduler_event_context(
    task_id: int | None = None,
) -> Generator[ObservationContext, None, None]:
    """建立 APScheduler Listener 技术事件边界."""

    with bind_observation_context(
        request_id=None,
        http_method=None,
        http_path=None,
        actor=None,
        source="scheduler",
        task_id=task_id,
        connection_id=None,
        operation=None,
        target_type=None,
        target_id=None,
    ) as context:
        yield context


@contextmanager
def bind_connection_context(
    connection_id: str,
) -> Generator[ObservationContext, None, None]:
    """在当前 Task/Runtime 上下文中绑定 Connection."""

    with bind_observation_context(
        connection_id=connection_id,
    ) as context:
        yield context


@contextmanager
def bind_operation_context(
    *,
    operation: str,
    target_type: str,
    target_id: str | None,
) -> Generator[ObservationContext, None, None]:
    """建立一次管理操作 / Audit 语义边界.

    保留当前 HTTP request、actor/source，同时写入 operation/target。
    若目标是 Task 且 target_id 可解析为整数，同时绑定 task_id，使同一管理
    操作产生的 Logs/Metrics/Diagnostics 能直接取得当前 Task。
    """

    task_id: int | None | object = _UNSET
    if target_type == "task" and target_id is not None:
        try:
            task_id = int(target_id)
        except ValueError:
            task_id = _UNSET

    with bind_observation_context(
        operation=operation,
        target_type=target_type,
        target_id=target_id,
        task_id=task_id,
    ) as context:
        yield context
