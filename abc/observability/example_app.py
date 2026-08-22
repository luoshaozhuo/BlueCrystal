"""FastAPI + Worker 的最小组合示例，不在模块导入时创建资源。"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from .manager import create_observability


async def business_runner(task_id: int) -> int:
    """模拟业务 Worker，并保持业务自行记录日志的边界。"""
    await asyncio.sleep(0.01)
    return task_id


def create_app(config_path: str | Path) -> FastAPI:
    """从 YAML 创建只组合 FastAPI 和 Worker 的示例应用。"""
    runtime = create_observability(config_path)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        """在应用结构安装完成后启动资源，并在退出时逆序关闭。"""
        await runtime.start()
        try:
            yield
        finally:
            await runtime.close()

    runner = runtime.instrument_worker(
        "task.execute",
        business_runner,
        resolver=lambda task_id: {
            "job_id": str(task_id),
            "attributes": {"example.task.id": task_id},
        },
    )
    app = FastAPI(title="Observability Example", lifespan=lifespan)
    runtime.instrument_fastapi(app)
    app.state.observability = runtime

    @app.post("/tasks/{task_id}/run")
    async def run_task(task_id: int) -> dict[str, int]:
        """触发示例 Worker 并返回其业务结果。"""
        return {"task_id": await runner(task_id)}

    return app
