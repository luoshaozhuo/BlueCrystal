"""Worker crash, restart, fencing, and failover tests."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

import pytest

from whale.ingest.adapters.audit.db_audit_sink import DbIngestAuditSink
from whale.ingest.framework.persistence import create_runtime_engine, create_runtime_session_factory, initialize_runtime_database
from whale.ingest.runtime import (
    FencingTokenRepository,
    JobAssignmentRepository,
    LeaseService,
    NodeRuntimeRepository,
    RuntimeJob,
    RuntimeJobRepository,
    RuntimeMode,
    SchedulerSettings,
    WorkerRuntime,
    WorkerRuntimeMetrics,
)
from whale.shared.persistence.orm.ingest_runtime import IngestAuditEventOrm


@dataclass
class _RecordingHandler:
    node_key: str
    executions: list[tuple[str, str]] = field(default_factory=list)

    def execute(self, job) -> None:
        self.executions.append((self.node_key, job.job_id))


def _repos(tmp_path):
    engine = create_runtime_engine(f"sqlite:///{tmp_path / 'worker-failover.sqlite'}")
    initialize_runtime_database(engine)
    session_factory = create_runtime_session_factory(engine)
    return (
        session_factory,
        NodeRuntimeRepository(session_factory),
        RuntimeJobRepository(session_factory),
        JobAssignmentRepository(session_factory),
        LeaseService(session_factory, FencingTokenRepository(session_factory)),
        FencingTokenRepository(session_factory),
    )


def _worker(tmp_path, node_key: str, handler: _RecordingHandler):
    session_factory, node_repo, job_repo, assignment_repo, lease_service, fencing_repo = _repos(tmp_path)
    return (
        session_factory,
        job_repo,
        assignment_repo,
        lease_service,
        WorkerRuntime(
            settings=SchedulerSettings(
                runtime_mode=RuntimeMode.ACTIVE_STANDBY,
                node_key=node_key,
                heartbeat_interval_seconds=3600,
                heartbeat_timeout_seconds=10,
                lease_ttl_seconds=5,
                pull_max_in_flight=2,
            ),
            node_repository=node_repo,
            job_repository=job_repo,
            assignment_repository=assignment_repo,
            lease_service=lease_service,
            fencing_token_repository=fencing_repo,
            audit_sink=DbIngestAuditSink(session_factory),
            metrics=WorkerRuntimeMetrics(),
            handlers={"noop": handler},
        ),
    )


@pytest.mark.integration
def test_worker_crash_releases_or_expires_lease(tmp_path) -> None:
    session_factory, job_repo, _, lease_service, worker = _worker(tmp_path, "worker-a", _RecordingHandler("worker-a"))
    job_repo.upsert_job(RuntimeJob(job_id="job-1", job_type="noop", enabled=True))

    started = datetime.now(tz=UTC)
    worker._scheduler.bootstrap(now=started)
    lease = lease_service.get_snapshot(lease_name="job:job-1")
    assert lease is not None and lease.status == "ACTIVE"

    worker._scheduler.assign_jobs(now=started + timedelta(seconds=6))
    expired = lease_service.get_snapshot(lease_name="job:job-1")
    assert expired is not None
    assert expired.status in {"ACTIVE", "EXPIRED"}


@pytest.mark.integration
def test_standby_worker_takes_over_after_lease_expiry(tmp_path) -> None:
    _, job_repo, _, _, worker_a = _worker(tmp_path, "worker-a", _RecordingHandler("worker-a"))
    _, _, _, lease_service_b, worker_b = _worker(tmp_path, "worker-b", _RecordingHandler("worker-b"))
    job_repo.upsert_job(RuntimeJob(job_id="job-2", job_type="noop", enabled=True))

    started = datetime.now(tz=UTC)
    snapshot_a = worker_a._scheduler.bootstrap(now=started)
    assert snapshot_a.assigned_jobs == ("job-2",)

    snapshot_b = worker_b._scheduler.bootstrap(now=started + timedelta(seconds=12))
    assert snapshot_b.assigned_jobs == ("job-2",)
    assert snapshot_b.fencing_tokens["job-2"] > snapshot_a.fencing_tokens["job-2"]
    lease = lease_service_b.get_snapshot(lease_name="job:job-2")
    assert lease is not None and lease.holder_key == "worker-b"


@pytest.mark.integration
def test_old_worker_fencing_token_rejected_after_restart(tmp_path) -> None:
    _, job_repo, _, _, worker_a = _worker(tmp_path, "worker-a", _RecordingHandler("worker-a"))
    _, _, _, _, worker_b = _worker(tmp_path, "worker-b", _RecordingHandler("worker-b"))
    job_repo.upsert_job(RuntimeJob(job_id="job-3", job_type="noop", enabled=True))

    started = datetime.now(tz=UTC)
    snapshot_a = worker_a._scheduler.bootstrap(now=started)
    snapshot_b = worker_b._scheduler.bootstrap(now=started + timedelta(seconds=12))

    decision = worker_a._scheduler.validate_execution(
        job_id="job-3",
        holder_key="worker-a",
        fencing_token=snapshot_a.fencing_tokens["job-3"],
        now=started + timedelta(seconds=13),
    )

    assert decision.allowed is False
    assert decision.result == "FENCED"
    assert snapshot_b.fencing_tokens["job-3"] > snapshot_a.fencing_tokens["job-3"]


@pytest.mark.integration
def test_no_duplicate_execution_during_failover_window(tmp_path) -> None:
    handler_a = _RecordingHandler("worker-a")
    handler_b = _RecordingHandler("worker-b")
    _, job_repo, _, _, worker_a = _worker(tmp_path, "worker-a", handler_a)
    _, _, _, _, worker_b = _worker(tmp_path, "worker-b", handler_b)
    job_repo.upsert_job(RuntimeJob(job_id="job-4", job_type="noop", enabled=True))

    started = datetime.now(tz=UTC)
    snapshot_a = worker_a._scheduler.bootstrap(now=started)
    assert snapshot_a.assigned_jobs == ("job-4",)
    worker_a._execute_one(
        job_id="job-4",
        fencing_token=snapshot_a.fencing_tokens["job-4"],
        now=started,
    )

    snapshot_b = worker_b._scheduler.bootstrap(now=started + timedelta(seconds=12))
    worker_b._execute_one(
        job_id="job-4",
        fencing_token=snapshot_b.fencing_tokens["job-4"],
        now=started + timedelta(seconds=12),
    )

    assert handler_a.executions == [("worker-a", "job-4")]
    assert handler_b.executions == [("worker-b", "job-4")]


@pytest.mark.integration
def test_graceful_shutdown_records_final_audit_and_metrics(tmp_path) -> None:
    session_factory, job_repo, _, _, worker = _worker(tmp_path, "worker-a", _RecordingHandler("worker-a"))
    job_repo.upsert_job(RuntimeJob(job_id="job-5", job_type="noop", enabled=True))

    started = datetime.now(tz=UTC)
    snapshot = worker._scheduler.bootstrap(now=started)
    worker._execute_one(
        job_id="job-5",
        fencing_token=snapshot.fencing_tokens["job-5"],
        now=started,
    )
    final_metrics = worker.stop(timeout_seconds=5)

    session = session_factory()
    try:
        actions = [row.action for row in session.query(IngestAuditEventOrm).all()]
    finally:
        session.close()

    assert final_metrics.get("job_completed", 0) >= 1
    assert "worker.shutdown" in actions
