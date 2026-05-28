"""Node / Lease / Audit-event query API integration tests."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi.testclient import TestClient
from sqlalchemy import select

from whale.ingest.api import create_app
from whale.ingest.framework.persistence import (
    create_runtime_engine,
    create_runtime_session_factory,
    initialize_runtime_database,
)
from whale.shared.persistence.orm import (
    IngestAuditEventOrm,
    IngestJobLease,
    IngestRuntimeNode,
)


def _client(tmp_path):
    engine = create_runtime_engine(f"sqlite:///{tmp_path / 'node-lease.sqlite'}")
    initialize_runtime_database(engine)
    session_factory = create_runtime_session_factory(engine)
    app = create_app(session_factory=session_factory, readiness_probe=lambda: True)
    return TestClient(app), session_factory


def test_node_query(tmp_path):
    client, factory = _client(tmp_path)
    now = datetime.now(tz=UTC)
    session = factory()
    try:
        session.add(IngestRuntimeNode(
            node_key="node-1", runtime_mode="standalone", status="ALIVE",
            heartbeat_at=now, last_seen_at=now,
        ))
        session.commit()
    finally:
        session.close()

    fetched = client.get("/api/v1/nodes/node-1", headers={"x-actor": "tester"})
    assert fetched.status_code == 200
    assert fetched.json()["node_key"] == "node-1"

    listed = client.get("/api/v1/nodes", headers={"x-actor": "tester"})
    assert listed.status_code == 200
    assert listed.json()["total"] >= 1


def test_lease_query(tmp_path):
    client, factory = _client(tmp_path)
    now = datetime.now(tz=UTC)
    session = factory()
    try:
        session.add(IngestJobLease(
            lease_name="lease:test", lease_scope="job", resource_id="test",
            holder_key="node-1", status="ACTIVE", fencing_token=1,
            acquired_at=now, renewed_at=now, expires_at=now,
        ))
        session.commit()
    finally:
        session.close()

    listed = client.get("/api/v1/leases", headers={"x-actor": "tester"})
    assert listed.status_code == 200
    assert listed.json()["total"] >= 1

    lid = listed.json()["items"][0]["lease_id"]
    fetched = client.get(f"/api/v1/leases/{lid}", headers={"x-actor": "tester"})
    assert fetched.status_code == 200

    # Filter by scope
    filtered = client.get("/api/v1/leases?scope=job", headers={"x-actor": "tester"})
    assert filtered.status_code == 200


def test_audit_event_query(tmp_path):
    client, factory = _client(tmp_path)
    now = datetime.now(tz=UTC)
    session = factory()
    try:
        session.add(IngestAuditEventOrm(
            request_id="req-1", action="test.action", resource_type="test",
            decision="ALLOW", result="SUCCESS",
            event_timestamp=now,
        ))
        session.commit()
    finally:
        session.close()

    listed = client.get("/api/v1/audit-events", headers={"x-actor": "tester"})
    assert listed.status_code == 200
    assert listed.json()["total"] >= 1

    aid = listed.json()["items"][0]["audit_id"]
    fetched = client.get(f"/api/v1/audit-events/{aid}", headers={"x-actor": "tester"})
    assert fetched.status_code == 200

    # Filter by action
    filtered = client.get("/api/v1/audit-events?action=test.action", headers={"x-actor": "tester"})
    assert filtered.status_code == 200
