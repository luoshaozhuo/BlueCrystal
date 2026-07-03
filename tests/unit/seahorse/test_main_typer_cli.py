"""Seahorse ``__main__.py`` Typer CLI 行为测试。

验证：

1. ``__main__.py`` 是 Typer app，且 4 个子命令
   （``generate-scenario`` / ``export-bundle`` / ``validate-bundle`` /
   ``export-server-config``）均已注册。
2. ``__main__.py`` 使用 Typer / Click 而非 argparse。
3. ``__main__.py`` AST 层面不 import ``seahorse.domain`` /
   ``seahorse.application`` / ``seahorse.adapters`` /
   ``seahorse.infrastructure``。
4. ``__main__.py`` 不构造 backend / scheduler / repository / writer。
5. CLI 子命令基本可用性（生成、导出、校验、ServerConfig 导出两种模式）。
6. CLI 异常处理：通过 ``typer.Exit(code=1)`` 返回非零退出码，不向终端
   直接抛出底层异常。
7. CLI 不构造 ``ScenarioConfig``：通过 facade 的 wrapper
   ``generate_bundle_from_cli_params`` /
   ``generate_minimal_server_config_from_cli_params`` 装配。

测试阶段：开发期验证 (P1) + 构建期验证 (P2)。
使用的替身：无 — 全部使用真实 ``SeahorseFacade`` 与 ``SeahorseGenerator``。
不能证明：跨进程 / 真实终端 / shell 兼容。
NOT_RUN 条件：无。
"""
from __future__ import annotations

import ast
import inspect
import json
import tempfile
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[3]
SEAHORSE_MAIN_FILE = PROJECT_ROOT / "src" / "seahorse" / "__main__.py"
SEAHORSE_API_DIR = PROJECT_ROOT / "src" / "seahorse" / "api"


def _read_text(path: Path) -> str:
    """读取文件 UTF-8 文本。

    Args:
        path: 目标文件绝对路径。

    Returns:
        文件正文文本。
    """
    return path.read_text(encoding="utf-8")


# ── 静态约束 ────────────────────────────────────────────────────────────────────


def test_main_module_uses_typer() -> None:
    """``__main__.py`` 必须 import 并使用 Typer。"""
    text = _read_text(SEAHORSE_MAIN_FILE)
    assert "import typer" in text, "__main__.py 必须 import typer"
    assert "Typer(" in text or "typer.Typer" in text, "__main__.py 必须实例化 Typer app"
    assert "@app.command" in text, "__main__.py 必须用 @app.command 注册子命令"


def test_main_module_does_not_use_argparse() -> None:
    """``__main__.py`` 不得使用 argparse（v4.2 蓝图 §5.2 强制 Typer）。"""
    text = _read_text(SEAHORSE_MAIN_FILE)
    assert "argparse" not in text, "__main__.py 不应 import 或使用 argparse"
    assert "ArgumentParser" not in text, "__main__.py 不应使用 argparse.ArgumentParser"


def test_main_module_forbids_inner_layer_imports() -> None:
    """``__main__.py`` 不得 import domain / application / adapters / infrastructure。"""
    text = _read_text(SEAHORSE_MAIN_FILE)
    tree = ast.parse(text)
    forbidden_prefixes = (
        "seahorse.domain",
        "seahorse.application",
        "seahorse.adapters",
        "seahorse.infrastructure",
    )
    offenders: list[tuple[str, str]] = []
    for node in ast.walk(tree):
        module: str | None = None
        if isinstance(node, ast.Import):
            for alias in node.names:
                module = alias.name
        elif isinstance(node, ast.ImportFrom):
            module = node.module
        if module is None:
            continue
        for prefix in forbidden_prefixes:
            if module == prefix or module.startswith(prefix + "."):
                offenders.append((prefix, module))
                break
    assert offenders == [], (
        "__main__.py 不应 import 内层模块: "
        f"{sorted(set(module for _, module in offenders))}"
    )


def test_main_module_only_imports_allowed_dependencies() -> None:
    """``__main__.py`` 只允许 import 标准库 / typer / seahorse.api。

    v4.2 蓝图 §2.1 / §5.2 / §9：CLI 薄入口只能 import 标准库 / typer
    / click（通过 typer 间接） / ``seahorse.api``；不得 import
    ``seahorse.domain`` / ``seahorse.application`` /
    ``seahorse.adapters`` / ``seahorse.infrastructure``，也不得
    import 第三方 CLI 框架（argparse 已经被排除）。
    """
    import sys as _sys

    text = _read_text(SEAHORSE_MAIN_FILE)
    tree = ast.parse(text)
    stdlib_names = set(_sys.stdlib_module_names)
    offenders: list[str] = []
    for node in ast.walk(tree):
        module: str | None = None
        if isinstance(node, ast.Import):
            for alias in node.names:
                module = alias.name.split(".")[0]
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                module = node.module.split(".")[0]
        if not module:
            continue
        # 允许标准库、typer、seahorse
        if module in stdlib_names:
            continue
        if module in {"typer", "seahorse", "__future__"}:
            continue
        offenders.append(module)
    assert offenders == [], (
        f"__main__.py 只允许 import 标准库 / typer / seahorse；违规: {sorted(set(offenders))}"
    )


def test_main_module_does_not_construct_backend_or_runtime() -> None:
    """``__main__.py`` 不得直接构造 backend / scheduler / repository / writer。"""
    text = _read_text(SEAHORSE_MAIN_FILE)
    forbidden_constructs = (
        "InMemoryStarfishWriterBackend",
        "InMemoryDataSourceRuntime",
        "DeterministicScheduler",
        "MonotonicClock",
        "WhaleMetadataRepository",
        "build_starfish_writer_gateway",
        "build_write_plan_use_case",
        "build_dispatch_write_batch_use_case",
        "build_runtime_smoke_workflow",
        "build_seahorse_facade",
    )
    offenders = [name for name in forbidden_constructs if name in text]
    assert offenders == [], (
        "__main__.py 不应直接构造 backend / scheduler / repository / writer "
        f"或调用 container.build_*: {offenders}"
    )


def test_main_module_does_not_construct_scenario_config_directly() -> None:
    """``__main__.py`` 不得在 AST 层引用 ``ScenarioConfig``。

    该检查扫描 import 语句和 identifier 引用，确保薄入口不直接构造
    domain model；docstring 中提到 "ScenarioConfig" 仅作为规则说明，
    不算违规。
    """
    text = _read_text(SEAHORSE_MAIN_FILE)
    tree = ast.parse(text)
    offenders: list[str] = []
    for node in ast.walk(tree):
        # 检查 import 与 from import
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "ScenarioConfig" or alias.name.endswith(".ScenarioConfig"):
                    offenders.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module and (
                node.module == "ScenarioConfig"
                or node.module.endswith(".ScenarioConfig")
            ):
                offenders.append(node.module)
        # 检查 Name / Attribute identifier 引用
        if isinstance(node, ast.Name) and node.id == "ScenarioConfig":
            offenders.append(f"Name[{node.lineno}]")
        if isinstance(node, ast.Attribute) and node.attr == "ScenarioConfig":
            offenders.append(f"Attribute[{node.lineno}]")
    assert offenders == [], (
        "__main__.py AST 层面不应引用 ScenarioConfig；"
        f"应通过 SeahorseFacade wrapper 间接装配 domain model。违规: {offenders}"
    )


# ── 命令注册 ────────────────────────────────────────────────────────────────────


def test_typer_app_registers_required_subcommands() -> None:
    """Typer app 必须注册 4 个子命令。"""
    from typer.testing import CliRunner
    from seahorse.__main__ import app

    runner = CliRunner()
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    for cmd in ("generate-scenario", "export-bundle", "validate-bundle", "export-server-config"):
        assert cmd in result.output, f"未注册子命令: {cmd}"


def test_typer_app_is_typer_instance() -> None:
    """``seahorse.__main__.app`` 必须是 :class:`typer.Typer` 实例。"""
    from seahorse.__main__ import app

    assert isinstance(app, __import__("typer").Typer)


def test_main_exports_app_and_main() -> None:
    """``__main__`` 必须导出 ``app`` 与 ``main``。"""
    import seahorse.__main__ as main_module

    assert hasattr(main_module, "app")
    assert hasattr(main_module, "main")
    assert callable(main_module.main)


# ── main() 顶层入口签名 ────────────────────────────────────────────────────────────


def test_main_function_signature() -> None:
    """``main(argv) -> int`` 签名必须保留，便于测试 / 脚本调用。"""
    from seahorse.__main__ import main

    sig = inspect.signature(main)
    params = list(sig.parameters.values())
    assert len(params) == 1
    assert params[0].name == "argv"
    # argv 应可为 None 或 list[str]
    ann = params[0].annotation
    assert ann in ("list[str] | None", "Optional[list[str]]") or "list" in str(ann)


def test_main_returns_zero_on_success() -> None:
    """正常子命令执行后 ``main()`` 返回 0。"""
    from typer.testing import CliRunner
    from seahorse.__main__ import app

    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        result = runner.invoke(
            app,
            [
                "generate-scenario",
                "--scenario-id", "main_ok",
                "--seed", "42",
                "--asset-count", "1",
                "--duration", "0.5",
                "--output-dir", tmpdir,
                "--start-time", "2024-01-01T00:00:00+00:00",
            ],
        )
        assert result.exit_code == 0, result.output


def test_main_returns_zero_for_help_in_standalone_false() -> None:
    """``main()`` 在 ``--help`` 下不应抛异常，应返回 0（``standalone_mode=False``）。

    :mod:`seahorse.__main__` 的 :func:`main` 显式使用
    ``standalone_mode=False`` 调用 Typer app，以便返回 int 给调用方，
    同时避免 Typer 在正常完成后调用 ``sys.exit(0)``。``--help`` 通过
    Typer 内部处理后返回 0。
    """
    from seahorse.__main__ import main

    rc = main(["generate-scenario", "--help"])
    assert rc == 0


def test_main_returns_zero_on_successful_subcommand() -> None:
    """``main()`` 在子命令正常完成时应返回 0。"""
    import tempfile

    from seahorse.__main__ import main

    with tempfile.TemporaryDirectory() as tmpdir:
        rc = main([
            "generate-scenario",
            "--scenario-id", "main_zero",
            "--seed", "42",
            "--asset-count", "1",
            "--duration", "0.5",
            "--output-dir", tmpdir,
            "--start-time", "2024-01-01T00:00:00+00:00",
        ])
        assert rc == 0


# ── 子命令错误处理 ────────────────────────────────────────────────────────────────


def test_cli_invalid_start_time_returns_nonzero() -> None:
    """无效 ``--start-time`` 应返回非零退出码，不抛出底层异常。"""
    from typer.testing import CliRunner
    from seahorse.__main__ import app

    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "generate-scenario",
            "--scenario-id", "bad_st",
            "--start-time", "not-a-datetime",
        ],
    )
    assert result.exit_code != 0
    # 错误应通过 typer 输出到 stderr（CliRunner 默认 mix_stderr=True）
    assert "start_time" in result.output or "start_time" in result.output.lower()


def test_cli_validate_bundle_json_parse_error_returns_nonzero() -> None:
    """``validate-bundle`` 遇到 JSON 解析错误应返回非零退出码。"""
    from typer.testing import CliRunner
    from seahorse.__main__ import app

    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        bad = Path(tmpdir) / "bad.json"
        bad.write_text("{not valid json", encoding="utf-8")
        result = runner.invoke(app, ["validate-bundle", "--input", str(bad)])
        assert result.exit_code != 0


def test_cli_export_bundle_missing_file_returns_nonzero() -> None:
    """``export-bundle`` 缺失输入文件应返回非零退出码。"""
    from typer.testing import CliRunner
    from seahorse.__main__ import app

    runner = CliRunner()
    result = runner.invoke(
        app,
        ["export-bundle", "--input", "/nonexistent/path/missing.json"],
    )
    assert result.exit_code != 0


def test_cli_export_server_config_missing_input_file_returns_nonzero() -> None:
    """``export-server-config`` 缺失 ``--input`` 文件应返回非零退出码。"""
    from typer.testing import CliRunner
    from seahorse.__main__ import app

    runner = CliRunner()
    result = runner.invoke(
        app,
        ["export-server-config", "--input", "/nonexistent/path/missing.json"],
    )
    assert result.exit_code != 0


def test_cli_export_server_config_no_input_no_scenario_id_returns_nonzero() -> None:
    """``export-server-config`` 既无 ``--input`` 也无 ``--scenario-id`` 应失败。"""
    from typer.testing import CliRunner
    from seahorse.__main__ import app

    runner = CliRunner()
    result = runner.invoke(
        app,
        ["export-server-config", "--output-dir", "/tmp"],
    )
    assert result.exit_code != 0


# ── CLI 子命令行为 ────────────────────────────────────────────────────────────────


def test_cli_generate_scenario_writes_bundle_and_jsonl() -> None:
    """``generate-scenario`` 默认同时输出 bundle JSON 和 JSONL 时序。"""
    from typer.testing import CliRunner
    from seahorse.__main__ import app

    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        result = runner.invoke(
            app,
            [
                "generate-scenario",
                "--scenario-id", "cli_full",
                "--seed", "42",
                "--asset-count", "1",
                "--duration", "0.5",
                "--output-dir", tmpdir,
                "--start-time", "2024-01-01T00:00:00+00:00",
            ],
        )
        assert result.exit_code == 0, result.output
        assert (Path(tmpdir) / "cli_full_bundle.json").exists()
        assert (Path(tmpdir) / "cli_full_timeseries.jsonl").exists()


def test_cli_generate_scenario_no_jsonl_skips_jsonl() -> None:
    """``--no-jsonl`` 时不应生成 JSONL 时序文件。"""
    from typer.testing import CliRunner
    from seahorse.__main__ import app

    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        result = runner.invoke(
            app,
            [
                "generate-scenario",
                "--scenario-id", "cli_no_ts",
                "--seed", "42",
                "--asset-count", "1",
                "--duration", "0.5",
                "--output-dir", tmpdir,
                "--start-time", "2024-01-01T00:00:00+00:00",
                "--no-jsonl",
            ],
        )
        assert result.exit_code == 0, result.output
        assert (Path(tmpdir) / "cli_no_ts_bundle.json").exists()
        assert not (Path(tmpdir) / "cli_no_ts_timeseries.jsonl").exists()


def test_cli_export_bundle_roundtrip() -> None:
    """``export-bundle`` 加载并重新导出 bundle JSON。"""
    from typer.testing import CliRunner
    from seahorse.__main__ import app

    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        gen = runner.invoke(
            app,
            [
                "generate-scenario",
                "--scenario-id", "cli_eb",
                "--seed", "42",
                "--asset-count", "1",
                "--duration", "0.5",
                "--output-dir", tmpdir,
                "--start-time", "2024-01-01T00:00:00+00:00",
            ],
        )
        assert gen.exit_code == 0, gen.output

        bundle_path = Path(tmpdir) / "cli_eb_bundle.json"
        export = runner.invoke(
            app,
            ["export-bundle", "--input", str(bundle_path), "--output-dir", tmpdir],
        )
        assert export.exit_code == 0, export.output

        re_exported = Path(tmpdir) / "cli_eb_bundle.json"
        assert re_exported.exists()
        parsed = json.loads(re_exported.read_text(encoding="utf-8"))
        assert parsed["scenario_id"] == "cli_eb"


def test_cli_export_bundle_fails_on_invalid_bundle() -> None:
    """``export-bundle`` 对校验失败的 bundle 应返回非零。"""
    from typer.testing import CliRunner
    from seahorse.__main__ import app

    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        bad = Path(tmpdir) / "invalid_bundle.json"
        bad.write_text(
            json.dumps({"schema_version": "", "scenario_id": ""}),
            encoding="utf-8",
        )
        result = runner.invoke(
            app,
            ["export-bundle", "--input", str(bad), "--output-dir", tmpdir],
        )
        assert result.exit_code != 0


def test_cli_validate_bundle_reports_errors() -> None:
    """``validate-bundle`` 对错误 bundle 应输出 ERROR 并返回非零。"""
    from typer.testing import CliRunner
    from seahorse.__main__ import app

    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        bad = Path(tmpdir) / "invalid.json"
        bad.write_text(json.dumps({"scenario_id": ""}), encoding="utf-8")
        result = runner.invoke(app, ["validate-bundle", "--input", str(bad)])
        assert result.exit_code != 0
        assert "ERROR" in result.output


def test_cli_export_server_config_from_bundle_input_mode() -> None:
    """``export-server-config --input`` 模式：从 bundle 提取 ServerConfig。"""
    from typer.testing import CliRunner
    from seahorse.__main__ import app

    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        gen = runner.invoke(
            app,
            [
                "generate-scenario",
                "--scenario-id", "cli_srv_in",
                "--seed", "42",
                "--asset-count", "1",
                "--duration", "0.5",
                "--output-dir", tmpdir,
                "--start-time", "2024-01-01T00:00:00+00:00",
            ],
        )
        assert gen.exit_code == 0, gen.output
        bundle_path = Path(tmpdir) / "cli_srv_in_bundle.json"

        exp = runner.invoke(
            app,
            [
                "export-server-config",
                "--input", str(bundle_path),
                "--output-dir", tmpdir,
            ],
        )
        assert exp.exit_code == 0, exp.output

        sp_path = Path(tmpdir) / "cli_srv_in_server_config.json"
        assert sp_path.exists()
        payload = json.loads(sp_path.read_text(encoding="utf-8"))
        assert payload["scenario_id"] == "cli_srv_in"
        assert payload["payload_hash"] != ""


def test_cli_export_server_config_direct_generate_mode() -> None:
    """``export-server-config --scenario-id`` 模式：直接生成 ServerConfig。"""
    from typer.testing import CliRunner
    from seahorse.__main__ import app

    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        result = runner.invoke(
            app,
            [
                "export-server-config",
                "--scenario-id", "cli_srv_direct",
                "--seed", "77",
                "--asset-count", "1",
                "--protocol-targets", "OPC_UA",
                "--output-dir", tmpdir,
            ],
        )
        assert result.exit_code == 0, result.output

        sp_path = Path(tmpdir) / "cli_srv_direct_server_config.json"
        assert sp_path.exists()
        payload = json.loads(sp_path.read_text(encoding="utf-8"))
        assert payload["scenario_id"] == "cli_srv_direct"
        assert payload["payload_hash"] != ""


def test_cli_protocol_targets_accepts_comma_separated() -> None:
    """``--protocol-targets`` 应接受逗号分隔的多协议输入。"""
    from typer.testing import CliRunner
    from seahorse.__main__ import app

    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        result = runner.invoke(
            app,
            [
                "export-server-config",
                "--scenario-id", "cli_multi_proto",
                "--seed", "77",
                "--asset-count", "1",
                "--protocol-targets", "OPC_UA,MODBUS_TCP",
                "--output-dir", tmpdir,
            ],
        )
        assert result.exit_code == 0, result.output
        sp_path = Path(tmpdir) / "cli_multi_proto_server_config.json"
        payload = json.loads(sp_path.read_text(encoding="utf-8"))
        # 应生成两个 endpoint（每协议一个）
        assert len(payload["servers"][0]["endpoints"]) == 2