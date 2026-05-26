"""Smoke test for deployment-ready JSONL observability sinks."""

from __future__ import annotations

import asyncio
import json
import os
from datetime import UTC, datetime

from whale.ingest.adapters.observability.file_sinks import (
    JsonlIngestMetricsSink,
    JsonlSourceCommandAuditSink,
)
from whale.ingest.adapters.source.static_source_write_port_registry import (
    StaticSourceWritePortRegistry,
)
from whale.ingest.ports.message.message_publisher_port import (
    MessagePublishResult,
    MessagePublisherPort,
)
from whale.ingest.ports.source.source_write_port import SourceWritePort
from whale.ingest.ports.state.source_state_snapshot_reader_port import (
    CachedNodeValue,
    CachedSourceState,
    SourceStateSnapshotReaderPort,
)
from whale.ingest.usecases.dtos.source_connection_data import SourceConnectionData
from whale.ingest.usecases.dtos.source_write_request import (
    SourceWriteExecutionOptions,
    SourceWriteItemData,
    SourceWriteRequest,
)
from whale.ingest.usecases.dtos.source_write_result import SourceWriteResult
from whale.ingest.usecases.dtos.state_publish_request import StateSnapshotPublishRequest
from whale.ingest.usecases.source_command_use_case import SourceCommandUseCase
from whale.ingest.usecases.state_snapshot_publish_use_case import StateSnapshotPublishUseCase


class _WritePort(SourceWritePort):
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
            pipeline_name="jsonl-smoke",
            success=True,
            message_id=message.message_id,
            message_count=1,
            published_at=datetime.now(tz=UTC),
        )


def test_jsonl_observability_sinks_capture_publish_and_command(tmp_path) -> None:
    metrics_path = tmp_path / "metrics.jsonl"
    audit_path = tmp_path / "audit.jsonl"
    metrics_sink = JsonlIngestMetricsSink(metrics_path)
    audit_sink = JsonlSourceCommandAuditSink(audit_path)

    os.environ["WHALE_INGEST_SOURCE_WRITE_ENABLED"] = "true"
    try:
        command = SourceCommandUseCase(
            write_port_registry=StaticSourceWritePortRegistry({"opcua": _WritePort()}),
            audit_port=audit_sink,
            metrics_port=metrics_sink,
        )
        asyncio.run(
            command.execute(
                SourceWriteRequest(
                    request_id="r1",
                    command_id="c1",
                    trace_id="t1",
                    execution=SourceWriteExecutionOptions(
                        protocol="opcua",
                        transport="tcp",
                        actor="tester",
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
    finally:
        os.environ.pop("WHALE_INGEST_SOURCE_WRITE_ENABLED", None)

    publish = StateSnapshotPublishUseCase(
        reader=_Reader(),
        publisher=_Publisher(),
        station_id="S1",
        metrics_port=metrics_sink,
    )
    publish.execute(StateSnapshotPublishRequest(trace_id="tp1"))

    metric_lines = metrics_path.read_text(encoding="utf-8").splitlines()
    audit_lines = audit_path.read_text(encoding="utf-8").splitlines()
    assert len(metric_lines) >= 2
    assert len(audit_lines) == 1
    metric_ops = {json.loads(line)["operation"] for line in metric_lines}
    assert "source_command" in metric_ops
    assert "snapshot_publish" in metric_ops
    audit_payload = json.loads(audit_lines[0])
    assert audit_payload["command_id"] == "c1"
    assert audit_payload["result"] == "SUCCESS"
