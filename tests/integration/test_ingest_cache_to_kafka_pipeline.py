"""Integration test: cache snapshot → StateSnapshotPublishUseCase → Kafka publisher.

测试步骤：
1. 通过 FakeSnapshotReader 模拟 Redis cache 中的最新状态。
2. 通过 StateSnapshotPublishUseCase 使用真实 KafkaMessagePublisher + FakeKafkaProducer。
3. 验证消息被正确序列化并通过 Kafka send() 发送。
4. 验证 dry_run 不调用 send()。
5. 验证过滤功能。

不依赖外部 Redis 或 Kafka。
"""

from __future__ import annotations

from datetime import UTC, datetime

from whale.ingest.adapters.message.kafka_message_publisher import KafkaMessagePublisher
from whale.ingest.ports.state.source_state_snapshot_reader_port import (
    CachedNodeValue,
    CachedSourceState,
    SourceStateSnapshotReaderPort,
)
from whale.ingest.runtime.message_pipeline_settings import KafkaMessageSettings
from whale.ingest.usecases.dtos.state_publish_request import StateSnapshotPublishRequest
from whale.ingest.usecases.dtos.state_publish_result import PublishStatus
from whale.ingest.usecases.state_snapshot_publish_use_case import (
    StateSnapshotPublishUseCase,
)

_TS = datetime(2026, 5, 24, 12, 0, 0, tzinfo=UTC)
_TOPIC = "whale.ingest.snapshot"


class _FakeKafkaFuture:
    """Capture `get()` timeout (no real Kafka needed)."""

    def __init__(self) -> None:
        self.timeouts: list[float | None] = []

    def get(self, timeout: float | None = None) -> object:
        self.timeouts.append(timeout)
        return {"topic": _TOPIC}


class _FakeKafkaProducer:
    """Capture Kafka send() calls for assertion."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, bytes, bytes]] = []
        self.future = _FakeKafkaFuture()
        self.flush_count = 0

    def send(self, topic: str, key: bytes, value: bytes) -> _FakeKafkaFuture:
        self.calls.append((topic, key, value))
        return self.future

    def flush(self) -> None:
        self.flush_count += 1


class _FakeSnapshotReader(SourceStateSnapshotReaderPort):
    """Return preset cached sources."""

    def __init__(self, sources: list[CachedSourceState]) -> None:
        self._sources = sources

    def read_snapshot(self) -> list[CachedSourceState]:
        return list(self._sources)


def _make_node(
    node_key: str = "temp_1",
    value: str = "23.5",
) -> CachedNodeValue:
    return CachedNodeValue(
        node_key=node_key,
        value=value,
        quality="Good",
        source_timestamp=_TS,
        server_timestamp=_TS,
        client_sequence=1,
        updated_at=_TS,
    )


def _make_source(
    ld_name: str = "StationA/MainDevice",
    source_id: str = "modbus_tcp:MainDevice",
    values: list[CachedNodeValue] | None = None,
) -> CachedSourceState:
    return CachedSourceState(
        ld_name=ld_name,
        source_id=source_id,
        availability_status="ALIVE",
        unavailable_reason=None,
        batch_observed_at=_TS,
        client_received_at=_TS,
        client_processed_at=_TS,
        last_alive_at=_TS,
        last_value_updated_at=_TS,
        state_updated_at=_TS,
        values=values or [_make_node()],
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_cache_to_kafka_full_pipeline() -> None:
    """Full pipeline: cache → use_case → KafkaMessagePublisher → producer."""
    sources = [
        _make_source(
            ld_name="StationA/Dev1",
            source_id="modbus:Dev1",
            values=[
                _make_node("temp_1", "25.0"),
                _make_node("pressure_1", "101.3"),
            ],
        ),
        _make_source(
            ld_name="StationA/Dev2",
            source_id="modbus:Dev2",
            values=[_make_node("temp_2", "30.0")],
        ),
    ]
    reader = _FakeSnapshotReader(sources)
    producer = _FakeKafkaProducer()
    publisher = KafkaMessagePublisher(
        settings=KafkaMessageSettings(
            bootstrap_servers=("localhost:9092",),
            topic=_TOPIC,
            ack_timeout_seconds=5.0,
        ),
        producer=producer,
    )
    use_case = StateSnapshotPublishUseCase(
        reader=reader, publisher=publisher, station_id="StationA"
    )

    result = use_case.execute(StateSnapshotPublishRequest(trace_id="int-001"))

    # Verify use case result
    assert result.status == PublishStatus.SUCCESS
    assert result.source_count == 2
    assert result.item_count == 3
    assert result.published_count == 3
    assert result.message_count == 1
    assert result.trace_id == "int-001"

    # Verify Kafka producer was called
    assert len(producer.calls) == 1
    topic, key, value = producer.calls[0]
    assert topic == _TOPIC
    assert key.startswith(b"StationA-")  # snapshot_id
    payload = value.decode("utf-8")
    assert '"message_type":"state_snapshot"' in payload
    assert '"variable_key":"temp_1"' in payload
    assert '"variable_key":"pressure_1"' in payload
    assert '"variable_key":"temp_2"' in payload
    assert '"source_module":"ingest"' in payload
    assert '"item_count":3' in payload
    assert "StationA/Dev1" in payload
    assert "StationA/Dev2" in payload

    # Verify flush
    assert producer.flush_count == 1
    assert len(producer.future.timeouts) == 1


def test_cache_to_kafka_dry_run_does_not_send() -> None:
    """dry_run reads cache but does not call Kafka producer.send()."""
    sources = [_make_source()]
    reader = _FakeSnapshotReader(sources)
    producer = _FakeKafkaProducer()
    publisher = KafkaMessagePublisher(
        settings=KafkaMessageSettings(
            bootstrap_servers=("localhost:9092",),
            topic=_TOPIC,
            ack_timeout_seconds=5.0,
        ),
        producer=producer,
    )
    use_case = StateSnapshotPublishUseCase(
        reader=reader, publisher=publisher, station_id="StationA"
    )

    result = use_case.execute(
        StateSnapshotPublishRequest(dry_run=True, trace_id="dry-int")
    )

    assert result.status == PublishStatus.DRY_RUN
    assert result.source_count == 1
    assert result.item_count == 1
    assert len(producer.calls) == 0  # no Kafka send
    assert producer.flush_count == 0


def test_cache_to_kafka_no_data_no_send() -> None:
    """Empty cache results in no Kafka send."""
    reader = _FakeSnapshotReader([])
    producer = _FakeKafkaProducer()
    publisher = KafkaMessagePublisher(
        settings=KafkaMessageSettings(
            bootstrap_servers=("localhost:9092",),
            topic=_TOPIC,
            ack_timeout_seconds=5.0,
        ),
        producer=producer,
    )
    use_case = StateSnapshotPublishUseCase(
        reader=reader, publisher=publisher, station_id="StationA"
    )

    result = use_case.execute(StateSnapshotPublishRequest())

    assert result.status == PublishStatus.NO_DATA
    assert len(producer.calls) == 0


def test_cache_to_kafka_multi_message_split() -> None:
    """max_items_per_message splits across multiple Kafka sends."""
    nodes = [_make_node(node_key=f"sensor_{i}") for i in range(7)]
    source = _make_source(values=nodes)
    reader = _FakeSnapshotReader([source])
    producer = _FakeKafkaProducer()
    publisher = KafkaMessagePublisher(
        settings=KafkaMessageSettings(
            bootstrap_servers=("localhost:9092",),
            topic=_TOPIC,
            ack_timeout_seconds=5.0,
        ),
        producer=producer,
    )
    use_case = StateSnapshotPublishUseCase(
        reader=reader, publisher=publisher, station_id="StationA"
    )

    result = use_case.execute(
        StateSnapshotPublishRequest(max_items_per_message=3)
    )

    assert result.status == PublishStatus.SUCCESS
    assert result.message_count == 3  # 7 / 3 = 3 msgs
    assert result.published_count == 7
    assert len(producer.calls) == 3

    # First msg: 3 items, second: 3, third: 1
    for i, call in enumerate(producer.calls):
        payload = call[2].decode("utf-8")
        assert '"source_module":"ingest"' in payload
    assert b'"item_count":3' in producer.calls[0][2]
    assert b'"item_count":3' in producer.calls[1][2]
    assert b'"item_count":1' in producer.calls[2][2]


def test_cache_to_kafka_with_filter() -> None:
    """source_id filter produces correct payload with only filtered data."""
    sources = [
        _make_source(ld_name="StationA/Dev1", source_id="modbus:Dev1"),
        _make_source(ld_name="StationA/Dev2", source_id="modbus:Dev2"),
    ]
    reader = _FakeSnapshotReader(sources)
    producer = _FakeKafkaProducer()
    publisher = KafkaMessagePublisher(
        settings=KafkaMessageSettings(
            bootstrap_servers=("localhost:9092",),
            topic=_TOPIC,
            ack_timeout_seconds=5.0,
        ),
        producer=producer,
    )
    use_case = StateSnapshotPublishUseCase(
        reader=reader, publisher=publisher, station_id="StationA"
    )

    result = use_case.execute(
        StateSnapshotPublishRequest(source_id="modbus:Dev1")
    )

    assert result.status == PublishStatus.SUCCESS
    assert result.source_count == 1
    payload = producer.calls[0][2].decode("utf-8")
    assert "StationA/Dev1" in payload
    assert "StationA/Dev2" not in payload
