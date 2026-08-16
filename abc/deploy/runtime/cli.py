
from typing import Annotated
from typer import Typer, Option
import asyncio

from deploy.bootstrap.runtime import RuntimeMode, runtime_factory

main = Typer()

@main.command('run')
def run(
    host: Annotated[str, Option('--host', help="主机地址")] = "0.0.0.0",
    port: Annotated[int, Option('--port', help="端口号")] = 8000,
    mode: Annotated[RuntimeMode, Option('--mode', help="运行模式")] = RuntimeMode.STANDALONE,
) -> None:
    """运行时部署模式的入口命令."""
    runtime = runtime_factory(host, port, mode)
    asyncio.run(runtime.run())