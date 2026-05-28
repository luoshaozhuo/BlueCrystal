"""Cluster scheduler assignment tests."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

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


def _build(tmp_path, node_key: str):
    engine = create_runtime_engine(f"sqlite:///{tmp_path / 'cluster.sqlite'}")
    initialize_runtime_database(engine)
    session_factory = create_runtime_session_factory(engine)
    scheduler = SourceScheduler(
        settings=SchedulerSettings(
            runtime_mode=RuntimeMode.CLUSTER,
            node_key=node_key,
            heartbeat_timeout_seconds=15,
            lease_ttl_seconds=10,
        ),
        node_repository=NodeRuntimeRepository(session_factory),
        job_repository=RuntimeJobRepository(session_factory),
        assignment_repository=JobAssignmentRepository(session_factory),
        lease_service=LeaseService(session_factory, FencingTokenRepository(session_factory)),
    )
    return session_factory, scheduler


def test_cluster_assignment_has_no_duplicate_job_owner(tmp_path) -> None:
    session_factory, node_a = _build(tmp_path, "node-a")
    _, node_b = _build(tmp_path, "node-b")
    _, node_c = _build(tmp_path, "node-c")
    jobs = RuntimeJobRepository(session_factory)
    for index in range(5):
        jobs.upsert_job(RuntimeJob(job_id=f"job-{index}", job_type="acquisition", partition_key=f"p-{index}"))

    now = datetime(2026, 5, 27, tzinfo=UTC)
    for scheduler in (node_a, node_b, node_c):
        scheduler.heartbeat(now=now)
    for scheduler in (node_a, node_b, node_c):
        scheduler.assign_jobs(now=now)

    assignments = JobAssignmentRepository(session_factory).list_active_assignments()
    owners = {}
    for row in assignments:
        assert row.job_id not in owners
        owners[row.job_id] = row.node_key
    assert len(owners) == 5


def test_lease_renewal_rejects_non_owner(tmp_path) -> None:
    session_factory, node_a = _build(tmp_path, "node-a")
    RuntimeJobRepository(session_factory).upsert_job(RuntimeJob(job_id="job-1", job_type="acquisition"))
    now = datetime(2026, 5, 27, tzinfo=UTC)
    node_a.bootstrap(now=now)

    lease_service = LeaseService(session_factory, FencingTokenRepository(session_factory))
    with pytest.raises(ValueError):
        lease_service.renew(lease_name="job:job-1", holder_key="node-b", ttl_seconds=10, now=now)


def test_fencing_token_mismatch_rejects_execution(tmp_path) -> None:
    session_factory, node_a = _build(tmp_path, "node-a")
    RuntimeJobRepository(session_factory).upsert_job(RuntimeJob(job_id="job-1", job_type="acquisition"))
    snapshot = node_a.bootstrap(now=datetime(2026, 5, 27, tzinfo=UTC))

    decision = node_a.validate_execution(
        job_id="job-1",
        holder_key="node-a",
        fencing_token=snapshot.fencing_tokens["job-1"] + 1,
        now=datetime(2026, 5, 27, 0, 0, 1, tzinfo=UTC),
    )

    assert decision.allowed is False
    assert decision.result == "FENCED"
