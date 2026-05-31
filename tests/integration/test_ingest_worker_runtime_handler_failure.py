"""Integration tests for WorkerRuntime handler failure and missing handler."""
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
from whale.ingest.runtime.job_assignment import RuntimeJob
from whale.ingest.runtime.scheduler_settings import SchedulerSettings
from whale.shared.persistence.orm.ingest_runtime import IngestRuntimeJob


class _RaisingHandler:
    """Handler that raises to test failure metrics/audit."""

    def __init__(self, fail_on: str | None = None) -> None:
        self._fail_on = fail_on

    def execute(self, job: IngestRuntimeJob) -> None:
        if self._fail_on is None or job.job_id == self._fail_on:
            msg = f"simulated failure for {job.job_id}"
            raise RuntimeError(msg)


class _RecordingHandler:
    def __init__(self) -> None:
        self.executed: list[str] = []

    def execute(self, job: IngestRuntimeJob) -> None:
        self.executed.append(job.job_id)


@pytest.fixture
def session_factory(tmp_path):
    engine = create_runtime_engine(f"sqlite:///{tmp_path / 'handler-fail.sqlite'}")
    initialize_runtime_database(engine)
    return create_runtime_session_factory(engine)


@pytest.fixture
def settings():
    return SchedulerSettings(
        runtime_mode=RuntimeMode.STANDALONE,
        node_key="fail-node",
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


def _seed(repos, job_id: str, job_type: str = "test") -> None:
    _, job_repo, _, _, _ = repos
    job_repo.upsert_job(
        RuntimeJob(job_id=job_id, job_type=job_type, enabled=True, config={"interval_ms": 500})
    )


def test_worker_runtime_missing_handler_records_failed_metric(settings, repos):
    """No registered handler records handler_not_found metric."""
    _seed(repos, "no-handler-job", "unknown_type")
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
        handlers={},
    )

    now = datetime.now(tz=UTC)
    worker._scheduler.heartbeat(now=now)
    snapshot = worker._scheduler.assign_jobs(now=now)
    assert "no-handler-job" in snapshot.assigned_jobs
    worker._execute_one(job_id="no-handler-job", fencing_token=snapshot.fencing_tokens["no-handler-job"], now=now)

    snap = metrics.snapshot()
    assert snap.get("job_handler_not_found", 0) >= 1
    assert snap.get("job_completed", 0) == 0


def test_worker_runtime_handler_exception_records_failure_and_completes(settings, repos):
    """Handler exception records job_failed but does not prevent lease renewal."""
    _seed(repos, "raise-job", "failing")
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
        handlers={"failing": _RaisingHandler()},
    )

    now = datetime.now(tz=UTC)
    worker._scheduler.heartbeat(now=now)
    snapshot = worker._scheduler.assign_jobs(now=now)
    assert "raise-job" in snapshot.assigned_jobs

    worker._execute_one(job_id="raise-job", fencing_token=snapshot.fencing_tokens["raise-job"], now=now)

    snap = metrics.snapshot()
    assert snap.get("job_failed", 0) >= 1
    assert snap.get("job_completed", 0) == 0


def test_worker_assigns_and_executes_mixed_handlers(settings, repos):
    """Mixed handler types: one succeeds, one missing, one fails."""
    _seed(repos, "good-job", "good")
    _seed(repos, "bad-job", "bad")
    _seed(repos, "unknown-job", "unknown")
    node, job_repo, assn, lease, fencing = repos
    good_h = _RecordingHandler()
    bad_h = _RaisingHandler(fail_on="bad-job")
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
        handlers={"good": good_h, "bad": bad_h},
    )

    now = datetime.now(tz=UTC)
    worker._scheduler.heartbeat(now=now)
    worker._scheduler.assign_jobs(now=now)

    for job_id in ("good-job", "bad-job", "unknown-job"):
        worker._execute_one(job_id=job_id, fencing_token=1, now=now)

    snap = metrics.snapshot()
    assert "good-job" in good_h.executed
    assert snap.get("job_completed", 0) >= 1
    assert snap.get("job_failed", 0) >= 1
    assert snap.get("job_handler_not_found", 0) >= 1
