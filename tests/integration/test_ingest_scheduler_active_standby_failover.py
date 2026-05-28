"""Active-standby scheduler failover tests."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import select

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
    SourceScheduler,
)
from whale.shared.persistence.orm import IngestAuditEventOrm


def _scheduler(tmp_path, node_key: str):
    engine = create_runtime_engine(f"sqlite:///{tmp_path / 'active-standby.sqlite'}")
    initialize_runtime_database(engine)
    session_factory = create_runtime_session_factory(engine)
    lease_service = LeaseService(session_factory, FencingTokenRepository(session_factory))
    scheduler = SourceScheduler(
        settings=SchedulerSettings(
            runtime_mode=RuntimeMode.ACTIVE_STANDBY,
            node_key=node_key,
            heartbeat_timeout_seconds=15,
            lease_ttl_seconds=10,
        ),
        node_repository=NodeRuntimeRepository(session_factory),
        job_repository=RuntimeJobRepository(session_factory),
        assignment_repository=JobAssignmentRepository(session_factory),
        lease_service=lease_service,
        audit_sink=DbIngestAuditSink(session_factory),
    )
    return session_factory, scheduler


def test_active_standby_failover_reassigns_expired_job_once(tmp_path) -> None:
    session_factory, node_a = _scheduler(tmp_path, "node-a")
    _, node_b = _scheduler(tmp_path, "node-b")
    RuntimeJobRepository(session_factory).upsert_job(RuntimeJob(job_id="job-1", job_type="acquisition"))

    started = datetime(2026, 5, 27, 0, 0, tzinfo=UTC)
    snapshot_a = node_a.bootstrap(now=started)
    node_b.heartbeat(now=started)
    snapshot_b = node_b.assign_jobs(now=started)

    assert snapshot_a.assigned_jobs == ("job-1",)
    assert snapshot_b.assigned_jobs == ()
    old_token = snapshot_a.fencing_tokens["job-1"]

    failed_over = node_b.bootstrap(now=started + timedelta(seconds=20))

    assert failed_over.assigned_jobs == ("job-1",)
    assert failed_over.fencing_tokens["job-1"] > old_token

    active_assignments = JobAssignmentRepository(session_factory).list_active_assignments()
    assert len(active_assignments) == 1
    assert active_assignments[0].node_key == "node-b"


def test_recovered_old_active_is_fenced_after_failover(tmp_path) -> None:
    session_factory, node_a = _scheduler(tmp_path, "node-a")
    _, node_b = _scheduler(tmp_path, "node-b")
    RuntimeJobRepository(session_factory).upsert_job(RuntimeJob(job_id="job-1", job_type="acquisition"))

    started = datetime(2026, 5, 27, 0, 0, tzinfo=UTC)
    snapshot_a = node_a.bootstrap(now=started)
    old_token = snapshot_a.fencing_tokens["job-1"]
    new_snapshot = node_b.bootstrap(now=started + timedelta(seconds=20))

    decision = node_a.validate_execution(
        job_id="job-1",
        holder_key="node-a",
        fencing_token=old_token,
        now=started + timedelta(seconds=21),
    )

    assert decision.allowed is False
    assert decision.result == "FENCED"
    assert new_snapshot.fencing_tokens["job-1"] > old_token

    session = session_factory()
    try:
        results = [row.result for row in session.scalars(select(IngestAuditEventOrm))]
    finally:
        session.close()
    assert "EXPIRED" in results
    assert "FENCED" in results
