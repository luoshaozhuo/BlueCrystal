"""starfish CLI 入口 —— 通过 Whale DB view 启动 Starfish simulator。

使用方式：

```text
python -m starfish run -id 1001
python -m starfish run -a --duration 30
```

模块职责：
- 只暴露 `run` 子命令，旧诊断入口不再作为隐藏命令保留；
- 从 `WHALE_DB_URL` 指向的数据库执行视图加载 simulator 配置；
- 统一经 composition root 装配 core manager，不直接耦合 loader 或协议 worker。
- 提供独立可单元测试的 `main(argv) -> int` 入口，封装 typer 的
  `SystemExit` 行为，错误路径以返回值表达退出码。

定位说明：
- 这是面向 simulator 生命周期的 server manager CLI。
- 测试逻辑应放在 `tests/` 中，由 pytest 驱动。
- 本 CLI 不再承担 smoke/probe/profile/capacity 这类测试入口职责。

不负责：
- 替代 pytest。
- 生产数据写入、落库或生产链路编排；server 数据更新由 Seahorse 负责。
- IEC104 frame 编解码实现（由 native runner 负责）。
"""

from __future__ import annotations

import os
import sys
import threading
from typing import Annotated

import typer
import typer.main
from click.exceptions import Exit as ClickExit
from click.exceptions import UsageError as ClickUsageError
from typer._click.exceptions import UsageError as TyperUsageError

from starfish.adapters.db_views import DbViewLoadError
from starfish.composition import (
    build_server_manager_from_db,
    list_connection_ids_from_db,
)
from starfish.core import StarfishServerManager


_PROG_NAME = "starfish"

app = typer.Typer(
    name=_PROG_NAME,
    help="Starfish 多协议 simulator 运行 CLI",
    no_args_is_help=False,
    rich_markup_mode="rich",
)


def _open_manager_or_print_error(
    *,
    connection_id: int | None,
    load_all: bool,
) -> StarfishServerManager | None:
    """从 DB view 创建 simulator manager，并将加载错误转为 CLI 输出。"""
    db_url = os.environ.get("WHALE_DB_URL", "").strip()
    if not db_url:
        print("错误：缺少环境变量 WHALE_DB_URL", file=sys.stderr)
        return None
    try:
        connection_ids = (
            list_connection_ids_from_db(db_url)
            if load_all
            else ([connection_id] if connection_id is not None else [])
        )
        if not connection_ids:
            raise DbViewLoadError("vw_connection_object_full 中没有可启动的 connection")
        return build_server_manager_from_db(
            db_url,
            connection_ids,
        )
    except DbViewLoadError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return None
    except Exception as exc:
        print(f"错误：加载 simulator 配置失败: {exc}", file=sys.stderr)
        return None


def _print_manager_summary(manager: StarfishServerManager) -> None:
    """打印 manager 当前装配的 server 摘要。"""
    description = manager.describe()
    print(f"servers: {description['server_count']}")
    print("Server 装配结果:")
    for server in description["servers"]:
        print(f"  connection_id: {server['connection_id']}")
        print(f"    name:        {server['name']}")
        print(f"    protocol:    {server['protocol']}")
        print(f"    bind:        {server['bind_host']}:{server['bind_port']}")
        print(f"    points:      {server['point_count']}")
        print(f"    tasks:       {server['task_count']}")
        print(f"    caps:        {server['capabilities']}")


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


def _selected_manager_count(manager: StarfishServerManager) -> int:
    """返回当前 manager 持有的 server 数量。"""
    return manager.server_count


@app.command("run")
def run_command(
    connection_id: Annotated[
        int | None,
        typer.Option(
            "-id",
            "--connection-id",
            min=1,
            help="按 vw_connection_object_full.connection_id 启动单个simulator",
        ),
    ] = None,
    load_all: Annotated[
        bool,
        typer.Option("-a", "--all", help="启动 DB view 中所有simulator"),
    ] = False,
    duration: Annotated[
        float | None,
        typer.Option("--duration", min=0.0, help="运行秒数；不传则持续运行直到 Ctrl+C"),
    ] = None,
) -> int:
    """按 DB view 启动 simulator 并保持运行。

    Args:
        connection_id: 单个 connection_id。
        load_all: 是否启动全部 connection。
        duration: 可选运行时长；None 表示持续运行直到收到中断。

    Returns:
        Typer 使用的进程退出码。
    """
    if (connection_id is None) == (not load_all):
        print("错误：必须且只能提供 -id <connection_id> 或 -a", file=sys.stderr)
        return 1

    manager = _open_manager_or_print_error(
        connection_id=connection_id,
        load_all=load_all,
    )
    if manager is None:
        return 1

    _print_manager_summary(manager)

    try:
        manager.start()
    except Exception as exc:
        print(f"错误：启动 simulator 失败: {exc}", file=sys.stderr)
        return 1

    started_count = _selected_manager_count(manager)
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
