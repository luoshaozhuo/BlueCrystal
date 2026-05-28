"""Scheduler-job CRUD integration tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from whale.ingest.api import create_app
from whale.ingest.framework.persistence import (
    create_runtime_engine,
    create_runtime_session_factory,
    initialize_runtime_database,
)


def _client(tmp_path):
    engine = create_runtime_engine(f"sqlite:///{tmp_path / 'scheduler-job.sqlite'}")
    initialize_runtime_database(engine)
    session_factory = create_runtime_session_factory(engine)
    app = create_app(session_factory=session_factory, readiness_probe=lambda: True)
    return TestClient(app)


def test_scheduler_job_create_and_read(tmp_path):
    client = _client(tmp_path)
    created = client.post(
        "/api/v1/scheduler-jobs",
        json={"job_id": "job-1", "job_type": "acquisition", "priority": 5},
        headers={"x-actor": "tester"},
    )
    assert created.status_code == 201
    assert created.json()["job_id"] == "job-1"

    fetched = client.get("/api/v1/scheduler-jobs/job-1", headers={"x-actor": "tester"})
    assert fetched.status_code == 200
    assert fetched.json()["job_type"] == "acquisition"


def test_scheduler_job_list(tmp_path):
    client = _client(tmp_path)
    client.post("/api/v1/scheduler-jobs", json={"job_id": "j1"}, headers={"x-actor": "tester"})
    client.post("/api/v1/scheduler-jobs", json={"job_id": "j2"}, headers={"x-actor": "tester"})
    resp = client.get("/api/v1/scheduler-jobs", headers={"x-actor": "tester"})
    assert resp.status_code == 200
    assert resp.json()["total"] == 2


def test_scheduler_job_patch(tmp_path):
    client = _client(tmp_path)
    created = client.post(
        "/api/v1/scheduler-jobs",
        json={"job_id": "job-p", "priority": 10},
        headers={"x-actor": "tester"},
    )
    assert created.status_code == 201
    patched = client.patch(
        "/api/v1/scheduler-jobs/job-p",
        json={"expected_version": 1, "priority": 20},
        headers={"x-actor": "tester"},
    )
    assert patched.status_code == 200
    assert patched.json()["priority"] == 20


def test_scheduler_job_delete(tmp_path):
    client = _client(tmp_path)
    created = client.post(
        "/api/v1/scheduler-jobs",
        json={"job_id": "job-d"},
        headers={"x-actor": "tester"},
    )
    assert created.status_code == 201
    deleted = client.delete("/api/v1/scheduler-jobs/job-d?expected_version=1", headers={"x-actor": "tester"})
    assert deleted.status_code == 204
    fetched = client.get("/api/v1/scheduler-jobs/job-d", headers={"x-actor": "tester"})
    assert fetched.status_code == 404


def test_scheduler_job_version_conflict(tmp_path):
    client = _client(tmp_path)
    client.post("/api/v1/scheduler-jobs", json={"job_id": "job-c"}, headers={"x-actor": "tester"})
    resp = client.patch(
        "/api/v1/scheduler-jobs/job-c",
        json={"expected_version": 99, "priority": 50},
        headers={"x-actor": "tester"},
    )
    assert resp.status_code == 409
