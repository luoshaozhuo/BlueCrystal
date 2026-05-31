"""StateSnapshotPublishUseCase 单元测试。

覆盖场景：正常发布、空数据、过滤、dry_run、异常、多消息拆分。
"""

from __future__ import annotations

from datetime import UTC, datetime


from whale.ingest.ports.message.message_publisher_port import (
    MessagePublishResult,
    MessagePublisherPort,
    StateSnapshotMessage,
)
from whale.ingest.ports.state.source_state_snapshot_reader_port import (
    CachedNodeValue,
    CachedSourceState,
    SourceStateSnapshotReaderPort,
)
from whale.ingest.usecases.dtos.state_publish_request import StateSnapshotPublishRequest
from whale.ingest.usecases.dtos.state_publish_result import PublishStatus
from whale.ingest.usecases.state_snapshot_publish_use_case import (
    StateSnapshotPublishUseCase,
)


# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------


class FakeSnapshotReader(SourceStateSnapshotReaderPort):
    """Return a predefined snapshot."""

    def __init__(self, sources: list[CachedSourceState] | None = None) -> None:
        self.sources = sources or []
        self.call_count = 0

    def read_snapshot(self) -> list[CachedSourceState]:
        self.call_count += 1
        return self.sources


class FakePublisher(MessagePublisherPort):
    """Record published messages and return configurable results."""

    def __init__(
        self,
        *,
        success: bool = True,
        error_message: str | None = None,
        pipeline_name: str = "test_pipeline",
    ) -> None:
        self.messages: list[StateSnapshotMessage] = []
        self._success = success
        self._error_message = error_message
        self.pipeline_name = pipeline_name

    def publish_snapshot(self, message: StateSnapshotMessage) -> MessagePublishResult:
        self.messages.append(message)
        return MessagePublishResult(
            pipeline_name=self.pipeline_name,
            success=self._success,
            message_id=message.message_id,
            message_count=1,
            published_at=datetime.now(tz=UTC),
            error_message=self._error_message,
        )


class FakeFailingPublisher(MessagePublisherPort):
    """Raise an exception on publish."""

    def publish_snapshot(self, message: StateSnapshotMessage) -> MessagePublishResult:
        msg = f"Kafka broker unreachable: {message.message_id}"
        raise RuntimeError(msg)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_TS = datetime(2026, 5, 24, 12, 0, 0, tzinfo=UTC)


def _make_node(
    node_key: str = "var_1",
    value: str = "42",
    quality: str | None = "Good",
    source_timestamp: datetime | None = None,
    server_timestamp: datetime | None = None,
    updated_at: datetime | None = None,
    attributes: dict[str, object] | None = None,
) -> CachedNodeValue:
    return CachedNodeValue(
        node_key=node_key,
        value=value,
        quality=quality,
        source_timestamp=source_timestamp or _TS,
        server_timestamp=server_timestamp,
        client_sequence=1,
        updated_at=updated_at or _TS,
        attributes=attributes,
    )


def _make_source(
    ld_name: str = "StationA/Device1",
    source_id: str = "modbus_tcp:Device1",
    values: list[CachedNodeValue] | None = None,
    availability: str = "ALIVE",
) -> CachedSourceState:
    return CachedSourceState(
        ld_name=ld_name,
        source_id=source_id,
        availability_status=availability,
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


class TestStateSnapshotPublishUseCase:
    """Test suite for StateSnapshotPublishUseCase."""

    def test_publish_one_source_one_value(self) -> None:
        """Basic success: one source with one value publishes one message."""
        reader = FakeSnapshotReader(sources=[_make_source()])
        publisher = FakePublisher()
        use_case = StateSnapshotPublishUseCase(
            reader=reader, publisher=publisher, station_id="StationA"
        )
        request = StateSnapshotPublishRequest(trace_id="trace-001")

        result = use_case.execute(request)

        assert result.status == PublishStatus.SUCCESS
        assert result.source_count == 1
        assert result.item_count == 1
        assert result.message_count == 1
        assert result.published_count == 1
        assert result.trace_id == "trace-001"
        assert result.is_success is True
        assert len(publisher.messages) == 1
        msg = publisher.messages[0]
        assert msg.item_count == 1
        assert msg.trace_id == "trace-001"
        assert msg.source_module == "ingest"

    def test_publish_multiple_sources(self) -> None:
        """Multiple sources with multiple values all published."""
        sources = [
            _make_source(
                ld_name="StationA/Dev1",
                source_id="dev1",
                values=[_make_node("v1"), _make_node("v2")],
            ),
            _make_source(
                ld_name="StationA/Dev2",
                source_id="dev2",
                values=[_make_node("v3")],
            ),
        ]
        reader = FakeSnapshotReader(sources=sources)
        publisher = FakePublisher()
        use_case = StateSnapshotPublishUseCase(
            reader=reader, publisher=publisher, station_id="StationA"
        )

        result = use_case.execute(StateSnapshotPublishRequest())

        assert result.status == PublishStatus.SUCCESS
        assert result.source_count == 2
        assert result.item_count == 3
        assert result.published_count == 3

    def test_empty_cache_returns_no_data(self) -> None:
        """When cache returns empty list, result is NO_DATA."""
        reader = FakeSnapshotReader(sources=[])
        publisher = FakePublisher()
        use_case = StateSnapshotPublishUseCase(
            reader=reader, publisher=publisher, station_id="StationA"
        )

        result = use_case.execute(StateSnapshotPublishRequest())

        assert result.status == PublishStatus.NO_DATA
        assert result.source_count == 0
        assert result.item_count == 0
        assert result.is_success is True
        assert len(publisher.messages) == 0

    def test_filter_by_source_id(self) -> None:
        """Filter by source_id returns only matching sources."""
        sources = [
            _make_source(ld_name="StationA/Dev1", source_id="dev1"),
            _make_source(ld_name="StationA/Dev2", source_id="dev2"),
        ]
        reader = FakeSnapshotReader(sources=sources)
        publisher = FakePublisher()
        use_case = StateSnapshotPublishUseCase(
            reader=reader, publisher=publisher, station_id="StationA"
        )

        result = use_case.execute(
            StateSnapshotPublishRequest(source_id="dev1")
        )

        assert result.status == PublishStatus.SUCCESS
        assert result.source_count == 1
        assert "dev1" in publisher.messages[0].items[0].device_code

    def test_filter_by_ld_name(self) -> None:
        """Filter by ld_name returns only matching sources."""
        sources = [
            _make_source(ld_name="StationA/Dev1", source_id="dev1"),
            _make_source(ld_name="StationA/Dev2", source_id="dev2"),
        ]
        reader = FakeSnapshotReader(sources=sources)
        publisher = FakePublisher()
        use_case = StateSnapshotPublishUseCase(
            reader=reader, publisher=publisher, station_id="StationA"
        )

        result = use_case.execute(
            StateSnapshotPublishRequest(ld_name="StationA/Dev2")
        )

        assert result.status == PublishStatus.SUCCESS
        assert result.source_count == 1
        assert result.item_count == 1
        assert "Dev2" in publisher.messages[0].items[0].device_id

    def test_filter_no_match_returns_no_data(self) -> None:
        """Filter that matches nothing returns NO_DATA."""
        reader = FakeSnapshotReader(sources=[_make_source()])
        publisher = FakePublisher()
        use_case = StateSnapshotPublishUseCase(
            reader=reader, publisher=publisher, station_id="StationA"
        )

        result = use_case.execute(
            StateSnapshotPublishRequest(source_id="nonexistent")
        )

        assert result.status == PublishStatus.NO_DATA
        assert result.source_count == 1  # total before filter
        assert result.item_count == 0
        assert len(publisher.messages) == 0

    def test_dry_run_does_not_publish(self) -> None:
        """dry_run=True reads cache but never publishes."""
        reader = FakeSnapshotReader(sources=[_make_source()])
        publisher = FakePublisher()
        use_case = StateSnapshotPublishUseCase(
            reader=reader, publisher=publisher, station_id="StationA"
        )

        result = use_case.execute(
            StateSnapshotPublishRequest(dry_run=True, trace_id="dry-001")
        )

        assert result.status == PublishStatus.DRY_RUN
        assert result.source_count == 1
        assert result.item_count == 1
        assert result.message_count == 1
        assert result.trace_id == "dry-001"
        assert result.is_success is True
        assert len(publisher.messages) == 0

    def test_cache_read_error_returns_failed(self) -> None:
        """When reader.read_snapshot() raises, result is FAILED."""

        class BrokenReader(SourceStateSnapshotReaderPort):
            def read_snapshot(self) -> list[CachedSourceState]:
                raise ConnectionError("Redis connection refused")

        reader = BrokenReader()
        publisher = FakePublisher()
        use_case = StateSnapshotPublishUseCase(
            reader=reader, publisher=publisher, station_id="StationA"
        )

        result = use_case.execute(StateSnapshotPublishRequest(trace_id="err-001"))

        assert result.status == PublishStatus.FAILED
        assert result.source_count == 0
        assert result.error is not None
        assert "Redis connection refused" in result.error
        assert result.is_success is False

    def test_publish_error_returns_failed(self) -> None:
        """When publisher raises, individual message result is FAILED but other messages still succeed."""
        reader = FakeSnapshotReader(sources=[_make_source(values=[_make_node("v1")])])
        publisher = FakeFailingPublisher()
        use_case = StateSnapshotPublishUseCase(
            reader=reader, publisher=publisher, station_id="StationA"
        )

        result = use_case.execute(StateSnapshotPublishRequest(trace_id="pub-err"))

        assert result.status == PublishStatus.FAILED
        assert result.source_count == 1
        assert result.item_count == 1
        assert result.failed_count == 1
        assert result.published_count == 0
        assert result.error is not None

    def test_publish_unsuccessful_result(self) -> None:
        """Publisher returns success=False -> item marked as failed."""
        reader = FakeSnapshotReader(sources=[_make_source()])
        publisher = FakePublisher(success=False, error_message="Topic not found")
        use_case = StateSnapshotPublishUseCase(
            reader=reader, publisher=publisher, station_id="StationA"
        )

        result = use_case.execute(StateSnapshotPublishRequest())

        assert result.status == PublishStatus.FAILED
        assert result.failed_count == 1
        assert result.published_count == 0
        assert result.is_success is False

    def test_message_item_field_mapping(self) -> None:
        """StateSnapshotItem fields are correctly mapped from CachedSourceState + CachedNodeValue."""
        node = _make_node(
            node_key="temperature",
            value="36.5",
            quality="Good",
            source_timestamp=_TS,
            updated_at=_TS,
        )
        source = _make_source(
            ld_name="SubA/Meter1",
            source_id="modbus:Meter1",
            values=[node],
        )
        reader = FakeSnapshotReader(sources=[source])
        publisher = FakePublisher()
        use_case = StateSnapshotPublishUseCase(
            reader=reader, publisher=publisher, station_id="StationA"
        )

        result = use_case.execute(StateSnapshotPublishRequest())

        assert result.status == PublishStatus.SUCCESS
        item = publisher.messages[0].items[0]
        assert item.station_id == "StationA"
        assert item.device_id == "SubA/Meter1"
        assert item.device_code == "modbus:Meter1"
        assert item.variable_key == "temperature"
        assert item.value == "36.5"
        assert item.quality_code == "Good"
        assert item.source_observed_at == _TS
        assert item.updated_at == _TS
        assert item.received_at == _TS  # from client_received_at

    def test_item_has_model_id_fallback(self) -> None:
        """When attributes have no model_id, device_code is used as fallback."""
        node = _make_node(node_key="v1", value="1")
        source = _make_source(source_id="dev1", values=[node])
        reader = FakeSnapshotReader(sources=[source])
        publisher = FakePublisher()
        use_case = StateSnapshotPublishUseCase(
            reader=reader, publisher=publisher, station_id="StationA"
        )

        result = use_case.execute(StateSnapshotPublishRequest())

        assert result.status == PublishStatus.SUCCESS
        item = publisher.messages[0].items[0]
        assert item.model_id == "dev1"  # fallback to device_code

    def test_multi_message_splitting(self) -> None:
        """max_items_per_message splits items across multiple messages."""
        nodes = [_make_node(node_key=f"v{i}") for i in range(10)]
        source = _make_source(values=nodes)
        reader = FakeSnapshotReader(sources=[source])
        publisher = FakePublisher()
        use_case = StateSnapshotPublishUseCase(
            reader=reader, publisher=publisher, station_id="StationA"
        )

        result = use_case.execute(
            StateSnapshotPublishRequest(max_items_per_message=3)
        )

        assert result.status == PublishStatus.SUCCESS
        assert result.item_count == 10
        assert result.message_count == 4  # 10 items / 3 per msg = 4 msgs
        assert result.published_count == 10
        assert len(publisher.messages) == 4
        # each of first 3 messages has 3 items, last has 1
        assert len(publisher.messages[0].items) == 3
        assert len(publisher.messages[1].items) == 3
        assert len(publisher.messages[2].items) == 3
        assert len(publisher.messages[3].items) == 1
        # message ids have seq suffix for split messages (first has no suffix)
        assert publisher.messages[0].message_id == publisher.messages[0].snapshot_id
        assert publisher.messages[1].message_id.endswith("-0001")
        assert publisher.messages[2].message_id.endswith("-0002")
        assert publisher.messages[3].message_id.endswith("-0003")

    def test_single_message_no_seq_suffix(self) -> None:
        """Single message (no splitting) has no seq suffix in message_id."""
        reader = FakeSnapshotReader(sources=[_make_source()])
        publisher = FakePublisher()
        use_case = StateSnapshotPublishUseCase(
            reader=reader, publisher=publisher, station_id="StationA"
        )

        result = use_case.execute(StateSnapshotPublishRequest())

        assert result.status == PublishStatus.SUCCESS
        mid = publisher.messages[0].message_id
        assert "-0000" not in mid
        assert mid.count("-") == 2  # station-YYYYMMDDTHHMMSS-hex

    def test_snapshot_message_structure(self) -> None:
        """Top-level StateSnapshotMessage fields are correctly populated."""
        reader = FakeSnapshotReader(sources=[_make_source()])
        publisher = FakePublisher()
        use_case = StateSnapshotPublishUseCase(
            reader=reader, publisher=publisher, station_id="StationA"
        )

        result = use_case.execute(
            StateSnapshotPublishRequest(trace_id="trace-s1")
        )

        assert result.status == PublishStatus.SUCCESS
        msg = publisher.messages[0]
        assert msg.schema_version == "1.0"
        assert msg.message_type == "state_snapshot"
        assert msg.source_module == "ingest"
        assert msg.trace_id == "trace-s1"
        assert msg.snapshot_at is not None
        assert msg.item_count == 1
        assert len(msg.items) == 1

    def test_snapshot_id_uniqueness(self) -> None:
        """Each execute call generates a unique snapshot_id."""
        reader = FakeSnapshotReader(sources=[_make_source(), _make_source()])
        publisher = FakePublisher()
        use_case = StateSnapshotPublishUseCase(
            reader=reader, publisher=publisher, station_id="StationA"
        )

        r1 = use_case.execute(StateSnapshotPublishRequest())
        r2 = use_case.execute(StateSnapshotPublishRequest())

        assert r1.status == PublishStatus.SUCCESS
        assert r2.status == PublishStatus.SUCCESS
        snap_ids = {m.snapshot_id for m in publisher.messages}
        assert len(snap_ids) == 2  # two separate calls, two unique ids

    def test_partial_failure_aggregation(self) -> None:
        """When some messages fail and some succeed, result is PARTIAL/FAILED with both counts."""
        nodes = [_make_node(node_key=f"v{i}") for i in range(5)]
        source = _make_source(values=nodes)
        reader = FakeSnapshotReader(sources=[source])

        class AlternatingPublisher(MessagePublisherPort):
            """Succeed first call, fail subsequent calls."""

            def __init__(self) -> None:
                self.call_no = 0

            def publish_snapshot(
                self, message: StateSnapshotMessage
            ) -> MessagePublishResult:
                self.call_no += 1
                ok = self.call_no == 1
                return MessagePublishResult(
                    pipeline_name="kafka",
                    success=ok,
                    message_id=message.message_id,
                    message_count=1,
                    published_at=datetime.now(tz=UTC),
                    error_message=None if ok else "Broker error",
                )

        publisher = AlternatingPublisher()
        use_case = StateSnapshotPublishUseCase(
            reader=reader, publisher=publisher, station_id="StationA"
        )

        # Split into 2 messages: 3 items + 2 items
        result = use_case.execute(
            StateSnapshotPublishRequest(max_items_per_message=3)
        )

        assert result.message_count == 2
        assert result.published_count == 3  # first msg succeeded
        assert result.failed_count == 2  # second msg failed
        assert result.status == PublishStatus.FAILED
