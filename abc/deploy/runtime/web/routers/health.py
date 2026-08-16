"""定义了健康检查相关的路由接口"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from deploy.runtime.scheduler import TaskScheduler


class RuntimeStatusResponse(BaseModel):
    """运行时健康状态响应."""

    scheduler_running: bool
    scheduled_task_count: int


def create_health_router(
    scheduler: TaskScheduler,
) -> APIRouter:
    """创建绑定指定调度器的健康检查路由.

    Args:
        scheduler: 提供运行状态和已调度任务列表的运行时调度器.

    Returns:
        路径前缀为 ``/health`` 的 FastAPI 路由器.
    """

    router = APIRouter(prefix="/health", tags=["health"])

    @router.get(
        "/",
        response_model=RuntimeStatusResponse,
    )
    async def health() -> RuntimeStatusResponse:
        """返回当前调度器进程内可观察到的健康状态."""
        tasks = scheduler.list()

        return RuntimeStatusResponse(
            scheduler_running=scheduler.running,
            scheduled_task_count=len(tasks),
        )

    return router
