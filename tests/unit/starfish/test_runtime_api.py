"""starfish 高层运行时 API 测试。

验证：
1. `StarfishServerManager(path)` 可返回统一运行时对象。
2. 单 endpoint runtime 支持 `describe/start/status/read/stop` 基本流程。
3. 多 endpoint runtime 在未指定 endpoint_id 时，`write()` 会拒绝歧义调用。

测试阶段：P1 开发期验证。
外部依赖：无。
不能证明：真实 TCP/socket 驱动生命周期。
"""

from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path

import pytest

from starfish.api import server_manager_api
from starfish.api import StarfishServerManager
from starfish.application import ServerManagerBuildError, StarfishRuntimeContext
from starfish.application.runtime import create_server_registry
from starfish.domain import (
    DriverEntry,
    StarfishEndpointConfig,
    StarfishServerConfig,
    StarfishServerMemberConfig,
    ValidationResult,
)


class _BoundaryDriverFactory:
    """为职责边界测试创建不可启动的 fake driver entry。"""

    def create_driver_for_endpoint(
        self,
        server: StarfishServerMemberConfig,
        endpoint: StarfishEndpointConfig,
    ) -> DriverEntry:
        """返回不可用 entry，避免职责边界测试触发真实 driver I/O。"""
        return DriverEntry(
            server=server,
            endpoint=endpoint,
            driver=None,
            available=False,
            reason="boundary-only",
            mode="fake",
        )


def _write_plan(
    tmpdir: str,
    *,
    scenario_id: str,
    endpoints: list[dict[str, object]],
) -> Path:
    point_id = f"{scenario_id}_point_000"
    payload = {
        "schema_version": "1.0.0",
        "scenario_id": scenario_id,
        "generator_version": "0.2.0",
        "generated_at": "2024-01-01T00:00:00+00:00",
        "synthetic": True,
        "server_name": f"{scenario_id} Server",
        "strategy_id": "test",
        "endpoints": endpoints,
        "points": [
            {
                "point_id": point_id,
                "point_name": "TestPoint",
                "node_key": f"ns=2;s={point_id}",
                "variable_key": "Value",
                "value_type": "Float",
                "access_mode": "RO",
                "data_type": "FLOAT64",
            }
        ],
        "capabilities": ["READ"],
        "update_policy": {"default": {"mode": "poll", "interval_ms": 100}},
        "initial_values": {point_id: 12.5},
        "payload_hash": "",
    }
    content = {k: v for k, v in payload.items() if k not in ("payload_hash", "generated_at")}
    canonical = json.dumps(content, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    payload["payload_hash"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    path = Path(tmpdir) / f"{scenario_id}_server_plan.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _runtime_context_for_boundary_test() -> StarfishRuntimeContext:
    """构造 manager 委托测试所需的最小 runtime context。"""
    config = StarfishServerConfig(
        scenario_id="runtime_api_boundary",
        config_name="boundary",
        servers=[
            StarfishServerMemberConfig(
                server_id="boundary-server",
                server_name="Boundary Server",
                endpoints=[
                    StarfishEndpointConfig(
                        endpoint_id="boundary-endpoint",
                        protocol="UNKNOWN_PROTOCOL",
                        host="127.0.0.1",
                        port=0,
                    )
                ],
            )
        ],
    )
    return StarfishRuntimeContext(
        config=config,
        validation=ValidationResult(),
        registry=create_server_registry(config, _BoundaryDriverFactory()),
    )


class TestStarfishRuntimeApi:
    """统一运行时 API 测试。"""

    def test_manager_path_input_delegates_runtime_build_to_composition_root(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """路径入口只委托 API composition root 创建 runtime context。"""
        plan_path = Path("boundary_server_plan.json")
        calls: list[Path] = []

        def fake_build_default_runtime(input_path: Path) -> StarfishRuntimeContext:
            calls.append(input_path)
            return _runtime_context_for_boundary_test()

        monkeypatch.setattr(server_manager_api, "build_runtime", fake_build_default_runtime)

        manager = StarfishServerManager(plan_path)

        assert calls == [plan_path]
        assert manager.config.scenario_id == "runtime_api_boundary"

    def test_open_runtime_returns_runtime_object(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            plan_path = _write_plan(
                tmpdir,
                scenario_id="runtime_api_single",
                endpoints=[
                    {
                        "endpoint_id": "runtime_api_single_stub",
                        "endpoint_name": "Stub",
                        "protocol": "UNKNOWN_PROTOCOL",
                        "host": "127.0.0.1",
                        "port": 0,
                    }
                ],
            )

            runtime = StarfishServerManager(plan_path)

            assert isinstance(runtime, StarfishServerManager)
            assert runtime.config.scenario_id == "runtime_api_single"

    def test_runtime_supports_basic_stub_flow(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            plan_path = _write_plan(
                tmpdir,
                scenario_id="runtime_api_flow",
                endpoints=[
                    {
                        "endpoint_id": "runtime_api_flow_stub",
                        "endpoint_name": "Stub",
                        "protocol": "UNKNOWN_PROTOCOL",
                        "host": "127.0.0.1",
                        "port": 0,
                    }
                ],
            )

            runtime = StarfishServerManager(plan_path)
            description = runtime.describe()
            assert description["scenario_id"] == "runtime_api_flow"
            assert description["endpoints"][0]["mode"] == "stub"

            runtime.start()
            status = runtime.status()
            endpoint_status = status["endpoints"]["runtime_api_flow_stub"]
            assert endpoint_status["status"] == "started"

            values = runtime.read()
            assert values["runtime_api_flow_stub"]["runtime_api_flow_point_000"] == 12.5

            runtime.stop()
            stopped_status = runtime.status()
            assert stopped_status["endpoints"]["runtime_api_flow_stub"]["status"] == "stopped"

    def test_write_requires_endpoint_id_when_multiple_available(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            plan_path = _write_plan(
                tmpdir,
                scenario_id="runtime_api_multi",
                endpoints=[
                    {
                        "endpoint_id": "runtime_api_multi_ads",
                        "endpoint_name": "ADS",
                        "protocol": "BECKHOFF_ADS",
                        "host": "127.0.0.1",
                        "port": 0,
                    },
                    {
                        "endpoint_id": "runtime_api_multi_stub",
                        "endpoint_name": "Stub",
                        "protocol": "UNKNOWN_PROTOCOL",
                        "host": "127.0.0.1",
                        "port": 0,
                    },
                ],
            )

            runtime = StarfishServerManager(plan_path)

            with pytest.raises(ValueError, match="endpoint_id"):
                runtime.write("runtime_api_multi_point_000", 1.0)

    def test_open_runtime_raises_runtime_build_error_with_validation_details(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            payload = {
                "schema_version": "1.0.0",
                "scenario_id": "runtime_api_invalid",
                "synthetic": True,
                "endpoints": [],
                "points": [],
                "capabilities": [],
                "initial_values": {},
                "payload_hash": "",
            }
            plan_path = Path(tmpdir) / "runtime_api_invalid.json"
            plan_path.write_text(json.dumps(payload), encoding="utf-8")

            with pytest.raises(ServerManagerBuildError, match="校验失败") as exc_info:
                StarfishServerManager(plan_path)

            assert exc_info.value.validation is not None
            assert exc_info.value.validation.errors
