"""端口接口定义。

定义调用方契约和实现方责任，相关功能。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass(slots=True)
class CachedNodeValue:
    """LD/源最新状态视图中的一个缓存节点值。"""

    node_key: str
    value: str
    quality: str | None = None
    source_timestamp: datetime | None = None
    server_timestamp: datetime | None = None
    client_sequence: int | None = None
    updated_at: datetime | None = None
    attributes: dict[str, object] | None = None


@dataclass(slots=True)
class CachedSourceState:
    """单个 LD/源的最新状态快照。"""

    ld_name: str
    source_id: str
    availability_status: str
    unavailable_reason: str | None
    batch_observed_at: datetime | None
    client_received_at: datetime | None
    client_processed_at: datetime | None
    last_alive_at: datetime | None
    last_value_updated_at: datetime | None
    state_updated_at: datetime
    values: list[CachedNodeValue]


class SourceStateSnapshotReaderPort(Protocol):
    """从本地最新状态缓存读取当前完整快照。"""

    def read_snapshot(self) -> list[CachedSourceState]:
        """返回当前完整的最新状态快照。"""
