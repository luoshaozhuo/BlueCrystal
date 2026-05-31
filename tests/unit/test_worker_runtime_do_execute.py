"""WorkerRuntime._do_execute handler dispatch 单元测试。

覆盖 _do_execute 的 handler dispatch 路径，不依赖数据库或 APScheduler。

验证场景：
1. 存在的 handler — dispatch 并返回 True
2. 不存在的 handler — HANDLER_NOT_FOUND 记录，返回 False
3. handler 抛出异常 — 异常向上传播，由 _execute_one 的 except 块处理
4. 空 handlers 字典 — 任何 job_type 都触发 HANDLER_NOT_FOUND
5. 多个 job_type — 各自正确路由到对应 handler

与集成测试（test_ingest_worker_runtime_executes_usecase_handlers.py）的区分：
本测试直接调用 _do_execute，不经过 _execute_one、scheduler 或 lease 流程。
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from whale.ingest.runtime.modes import RuntimeMode
from whale.ingest.runtime.scheduler_settings import SchedulerSettings
from whale.ingest.runtime.worker_runtime import WorkerRuntime, WorkerRuntimeMetrics
from whale.shared.persistence.orm.ingest_runtime import IngestRuntimeJob


class _RecordingHandler:
    """记录执行 job 的 handler。"""

    def __init__(self) -> None:
        self.executed_jobs: list[str] = []

    def execute(self, job: IngestRuntimeJob) -> None:
        self.executed_jobs.append(job.job_id)


class _RaisingHandler:
    """抛出异常的 handler，用于测试异常传播。"""

    def execute(self, job: IngestRuntimeJob) -> None:
        msg = f"handler failure for {job.job_id}"
        raise RuntimeError(msg)


def _make_job_row(
    job_id: str = "job-1",
    job_type: str = "test_type",
) -> IngestRuntimeJob:
    """构建最小 IngestRuntimeJob 仅用于 handler dispatch 测试。"""
    row = MagicMock(spec=IngestRuntimeJob)
    row.job_id = job_id
    row.job_type = job_type
    row.config_json = {}
    return row


def _build_test_worker(
    handlers: dict[str, _RecordingHandler | _RaisingHandler] | None = None,
    metrics: WorkerRuntimeMetrics | None = None,
) -> WorkerRuntime:
    """构建最小 WorkerRuntime 实例，仅用于 _do_execute 测试。

    使用真实 SchedulerSettings 避免 APScheduler 初始化时因 MagicMock
    的 timezone 字段触发 TypeError。
    """
    resolved_metrics = metrics or WorkerRuntimeMetrics()
    settings = SchedulerSettings(
        timezone="UTC",
        runtime_mode=RuntimeMode.STANDALONE,
        node_key="test-node",
        heartbeat_interval_seconds=3600,
        lease_ttl_seconds=30,
        pull_max_in_flight=1,
    )
    return WorkerRuntime(
        settings=settings,
        node_repository=MagicMock(),
        job_repository=MagicMock(),
        assignment_repository=MagicMock(),
        lease_service=MagicMock(),
        fencing_token_repository=MagicMock(),
        metrics=resolved_metrics,
        handlers=handlers or {},
    )


def test_do_execute_dispatches_to_handler() -> None:
    """已注册 handler → _do_execute 调用 handler.execute 并返回 True。"""
    metrics = WorkerRuntimeMetrics()
    handler = _RecordingHandler()
    worker = _build_test_worker(handlers={"test_type": handler}, metrics=metrics)
    job = _make_job_row(job_id="job-dispatch", job_type="test_type")
    result = worker._do_execute(job)

    assert result is True
    assert "job-dispatch" in handler.executed_jobs
    snap = metrics.snapshot()
    assert snap.get("job_handler_not_found", 0) == 0
    assert snap.get("job_completed", 0) == 0  # completed 由 _execute_one 记录


def test_do_execute_returns_false_when_handler_missing() -> None:
    """不存在的 handler → _do_execute 返回 False 并记录 HANDLER_NOT_FOUND。"""
    metrics = WorkerRuntimeMetrics()
    worker = _build_test_worker(metrics=metrics)
    job = _make_job_row(job_id="job-unknown", job_type="unknown_type")
    result = worker._do_execute(job)

    assert result is False
    snap = metrics.snapshot()
    assert snap.get("job_handler_not_found", 0) >= 1


def test_do_execute_returns_false_for_empty_handlers() -> None:
    """handlers={} 时任何 job_type 都触发 HANDLER_NOT_FOUND。"""
    metrics = WorkerRuntimeMetrics()
    worker = _build_test_worker(metrics=metrics)
    job = _make_job_row(job_id="job-empty", job_type="any_type")
    result = worker._do_execute(job)

    assert result is False
    snap = metrics.snapshot()
    assert snap.get("job_handler_not_found", 0) >= 1


def test_do_execute_propagates_handler_exception() -> None:
    """handler 抛出异常 → _do_execute 让异常向上传播。"""
    metrics = WorkerRuntimeMetrics()
    worker = _build_test_worker(handlers={"failing": _RaisingHandler()}, metrics=metrics)
    job = _make_job_row(job_id="job-fail", job_type="failing")

    with pytest.raises(RuntimeError, match="handler failure for job-fail"):
        worker._do_execute(job)

    # _do_execute 不记录 job_failed — 由 _execute_one 的 except 块负责
    snap = metrics.snapshot()
    assert snap.get("job_failed", 0) == 0


def test_do_execute_multiple_job_types_accurate() -> None:
    """多个 job_type 各自正确路由到对应 handler。"""
    metrics = WorkerRuntimeMetrics()
    handler_a = _RecordingHandler()
    handler_b = _RecordingHandler()
    worker = _build_test_worker(
        handlers={"type_a": handler_a, "type_b": handler_b},
        metrics=metrics,
    )

    job_a = _make_job_row(job_id="job-a", job_type="type_a")
    job_b = _make_job_row(job_id="job-b", job_type="type_b")

    assert worker._do_execute(job_a) is True
    assert worker._do_execute(job_b) is True

    assert "job-a" in handler_a.executed_jobs
    assert "job-b" not in handler_a.executed_jobs
    assert "job-b" in handler_b.executed_jobs
    assert "job-a" not in handler_b.executed_jobs
