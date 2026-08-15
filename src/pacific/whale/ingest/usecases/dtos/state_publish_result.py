"""数据传输对象。

定义 use case 层输入输出数据结构，与 ORM 模型解耦。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class PublishStatus(Enum):
    """发布状态枚举。"""
    SUCCESS = "SUCCESS"
    NO_DATA = "NO_DATA"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"
    DRY_RUN = "DRY_RUN"


@dataclass(slots=True)
class StateSnapshotPublishResult:
    """一次状态快照发布操作的结果 DTO。记录发布条目数和成功/失败状态。"""

    status: PublishStatus
    source_count: int
    item_count: int
    message_count: int = 0
    published_count: int = 0
    skipped_count: int = 0
    failed_count: int = 0
    trace_id: str | None = None
    snapshot_at: datetime | None = None
    error: str | None = None
    attributes: dict[str, str] = field(default_factory=dict)

    @property
    def is_success(self) -> bool:
        """快照发布成功或 dry-run 无失败时返回 True。"""
        return self.status in (PublishStatus.SUCCESS, PublishStatus.NO_DATA, PublishStatus.DRY_RUN)

    def merge(self, other: StateSnapshotPublishResult) -> StateSnapshotPublishResult:
        """将另一个部分结果合并到当前结果中，用于多消息报告。"""
        self.item_count += other.item_count
        self.message_count += other.message_count
        self.published_count += other.published_count
        self.skipped_count += other.skipped_count
        self.failed_count += other.failed_count
        if other.error:
            self.error = other.error
        if self.status == PublishStatus.SUCCESS and other.status != PublishStatus.SUCCESS:
            self.status = other.status
        return self
