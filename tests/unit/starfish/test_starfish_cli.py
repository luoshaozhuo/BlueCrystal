"""starfish CLI 测试。

验证：
1. CLI 只暴露 run 子命令，旧诊断子命令不能作为隐藏入口调用。
2. run 可使用位置参数或既有 --input 用法启动并停止 facade。
3. 文件不存在时 CLI 返回非零。
4. 无效 JSON 时 CLI 返回非零。
5. --help 输出正常。

测试阶段：P1 开发期验证 + P2 构建期验证。
使用的替身：临时 JSON 文件。
外部依赖：无。
不能证明：真实工业现场部署行为。
NOT_RUN 条件：无。
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

import starfish.__main__ as starfish_cli
from starfish.__main__ import main


def _python_m_starfish(*args: str) -> subprocess.CompletedProcess[str]:
    """以真实模块入口执行 CLI，覆盖 `__main__` 的进程退出语义。

    Args:
        *args: 传给 `python -m starfish` 的参数。

    Returns:
        已捕获 stdout/stderr 的子进程结果。
    """
    env = os.environ.copy()
    src_path = str(Path(__file__).resolve().parents[3] / "src")
    existing_pythonpath = env.get("PYTHONPATH")
    env["PYTHONPATH"] = (
        src_path
        if not existing_pythonpath
        else os.pathsep.join([src_path, existing_pythonpath])
    )
    return subprocess.run(
        [sys.executable, "-m", "starfish", *args],
        check=False,
        cwd=Path(__file__).resolve().parents[3],
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


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


class TestRemovedCLICommands:
    """旧诊断命令必须从 CLI 入口彻底移除。"""

    @pytest.mark.parametrize("command", ["validate-config", "describe", "health", "read"])
    def test_removed_command_fails_before_loading_manager(
        self,
        command: str,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """旧命令应被 Typer 拒绝，不能成为隐藏可用入口。"""

        called = False

        def fake_manager(input_path: Path) -> object:
            nonlocal called
            called = True
            raise AssertionError(f"{command} 不应加载 manager: {input_path}")

        monkeypatch.setattr(starfish_cli, "StarfishServerManager", fake_manager)

        with pytest.raises(SystemExit) as exc_info:
            main([command, "--input", "/tmp/runtime_api_plan.json"])

        assert exc_info.value.code != 0
        assert called is False


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

    def test_run_accepts_positional_config_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            plan_path = _write_valid_json(tmpdir, "cli_run_positional")
            assert main(["run", str(plan_path), "--duration", "0"]) == 0

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
        assert main(["run"]) != 0


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


class TestPythonModuleEntrypoint:
    """真实 `python -m starfish` 入口回归测试。"""

    def test_python_m_keeps_run_as_subcommand(self) -> None:
        result = _python_m_starfish("run", "--duration", "0")

        assert result.returncode != 0
        assert "文件不存在: run" not in result.stdout
        assert "文件不存在: run" not in result.stderr
        assert "缺少 server 配置 JSON 文件路径" in result.stderr

    @pytest.mark.parametrize("command", ["validate-config", "describe", "health", "read"])
    def test_python_m_removed_commands_fail_during_parse(self, command: str) -> None:
        result = _python_m_starfish(
            command,
            "--input",
            "/nonexistent/file.json",
            "--duration",
            "0",
        )

        assert result.returncode != 0
        assert "/nonexistent/file.json" not in result.stdout
        assert "/nonexistent/file.json" not in result.stderr
        assert "No such command" in result.stderr or "No such command" in result.stdout


class TestSeahorseStarfishCLIIntegration:
    """验证 Seahorse 导出 JSON 可被 Starfish CLI 直接消费。"""

    def test_cli_runs_seahorse_exported_json_with_positional_config(self) -> None:
        sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))

        from seahorse.adapters.gateways.server_plan_handoff_gateway import export_server_plan_to_json
        from seahorse.domain.scenario import ScenarioConfig
        from seahorse.application.use_cases.scenario_generator import SeahorseGenerator

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
            assert main(["run", str(plan_path), "--duration", "0"]) == 0

    def test_cli_runs_seahorse_exported_json(self) -> None:
        sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))

        from seahorse.adapters.gateways.server_plan_handoff_gateway import export_server_plan_to_json
        from seahorse.domain.scenario import ScenarioConfig
        from seahorse.application.use_cases.scenario_generator import SeahorseGenerator

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
