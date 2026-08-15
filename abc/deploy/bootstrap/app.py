"""Ingest 应用装配入口."""

from __future__ import annotations
import asyncio

from enum import StrEnum

import uvicorn

from deploy.runtime.api import create_api
from deploy.runtime.scheduler import RuntimeScheduler


class RuntimeMode(StrEnum):
    """Ingest 运行模式."""

    STANDALONE = "standalone"
    ACTIVE_STANDBY = "active_standby"
    DUAL_ACTIVE_PARTITIONED = "dual_active"
    CLUSTER = "cluster"


async def execute_task(task_id: int) -> None:
    """临时任务执行入口.

    后续由正式 Worker / Task Executor 替换.
    """
    print(f"execute ingest task: {task_id}")


class StandaloneApplication:
    """Standalone Ingest 应用."""

    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 8000,
    ) -> None:
        """初始化."""
        self._scheduler = RuntimeScheduler(execute_task)
        self._api = create_api(self._scheduler)

        self._server = uvicorn.Server(
            uvicorn.Config(
                app=self._api,
                host=host,
                port=port,
                loop="asyncio",
            )
        )

    async def run(self) -> None:
        """运行应用."""
        self._scheduler.start()

        try:
            await self._server.serve()
        finally:
            self._scheduler.stop()


def app_factory(mode: RuntimeMode) -> StandaloneApplication:
    """创建指定运行模式的 Application."""
    if mode == RuntimeMode.STANDALONE:
        return StandaloneApplication()

    raise ValueError(f"Unsupported runtime mode: {mode}")

if __name__ == "__main__":
    asyncio.run(app_factory(RuntimeMode.STANDALONE).run())