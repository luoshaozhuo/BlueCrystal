"""starfish CLI 入口 —— 通过高层 API 校验 server 配置并管理 servers。

使用方式：

```text
python -m starfish validate-config --input <server_config.json>
python -m starfish describe --input <server_config.json>
python -m starfish health --input <server_config.json> --start
python -m starfish read --input <server_config.json>
python -m starfish run --input <server_config.json> --duration 30
```

模块职责：
- 暴露 5 个子命令：validate-config / describe / health / read / run。
- 统一经 `starfish.api` 进入 application usecase，而不是直接耦合 loader/registry。
- 提供独立可单元测试的 `main(argv) -> int` 入口，封装 typer 的
  `SystemExit` 行为，错误路径以返回值表达退出码。

定位说明：
- 这是面向单份 server 配置的 server manager CLI。
- 测试逻辑应放在 `tests/` 中，由 pytest 驱动。
- 本 CLI 不再承担 smoke/probe/profile/capacity 这类测试入口职责。

不负责：
- 替代 pytest。
- 生产数据写入、落库或生产链路编排。
- 协议 frame 编解码实现（由 `starfish.protocols` 负责）。
"""

from __future__ import annotations

import sys
import threading
from pathlib import Path
from typing import Annotated, Any

import typer
import typer.main
from click.exceptions import UsageError

from starfish.api import StarfishServerManager, load_config, open_manager
from starfish.application import ServerManagerBuildError


_PROG_NAME = "starfish"

app = typer.Typer(
    name=_PROG_NAME,
    help="Starfish 多协议 simulator 运行 CLI",
    rich_markup_mode="rich",
)


def _load_config_or_exit(input_path: Path) -> tuple[Any | None, Any]:
    """加载并校验 server 配置 JSON。"""
    try:
        result = load_config(input_path)
    except FileNotFoundError:
        print(f"错误：文件不存在: {input_path}", file=sys.stderr)
        return None, None
    except Exception as exc:
        print(f"错误：加载失败: {exc}", file=sys.stderr)
        return None, None

    validation = result.validation
    if not validation.is_valid:
        print(f"错误：校验失败 ({len(validation.errors)} 个错误)")
        return None, validation

    config = result.config
    if config is None:
        print("错误：config 为 None")
        return None, validation
    return config, validation


def _print_validation(validation: Any) -> None:
    """打印 validate-config 校验明细。"""
    if validation.errors:
        print(f"\n校验错误 ({len(validation.errors)}):")
        for err in validation.errors:
            print(f"  [ERROR] {err}")
    if validation.warnings:
        print(f"\n校验警告 ({len(validation.warnings)}):")
        for warn in validation.warnings:
            print(f"  [WARN]  {warn}")
    if validation.passed_checks:
        print(f"\n通过项 ({len(validation.passed_checks)}):")
        for passed in validation.passed_checks:
            print(f"  [PASS] {passed}")


def _open_manager_or_print_error(input_path: Path) -> StarfishServerManager | None:
    """加载配置并创建统一 server manager 对象。"""
    try:
        return open_manager(input_path)
    except FileNotFoundError:
        print(f"错误：文件不存在: {input_path}", file=sys.stderr)
        return None
    except ServerManagerBuildError as exc:
        print(f"错误：{exc}")
        validation = exc.validation
        if validation is not None and validation.errors:
            for err in validation.errors:
                print(f"  [ERROR] {err}")
        return None
    except Exception as exc:
        print(f"错误：加载失败: {exc}", file=sys.stderr)
        return None


def _print_config_summary(config: Any) -> None:
    """打印 server 配置摘要。"""
    print(f"scenario_id: {config.scenario_id}")
    config_name = getattr(config, "config_name", getattr(config, "server_name", ""))
    servers = getattr(config, "servers", None)
    if servers is None:
        endpoint_count = len(getattr(config, "endpoints", []))
        point_count = len(getattr(config, "points", []))
        server_count = 1
    else:
        endpoint_count = sum(len(server.endpoints) for server in servers)
        point_count = sum(len(server.points) for server in servers)
        server_count = len(servers)
    print(f"config_name: {config_name}")
    print(f"servers:     {server_count}")
    print(f"endpoints:   {endpoint_count}")
    print(f"points:      {point_count}")
    print(f"synthetic:   {config.synthetic}")


def _print_registry_summary(config: Any, registry: Any) -> None:
    """打印 facade 装配结果摘要。"""
    print("Facade 装配结果:")
    for entry in registry.entries:
        endpoint = entry.endpoint
        server = entry.server
        bind_host = endpoint.bind_host or endpoint.host
        bind_port = endpoint.bind_port or endpoint.port
        print(f"  server:     {server.server_id or server.server_name}")
        print(f"  endpoint:   {endpoint.endpoint_id}")
        print(f"    protocol: {endpoint.protocol}")
        print(f"    bind:     {bind_host}:{bind_port}")
        print(f"    mode:     {entry.mode}")
        print(f"    available:{entry.available}")
        if entry.reason:
            print(f"    reason:   {entry.reason}")
        if entry.driver is not None:
            health = entry.driver.health()
            print(f"    points:   {health.get('point_count', len(server.points))}")
            print(f"    caps:     {health.get('capabilities', server.capabilities)}")


def main(argv: list[str]) -> int:
    """Starfish CLI 统一入口。"""
    try:
        rc = typer.main.get_group(app).main(
            args=argv,
            prog_name=_PROG_NAME,
            standalone_mode=False,
        )
    except UsageError as exc:
        raise SystemExit(exc.exit_code) from None

    return 0 if rc is None else rc


@app.command("validate-config")
def validate_config(
    input_path: Annotated[
        Path,
        typer.Option("--input", help="server 配置 JSON 文件路径"),
    ],
) -> int:
    """加载并校验 Seahorse 导出的 server config JSON 文件。"""
    config, validation = _load_config_or_exit(input_path)
    if config is None:
        if validation is not None and getattr(validation, "errors", None):
            for err in validation.errors:
                print(f"  [ERROR] {err}")
        return 1

    _print_validation(validation)
    print()
    _print_config_summary(config)
    return 0


@app.command("describe")
def describe_config(
    input_path: Annotated[
        Path,
        typer.Option("--input", help="server 配置 JSON 文件路径"),
    ],
) -> int:
    """展示 server 配置摘要和 facade 装配结果。"""
    manager = _open_manager_or_print_error(input_path)
    if manager is None:
        return 1

    _print_config_summary(manager.config)
    print()
    _print_registry_summary(manager.config, manager.registry)
    return 0


@app.command("health")
def health_command(
    input_path: Annotated[
        Path,
        typer.Option("--input", help="server 配置 JSON 文件路径"),
    ],
    start_first: Annotated[
        bool,
        typer.Option("--start/--no-start", help="先启动 facade 再查询 health"),
    ] = False,
) -> int:
    """查看各 endpoint 当前 health。"""
    manager = _open_manager_or_print_error(input_path)
    if manager is None:
        return 1

    all_ok = True
    if start_first:
        try:
            manager.start()
        except Exception as exc:
            print(f"[start] 失败: {exc}", file=sys.stderr)
            all_ok = False

    for entry in manager.registry.entries:
        print(f"\n--- health endpoint={entry.endpoint.endpoint_id} ---")
        print(f"  protocol:  {entry.endpoint.protocol}")
        print(f"  mode:      {entry.mode}")
        print(f"  available: {entry.available}")
        if not entry.available or entry.driver is None:
            print("  status:    unavailable")
            print(f"  reason:    {entry.reason}")
            continue
        try:
            health = manager.health(entry.endpoint.endpoint_id)
            for key, value in health.items():
                print(f"  {key}: {value}")
        except Exception as exc:
            print(f"  错误: {exc}", file=sys.stderr)
            all_ok = False

    if start_first:
        manager.stop()
    return 0 if all_ok else 1


@app.command("read")
def read_command(
    input_path: Annotated[
        Path,
        typer.Option("--input", help="server 配置 JSON 文件路径"),
    ],
    point_ids: Annotated[
        list[str],
        typer.Option("--point", help="只读取指定 point_id，可重复传入"),
    ] = [],
) -> int:
    """启动 simulator，读取当前点位值并停止。"""
    manager = _open_manager_or_print_error(input_path)
    if manager is None:
        return 1

    try:
        manager.start()
    except Exception as exc:
        print(f"错误：启动 simulator 失败: {exc}", file=sys.stderr)
        return 1

    available_entries = [
        entry for entry in manager.registry.entries
        if entry.available and entry.driver is not None
    ]
    if not available_entries:
        print("错误：没有可启动的 simulator endpoint", file=sys.stderr)
        return 1

    all_ok = True
    selected_points = point_ids or None
    try:
        values_by_endpoint = manager.read(selected_points)
    except Exception as exc:
        print(f"错误：读取失败: {exc}", file=sys.stderr)
        manager.stop()
        return 1

    for entry in available_entries:
        print(f"\n--- read endpoint={entry.endpoint.endpoint_id} ---")
        print(f"  protocol: {entry.endpoint.protocol}")
        print(f"  mode:     {entry.mode}")
        try:
            values = values_by_endpoint.get(entry.endpoint.endpoint_id, {})
            print(f"  point_count: {len(values)}")
            for point_id, value in values.items():
                print(f"  {point_id}={value}")
        except Exception as exc:
            print(f"  错误: {exc}", file=sys.stderr)
            all_ok = False

    manager.stop()
    return 0 if all_ok else 1


@app.command("run")
def run_command(
    input_path: Annotated[
        Path,
        typer.Option("--input", help="server 配置 JSON 文件路径"),
    ],
    duration: Annotated[
        float | None,
        typer.Option("--duration", min=0.0, help="运行秒数；不传则持续运行直到 Ctrl+C"),
    ] = None,
) -> int:
    """启动全部可用 simulator facade 并保持运行。"""
    manager = _open_manager_or_print_error(input_path)
    if manager is None:
        return 1

    _print_config_summary(manager.config)
    print()
    _print_registry_summary(manager.config, manager.registry)

    try:
        manager.start()
    except Exception as exc:
        print(f"错误：启动 simulator 失败: {exc}", file=sys.stderr)
        return 1

    started_count = len(
        [
            entry for entry in manager.registry.entries
            if entry.available and entry.driver is not None
        ]
    )
    print(f"\n已启动 {started_count} 个 simulator endpoint。")
    print("按 Ctrl+C 停止。" if duration is None else f"将运行 {duration:.2f} 秒后自动停止。")

    stop_event = threading.Event()
    try:
        stop_event.wait(duration)
    except KeyboardInterrupt:
        print("\n收到中断信号，正在停止 simulator...")
    finally:
        manager.stop()

    print("Simulator 已停止。")
    return 0


if __name__ == "__main__":
    app()
