"""Full audit matrix integration tests — verify every API action emits audit."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import select

from whale.ingest.api import create_app
from whale.ingest.framework.persistence import (
    create_runtime_engine,
    create_runtime_session_factory,
    initialize_runtime_database,
)
from whale.shared.persistence.orm import IngestAuditEventOrm


def _client(tmp_path):
    engine = create_runtime_engine(f"sqlite:///{tmp_path / 'audit-matrix.sqlite'}")
    initialize_runtime_database(engine)
    session_factory = create_runtime_session_factory(engine)
    app = create_app(session_factory=session_factory, readiness_probe=lambda: True)
    return TestClient(app), session_factory


def _audit_count(factory) -> int:
    session = factory()
    try:
        return session.scalar(select(IngestAuditEventOrm).where(
            IngestAuditEventOrm.action == "healthz.read"
        )) or 0
    finally:
        session.close()


def test_healthz_emits_audit(tmp_path):
    client, factory = _client(tmp_path)
    client.get("/healthz", headers={"x-actor": "tester"})
    session = factory()
    try:
        events = list(session.scalars(
            select(IngestAuditEventOrm).where(IngestAuditEventOrm.action == "healthz.read")
        ))
        assert len(events) >= 1
        assert events[0].decision == "ALLOW"
        assert events[0].result == "SUCCESS"
    finally:
        session.close()


def test_readyz_emits_audit(tmp_path):
    client, factory = _client(tmp_path)
    client.get("/readyz", headers={"x-actor": "tester"})
    session = factory()
    try:
        events = list(session.scalars(
            select(IngestAuditEventOrm).where(IngestAuditEventOrm.action == "readyz.read")
        ))
        assert len(events) >= 1
    finally:
        session.close()


def test_404_emits_not_found_audit(tmp_path):
    client, factory = _client(tmp_path)
    client.get("/api/v1/sources/999999", headers={"x-actor": "tester"})
    session = factory()
    try:
        events = list(session.scalars(
            select(IngestAuditEventOrm).where(IngestAuditEventOrm.result == "NOT_FOUND")
        ))
        assert len(events) >= 1
    finally:
        session.close()


def test_validation_error_emits_audit(tmp_path):
    client, factory = _client(tmp_path)
    client.post(
        "/api/v1/sources",
        json={"ied_name": ""},  # invalid
        headers={"x-actor": "tester"},
    )
    session = factory()
    try:
        events = list(session.scalars(
            select(IngestAuditEventOrm).where(IngestAuditEventOrm.result == "VALIDATION_ERROR")
        ))
        assert len(events) >= 1
    finally:
        session.close()


def test_conflict_emits_audit(tmp_path):
    client, factory = _client(tmp_path)
    client.post(
        "/api/v1/sources",
        json={"ied_name": "conflict-src", "asset_code": "C1", "asset_name": "C1"},
        headers={"x-actor": "tester"},
    )
    # Try creating duplicate
    client.post(
        "/api/v1/sources",
        json={"ied_name": "conflict-src", "asset_code": "C2", "asset_name": "C2"},
        headers={"x-actor": "tester"},
    )
    session = factory()
    try:
        events = list(session.scalars(
            select(IngestAuditEventOrm).where(IngestAuditEventOrm.result == "CONFLICT")
        ))
        assert len(events) >= 1
    finally:
        session.close()
