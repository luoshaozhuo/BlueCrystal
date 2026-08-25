"""通用同步/异步 Worker 执行边界 instrumentation。

包装器只产生执行指标、span 和关联上下文，不接管 Worker 内部业务日志。
"""

from __future__ import annotations

import asyncio
import inspect
import logging
from collections.abc import Awaitable, Callable
from functools import wraps
from time import perf_counter
from typing import TYPE_CHECKING, ParamSpec, TypeVar, cast, overload
from uuid import uuid4

from opentelemetry.trace import Status, StatusCode

from ..context import bind_worker_context

if TYPE_CHECKING:
    from ..runtime import ObservabilityRuntime
    from ..status import WorkerStatusTracker

P = ParamSpec("P")
R = TypeVar("R")
_LOGGER = logging.getLogger(__name__)


def _record_execution_metrics(
    runtime: ObservabilityRuntime,
    name: str,
    result: str,
    duration: float,
) -> None:
    """尽力写入执行结果指标，backend 故障不得改变业务执行语义。"""
    if runtime.metrics is None:
        return
    try:
        runtime.metrics.worker_executions.labels(
            operation=name,
            result=result,
        ).inc()
        runtime.metrics.worker_duration.labels(
            operation=name,
            result=result,
        ).observe(duration)
    except Exception:
        # Metrics 是旁路观测能力，失败时记录诊断但不覆盖业务返回或异常。
        _LOGGER.exception(
            "failed to record worker execution metrics",
            extra={"worker_operation": name, "worker_result": result},
        )


def _increment_in_flight_metric(
    runtime: ObservabilityRuntime,
    name: str,
) -> bool:
    """尽力增加运行中指标，并返回是否需要执行对应递减。"""
    if runtime.metrics is None:
        return False
    try:
        runtime.metrics.worker_in_flight.labels(operation=name).inc()
    except Exception:
        # 指标故障不能阻止 Worker 执行；失败的增量也不能在结束时递减。
        _LOGGER.exception(
            "failed to increment worker in-flight metric",
            extra={"worker_operation": name},
        )
        return False
    return True


def _decrement_in_flight_metric(
    runtime: ObservabilityRuntime,
    name: str,
) -> None:
    """尽力回收已成功增加的运行中指标，不影响业务执行结果。"""
    if runtime.metrics is None:
        return
    try:
        runtime.metrics.worker_in_flight.labels(operation=name).dec()
    except Exception:
        # 结束阶段无法向调用方补救 Prometheus 状态，只记录诊断并保持业务语义。
        _LOGGER.exception(
            "failed to decrement worker in-flight metric",
            extra={"worker_operation": name},
        )


@overload
def wrap_worker(
    name: str,
    runner: Callable[P, Awaitable[R]],
    *,
    runtime: ObservabilityRuntime,
    status_tracker: WorkerStatusTracker | None = None,
) -> Callable[P, Awaitable[R]]:
    """声明异步 Worker 包装后的签名。"""
    ...


@overload
def wrap_worker(
    name: str,
    runner: Callable[P, R],
    *,
    runtime: ObservabilityRuntime,
    status_tracker: WorkerStatusTracker | None = None,
) -> Callable[P, R]:
    """声明同步 Worker 包装后的签名。"""
    ...


def wrap_worker(
    name: str,
    runner: Callable[P, R],
    *,
    runtime: ObservabilityRuntime,
    status_tracker: WorkerStatusTracker | None = None,
) -> Callable[P, R]:
    """包装 Worker 并保留同步/异步返回及异常、取消语义。"""
    if inspect.iscoroutinefunction(runner):
        async_runner = cast(Callable[P, Awaitable[R]], runner)

        @wraps(runner)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            """执行异步 Worker，并显式区分成功、失败与取消。"""
            execution_id = uuid4().hex
            started = perf_counter()
            if status_tracker is not None:
                status_tracker.worker_started(name)
            in_flight_metric_incremented = _increment_in_flight_metric(runtime, name)
            span_attributes = {"worker.operation": name}
            try:
                with bind_worker_context(
                    runtime_context=runtime.context,
                    execution_id=execution_id,
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
                if status_tracker is not None:
                    status_tracker.worker_finished(name, "cancelled")
                _record_execution_metrics(runtime, name, "cancelled", perf_counter() - started)
                raise
            except Exception:
                # 外层只负责结果指标，绝不转换或吞掉业务异常。
                if status_tracker is not None:
                    status_tracker.worker_finished(name, "failure")
                _record_execution_metrics(runtime, name, "failure", perf_counter() - started)
                raise
            else:
                if status_tracker is not None:
                    status_tracker.worker_finished(name, "success")
                _record_execution_metrics(runtime, name, "success", perf_counter() - started)
                return value
            finally:
                if in_flight_metric_incremented:
                    _decrement_in_flight_metric(runtime, name)

        return cast(Callable[P, R], async_wrapper)

    @wraps(runner)
    def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        """执行同步 Worker，并保持返回值和业务异常不变。"""
        execution_id = uuid4().hex
        started = perf_counter()
        if status_tracker is not None:
            status_tracker.worker_started(name)
        in_flight_metric_incremented = _increment_in_flight_metric(runtime, name)
        try:
            with bind_worker_context(
                runtime_context=runtime.context,
                execution_id=execution_id,
            ):
                if runtime.tracing is None:
                    value = runner(*args, **kwargs)
                else:
                    with runtime.tracing.span(
                        name, attributes={"worker.operation": name}
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
            if status_tracker is not None:
                status_tracker.worker_finished(name, "failure")
            _record_execution_metrics(runtime, name, "failure", perf_counter() - started)
            raise
        else:
            if status_tracker is not None:
                status_tracker.worker_finished(name, "success")
            _record_execution_metrics(runtime, name, "success", perf_counter() - started)
            return value
        finally:
            if in_flight_metric_incremented:
                _decrement_in_flight_metric(runtime, name)

    return sync_wrapper
