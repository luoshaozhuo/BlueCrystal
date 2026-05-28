"""Security-partition CRUD integration tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from whale.ingest.api import create_app
from whale.ingest.framework.persistence import (
    create_runtime_engine,
    create_runtime_session_factory,
    initialize_runtime_database,
)


def _client(tmp_path):
    engine = create_runtime_engine(f"sqlite:///{tmp_path / 'sec-part.sqlite'}")
    initialize_runtime_database(engine)
    session_factory = create_runtime_session_factory(engine)
    app = create_app(session_factory=session_factory, readiness_probe=lambda: True)
    return TestClient(app)


def test_security_partition_crud_roundtrip(tmp_path):
    client = _client(tmp_path)
    created = client.post(
        "/api/v1/security-partitions",
        json={"partition_code": "ZONE-A", "partition_name": "Zone A", "security_zone": "PROTECTION"},
        headers={"x-actor": "tester"},
    )
    assert created.status_code == 201
    pid = created.json()["partition_id"]

    fetched = client.get(f"/api/v1/security-partitions/{pid}", headers={"x-actor": "tester"})
    assert fetched.status_code == 200
    assert fetched.json()["partition_code"] == "ZONE-A"

    listed = client.get("/api/v1/security-partitions", headers={"x-actor": "tester"})
    assert listed.status_code == 200
    assert listed.json()["total"] >= 1

    patched = client.patch(
        f"/api/v1/security-partitions/{pid}",
        json={"expected_version": 1, "partition_name": "Zone A Updated"},
        headers={"x-actor": "tester"},
    )
    assert patched.status_code == 200

    deleted = client.delete(f"/api/v1/security-partitions/{pid}?expected_version=2", headers={"x-actor": "tester"})
    assert deleted.status_code == 204
