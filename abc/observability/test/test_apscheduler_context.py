"""验证 APScheduler 3.x 各受支持 Executor 在真实执行边界传播上下文。

测试使用本地 BackgroundScheduler、AsyncIOScheduler 及线程池，不连接外部服务；
它能证明单进程线程/协程组合的 ContextVar 语义，但不覆盖 ProcessPoolExecutor、
持久化 JobStore 重启或跨进程任务传输。
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from threading import Event

from apscheduler.executors.asyncio import AsyncIOExecutor
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.events import EVENT_JOB_REMOVED
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.schedulers.background import BackgroundScheduler
import pytest

from observability.config import ObservabilityConfig
from observability.context import bind_request_context, get_observation_context
from observability.context.models import ObservationContext
from observability.runtime import ObservabilityRuntime, install_observability


def _config() -> ObservabilityConfig:
    """创建只启用 APScheduler 与 Worker instrumentation 的测试配置。"""
    return ObservabilityConfig.model_validate(
        {
            "service": {"name": "scheduler-context-test", "instance_id": "node-1"},
            "logging": {"enabled": False},
            "metrics": {"enabled": False},
            "tracing": {"enabled": False},
            "audit": {"enabled": False},
            "status": {"enabled": False},
            "instrumentation": {
                "apscheduler": {"enabled": True},
                "worker": {"enabled": True},
            },
        }
    )


def _recording_worker(
    runtime: ObservabilityRuntime,
    observed: list[ObservationContext],
    completed: Event,
):
    """创建记录执行点上下文并通知测试线程的同步 Worker。"""

    def worker() -> None:
        """保存 wrapper 内部可见的不可变上下文快照。"""
        observed.append(get_observation_context())
        completed.set()

    return runtime.instrument_worker("context-worker", worker)


def _add_request_job(
    scheduler: BackgroundScheduler | AsyncIOScheduler,
    runtime: ObservabilityRuntime,
    worker: object,
    *,
    job_id: str,
) -> None:
    """在模拟 HTTP 请求上下文中注册即将执行的一次性 Job。"""
    with bind_request_context(
        runtime_context=runtime.context,
        request_id="request-1",
        correlation_id="correlation-1",
        actor="operator",
    ):
        scheduler.add_job(
            worker,
            trigger="date",
            run_date=datetime.now(timezone.utc) + timedelta(milliseconds=50),
            id=job_id,
        )


def _job_removed_event(
    scheduler: BackgroundScheduler | AsyncIOScheduler,
    job_id: str,
) -> Event:
    """返回在一次性 Job 从 JobStore 移除后置位的同步事件。"""
    removed = Event()

    def listener(event: object) -> None:
        """只响应目标 Job，避免测试过早关闭 scheduler 造成竞态。"""
        if getattr(event, "job_id", None) == job_id:
            removed.set()

    scheduler.add_listener(listener, EVENT_JOB_REMOVED)
    return removed


def _assert_complete_context(context: ObservationContext, job_id: str) -> None:
    """断言 Runtime、请求、Scheduler 与 Worker 四层字段形成同一条链路。"""
    assert context.service_name == "scheduler-context-test"
    assert context.service_instance_id == "node-1"
    assert context.request_id == "request-1"
    assert context.correlation_id == "correlation-1"
    assert context.actor == "operator"
    assert context.job_id == job_id
    assert context.source == "worker"
    assert context.execution_id is not None


def test_background_scheduler_thread_pool_propagates_context() -> None:
    """BackgroundScheduler 的 APScheduler ThreadPoolExecutor 应恢复完整上下文。"""
    scheduler = BackgroundScheduler(
        executors={"default": ThreadPoolExecutor(max_workers=1)},
        timezone="UTC",
    )
    runtime = install_observability(_config(), scheduler=scheduler)
    observed: list[ObservationContext] = []
    completed = Event()
    worker = _recording_worker(runtime, observed, completed)
    removed = _job_removed_event(scheduler, "background-thread")

    asyncio.run(runtime.start())
    scheduler.start()
    try:
        _add_request_job(scheduler, runtime, worker, job_id="background-thread")
        assert completed.wait(2)
        assert removed.wait(2)
    finally:
        scheduler.shutdown(wait=True)
        asyncio.run(runtime.close())

    assert len(observed) == 1
    _assert_complete_context(observed[0], "background-thread")


@pytest.mark.asyncio
async def test_asyncio_scheduler_asyncio_executor_coroutine_propagates_context() -> None:
    """AsyncIOExecutor 创建的原生协程 Task 应继承隔离的完整上下文。"""
    scheduler = AsyncIOScheduler(
        executors={"default": AsyncIOExecutor()},
        timezone="UTC",
    )
    runtime = install_observability(_config(), scheduler=scheduler)
    observed: list[ObservationContext] = []
    completed = asyncio.Event()
    removed = _job_removed_event(scheduler, "asyncio-coroutine")

    async def worker() -> None:
        """记录异步 wrapper 内部上下文。"""
        observed.append(get_observation_context())
        completed.set()

    wrapped = runtime.instrument_worker("async-context-worker", worker)
    await runtime.start()
    scheduler.start()
    try:
        _add_request_job(scheduler, runtime, wrapped, job_id="asyncio-coroutine")
        await asyncio.wait_for(completed.wait(), timeout=2)
        assert await asyncio.wait_for(asyncio.to_thread(removed.wait, 2), timeout=3)
    finally:
        scheduler.shutdown(wait=True)
        await runtime.close()

    assert len(observed) == 1
    _assert_complete_context(observed[0], "asyncio-coroutine")


@pytest.mark.asyncio
async def test_asyncio_scheduler_asyncio_executor_sync_job_propagates_context() -> None:
    """AsyncIOExecutor 提交到事件循环默认线程池的同步 Job 应恢复完整上下文。"""
    scheduler = AsyncIOScheduler(
        executors={"default": AsyncIOExecutor()},
        timezone="UTC",
    )
    runtime = install_observability(_config(), scheduler=scheduler)
    observed: list[ObservationContext] = []
    completed = Event()
    worker = _recording_worker(runtime, observed, completed)
    removed = _job_removed_event(scheduler, "asyncio-sync")

    await runtime.start()
    scheduler.start()
    try:
        _add_request_job(scheduler, runtime, worker, job_id="asyncio-sync")
        assert await asyncio.wait_for(asyncio.to_thread(completed.wait, 2), timeout=3)
        assert await asyncio.wait_for(asyncio.to_thread(removed.wait, 2), timeout=3)
    finally:
        scheduler.shutdown(wait=True)
        await runtime.close()

    assert len(observed) == 1
    _assert_complete_context(observed[0], "asyncio-sync")


@pytest.mark.asyncio
async def test_asyncio_scheduler_apscheduler_thread_pool_propagates_context() -> None:
    """AsyncIOScheduler 显式使用 APScheduler ThreadPoolExecutor 时也应恢复上下文。"""
    scheduler = AsyncIOScheduler(
        executors={"default": ThreadPoolExecutor(max_workers=1)},
        timezone="UTC",
    )
    runtime = install_observability(_config(), scheduler=scheduler)
    observed: list[ObservationContext] = []
    completed = Event()
    worker = _recording_worker(runtime, observed, completed)
    removed = _job_removed_event(scheduler, "asyncio-thread")

    await runtime.start()
    scheduler.start()
    try:
        _add_request_job(scheduler, runtime, worker, job_id="asyncio-thread")
        assert await asyncio.wait_for(asyncio.to_thread(completed.wait, 2), timeout=3)
        assert await asyncio.wait_for(asyncio.to_thread(removed.wait, 2), timeout=3)
    finally:
        scheduler.shutdown(wait=True)
        await runtime.close()

    assert len(observed) == 1
    _assert_complete_context(observed[0], "asyncio-thread")


@pytest.mark.asyncio
async def test_asyncio_executor_keeps_concurrent_job_contexts_isolated() -> None:
    """并发协程 Job 在挂起和恢复后不得串用 request、job 或 execution 字段。"""
    scheduler = AsyncIOScheduler(
        executors={"default": AsyncIOExecutor()},
        timezone="UTC",
    )
    runtime = install_observability(_config(), scheduler=scheduler)
    observed: dict[str, list[ObservationContext]] = {"a": [], "b": []}
    both_entered = asyncio.Event()
    release = asyncio.Event()

    async def worker(label: str) -> None:
        """在 await 前后读取上下文，以验证 asyncio Task 隔离。"""
        observed[label].append(get_observation_context())
        if all(values for values in observed.values()):
            both_entered.set()
        await release.wait()
        observed[label].append(get_observation_context())

    wrapped = runtime.instrument_worker("concurrent-context-worker", worker)
    await runtime.start()
    scheduler.start()
    removed = {
        label: _job_removed_event(scheduler, f"concurrent-{label}")
        for label in observed
    }
    try:
        for label in observed:
            with bind_request_context(
                runtime_context=runtime.context,
                request_id=f"request-{label}",
                correlation_id=f"correlation-{label}",
                actor=f"actor-{label}",
            ):
                scheduler.add_job(
                    wrapped,
                    trigger="date",
                    run_date=datetime.now(timezone.utc) + timedelta(milliseconds=50),
                    id=f"concurrent-{label}",
                    args=(label,),
                )
        await asyncio.wait_for(both_entered.wait(), timeout=2)
        release.set()
        for event in removed.values():
            assert await asyncio.wait_for(asyncio.to_thread(event.wait, 2), timeout=3)
    finally:
        scheduler.shutdown(wait=True)
        await runtime.close()

    for label, contexts in observed.items():
        assert len(contexts) == 2
        assert contexts[0] == contexts[1]
        assert contexts[0].request_id == f"request-{label}"
        assert contexts[0].correlation_id == f"correlation-{label}"
        assert contexts[0].job_id == f"concurrent-{label}"
        assert contexts[0].execution_id is not None
    assert observed["a"][0].execution_id != observed["b"][0].execution_id
