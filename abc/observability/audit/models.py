"""审计领域数据模型。"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from types import MappingProxyType


class AuditResult(StrEnum):
    """审计操作结果。"""

    SUCCESS = "success"
    FAILURE = "failure"


@dataclass(frozen=True, slots=True)
class AuditRecord:
    """一条不可变审计记录，保存操作主体和关联链路。"""

    audit_id: str
    timestamp: datetime
    service_name: str | None
    service_instance_id: str | None
    request_id: str | None
    actor: str | None
    source: str
    operation: str
    target_type: str
    target_id: str | None
    result: AuditResult
    detail: Mapping[str, object] = field(
        default_factory=lambda: MappingProxyType({})
    )
    error_type: str | None = None
    error_message: str | None = None


@dataclass(frozen=True, slots=True)
class AuditQuery:
    """审计记录查询条件。"""

    operation: str | None = None
    target_type: str | None = None
    target_id: str | None = None
    actor: str | None = None
    result: AuditResult | None = None
    limit: int = 100

    def __post_init__(self) -> None:
        """限制单次读取量，避免无界审计查询占用内存。"""
        if self.limit <= 0:
            raise ValueError("audit query limit must be positive")


@dataclass(frozen=True, slots=True)
class AuditSpec:
    """声明式审计动作定义。"""

    operation: str
    target_type: str
    target_arg: str | None = None
    detail_args: tuple[str, ...] = ()
