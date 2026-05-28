"""Acquisition-task CRUD integration tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from whale.ingest.api import create_app
from whale.ingest.framework.persistence import (
    create_runtime_engine,
    create_runtime_session_factory,
    initialize_runtime_database,
)


def _build_client(tmp_path):
    engine = create_runtime_engine(f"sqlite:///{tmp_path / 'api-crud.sqlite'}")
    initialize_runtime_database(engine)
    session_factory = create_runtime_session_factory(engine)
    app = create_app(session_factory=session_factory, readiness_probe=lambda: True)
    return TestClient(app)


def test_acquisition_task_crud_round_trip(tmp_path) -> None:
    client = _build_client(tmp_path)

    create_response = client.post(
        "/api/v1/acquisition-tasks",
        json={
            "task_name": "task-1",
            "ld_instance_id": 1,
            "acquisition_mode": "POLLING",
            "poll_interval_ms": 250,
            "request_timeout_ms": 800,
            "enabled": True,
            "priority": 10,
            "partition_key": "p-1",
            "assignment_policy": "AUTO",
        },
        headers={"x-actor": "tester"},
    )
    assert create_response.status_code == 201
    created = create_response.json()
    task_id = created["task_id"]
    assert created["version"] == 1

    get_response = client.get(f"/api/v1/acquisition-tasks/{task_id}", headers={"x-actor": "tester"})
    assert get_response.status_code == 200
    assert get_response.json()["task_name"] == "task-1"

    list_response = client.get("/api/v1/acquisition-tasks", headers={"x-actor": "tester"})
    assert list_response.status_code == 200
    assert len(list_response.json()["items"]) == 1

    patch_response = client.patch(
        f"/api/v1/acquisition-tasks/{task_id}",
        json={"expected_version": 1, "priority": 20},
        headers={"x-actor": "tester"},
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["priority"] == 20
    assert patch_response.json()["version"] == 2

    delete_response = client.delete(
        f"/api/v1/acquisition-tasks/{task_id}?expected_version=2",
        headers={"x-actor": "tester"},
    )
    assert delete_response.status_code == 204
