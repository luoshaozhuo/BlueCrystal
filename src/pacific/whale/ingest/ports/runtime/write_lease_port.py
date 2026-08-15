"""ingest 运行时 write lease port。

负责 相关功能，包含并发模型、租约、fencing token、
异常传播和资源释放语义。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True, slots=True)
class WriteLeaseDecisionData:
    """写入租约守卫返回的结果。"""

    allowed: bool
    result: str
    reason_code: str | None
    fencing_token: int | None
    expires_at: datetime | None = None


class WriteLeasePort(Protocol):
    """使用专用租约保护真实的写入/控制执行。"""

    def acquire(
        self,
        *,
        resource_id: str,
        holder_key: str,
        requested_fencing_token: int | None = None,
    ) -> WriteLeaseDecisionData:
        """获取一个写入租约。"""

    def renew(self, *, resource_id: str, holder_key: str) -> WriteLeaseDecisionData:
        """续期一个写入租约。"""

    def validate(
        self,
        *,
        resource_id: str,
        holder_key: str,
        fencing_token: int,
    ) -> WriteLeaseDecisionData:
        """验证写入租约 token。"""

    def release(self, *, resource_id: str, holder_key: str) -> None:
        """释放一个写入租约。"""
