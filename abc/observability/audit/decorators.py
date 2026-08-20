"""审计动作声明装饰器。"""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar, cast

from .models import AuditSpec


F = TypeVar("F", bound=Callable[..., object])
_ATTR = "__bluecrystal_audit_spec__"


def audit_action(
    *,
    operation: str,
    target_type: str,
    target_arg: str | None = None,
    detail_args: tuple[str, ...] = (),
) -> Callable[[F], F]:
    """为处理函数附加审计定义。

    Args:
        operation: 审计操作名称。
        target_type: 审计目标类型。
        target_arg: 从请求参数中获取目标 ID 的参数名。
        detail_args: 需要记录到审计详情的参数名集合。

    Returns:
        保持原函数类型不变的装饰器。

    Raises:
        ValueError: `operation` 或 `target_type` 为空时抛出。
    """
    spec = AuditSpec(
        operation.strip(),
        target_type.strip(),
        target_arg,
        detail_args,
    )
    if not spec.operation or not spec.target_type:
        raise ValueError("operation and target_type must not be empty")

    def decorator(func: F) -> F:
        setattr(func, _ATTR, spec)
        return func

    return decorator


def get_audit_spec(func: Callable[..., object]) -> AuditSpec | None:
    """读取函数上绑定的审计定义。

    Args:
        func: 待检查函数。

    Returns:
        已绑定的审计定义；未绑定时返回 `None`。
    """
    value = getattr(func, _ATTR, None)
    if value is None:
        return None
    return cast(AuditSpec, value)
