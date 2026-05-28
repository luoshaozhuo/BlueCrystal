"""Runtime ORM model registration tests."""

from __future__ import annotations

from whale.shared.persistence import Base
import whale.shared.persistence.orm  # noqa: F401


def test_runtime_tables_are_registered_in_metadata() -> None:
    table_names = set(Base.metadata.tables)
    assert "ingest_runtime_node" in table_names
    assert "ingest_runtime_job" in table_names
    assert "ingest_job_assignment" in table_names
    assert "ingest_job_lease" in table_names
    assert "ingest_fencing_token" in table_names
    assert "ingest_bundle_metadata" in table_names
    assert "ingest_audit_event" in table_names
    assert "ingest_runtime_config_version" in table_names
