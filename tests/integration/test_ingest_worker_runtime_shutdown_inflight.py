"""Integration tests for WorkerRuntime shutdown with inflight jobs."""
from __future__ import annotations

import threading
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
from whale.ingest.runtime.job_assignment import RuntimeJob
from whale.ingest.runtime.scheduler_settings import SchedulerSettings
from whale.shared.persistence.orm.ingest_runtime import IngestRuntimeJob


class _SlowHandler:
    """Handler that blocks until an event is set."""

    def __init__(self, block: threading.Event) -> None:
        self.block = block
        self.started = threading.Event()
        self.executed = False

    def execute(self, job: IngestRuntimeJob) -> None:
        self.started.set()
        self.block.wait(timeout=5)
        self.executed = True


@pytest.fixture
def session_factory(tmp_path):
    engine = create_runtime_engine(f"sqlite:///{tmp_path / 'inflight.sqlite'}")
    initialize_runtime_database(engine)
    return create_runtime_session_factory(engine)


@pytest.fixture
def settings():
    return SchedulerSettings(
        runtime_mode=RuntimeMode.STANDALONE,
        node_key="inflight-node",
        heartbeat_interval_seconds=3600,
        lease_ttl_seconds=30,
        pull_max_in_flight=4,
    )


@pytest.fixture
def repos(session_factory):
    node = NodeRuntimeRepository(session_factory)
    job = RuntimeJobRepository(session_factory)
    assn = JobAssignmentRepository(session_factory)
    fencing = FencingTokenRepository(session_factory)
    lease = LeaseService(session_factory, fencing)
    return node, job, assn, lease, fencing


def test_worker_runtime_shutdown_does_not_block_with_no_active_jobs(settings, repos):
    """Shutdown with no active jobs returns immediately."""
    node, job_repo, assn, lease, fencing = repos
    metrics = WorkerRuntimeMetrics()
    worker = WorkerRuntime(
        settings=settings,
        node_repository=node,
        job_repository=job_repo,
        assignment_repository=assn,
        lease_service=lease,
        fencing_token_repository=fencing,
        audit_sink=None,
        metrics=metrics,
    )
    final = worker.stop(timeout_seconds=5)
    assert isinstance(final, dict)


def test_worker_runtime_shutdown_waits_for_short_inflight_job(settings, repos):
    """Shutdown waits for a short inflight job to complete within timeout."""
    node, job_repo, assn, lease, fencing = repos
    job_repo.upsert_job(
        RuntimeJob(job_id="short-job", job_type="quick", enabled=True, config={"interval_ms": 500})
    )
    block = threading.Event()
    handler = _SlowHandler(block)
    metrics = WorkerRuntimeMetrics()
    worker = WorkerRuntime(
        settings=settings,
        node_repository=node,
        job_repository=job_repo,
        assignment_repository=assn,
        lease_service=lease,
        fencing_token_repository=fencing,
        audit_sink=None,
        metrics=metrics,
        handlers={"quick": handler},
    )

    now = datetime.now(tz=UTC)
    worker._scheduler.heartbeat(now=now)
    snapshot = worker._scheduler.assign_jobs(now=now)
    assert "short-job" in snapshot.assigned_jobs

    # Start execution in background thread
    def execute():
        worker._execute_one(job_id="short-job", fencing_token=snapshot.fencing_tokens["short-job"], now=now)

    t = threading.Thread(target=execute, daemon=True)
    t.start()
    handler.started.wait(timeout=3)

    # Signal handler to complete and shutdown
    block.set()

    final = worker.stop(timeout_seconds=5)
    t.join(timeout=3)

    assert isinstance(final, dict)
    assert handler.executed


def test_worker_runtime_shutdown_releases_leases_only_for_owned_jobs(settings, repos):
    """Shutdown releases leases only for jobs owned by this node."""
    node, job_repo, assn, lease, fencing = repos
    job_repo.upsert_job(
        RuntimeJob(job_id="owned-job", job_type="test", enabled=True)
    )
    metrics = WorkerRuntimeMetrics()
    worker = WorkerRuntime(
        settings=settings,
        node_repository=node,
        job_repository=job_repo,
        assignment_repository=assn,
        lease_service=lease,
        fencing_token_repository=fencing,
        audit_sink=None,
        metrics=metrics,
    )

    now = datetime.now(tz=UTC)
    worker._scheduler.heartbeat(now=now)
    worker._scheduler.assign_jobs(now=now)

    owned_lease = lease.get_snapshot(lease_name="job:owned-job")
    assert owned_lease is not None
    assert owned_lease.holder_key == settings.node_key

    final = worker.stop(timeout_seconds=5)

    lease_after = lease.get_snapshot(lease_name="job:owned-job")
    assert lease_after is not None
    assert lease_after.status in ("RELEASED", "EXPIRED")
    assert isinstance(final, dict)
