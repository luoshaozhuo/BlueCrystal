"""Runtime DB initialization smoke."""

from __future__ import annotations

from sqlalchemy import inspect

from whale.ingest.framework.persistence import (
    create_runtime_engine,
    initialize_runtime_database,
)


def test_runtime_db_init_creates_runtime_tables(tmp_path) -> None:
    engine = create_runtime_engine(f"sqlite:///{tmp_path / 'runtime.sqlite'}")
    initialize_runtime_database(engine)

    table_names = set(inspect(engine).get_table_names())
    assert "ingest_runtime_node" in table_names
    assert "ingest_runtime_job" in table_names
    assert "ingest_job_assignment" in table_names
    assert "ingest_job_lease" in table_names
    assert "ingest_fencing_token" in table_names
    assert "ingest_bundle_metadata" in table_names
    assert "ingest_audit_event" in table_names
    assert "ingest_runtime_config_version" in table_names
