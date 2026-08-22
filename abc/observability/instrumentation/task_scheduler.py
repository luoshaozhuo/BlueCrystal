"""显式 scheduler 管理操作的 trace 与 audit 边界。

Listener 只能观察调度事实；本包装器补充“谁发起了什么管理操作”的语义。
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from contextlib import nullcontext
from typing import TYPE_CHECKING, ParamSpec, TypeVar

from opentelemetry.trace import Status, StatusCode

from ..context import bind_observation_context

if TYPE_CHECKING:
    from ..manager import ObservabilityRuntime

P = ParamSpec("P")
R = TypeVar("R")


def observe_scheduler_action(
    runtime: ObservabilityRuntime,
    *,
    operation: str,
    target_type: str,
    target_id: str | None,
    action: Callable[P, R],
    detail: Mapping[str, object] | None = None,
) -> Callable[P, R]:
    """包装显式调度管理操作，记录 span 和可选 Audit。

    原函数返回值与异常保持不变；Audit store 写入失败会向上传播，避免把
    需要审计的操作误报为成功。
    """

    def wrapped(*args: P.args, **kwargs: P.kwargs) -> R:
        """在统一 trace/audit 作用域中执行原调度管理操作。"""
        attributes: dict[str, object] = {
            "scheduler.operation": operation,
            "scheduler.target.type": target_type,
            "scheduler.target.id": target_id or "",
        }
        span_scope = (
            runtime.tracing.span(f"scheduler.{operation}", attributes=attributes)
            if runtime.tracing is not None
            else nullcontext(None)
        )
        with bind_observation_context(
            source="scheduler",
            attributes=attributes,
        ):
            with span_scope as span:
                try:
                    result = action(*args, **kwargs)
                except Exception as exc:
                    # 记录后重新抛出，保持调度管理操作的原始失败语义。
                    if span is not None:
                        span.record_exception(exc)
                        span.set_status(Status(StatusCode.ERROR, str(exc)))
                    if runtime.audit is not None:
                        runtime.audit.failure(
                            operation=operation,
                            target_type=target_type,
                            target_id=target_id,
                            detail=detail,
                            exception=exc,
                        )
                    raise
                if runtime.audit is not None:
                    runtime.audit.success(
                        operation=operation,
                        target_type=target_type,
                        target_id=target_id,
                        detail=detail,
                    )
                return result

    return wrapped
