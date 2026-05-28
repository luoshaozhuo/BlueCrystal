"""Runtime-config API audit tests."""

from __future__ import annotations

from fastapi import Request
from fastapi.testclient import TestClient
from sqlalchemy import select

from whale.ingest.api import create_app
from whale.ingest.framework.persistence import create_runtime_engine, create_runtime_session_factory, initialize_runtime_database
from whale.shared.persistence.orm import IngestAuditEventOrm


def _build_client(tmp_path, *, deny: bool = False):
    engine = create_runtime_engine(f"sqlite:///{tmp_path / 'runtime-config-audit.sqlite'}")
    initialize_runtime_database(engine)
    session_factory = create_runtime_session_factory(engine)

    def access_evaluator(request: Request, action: str, resource_id: str | None = None) -> bool:
        del request, action, resource_id
        return not deny

    app = create_app(session_factory=session_factory, readiness_probe=lambda: True, access_evaluator=access_evaluator)
    return TestClient(app), session_factory


def test_query_success_and_query_failure_are_audited(tmp_path) -> None:
    client, session_factory = _build_client(tmp_path)
    source_id = client.post(
        "/api/v1/sources",
        json={"ied_name": "IED-1", "asset_code": "SRC-1", "asset_name": "Source 1"},
        headers={"x-actor": "tester"},
    ).json()["source_id"]
    assert client.get(f"/api/v1/sources/{source_id}", headers={"x-actor": "tester"}).status_code == 200
    assert client.get("/api/v1/sources/999", headers={"x-actor": "tester"}).status_code == 404

    session = session_factory()
    try:
        results = [row.result for row in session.scalars(select(IngestAuditEventOrm).order_by(IngestAuditEventOrm.audit_id))]
    finally:
        session.close()
    assert "SUCCESS" in results
    assert "NOT_FOUND" in results


def test_validation_error_and_conflict_are_audited(tmp_path) -> None:
    client, session_factory = _build_client(tmp_path)
    source_id = client.post(
        "/api/v1/sources",
        json={"ied_name": "IED-1", "asset_code": "SRC-1", "asset_name": "Source 1"},
        headers={"x-actor": "tester"},
    ).json()["source_id"]
    assert client.post("/api/v1/sources", json={"asset_code": "SRC-2"}, headers={"x-actor": "tester"}).status_code == 422
    assert client.patch(
        f"/api/v1/sources/{source_id}",
        json={"expected_version": 99, "asset_name": "bad"},
        headers={"x-actor": "tester"},
    ).status_code == 409

    session = session_factory()
    try:
        results = [row.result for row in session.scalars(select(IngestAuditEventOrm).order_by(IngestAuditEventOrm.audit_id))]
    finally:
        session.close()
    assert "VALIDATION_ERROR" in results
    assert "CONFLICT" in results


def test_delete_is_audited(tmp_path) -> None:
    client, session_factory = _build_client(tmp_path)
    source_id = client.post(
        "/api/v1/sources",
        json={"ied_name": "IED-1", "asset_code": "SRC-1", "asset_name": "Source 1"},
        headers={"x-actor": "tester"},
    ).json()["source_id"]
    assert client.delete(f"/api/v1/sources/{source_id}?expected_version=1", headers={"x-actor": "tester"}).status_code == 204

    session = session_factory()
    try:
        delete_event = session.execute(
            select(IngestAuditEventOrm).where(IngestAuditEventOrm.action == "source.delete")
        ).scalar_one()
    finally:
        session.close()
    assert delete_event.result == "SUCCESS"


def test_deny_is_audited(tmp_path) -> None:
    client, session_factory = _build_client(tmp_path, deny=True)
    assert client.get("/api/v1/sources", headers={"x-actor": "tester"}).status_code == 403

    session = session_factory()
    try:
        deny_event = session.execute(
            select(IngestAuditEventOrm).where(IngestAuditEventOrm.result == "DENIED")
        ).scalar_one()
    finally:
        session.close()
    assert deny_event.decision == "DENY"
