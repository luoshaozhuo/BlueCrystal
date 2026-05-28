"""Alembic PostgreSQL migration matrix — upgrade head & verify schema.

PostgreSQL must be accessible for these tests.  They are skipped when no
PostgreSQL is available (e.g. CI without PG service).
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text

_PG_DSN = os.environ.get(
    "WHALE_INGEST_TEST_PG_DSN",
    "postgresql+psycopg://whale:whale@127.0.0.1:5432/whale_ingest",
)


def _pg_reachable() -> bool:
    try:
        eng = create_engine(_PG_DSN)
        with eng.connect():
            pass
        eng.dispose()
        return True
    except Exception:
        return False


def _alembic_config(db_url: str) -> Config:
    alembic_ini = Path(__file__).resolve().parents[2] / "alembic.ini"
    config = Config(str(alembic_ini))
    config.set_main_option("sqlalchemy.url", db_url)
    return config


def _reset_ingest_schema(engine) -> None:
    """Drop all ingest tables and alembic version for a clean upgrade start."""
    with engine.connect() as conn:
        conn.execution_options(isolation_level="AUTOCOMMIT")
        for tbl in [
            "alembic_version",
            "ingest_audit_event",
            "ingest_bundle_metadata",
            "ingest_fencing_token",
            "ingest_job_lease",
            "ingest_job_assignment",
            "ingest_runtime_job",
            "ingest_runtime_node",
            "ingest_runtime_config_version",
            "ingest_idempotency_record",
        ]:
            conn.execute(text(f"DROP TABLE IF EXISTS {tbl} CASCADE"))


@pytest.mark.skipif(not _pg_reachable(), reason="PostgreSQL not reachable")
def test_postgres_upgrade_head_creates_all_tables() -> None:
    engine = create_engine(_PG_DSN)
    config = _alembic_config(_PG_DSN)

    _reset_ingest_schema(engine)

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
    assert not missing, f"PG tables missing after upgrade: {missing}"


@pytest.mark.skipif(not _pg_reachable(), reason="PostgreSQL not reachable")
def test_postgres_upgrade_head_has_audit_index() -> None:
    engine = create_engine(_PG_DSN)
    config = _alembic_config(_PG_DSN)
    _reset_ingest_schema(engine)
    command.upgrade(config, "head")
    indexes = {
        idx["name"]
        for idx in inspect(engine).get_indexes("ingest_audit_event")
        if idx["name"] is not None
    }
    assert "ix_ingest_audit_event_action_ts" in indexes


@pytest.mark.skipif(not _pg_reachable(), reason="PostgreSQL not reachable")
def test_postgres_downgrade_base_then_upgrade_head() -> None:
    engine = create_engine(_PG_DSN)
    config = _alembic_config(_PG_DSN)
    _reset_ingest_schema(engine)
    command.upgrade(config, "head")
    command.downgrade(config, "base")
    command.upgrade(config, "head")
    tables = set(inspect(engine).get_table_names())
    assert "ingest_runtime_node" in tables
