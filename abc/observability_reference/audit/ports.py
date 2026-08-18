"""Audit 输出端口."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from .models import AuditQuery, AuditRecord


@runtime_checkable
class AuditStore(Protocol):
    """Audit 持久化端口."""

    def append(self, record: AuditRecord) -> None:
        ...

    def query(self, query: AuditQuery) -> tuple[AuditRecord, ...]:
        ...

    def flush(self) -> None:
        ...

    def close(self) -> None:
        ...
