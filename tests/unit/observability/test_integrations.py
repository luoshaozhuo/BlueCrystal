"""验证本地 FastAPI、APScheduler 与 SQLite Audit 最小集成。

测试使用进程内 HTTP client、真实 APScheduler listener 注册和临时 SQLite；
不证明 OTLP、Prometheus scraper 或任何远端服务可用。
"""

from __future__ import annotations

import importlib
from pathlib import Path
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


def test_example_app_installs_structure_before_lifespan(tmp_path: Path) -> None:
    """真实 composition root 不得在 FastAPI startup 阶段新增 middleware。"""
    config_path = tmp_path / "observability.yaml"
    config_path.write_text(
        """
observability:
  service:
    name: composition-test
  logging:
    enabled: false
  metrics:
    enabled: true
  tracing:
    enabled: false
  audit:
    enabled: false
  instrumentation:
    fastapi:
      enabled: true
      options:
        expose_metrics: true
    worker:
      enabled: true
""",
        encoding="utf-8",
    )
    app = create_app(config_path)
    with TestClient(app) as client:
        response = client.post("/tasks/7/run")
        assert response.status_code == 200
        assert response.json() == {"task_id": 7}
        assert client.get("/metrics").status_code == 200


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
