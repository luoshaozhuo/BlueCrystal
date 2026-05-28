"""Authorization deny E2E tests for ingest runtime API."""
from __future__ import annotations

from fastapi import Request
from fastapi.testclient import TestClient

from whale.ingest.api import create_app
from whale.ingest.framework.persistence import (
    create_runtime_engine,
    create_runtime_session_factory,
    initialize_runtime_database,
)


def _build_app(tmp_path, *, deny: bool = False):
    engine = create_runtime_engine(f"sqlite:///{tmp_path / 'access-deny.sqlite'}")
    initialize_runtime_database(engine)
    session_factory = create_runtime_session_factory(engine)

    def access_evaluator(request: Request, action: str, resource_id: str | None = None) -> bool:
        del request, action, resource_id
        return not deny

    app = create_app(
        session_factory=session_factory,
        readiness_probe=lambda: True,
        access_evaluator=access_evaluator,
    )
    return TestClient(app), session_factory


def _seed(client: TestClient) -> None:
    """Create minimal seed data so list/get operations have something to find."""
    client.post("/api/v1/scheduler-jobs", json={"job_id": "seed-job"}, headers={"x-actor": "tester"})
    client.post("/api/v1/security-partitions", json={"partition_code": "seed", "partition_name": "Seed"}, headers={"x-actor": "tester"})


# ── Deny responses ───────────────────────────────────────────────────────────


def test_deny_on_scheduler_job_create(tmp_path):
    """POST scheduler-jobs returns 403 when access is denied."""
    client, _ = _build_app(tmp_path, deny=True)
    resp = client.post("/api/v1/scheduler-jobs", json={"job_id": "j1"}, headers={"x-actor": "tester"})
    assert resp.status_code == 403
    assert resp.json()["error"] == "DENIED"


def test_deny_on_scheduler_job_list(tmp_path):
    """GET scheduler-jobs returns 403 when access is denied."""
    client, _ = _build_app(tmp_path, deny=True)
    resp = client.get("/api/v1/scheduler-jobs", headers={"x-actor": "tester"})
    assert resp.status_code == 403


def test_deny_on_scheduler_job_read(tmp_path):
    """GET scheduler-jobs/{id} returns 403 when access is denied."""
    allow_client, _ = _build_app(tmp_path, deny=False)
    allow_client.post("/api/v1/scheduler-jobs", json={"job_id": "j1"}, headers={"x-actor": "tester"})

    deny_client, _ = _build_app(tmp_path, deny=True)
    resp = deny_client.get("/api/v1/scheduler-jobs/j1", headers={"x-actor": "tester"})
    assert resp.status_code == 403


def test_deny_on_scheduler_job_update(tmp_path):
    """PATCH scheduler-jobs returns 403 when access is denied."""
    allow_client, _ = _build_app(tmp_path, deny=False)
    allow_client.post("/api/v1/scheduler-jobs", json={"job_id": "j1"}, headers={"x-actor": "tester"})

    deny_client, _ = _build_app(tmp_path, deny=True)
    resp = deny_client.patch("/api/v1/scheduler-jobs/j1", json={"expected_version": 1}, headers={"x-actor": "tester"})
    assert resp.status_code == 403


def test_deny_on_scheduler_job_delete(tmp_path):
    """DELETE scheduler-jobs returns 403 when access is denied."""
    allow_client, _ = _build_app(tmp_path, deny=False)
    allow_client.post("/api/v1/scheduler-jobs", json={"job_id": "j1"}, headers={"x-actor": "tester"})

    deny_client, _ = _build_app(tmp_path, deny=True)
    resp = deny_client.delete("/api/v1/scheduler-jobs/j1?expected_version=1", headers={"x-actor": "tester"})
    assert resp.status_code == 403


def test_deny_on_acquisition_task_crud(tmp_path):
    """All CRUD operations on acquisition-tasks return 403 when denied."""
    client, _ = _build_app(tmp_path, deny=True)
    assert client.post("/api/v1/acquisition-tasks", json={"task_name": "t", "ld_instance_id": 1}, headers={"x-actor": "tester"}).status_code == 403
    assert client.get("/api/v1/acquisition-tasks", headers={"x-actor": "tester"}).status_code == 403
    assert client.get("/api/v1/acquisition-tasks/1", headers={"x-actor": "tester"}).status_code == 403
    assert client.patch("/api/v1/acquisition-tasks/1", json={"expected_version": 1}, headers={"x-actor": "tester"}).status_code == 403
    assert client.delete("/api/v1/acquisition-tasks/1?expected_version=1", headers={"x-actor": "tester"}).status_code == 403


def test_deny_on_security_partition_crud(tmp_path):
    """All CRUD operations on security-partitions return 403 when denied."""
    client, _ = _build_app(tmp_path, deny=True)
    assert client.post("/api/v1/security-partitions", json={"partition_code": "p", "partition_name": "P"}, headers={"x-actor": "tester"}).status_code == 403
    assert client.get("/api/v1/security-partitions", headers={"x-actor": "tester"}).status_code == 403
    assert client.get("/api/v1/security-partitions/1", headers={"x-actor": "tester"}).status_code == 403
    assert client.patch("/api/v1/security-partitions/1", json={"expected_version": 1}, headers={"x-actor": "tester"}).status_code == 403
    assert client.delete("/api/v1/security-partitions/1?expected_version=1", headers={"x-actor": "tester"}).status_code == 403


def test_deny_on_node_list(tmp_path):
    """GET nodes returns 403 when access is denied."""
    client, _ = _build_app(tmp_path, deny=True)
    assert client.get("/api/v1/nodes", headers={"x-actor": "tester"}).status_code == 403


def test_deny_on_lease_list(tmp_path):
    """GET leases returns 403 when access is denied."""
    client, _ = _build_app(tmp_path, deny=True)
    assert client.get("/api/v1/leases", headers={"x-actor": "tester"}).status_code == 403


def test_deny_on_audit_event_query(tmp_path):
    """GET audit-events returns 403 when access is denied."""
    client, _ = _build_app(tmp_path, deny=True)
    assert client.get("/api/v1/audit-events", headers={"x-actor": "tester"}).status_code == 403


def test_deny_on_bundle_read(tmp_path):
    """GET bundles returns 403 when access is denied."""
    client, _ = _build_app(tmp_path, deny=True)
    assert client.get("/api/v1/bundles/1", headers={"x-actor": "tester"}).status_code == 403


def test_allow_when_not_denied(tmp_path):
    """Requests are allowed when access_evaluator returns True."""
    client, _ = _build_app(tmp_path, deny=False)
    # GET is readable without creating first
    assert client.get("/api/v1/scheduler-jobs", headers={"x-actor": "tester"}).status_code == 200
    assert client.get("/api/v1/nodes", headers={"x-actor": "tester"}).status_code == 200
    assert client.get("/api/v1/leases", headers={"x-actor": "tester"}).status_code == 200
    assert client.get("/api/v1/audit-events", headers={"x-actor": "tester"}).status_code == 200


def test_healthz_readyz_not_blocked_by_deny(tmp_path):
    """Health/readiness probes bypass authorization."""
    client, _ = _build_app(tmp_path, deny=True)
    assert client.get("/healthz").status_code == 200
    assert client.get("/readyz").status_code == 200
