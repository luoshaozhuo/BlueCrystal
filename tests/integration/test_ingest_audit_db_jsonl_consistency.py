"""Audit DB/JSONL sink consistency tests."""

from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest
from sqlalchemy import select

from whale.ingest.adapters.audit.db_audit_sink import DbIngestAuditSink
from whale.ingest.adapters.observability.file_sinks import JsonlIngestAuditSink
from whale.ingest.domain.audit_event import IngestAuditEvent
from whale.ingest.framework.persistence import (
    create_runtime_engine,
    create_runtime_session_factory,
    initialize_runtime_database,
)
from whale.shared.persistence.orm import IngestAuditEventOrm


@pytest.fixture
def session_factory(tmp_path):
    engine = create_runtime_engine(f"sqlite:///{tmp_path / 'consistency.sqlite'}")
    initialize_runtime_database(engine)
    return create_runtime_session_factory(engine)


def test_db_and_jsonl_sink_consistent_schema(tmp_path, session_factory):
    """DB and JSONL sinks produce same fields for the same event."""
    jsonl_path = tmp_path / "audit.jsonl"
    db_sink = DbIngestAuditSink(session_factory)
    jsonl_sink = JsonlIngestAuditSink(jsonl_path)

    now = datetime.now(tz=UTC)
    event = IngestAuditEvent(
        request_id="consistency-1", actor="tester", action="test.consistency",
        resource_type="test", resource_id="r1", decision="ALLOW",
        result="SUCCESS", reason_code=None, http_status=200,
        trace_id="trace-1", client_ip="10.0.0.1", node_id="node-1",
        timestamp=now,
        before_version=1, after_version=2,
        changed_fields=["field_a"],
        attributes={"key": "value"},
    )

    db_sink.emit(event)
    jsonl_sink.emit(event)

    # Verify DB
    session = session_factory()
    try:
        row = session.scalar(select(IngestAuditEventOrm).where(
            IngestAuditEventOrm.request_id == "consistency-1"
        ))
        assert row is not None
        assert row.actor == "tester"
        assert row.action == "test.consistency"
        assert row.before_version == 1
        assert row.after_version == 2
    finally:
        session.close()

    # Verify JSONL
    lines = jsonl_path.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) >= 1
    parsed = json.loads(lines[0])
    assert parsed["request_id"] == "consistency-1"
    assert parsed["actor"] == "tester"
    assert parsed["action"] == "test.consistency"
    assert "before_version" in parsed
    assert "after_version" in parsed
