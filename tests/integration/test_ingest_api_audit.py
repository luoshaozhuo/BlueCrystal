"""API audit integration tests."""

from __future__ import annotations

from fastapi import Request
from fastapi.testclient import TestClient
from sqlalchemy import select

from whale.ingest.api import create_app
from whale.ingest.framework.persistence import (
    create_runtime_engine,
    create_runtime_session_factory,
    initialize_runtime_database,
)
from whale.shared.persistence.orm import IngestAuditEventOrm


def _build_client(tmp_path, *, deny: bool = False):
    engine = create_runtime_engine(f"sqlite:///{tmp_path / 'api-audit.sqlite'}")
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


def test_api_audit_covers_success_failure_conflict_validation_and_deny(tmp_path) -> None:
    client, session_factory = _build_client(tmp_path)

    created = client.post(
        "/api/v1/acquisition-tasks",
        json={"task_name": "task-1", "ld_instance_id": 1},
        headers={"x-actor": "tester"},
    )
    assert created.status_code == 201
    task_id = created.json()["task_id"]

    assert client.get(f"/api/v1/acquisition-tasks/{task_id}", headers={"x-actor": "tester"}).status_code == 200
    assert client.get("/api/v1/acquisition-tasks/999", headers={"x-actor": "tester"}).status_code == 404
    assert client.patch(
        f"/api/v1/acquisition-tasks/{task_id}",
        json={"expected_version": 99, "priority": 2},
        headers={"x-actor": "tester"},
    ).status_code == 409
    assert client.post(
        "/api/v1/acquisition-tasks",
        json={"ld_instance_id": 1},
        headers={"x-actor": "tester"},
    ).status_code == 422

    deny_client, _ = _build_client(tmp_path, deny=True)
    assert deny_client.get("/api/v1/acquisition-tasks", headers={"x-actor": "tester"}).status_code == 403

    session = session_factory()
    try:
        results = [row.result for row in session.scalars(select(IngestAuditEventOrm).order_by(IngestAuditEventOrm.audit_id))]
    finally:
        session.close()

    assert "SUCCESS" in results
    assert "NOT_FOUND" in results
    assert "CONFLICT" in results
    assert "VALIDATION_ERROR" in results
    assert "DENIED" in results
