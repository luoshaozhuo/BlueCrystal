"""端口接口定义。

定义调用方契约和实现方责任，相关功能。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol


@dataclass(slots=True)
class StateSnapshotItem:
    """代表已发布状态快照中的一行变量数据。"""

    station_id: str | None
    device_id: str | None
    device_code: str
    model_id: str
    variable_key: str
    value: str | None
    value_type: str | None
    quality_code: str | None
    source_observed_at: datetime | None
    received_at: datetime | None
    updated_at: datetime | None

    def to_dict(self) -> dict[str, object | None]:
        """将单个快照条目序列化为 JSON 友好的映射。"""
        return {
            "station_id": self.station_id,
            "device_id": self.device_id,
            "device_code": self.device_code,
            "model_id": self.model_id,
            "variable_key": self.variable_key,
            "value": self.value,
            "value_type": self.value_type,
            "quality_code": self.quality_code,
            "source_observed_at": _serialize_datetime(self.source_observed_at),
            "received_at": _serialize_datetime(self.received_at),
            "updated_at": _serialize_datetime(self.updated_at),
        }


@dataclass(slots=True)
class StateSnapshotMessage:
    """代表 ingest 发出的一条完整快照消息。"""

    message_id: str
    schema_version: str
    message_type: str
    source_module: str
    snapshot_id: str
    snapshot_at: datetime
    item_count: int
    items: list[StateSnapshotItem]
    trace_id: str | None = None
    attributes: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        """将完整快照消息序列化为 JSON 友好的映射。"""
        return {
            "message_id": self.message_id,
            "schema_version": self.schema_version,
            "message_type": self.message_type,
            "source_module": self.source_module,
            "snapshot_id": self.snapshot_id,
            "snapshot_at": _serialize_datetime(self.snapshot_at),
            "item_count": self.item_count,
            "items": [item.to_dict() for item in self.items],
            "trace_id": self.trace_id,
            "attributes": dict(self.attributes),
        }

    def to_json(self) -> str:
        """将完整快照消息序列化为稳定的 JSON 字符串。"""
        return json.dumps(
            self.to_dict(),
            ensure_ascii=False,
            separators=(",", ":"),
        )


@dataclass(slots=True)
class MessagePublishResult:
    """代表发布一条快照消息的结果。"""

    pipeline_name: str
    success: bool
    message_id: str
    message_count: int
    published_at: datetime
    error_message: str | None = None


class MessagePublisherPort(Protocol):
    """将一条组装好的状态快照消息发布到管道。"""

    def publish_snapshot(self, message: StateSnapshotMessage) -> MessagePublishResult:
        """发布一条状态快照消息。"""


def _serialize_datetime(value: datetime | None) -> str | None:
    """将单个审计事件转换为安全的 JSON 可序列化字典。"""
    if value is None:
        return None
    return value.isoformat()
