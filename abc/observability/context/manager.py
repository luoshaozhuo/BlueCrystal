"""基于 ContextVar 的 token-safe 关联上下文作用域。"""

from __future__ import annotations

from collections.abc import Generator, Mapping
from contextlib import AbstractContextManager, contextmanager
from contextvars import ContextVar
from typing import Final, cast

from .models import ObservationContext

_EMPTY_CONTEXT: Final = ObservationContext()
_observation_context_var: ContextVar[ObservationContext] = ContextVar(
    "observability_context", default=_EMPTY_CONTEXT
)
_UNSET = object()


def get_observation_context() -> ObservationContext:
    """返回当前不可变关联上下文。"""
    return _observation_context_var.get()


def initialize_runtime_context(
    *, service_name: str, service_instance_id: str | None = None
) -> ObservationContext:
    """初始化当前执行流的服务级上下文。

    该函数用于 composition root；临时边界应使用
    ``bind_observation_context`` 以确保退出时恢复 token。
    """
    observation = ObservationContext(
        service_name=service_name,
        service_instance_id=service_instance_id,
    )
    _observation_context_var.set(observation)
    return observation


@contextmanager
def bind_observation_context(
    *,
    parent_context: ObservationContext | None = None,
    service_name: str | None | object = _UNSET,
    service_instance_id: str | None | object = _UNSET,
    request_id: str | None | object = _UNSET,
    correlation_id: str | None | object = _UNSET,
    actor: str | None | object = _UNSET,
    source: str | None | object = _UNSET,
    job_id: str | None | object = _UNSET,
    execution_id: str | None | object = _UNSET,
    attributes: Mapping[str, object] | object = _UNSET,
) -> Generator[ObservationContext, None, None]:
    """在当前或显式父上下文上绑定字段，并可靠恢复 ContextVar token。
    
    普通的同步调用链或同一个 asyncio Task 中，get_observation_context() 确实足够，
    能直接获得父 context。 增加 parent_context 是为了处理“执行载体发生切换”的情况：
    - BackgroundScheduler → ThreadPoolExecutor：新线程拿不到提交线程的 ContextVar
    - AsyncIOExecutor → run_in_executor()：工作线程也不能可靠继承调用方 context
    - Scheduler 延迟执行：执行 Job 时，原来的 FastAPI 请求作用域通常早已退出
    所以 Scheduler 注册 Job 时先保存当时的 context，Executor 执行时再显式恢复：
    """
    current = (
        parent_context
        if parent_context is not None
        else get_observation_context()
    )
    # _UNSET 的作用是“区分‘没传参数’和‘传了一个真实值’”。
    supplied = {
        "service_name": service_name,
        "service_instance_id": service_instance_id,
        "request_id": request_id,
        "correlation_id": correlation_id,
        "actor": actor,
        "source": source,
        "job_id": job_id,
        "execution_id": execution_id,
    }
    changes = {key: value for key, value in supplied.items() if value is not _UNSET}
    if attributes is not _UNSET:
        # 合并父上下文的 attributes 与新传入的 attributes。
        # 例如：
        # >>> parent = {"tenant_id": "t1", "region": "cn"}
        # >>> child = {"region": "us", "order_id": "O-99"}
        # >>> merged = {**parent, **child}
        # >>> print(merged)
        # >>> {'tenant_id': 't1', 'region': 'us', 'order_id': 'O-99'}
        changes["attributes"] = {
            **current.attributes,
            **dict(cast(Mapping[str, object], attributes)),
        }
    # 下面的 cast 不是为了业务逻辑，而是为了“让静态类型检查器接受”这个值的来源。
    # changes.get(...) 的返回值来自字典，字典的值类型通常被推断为更宽泛的 object | None
    updated = ObservationContext(
        service_name=cast(str | None, changes.get("service_name", current.service_name)),
        service_instance_id=cast(
            str | None,
            changes.get("service_instance_id", current.service_instance_id),
        ),
        request_id=cast(str | None, changes.get("request_id", current.request_id)),
        correlation_id=cast(
            str | None, changes.get("correlation_id", current.correlation_id)
        ),
        actor=cast(str | None, changes.get("actor", current.actor)),
        source=cast(str | None, changes.get("source", current.source)),
        job_id=cast(str | None, changes.get("job_id", current.job_id)),
        execution_id=cast(
            str | None, changes.get("execution_id", current.execution_id)
        ),
        attributes=cast(
            Mapping[str, object], changes.get("attributes", current.attributes)
        ),
    )
    token = _observation_context_var.set(updated)
    try:
        yield updated
    finally:
        _observation_context_var.reset(token)


def bind_request_context(
    *,
    runtime_context: ObservationContext,
    request_id: str | None = None,
    actor: str | None = None,
    correlation_id: str | None = None,
) -> AbstractContextManager[ObservationContext]:
    """创建 HTTP 或其他请求边界的关联作用域。"""
    return bind_observation_context(
        parent_context=runtime_context,
        request_id=request_id,
        correlation_id=correlation_id,
        actor=actor,
        source="http",
    )


def bind_worker_context(
    *,
    runtime_context: ObservationContext,
    execution_id: str,
) -> AbstractContextManager[ObservationContext]:
    """继承同一 Runtime 的当前上下文，并只补充 Worker 执行标识。"""
    return bind_observation_context(
        parent_context=resolve_parent_context(runtime_context),
        execution_id=execution_id,
        source="worker",
    )


def bind_scheduler_context(
    *,
    runtime_context: ObservationContext,
    operation: str,
    target_type: str,
    target_id: str | None,
    attributes: Mapping[str, object] | None = None,
) -> AbstractContextManager[ObservationContext]:
    """创建 Scheduler 管理操作的关联作用域，必要时补齐线程服务信息。"""
    return bind_observation_context(
        parent_context=resolve_parent_context(runtime_context),
        source="scheduler",
        attributes={
            "scheduler.operation": operation,
            "scheduler.target.type": target_type,
            "scheduler.target.id": target_id or "",
            **dict(attributes or {}),
        },
    )


def bind_scheduler_execution_context(
    *,
    parent_context: ObservationContext,
    job_id: str,
) -> AbstractContextManager[ObservationContext]:
    """在 Executor 的真实执行边界恢复调度上下文并绑定 Job ID。"""
    return bind_observation_context(
        parent_context=parent_context,
        source="scheduler",
        job_id=job_id,
        execution_id=None,
    )


def resolve_parent_context(runtime_context: ObservationContext) -> ObservationContext:
    """选择属于同一 Runtime 的当前上下文，否则回退到服务级基线。"""
    current = get_observation_context()
    if (
        current.service_name == runtime_context.service_name
        and current.service_instance_id == runtime_context.service_instance_id
    ):
        return current
    return runtime_context
