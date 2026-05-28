"""Audit matrix tests covering API, bundle, scheduler, and write events."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from sqlalchemy import select

from whale.ingest.adapters.audit.db_audit_sink import DbIngestAuditSink
from whale.ingest.domain.audit_event import IngestAuditEvent
from whale.ingest.framework.persistence import (
    create_runtime_engine,
    create_runtime_session_factory,
    initialize_runtime_database,
)
from whale.shared.persistence.orm import IngestAuditEventOrm


@pytest.fixture
def session_factory(tmp_path):
    engine = create_runtime_engine(f"sqlite:///{tmp_path / 'audit-matrix.sqlite'}")
    initialize_runtime_database(engine)
    return create_runtime_session_factory(engine)


def test_audit_event_sink_persists_minimal_fields(session_factory):
    sink = DbIngestAuditSink(session_factory)
    now = datetime.now(tz=UTC)
    sink.emit(IngestAuditEvent(
        request_id="req-1", actor="tester", action="test.action",
        resource_type="test", resource_id="r1", decision="ALLOW",
        result="SUCCESS", reason_code=None, http_status=200,
        trace_id="trace-1", client_ip="10.0.0.1", node_id="node-1",
        timestamp=now,
    ))
    session = session_factory()
    try:
        rows = list(session.scalars(
            select(IngestAuditEventOrm).where(IngestAuditEventOrm.request_id == "req-1")
        ))
        assert len(rows) == 1
        row = rows[0]
        assert row.actor == "tester"
        assert row.action == "test.action"
        assert row.decision == "ALLOW"
        assert row.result == "SUCCESS"
        assert row.http_status == 200
        assert row.trace_id == "trace-1"
        assert row.client_ip == "10.0.0.1"
        assert row.node_id == "node-1"
    finally:
        session.close()


def test_audit_event_sink_persists_bundle_events(session_factory):
    sink = DbIngestAuditSink(session_factory)
    for action in ("bundle.export", "bundle.import", "bundle.import_rollback"):
        sink.emit(IngestAuditEvent(
            request_id=f"bundle-{action}", actor="cli", action=action,
            resource_type="bundle", resource_id="bundle-v1", decision="ALLOW",
            result="SUCCESS" if action != "bundle.import_rollback" else "FAILED",
            reason_code=None if action != "bundle.import_rollback" else "ROLLBACK",
            http_status=None, trace_id=None, client_ip=None, node_id="bundle-node",
            timestamp=datetime.now(tz=UTC),
        ))
    session = session_factory()
    try:
        from sqlalchemy import func
        count = session.scalar(
            select(func.count()).select_from(IngestAuditEventOrm).where(
                IngestAuditEventOrm.resource_type == "bundle"
            ).where(IngestAuditEventOrm.action.like("bundle.%"))
        ) or 0
        assert count >= 3
    finally:
        session.close()


def test_audit_event_sink_persists_scheduler_events(session_factory):
    sink = DbIngestAuditSink(session_factory)
    for action in ("scheduler.node_heartbeat", "scheduler.lease_acquire", "scheduler.lease_renew"):
        sink.emit(IngestAuditEvent(
            request_id=f"sched-{action}", actor="node-1", action=action,
            resource_type="scheduler", resource_id="node-1", decision="ALLOW",
            result="SUCCESS", reason_code=None, http_status=None,
            trace_id=None, client_ip=None, node_id="node-1",
            timestamp=datetime.now(tz=UTC),
        ))
    session = session_factory()
    try:
        from sqlalchemy import func
        count = session.scalar(
            select(func.count()).select_from(IngestAuditEventOrm).where(
                IngestAuditEventOrm.action.like("scheduler.%")
            ).where(IngestAuditEventOrm.node_id == "node-1")
        ) or 0
        assert count >= 3
    finally:
        session.close()


def test_audit_event_sink_persists_write_events(session_factory):
    sink = DbIngestAuditSink(session_factory)
    for action in ("write.precheck", "write.lease_acquire", "write.readback_mismatch"):
        sink.emit(IngestAuditEvent(
            request_id=f"write-{action}", actor="operator", action=action,
            resource_type="write", resource_id="source-1", decision="ALLOW",
            result="SUCCESS" if "mismatch" not in action else "FAILED",
            reason_code=None if "mismatch" not in action else "READBACK_MISMATCH",
            http_status=None, trace_id=None, client_ip=None, node_id="write-node",
            timestamp=datetime.now(tz=UTC),
        ))
    session = session_factory()
    try:
        from sqlalchemy import func
        count = session.scalar(
            select(func.count()).select_from(IngestAuditEventOrm).where(
                IngestAuditEventOrm.action.like("write.%")
            )
        ) or 0
        assert count >= 3
    finally:
        session.close()


def test_audit_event_redaction(session_factory):
    sink = DbIngestAuditSink(session_factory)
    sink.emit(IngestAuditEvent(
        request_id="redact-test", actor="tester", action="test.redact",
        resource_type="test", resource_id="r1", decision="ALLOW",
        result="SUCCESS", reason_code=None, http_status=200,
        trace_id=None, client_ip=None, node_id="node-1",
        timestamp=datetime.now(tz=UTC),
        attributes={"password": "secret123", "token": "tok_abc", "safe_field": "visible"},
    ))
    session = session_factory()
    try:
        rows = list(session.scalars(
            select(IngestAuditEventOrm).where(IngestAuditEventOrm.request_id == "redact-test")
        ))
        assert len(rows) == 1
        attrs = rows[0].attributes_json
        assert attrs.get("safe_field") == "visible"
        assert "***REDACTED***" in str(attrs.get("password", ""))
        assert "***REDACTED***" in str(attrs.get("token", ""))
    finally:
        session.close()
