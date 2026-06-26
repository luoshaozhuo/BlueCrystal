"""starfish CLI 测试。

验证：
1. validate-config 正常加载和校验输出。
2. describe 展示 plan 与 facade 装配结果。
3. health 可查询未启动/已启动 facade 状态。
4. read 可启动 simulator 并读取当前值。
5. run 可作为 simulator 运行入口启动并停止 facade。
6. 文件不存在时 CLI 返回非零。
7. 无效 JSON 时 CLI 返回非零。
8. --help 输出正常。

测试阶段：P1 开发期验证 + P2 构建期验证。
使用的替身：临时 JSON 文件。
外部依赖：无。
不能证明：真实工业现场部署行为。
NOT_RUN 条件：无。
"""

from __future__ import annotations

import hashlib
import json
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

import pytest

import starfish.__main__ as starfish_cli
from starfish.__main__ import main
from starfish.application import ServerManagerBuildError
from starfish.domain import ValidationResult


def _write_valid_json(
    tmpdir: str,
    scenario_id: str = "cli_test",
    protocol: str = "BECKHOFF_ADS",
    initial_values: dict | None = None,
) -> Path:
    """写入最小有效 ServerPlan JSON。"""
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


def _write_multi_endpoint_json(tmpdir: str, scenario_id: str = "multi_cli") -> Path:
    """写入多协议 endpoint 的 ServerPlan JSON。"""
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
                "endpoint_id": f"{scenario_id}_ads_ep",
                "endpoint_name": "ADS_EP",
                "protocol": "BECKHOFF_ADS",
                "host": "127.0.0.1",
                "port": 0,
            },
            {
                "endpoint_id": f"{scenario_id}_goose_ep",
                "endpoint_name": "GOOSE_EP",
                "protocol": "GOOSE",
                "host": "127.0.0.1",
                "port": 0,
            },
            {
                "endpoint_id": f"{scenario_id}_stub_ep",
                "endpoint_name": "STUB_EP",
                "protocol": "UNKNOWN_PROTOCOL",
                "host": "127.0.0.1",
                "port": 0,
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


def _write_invalid_json_payload(tmpdir: str, name: str) -> Path:
    """写入结构无效的 JSON。"""
    payload = {
        "schema_version": "1.0.0",
        "scenario_id": name,
        "synthetic": True,
        "endpoints": [],
        "points": [],
        "capabilities": [],
        "initial_values": {},
        "payload_hash": "",
    }
    path = Path(tmpdir) / f"{name}.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


class TestValidatePlanCLI:
    """validate-config CLI 测试。"""

    def test_validate_plan_routes_through_api_function(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """CLI 应通过 `starfish.api` 高层入口触发计划加载。"""

        called_with: list[Path] = []

        def fake_load_config(input_path: Path) -> object:
            called_with.append(input_path)
            return SimpleNamespace(
                config=SimpleNamespace(
                    scenario_id="api_cli",
                    server_name="api_cli server",
                    endpoints=[],
                    points=[],
                    synthetic=True,
                    capabilities=[],
                ),
                validation=SimpleNamespace(
                    is_valid=True,
                    errors=[],
                    warnings=[],
                    passed_checks=[],
                ),
            )

        monkeypatch.setattr(starfish_cli, "load_config", fake_load_config)
        plan_path = Path("/tmp/runtime_api_plan.json")

        assert main(["validate-config", "--input", str(plan_path)]) == 0
        assert called_with == [plan_path]

    @pytest.mark.smoke
    def test_help(self) -> None:
        assert main(["validate-config", "--help"]) == 0

    @pytest.mark.smoke
    def test_load_valid_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            plan_path = _write_valid_json(tmpdir, "cli_validate_ok")
            assert main(["validate-config", "--input", str(plan_path)]) == 0

    def test_invalid_file_reports_errors(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = _write_invalid_json_payload(tmpdir, "bad_validate")
            assert main(["validate-config", "--input", str(path)]) != 0

    def test_missing_file(self) -> None:
        assert main(["validate-config", "--input", "/nonexistent/file.json"]) != 0

    def test_invalid_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "bad.json"
            path.write_text("not valid json {{{", encoding="utf-8")
            assert main(["validate-config", "--input", str(path)]) != 0

    def test_requires_input(self) -> None:
        with pytest.raises(SystemExit) as exc_info:
            main(["validate-config"])
        assert exc_info.value.code != 0


class TestDescribeCLI:
    """describe CLI 测试。"""

    @pytest.mark.smoke
    def test_help(self) -> None:
        assert main(["describe", "--help"]) == 0

    def test_describe_valid_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            plan_path = _write_valid_json(tmpdir, "cli_describe_ok")
            assert main(["describe", "--input", str(plan_path)]) == 0

    def test_describe_multi_endpoint(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            plan_path = _write_multi_endpoint_json(tmpdir, "cli_describe_multi")
            assert main(["describe", "--input", str(plan_path)]) == 0

    def test_describe_missing_file(self) -> None:
        assert main(["describe", "--input", "/nonexistent/file.json"]) != 0

    def test_describe_requires_input(self) -> None:
        with pytest.raises(SystemExit) as exc_info:
            main(["describe"])
        assert exc_info.value.code != 0

    def test_describe_uses_runtime_build_error_details_without_reloading_plan(
        self,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """open_manager 失败时应直接使用异常内的校验明细。"""

        def fake_open_manager(input_path: Path) -> object:
            del input_path
            raise ServerManagerBuildError(
                "校验失败 (2 个错误)",
                validation=ValidationResult(
                    errors=["缺少 endpoints", "缺少 points"],
                ),
            )

        monkeypatch.setattr(starfish_cli, "open_manager", fake_open_manager)

        assert main(["describe", "--input", "/tmp/invalid.json"]) == 1
        captured = capsys.readouterr()
        assert "错误：校验失败 (2 个错误)" in captured.out
        assert "[ERROR] 缺少 endpoints" in captured.out
        assert "[ERROR] 缺少 points" in captured.out


class TestHealthCLI:
    """health CLI 测试。"""

    def test_help(self) -> None:
        assert main(["health", "--help"]) == 0

    def test_health_valid_file_without_start(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            plan_path = _write_valid_json(tmpdir, "cli_health_ok")
            assert main(["health", "--input", str(plan_path)]) == 0

    def test_health_valid_file_with_start(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            plan_path = _write_valid_json(tmpdir, "cli_health_start")
            assert main(["health", "--input", str(plan_path), "--start"]) == 0

    def test_health_missing_file(self) -> None:
        assert main(["health", "--input", "/nonexistent/file.json"]) != 0

    def test_health_invalid_file_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = _write_invalid_json_payload(tmpdir, "bad_health")
            assert main(["health", "--input", str(path)]) != 0

    def test_health_requires_input(self) -> None:
        with pytest.raises(SystemExit) as exc_info:
            main(["health"])
        assert exc_info.value.code != 0


class TestReadCLI:
    """read CLI 测试。"""

    def test_help(self) -> None:
        assert main(["read", "--help"]) == 0

    def test_read_valid_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            plan_path = _write_valid_json(tmpdir, "cli_read_ok")
            assert main(["read", "--input", str(plan_path)]) == 0

    def test_read_selected_point(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            plan_path = _write_valid_json(tmpdir, "cli_read_point")
            point_id = "cli_read_point_point_000"
            assert main(["read", "--input", str(plan_path), "--point", point_id]) == 0

    def test_read_missing_file(self) -> None:
        assert main(["read", "--input", "/nonexistent/file.json"]) != 0

    def test_read_invalid_file_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = _write_invalid_json_payload(tmpdir, "bad_read")
            assert main(["read", "--input", str(path)]) != 0

    def test_read_requires_input(self) -> None:
        with pytest.raises(SystemExit) as exc_info:
            main(["read"])
        assert exc_info.value.code != 0


class TestRunCLI:
    """run CLI 测试。"""

    @pytest.mark.smoke
    def test_help(self) -> None:
        assert main(["run", "--help"]) == 0

    @pytest.mark.smoke
    def test_run_valid_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            plan_path = _write_valid_json(tmpdir, "cli_run_ok")
            assert main(["run", "--input", str(plan_path), "--duration", "0"]) == 0

    def test_run_multi_endpoint(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            plan_path = _write_multi_endpoint_json(tmpdir, "cli_run_multi")
            assert main(["run", "--input", str(plan_path), "--duration", "0"]) == 0

    def test_run_missing_file(self) -> None:
        assert main(["run", "--input", "/nonexistent/file.json", "--duration", "0"]) != 0

    def test_run_invalid_file_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = _write_invalid_json_payload(tmpdir, "bad_run")
            assert main(["run", "--input", str(path), "--duration", "0"]) != 0

    def test_run_requires_input(self) -> None:
        with pytest.raises(SystemExit) as exc_info:
            main(["run"])
        assert exc_info.value.code != 0


class TestTopLevelCLI:
    """顶层 CLI 测试。"""

    def test_no_command_prints_help(self) -> None:
        with pytest.raises(SystemExit) as exc_info:
            main([])
        assert exc_info.value.code != 0

    def test_unknown_command_fails(self) -> None:
        with pytest.raises(SystemExit):
            main(["nonexistent-command"])

    def test_top_level_help(self) -> None:
        assert main(["--help"]) == 0


class TestSeahorseStarfishCLIIntegration:
    """验证 Seahorse 导出 JSON 可被 Starfish CLI 直接消费。"""

    def test_cli_loads_seahorse_exported_json(self) -> None:
        sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))

        from seahorse.exporters.server_plan_exporter import export_server_plan_to_json
        from seahorse.models.scenario import ScenarioConfig
        from seahorse.orchestration import SeahorseGenerator

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
            assert main(["validate-config", "--input", str(plan_path)]) == 0

    def test_cli_runs_seahorse_exported_json(self) -> None:
        sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))

        from seahorse.exporters.server_plan_exporter import export_server_plan_to_json
        from seahorse.models.scenario import ScenarioConfig
        from seahorse.orchestration import SeahorseGenerator

        config = ScenarioConfig(
            scenario_id="cli_run_integration",
            deterministic_seed=77,
            asset_count=2,
            protocol_targets=["BECKHOFF_ADS", "GOOSE"],
        )
        generator = SeahorseGenerator(config)
        _, server_plan = generator.generate_minimal()
        json_str = export_server_plan_to_json(server_plan)

        with tempfile.TemporaryDirectory() as tmpdir:
            plan_path = Path(tmpdir) / "cli_run_integration_server_plan.json"
            plan_path.write_text(json_str, encoding="utf-8")
            assert main(["run", "--input", str(plan_path), "--duration", "0"]) == 0
