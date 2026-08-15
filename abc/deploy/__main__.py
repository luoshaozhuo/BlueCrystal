"""保留运行时部署模式的模块执行入口；当前骨架不提供启动行为."""

import asyncio
import typer
from typing import Annotated

from deploy.bootstrap.app import RuntimeMode, app_factory

main = typer.Typer(
    name="runtime_deployment_mode",
    help="保留运行时部署模式的模块执行入口；当前骨架不提供启动行为.",
)


@main.callback()
def main_callback() -> None:
    """保留运行时部署模式的模块执行入口；当前骨架不提供启动行为."""
    pass


@main.command('run')
def run(
    mode: Annotated[RuntimeMode, typer.Option('--mode', help="运行模式")] = RuntimeMode.STANDALONE,
    slave: Annotated[bool, typer.Option('--slave', help="只在主从模式下使用，默认是master")] = False,
) -> None:
    """运行时部署模式的入口命令."""
    app = app_factory(mode, slave=slave)
    asyncio.run(app.run())

if __name__ == "__main__":
    main()