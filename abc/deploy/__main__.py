"""提供cli命令行入口"""

from __future__ import annotations

import typer

from deploy.runtime.cli import main as runtime_main

main = typer.Typer(
    name="runtime_deployment_mode",
    help="BlueCrystal 部署与运行时管理.",
)

main.add_typer(runtime_main, name="runtime", help="运行时部署模式的入口命令.")

@main.callback()
def main_callback() -> None:
    """保留运行时部署模式的模块执行入口；当前骨架不提供启动行为."""
    pass

if __name__ == "__main__":
    main()