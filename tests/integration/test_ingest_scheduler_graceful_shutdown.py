"""Integration tests for WorkerRuntime graceful shutdown."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from whale.ingest.framework.persistence import (
    create_runtime_engine,
    create_runtime_session_factory,
    initialize_runtime_database,
)
from whale.ingest.runtime import (
    FencingTokenRepository,
    JobAssignmentRepository,
    LeaseService,
    NodeRuntimeRepository,
    RuntimeJobRepository,
    RuntimeMode,
    WorkerRuntime,
    WorkerRuntimeMetrics,
)
from whale.ingest.runtime.job_assignment import JobAssignment, RuntimeJob
from whale.ingest.runtime.scheduler_settings import SchedulerSettings


@pytest.fixture
def session_factory(tmp_path):
    engine = create_runtime_engine(f"sqlite:///{tmp_path / 'shutdown-test.sqlite'}")
    initialize_runtime_database(engine)
    return create_runtime_session_factory(engine)


@pytest.fixture
def settings():
    return SchedulerSettings(
        runtime_mode=RuntimeMode.STANDALONE,
        node_key="shutdown-node",
        heartbeat_interval_seconds=3600,
        lease_ttl_seconds=30,
        pull_max_in_flight=4,
    )


@pytest.fixture
def repos(session_factory):
    node = NodeRuntimeRepository(session_factory)
    job = RuntimeJobRepository(session_factory)
    assign = JobAssignmentRepository(session_factory)
    fencing = FencingTokenRepository(session_factory)
    lease = LeaseService(session_factory, fencing)
    return node, job, assign, lease, fencing


def test_worker_graceful_shutdown_releases_leases(settings, repos):
    """Shutdown releases all owned leases."""
    node, job_repo, assign, lease, fencing = repos
    job_repo.upsert_job(
        RuntimeJob(job_id="shutdown-job", job_type="acquisition", enabled=True)
    )
    metrics = WorkerRuntimeMetrics()
    worker = WorkerRuntime(
        settings=settings,
        node_repository=node,
        job_repository=job_repo,
        assignment_repository=assign,
        lease_service=lease,
        fencing_token_repository=fencing,
        audit_sink=None,
        metrics=metrics,
    )

    now = datetime.now(tz=UTC)
    worker._scheduler.heartbeat(now=now)
    worker._scheduler.assign_jobs(now=now)

    lease_snap = lease.get_snapshot(lease_name="job:shutdown-job")
    assert lease_snap is not None and lease_snap.status == "ACTIVE"

    final = worker.stop(timeout_seconds=5)

    lease_after = lease.get_snapshot(lease_name="job:shutdown-job")
    assert lease_after is not None
    assert lease_after.status in ("RELEASED", "EXPIRED")
    assert isinstance(final, dict)


def test_worker_graceful_shutdown_with_no_active_jobs(settings, repos):
    """Shutdown with no active jobs succeeds cleanly."""
    node, job_repo, assign, lease, fencing = repos
    metrics = WorkerRuntimeMetrics()
    worker = WorkerRuntime(
        settings=settings,
        node_repository=node,
        job_repository=job_repo,
        assignment_repository=assign,
        lease_service=lease,
        fencing_token_repository=fencing,
        audit_sink=None,
        metrics=metrics,
    )
    final = worker.stop(timeout_seconds=5)
    assert isinstance(final, dict)


def test_worker_graceful_shutdown_releases_only_owned_leases(settings, repos):
    """Shutdown only releases leases matching our node_key."""
    node, job_repo, assign, lease, fencing = repos
    job_repo.upsert_job(
        RuntimeJob(job_id="owned-job", job_type="acquisition", enabled=True)
    )
    job_repo.upsert_job(
        RuntimeJob(job_id="other-job", job_type="acquisition", enabled=True)
    )
    metrics = WorkerRuntimeMetrics()

    now = datetime.now(tz=UTC)

    # Manually acquire lease for "other-job" from a different node
    lease.acquire(
        lease_name="job:other-job",
        lease_scope="job",
        resource_id="other-job",
        holder_key="other-node",
        ttl_seconds=30,
        now=now,
    )

    # Directly acquire the lease for owned-job and create the assignment,
    # bypassing assign_jobs() to avoid multi-node partitioning in STANDALONE mode.
    lease.acquire(
        lease_name="job:owned-job",
        lease_scope="job",
        resource_id="owned-job",
        holder_key=settings.node_key,
        ttl_seconds=30,
        now=now,
    )
    assign.assign(
        JobAssignment(
            job_id="owned-job",
            node_key=settings.node_key,
            active=True,
            assigned_at=now,
        )
    )

    # Our worker only needs _scheduler for the release-on-stop path
    worker = WorkerRuntime(
        settings=settings,
        node_repository=node,
        job_repository=job_repo,
        assignment_repository=assign,
        lease_service=lease,
        fencing_token_repository=fencing,
        audit_sink=None,
        metrics=metrics,
    )

    owned_lease = lease.get_snapshot(lease_name="job:owned-job")
    assert owned_lease is not None and owned_lease.holder_key == settings.node_key

    other_lease = lease.get_snapshot(lease_name="job:other-job")
    assert other_lease is not None and other_lease.holder_key == "other-node"

    worker.stop(timeout_seconds=5)

    owned_after = lease.get_snapshot(lease_name="job:owned-job")
    assert owned_after is not None
    assert owned_after.status in ("RELEASED", "EXPIRED")

    other_after = lease.get_snapshot(lease_name="job:other-job")
    assert other_after is not None and other_after.holder_key == "other-node"
