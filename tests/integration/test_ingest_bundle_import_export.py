"""Bundle import/export integration tests."""

from __future__ import annotations

import pytest
from sqlalchemy import select

from whale.ingest.bundle.service import BundleService
from whale.ingest.framework.persistence import (
    create_runtime_engine,
    create_runtime_session_factory,
    initialize_runtime_database,
)
from whale.shared.persistence.orm import AcquisitionTask, IngestBundleMetadata, IngestRuntimeConfigVersion


def test_bundle_export_and_import_round_trip(tmp_path) -> None:
    engine = create_runtime_engine(f"sqlite:///{tmp_path / 'bundle.sqlite'}")
    initialize_runtime_database(engine)
    session_factory = create_runtime_session_factory(engine)

    session = session_factory()
    session.add(
        AcquisitionTask(
            task_name="task-1",
            ld_instance_id=1,
            acquisition_mode="POLLING",
            task_status="STOPPED",
            request_timeout_ms=500,
            poll_interval_ms=100,
            enabled=True,
            priority=10,
            assignment_policy="AUTO",
            version=1,
        )
    )
    session.commit()
    session.close()

    service = BundleService(session_factory)
    raw_bundle = service.export_bundle(source="test", actor="tester", redacted=False, bundle_version="bundle-v1")
    redacted_bundle = service.export_bundle(source="test", actor="tester", redacted=True, bundle_version="bundle-v2")

    assert raw_bundle.redacted is False
    assert redacted_bundle.redacted is True

    imported = service.import_bundle(raw_bundle, actor="tester", dry_run=False)
    assert imported.imported_count == 1

    with pytest.raises(ValueError):
        service.import_bundle(redacted_bundle, actor="tester", dry_run=False)

    session = session_factory()
    try:
        metadata_versions = [row.bundle_version for row in session.scalars(select(IngestBundleMetadata))]
        current_version = session.execute(
            select(IngestRuntimeConfigVersion).where(IngestRuntimeConfigVersion.scope == "acquisition_tasks")
        ).scalar_one()
    finally:
        session.close()

    assert "bundle-v1" in metadata_versions
    assert "bundle-v2" in metadata_versions
    assert current_version.accepted_bundle_version == "bundle-v1"
