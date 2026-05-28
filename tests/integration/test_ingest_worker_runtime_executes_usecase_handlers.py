"""Integration tests for WorkerRuntime job-type handler dispatch."""
from __future__ import annotations

from datetime import UTC, datetime

import pytest
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


class _RecordingHandler:
    """Handler that records execution for verification."""

    def __init__(self) -> None:
        self.executed_jobs: list[str] = []
        self.last_job: IngestRuntimeJob | None = None

    def execute(self, job: IngestRuntimeJob) -> None:
        self.executed_jobs.append(job.job_id)
        self.last_job = job


class _RaisingHandler:
    """Handler that raises to test failure path."""

    def execute(self, job: IngestRuntimeJob) -> None:
        msg = f"simulated failure for {job.job_id}"
        raise RuntimeError(msg)


@pytest.fixture
def session_factory(tmp_path):
    engine = create_runtime_engine(f"sqlite:///{tmp_path / 'handler-test.sqlite'}")
    initialize_runtime_database(engine)
    return create_runtime_session_factory(engine)


@pytest.fixture
def settings():
    return SchedulerSettings(
        runtime_mode=RuntimeMode.STANDALONE,
        node_key="handler-node",
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


def _seed_job(job_repo: RuntimeJobRepository, job_id: str, job_type: str) -> None:
    job_repo.upsert_job(
        RuntimeJob(
            job_id=job_id,
            job_type=job_type,
            enabled=True,
            config={"interval_ms": 500},
        )
    )


def test_worker_runtime_executes_acquisition_handler_with_lease(settings, repos):
    """Handler for 'acquisition' job type is dispatched with valid lease."""
    node, job_repo, assn, lease, fencing = repos
    _seed_job(job_repo, "acq-job-1", "acquisition")
    handler = _RecordingHandler()
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
        handlers={"acquisition": handler},
    )

    now = datetime.now(tz=UTC)
    worker._scheduler.heartbeat(now=now)
    snapshot = worker._scheduler.assign_jobs(now=now)
    assert "acq-job-1" in snapshot.assigned_jobs

    worker._execute_one(job_id="acq-job-1", fencing_token=snapshot.fencing_tokens["acq-job-1"], now=now)

    assert "acq-job-1" in handler.executed_jobs
    snap = metrics.snapshot()
    assert snap.get("job_completed", 0) >= 1


def test_worker_runtime_executes_publish_snapshot_handler_with_lease(settings, repos):
    """Handler for 'publish_snapshot' job type is dispatched with valid lease."""
    node, job_repo, assn, lease, fencing = repos
    _seed_job(job_repo, "pub-job-1", "publish_snapshot")
    handler = _RecordingHandler()
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
        handlers={"publish_snapshot": handler},
    )

    now = datetime.now(tz=UTC)
    worker._scheduler.heartbeat(now=now)
    snapshot = worker._scheduler.assign_jobs(now=now)
    assert "pub-job-1" in snapshot.assigned_jobs

    worker._execute_one(job_id="pub-job-1", fencing_token=snapshot.fencing_tokens["pub-job-1"], now=now)

    assert "pub-job-1" in handler.executed_jobs
    snap = metrics.snapshot()
    assert snap.get("job_completed", 0) >= 1


def test_worker_runtime_missing_handler_records_failed_metric(settings, repos):
    """No handler for job type records handler_not_found instead of completed."""
    node, job_repo, assn, lease, fencing = repos
    _seed_job(job_repo, "unknown-job", "unknown_type")
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
        handlers={},
    )

    now = datetime.now(tz=UTC)
    worker._scheduler.heartbeat(now=now)
    snapshot = worker._scheduler.assign_jobs(now=now)
    assert "unknown-job" in snapshot.assigned_jobs

    worker._execute_one(job_id="unknown-job", fencing_token=snapshot.fencing_tokens["unknown-job"], now=now)

    snap = metrics.snapshot()
    assert snap.get("job_handler_not_found", 0) >= 1
    assert snap.get("job_completed", 0) == 0


def test_worker_runtime_handler_exception_records_failure(settings, repos):
    """Handler exception records job_failed metric."""
    node, job_repo, assn, lease, fencing = repos
    _seed_job(job_repo, "fail-job", "failing")
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
        handlers={"failing": _RaisingHandler()},
    )

    now = datetime.now(tz=UTC)
    worker._scheduler.heartbeat(now=now)
    snapshot = worker._scheduler.assign_jobs(now=now)
    assert "fail-job" in snapshot.assigned_jobs

    worker._execute_one(job_id="fail-job", fencing_token=snapshot.fencing_tokens["fail-job"], now=now)

    snap = metrics.snapshot()
    assert snap.get("job_failed", 0) >= 1
    assert snap.get("job_completed", 0) == 0


def test_worker_runtime_multiple_handlers_dispatched_correctly(settings, repos):
    """Multiple job types each routed to their own handler."""
    node, job_repo, assn, lease, fencing = repos
    _seed_job(job_repo, "acq-1", "acquisition")
    _seed_job(job_repo, "pub-1", "publish_snapshot")
    acq_handler = _RecordingHandler()
    pub_handler = _RecordingHandler()
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
        handlers={
            "acquisition": acq_handler,
            "publish_snapshot": pub_handler,
        },
    )

    now = datetime.now(tz=UTC)
    worker._scheduler.heartbeat(now=now)
    # In STANDALONE mode, alive_nodes[0] gets all jobs
    worker._scheduler.assign_jobs(now=now)

    # Execute both jobs
    for job_id in ("acq-1", "pub-1"):
        fencing_token = 1  # simplified for test
        worker._execute_one(job_id=job_id, fencing_token=fencing_token, now=now)

    assert "acq-1" in acq_handler.executed_jobs
    assert "pub-1" not in acq_handler.executed_jobs
    assert "pub-1" in pub_handler.executed_jobs
    assert "acq-1" not in pub_handler.executed_jobs
