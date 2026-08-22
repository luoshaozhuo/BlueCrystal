"""基于 ContextVar 的 token-safe 关联上下文作用域。"""

from __future__ import annotations

from collections.abc import Generator, Mapping
from contextlib import AbstractContextManager, contextmanager
from contextvars import ContextVar
from dataclasses import replace
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
    observation = replace(
        get_observation_context(),
        service_name=service_name,
        service_instance_id=service_instance_id,
    )
    _observation_context_var.set(observation)
    return observation


@contextmanager
def bind_observation_context(
    *,
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
    """临时绑定关联字段，并在异常或取消时可靠恢复父上下文。"""
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
        changes["attributes"] = {
            **get_observation_context().attributes,
            **dict(cast(Mapping[str, object], attributes)),
        }
    current = get_observation_context()
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
    request_id: str | None = None,
    actor: str | None = None,
    correlation_id: str | None = None,
) -> AbstractContextManager[ObservationContext]:
    """创建 HTTP 或其他请求边界的关联作用域。"""
    return bind_observation_context(
        request_id=request_id,
        correlation_id=correlation_id,
        actor=actor,
        source="http",
    )


def bind_execution_context(
    *,
    job_id: str | None = None,
    execution_id: str | None = None,
    attributes: Mapping[str, object] | None = None,
) -> AbstractContextManager[ObservationContext]:
    """创建 scheduler 或 worker 执行边界的关联作用域。"""
    return bind_observation_context(
        job_id=job_id,
        execution_id=execution_id,
        source="worker",
        attributes=attributes or {},
    )
