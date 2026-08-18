"""Audit 数据模型."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from types import MappingProxyType
from typing import Mapping


class AuditResult(StrEnum):
    """管理操作最终结果."""

    SUCCESS = "success"
    FAILURE = "failure"


@dataclass(frozen=True, slots=True)
class AuditRecord:
    """一条不可变审计记录."""

    audit_id: str
    timestamp: datetime

    runtime_id: str | None
    node_id: str | None
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
    """Audit 查询条件."""

    start_time: datetime | None = None
    end_time: datetime | None = None

    actor: str | None = None
    source: str | None = None
    operation: str | None = None

    target_type: str | None = None
    target_id: str | None = None

    result: AuditResult | None = None
    request_id: str | None = None

    limit: int = 100


@dataclass(frozen=True, slots=True)
class AuditSpec:
    """声明式审计元数据.

    该对象只描述“这是什么管理操作”，不执行 Audit。
    成功/失败、actor、request_id、异常捕获和持久化由外层适配器完成。
    """

    operation: str
    target_type: str
    target_arg: str | None = None
    detail_args: tuple[str, ...] = ()
