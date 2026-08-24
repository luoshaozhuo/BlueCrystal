"""通用同步/异步 Worker 执行边界 instrumentation。

包装器只产生执行指标、span 和关联上下文，不接管 Worker 内部业务日志。
"""

from __future__ import annotations

import asyncio
import inspect
from collections.abc import Awaitable, Callable, Mapping
from functools import wraps
from time import perf_counter
from typing import TYPE_CHECKING, ParamSpec, TypeVar, cast, overload
from uuid import uuid4

from opentelemetry.trace import Status, StatusCode

from ..context import bind_worker_context

if TYPE_CHECKING:
    from ..runtime import ObservabilityRuntime

P = ParamSpec("P")
R = TypeVar("R")
IdentityResolver = Callable[..., Mapping[str, object]]


def _identity(
    resolver: IdentityResolver | None,
    args: tuple[object, ...],
    kwargs: dict[str, object],
) -> tuple[str | None, str, Mapping[str, object]]:
    """将业务 resolver 结果收敛为通用 job/execution/attributes。"""
    resolved = resolver(*args, **kwargs) if resolver else {}
    job_id = resolved.get("job_id")
    execution_id = resolved.get("execution_id") or uuid4().hex
    attributes = resolved.get("attributes", {})
    if job_id is not None and not isinstance(job_id, str):
        raise TypeError("worker resolver job_id must be str or None")
    if not isinstance(execution_id, str):
        raise TypeError("worker resolver execution_id must be str")
    if not isinstance(attributes, Mapping):
        raise TypeError("worker resolver attributes must be a mapping")
    return job_id, execution_id, cast(Mapping[str, object], attributes)


def _record_execution_metrics(
    runtime: ObservabilityRuntime,
    name: str,
    result: str,
    duration: float,
) -> None:
    """写入可选 Metrics backend；关闭 metrics 时自然降级。"""
    if runtime.metrics is None:
        return
    runtime.metrics.worker_executions.labels(operation=name, result=result).inc()
    runtime.metrics.worker_duration.labels(operation=name, result=result).observe(duration)


@overload
def wrap_worker(
    name: str,
    runner: Callable[P, Awaitable[R]],
    *,
    runtime: ObservabilityRuntime,
    resolver: IdentityResolver | None = None,
) -> Callable[P, Awaitable[R]]:
    """声明异步 Worker 包装后的签名。"""
    ...


@overload
def wrap_worker(
    name: str,
    runner: Callable[P, R],
    *,
    runtime: ObservabilityRuntime,
    resolver: IdentityResolver | None = None,
) -> Callable[P, R]:
    """声明同步 Worker 包装后的签名。"""
    ...


def wrap_worker(
    name: str,
    runner: Callable[P, R],
    *,
    runtime: ObservabilityRuntime,
    resolver: IdentityResolver | None = None,
) -> Callable[P, R]:
    """包装 Worker 并保留同步/异步返回及异常、取消语义。"""
    if inspect.iscoroutinefunction(runner):
        async_runner = cast(Callable[P, Awaitable[R]], runner)

        @wraps(runner)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            """执行异步 Worker，并显式区分成功、失败与取消。"""
            job_id, execution_id, attributes = _identity(
                resolver, cast(tuple[object, ...], args), cast(dict[str, object], kwargs)
            )
            started = perf_counter()
            if runtime.metrics is not None:
                runtime.metrics.worker_in_flight.labels(operation=name).inc()
            span_attributes = {"worker.operation": name, **attributes}
            try:
                with bind_worker_context(
                    job_id=job_id,
                    execution_id=execution_id,
                    attributes=attributes,
                ):
                    if runtime.tracing is None:
                        value = await async_runner(*args, **kwargs)
                    else:
                        with runtime.tracing.span(name, attributes=span_attributes) as span:
                            try:
                                value = await async_runner(*args, **kwargs)
                            except asyncio.CancelledError:
                                span.set_status(Status(StatusCode.ERROR, "cancelled"))
                                raise
                            except Exception as exc:
                                # OTel 记录后重新抛出，业务异常类型和值保持不变。
                                span.record_exception(exc)
                                span.set_status(Status(StatusCode.ERROR, str(exc)))
                                raise
            except asyncio.CancelledError:
                _record_execution_metrics(runtime, name, "cancelled", perf_counter() - started)
                raise
            except Exception:
                # 外层只负责结果指标，绝不转换或吞掉业务异常。
                _record_execution_metrics(runtime, name, "failure", perf_counter() - started)
                raise
            else:
                _record_execution_metrics(runtime, name, "success", perf_counter() - started)
                return value
            finally:
                if runtime.metrics is not None:
                    runtime.metrics.worker_in_flight.labels(operation=name).dec()

        return cast(Callable[P, R], async_wrapper)

    @wraps(runner)
    def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        """执行同步 Worker，并保持返回值和业务异常不变。"""
        job_id, execution_id, attributes = _identity(
            resolver, cast(tuple[object, ...], args), cast(dict[str, object], kwargs)
        )
        started = perf_counter()
        if runtime.metrics is not None:
            runtime.metrics.worker_in_flight.labels(operation=name).inc()
        try:
            with bind_worker_context(
                job_id=job_id,
                execution_id=execution_id,
                attributes=attributes,
            ):
                if runtime.tracing is None:
                    value = runner(*args, **kwargs)
                else:
                    with runtime.tracing.span(
                        name, attributes={"worker.operation": name, **attributes}
                    ) as span:
                        try:
                            value = runner(*args, **kwargs)
                        except Exception as exc:
                            # OTel 记录后重新抛出，业务异常类型和值保持不变。
                            span.record_exception(exc)
                            span.set_status(Status(StatusCode.ERROR, str(exc)))
                            raise
        except Exception:
            # 外层只负责结果指标，绝不转换或吞掉业务异常。
            _record_execution_metrics(runtime, name, "failure", perf_counter() - started)
            raise
        else:
            _record_execution_metrics(runtime, name, "success", perf_counter() - started)
            return value
        finally:
            if runtime.metrics is not None:
                runtime.metrics.worker_in_flight.labels(operation=name).dec()

    return sync_wrapper
