"""message_pipeline 领域模型单元测试。

验证 Envelope、TopicSpec、PartitionKey 策略、MessageOffset 和 ReplayRequest
的字段语义和构造行为。

被验证对象：
- whale.message_pipeline.model: Envelope, TopicSpec, PartitionKeyStrategy,
  PartitionKey, SourceIdPartitionKey, DeviceIdPartitionKey, StationIdPartitionKey,
  CustomPartitionKey, MessageOffset, ReplayRequest

测试阶段：开发期验证 (unit/mock)（纯内存单元测试，不依赖外部系统）。
"""

from __future__ import annotations

from datetime import datetime, timezone

from whale.message_pipeline.model import (
    CustomPartitionKey,
    DeviceIdPartitionKey,
    Envelope,
    MessageOffset,
    PartitionKeyStrategy,
    ReplayRequest,
    SourceIdPartitionKey,
    StationIdPartitionKey,
    TopicSpec,
)


def _make_envelope(
    source_id: str = "source-1",
    items: list[dict[str, object]] | None = None,
    partition_key: str | None = None,
) -> Envelope:
    """构造测试用 Envelope。

    Args:
        source_id: 数据源标识。
        items: 载荷数据项列表。
        partition_key: 分区键。

    Returns:
        填充了合理默认值的 Envelope 实例。
    """
    if items is None:
        items = [
            {"variable_key": "temp", "value": "25.5", "device_id": "dev-1"}
        ]
    return Envelope(
        schema_version="1.0",
        message_id="msg-001",
        message_type="state_snapshot",
        trace_id="trace-001",
        source_id=source_id,
        published_at=datetime(2026, 6, 2, 10, 0, 0, tzinfo=timezone.utc),
        items=items,
        partition_key=partition_key,
    )


class TestEnvelope:
    """Envelope 领域模型测试。"""

    def test_create_with_all_fields(self) -> None:
        """验证 Envelope 所有字段可正常构造。"""
        env = _make_envelope()
        assert env.schema_version == "1.0"
        assert env.message_id == "msg-001"
        assert env.message_type == "state_snapshot"
        assert env.trace_id == "trace-001"
        assert env.source_id == "source-1"
        assert len(env.items) == 1

    def test_default_partition_key_none(self) -> None:
        """验证 partition_key 默认为 None。"""
        env = Envelope(
            schema_version="1.0",
            message_id="msg-001",
            message_type="state_snapshot",
            trace_id=None,
            source_id="source-1",
            published_at=datetime.now(tz=timezone.utc),
            items=[],
        )
        assert env.partition_key is None

    def test_published_at_preserves_timezone(self) -> None:
        """验证 published_at 保留时区信息。"""
        ts = datetime(2026, 6, 2, 10, 0, 0, tzinfo=timezone.utc)
        env = Envelope(
            schema_version="1.0",
            message_id="msg-001",
            message_type="state_snapshot",
            trace_id=None,
            source_id="source-1",
            published_at=ts,
            items=[],
        )
        assert env.published_at == ts
        assert env.published_at.tzinfo == timezone.utc


class TestTopicSpec:
    """TopicSpec 配置模型测试。"""

    def test_default_values(self) -> None:
        """验证 TopicSpec 默认分区数和副本因子。"""
        spec = TopicSpec(name="test-topic")
        assert spec.name == "test-topic"
        assert spec.partitions == 1
        assert spec.replication_factor == 1
        assert spec.retention_ms is None

    def test_explicit_values(self) -> None:
        """验证 TopicSpec 显式构造值。"""
        spec = TopicSpec(
            name="prod-topic",
            partitions=3,
            replication_factor=2,
            retention_ms=86400000,
        )
        assert spec.partitions == 3
        assert spec.replication_factor == 2
        assert spec.retention_ms == 86400000


class TestPartitionKeyStrategies:
    """分区键策略测试。"""

    def test_source_id_strategy(self) -> None:
        """验证 SourceIdPartitionKey 使用 envelope.source_id。"""
        env = _make_envelope(source_id="station-42")
        strategy = SourceIdPartitionKey()
        key = strategy.resolve(env)
        assert key == "station-42"

    def test_device_id_strategy(self) -> None:
        """验证 DeviceIdPartitionKey 使用 items 中的 device_id。"""
        env = _make_envelope(
            source_id="source-1",
            items=[
                {"device_id": "dev-abc", "variable_key": "temp", "value": "25"}
            ],
        )
        strategy = DeviceIdPartitionKey()
        key = strategy.resolve(env)
        assert key == "dev-abc"

    def test_device_id_strategy_fallback(self) -> None:
        """验证 DeviceIdPartitionKey 在无 device_id 时 fallback 到 source_id。"""
        env = _make_envelope(
            source_id="source-1",
            items=[{"variable_key": "temp", "value": "25"}],
        )
        strategy = DeviceIdPartitionKey()
        key = strategy.resolve(env)
        assert key == "source-1"

    def test_station_id_strategy(self) -> None:
        """验证 StationIdPartitionKey 使用 items 中的 station_id。"""
        env = _make_envelope(
            source_id="source-1",
            items=[
                {
                    "station_id": "station-xyz",
                    "variable_key": "temp",
                    "value": "25",
                }
            ],
        )
        strategy = StationIdPartitionKey()
        key = strategy.resolve(env)
        assert key == "station-xyz"

    def test_station_id_strategy_fallback(self) -> None:
        """验证 StationIdPartitionKey 在无 station_id 时 fallback 到 source_id。"""
        env = _make_envelope(source_id="source-1")
        strategy = StationIdPartitionKey()
        key = strategy.resolve(env)
        assert key == "source-1"

    def test_custom_strategy(self) -> None:
        """验证 CustomPartitionKey 使用 envelope.partition_key。"""
        env = _make_envelope(partition_key="my-custom-key")
        strategy = CustomPartitionKey()
        key = strategy.resolve(env)
        assert key == "my-custom-key"

    def test_custom_strategy_fallback(self) -> None:
        """验证 CustomPartitionKey 在 partition_key 为 None 时 fallback。"""
        env = _make_envelope(partition_key=None)
        strategy = CustomPartitionKey()
        key = strategy.resolve(env)
        assert key == env.source_id

    def test_partition_key_strategy_enum_values(self) -> None:
        """验证 PartitionKeyStrategy 枚举值正确。"""
        assert PartitionKeyStrategy.SOURCE_ID.value == "source_id"
        assert PartitionKeyStrategy.DEVICE_ID.value == "device_id"
        assert PartitionKeyStrategy.STATION_ID.value == "station_id"
        assert PartitionKeyStrategy.CUSTOM.value == "custom"


class TestMessageOffset:
    """MessageOffset 模型测试。"""

    def test_create_offset(self) -> None:
        """验证 MessageOffset 正常构造。"""
        offset = MessageOffset(partition=2, offset=100)
        assert offset.partition == 2
        assert offset.offset == 100
        assert offset.timestamp is None

    def test_offset_with_timestamp(self) -> None:
        """验证 MessageOffset 带时间戳构造。"""
        ts = datetime.now(tz=timezone.utc)
        offset = MessageOffset(partition=0, offset=42, timestamp=ts)
        assert offset.timestamp == ts


class TestReplayRequest:
    """ReplayRequest 模型测试。"""

    def test_create_with_topic_only(self) -> None:
        """验证 ReplayRequest 最少参数构造（仅 topic）。"""
        req = ReplayRequest(topic="test-topic")
        assert req.topic == "test-topic"
        assert req.start_offset is None
        assert req.start_timestamp is None
        assert req.end_offset is None
        assert req.end_timestamp is None

    def test_create_with_timestamp_range(self) -> None:
        """验证 ReplayRequest 按时间范围构造。"""
        start = datetime(2026, 6, 1, tzinfo=timezone.utc)
        end = datetime(2026, 6, 2, tzinfo=timezone.utc)
        req = ReplayRequest(
            topic="test-topic",
            start_timestamp=start,
            end_timestamp=end,
        )
        assert req.start_timestamp == start
        assert req.end_timestamp == end

    def test_create_with_offset_range(self) -> None:
        """验证 ReplayRequest 按 offset 范围构造。"""
        start_off = MessageOffset(partition=0, offset=10)
        end_off = MessageOffset(partition=0, offset=100)
        req = ReplayRequest(
            topic="test-topic",
            start_offset=start_off,
            end_offset=end_off,
        )
        assert req.start_offset == start_off
        assert req.end_offset == end_off
