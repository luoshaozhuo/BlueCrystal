"""Unit tests for lightweight ingest observability sinks."""

from __future__ import annotations

import json
from datetime import UTC, datetime

from whale.ingest.adapters.observability.file_sinks import (
    JsonlIngestMetricsSink,
    JsonlSourceCommandAuditSink,
)
from whale.ingest.ports.command.source_command_audit_port import SourceCommandAuditEvent
from whale.ingest.ports.metrics import IngestMetricEvent


def test_jsonl_metrics_sink_persists_event(tmp_path) -> None:
    path = tmp_path / "metrics.jsonl"
    sink = JsonlIngestMetricsSink(path)
    sink.emit(
        IngestMetricEvent(
            operation="snapshot_publish",
            source_id="LD1",
            protocol="opcua",
            duration_ms=12.5,
            status="SUCCESS",
            error_code=None,
            timestamp=datetime.now(tz=UTC),
        )
    )
    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    payload = json.loads(lines[0])
    assert payload["operation"] == "snapshot_publish"
    assert payload["protocol"] == "opcua"
    assert payload["duration_ms"] == 12.5


def test_jsonl_audit_sink_persists_event(tmp_path) -> None:
    path = tmp_path / "audit.jsonl"
    sink = JsonlSourceCommandAuditSink(path)
    sink.emit(
        SourceCommandAuditEvent(
            request_id="r1",
            command_id="c1",
            trace_id="t1",
            actor="tester",
            protocol="opcua",
            source_id="LD1",
            target="n1",
            result="SUCCESS",
            failure_reason=None,
            timestamp=datetime.now(tz=UTC),
        )
    )
    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    payload = json.loads(lines[0])
    assert payload["command_id"] == "c1"
    assert payload["actor"] == "tester"
    assert payload["result"] == "SUCCESS"
