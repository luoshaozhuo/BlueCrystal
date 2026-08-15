"""starfish CLI 入口 —— 通过 Whale DB view 启动 Starfish simulator。

安装：

```bash
conda activate <bluecrystal_env>
cd <bluecrystal_project_root>
pip install -e . ".[iec104]"
```

使用方式：

```text
starfish run -id 1001
starfish run -a --duration 30
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
- 持久化模拟值、生产数据写入、落库或生产链路编排。
- IEC104 frame 编解码实现（由延迟加载的 c104 runtime 负责）。
"""

from __future__ import annotations

import os
import sys
import threading
from typing import Annotated

import typer
import typer.main
from click.exceptions import UsageError as ClickUsageError
from typer._click.exceptions import UsageError as TyperUsageError

from pacific.starfish.composition import build_server_manager_from_db
from pacific.starfish.core import StarfishServerManager
from pacific.starfish.errors import DbViewLoadError

_PROG_NAME = "starfish"

app = typer.Typer(
    name=_PROG_NAME,
    help="Starfish 多协议 simulator 运行 CLI",
    no_args_is_help=True,
    rich_markup_mode="rich",
)


def _open_manager_or_print_error(
    *,
    connection_ids:str | None,
    load_all: bool,
) -> StarfishServerManager | None:
    """从 DB view 创建 simulator manager，并将加载错误转为 CLI 输出。"""
    db_url = os.environ.get("WHALE_DB_URL", "").strip()
    if not db_url:
        print("错误：缺少环境变量 WHALE_DB_URL", file=sys.stderr)
        return None
    try:
        return build_server_manager_from_db(
            None
            if load_all
            else ([int(cid) for cid in connection_ids.split(",")] if connection_ids is not None else []),
        )
    except DbViewLoadError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return None
    except Exception as exc:
        print(f"错误：加载 simulator 配置失败: {exc}", file=sys.stderr)
        return None

def main(argv: list[str]) -> int:
    """Starfish CLI 统一入口。"""
    try:
        rc = typer.main.get_group(app).main(
            args=argv,
            prog_name=_PROG_NAME,
            standalone_mode=False,
        )
    except (ClickUsageError, TyperUsageError) as exc:
        print(exc.format_message(), file=sys.stderr)
        raise SystemExit(exc.exit_code) from None

    return 0 if rc is None else rc


@app.callback()
def cli(ctx: typer.Context) -> None:
    """Starfish CLI 根命令组。"""


@app.command("run")
def run_command(
    connection_ids: Annotated[
        int | None,
        typer.Option(
            "-id",
            "--connection-id",
            help="connection_id，多个 ID 使用逗号分隔，例如：-id 1001,1002,1003",
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
    if (connection_ids is None) == (not load_all):
        print("错误：必须且只能提供 -id <connection_id> 或 -a", file=sys.stderr)
        return 1

    manager = _open_manager_or_print_error(
        connection_ids=connection_ids,
        load_all=load_all,
    )
    if manager is None:
        return 1

    try:
        manager.start()
    except Exception as exc:
        print(f"错误：启动 simulator 失败: {exc}", file=sys.stderr)
        return 1

    print(manager.status())
    print(
        "按 Ctrl+C 停止。"
        if duration is None
        else f"将运行 {duration:.2f} 秒后自动停止。"
    )

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
    # 支持通过 `python -m starfish ...` 启动 CLI。
    # `starfish run ...` 由 pyproject.toml 注册的 console script 直接调用 app。
    sys.exit(main(sys.argv[1:]))
