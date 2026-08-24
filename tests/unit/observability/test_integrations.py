"""验证本地 FastAPI、APScheduler 与 SQLite Audit 最小集成。

测试使用进程内 HTTP client、真实 APScheduler listener 注册和临时 SQLite；
不证明 OTLP、Prometheus scraper 或任何远端服务可用。
"""

from __future__ import annotations

import importlib
from pathlib import Path
import time
from typing import Any, cast

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from observability import install_observability
from observability.audit import AuditQuery, AuditService, SQLiteAuditStore
from observability.config import ObservabilityConfig
from observability.context import bind_observation_context
from observability.example_app import create_app
from observability.manager import ObservabilityRuntime

BackgroundScheduler = cast(
    Any,
    importlib.import_module("apscheduler.schedulers.background").BackgroundScheduler,
)


def _config() -> ObservabilityConfig:
    """创建关闭网络 tracing 的框架集成配置。"""
    return ObservabilityConfig.model_validate(
        {
            "service": {"name": "integration-test", "instance_id": "node-a"},
            "logging": {"enabled": False},
            "tracing": {"enabled": False},
            "instrumentation": {
                "fastapi": {"options": {"expose_metrics": True}},
                "apscheduler": {},
            },
        }
    )


@pytest.mark.asyncio
async def test_fastapi_third_party_instrumentation_minimal_request() -> None:
    """真实 FastAPI adapter 应返回 request ID 并暴露第三方 metrics route。"""
    runtime = ObservabilityRuntime(_config())
    app = FastAPI()

    @app.get("/hello")
    async def hello() -> dict[str, str]:
        """提供只用于验证 middleware 的本地测试路由。"""
        return {"hello": "world"}

    runtime.instrument_fastapi(app)
    await runtime.start()
    try:
        with TestClient(app) as client:
            response = client.get("/hello", headers={"x-request-id": "request-1"})
            assert response.status_code == 200
            assert response.headers["x-request-id"] == "request-1"
            metrics = client.get("/metrics")
            assert metrics.status_code == 200
            assert "http_requests_total" in metrics.text
    finally:
        await runtime.close()


def test_example_app_complete_local_observability_loop(
    tmp_path: Path,
    capfd: pytest.CaptureFixture[str],
) -> None:
    """真实单机示例应闭环 HTTP、scheduler、Worker 和四类输出。

    Console exporter、结构化日志、SQLite 和进程内 Prometheus registry 均为真实
    本地实现；本测试不证明远端 collector 或 scraper 可用。
    """
    config_path = tmp_path / "observability.yaml"
    config_path.write_text(
        """
observability:
  service:
    name: example-test
    instance_id: node-test
  logging:
    enabled: true
    renderer: json
  metrics:
    enabled: true
    namespace: example_test
  tracing:
    enabled: true
    exporter: console
    sample_rate: 1.0
  audit:
    enabled: true
    store: sqlite
    options:
      path: audit.sqlite3
  instrumentation:
    fastapi:
      enabled: true
      options:
        expose_metrics: true
    apscheduler:
      enabled: true
    worker:
      enabled: true
""",
        encoding="utf-8",
    )
    app = create_app(config_path)
    scheduler = app.state.scheduler
    installed_callbacks = {callback for callback, _ in scheduler._listeners}
    assert installed_callbacks

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.post(
            "/tasks/7/run",
            headers={"x-request-id": "request-direct", "x-actor": "operator"},
        )
        assert response.status_code == 200
        assert response.json() == {"task_id": 7}

        failed = client.post("/tasks/8/run?fail=true")
        assert failed.status_code == 500

        created = client.post(
            "/schedules/job-9?task_id=9&delay_seconds=60",
            headers={
                "x-request-id": "request-create",
                "x-actor": "scheduler-operator",
            },
        )
        assert created.status_code == 200
        triggered = client.post(
            "/schedules/job-9/run-now",
            headers={
                "x-request-id": "request-run-now",
                "x-actor": "scheduler-operator",
            },
        )
        assert triggered.status_code == 200

        missing = client.post(
            "/schedules/missing-job/run-now",
            headers={
                "x-request-id": "request-missing",
                "x-actor": "failure-operator",
            },
        )
        assert missing.status_code == 500

        deadline = time.monotonic() + 2.0
        scheduler_state: dict[str, object] = {}
        while time.monotonic() < deadline:
            health = client.get("/health")
            scheduler_state = cast(
                dict[str, object], health.json()["scheduler_executions"]
            )
            if scheduler_state["succeeded"] == 1:
                break
            time.sleep(0.02)
        assert scheduler_state == {"succeeded": 1, "failed": 0, "last_task_id": 9}

        metrics = client.get("/metrics")
        assert metrics.status_code == 200
        assert "http_requests_total" in metrics.text
        assert "example_test_worker_executions_total" in metrics.text
        assert "example_test_scheduler_events_total" in metrics.text
        assert 'event="job_executed"' in metrics.text

        management_audit = client.get(
            "/audit?operation=schedule.run_now&target_id=job-9"
        ).json()
        assert len(management_audit) == 1
        assert management_audit[0]["actor"] == "scheduler-operator"
        assert management_audit[0]["request_id"] == "request-run-now"
        assert management_audit[0]["operation"] == "schedule.run_now"
        assert management_audit[0]["target_id"] == "job-9"
        assert management_audit[0]["result"] == "success"

        failed_management_audit = client.get(
            "/audit?operation=schedule.run_now&target_id=missing-job"
        ).json()
        assert len(failed_management_audit) == 1
        assert failed_management_audit[0]["actor"] == "failure-operator"
        assert failed_management_audit[0]["request_id"] == "request-missing"
        assert failed_management_audit[0]["operation"] == "schedule.run_now"
        assert failed_management_audit[0]["target_id"] == "missing-job"
        assert failed_management_audit[0]["result"] == "failure"
        assert failed_management_audit[0]["error_type"] == "JobLookupError"

        worker_audit = client.get("/audit?operation=task.run&target_id=7").json()
        assert len(worker_audit) == 1
        assert worker_audit[0]["actor"] == "operator"
        assert worker_audit[0]["request_id"] == "request-direct"

    assert scheduler.running is False
    assert installed_callbacks.isdisjoint(
        callback for callback, _ in scheduler._listeners
    )
    assert (tmp_path / "audit.sqlite3").exists()

    output = capfd.readouterr().out
    assert '"event": "business_task_started"' in output
    assert '"event": "business_task_completed"' in output
    assert '"event": "business_task_failed"' in output
    assert '"request_id": "request-direct"' in output
    assert '"job_id": "job-9"' in output
    assert '"service_name": "example-test"' in output
    assert '"trace_id":' in output
    assert '"name": "example.task.execute"' in output
    assert '"name": "scheduler.schedule.run_now"' in output
    assert '"scheduler.target.id": "missing-job"' in output


@pytest.mark.asyncio
async def test_apscheduler_listener_install_and_remove() -> None:
    """公共安装入口应完成真实 scheduler listener 注册与逆序移除。"""
    scheduler = BackgroundScheduler()
    runtime = install_observability(_config(), scheduler=scheduler)
    await runtime.start()
    installed_callbacks = {callback for callback, _ in scheduler._listeners}
    assert installed_callbacks
    await runtime.close()
    assert installed_callbacks.isdisjoint(
        callback for callback, _ in scheduler._listeners
    )


def test_sqlite_audit_store_contract(tmp_path: Path) -> None:
    """SQLite store 应持久化上下文、结果和结构化 detail。"""
    service = AuditService(SQLiteAuditStore(tmp_path / "audit.sqlite3"))
    with bind_observation_context(
        service_name="audit-test",
        service_instance_id="node-1",
        request_id="request-1",
        actor="operator",
        source="http",
    ):
        written = service.success(
            operation="schedule.pause",
            target_type="job",
            target_id="job-1",
            detail={"reason": "maintenance"},
        )
    records = service.query(AuditQuery(operation="schedule.pause"))
    assert records == (written,)
    assert records[0].service_name == "audit-test"
    assert records[0].detail == {"reason": "maintenance"}
