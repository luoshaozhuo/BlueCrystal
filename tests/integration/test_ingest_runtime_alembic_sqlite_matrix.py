"""Alembic SQLite migration matrix — upgrade head & downgrade base."""

from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect


def _alembic_config(db_url: str) -> Config:
    alembic_ini = Path(__file__).resolve().parents[2] / "alembic.ini"
    config = Config(str(alembic_ini))
    config.set_main_option("sqlalchemy.url", db_url)
    return config


def test_sqlite_upgrade_head_creates_all_tables(tmp_path) -> None:
    db_path = tmp_path / "alembic-sqlite-upgrade.sqlite"
    engine = create_engine(f"sqlite:///{db_path}")
    config = _alembic_config(str(engine.url))
    command.upgrade(config, "head")
    tables = set(inspect(engine).get_table_names())
    required = {
        "ingest_runtime_node",
        "ingest_runtime_job",
        "ingest_job_assignment",
        "ingest_job_lease",
        "ingest_fencing_token",
        "ingest_bundle_metadata",
        "ingest_audit_event",
        "ingest_runtime_config_version",
        "ingest_idempotency_record",
    }
    missing = required - tables
    assert not missing, f"Tables missing after upgrade: {missing}"


def test_sqlite_upgrade_head_has_audit_index(tmp_path) -> None:
    """Verify that upgrade head creates the audit event index."""
    db_path = tmp_path / "alembic-sqlite-index.sqlite"
    engine = create_engine(f"sqlite:///{db_path}")
    config = _alembic_config(str(engine.url))
    command.upgrade(config, "head")
    indexes = {idx["name"] for idx in inspect(engine).get_indexes("ingest_audit_event")}
    assert "ix_ingest_audit_event_action_ts" in indexes


def test_sqlite_upgrade_head_has_stagger_column(tmp_path) -> None:
    """Verify that ingest_runtime_job has stagger_offset_ms column."""
    db_path = tmp_path / "alembic-sqlite-stagger.sqlite"
    engine = create_engine(f"sqlite:///{db_path}")
    config = _alembic_config(str(engine.url))
    command.upgrade(config, "head")
    cols = {c["name"] for c in inspect(engine).get_columns("ingest_runtime_job")}
    assert "stagger_offset_ms" in cols, f"stagger_offset_ms not found in columns: {cols}"


def test_sqlite_downgrade_base_removes_stagger_column(tmp_path) -> None:
    """Upgrade head then downgrade base removes the new column."""
    db_path = tmp_path / "alembic-sqlite-downgrade.sqlite"
    engine = create_engine(f"sqlite:///{db_path}")
    config = _alembic_config(str(engine.url))

    # Upgrade to head
    command.upgrade(config, "head")
    cols_after_upgrade = {c["name"] for c in inspect(engine).get_columns("ingest_runtime_job")}
    assert "stagger_offset_ms" in cols_after_upgrade

    # Downgrade one revision (remove stagger column, keep table)
    command.downgrade(config, "20260527_000001")
    cols_after_downgrade = {c["name"] for c in inspect(engine).get_columns("ingest_runtime_job")}
    assert "stagger_offset_ms" not in cols_after_downgrade


def test_sqlite_upgrade_has_idempotency_table(tmp_path) -> None:
    """Verify that ingest_idempotency_record table is created by migration."""
    db_path = tmp_path / "alembic-sqlite-idempotent-table.sqlite"
    engine = create_engine(f"sqlite:///{db_path}")
    config = _alembic_config(str(engine.url))
    command.upgrade(config, "head")
    tables = set(inspect(engine).get_table_names())
    assert "ingest_idempotency_record" in tables


def test_sqlite_downgrade_upgrade_idempotent(tmp_path) -> None:
    """Downgrade base then upgrade head — must succeed."""
    db_path = tmp_path / "alembic-sqlite-idempotent.sqlite"
    engine = create_engine(f"sqlite:///{db_path}")
    config = _alembic_config(str(engine.url))

    command.upgrade(config, "head")
    command.downgrade(config, "base")
    command.upgrade(config, "head")

    tables = set(inspect(engine).get_table_names())
    assert "ingest_runtime_node" in tables
