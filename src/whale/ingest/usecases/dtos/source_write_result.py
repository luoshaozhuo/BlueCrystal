"""Source write result DTOs for the write/control use case."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(slots=True)
class SourceWriteItemResult:
    """描述一个点位写入结果。"""

    key: str
    """点位业务 key。"""

    node_id: str
    """协议层节点地址。"""

    ok: bool
    """写入是否成功。"""

    status_code: str | None = None
    """状态码，如 GOOD / BAD_*。"""

    error_message: str | None = None
    """失败时的错误消息。"""

    value_type: str | None = None
    """写入值类型。"""


@dataclass(slots=True)
class SourceWriteResult:
    """描述一次写入请求的完整结果。"""

    request_id: str
    """请求唯一标识，与 SourceWriteRequest.request_id 一致。"""

    dry_run: bool
    """是否仅模拟（dry_run）模式。"""

    success_count: int
    """成功写入数。"""

    failure_count: int
    """失败写入数。"""

    results: list[SourceWriteItemResult] = field(default_factory=list)
    """每个点位的详细写入结果。"""

    client_requested_at: datetime | None = None
    """客户端请求时间。"""

    client_completed_at: datetime | None = None
    """客户端完成时间。"""

    trace_id: str | None = None
    """追踪 ID，用于审计和日志关联。"""

    attributes: dict[str, object] = field(default_factory=dict)
    """扩展属性。"""
