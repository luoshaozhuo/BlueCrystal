"""Idempotency-Key coverage across all mutating CRUD route groups.

IdempotencyMiddleware is ASGI-level so it covers all routes automatically.
These tests verify that non-scheduler routes also get idempotency protection.
"""
from __future__ import annotations

from fastapi.testclient import TestClient

from whale.ingest.api import create_app
from whale.ingest.framework.persistence import (
    create_runtime_engine,
    create_runtime_session_factory,
    initialize_runtime_database,
)


def _client(tmp_path):
    engine = create_runtime_engine(f"sqlite:///{tmp_path / 'idem-all.sqlite'}")
    initialize_runtime_database(engine)
    session_factory = create_runtime_session_factory(engine)
    app = create_app(session_factory=session_factory, readiness_probe=lambda: True)
    return TestClient(app)


# ── acquisition_tasks ─────────────────────────────────────────────────────────


def test_idempotency_acquisition_task_post(tmp_path):
    client = _client(tmp_path)
    headers = {"Idempotency-Key": "acq-post", "x-actor": "tester"}

    first = client.post(
        "/api/v1/acquisition-tasks",
        json={"task_name": "idem-acq", "ld_instance_id": 1},
        headers=headers,
    )
    assert first.status_code == 201

    second = client.post(
        "/api/v1/acquisition-tasks",
        json={"task_name": "idem-acq", "ld_instance_id": 1},
        headers=headers,
    )
    assert second.status_code == 201
    assert second.json() == first.json()


def test_idempotency_acquisition_task_post_different_payload_422(tmp_path):
    client = _client(tmp_path)
    headers = {"Idempotency-Key": "acq-conflict", "x-actor": "tester"}

    first = client.post(
        "/api/v1/acquisition-tasks",
        json={"task_name": "idem-acq-2", "ld_instance_id": 1},
        headers=headers,
    )
    assert first.status_code == 201

    second = client.post(
        "/api/v1/acquisition-tasks",
        json={"task_name": "idem-acq-2b", "ld_instance_id": 2},
        headers=headers,
    )
    assert second.status_code == 422
    assert second.json()["error"] == "IDEMPOTENCY_KEY_REUSE"


# ── security_partitions ───────────────────────────────────────────────────────


def test_idempotency_security_partition_post(tmp_path):
    client = _client(tmp_path)
    headers = {"Idempotency-Key": "sec-post", "x-actor": "tester"}

    first = client.post(
        "/api/v1/security-partitions",
        json={"partition_code": "idem-sec", "partition_name": "Idem Sec"},
        headers=headers,
    )
    assert first.status_code == 201

    second = client.post(
        "/api/v1/security-partitions",
        json={"partition_code": "idem-sec", "partition_name": "Idem Sec"},
        headers=headers,
    )
    assert second.status_code == 201
    assert second.json() == first.json()


# ── runtime_config / sources ──────────────────────────────────────────────────


def test_idempotency_source_post(tmp_path):
    client = _client(tmp_path)
    headers = {"Idempotency-Key": "src-post", "x-actor": "tester"}

    first = client.post(
        "/api/v1/sources",
        json={"ied_name": "idem-src", "asset_code": "A01", "asset_name": "Idem Src"},
        headers=headers,
    )
    assert first.status_code == 201

    second = client.post(
        "/api/v1/sources",
        json={"ied_name": "idem-src", "asset_code": "A01", "asset_name": "Idem Src"},
        headers=headers,
    )
    assert second.status_code == 201
    assert second.json() == first.json()


# ── runtime_config / connections ──────────────────────────────────────────────


def test_idempotency_connection_post(tmp_path):
    """Idempotency covers connection create."""
    client = _client(tmp_path)

    # Need a source first
    src = client.post(
        "/api/v1/sources",
        json={"ied_name": "idem-conn-src", "asset_code": "A02", "asset_name": "Conn Src"},
        headers={"x-actor": "tester"},
    )
    assert src.status_code == 201
    source_id = src.json()["source_id"]

    headers = {"Idempotency-Key": "conn-post", "x-actor": "tester"}
    payload = {
        "source_id": source_id,
        "access_point_name": "AP1",
        "application_protocol": "OPC_UA",
        "transport": "TCP",
    }

    first = client.post("/api/v1/connections", json=payload, headers=headers)
    assert first.status_code == 201

    second = client.post("/api/v1/connections", json=payload, headers=headers)
    assert second.status_code == 201
    assert second.json() == first.json()


# ── runtime_config / signal-profiles ──────────────────────────────────────────


def test_idempotency_signal_profile_post(tmp_path):
    client = _client(tmp_path)
    headers = {"Idempotency-Key": "sp-post", "x-actor": "tester"}

    first = client.post(
        "/api/v1/signal-profiles",
        json={"profile_code": "IDEM-SP", "profile_name": "Idem SP"},
        headers=headers,
    )
    assert first.status_code == 201

    second = client.post(
        "/api/v1/signal-profiles",
        json={"profile_code": "IDEM-SP", "profile_name": "Idem SP"},
        headers=headers,
    )
    assert second.status_code == 201
    assert second.json() == first.json()


# ── runtime_config / points ───────────────────────────────────────────────────


def test_idempotency_point_post(tmp_path):
    """Idempotency covers point create."""
    client = _client(tmp_path)

    # Need a signal profile first
    sp = client.post(
        "/api/v1/signal-profiles",
        json={"profile_code": "IDEM-PT", "profile_name": "Idem PT"},
        headers={"x-actor": "tester"},
    )
    assert sp.status_code == 201
    sp_id = sp.json()["signal_profile_id"]

    headers = {"Idempotency-Key": "pt-post", "x-actor": "tester"}
    payload = {
        "signal_profile_id": sp_id,
        "relative_path": "idem/pt",
        "do_name": "IdemPT",
        "data_type_name": "FLOAT",
    }

    first = client.post("/api/v1/points", json=payload, headers=headers)
    assert first.status_code == 201

    second = client.post("/api/v1/points", json=payload, headers=headers)
    assert second.status_code == 201
    assert second.json() == first.json()
