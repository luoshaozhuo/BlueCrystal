"""Integration tests for the migrate CLI entrypoint."""

from __future__ import annotations

from sqlalchemy import inspect

from typer.testing import CliRunner

from whale.ingest.framework.persistence import create_runtime_engine, migrate_runtime_database
from whale.ingest.runtime.cli import app


def test_migrate_entrypoint_runs_via_alembic(tmp_path) -> None:
    """`whale-ingest-runtime migrate` runs Alembic upgrade head."""
    runner = CliRunner()
    db_path = tmp_path / "migrate-entry.sqlite"
    result = runner.invoke(
        app,
        ["migrate"],
        env={
            "WHALE_INGEST_DATABASE_BACKEND": "sqlite",
            "WHALE_INGEST_DB_PATH": str(db_path),
            "WHALE_DB_URL": f"sqlite:///{tmp_path / 'shared.sqlite'}",
            "WHALE_INGEST_REDIS_HOST": "127.0.0.1",
            "WHALE_INGEST_REDIS_STATE_HASH_KEY": "whale:test:migrate",
            "WHALE_INGEST_STATION_ID": "station-migrate",
        },
    )
    assert result.exit_code == 0
    engine = create_runtime_engine(f"sqlite:///{db_path}")
    tables = set(inspect(engine).get_table_names())
    assert "ingest_runtime_node" in tables
    assert "ingest_audit_event" in tables


def test_migrate_database_function_direct(tmp_path) -> None:
    """migrate_runtime_database upgrades schema directly."""
    db_path = tmp_path / "direct-migrate.sqlite"
    engine = create_runtime_engine(f"sqlite:///{db_path}")
    migrate_runtime_database(engine)
    tables = set(inspect(engine).get_table_names())
    assert "ingest_runtime_job" in tables
    # Verify second revision column is present
    cols = {c["name"] for c in inspect(engine).get_columns("ingest_runtime_job")}
    assert "stagger_offset_ms" in cols


def test_migrate_idempotent(tmp_path) -> None:
    """Running migrate twice succeeds."""
    db_path = tmp_path / "idempotent-migrate.sqlite"
    engine = create_runtime_engine(f"sqlite:///{db_path}")
    migrate_runtime_database(engine)
    migrate_runtime_database(engine)  # second call
    tables = set(inspect(engine).get_table_names())
    assert "ingest_runtime_node" in tables
