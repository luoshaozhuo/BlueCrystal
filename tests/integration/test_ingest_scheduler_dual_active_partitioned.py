"""Dual-active partitioned scheduler tests."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

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
    engine = create_runtime_engine(f"sqlite:///{tmp_path / 'dual-active.sqlite'}")
    initialize_runtime_database(engine)
    session_factory = create_runtime_session_factory(engine)
    scheduler = SourceScheduler(
        settings=SchedulerSettings(
            runtime_mode=RuntimeMode.DUAL_ACTIVE_PARTITIONED,
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


def test_dual_active_partitioned_assigns_different_partitions_to_different_nodes(tmp_path) -> None:
    session_factory, node_a = _build(tmp_path, "node-a")
    _, node_b = _build(tmp_path, "node-b")
    jobs = RuntimeJobRepository(session_factory)
    jobs.upsert_job(RuntimeJob(job_id="job-a", job_type="acquisition", partition_key="alpha"))
    jobs.upsert_job(RuntimeJob(job_id="job-b", job_type="acquisition", partition_key="delta"))

    now = datetime(2026, 5, 27, tzinfo=UTC)
    node_a.heartbeat(now=now)
    node_b.heartbeat(now=now)
    snapshot_a = node_a.assign_jobs(now=now)
    snapshot_b = node_b.assign_jobs(now=now)

    owners = {job_id: "node-a" for job_id in snapshot_a.assigned_jobs} | {job_id: "node-b" for job_id in snapshot_b.assigned_jobs}
    assert owners["job-a"] != owners["job-b"]


def test_dual_active_partitioned_prevents_duplicate_partition_execution(tmp_path) -> None:
    session_factory, node_a = _build(tmp_path, "node-a")
    _, node_b = _build(tmp_path, "node-b")
    jobs = RuntimeJobRepository(session_factory)
    jobs.upsert_job(RuntimeJob(job_id="job-a1", job_type="acquisition", partition_key="shared"))
    jobs.upsert_job(RuntimeJob(job_id="job-a2", job_type="acquisition", partition_key="shared"))

    now = datetime(2026, 5, 27, tzinfo=UTC)
    node_a.heartbeat(now=now)
    node_b.heartbeat(now=now)
    snapshot_a = node_a.assign_jobs(now=now)
    snapshot_b = node_b.assign_jobs(now=now)

    assignment_nodes = set()
    if snapshot_a.assigned_jobs:
        assignment_nodes.add("node-a")
    if snapshot_b.assigned_jobs:
        assignment_nodes.add("node-b")
    assert len(assignment_nodes) == 1


def test_partition_lease_expiry_allows_reassignment(tmp_path) -> None:
    session_factory, node_a = _build(tmp_path, "node-a")
    _, node_b = _build(tmp_path, "node-b")
    jobs = RuntimeJobRepository(session_factory)
    jobs.upsert_job(RuntimeJob(job_id="job-a", job_type="acquisition", partition_key="alpha"))

    now = datetime(2026, 5, 27, tzinfo=UTC)
    first = node_a.bootstrap(now=now)
    owner = "node-a" if first.assigned_jobs else "node-b"
    other = node_b if owner == "node-a" else node_a
    other_snapshot = other.bootstrap(now=now + timedelta(seconds=20))

    assert other_snapshot.assigned_jobs == ("job-a",)
    active_assignments = JobAssignmentRepository(session_factory).list_active_assignments()
    assert len(active_assignments) == 1
    assert active_assignments[0].node_key != owner
