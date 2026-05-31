"""Integration tests for missed_tick and stagger_offset behavior."""

from __future__ import annotations

import time
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


@pytest.fixture
def session_factory(tmp_path):
    engine = create_runtime_engine(f"sqlite:///{tmp_path / 'stagger-test.sqlite'}")
    initialize_runtime_database(engine)
    return create_runtime_session_factory(engine)


@pytest.fixture
def settings():
    return SchedulerSettings(
        runtime_mode=RuntimeMode.STANDALONE,
        node_key="test-node",
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


def test_worker_runtime_records_missed_tick_on_overrun(settings, repos):
    """Overrun beyond interval_ms records missed_tick."""
    node, job_repo, assign, lease, fencing = repos
    job_repo.upsert_job(
        RuntimeJob(
            job_id="slow-job",
            job_type="acquisition",
            enabled=True,
            config={"interval_ms": 20},
        )
    )
    metrics = WorkerRuntimeMetrics()

    class SlowWorker(WorkerRuntime):
        def _do_execute(self, job_row):
            time.sleep(0.06)  # 60ms > 20ms interval

    worker = SlowWorker(
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
    snapshot = worker._scheduler.assign_jobs(now=now)
    assert "slow-job" in snapshot.assigned_jobs

    worker._execute_one(job_id="slow-job", fencing_token=snapshot.fencing_tokens["slow-job"], now=now)

    snap = metrics.snapshot()
    assert snap.get("missed_tick", 0) >= 1, f"missed_tick not recorded: {snap}"


def test_stagger_offset_delays_execution(settings, repos):
    """stagger_offset_ms in job config delays start."""
    node, job_repo, assign, lease, fencing = repos
    job_repo.upsert_job(
        RuntimeJob(
            job_id="stagger-job",
            job_type="acquisition",
            enabled=True,
            config={"interval_ms": 200, "stagger_offset_ms": 40},
        )
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
    snapshot = worker._scheduler.assign_jobs(now=now)
    assert "stagger-job" in snapshot.assigned_jobs

    t0 = time.monotonic()
    worker._execute_one(
        job_id="stagger-job",
        fencing_token=snapshot.fencing_tokens["stagger-job"],
        now=now,
    )
    elapsed_ms = (time.monotonic() - t0) * 1000
    assert elapsed_ms >= 35, f"Stagger too short: {elapsed_ms}ms"
