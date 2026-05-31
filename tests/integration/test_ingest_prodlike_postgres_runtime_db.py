"""Production-like PostgreSQL runtime DB integration tests.

Uses the compose-managed PostgreSQL instance. Requires:
  WHALE_INGEST_TEST_PG_DSN env var
  or docker compose services running.
"""

from __future__ import annotations

import os

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from whale.ingest.framework.persistence import (
    create_runtime_engine,
    create_runtime_session_factory,
    migrate_runtime_database,
)
from whale.ingest.framework.persistence.runtime_db import probe_runtime_readiness
from whale.shared.persistence.orm.ingest_runtime import (
    IngestAuditEventOrm,
    IngestRuntimeJob,
)

PG_DSN_ENV = "WHALE_INGEST_TEST_PG_DSN"


def _pg_engine():
    dsn = os.environ.get(PG_DSN_ENV)
    if not dsn:
        pytest.skip(f"{PG_DSN_ENV} not set")
    return create_runtime_engine(dsn)


def _pg_session_factory(engine):
    return create_runtime_session_factory(engine)


@pytest.fixture(scope="module")
def pg_engine():
    engine = _pg_engine()
    migrate_runtime_database(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def pg_session(pg_engine):
    session_factory = _pg_session_factory(pg_engine)
    session = session_factory()
    # Clean slate for tables mutated by these tests
    from whale.shared.persistence.orm.ingest_runtime import IngestJobLease, IngestAuditEventOrm, IngestRuntimeJob

    for table in (IngestJobLease, IngestAuditEventOrm, IngestRuntimeJob):
        session.query(table).delete()
    session.commit()
    yield session
    session.rollback()
    session.close()


# ── CRUD roundtrip ─────────────────────────────────────────────────────


def test_postgres_runtime_db_api_crud_roundtrip(pg_session: Session):
    """Create, read, update a scheduler job via PostgreSQL."""
    job = IngestRuntimeJob(
        job_id="prodlike-crud-job",
        job_type="acquisition",
        priority=5,
    )
    pg_session.add(job)
    pg_session.commit()

    fetched = pg_session.get(IngestRuntimeJob, "prodlike-crud-job")
    assert fetched is not None
    assert fetched.job_type == "acquisition"
    assert fetched.priority == 5

    fetched.priority = 10
    pg_session.commit()

    updated = pg_session.get(IngestRuntimeJob, "prodlike-crud-job")
    assert updated.priority == 10

    pg_session.delete(updated)
    pg_session.commit()

    deleted = pg_session.get(IngestRuntimeJob, "prodlike-crud-job")
    assert deleted is None


# ── Scheduler lease unique owner ───────────────────────────────────────


def test_postgres_runtime_db_scheduler_lease_unique_owner(pg_session: Session):
    """Verify lease unique constraint prevents duplicate ownership."""
    from whale.shared.persistence.orm.ingest_runtime import IngestJobLease
    from datetime import UTC, datetime, timedelta

    now = datetime.now(tz=UTC)
    lease = IngestJobLease(
        lease_name="lease:prodlike-job",
        lease_scope="scheduler",
        resource_id="prodlike-job",
        holder_key="worker-a",
        status="ACTIVE",
        fencing_token=1,
        acquired_at=now,
        renewed_at=now,
        expires_at=now + timedelta(seconds=30),
    )
    pg_session.add(lease)
    pg_session.commit()

    # Same lease_name should fail (unique constraint)
    dup = IngestJobLease(
        lease_name="lease:prodlike-job",
        lease_scope="scheduler",
        resource_id="prodlike-job",
        holder_key="worker-b",
        status="ACTIVE",
        fencing_token=1,
        acquired_at=now,
        renewed_at=now,
        expires_at=now + timedelta(seconds=30),
    )
    pg_session.add(dup)
    with pytest.raises(Exception):
        pg_session.commit()
    pg_session.rollback()


# ── Audit event persisted ──────────────────────────────────────────────


def test_postgres_runtime_db_audit_event_persisted(pg_session: Session):
    """Verify audit events are stored in PostgreSQL."""
    event = IngestAuditEventOrm(
        request_id="prodlike-audit-req",
        actor="tester",
        action="test.action",
        resource_type="test",
        resource_id="test-resource",
        decision="ALLOW",
        result="SUCCESS",
        http_status=200,
    )
    pg_session.add(event)
    pg_session.commit()

    fetched = pg_session.query(IngestAuditEventOrm).filter_by(
        request_id="prodlike-audit-req"
    ).first()
    assert fetched is not None
    assert fetched.actor == "tester"
    assert fetched.decision == "ALLOW"


# ── Readiness probe ────────────────────────────────────────────────────


def test_postgres_runtime_db_readyz_fails_when_db_unavailable():
    """probe_runtime_readiness should fail when database is unreachable."""
    bad_engine = create_engine(
        "postgresql+psycopg://whale:whale@127.0.0.1:1/nonexistent",
        future=True,
    )
    with pytest.raises(Exception):
        probe_runtime_readiness(bad_engine)
    bad_engine.dispose()
