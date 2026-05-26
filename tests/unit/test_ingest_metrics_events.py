"""Metrics event emission tests for ingest core chains."""

from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass, field
from datetime import UTC, datetime

from whale.ingest.adapters.source.static_source_write_port_registry import (
    StaticSourceWritePortRegistry,
)
from whale.ingest.ports.message.message_publisher_port import (
    MessagePublishResult,
    MessagePublisherPort,
)
from whale.ingest.ports.metrics import IngestMetricEvent, IngestMetricsPort
from whale.ingest.ports.source.source_write_port import SourceWritePort
from whale.ingest.ports.state.source_state_snapshot_reader_port import (
    CachedNodeValue,
    CachedSourceState,
    SourceStateSnapshotReaderPort,
)
from whale.ingest.usecases.dtos.source_acquisition_request import (
    AcquisitionExecutionOptions,
    AcquisitionItemData,
    SourceAcquisitionRequest,
)
from whale.ingest.usecases.dtos.source_connection_data import SourceConnectionData
from whale.ingest.usecases.dtos.source_write_request import (
    SourceWriteExecutionOptions,
    SourceWriteItemData,
    SourceWriteRequest,
)
from whale.ingest.usecases.dtos.source_write_result import SourceWriteResult
from whale.ingest.usecases.dtos.state_publish_request import StateSnapshotPublishRequest
from whale.ingest.usecases.roles.polling_acquisition_role import PollingAcquisitionRole
from whale.ingest.usecases.source_command_use_case import SourceCommandUseCase
from whale.ingest.usecases.state_snapshot_publish_use_case import (
    StateSnapshotPublishUseCase,
)


@dataclass
class _InMemoryMetrics(IngestMetricsPort):
    events: list[IngestMetricEvent] = field(default_factory=list)

    def emit(self, event: IngestMetricEvent) -> None:
        self.events.append(event)


class _FakeWritePort(SourceWritePort):
    async def write(self, execution, connection, items):
        del execution, connection, items
        return SourceWriteResult(
            request_id="r1",
            dry_run=False,
            success_count=1,
            failure_count=0,
        )


class _Reader(SourceStateSnapshotReaderPort):
    def read_snapshot(self) -> list[CachedSourceState]:
        ts = datetime.now(tz=UTC)
        return [
            CachedSourceState(
                ld_name="LD1",
                source_id="s1",
                availability_status="ALIVE",
                unavailable_reason=None,
                batch_observed_at=ts,
                client_received_at=ts,
                client_processed_at=ts,
                last_alive_at=ts,
                last_value_updated_at=ts,
                state_updated_at=ts,
                values=[
                    CachedNodeValue(
                        node_key="k1",
                        value="1",
                        quality="GOOD",
                        source_timestamp=ts,
                        server_timestamp=ts,
                        client_sequence=1,
                        updated_at=ts,
                    )
                ],
            )
        ]


class _Publisher(MessagePublisherPort):
    def publish_snapshot(self, message) -> MessagePublishResult:
        return MessagePublishResult(
            pipeline_name="p",
            success=True,
            message_id=message.message_id,
            message_count=1,
            published_at=datetime.now(tz=UTC),
        )


class _AcqPort:
    def supports_subscription(self, execution, connection):
        del execution, connection
        return False

    async def read(self, execution, connection, items):
        del execution, items
        ts = datetime.now(tz=UTC)
        from whale.ingest.usecases.dtos.acquired_node_state import (
            AcquiredNodeStateBatch,
            AcquiredNodeValue,
        )

        return AcquiredNodeStateBatch(
            source_id=connection.ld_name,
            batch_observed_at=ts,
            client_received_at=ts,
            client_processed_at=ts,
            values=[AcquiredNodeValue(node_key="k1", value="1", quality="GOOD")],
        )

    async def start_subscription(self, execution, connection, items, *, state_received):
        raise RuntimeError("unused")


class _Cache:
    def update(self, *, ld_name, batch):
        del ld_name, batch
        return 1

    def mark_alive(self, *, ld_name, observed_at):
        del ld_name, observed_at

    def mark_unavailable(self, *, ld_name, status, observed_at, reason=None):
        del ld_name, status, observed_at, reason


def test_metrics_events_emitted_for_command_publish_and_polling() -> None:
    metrics = _InMemoryMetrics()

    os.environ["WHALE_INGEST_SOURCE_WRITE_ENABLED"] = "true"
    command = SourceCommandUseCase(
        write_port_registry=StaticSourceWritePortRegistry({"opcua": _FakeWritePort()}),
        metrics_port=metrics,
    )
    req = SourceWriteRequest(
        request_id="r1",
        command_id="c1",
        trace_id="t1",
        execution=SourceWriteExecutionOptions(protocol="opcua", transport="tcp", actor="a1"),
        connections=[
            SourceConnectionData(
                host="127.0.0.1",
                port=4840,
                ied_name="IED1",
                ld_name="LD1",
                namespace_uri="",
            )
        ],
        items=[SourceWriteItemData(key="k1", node_id="n1", value_type="double", value="1.0")],
    )
    asyncio.run(command.execute(req))
    os.environ.pop("WHALE_INGEST_SOURCE_WRITE_ENABLED", None)

    publish = StateSnapshotPublishUseCase(
        reader=_Reader(),
        publisher=_Publisher(),
        station_id="S1",
        metrics_port=metrics,
    )
    publish.execute(StateSnapshotPublishRequest(trace_id="tp1"))

    polling = PollingAcquisitionRole(
        acquisition_port=_AcqPort(),
        state_cache_port=_Cache(),
        metrics_port=metrics,
    )
    acq_req = SourceAcquisitionRequest(
        request_id="ar1",
        task_id=1,
        execution=AcquisitionExecutionOptions(
            protocol="opcua",
            transport="tcp",
            acquisition_mode="READ_ONCE",
            interval_ms=10,
            max_iteration=1,
            request_timeout_ms=1000,
            freshness_timeout_ms=1000,
            alive_timeout_ms=1000,
        ),
        connections=[
            SourceConnectionData(
                host="127.0.0.1",
                port=4840,
                ied_name="IED1",
                ld_name="LD1",
                namespace_uri="",
            )
        ],
        items=[AcquisitionItemData(key="k1", profile_item_id=1, relative_path="k1")],
    )
    asyncio.run(polling._read_connection(request=acq_req, connection=acq_req.connections[0]))  # noqa: SLF001

    ops = {event.operation for event in metrics.events}
    assert "source_command" in ops
    assert "snapshot_publish" in ops
    assert "polling_read" in ops
    for event in metrics.events:
        assert event.duration_ms >= 0
        assert event.status
