"""审计记录写入与查询服务。"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Protocol
from uuid import uuid4

from ..context import get_observation_context
from .models import AuditQuery, AuditRecord, AuditResult


class AuditStore(Protocol):
    """审计记录存储端口。"""

    def append(self, record: AuditRecord) -> None:
        """追加一条审计记录。"""
        ...

    def query(self, query: AuditQuery) -> tuple[AuditRecord, ...]:
        """按条件查询审计记录。"""
        ...


class AuditService:
    """统一构造、写入并查询审计记录。"""

    def __init__(self, store: AuditStore) -> None:
        self._store = store

    def success(
        self,
        *,
        operation: str,
        target_type: str,
        target_id: str | None,
        detail: Mapping[str, object] | None = None,
    ) -> AuditRecord:
        """记录成功审计事件。"""
        return self._write(
            AuditResult.SUCCESS,
            operation,
            target_type,
            target_id,
            detail,
            None,
        )

    def failure(
        self,
        *,
        operation: str,
        target_type: str,
        target_id: str | None,
        exception: BaseException,
        detail: Mapping[str, object] | None = None,
    ) -> AuditRecord:
        """记录失败审计事件。"""
        return self._write(
            AuditResult.FAILURE,
            operation,
            target_type,
            target_id,
            detail,
            exception,
        )

    def query(self, query: AuditQuery) -> tuple[AuditRecord, ...]:
        """查询审计记录。"""
        return self._store.query(query)

    def _write(
        self,
        result: AuditResult,
        operation: str,
        target_type: str,
        target_id: str | None,
        detail: Mapping[str, object] | None,
        exception: BaseException | None,
    ) -> AuditRecord:
        observation = get_observation_context()
        record = AuditRecord(
            audit_id=uuid4().hex,
            timestamp=datetime.now(timezone.utc),
            runtime_id=observation.runtime_id,
            node_id=observation.node_id,
            request_id=observation.request_id,
            actor=observation.actor,
            source=observation.source or "unknown",
            operation=operation,
            target_type=target_type,
            target_id=target_id,
            result=result,
            detail=MappingProxyType(dict(detail or {})),
            error_type=(
                type(exception).__qualname__ if exception is not None else None
            ),
            error_message=str(exception) if exception is not None else None,
        )
        self._store.append(record)
        return record
