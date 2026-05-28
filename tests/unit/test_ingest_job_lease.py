"""DB-backed lease semantics tests."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from whale.ingest.framework.persistence import (
    create_runtime_engine,
    create_runtime_session_factory,
    initialize_runtime_database,
)
from whale.ingest.runtime.fencing import FencingTokenRepository
from whale.ingest.runtime.lease import LeaseService


def test_job_lease_acquire_renew_release_and_expire(tmp_path) -> None:
    engine = create_runtime_engine(f"sqlite:///{tmp_path / 'lease.sqlite'}")
    initialize_runtime_database(engine)
    session_factory = create_runtime_session_factory(engine)
    service = LeaseService(session_factory, FencingTokenRepository(session_factory))
    now = datetime.now(tz=UTC)

    acquired = service.acquire(
        lease_name="job:1",
        lease_scope="job",
        resource_id="job-1",
        holder_key="node-a",
        ttl_seconds=10,
        now=now,
    )
    assert acquired.acquired is True
    assert acquired.fencing_token == 1

    conflict = service.acquire(
        lease_name="job:1",
        lease_scope="job",
        resource_id="job-1",
        holder_key="node-b",
        ttl_seconds=10,
        now=now + timedelta(seconds=1),
    )
    assert conflict.acquired is False
    assert conflict.reason == "LEASE_CONFLICT"

    renewed = service.renew(
        lease_name="job:1",
        holder_key="node-a",
        ttl_seconds=10,
        now=now + timedelta(seconds=2),
    )
    assert renewed.status == "ACTIVE"
    assert renewed.expires_at > now + timedelta(seconds=10)

    expired_count = service.expire_due_leases(now=now + timedelta(seconds=20))
    assert expired_count == 1

    reacquired = service.acquire(
        lease_name="job:1",
        lease_scope="job",
        resource_id="job-1",
        holder_key="node-b",
        ttl_seconds=10,
        now=now + timedelta(seconds=21),
    )
    assert reacquired.acquired is True
    assert reacquired.fencing_token == 2

    released = service.release(
        lease_name="job:1",
        holder_key="node-b",
        now=now + timedelta(seconds=22),
    )
    assert released.status == "RELEASED"
