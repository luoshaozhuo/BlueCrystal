"""Bundle-metadata query API integration tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from whale.ingest.api import create_app
from whale.ingest.framework.persistence import (
    create_runtime_engine,
    create_runtime_session_factory,
    initialize_runtime_database,
)


def _client(tmp_path):
    engine = create_runtime_engine(f"sqlite:///{tmp_path / 'bundle-api.sqlite'}")
    initialize_runtime_database(engine)
    session_factory = create_runtime_session_factory(engine)
    app = create_app(session_factory=session_factory, readiness_probe=lambda: True)
    return TestClient(app)


def test_bundle_list_and_get(tmp_path):
    client = _client(tmp_path)
    listed = client.get("/api/v1/bundles", headers={"x-actor": "tester"})
    assert listed.status_code == 200
    assert listed.json()["total"] == 0

    # Seed a bundle row directly
    from whale.shared.persistence.orm import IngestBundleMetadata
    from sqlalchemy.orm import Session

    factory = client.app.state.session_factory
    session: Session = factory() if callable(factory) else factory()
    try:
        session.add(IngestBundleMetadata(
            bundle_version="v1", schema_version="1.0", checksum="abc",
            source="test", status="EXPORTED",
        ))
        session.commit()
        bid = session.execute(
            __import__("sqlalchemy").select(IngestBundleMetadata).where(
                IngestBundleMetadata.bundle_version == "v1"
            )
        ).scalar_one().bundle_id
    finally:
        session.close()

    fetched = client.get(f"/api/v1/bundles/{bid}", headers={"x-actor": "tester"})
    assert fetched.status_code == 200
    assert fetched.json()["bundle_version"] == "v1"

    listed2 = client.get("/api/v1/bundles", headers={"x-actor": "tester"})
    assert listed2.status_code == 200
    assert listed2.json()["total"] >= 1
