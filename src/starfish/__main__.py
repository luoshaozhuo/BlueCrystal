"""starfish CLI 入口 —— 通过高层 API 启动 Starfish simulator。

使用方式：

```text
python -m starfish run <server_config.json>
python -m starfish run --input <server_config.json> --duration 30
```

模块职责：
- 只暴露 `run` 子命令，旧诊断入口不再作为隐藏命令保留。
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
- 协议 frame 编解码实现（由 `starfish.domain.protocols` 负责）。
"""

from __future__ import annotations

import sys
import threading
from pathlib import Path
from typing import Annotated, Any

import typer
import typer.main
from click.exceptions import Exit as ClickExit
from click.exceptions import UsageError as ClickUsageError
from typer._click.exceptions import UsageError as TyperUsageError

from starfish.api import StarfishServerManager
from starfish.application import ServerManagerBuildError


_PROG_NAME = "starfish"

app = typer.Typer(
    name=_PROG_NAME,
    help="Starfish 多协议 simulator 运行 CLI",
    no_args_is_help=False,
    rich_markup_mode="rich",
)


def _open_manager_or_print_error(config_path: Path) -> StarfishServerManager | None:
    """加载配置并创建统一 server manager 对象。"""
    if config_path is None:
        print("错误：缺少 server 配置 JSON 文件路径", file=sys.stderr)
        return None
    try:
        return StarfishServerManager(config_path)
    except FileNotFoundError:
        print(f"错误：文件不存在: {config_path}", file=sys.stderr)
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
    except ClickExit as exc:
        if exc.exit_code == 0:
            return 0
        raise SystemExit(exc.exit_code) from None
    except (ClickUsageError, TyperUsageError) as exc:
        print(exc.format_message(), file=sys.stderr)
        raise SystemExit(exc.exit_code) from None

    return 0 if rc is None else rc


@app.callback()
def cli(ctx: typer.Context) -> None:
    """保持 `python -m starfish` 的显式子命令解析边界。

    Args:
        ctx: Typer/Click 当前解析上下文。

    Raises:
        typer.Exit: 未提供子命令时以解析错误退出，避免误触发 manager 加载。
    """
    if ctx.invoked_subcommand is None:
        print(ctx.get_help(), file=sys.stderr)
        raise typer.Exit(2)


@app.command("run")
def run_command(
    config_path: Annotated[
        Path | None,
        typer.Argument(help="server 配置 JSON 文件路径"),
    ] = None,
    input_path: Annotated[
        Path | None,
        typer.Option("--input", help="server 配置 JSON 文件路径（兼容旧用法）"),
    ] = None,
    duration: Annotated[
        float | None,
        typer.Option("--duration", min=0.0, help="运行秒数；不传则持续运行直到 Ctrl+C"),
    ] = None,
) -> int:
    """启动全部可用 simulator facade 并保持运行。

    Args:
        config_path: 推荐的位置参数配置路径。
        input_path: 兼容既有 `--input` run 用法的配置路径。
        duration: 可选运行时长；None 表示持续运行直到收到中断。

    Returns:
        Typer 使用的进程退出码。
    """
    selected_path = input_path or config_path
    manager = _open_manager_or_print_error(selected_path)
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
    sys.exit(main(sys.argv[1:]))
