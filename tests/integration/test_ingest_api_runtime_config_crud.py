"""Runtime-config CRUD integration tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from whale.ingest.api import create_app
from whale.ingest.framework.persistence import create_runtime_engine, create_runtime_session_factory, initialize_runtime_database


def _build_client(tmp_path):
    engine = create_runtime_engine(f"sqlite:///{tmp_path / 'runtime-config-api.sqlite'}")
    initialize_runtime_database(engine)
    session_factory = create_runtime_session_factory(engine)
    app = create_app(session_factory=session_factory, readiness_probe=lambda: True)
    return TestClient(app)


def test_source_crud_roundtrip(tmp_path) -> None:
    client = _build_client(tmp_path)
    created = client.post(
        "/api/v1/sources",
        json={"ied_name": "IED-1", "asset_code": "SRC-1", "asset_name": "Source 1"},
        headers={"x-actor": "tester"},
    )
    assert created.status_code == 201
    source_id = created.json()["source_id"]
    assert client.get(f"/api/v1/sources/{source_id}", headers={"x-actor": "tester"}).status_code == 200
    listed = client.get("/api/v1/sources?limit=10&offset=0", headers={"x-actor": "tester"})
    assert listed.status_code == 200
    assert listed.json()["total"] == 1
    patched = client.patch(
        f"/api/v1/sources/{source_id}",
        json={"expected_version": 1, "asset_name": "Source 1 Updated"},
        headers={"x-actor": "tester"},
    )
    assert patched.status_code == 200
    assert patched.json()["version"] == 2
    deleted = client.delete(f"/api/v1/sources/{source_id}?expected_version=2", headers={"x-actor": "tester"})
    assert deleted.status_code == 204


def test_connection_crud_roundtrip(tmp_path) -> None:
    client = _build_client(tmp_path)
    source_id = client.post(
        "/api/v1/sources",
        json={"ied_name": "IED-1", "asset_code": "SRC-1", "asset_name": "Source 1"},
        headers={"x-actor": "tester"},
    ).json()["source_id"]
    created = client.post(
        "/api/v1/connections",
        json={
            "source_id": source_id,
            "access_point_name": "AP1",
            "application_protocol": "OPC_UA",
            "transport": "TCP",
            "host": "127.0.0.1",
            "port": 4840,
        },
        headers={"x-actor": "tester"},
    )
    assert created.status_code == 201
    connection_id = created.json()["connection_id"]
    assert client.get(f"/api/v1/connections/{connection_id}", headers={"x-actor": "tester"}).status_code == 200
    patched = client.patch(
        f"/api/v1/connections/{connection_id}",
        json={"expected_version": 1, "host": "127.0.0.2"},
        headers={"x-actor": "tester"},
    )
    assert patched.status_code == 200
    assert patched.json()["version"] == 2
    assert client.delete(f"/api/v1/connections/{connection_id}?expected_version=2", headers={"x-actor": "tester"}).status_code == 204


def test_point_crud_roundtrip(tmp_path) -> None:
    client = _build_client(tmp_path)
    profile_id = client.post(
        "/api/v1/signal-profiles",
        json={"profile_code": "P1", "profile_name": "Profile 1"},
        headers={"x-actor": "tester"},
    ).json()["signal_profile_id"]
    created = client.post(
        "/api/v1/points",
        json={
            "signal_profile_id": profile_id,
            "relative_path": "MMXU1.TotW.mag.f",
            "do_name": "TotW",
            "data_type_name": "FLOAT64",
        },
        headers={"x-actor": "tester"},
    )
    assert created.status_code == 201
    point_id = created.json()["point_id"]
    assert client.get(f"/api/v1/points/{point_id}", headers={"x-actor": "tester"}).status_code == 200
    patched = client.patch(
        f"/api/v1/points/{point_id}",
        json={"expected_version": 1, "display_name": "Power"},
        headers={"x-actor": "tester"},
    )
    assert patched.status_code == 200
    assert patched.json()["version"] == 2
    assert client.delete(f"/api/v1/points/{point_id}?expected_version=2", headers={"x-actor": "tester"}).status_code == 204


def test_signal_profile_crud_roundtrip(tmp_path) -> None:
    client = _build_client(tmp_path)
    created = client.post(
        "/api/v1/signal-profiles",
        json={"profile_code": "P1", "profile_name": "Profile 1", "version_label": "v1"},
        headers={"x-actor": "tester"},
    )
    assert created.status_code == 201
    profile_id = created.json()["signal_profile_id"]
    assert client.get(f"/api/v1/signal-profiles/{profile_id}", headers={"x-actor": "tester"}).status_code == 200
    patched = client.patch(
        f"/api/v1/signal-profiles/{profile_id}",
        json={"expected_version": 1, "description": "Updated"},
        headers={"x-actor": "tester"},
    )
    assert patched.status_code == 200
    assert patched.json()["version"] == 2
    assert client.delete(f"/api/v1/signal-profiles/{profile_id}?expected_version=2", headers={"x-actor": "tester"}).status_code == 204


def test_expected_version_conflict(tmp_path) -> None:
    client = _build_client(tmp_path)
    source_id = client.post(
        "/api/v1/sources",
        json={"ied_name": "IED-1", "asset_code": "SRC-1", "asset_name": "Source 1"},
        headers={"x-actor": "tester"},
    ).json()["source_id"]
    conflict_response = client.patch(
        f"/api/v1/sources/{source_id}",
        json={"expected_version": 99, "asset_name": "oops"},
        headers={"x-actor": "tester"},
    )
    assert conflict_response.status_code == 409
