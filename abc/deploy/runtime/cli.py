
from typing import Annotated
from typer import Typer, Option
import asyncio

from deploy.bootstrap.runtime import RuntimeMode, runtime_factory

main = Typer()

@main.command('run')
def run(
    mode: Annotated[RuntimeMode, Option('--mode', help="运行模式")] = RuntimeMode.STANDALONE,
    slave: Annotated[bool, Option('--slave', help="只在主从模式下使用，默认是master")] = False,
) -> None:
    """运行时部署模式的入口命令."""
    runtime = runtime_factory(mode, slave=slave)
    asyncio.run(runtime.run())