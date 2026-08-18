"""声明式 Audit 元数据."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeVar, cast

from .models import AuditSpec


F = TypeVar("F", bound=Callable[..., Any])

_AUDIT_SPEC_ATTRIBUTE = "__bluecrystal_audit_spec__"


def audit_action(
    *,
    operation: str,
    target_type: str,
    target_arg: str | None = None,
    detail_args: tuple[str, ...] = (),
) -> Callable[[F], F]:
    """声明一个函数对应的管理操作.

    本装饰器只附加 ``AuditSpec``，不包装函数、不捕获异常，也不写 Audit。
    因而业务函数的控制流不会被 Audit 逻辑侵入。

    FastAPI 示例::

        @app.post("/tasks/{task_id}/pause")
        @audit_action(
            operation="task.pause",
            target_type="task",
            target_arg="task_id",
        )
        async def pause_task(task_id: int):
            ...
    """

    spec = AuditSpec(
        operation=_required_text(operation, "operation"),
        target_type=_required_text(target_type, "target_type"),
        target_arg=_optional_text(target_arg),
        detail_args=tuple(detail_args),
    )

    def decorator(func: F) -> F:
        setattr(func, _AUDIT_SPEC_ATTRIBUTE, spec)
        return func

    return decorator


def get_audit_spec(func: Callable[..., Any]) -> AuditSpec | None:
    """读取函数上的声明式 AuditSpec."""

    value = getattr(func, _AUDIT_SPEC_ATTRIBUTE, None)
    if value is None:
        return None
    return cast(AuditSpec, value)


def _required_text(value: str, name: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError(f"{name} must not be empty")
    return value


def _optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value or None
