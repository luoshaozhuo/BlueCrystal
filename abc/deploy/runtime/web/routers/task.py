"""定义了任务相关的路由接口"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field
from datetime import datetime
from fastapi import HTTPException, Response, status

from deploy.runtime.scheduler import TaskScheduler, ScheduledTask, ScheduledTaskNotFoundError


class ScheduleIntervalRequest(BaseModel):
    """周期调度请求."""

    interval_ms: int = Field(gt=0)


class ScheduledTaskResponse(BaseModel):
    """运行时任务响应."""

    task_id: int
    next_run_time: datetime | None
    paused: bool


def _to_response(task: ScheduledTask) -> ScheduledTaskResponse:
    """转换为 API 响应模型."""
    return ScheduledTaskResponse(
        task_id=task.task_id,
        next_run_time=task.next_run_time,
        paused=task.paused,
    )


def create_task_router(
    scheduler: TaskScheduler,
) -> APIRouter:
    """创建绑定指定调度器的任务管理路由.

    Args:
        scheduler: 承担任务查询、调度和状态切换的运行时调度器.

    Returns:
        路径前缀为 ``/task`` 的 FastAPI 路由器.
    """

    router = APIRouter(prefix="/tasks", tags=["task"])

    @router.get(
        "/",
        response_model=list[ScheduledTaskResponse],
        summary="查询所有运行时任务",
    )
    async def list_tasks() -> list[ScheduledTaskResponse]:
        """查询所有运行时任务."""
        return [_to_response(task) for task in scheduler.list()]

    @router.get(
        "/{task_id}",
        response_model=ScheduledTaskResponse,
        summary="查询指定运行时任务",
    )
    async def get_task(task_id: int) -> ScheduledTaskResponse:
        """查询指定运行时任务."""
        try:
            task = scheduler.get(task_id)
        except ScheduledTaskNotFoundError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task {task_id} is not scheduled",
            ) from exc

        return _to_response(task)

    @router.put(
        "/{task_id}",
        response_model=ScheduledTaskResponse,
        summary="创建或更新周期运行任务",
    )
    async def schedule_task(
        task_id: int,
        request: ScheduleIntervalRequest,
    ) -> ScheduledTaskResponse:
        """创建或更新周期运行任务."""
        task = scheduler.schedule_interval(
            task_id=task_id,
            interval_ms=request.interval_ms,
        )

        return _to_response(task)

    @router.delete(
        "/{task_id}",
        status_code=status.HTTP_204_NO_CONTENT,
        summary="停止并移除运行时任务",
    )
    async def remove_task(task_id: int) -> Response:
        """停止并移除运行时任务."""
        try:
            scheduler.remove(task_id)
        except ScheduledTaskNotFoundError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task {task_id} is not scheduled",
            ) from exc

        return Response(status_code=status.HTTP_204_NO_CONTENT)

    @router.post(
        "/{task_id}/pause",
        response_model=ScheduledTaskResponse,
        summary="暂停运行时任务",
    )
    async def pause_task(task_id: int) -> ScheduledTaskResponse:
        """暂停运行时任务."""
        try:
            task = scheduler.pause(task_id)
        except ScheduledTaskNotFoundError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task {task_id} is not scheduled",
            ) from exc

        return _to_response(task)

    @router.post(
        "/{task_id}/resume",
        response_model=ScheduledTaskResponse,
        summary="恢复运行时任务",
    )
    async def resume_task(task_id: int) -> ScheduledTaskResponse:
        """恢复运行时任务."""
        try:
            task = scheduler.resume(task_id)
        except ScheduledTaskNotFoundError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task {task_id} is not scheduled",
            ) from exc

        return _to_response(task)

    @router.post(
        "/{task_id}/run",
        status_code=status.HTTP_202_ACCEPTED,
        summary="立即执行一次任务",
    )
    async def run_task(task_id: int) -> dict[str, int]:
        """立即执行一次任务."""
        scheduler.run_now(task_id)

        return {"task_id": task_id}

    return router
