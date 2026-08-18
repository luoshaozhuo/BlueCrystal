"""Audit 调用上下文."""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Generator


@dataclass(frozen=True, slots=True)
class AuditContext:
    """当前管理调用中可传播的 Audit 上下文."""

    actor: str | None = None
    source: str = "unknown"


_EMPTY_AUDIT_CONTEXT = AuditContext()

_AUDIT_CONTEXT: ContextVar[AuditContext] = ContextVar(
    "bluecrystal_audit_context",
    default=_EMPTY_AUDIT_CONTEXT,
)


def get_audit_context() -> AuditContext:
    """取得当前 AuditContext."""

    return _AUDIT_CONTEXT.get()


@contextmanager
def bind_audit_context(
    *,
    actor: str | None = None,
    source: str = "unknown",
) -> Generator[AuditContext, None, None]:
    """在当前执行作用域绑定 actor/source，并在退出时恢复."""

    context = AuditContext(
        actor=actor,
        source=source,
    )
    token = _AUDIT_CONTEXT.set(context)

    try:
        yield context
    finally:
        _AUDIT_CONTEXT.reset(token)
