"""Alembic migration integration tests."""

from __future__ import annotations

import importlib
import importlib.util
from pathlib import Path

from sqlalchemy import inspect
from typer.testing import CliRunner

from whale.ingest.framework.persistence import create_runtime_engine, migrate_runtime_database
from whale.ingest.runtime.cli import app


def test_alembic_upgrade_head_creates_runtime_tables(tmp_path) -> None:
    engine = create_runtime_engine(f"sqlite:///{tmp_path / 'alembic-upgrade.sqlite'}")
    migrate_runtime_database(engine)
    table_names = set(inspect(engine).get_table_names())
    assert "ingest_runtime_node" in table_names
    assert "ingest_job_lease" in table_names
    assert "ingest_audit_event" in table_names


def test_migrate_entrypoint_runs_upgrade_head(tmp_path, monkeypatch) -> None:
    runner = CliRunner()
    monkeypatch.setenv("WHALE_INGEST_DATABASE_BACKEND", "sqlite")
    monkeypatch.setenv("WHALE_INGEST_DB_PATH", str(tmp_path / "runtime.sqlite"))
    monkeypatch.setenv("WHALE_DB_URL", f"sqlite:///{tmp_path / 'shared.sqlite'}")
    monkeypatch.setenv("WHALE_INGEST_REDIS_HOST", "127.0.0.1")
    monkeypatch.setenv("WHALE_INGEST_REDIS_STATE_HASH_KEY", "whale:test:runtime")
    monkeypatch.setenv("WHALE_INGEST_STATION_ID", "station-runtime")
    result = runner.invoke(app, ["migrate"])
    assert result.exit_code == 0


def test_runtime_orm_metadata_matches_migrated_schema_minimum(tmp_path) -> None:
    engine = create_runtime_engine(f"sqlite:///{tmp_path / 'alembic-metadata.sqlite'}")
    migrate_runtime_database(engine)
    columns = {column["name"] for column in inspect(engine).get_columns("ingest_job_lease")}
    assert {"lease_id", "lease_name", "holder_key", "fencing_token", "expires_at"} <= columns


def test_alembic_revision_is_not_empty() -> None:
    path = Path(__file__).resolve().parents[2] / "alembic" / "versions" / "20260527_000001_ingest_runtime_initial.py"
    spec = importlib.util.spec_from_file_location("ingest_runtime_initial_revision", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.revision
