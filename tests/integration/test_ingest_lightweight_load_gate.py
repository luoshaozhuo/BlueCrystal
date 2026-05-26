"""Lightweight ingest load gate with in-memory/test sinks."""

from __future__ import annotations

import asyncio
import statistics
import time
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
from whale.ingest.usecases.dtos.source_connection_data import SourceConnectionData
from whale.ingest.usecases.dtos.source_acquisition_request import (
    AcquisitionExecutionOptions,
    AcquisitionItemData,
    SourceAcquisitionRequest,
)
from whale.ingest.usecases.roles.polling_acquisition_role import PollingAcquisitionRole
from whale.ingest.usecases.dtos.source_write_request import (
    SourceWriteExecutionOptions,
    SourceWriteItemData,
    SourceWriteRequest,
)
from whale.ingest.usecases.dtos.state_publish_request import StateSnapshotPublishRequest
from whale.ingest.usecases.source_command_use_case import SourceCommandUseCase
from whale.ingest.usecases.state_snapshot_publish_use_case import StateSnapshotPublishUseCase


@dataclass
class _Metrics(IngestMetricsPort):
    events: list[IngestMetricEvent] = field(default_factory=list)

    def emit(self, event: IngestMetricEvent) -> None:
        self.events.append(event)


class _WritePort(SourceWritePort):
    async def write(self, execution, connection, items):
        del execution, connection, items
        from whale.ingest.usecases.dtos.source_write_result import SourceWriteResult

        return SourceWriteResult(
            request_id="r",
            dry_run=False,
            success_count=1,
            failure_count=0,
        )


class _Reader(SourceStateSnapshotReaderPort):
    def __init__(self, count: int) -> None:
        self._count = count

    def read_snapshot(self) -> list[CachedSourceState]:
        ts = datetime.now(tz=UTC)
        values = [
            CachedNodeValue(
                node_key=f"k{i}",
                value=str(i),
                quality="GOOD",
                source_timestamp=ts,
                server_timestamp=ts,
                client_sequence=i + 1,
                updated_at=ts,
            )
            for i in range(self._count)
        ]
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
                values=values,
            )
        ]


class _Publisher(MessagePublisherPort):
    def __init__(self) -> None:
        self.message_count = 0

    def publish_snapshot(self, message) -> MessagePublishResult:
        self.message_count += 1
        return MessagePublishResult(
            pipeline_name="load-gate",
            success=True,
            message_id=message.message_id,
            message_count=1,
            published_at=datetime.now(tz=UTC),
        )


class _AcquisitionPort:
    async def read(self, execution, connection, items):
        del execution, items
        from whale.ingest.usecases.dtos.acquired_node_state import (
            AcquiredNodeStateBatch,
            AcquiredNodeValue,
        )

        ts = datetime.now(tz=UTC)
        return AcquiredNodeStateBatch(
            source_id=connection.ld_name,
            batch_observed_at=ts,
            client_received_at=ts,
            client_processed_at=ts,
            values=[
                AcquiredNodeValue(node_key=f"k{i}", value=str(i), quality="GOOD")
                for i in range(item_count_for_acquisition())
            ],
        )


class _StateCache:
    def __init__(self) -> None:
        self.update_count = 0

    def update(self, *, ld_name, batch):
        del ld_name
        self.update_count += 1
        return len(batch.values)

    def mark_alive(self, *, ld_name, observed_at):
        del ld_name, observed_at

    def mark_unavailable(self, *, ld_name, status, observed_at, reason=None):
        del ld_name, status, observed_at, reason


def item_count_for_acquisition() -> int:
    return 20


def test_ingest_lightweight_load_gate() -> None:
    metrics = _Metrics()
    batch_count = 25
    item_count = 40
    acquisition_cache = _StateCache()

    polling = PollingAcquisitionRole(
        acquisition_port=_AcquisitionPort(),
        state_cache_port=acquisition_cache,
        metrics_port=metrics,
    )
    acq_request = SourceAcquisitionRequest(
        request_id="load-acq",
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
        items=[
            AcquisitionItemData(key=f"k{i}", profile_item_id=i + 1, relative_path=f"k{i}")
            for i in range(item_count_for_acquisition())
        ],
    )
    acquisition_durations: list[float] = []
    for _ in range(batch_count):
        started = time.monotonic()
        asyncio.run(
            polling._read_connection(request=acq_request, connection=acq_request.connections[0])  # noqa: SLF001
        )
        acquisition_durations.append((time.monotonic() - started) * 1000.0)

    publisher = _Publisher()
    publish = StateSnapshotPublishUseCase(
        reader=_Reader(item_count),
        publisher=publisher,
        station_id="station-load",
        metrics_port=metrics,
    )

    publish_durations: list[float] = []
    for _ in range(batch_count):
        started = time.monotonic()
        result = publish.execute(StateSnapshotPublishRequest(trace_id="load-publish"))
        publish_durations.append((time.monotonic() - started) * 1000.0)
        assert result.failed_count == 0
        assert result.item_count == item_count

    command = SourceCommandUseCase(
        write_port_registry=StaticSourceWritePortRegistry({"opcua": _WritePort()}),
        metrics_port=metrics,
    )
    command_durations: list[float] = []
    for idx in range(batch_count):
        started = time.monotonic()
        asyncio.run(
            command.execute(
                SourceWriteRequest(
                    request_id=f"r{idx}",
                    command_id=f"c{idx}",
                    trace_id=f"t{idx}",
                    execution=SourceWriteExecutionOptions(
                        protocol="opcua",
                        transport="tcp",
                        dry_run=True,
                        actor="load-gate",
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
                    items=[
                        SourceWriteItemData(
                            key="k1",
                            node_id="n1",
                            value_type="double",
                            value="1.0",
                        )
                    ],
                )
            )
        )
        command_durations.append((time.monotonic() - started) * 1000.0)

    assert publisher.message_count == batch_count
    assert acquisition_cache.update_count == batch_count
    assert statistics.mean(acquisition_durations) > 0
    assert max(acquisition_durations) > 0
    assert statistics.mean(publish_durations) > 0
    assert max(publish_durations) > 0
    assert statistics.mean(command_durations) > 0
    assert max(command_durations) > 0
    values_per_sec = (batch_count * item_count) / (sum(publish_durations) / 1000.0)
    assert values_per_sec > 0
    assert len(metrics.events) >= batch_count * 2
