"""Production-like audit sink integration tests.

Verifies audit events flow to PostgreSQL and/or JSONL.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import pytest

from whale.ingest.adapters.audit.db_audit_sink import DbIngestAuditSink
from whale.ingest.adapters.observability.file_sinks import JsonlIngestAuditSink
from whale.ingest.domain.audit_event import IngestAuditEvent
from whale.ingest.framework.persistence import (
    create_runtime_engine,
    create_runtime_session_factory,
    migrate_runtime_database,
)
from whale.shared.persistence.orm.ingest_runtime import IngestAuditEventOrm

PG_DSN_ENV = "WHALE_INGEST_TEST_PG_DSN"


def _pg_engine():
    dsn = os.environ.get(PG_DSN_ENV)
    if not dsn:
        pytest.skip(f"{PG_DSN_ENV} not set")
    return create_runtime_engine(dsn)


def _pg_session_factory(engine):
    return create_runtime_session_factory(engine)


@pytest.fixture(scope="module")
def pg_engine():
    engine = _pg_engine()
    migrate_runtime_database(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def pg_sf(pg_engine):
    return _pg_session_factory(pg_engine)


# ── API audit written to PostgreSQL ────────────────────────────────────


def test_api_audit_written_to_postgres(pg_sf):
    """Verify API audit event is persisted in PostgreSQL audit_event table."""
    sink = DbIngestAuditSink(pg_sf)
    event = IngestAuditEvent(
        request_id="prod-api-audit",
        actor="tester",
        action="create scheduler_job",
        resource_type="scheduler_job",
        resource_id="job-1",
        decision="ALLOW",
        result="SUCCESS",
        reason_code=None,
        http_status=201,
        trace_id="trace-abc",
        client_ip="10.0.0.1",
        node_id="api-node-1",
    )
    sink.emit(event)

    session = pg_sf()
    try:
        row = session.query(IngestAuditEventOrm).filter_by(
            request_id="prod-api-audit"
        ).first()
        assert row is not None
        assert row.actor == "tester"
        assert row.action == "create scheduler_job"
        assert row.decision == "ALLOW"
        assert row.http_status == 201
    finally:
        session.close()


# ── Scheduler audit written to PostgreSQL ──────────────────────────────


def test_scheduler_audit_written_to_postgres(pg_sf):
    """Verify scheduler audit event is persisted."""
    sink = DbIngestAuditSink(pg_sf)
    event = IngestAuditEvent(
        request_id="prod-scheduler-audit",
        actor="worker-a",
        action="job.executed",
        resource_type="job",
        resource_id="job-sch-1",
        decision="ALLOW",
        result="SUCCESS",
        reason_code=None,
        http_status=None,
        trace_id=None,
        client_ip=None,
        node_id="worker-a",
    )
    sink.emit(event)

    session = pg_sf()
    try:
        row = session.query(IngestAuditEventOrm).filter_by(
            request_id="prod-scheduler-audit"
        ).first()
        assert row is not None
        assert row.actor == "worker-a"
        assert row.action == "job.executed"
    finally:
        session.close()


# ── Bundle audit written to PostgreSQL ─────────────────────────────────


def test_bundle_audit_written_to_postgres(pg_sf):
    """Verify bundle audit event is persisted."""
    sink = DbIngestAuditSink(pg_sf)
    event = IngestAuditEvent(
        request_id="prod-bundle-audit",
        actor="cli",
        action="bundle.import",
        resource_type="bundle",
        resource_id="bundle-v1",
        decision="ALLOW",
        result="SUCCESS",
        reason_code=None,
        http_status=None,
        trace_id=None,
        client_ip=None,
        node_id="bundle-import",
    )
    sink.emit(event)

    session = pg_sf()
    try:
        row = session.query(IngestAuditEventOrm).filter_by(
            request_id="prod-bundle-audit"
        ).first()
        assert row is not None
        assert row.action == "bundle.import"
    finally:
        session.close()


# ── Write deny audit ───────────────────────────────────────────────────


def test_write_deny_audit_written_to_postgres(pg_sf):
    """Verify write/control deny audit event is persisted."""
    sink = DbIngestAuditSink(pg_sf)
    event = IngestAuditEvent(
        request_id="prod-write-deny",
        actor="unauthorized-actor",
        action="write source_write",
        resource_type="source_write",
        resource_id="opcua-device-1",
        decision="DENY",
        result="DENIED",
        reason_code="ACCESS_DENIED",
        http_status=403,
        trace_id="trace-deny",
        client_ip="10.0.0.2",
        node_id="api-node-1",
    )
    sink.emit(event)

    session = pg_sf()
    try:
        row = session.query(IngestAuditEventOrm).filter_by(
            request_id="prod-write-deny"
        ).first()
        assert row is not None
        assert row.decision == "DENY"
        assert row.reason_code == "ACCESS_DENIED"
    finally:
        session.close()


# ── JSONL + DB dual sink consistency ───────────────────────────────────


def test_jsonl_and_db_audit_sink_consistency(pg_sf):
    """Verify DB and JSONL sinks receive the same redacted payload."""
    sink = DbIngestAuditSink(pg_sf)
    tmp = tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False, mode="w")
    tmp.close()
    jsonl_sink = JsonlIngestAuditSink(tmp.name)

    event = IngestAuditEvent(
        request_id="prod-dual-sink-test",
        actor="tester",
        action="test.dual_sink",
        resource_type="test",
        resource_id="dual-test",
        decision="ALLOW",
        result="SUCCESS",
        reason_code=None,
        http_status=200,
        trace_id="trace-dual",
        client_ip="10.0.0.3",
        node_id="api-node",
    )

    # Emit to both
    sink.emit(event)
    jsonl_sink.emit(event)

    # Verify DB
    session = pg_sf()
    try:
        db_row = session.query(IngestAuditEventOrm).filter_by(
            request_id="prod-dual-sink-test"
        ).first()
        assert db_row is not None
        assert db_row.actor == "tester"
    finally:
        session.close()

    # Verify JSONL
    lines = Path(tmp.name).read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) >= 1
    jsonl_event = json.loads(lines[0])
    assert jsonl_event["request_id"] == "prod-dual-sink-test"
    assert jsonl_event["actor"] == "tester"

    Path(tmp.name).unlink(missing_ok=True)


# ── Audit redaction in prodlike sink ───────────────────────────────────


def test_audit_redacts_sensitive_fields_in_prodlike_sink():
    """Verify audit event redaction works for sensitive fields."""
    event = IngestAuditEvent(
        request_id="redact-test",
        actor="tester",
        action="test",
        resource_type="test",
        resource_id="test",
        decision="ALLOW",
        result="SUCCESS",
        reason_code=None,
        http_status=200,
        trace_id=None,
        client_ip=None,
        node_id=None,
        attributes={
            "password": "secret123",
            "token": "tok_abc",
            "safe_field": "hello",
        },
    )
    payload = event.sanitized_payload()
    assert payload["attributes"]["password"] == "***REDACTED***"
    assert payload["attributes"]["token"] == "***REDACTED***"
    assert payload["attributes"]["safe_field"] == "hello"
