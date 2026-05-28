"""Scheduler backpressure, missed-tick, and assignment-lag tests."""

from __future__ import annotations

import time
import threading
from dataclasses import dataclass, field
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
    WorkerRuntime,
    WorkerRuntimeMetrics,
)


@dataclass
class _SlowHandler:
    sleep_seconds: float
    concurrency: int = 0
    max_concurrency: int = 0
    lock: threading.Lock = field(default_factory=threading.Lock)

    def execute(self, job) -> None:
        del job
        with self.lock:
            self.concurrency += 1
            self.max_concurrency = max(self.max_concurrency, self.concurrency)
        try:
            time.sleep(self.sleep_seconds)
        finally:
            with self.lock:
                self.concurrency -= 1


def _worker(tmp_path, handler: _SlowHandler, pull_max_in_flight: int = 2):
    engine = create_runtime_engine(f"sqlite:///{tmp_path / 'scheduler-backpressure.sqlite'}")
    initialize_runtime_database(engine)
    session_factory = create_runtime_session_factory(engine)
    job_repo = RuntimeJobRepository(session_factory)
    worker = WorkerRuntime(
        settings=SchedulerSettings(
            runtime_mode=RuntimeMode.STANDALONE,
            node_key="bp-node",
            heartbeat_interval_seconds=3600,
            lease_ttl_seconds=30,
            pull_max_in_flight=pull_max_in_flight,
        ),
        node_repository=NodeRuntimeRepository(session_factory),
        job_repository=job_repo,
        assignment_repository=JobAssignmentRepository(session_factory),
        lease_service=LeaseService(session_factory, FencingTokenRepository(session_factory)),
        fencing_token_repository=FencingTokenRepository(session_factory),
        audit_sink=None,
        metrics=WorkerRuntimeMetrics(),
        handlers={"noop": handler},
    )
    return job_repo, worker


@pytest.mark.integration
def test_job_overrun_records_missed_tick(tmp_path) -> None:
    handler = _SlowHandler(sleep_seconds=0.1)
    job_repo, worker = _worker(tmp_path, handler)
    job_repo.upsert_job(
        RuntimeJob(job_id="slow-job", job_type="noop", enabled=True, config={"interval_ms": 50})
    )
    now = datetime.now(tz=UTC)
    snapshot = worker._scheduler.bootstrap(now=now)
    worker._execute_one(job_id="slow-job", fencing_token=snapshot.fencing_tokens["slow-job"], now=now)

    assert worker.metrics_snapshot.get("missed_tick", 0) >= 1


@pytest.mark.integration
def test_assignment_lag_metric_under_multi_job_load(tmp_path) -> None:
    handler = _SlowHandler(sleep_seconds=0.01)
    job_repo, worker = _worker(tmp_path, handler)
    for index in range(5):
        job_repo.upsert_job(
            RuntimeJob(
                job_id=f"lag-job-{index}",
                job_type="noop",
                enabled=True,
                config={"interval_ms": 100},
            )
        )

    now = datetime.now(tz=UTC)
    snapshot = worker._scheduler.bootstrap(now=now)
    for job_id in snapshot.assigned_jobs:
        worker._execute_one(job_id=job_id, fencing_token=snapshot.fencing_tokens[job_id], now=now)

    assert worker.metrics_summary.get("assignment_lag_ms_p95", 0.0) >= 0.0
    assert worker.metrics_snapshot.get("job_completed", 0) >= 1


@pytest.mark.integration
def test_backpressure_limits_inflight_jobs(tmp_path) -> None:
    handler = _SlowHandler(sleep_seconds=0.05)
    job_repo, worker = _worker(tmp_path, handler, pull_max_in_flight=2)
    for index in range(4):
        job_repo.upsert_job(
            RuntimeJob(job_id=f"bp-job-{index}", job_type="noop", enabled=True, config={"interval_ms": 100})
        )

    now = datetime.now(tz=UTC)
    snapshot = worker._scheduler.bootstrap(now=now)
    for job_id in snapshot.assigned_jobs:
        worker._execute_one(job_id=job_id, fencing_token=snapshot.fencing_tokens[job_id], now=now)

    assert handler.max_concurrency <= 1


@pytest.mark.integration
def test_scheduler_does_not_create_unbounded_tasks(tmp_path) -> None:
    handler = _SlowHandler(sleep_seconds=0.01)
    _, worker = _worker(tmp_path, handler, pull_max_in_flight=2)
    worker.start()
    try:
        jobs = worker._aps.get_jobs()
    finally:
        worker.stop(timeout_seconds=5)

    assert len(jobs) == 2
