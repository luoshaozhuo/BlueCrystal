"""DTO for state snapshot publish results."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class PublishStatus(Enum):
    SUCCESS = "SUCCESS"
    NO_DATA = "NO_DATA"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"
    DRY_RUN = "DRY_RUN"


@dataclass(slots=True)
class StateSnapshotPublishResult:
    """Result of one state snapshot publish operation.

    Fields:
        status: Overall status enum.
        source_count: Number of sources read from cache.
        item_count: Total node values across all sources.
        message_count: Number of messages published.
        published_count: Number of items successfully published.
        skipped_count: Number of items skipped.
        failed_count: Number of items that failed to publish.
        trace_id: Correlation trace id.
        snapshot_at: When the snapshot was taken (UTC).
        error: Error message if the operation failed.
    """

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
        """Return True when snapshot was published or dry-run without failure."""
        return self.status in (PublishStatus.SUCCESS, PublishStatus.NO_DATA, PublishStatus.DRY_RUN)

    def merge(self, other: StateSnapshotPublishResult) -> StateSnapshotPublishResult:
        """Merge another partial result into this one for multi-message reporting."""
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
