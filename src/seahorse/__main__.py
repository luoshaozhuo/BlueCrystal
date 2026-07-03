"""Seahorse CLI 薄输入入口（Typer）。

``__main__.py`` 是 :mod:`seahorse` 的输入侧 Typer CLI 薄入口，严格遵守
``docs/clean_architecture.md`` v4.2 蓝图：

1. CLI 统一使用 Typer，禁止使用其它 CLI 框架；
2. CLI 入口固定在 ``__main__.py``；
3. ``__main__.py`` 只能调用 :mod:`seahorse.api` 的稳定 facade
   （:class:`seahorse.api.seahorse_facade.SeahorseFacade`），不得直接
   import :mod:`seahorse.domain`、``seahorse.application``、
   :mod:`seahorse.adapters` 或 :mod:`seahorse.infrastructure`；
4. ``__main__.py`` 不构造 backend / scheduler / repository / writer /
   ORM session，也不直接构造 :class:`ScenarioConfig`；
5. CLI 参数以 primitives / Path / list / dict 形式传给 facade，由
   facade 在内部装配 domain model。

子命令列表：

- ``generate-scenario`` —— 生成场景并保存 bundle JSON（默认同步生成 JSONL 时序）；
- ``export-bundle`` —— 重新加载并导出已有 bundle JSON；
- ``validate-bundle`` —— 校验 bundle JSON 的完整性与一致性；
- ``export-server-config`` —— 从已有 bundle 提取或直接生成 ServerConfig
  并导出为 Starfish handoff JSON。

异常处理策略：CLI 不向终端直接抛出底层异常。所有错误通过
:func:`typer.echo` / :func:`typer.secho` 输出，并由 :func:`typer.Exit`
以非零退出码收口；最终由 ``sys.exit(main())`` 将退出码传递给 OS。
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import typer

from seahorse.api.seahorse_facade import SeahorseFacade


# Typer app 是 v4.2 蓝图允许的薄入口对象；它只承载命令注册、参数声明
# 和退出码；不允许在 app 上挂业务规则。
app = typer.Typer(
    name="seahorse",
    help="Seahorse 样例场站生成器 CLI —— 场景生成、bundle 导出与校验。",
    no_args_is_help=True,
    add_completion=False,
)


def _build_facade() -> SeahorseFacade:
    """构造 CLI 使用的 :class:`SeahorseFacade` 实例。

    Returns:
        不连接外部系统的默认 :class:`SeahorseFacade`。
    """
    return SeahorseFacade()


def _echo_error(message: str) -> None:
    """统一 CLI 错误输出样式（红色）。

    Args:
        message: 待输出的错误文本。
    """
    typer.secho(message, fg=typer.colors.RED, err=True)


def _echo_success(message: str) -> None:
    """统一 CLI 成功输出样式（绿色）。

    Args:
        message: 待输出的成功文本。
    """
    typer.secho(message, fg=typer.colors.GREEN)


def _echo_info(message: str) -> None:
    """统一 CLI 普通输出样式。

    Args:
        message: 待输出的普通文本。
    """
    typer.echo(message)


def _normalize_protocol_targets(values: list[str]) -> list[str]:
    """将 Typer 收到的 ``--protocol-targets`` 元素归一化为协议列表。

    Typer 的 ``list[str]`` 选项默认按出现次数接收多个值；同时为兼容
    旧 CLI 的多 token 用法，CLI 也接受以逗号分隔的单个字符串
    （如 ``"OPC_UA,MODBUS_TCP"``）。该 helper 展开逗号并去重，保留
    首次出现的顺序。

    Args:
        values: Typer 传入的原始字符串列表。

    Returns:
        归一化后的协议列表。
    """
    result: list[str] = []
    for value in values:
        for token in value.split(","):
            token = token.strip()
            if token and token not in result:
                result.append(token)
    return result


@app.command("generate-scenario")
def generate_scenario(
    scenario_id: str = typer.Option(..., "--scenario-id", help="场景唯一标识（必填）。"),
    name: str = typer.Option("", "--name", help="场景可读名称。"),
    seed: int = typer.Option(42, "--seed", help="确定性伪随机种子（默认 42）。"),
    asset_count: int = typer.Option(1, "--asset-count", help="要生成的资产数量（默认 1）。"),
    duration: float = typer.Option(3600.0, "--duration", help="模拟总时长，单位秒（默认 3600.0）。"),
    sample_interval: int = typer.Option(
        100, "--sample-interval", help="信号采样间隔，单位毫秒（默认 100）。"
    ),
    protocol_targets: list[str] = typer.Option(
        ["OPC_UA"],
        "--protocol-targets",
        help="目标协议列表（默认 OPC_UA）。",
    ),
    output_dir: Path = typer.Option(Path("."), "--output-dir", help="输出目录路径（默认当前目录）。"),
    no_jsonl: bool = typer.Option(False, "--no-jsonl", help="禁用 JSONL 时序导出。"),
    start_time: str | None = typer.Option(
        None,
        "--start-time",
        help="模拟起始时间，ISO 8601 格式（如 2024-01-01T00:00:00+0000），默认 UTC 当前时间。"
        "注意：使用默认值会导致校验和不可重现。",
    ),
) -> None:
    """根据参数生成场景并保存 bundle JSON 文件。"""
    parsed_start_time: datetime | None = None
    if start_time is not None:
        try:
            parsed_start_time = datetime.fromisoformat(start_time)
        except ValueError as exc:
            _echo_error(f"错误：start_time 格式无效: {exc}")
            raise typer.Exit(code=1) from exc

    facade = _build_facade()
    bundle = facade.generate_bundle_from_cli_params(
        scenario_id=scenario_id,
        name=name,
        deterministic_seed=seed,
        start_time=parsed_start_time,
        duration_seconds=duration,
        sample_interval_ms=sample_interval,
        asset_count=asset_count,
        protocol_targets=_normalize_protocol_targets(protocol_targets),
    )

    bundle_path = facade.save_bundle(bundle, output_dir)
    _echo_success(f"bundle JSON 已保存: {bundle_path}")

    if not no_jsonl:
        signals = bundle.generated_timeseries_sample
        ts_path = facade.save_timeseries(
            signals,
            output_dir,
            scenario_id=scenario_id,
        )
        _echo_success(f"JSONL 时序已保存: {ts_path}")

    stats = facade.generator_metadata_stats(bundle)
    _echo_info(f"生成摘要: {stats}")
    _echo_info(f"校验和: {bundle.checksum[:16]}...")

    if start_time is None:
        _echo_error(
            "注意：未指定 --start-time，校验和在下一次运行时可能不同。"
        )


@app.command("export-bundle")
def export_bundle(
    input_path: Path = typer.Option(..., "--input", help="输入的 bundle JSON 文件路径。"),
    output_dir: Path = typer.Option(Path("."), "--output-dir", help="输出目录路径（默认当前目录）。"),
) -> None:
    """加载已有 bundle JSON 并重新导出。"""
    if not input_path.is_file():
        _echo_error(f"错误：输入文件不存在: {input_path}")
        raise typer.Exit(code=1)

    try:
        raw = json.loads(input_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        _echo_error(f"错误：JSON 解析失败: {exc}")
        raise typer.Exit(code=1) from exc

    facade = _build_facade()
    result = facade.validate_bundle_dict(raw)
    if not result.is_valid:
        _echo_error("校验失败:")
        for err in result.errors:
            _echo_error(f"  [ERROR] {err}")
        for warn in result.warnings:
            _echo_error(f"  [WARN]  {warn}")
        raise typer.Exit(code=1)

    _echo_success("校验通过")
    for passed in result.passed_checks:
        _echo_success(f"  [PASS] {passed}")

    output_dir.mkdir(parents=True, exist_ok=True)
    scenario_id = raw.get("scenario_id", "exported")
    output_path = output_dir / f"{scenario_id}_bundle.json"
    output_path.write_text(
        json.dumps(raw, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    _echo_success(f"bundle 已重新导出: {output_path}")


@app.command("validate-bundle")
def validate_bundle(
    input_path: Path = typer.Option(..., "--input", help="输入的 bundle JSON 文件路径。"),
) -> None:
    """校验 bundle JSON 文件的完整性和一致性。"""
    if not input_path.is_file():
        _echo_error(f"错误：输入文件不存在: {input_path}")
        raise typer.Exit(code=1)

    try:
        raw = json.loads(input_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        _echo_error(f"错误：JSON 解析失败: {exc}")
        raise typer.Exit(code=1) from exc

    facade = _build_facade()
    result = facade.validate_bundle_dict(raw)

    if result.errors:
        _echo_error("校验错误:")
        for err in result.errors:
            _echo_error(f"  [ERROR] {err}")

    if result.warnings:
        _echo_error("校验警告:")
        for warn in result.warnings:
            _echo_error(f"  [WARN]  {warn}")

    if result.passed_checks:
        _echo_success("通过项:")
        for passed in result.passed_checks:
            _echo_success(f"  [PASS] {passed}")

    if result.is_valid:
        _echo_success("\n校验结果: 通过")
        return

    _echo_error(f"\n校验结果: 失败（{len(result.errors)} 个错误）")
    raise typer.Exit(code=1)


@app.command("export-server-config")
def export_server_config(
    input_path: Path | None = typer.Option(
        None,
        "--input",
        help="输入的 bundle JSON 文件路径（从已有 bundle 提取模式）。",
    ),
    scenario_id: str | None = typer.Option(
        None,
        "--scenario-id",
        help="场景唯一标识（直接生成模式）。",
    ),
    seed: int = typer.Option(42, "--seed", help="确定性伪随机种子（直接生成模式，默认 42）。"),
    asset_count: int = typer.Option(1, "--asset-count", help="资产数量（直接生成模式，默认 1）。"),
    protocol_targets: list[str] = typer.Option(
        ["OPC_UA"],
        "--protocol-targets",
        help="目标协议列表（直接生成模式，默认 OPC_UA）。",
    ),
    output_dir: Path = typer.Option(Path("."), "--output-dir", help="输出目录路径（默认当前目录）。"),
) -> None:
    """导出 ServerConfig 为 Starfish handoff JSON 文件。

    支持两种模式：
    1. 从已有 bundle JSON 文件提取 ServerConfig 并导出（使用 ``--input``）。
    2. 直接根据参数生成 ServerConfig 并导出（使用 ``--scenario-id``）。
    """
    facade = _build_facade()

    if input_path is not None:
        if not input_path.is_file():
            _echo_error(f"错误：输入文件不存在: {input_path}")
            raise typer.Exit(code=1)
        server_config = facade.load_server_config_from_bundle_json(input_path)
    elif scenario_id is not None:
        server_config = facade.generate_minimal_server_config_from_cli_params(
            scenario_id=scenario_id,
            deterministic_seed=seed,
            asset_count=asset_count,
            protocol_targets=_normalize_protocol_targets(protocol_targets),
        )
    else:
        _echo_error("错误：必须指定 --input（从 bundle 提取）或 --scenario-id（直接生成）。")
        raise typer.Exit(code=1)

    result = facade.validate_server_config(server_config)
    if result.errors:
        _echo_error("ServerConfig 校验错误:")
        for err in result.errors:
            _echo_error(f"  [ERROR] {err}")
    if result.warnings:
        _echo_error("ServerConfig 校验警告:")
        for warn in result.warnings:
            _echo_error(f"  [WARN]  {warn}")

    saved_path = facade.save_server_config(server_config, output_dir)
    _echo_success(f"ServerConfig handoff JSON 已保存: {saved_path}")

    if result.is_valid:
        _echo_success("ServerConfig 校验通过")
        return

    _echo_error(
        f"ServerConfig 校验未通过（{len(result.errors)} 个错误），但文件已导出"
    )
    raise typer.Exit(code=1)


def main(argv: list[str] | None = None) -> int:
    """Seahorse CLI 顶层入口。

    该函数保留 ``main(argv) -> int`` 签名供现有测试与脚本使用；
    ``argv`` 为 None 时使用 ``sys.argv[1:]``。

    调用 :meth:`app` 时显式传入 ``standalone_mode=False`，避免 Typer
    在子命令正常返回后调用 ``sys.exit(0)``，从而允许 :func:`main`
    将退出码以 int 形式返回给调用方；同时 :class:`typer.Exit` 抛
    出的 :class:`SystemExit` 仍按 Typer 语义自然向上传播（例如
    ``--help`` / 解析错误），不会被本函数吞掉。

    Args:
        argv: 命令行参数列表；None 时使用 ``sys.argv[1:]``。

    Returns:
        进程退出码，0 表示子命令正常完成。
    """
    if argv is None:
        app(standalone_mode=False)
    else:
        app(args=list(argv), standalone_mode=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())


__all__ = ["app", "main"]