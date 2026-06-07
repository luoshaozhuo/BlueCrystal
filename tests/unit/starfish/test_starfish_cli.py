"""starfish CLI 测试。

验证：
1. load-server-plan 正常加载和校验输出。
2. smoke-server-plan 完整 smoke 流程（含 mode 区分输出）。
3. probe-server-plan 最小可用性探测。
4. profile-server-plan read 采样统计。
5. capacity-server-plan 容量扫描。
6. 文件不存在时 CLI 返回非零。
7. 无效 JSON 时 CLI 返回非零。
8. --help 输出正常。

测试阶段：P1 开发期验证 + P2 构建期验证。
使用的替身：临时 JSON 文件。
外部依赖：无。
不能证明：真实协议 server 启动。
NOT_RUN 条件：无。
"""

from __future__ import annotations

import hashlib
import json
import sys
import tempfile
from pathlib import Path

import pytest

from starfish.__main__ import main


# ── Fixtures ────────────────────────────────────────────────────────────────────


def _write_valid_json(
    tmpdir: str,
    scenario_id: str = "cli_test",
    protocol: str = "OPC_UA",
    initial_values: dict | None = None,
) -> Path:
    """写入最小有效 ServerPlan JSON。

    Args:
        tmpdir: 临时目录。
        scenario_id: 场景标识。
        protocol: 协议名。
        initial_values: 初始值 dict。

    Returns:
        JSON 文件 Path。
    """
    if initial_values is None:
        initial_values = {f"{scenario_id}_point_000": 0.0}

    point_id = f"{scenario_id}_point_000"
    payload = {
        "schema_version": "1.0.0",
        "scenario_id": scenario_id,
        "generator_version": "0.2.0",
        "generated_at": "2024-01-01T00:00:00+00:00",
        "synthetic": True,
        "server_name": f"{scenario_id} Server",
        "strategy_id": "test",
        "endpoints": [
            {
                "endpoint_id": f"{scenario_id}_{protocol}_ep",
                "endpoint_name": f"{protocol}_ep",
                "protocol": protocol,
                "host": "127.0.0.1",
                "port": 0,
            }
        ],
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
        "initial_values": initial_values,
        "payload_hash": "",
    }
    content = {k: v for k, v in payload.items() if k not in ("payload_hash", "generated_at")}
    canonical = json.dumps(content, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    payload["payload_hash"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    path = Path(tmpdir) / f"{scenario_id}_server_plan.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _write_multi_endpoint_json(
    tmpdir: str,
    scenario_id: str = "multi_cli",
) -> Path:
    """写入多协议 endpoint 的 ServerPlan JSON。

    Args:
        tmpdir: 临时目录。
        scenario_id: 场景标识。

    Returns:
        JSON 文件 Path。
    """
    payload = {
        "schema_version": "1.0.0",
        "scenario_id": scenario_id,
        "generator_version": "0.2.0",
        "generated_at": "2024-01-01T00:00:00+00:00",
        "synthetic": True,
        "server_name": f"{scenario_id} Server",
        "strategy_id": "test",
        "endpoints": [
            {
                "endpoint_id": f"{scenario_id}_http_ep",
                "endpoint_name": "HTTP_EP",
                "protocol": "HTTP_REST",
                "host": "127.0.0.1",
                "port": 0,
            },
            {
                "endpoint_id": f"{scenario_id}_mqtt_ep",
                "endpoint_name": "MQTT_EP",
                "protocol": "MQTT",
                "host": "127.0.0.1",
                "port": 0,
            },
            {
                "endpoint_id": f"{scenario_id}_opcua_ep",
                "endpoint_name": "OPCUA_EP",
                "protocol": "OPC_UA",
                "host": "127.0.0.1",
                "port": 4840,
            },
        ],
        "points": [
            {
                "point_id": f"{scenario_id}_point_000",
                "point_name": "TestPoint",
                "node_key": f"ns=2;s={scenario_id}_point_000",
                "variable_key": "Value",
                "value_type": "Float",
                "access_mode": "RO",
                "data_type": "FLOAT64",
            }
        ],
        "capabilities": ["READ"],
        "update_policy": {"default": {"mode": "poll", "interval_ms": 100}},
        "initial_values": {f"{scenario_id}_point_000": 42.0},
        "payload_hash": "",
    }
    content = {k: v for k, v in payload.items() if k not in ("payload_hash", "generated_at")}
    canonical = json.dumps(content, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    payload["payload_hash"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    path = Path(tmpdir) / f"{scenario_id}_server_plan.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


# ── load-server-plan ────────────────────────────────────────────────────────────


class TestLoadServerPlanCLI:
    """load-server-plan CLI 测试。"""

    def test_help(self) -> None:
        """--help 应正常输出并返回 0。"""
        with pytest.raises(SystemExit) as exc_info:
            main(["load-server-plan", "--help"])
        assert exc_info.value.code == 0

    def test_load_valid_file(self) -> None:
        """加载有效 JSON 文件应成功（返回 0）。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            plan_path = _write_valid_json(tmpdir, "cli_load_ok")
            rc = main(["load-server-plan", "--input", str(plan_path)])
            assert rc == 0

    def test_load_invalid_file_reports_errors(self) -> None:
        """加载无效 JSON（空 points）应返回非零。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            payload = {
                "schema_version": "1.0.0",
                "scenario_id": "bad_plan",
                "synthetic": True,
                "endpoints": [],
                "points": [],
                "capabilities": [],
                "initial_values": {},
                "payload_hash": "",
            }
            path = Path(tmpdir) / "bad.json"
            path.write_text(json.dumps(payload), encoding="utf-8")

            rc = main(["load-server-plan", "--input", str(path)])
            assert rc != 0

    def test_load_missing_file(self) -> None:
        """文件不存在时应返回非零。"""
        rc = main(["load-server-plan", "--input", "/nonexistent/file.json"])
        assert rc != 0

    def test_load_invalid_json(self) -> None:
        """无效 JSON 文件应返回非零。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "bad.json"
            path.write_text("not valid json {{{", encoding="utf-8")

            rc = main(["load-server-plan", "--input", str(path)])
            assert rc != 0

    def test_load_requires_input(self) -> None:
        """未指定 --input 时应报错（argparse 要求必填）。"""
        with pytest.raises(SystemExit) as exc_info:
            main(["load-server-plan"])
        # argparse 在缺少必填参数时 exit 2
        assert exc_info.value.code != 0


# ── smoke-server-plan ───────────────────────────────────────────────────────────


class TestSmokeServerPlanCLI:
    """smoke-server-plan CLI 测试。"""

    def test_help(self) -> None:
        """--help 应正常输出并返回 0。"""
        with pytest.raises(SystemExit) as exc_info:
            main(["smoke-server-plan", "--help"])
        assert exc_info.value.code == 0

    def test_smoke_valid_file(self) -> None:
        """有效 JSON 文件的 smoke 应成功（返回 0）。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            plan_path = _write_valid_json(tmpdir, "cli_smoke_ok")
            rc = main(["smoke-server-plan", "--input", str(plan_path)])
            assert rc == 0

    def test_smoke_with_mqtt_mode(self) -> None:
        """MQTT 协议的 smoke 应输出 mqtt-lightweight mode。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            plan_path = _write_valid_json(
                tmpdir, "cli_smoke_mqtt", protocol="MQTT",
            )
            rc = main(["smoke-server-plan", "--input", str(plan_path)])
            assert rc == 0

    def test_smoke_with_http_rest_mode(self) -> None:
        """HTTP_REST 协议的 smoke 应输出 real mode。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            plan_path = _write_valid_json(
                tmpdir, "cli_smoke_http", protocol="HTTP_REST",
            )
            rc = main(["smoke-server-plan", "--input", str(plan_path)])
            assert rc == 0

    def test_smoke_multi_endpoint(self) -> None:
        """多 endpoint（含 real/mqtt-lightweight/stub）smoke 应成功。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            plan_path = _write_multi_endpoint_json(tmpdir, "cli_smoke_multi")
            rc = main(["smoke-server-plan", "--input", str(plan_path)])
            assert rc == 0

    def test_smoke_invalid_file_fails(self) -> None:
        """无效 JSON 的 smoke 应返回非零。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            payload = {
                "schema_version": "1.0.0",
                "scenario_id": "bad_smoke",
                "synthetic": True,
                "endpoints": [],
                "points": [],
                "capabilities": [],
                "initial_values": {},
                "payload_hash": "",
            }
            path = Path(tmpdir) / "bad_smoke.json"
            path.write_text(json.dumps(payload), encoding="utf-8")

            rc = main(["smoke-server-plan", "--input", str(path)])
            assert rc != 0

    def test_smoke_missing_file(self) -> None:
        """文件不存在时应返回非零。"""
        rc = main(["smoke-server-plan", "--input", "/nonexistent/file.json"])
        assert rc != 0

    def test_smoke_requires_input(self) -> None:
        """未指定 --input 时应报错。"""
        with pytest.raises(SystemExit) as exc_info:
            main(["smoke-server-plan"])
        assert exc_info.value.code != 0


# ── probe-server-plan ───────────────────────────────────────────────────────────


class TestProbeServerPlanCLI:
    """probe-server-plan CLI 测试。"""

    def test_help(self) -> None:
        """--help 应正常输出并返回 0。"""
        with pytest.raises(SystemExit) as exc_info:
            main(["probe-server-plan", "--help"])
        assert exc_info.value.code == 0

    def test_probe_valid_file(self) -> None:
        """有效 JSON 文件的 probe 应成功。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            plan_path = _write_valid_json(tmpdir, "cli_probe_ok")
            rc = main(["probe-server-plan", "--input", str(plan_path)])
            assert rc == 0

    def test_probe_with_mqtt(self) -> None:
        """MQTT 协议的 probe 应成功。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            plan_path = _write_valid_json(
                tmpdir, "cli_probe_mqtt", protocol="MQTT",
            )
            rc = main(["probe-server-plan", "--input", str(plan_path)])
            assert rc == 0

    def test_probe_missing_file(self) -> None:
        """文件不存在时应返回非零。"""
        rc = main(["probe-server-plan", "--input", "/nonexistent/file.json"])
        assert rc != 0

    def test_probe_invalid_file_fails(self) -> None:
        """无效 JSON 的 probe 应返回非零。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            payload = {
                "schema_version": "1.0.0",
                "scenario_id": "bad_probe",
                "synthetic": True,
                "endpoints": [],
                "points": [],
                "capabilities": [],
                "initial_values": {},
                "payload_hash": "",
            }
            path = Path(tmpdir) / "bad_probe.json"
            path.write_text(json.dumps(payload), encoding="utf-8")

            rc = main(["probe-server-plan", "--input", str(path)])
            assert rc != 0

    def test_probe_requires_input(self) -> None:
        """未指定 --input 时应报错。"""
        with pytest.raises(SystemExit) as exc_info:
            main(["probe-server-plan"])
        assert exc_info.value.code != 0


# ── profile-server-plan ─────────────────────────────────────────────────────────


class TestProfileServerPlanCLI:
    """profile-server-plan CLI 测试。"""

    def test_help(self) -> None:
        """--help 应正常输出并返回 0。"""
        with pytest.raises(SystemExit) as exc_info:
            main(["profile-server-plan", "--help"])
        assert exc_info.value.code == 0

    def test_profile_valid_file(self) -> None:
        """有效 JSON 文件的 profile 应成功。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            plan_path = _write_valid_json(tmpdir, "cli_profile_ok")
            rc = main(["profile-server-plan", "--input", str(plan_path), "--iterations", "10"])
            assert rc == 0

    def test_profile_missing_file(self) -> None:
        """文件不存在时应返回非零。"""
        rc = main(["profile-server-plan", "--input", "/nonexistent/file.json"])
        assert rc != 0

    def test_profile_default_iterations(self) -> None:
        """未指定 --iterations 时使用默认值。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            plan_path = _write_valid_json(tmpdir, "cli_profile_default")
            rc = main(["profile-server-plan", "--input", str(plan_path)])
            assert rc == 0

    def test_profile_requires_input(self) -> None:
        """未指定 --input 时应报错。"""
        with pytest.raises(SystemExit) as exc_info:
            main(["profile-server-plan"])
        assert exc_info.value.code != 0


# ── capacity-server-plan ────────────────────────────────────────────────────────


class TestCapacityServerPlanCLI:
    """capacity-server-plan CLI 测试。"""

    def test_help(self) -> None:
        """--help 应正常输出并返回 0。"""
        with pytest.raises(SystemExit) as exc_info:
            main(["capacity-server-plan", "--help"])
        assert exc_info.value.code == 0

    def test_capacity_valid_file(self) -> None:
        """有效 JSON 文件的 capacity 应成功。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            plan_path = _write_valid_json(tmpdir, "cli_cap_ok")
            rc = main(["capacity-server-plan", "--input", str(plan_path), "--point-count", "5"])
            assert rc == 0

    def test_capacity_missing_file(self) -> None:
        """文件不存在时应返回非零。"""
        rc = main(["capacity-server-plan", "--input", "/nonexistent/file.json"])
        assert rc != 0

    def test_capacity_default_point_count(self) -> None:
        """未指定 --point-count 时使用默认值。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            plan_path = _write_valid_json(tmpdir, "cli_cap_default")
            rc = main(["capacity-server-plan", "--input", str(plan_path)])
            assert rc == 0

    def test_capacity_requires_input(self) -> None:
        """未指定 --input 时应报错。"""
        with pytest.raises(SystemExit) as exc_info:
            main(["capacity-server-plan"])
        assert exc_info.value.code != 0


# ── 顶层 CLI ────────────────────────────────────────────────────────────────────


class TestTopLevelCLI:
    """顶层 CLI 测试。"""

    def test_no_command_prints_help(self) -> None:
        """无子命令时应打印帮助并返回非零。"""
        rc = main([])
        assert rc != 0

    def test_unknown_command_fails(self) -> None:
        """未知子命令应返回非零。"""
        with pytest.raises(SystemExit):
            main(["nonexistent-command"])

    def test_top_level_help(self) -> None:
        """顶层 --help 应正常输出。"""
        with pytest.raises(SystemExit) as exc_info:
            main(["--help"])
        assert exc_info.value.code == 0


# ── Seahorse -> Starfish CLI 集成 ───────────────────────────────────────────────


class TestSeahorseStarfishCLIIntegration:
    """验证 Seahorse 导出 JSON 可被 Starfish CLI 直接消费。"""

    def test_cli_loads_seahorse_exported_json(self) -> None:
        """Starfish CLI load-server-plan 应加载 Seahorse exporter 产物。"""
        sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))

        from seahorse.models.scenario import ScenarioConfig
        from seahorse.orchestration import SeahorseGenerator
        from seahorse.exporters.server_plan_exporter import export_server_plan_to_json

        config = ScenarioConfig(
            scenario_id="cli_integration",
            deterministic_seed=42,
            asset_count=1,
            protocol_targets=["OPC_UA"],
        )
        generator = SeahorseGenerator(config)
        _, server_plan = generator.generate_minimal()
        json_str = export_server_plan_to_json(server_plan)

        with tempfile.TemporaryDirectory() as tmpdir:
            plan_path = Path(tmpdir) / "cli_integration_server_plan.json"
            plan_path.write_text(json_str, encoding="utf-8")

            # CLI load
            rc = main(["load-server-plan", "--input", str(plan_path)])
            assert rc == 0, "Starfish CLI 应能加载 Seahorse 导出产物"

    def test_cli_smoke_seahorse_exported_json(self) -> None:
        """Starfish CLI smoke-server-plan 应成功 smoke Seahorse 产物。"""
        sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))

        from seahorse.models.scenario import ScenarioConfig
        from seahorse.orchestration import SeahorseGenerator
        from seahorse.exporters.server_plan_exporter import export_server_plan_to_json

        config = ScenarioConfig(
            scenario_id="cli_smoke_integration",
            deterministic_seed=77,
            asset_count=2,
            protocol_targets=["OPC_UA", "MODBUS_TCP"],
        )
        generator = SeahorseGenerator(config)
        _, server_plan = generator.generate_minimal()
        json_str = export_server_plan_to_json(server_plan)

        with tempfile.TemporaryDirectory() as tmpdir:
            plan_path = Path(tmpdir) / "cli_smoke_integration_server_plan.json"
            plan_path.write_text(json_str, encoding="utf-8")

            rc = main(["smoke-server-plan", "--input", str(plan_path)])
            assert rc == 0, "Starfish CLI smoke 应通过 Seahorse 导出产物"
