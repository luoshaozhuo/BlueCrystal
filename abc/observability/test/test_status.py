"""验证 status 单元及其与 Runtime、Worker wrapper、FastAPI 的轻量装配。

测试使用本地 FastAPI TestClient 和内存中的业务函数，不连接外部服务，也不证明
真实 ASGI server、APScheduler 线程池或多进程部署下的运行行为。
"""

from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier
from typing import Any, Callable, cast

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from observability.config import ObservabilityConfig, load_observability_config
from observability.config.loader import ObservabilityConfigError
from observability.runtime import ObservabilityRuntime, install_observability
from observability.status import RuntimeLifecycle, WorkerStatusTracker
from observability.status.models import immutable_details


class _FakeScheduler:
    """仅模拟 status 所需 listener、running 和 jobs 边界的调度器。"""

    def __init__(self) -> None:
        """创建未运行且没有任务的调度器替身。"""
        self.running = False
        self.listeners: list[Callable[[object], None]] = []
        self.jobs: list[object] = []

    def add_listener(self, callback: Callable[[object], None], _: int) -> None:
        """记录 listener，不产生真实调度线程。"""
        self.listeners.append(callback)

    def remove_listener(self, callback: Callable[[object], None]) -> None:
        """移除先前记录的 listener。"""
        self.listeners.remove(callback)

    def get_jobs(self) -> list[object]:
        """返回任务列表副本供状态快照计数。"""
        return list(self.jobs)


class _FakeInstrumentation:
    """记录 Runtime 生命周期调用并可注入启动失败的 adapter 替身。"""

    name = "fake"

    def __init__(self, *, fail_start: bool = False) -> None:
        """配置是否在启动阶段抛错。"""
        self.fail_start = fail_start
        self.install_calls = 0
        self.start_calls = 0
        self.stop_calls = 0
        self.uninstall_calls = 0
        self.details: dict[str, object] = {"nested": {"value": 1}}

    def install(self, _: ObservabilityRuntime) -> None:
        """记录结构安装。"""
        self.install_calls += 1

    def start(self) -> None:
        """记录资源启动，并按测试配置注入失败。"""
        self.start_calls += 1
        if self.fail_start:
            raise RuntimeError("adapter start failed")

    def stop(self) -> None:
        """记录资源停止。"""
        self.stop_calls += 1

    def uninstall(self) -> None:
        """记录结构卸载。"""
        self.uninstall_calls += 1

    def status_details(self) -> dict[str, object]:
        """返回包含嵌套值的详情，用于验证快照隔离。"""
        return self.details


class _MetricHandle:
    """模拟 Prometheus labels 后的最小计数器或直方图句柄。"""

    def __init__(self, *, fail_inc: bool = False) -> None:
        """配置 inc 是否模拟 backend 写入失败。"""
        self.fail_inc = fail_inc

    def labels(self, **_: str) -> _MetricHandle:
        """返回自身，模拟带标签的指标句柄。"""
        return self

    def inc(self) -> None:
        """递增指标，或按配置抛出观测故障。"""
        if self.fail_inc:
            raise RuntimeError("metrics unavailable")

    def dec(self) -> None:
        """模拟递减运行中指标。"""

    def observe(self, _: float) -> None:
        """模拟记录耗时。"""


class _FailingMetrics:
    """只在执行结果计数阶段失败的 Metrics backend 替身。"""

    def __init__(self) -> None:
        """创建可进入 Worker、但无法记录执行结果的指标集合。"""
        self.worker_in_flight = _MetricHandle()
        self.worker_executions = _MetricHandle(fail_inc=True)
        self.worker_duration = _MetricHandle()


class _FakeTracing:
    """记录 close 调用的 tracing backend 替身。"""

    def __init__(self) -> None:
        """创建尚未关闭的 tracing 替身。"""
        self.closed = False

    def close(self) -> None:
        """记录 backend 已关闭。"""
        self.closed = True


def _config(
    *,
    status_enabled: bool = True,
    fastapi_enabled: bool = False,
    apscheduler_enabled: bool = False,
    worker_enabled: bool = True,
) -> ObservabilityConfig:
    """创建关闭外部 backend 的最小配置，隔离 status 行为。

    Args:
        status_enabled: 是否启用状态快照及其 HTTP 路由。
        fastapi_enabled: 是否安装 FastAPI instrumentation。
        apscheduler_enabled: 是否安装 APScheduler instrumentation。
        worker_enabled: 是否包装 Worker。

    Returns:
        不产生日志、指标、链路和审计外部副作用的配置。
    """
    return ObservabilityConfig.model_validate(
        {
            "service": {"name": "status-test", "instance_id": "node-1"},
            "logging": {"enabled": False},
            "metrics": {"enabled": False},
            "tracing": {"enabled": False},
            "audit": {"enabled": False},
            "status": {"enabled": status_enabled},
            "instrumentation": {
                "fastapi": {"enabled": fastapi_enabled},
                "apscheduler": {"enabled": apscheduler_enabled},
                "worker": {"enabled": worker_enabled},
            },
        }
    )


def test_worker_tracker_records_sorted_immutable_snapshots() -> None:
    """Tracker 应记录并发数与最近结果，且旧快照不随新事件变化。"""
    tracker = WorkerStatusTracker()
    tracker.worker_started("worker-b")
    tracker.worker_started("worker-a")
    initial = tracker.worker_statuses()

    tracker.worker_finished("worker-a", "success")
    current = tracker.worker_statuses()

    assert [item.operation for item in current] == ["worker-a", "worker-b"]
    assert initial[0].in_flight == 1
    assert initial[0].last_result is None
    assert current[0].in_flight == 0
    assert current[0].last_result == "success"
    assert current[0].last_finished_at is not None


def test_worker_tracker_rejects_finish_without_matching_start() -> None:
    """没有对应开始事件的结束事件应暴露状态配对错误。"""
    tracker = WorkerStatusTracker()

    with pytest.raises(RuntimeError, match="without matching start"):
        tracker.worker_finished("orphan-worker", "failure")


def test_worker_tracker_counts_overlapping_executions() -> None:
    """同一 operation 的重叠执行应逐次递减，并保留最近完成结果。"""
    tracker = WorkerStatusTracker()
    tracker.worker_started("overlap-worker")
    tracker.worker_started("overlap-worker")

    tracker.worker_finished("overlap-worker", "success")
    first_finish = tracker.worker_statuses()[0]
    tracker.worker_finished("overlap-worker", "failure")
    second_finish = tracker.worker_statuses()[0]

    assert first_finish.in_flight == 1
    assert first_finish.last_result == "success"
    assert second_finish.in_flight == 0
    assert second_finish.last_result == "failure"
    with pytest.raises(RuntimeError, match="without matching start"):
        tracker.worker_finished("overlap-worker", "success")


def test_worker_tracker_invalid_result_does_not_mutate_state() -> None:
    """非法结果应被拒绝，并保持原运行中状态不变。"""
    tracker = WorkerStatusTracker()
    tracker.worker_started("worker")

    with pytest.raises(ValueError, match="unsupported worker result"):
        tracker.worker_finished("worker", "unknown")

    status = tracker.worker_statuses()[0]
    assert status.in_flight == 1
    assert status.last_result is None


def test_worker_tracker_is_thread_safe_for_same_operation() -> None:
    """多个线程同时执行同一 operation 时不得丢失运行中计数。"""
    tracker = WorkerStatusTracker()
    worker_count = 8
    all_started = Barrier(worker_count + 1)
    allow_finish = Barrier(worker_count + 1)

    def run_once() -> None:
        """登记开始后等待主线程读取峰值，再登记完成。"""
        tracker.worker_started("threaded-worker")
        all_started.wait()
        allow_finish.wait()
        tracker.worker_finished("threaded-worker", "success")

    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        futures = [executor.submit(run_once) for _ in range(worker_count)]
        all_started.wait()
        assert tracker.worker_statuses()[0].in_flight == worker_count
        allow_finish.wait()
        for future in futures:
            future.result()

    status = tracker.worker_statuses()[0]
    assert status.in_flight == 0
    assert status.last_result == "success"


def test_sync_worker_wrapper_updates_in_flight_and_success() -> None:
    """同步 wrapper 应在业务函数执行前登记运行中，并在返回后记录成功。"""
    runtime = ObservabilityRuntime(_config())

    def runner() -> str:
        """从业务执行点读取 wrapper 已登记的状态。"""
        status = runtime.status().workers
        assert len(status) == 1
        assert status[0].in_flight == 1
        assert status[0].last_result is None
        return "done"

    wrapped = runtime.instrument_worker("sync-worker", runner)

    assert wrapped() == "done"
    status = runtime.status().workers[0]
    assert status.in_flight == 0
    assert status.last_result == "success"


def test_sync_worker_wrapper_records_failure_without_changing_exception() -> None:
    """同步 wrapper 应记录失败，同时保留业务异常类型和值。"""
    runtime = ObservabilityRuntime(_config())
    error = ValueError("business failure")

    def runner() -> None:
        """抛出调用方需要原样接收的业务异常。"""
        raise error

    wrapped = runtime.instrument_worker("failing-worker", runner)

    with pytest.raises(ValueError) as captured:
        wrapped()

    assert captured.value is error
    status = runtime.status().workers[0]
    assert status.in_flight == 0
    assert status.last_result == "failure"


@pytest.mark.asyncio
async def test_async_worker_wrapper_records_cancellation() -> None:
    """异步 wrapper 应在任务取消后清除运行中计数并记录 cancelled。"""
    runtime = ObservabilityRuntime(_config())
    entered = asyncio.Event()

    async def runner() -> None:
        """保持执行直到测试任务主动取消。"""
        entered.set()
        await asyncio.Event().wait()

    wrapped = runtime.instrument_worker("async-worker", runner)
    task = asyncio.create_task(wrapped())
    await entered.wait()

    running = runtime.status().workers[0]
    assert running.in_flight == 1

    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task

    finished = runtime.status().workers[0]
    assert finished.in_flight == 0
    assert finished.last_result == "cancelled"


@pytest.mark.asyncio
async def test_async_worker_wrapper_records_success() -> None:
    """异步 wrapper 应保留返回值并记录成功。"""
    runtime = ObservabilityRuntime(_config())

    async def runner() -> str:
        """返回异步业务结果。"""
        assert runtime.status().workers[0].in_flight == 1
        return "done"

    wrapped = runtime.instrument_worker("async-success", runner)

    assert await wrapped() == "done"
    status = runtime.status().workers[0]
    assert status.in_flight == 0
    assert status.last_result == "success"


@pytest.mark.asyncio
async def test_async_worker_wrapper_records_failure_without_changing_exception() -> None:
    """异步 wrapper 应记录失败并保留业务异常对象。"""
    runtime = ObservabilityRuntime(_config())
    error = LookupError("async business failure")

    async def runner() -> None:
        """抛出调用方需要原样接收的异步业务异常。"""
        raise error

    wrapped = runtime.instrument_worker("async-failure", runner)

    with pytest.raises(LookupError) as captured:
        await wrapped()

    assert captured.value is error
    status = runtime.status().workers[0]
    assert status.in_flight == 0
    assert status.last_result == "failure"


def test_metrics_failure_does_not_change_worker_result() -> None:
    """观测 backend 故障不应覆盖已经成功产生的业务结果。"""
    runtime = ObservabilityRuntime(_config())
    cast(Any, runtime).metrics = _FailingMetrics()
    wrapped = runtime.instrument_worker("metrics-failure", lambda: "done")

    assert wrapped() == "done"


def test_metrics_failure_does_not_leave_worker_status_running() -> None:
    """结果指标写入失败后，Worker 状态仍应完成并记录业务成功。"""
    runtime = ObservabilityRuntime(_config())
    cast(Any, runtime).metrics = _FailingMetrics()
    wrapped = runtime.instrument_worker("metrics-failure", lambda: "done")

    wrapped()

    status = runtime.status().workers[0]
    assert status.in_flight == 0
    assert status.last_result == "success"


@pytest.mark.asyncio
async def test_runtime_status_tracks_lifecycle() -> None:
    """Runtime 快照应依次反映 created、started 和 closed 生命周期。"""
    runtime = ObservabilityRuntime(_config())

    assert runtime.status().lifecycle is RuntimeLifecycle.CREATED
    await runtime.start()
    assert runtime.status().lifecycle is RuntimeLifecycle.STARTED
    await runtime.close()
    assert runtime.status().lifecycle is RuntimeLifecycle.CLOSED


@pytest.mark.asyncio
async def test_runtime_lifecycle_operations_are_idempotent() -> None:
    """重复启动和关闭不得重复调用 adapter，并且关闭后禁止重启。"""
    runtime = ObservabilityRuntime(_config())
    adapter = _FakeInstrumentation()
    runtime.install(adapter)

    await runtime.start()
    await runtime.start()
    await runtime.close()
    await runtime.close()

    assert adapter.start_calls == 1
    assert adapter.stop_calls == 1
    assert adapter.uninstall_calls == 1
    with pytest.raises(RuntimeError, match="runtime is closed"):
        await runtime.start()


@pytest.mark.asyncio
async def test_runtime_start_failure_closes_and_clears_instrumentation_status() -> None:
    """adapter 启动失败后 Runtime 应关闭，并清除半安装状态。"""
    runtime = ObservabilityRuntime(_config())
    adapter = _FakeInstrumentation(fail_start=True)
    runtime.install(adapter)

    with pytest.raises(RuntimeError, match="adapter start failed"):
        await runtime.start()

    status = runtime.status()
    assert status.lifecycle is RuntimeLifecycle.CLOSED
    assert status.instrumentations == ()
    assert adapter.stop_calls == 1
    assert adapter.uninstall_calls == 1


@pytest.mark.asyncio
async def test_instrumentation_status_tracks_install_start_and_close() -> None:
    """adapter 状态应区分结构已安装、资源已启动和已经卸载。"""
    runtime = ObservabilityRuntime(_config())
    adapter = _FakeInstrumentation()
    runtime.install(adapter)

    installed = runtime.status().instrumentations[0]
    await runtime.start()
    started = runtime.status().instrumentations[0]
    await runtime.close()
    closed = runtime.status().instrumentations[0]

    assert (installed.installed, installed.started) == (True, False)
    assert (started.installed, started.started) == (True, True)
    assert (closed.installed, closed.started) == (False, False)


@pytest.mark.asyncio
async def test_closed_tracing_backend_is_not_reported_ready() -> None:
    """Runtime 关闭后，已关闭的 tracing backend 不应继续报告 ready。"""
    runtime = ObservabilityRuntime(_config())
    tracing = _FakeTracing()
    cast(Any, runtime).tracing = tracing

    assert next(item for item in runtime.status().backends if item.name == "tracing").state == "ready"
    await runtime.close()

    assert tracing.closed is True
    assert next(item for item in runtime.status().backends if item.name == "tracing").state == "closed"


def test_instrumentation_details_snapshot_is_deeply_immutable() -> None:
    """嵌套详情不得通过原始对象修改而改变已经生成的状态快照。"""
    nested = {"value": 1}
    details = immutable_details({"nested": nested})

    nested["value"] = 2

    assert details["nested"] == {"value": 1}


def test_status_route_is_installed_without_fastapi_instrumentation() -> None:
    """只启用 status 时也应自动安装路由并把 Runtime 挂到应用状态。"""
    app = FastAPI()
    runtime = install_observability(_config(), app=app)

    response = TestClient(app).get("/status")

    assert response.status_code == 200
    assert response.json()["lifecycle"] == "created"
    assert app.state.observability is runtime


@pytest.mark.asyncio
async def test_reinstalling_runtime_rebinds_existing_status_route() -> None:
    """同一 app 安装新 Runtime 后，既有路由应读取新 Runtime 而非旧闭包。"""
    app = FastAPI()
    first = install_observability(_config(), app=app)
    await first.close()

    second = install_observability(_config(), app=app)
    response = TestClient(app).get("/status")

    assert app.state.observability is second
    assert response.json()["lifecycle"] == "created"
    assert sum(getattr(route, "path", None) == "/status" for route in app.routes) == 1


def test_disabled_status_does_not_install_route_or_track_workers() -> None:
    """关闭 status 后不应添加路由，也不应维护 Worker 状态。"""
    app = FastAPI()
    runtime = install_observability(
        _config(status_enabled=False, fastapi_enabled=True),
        app=app,
    )
    wrapped = runtime.instrument_worker("worker", lambda: "done")

    assert wrapped() == "done"
    assert runtime.status().enabled is False
    assert runtime.status().workers == ()
    assert all(getattr(route, "path", None) != "/status" for route in app.routes)
    assert app.state.observability is runtime
    assert TestClient(app).get("/status").status_code == 404


def test_status_http_contract_excludes_schema_health_metrics_and_metric_totals() -> None:
    """Status HTTP 契约应隐藏 schema，并保持与 health、metrics 及累计值分离。"""
    app = FastAPI()
    runtime = install_observability(_config(), app=app)
    runtime.instrument_worker("worker", lambda: "done")()
    client = TestClient(app)

    response = client.get("/status")
    worker = response.json()["workers"][0]

    assert response.status_code == 200
    assert set(worker) == {
        "operation",
        "in_flight",
        "last_result",
        "last_finished_at",
    }
    assert "/status" not in app.openapi()["paths"]
    assert client.get("/health").status_code == 404
    assert client.get("/metrics").status_code == 404


def test_scheduler_and_worker_status_work_without_fastapi() -> None:
    """APScheduler + Worker 形态不依赖 FastAPI app 或 HTTP 路由。"""
    scheduler = _FakeScheduler()
    scheduler.jobs.extend([object(), object()])
    runtime = install_observability(
        _config(apscheduler_enabled=True),
        scheduler=scheduler,
    )
    runtime.instrument_worker("worker", lambda: "done")()

    status = runtime.status()
    scheduler_status = next(
        item for item in status.instrumentations if item.name == "apscheduler"
    )

    assert scheduler_status.installed is True
    assert scheduler_status.details["listener_installed"] is True
    assert scheduler_status.details["job_count"] == 2
    assert status.workers[0].last_result == "success"


def test_fastapi_scheduler_and_worker_status_are_aggregated() -> None:
    """完整组合形态应在同一快照聚合 FastAPI、Scheduler 和 Worker。"""
    app = FastAPI()
    scheduler = _FakeScheduler()
    runtime = install_observability(
        _config(fastapi_enabled=True, apscheduler_enabled=True),
        app=app,
        scheduler=scheduler,
    )
    runtime.instrument_worker("worker", lambda: "done")()

    payload = TestClient(app).get("/status").json()

    assert {item["name"] for item in payload["instrumentations"]} == {
        "fastapi",
        "apscheduler",
    }
    assert payload["workers"][0]["last_result"] == "success"


def test_shipped_yaml_enables_status() -> None:
    """项目提供的真实 observability.yaml 应显式启用 status。"""
    config_path = Path(__file__).parents[1] / "config" / "observability.yaml"

    config = load_observability_config(config_path)

    assert config.status.enabled is True


def test_yaml_uses_status_default_and_accepts_disabled_switch(tmp_path: Path) -> None:
    """YAML 未声明 status 时应使用默认值，显式 false 时应关闭能力。"""
    default_path = tmp_path / "default.yaml"
    disabled_path = tmp_path / "disabled.yaml"
    default_path.write_text(
        "observability:\n  service:\n    name: config-test\n",
        encoding="utf-8",
    )
    disabled_path.write_text(
        "observability:\n  service:\n    name: config-test\n  status:\n    enabled: false\n",
        encoding="utf-8",
    )

    assert load_observability_config(default_path).status.enabled is True
    assert load_observability_config(disabled_path).status.enabled is False


def test_yaml_rejects_unknown_status_fields(tmp_path: Path) -> None:
    """Status 稳定配置应拒绝未知键，避免拼写错误被静默忽略。"""
    config_path = tmp_path / "invalid.yaml"
    config_path.write_text(
        "observability:\n"
        "  service:\n"
        "    name: config-test\n"
        "  status:\n"
        "    enabled: true\n"
        "    unknown: true\n",
        encoding="utf-8",
    )

    with pytest.raises(ObservabilityConfigError, match="status.unknown"):
        load_observability_config(config_path)
