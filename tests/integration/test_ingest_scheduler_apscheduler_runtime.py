"""Integration tests for WorkerRuntime / APScheduler-driven ingestion."""

from __future__ import annotations

import time
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

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
from whale.ingest.runtime.job_assignment import RuntimeJob
from whale.ingest.runtime.scheduler_settings import SchedulerSettings
from whale.shared.persistence.orm.ingest_runtime import IngestRuntimeJob


class _NoopHandler:
    """Noop handler that records execution for test verification."""

    def execute(self, job: IngestRuntimeJob) -> None:
        pass


@pytest.fixture
def sqlite_session_factory(tmp_path):
    engine = create_runtime_engine(f"sqlite:///{tmp_path / 'worker-test.sqlite'}")
    initialize_runtime_database(engine)
    factory: sessionmaker[Session] = create_runtime_session_factory(engine)
    return factory


@pytest.fixture
def settings():
    return SchedulerSettings(
        runtime_mode=RuntimeMode.STANDALONE,
        node_key="worker-test-1",
        heartbeat_interval_seconds=3600,  # long so they don't fire during test
        lease_ttl_seconds=30,
        pull_max_in_flight=4,
    )


@pytest.fixture
def repos(sqlite_session_factory):
    node_repo = NodeRuntimeRepository(sqlite_session_factory)
    job_repo = RuntimeJobRepository(sqlite_session_factory)
    assignment_repo = JobAssignmentRepository(sqlite_session_factory)
    fencing_repo = FencingTokenRepository(sqlite_session_factory)
    lease_service = LeaseService(sqlite_session_factory, fencing_repo)
    return node_repo, job_repo, assignment_repo, lease_service, fencing_repo


@pytest.fixture
def seeded_job_repo(repos):
    _, job_repo, _, _, _ = repos
    job_repo.upsert_job(
        RuntimeJob(
            job_id="test-job-1",
            job_type="acquisition",
            partition_key="p-1",
            priority=10,
            enabled=True,
            config={"interval_ms": 50},
        )
    )
    return job_repo


def test_worker_runtime_executes_enabled_job_with_lease(tmp_path, settings, repos, seeded_job_repo):
    """Worker assigns and executes an enabled job when lease is acquired."""
    node_repo, job_repo, assignment_repo, lease_service, fencing_repo = repos
    metrics = WorkerRuntimeMetrics()
    worker = WorkerRuntime(
        settings=settings,
        node_repository=node_repo,
        job_repository=job_repo,
        assignment_repository=assignment_repo,
        lease_service=lease_service,
        fencing_token_repository=fencing_repo,
        audit_sink=None,
        metrics=metrics,
        handlers={
            "acquisition": _NoopHandler(),
        },
    )

    # Simulate one reconcile tick
    from datetime import UTC, datetime

    now = datetime.now(tz=UTC)
    worker._scheduler.heartbeat(now=now)
    snapshot = worker._scheduler.assign_jobs(now=now)
    assert "test-job-1" in snapshot.assigned_jobs

    worker._execute_one(job_id="test-job-1", fencing_token=snapshot.fencing_tokens["test-job-1"], now=now)

    snap = metrics.snapshot()
    assert snap.get("job_started", 0) >= 1
    assert snap.get("job_completed", 0) >= 1


def test_worker_runtime_does_not_execute_without_lease(tmp_path, settings, repos, seeded_job_repo):
    """Worker skips execution when lease does not belong to this node."""
    node_repo, job_repo, assignment_repo, lease_service, fencing_repo = repos
    metrics = WorkerRuntimeMetrics()
    worker = WorkerRuntime(
        settings=settings,
        node_repository=node_repo,
        job_repository=job_repo,
        assignment_repository=assignment_repo,
        lease_service=lease_service,
        fencing_token_repository=fencing_repo,
        audit_sink=None,
        metrics=metrics,
    )

    now = datetime.now(tz=UTC)
    worker._scheduler.heartbeat(now=now)
    worker._scheduler.assign_jobs(now=now)

    # Acquire lease from a different node manually so our worker's fencing token fails
    lease_service.acquire(
        lease_name="job:test-job-1",
        lease_scope="job",
        resource_id="test-job-1",
        holder_key="other-node",
        ttl_seconds=30,
        now=now,
    )

    # Worker calls _execute_one with current fencing token -> lease held by other-node
    # so validate_execution will reject it
    decision = worker._scheduler.validate_execution(
        job_id="test-job-1",
        holder_key=settings.node_key,
        fencing_token=999999,
        now=now,
    )
    assert not decision.allowed

    snap = metrics.snapshot()
    # If we call _execute_one with bad token, it'll skip
    worker._execute_one(job_id="test-job-1", fencing_token=999999, now=now)
    snap2 = metrics.snapshot()
    assert snap2.get("job_skipped_no_lease", 0) >= 1


def test_worker_runtime_records_missed_tick_on_overrun(tmp_path, settings, repos, seeded_job_repo):
    """Worker records missed_tick when execution exceeds the configured interval."""
    node_repo, job_repo, assignment_repo, lease_service, fencing_repo = repos
    metrics = WorkerRuntimeMetrics()

    class SlowWorker(WorkerRuntime):
        def _do_execute(self, job_row):
            time.sleep(0.1)  # 100ms > 50ms interval -> missed tick

    worker = SlowWorker(
        settings=settings,
        node_repository=node_repo,
        job_repository=job_repo,
        assignment_repository=assignment_repo,
        lease_service=lease_service,
        fencing_token_repository=fencing_repo,
        audit_sink=None,
        metrics=metrics,
    )

    now = datetime.now(tz=UTC)
    worker._scheduler.heartbeat(now=now)
    snapshot = worker._scheduler.assign_jobs(now=now)
    assert "test-job-1" in snapshot.assigned_jobs

    worker._execute_one(job_id="test-job-1", fencing_token=snapshot.fencing_tokens["test-job-1"], now=now)

    snap = metrics.snapshot()
    assert snap.get("missed_tick", 0) >= 1, f"missed_tick not recorded: {snap}"


def test_worker_runtime_preserves_stagger_offset(tmp_path, settings, repos):
    """Worker applies stagger_offset_ms from job config."""
    node_repo, job_repo, assignment_repo, lease_service, fencing_repo = repos
    job_repo.upsert_job(
        RuntimeJob(
            job_id="stagger-job",
            job_type="acquisition",
            partition_key="p-2",
            priority=10,
            enabled=True,
            config={"interval_ms": 200, "stagger_offset_ms": 50},
        )
    )
    metrics = WorkerRuntimeMetrics()
    worker = WorkerRuntime(
        settings=settings,
        node_repository=node_repo,
        job_repository=job_repo,
        assignment_repository=assignment_repo,
        lease_service=lease_service,
        fencing_token_repository=fencing_repo,
        audit_sink=None,
        metrics=metrics,
    )

    now = datetime.now(tz=UTC)
    worker._scheduler.heartbeat(now=now)
    snapshot = worker._scheduler.assign_jobs(now=now)
    assert "stagger-job" in snapshot.assigned_jobs

    started_at = time.monotonic()
    worker._execute_one(
        job_id="stagger-job",
        fencing_token=snapshot.fencing_tokens["stagger-job"],
        now=now,
    )
    elapsed = (time.monotonic() - started_at) * 1000
    # With 50ms stagger, execution should take at least 40ms
    assert elapsed >= 40, f"Stagger too short: {elapsed}ms"


def test_worker_runtime_graceful_shutdown_releases_or_expires_lease(tmp_path, settings, repos, seeded_job_repo):
    """Graceful shutdown cancels scheduled jobs and releases owned leases."""
    node_repo, job_repo, assignment_repo, lease_service, fencing_repo = repos
    metrics = WorkerRuntimeMetrics()
    worker = WorkerRuntime(
        settings=settings,
        node_repository=node_repo,
        job_repository=job_repo,
        assignment_repository=assignment_repo,
        lease_service=lease_service,
        fencing_token_repository=fencing_repo,
        audit_sink=None,
        metrics=metrics,
    )

    # First acquire a lease for this node
    now = datetime.now(tz=UTC)
    worker._scheduler.heartbeat(now=now)
    worker._scheduler.assign_jobs(now=now)

    # Verify lease exists
    lease = lease_service.get_snapshot(lease_name="job:test-job-1")
    assert lease is not None, "Lease should have been acquired"
    assert lease.holder_key == settings.node_key

    # Shutdown
    final_metrics = worker.stop(timeout_seconds=5)

    # After shutdown, the lease should be released or expired
    lease_after = lease_service.get_snapshot(lease_name="job:test-job-1")
    assert lease_after is not None
    assert lease_after.status in ("RELEASED", "EXPIRED")

    assert isinstance(final_metrics, dict)
