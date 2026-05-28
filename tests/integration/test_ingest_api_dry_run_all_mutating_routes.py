"""Dry-run coverage across all mutating CRUD routes.

Each route group: POST dry_run does not persist, PATCH dry_run validates but
does not persist, DELETE dry_run validates but does not delete.
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
    engine = create_runtime_engine(f"sqlite:///{tmp_path / 'dry-run-all.sqlite'}")
    initialize_runtime_database(engine)
    session_factory = create_runtime_session_factory(engine)
    app = create_app(session_factory=session_factory, readiness_probe=lambda: True)
    return TestClient(app)


# ── acquisition_tasks ─────────────────────────────────────────────────────────


def test_dry_run_acquisition_task_create_does_not_persist(tmp_path):
    client = _client(tmp_path)
    resp = client.post(
        "/api/v1/acquisition-tasks?dry_run=true",
        json={"task_name": "dry-acq", "ld_instance_id": 1},
        headers={"x-actor": "tester"},
    )
    assert resp.status_code == 201
    assert resp.json()["task_name"] == "dry-acq"

    fetched = client.get("/api/v1/acquisition-tasks/1", headers={"x-actor": "tester"})
    assert fetched.status_code == 404


def test_dry_run_acquisition_task_patch_validates_not_persist(tmp_path):
    client = _client(tmp_path)
    created = client.post(
        "/api/v1/acquisition-tasks",
        json={"task_name": "dry-acq-p", "ld_instance_id": 1},
        headers={"x-actor": "tester"},
    )
    assert created.status_code == 201

    resp = client.patch(
        "/api/v1/acquisition-tasks/1?dry_run=true",
        json={"expected_version": 1, "task_name": "DRY-RENAMED"},
        headers={"x-actor": "tester"},
    )
    assert resp.status_code == 200
    assert resp.json()["task_name"] == "dry-acq-p"  # unchanged

    fetched = client.get("/api/v1/acquisition-tasks/1", headers={"x-actor": "tester"})
    assert fetched.json()["task_name"] == "dry-acq-p"  # still original


def test_dry_run_acquisition_task_patch_version_conflict(tmp_path):
    client = _client(tmp_path)
    created = client.post(
        "/api/v1/acquisition-tasks",
        json={"task_name": "dry-acq-pc", "ld_instance_id": 1},
        headers={"x-actor": "tester"},
    )
    assert created.status_code == 201

    resp = client.patch(
        "/api/v1/acquisition-tasks/1?dry_run=true",
        json={"expected_version": 99, "task_name": "FAIL"},
        headers={"x-actor": "tester"},
    )
    assert resp.status_code == 409


def test_dry_run_acquisition_task_delete_validates_not_delete(tmp_path):
    client = _client(tmp_path)
    created = client.post(
        "/api/v1/acquisition-tasks",
        json={"task_name": "dry-acq-d", "ld_instance_id": 1},
        headers={"x-actor": "tester"},
    )
    assert created.status_code == 201

    resp = client.delete(
        "/api/v1/acquisition-tasks/1?expected_version=1&dry_run=true",
        headers={"x-actor": "tester"},
    )
    assert resp.status_code == 204

    # Resource still exists
    fetched = client.get("/api/v1/acquisition-tasks/1", headers={"x-actor": "tester"})
    assert fetched.status_code == 200


def test_dry_run_acquisition_task_delete_version_conflict(tmp_path):
    client = _client(tmp_path)
    created = client.post(
        "/api/v1/acquisition-tasks",
        json={"task_name": "dry-acq-dc", "ld_instance_id": 1},
        headers={"x-actor": "tester"},
    )
    assert created.status_code == 201

    resp = client.delete(
        "/api/v1/acquisition-tasks/1?expected_version=99&dry_run=true",
        headers={"x-actor": "tester"},
    )
    assert resp.status_code == 409


# ── security_partitions ───────────────────────────────────────────────────────


def test_dry_run_security_partition_create_does_not_persist(tmp_path):
    client = _client(tmp_path)
    resp = client.post(
        "/api/v1/security-partitions?dry_run=true",
        json={"partition_code": "dry-sec", "partition_name": "Dry Sec"},
        headers={"x-actor": "tester"},
    )
    assert resp.status_code == 201
    assert resp.json()["partition_code"] == "dry-sec"

    fetched = client.get("/api/v1/security-partitions/1", headers={"x-actor": "tester"})
    assert fetched.status_code == 404


def test_dry_run_security_partition_patch_validates_not_persist(tmp_path):
    client = _client(tmp_path)
    created = client.post(
        "/api/v1/security-partitions",
        json={"partition_code": "dry-sec-p", "partition_name": "Original"},
        headers={"x-actor": "tester"},
    )
    assert created.status_code == 201

    resp = client.patch(
        "/api/v1/security-partitions/1?dry_run=true",
        json={"expected_version": 1, "partition_name": "Dry Renamed"},
        headers={"x-actor": "tester"},
    )
    assert resp.status_code == 200
    assert resp.json()["partition_name"] == "Original"

    fetched = client.get("/api/v1/security-partitions/1", headers={"x-actor": "tester"})
    assert fetched.json()["partition_name"] == "Original"


def test_dry_run_security_partition_delete_validates_not_delete(tmp_path):
    client = _client(tmp_path)
    created = client.post(
        "/api/v1/security-partitions",
        json={"partition_code": "dry-sec-d", "partition_name": "To Delete"},
        headers={"x-actor": "tester"},
    )
    assert created.status_code == 201

    resp = client.delete(
        "/api/v1/security-partitions/1?expected_version=1&dry_run=true",
        headers={"x-actor": "tester"},
    )
    assert resp.status_code == 204

    fetched = client.get("/api/v1/security-partitions/1", headers={"x-actor": "tester"})
    assert fetched.status_code == 200


# ── runtime_config / sources ──────────────────────────────────────────────────


def test_dry_run_source_create_does_not_persist(tmp_path):
    client = _client(tmp_path)
    resp = client.post(
        "/api/v1/sources?dry_run=true",
        json={"ied_name": "dry-src", "asset_code": "A01", "asset_name": "Dry Src"},
        headers={"x-actor": "tester"},
    )
    assert resp.status_code == 201
    assert resp.json()["ied_name"] == "dry-src"

    fetched = client.get("/api/v1/sources/1", headers={"x-actor": "tester"})
    assert fetched.status_code == 404


def test_dry_run_source_patch_validates_not_persist(tmp_path):
    client = _client(tmp_path)
    created = client.post(
        "/api/v1/sources",
        json={"ied_name": "dry-src-p", "asset_code": "A02", "asset_name": "Original"},
        headers={"x-actor": "tester"},
    )
    assert created.status_code == 201

    resp = client.patch(
        "/api/v1/sources/1?dry_run=true",
        json={"expected_version": 1, "ied_name": "DRY-RENAMED"},
        headers={"x-actor": "tester"},
    )
    assert resp.status_code == 200
    assert resp.json()["ied_name"] == "dry-src-p"

    fetched = client.get("/api/v1/sources/1", headers={"x-actor": "tester"})
    assert fetched.json()["ied_name"] == "dry-src-p"


def test_dry_run_source_delete_validates_not_delete(tmp_path):
    client = _client(tmp_path)
    created = client.post(
        "/api/v1/sources",
        json={"ied_name": "dry-src-d", "asset_code": "A03", "asset_name": "To Delete"},
        headers={"x-actor": "tester"},
    )
    assert created.status_code == 201

    resp = client.delete(
        "/api/v1/sources/1?expected_version=1&dry_run=true",
        headers={"x-actor": "tester"},
    )
    assert resp.status_code == 204

    fetched = client.get("/api/v1/sources/1", headers={"x-actor": "tester"})
    assert fetched.status_code == 200


# ── runtime_config / connections ──────────────────────────────────────────────


def _seed_source(client) -> int:
    resp = client.post(
        "/api/v1/sources",
        json={"ied_name": "dry-conn-src", "asset_code": "A99", "asset_name": "Conn Src"},
        headers={"x-actor": "tester"},
    )
    return resp.json()["source_id"]


def test_dry_run_connection_create_does_not_persist(tmp_path):
    client = _client(tmp_path)
    src_id = _seed_source(client)

    resp = client.post(
        f"/api/v1/connections?dry_run=true",
        json={
            "source_id": src_id,
            "access_point_name": "AP1",
            "application_protocol": "OPC_UA",
            "transport": "TCP",
        },
        headers={"x-actor": "tester"},
    )
    assert resp.status_code == 201
    assert resp.json()["source_id"] == src_id

    fetched = client.get("/api/v1/connections/1", headers={"x-actor": "tester"})
    assert fetched.status_code == 404


def test_dry_run_connection_patch_validates_not_persist(tmp_path):
    client = _client(tmp_path)
    src_id = _seed_source(client)

    created = client.post(
        "/api/v1/connections",
        json={
            "source_id": src_id,
            "access_point_name": "AP1",
            "application_protocol": "OPC_UA",
            "transport": "TCP",
        },
        headers={"x-actor": "tester"},
    )
    assert created.status_code == 201

    resp = client.patch(
        "/api/v1/connections/1?dry_run=true",
        json={"expected_version": 1, "access_point_name": "AP2"},
        headers={"x-actor": "tester"},
    )
    assert resp.status_code == 200
    assert resp.json()["access_point_name"] == "AP1"

    fetched = client.get("/api/v1/connections/1", headers={"x-actor": "tester"})
    assert fetched.json()["access_point_name"] == "AP1"


def test_dry_run_connection_delete_validates_not_delete(tmp_path):
    client = _client(tmp_path)
    src_id = _seed_source(client)

    created = client.post(
        "/api/v1/connections",
        json={
            "source_id": src_id,
            "access_point_name": "AP1",
            "application_protocol": "OPC_UA",
            "transport": "TCP",
        },
        headers={"x-actor": "tester"},
    )
    assert created.status_code == 201

    resp = client.delete(
        "/api/v1/connections/1?expected_version=1&dry_run=true",
        headers={"x-actor": "tester"},
    )
    assert resp.status_code == 204

    fetched = client.get("/api/v1/connections/1", headers={"x-actor": "tester"})
    assert fetched.status_code == 200


# ── runtime_config / signal-profiles ──────────────────────────────────────────


def test_dry_run_signal_profile_create_does_not_persist(tmp_path):
    client = _client(tmp_path)
    resp = client.post(
        "/api/v1/signal-profiles?dry_run=true",
        json={"profile_code": "DRY-SP", "profile_name": "Dry SP"},
        headers={"x-actor": "tester"},
    )
    assert resp.status_code == 201
    assert resp.json()["profile_code"] == "DRY-SP"

    fetched = client.get("/api/v1/signal-profiles/1", headers={"x-actor": "tester"})
    assert fetched.status_code == 404


def test_dry_run_signal_profile_patch_validates_not_persist(tmp_path):
    client = _client(tmp_path)
    created = client.post(
        "/api/v1/signal-profiles",
        json={"profile_code": "DRY-SP-P", "profile_name": "Original"},
        headers={"x-actor": "tester"},
    )
    assert created.status_code == 201

    resp = client.patch(
        "/api/v1/signal-profiles/1?dry_run=true",
        json={"expected_version": 1, "profile_name": "Dry Renamed"},
        headers={"x-actor": "tester"},
    )
    assert resp.status_code == 200
    assert resp.json()["profile_name"] == "Original"

    fetched = client.get("/api/v1/signal-profiles/1", headers={"x-actor": "tester"})
    assert fetched.json()["profile_name"] == "Original"


def test_dry_run_signal_profile_delete_validates_not_delete(tmp_path):
    client = _client(tmp_path)
    created = client.post(
        "/api/v1/signal-profiles",
        json={"profile_code": "DRY-SP-D", "profile_name": "To Delete"},
        headers={"x-actor": "tester"},
    )
    assert created.status_code == 201

    resp = client.delete(
        "/api/v1/signal-profiles/1?expected_version=1&dry_run=true",
        headers={"x-actor": "tester"},
    )
    assert resp.status_code == 204

    fetched = client.get("/api/v1/signal-profiles/1", headers={"x-actor": "tester"})
    assert fetched.status_code == 200


# ── runtime_config / points ───────────────────────────────────────────────────


def _seed_signal_profile(client) -> int:
    resp = client.post(
        "/api/v1/signal-profiles",
        json={"profile_code": "DRY-PT-SP", "profile_name": "PT SP"},
        headers={"x-actor": "tester"},
    )
    return resp.json()["signal_profile_id"]


def test_dry_run_point_create_does_not_persist(tmp_path):
    client = _client(tmp_path)
    sp_id = _seed_signal_profile(client)

    resp = client.post(
        f"/api/v1/points?dry_run=true",
        json={
            "signal_profile_id": sp_id,
            "relative_path": "dry/pt",
            "do_name": "DryPT",
            "data_type_name": "FLOAT",
        },
        headers={"x-actor": "tester"},
    )
    assert resp.status_code == 201
    assert resp.json()["signal_profile_id"] == sp_id

    fetched = client.get("/api/v1/points/1", headers={"x-actor": "tester"})
    assert fetched.status_code == 404


def test_dry_run_point_patch_validates_not_persist(tmp_path):
    client = _client(tmp_path)
    sp_id = _seed_signal_profile(client)

    created = client.post(
        "/api/v1/points",
        json={
            "signal_profile_id": sp_id,
            "relative_path": "dry/pt-p",
            "do_name": "DryPT",
            "data_type_name": "FLOAT",
        },
        headers={"x-actor": "tester"},
    )
    assert created.status_code == 201

    resp = client.patch(
        "/api/v1/points/1?dry_run=true",
        json={"expected_version": 1, "do_name": "RenamedPT"},
        headers={"x-actor": "tester"},
    )
    assert resp.status_code == 200
    assert resp.json()["do_name"] == "DryPT"

    fetched = client.get("/api/v1/points/1", headers={"x-actor": "tester"})
    assert fetched.json()["do_name"] == "DryPT"


def test_dry_run_point_delete_validates_not_delete(tmp_path):
    client = _client(tmp_path)
    sp_id = _seed_signal_profile(client)

    created = client.post(
        "/api/v1/points",
        json={
            "signal_profile_id": sp_id,
            "relative_path": "dry/pt-d",
            "do_name": "DryPT",
            "data_type_name": "FLOAT",
        },
        headers={"x-actor": "tester"},
    )
    assert created.status_code == 201

    resp = client.delete(
        "/api/v1/points/1?expected_version=1&dry_run=true",
        headers={"x-actor": "tester"},
    )
    assert resp.status_code == 204

    fetched = client.get("/api/v1/points/1", headers={"x-actor": "tester"})
    assert fetched.status_code == 200
