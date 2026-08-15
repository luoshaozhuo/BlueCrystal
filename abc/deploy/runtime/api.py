"""Ingest 运行时管理 API."""

from __future__ import annotations

from datetime import datetime

from fastapi import FastAPI, HTTPException, Response, status
from pydantic import BaseModel, Field

from deploy.runtime.scheduler import (
    RuntimeScheduler,
    ScheduledTask,
    ScheduledTaskNotFoundError,
)


class ScheduleIntervalRequest(BaseModel):
    """周期调度请求."""

    interval_ms: int = Field(gt=0)


class ScheduledTaskResponse(BaseModel):
    """运行时任务响应."""

    task_id: int
    next_run_time: datetime | None
    paused: bool


class RuntimeStatusResponse(BaseModel):
    """运行时状态响应."""

    scheduler_running: bool
    scheduled_task_count: int


def create_api(scheduler: RuntimeScheduler) -> FastAPI:
    """创建 Ingest Management API."""

    app = FastAPI(
        title="BlueCrystal Ingest Management API",
        version="0.1.0",
    )

    @app.get(
        "/health",
        response_model=RuntimeStatusResponse,
    )
    async def health() -> RuntimeStatusResponse:
        """查询运行状态."""
        tasks = scheduler.list()

        return RuntimeStatusResponse(
            scheduler_running=scheduler.running,
            scheduled_task_count=len(tasks),
        )

    @app.get(
        "/runtime/tasks",
        response_model=list[ScheduledTaskResponse],
    )
    async def list_tasks() -> list[ScheduledTaskResponse]:
        """查询所有运行时任务."""
        return [_to_response(task) for task in scheduler.list()]

    @app.get(
        "/runtime/tasks/{task_id}",
        response_model=ScheduledTaskResponse,
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

    @app.put(
        "/runtime/tasks/{task_id}",
        response_model=ScheduledTaskResponse,
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

    @app.delete(
        "/runtime/tasks/{task_id}",
        status_code=status.HTTP_204_NO_CONTENT,
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

    @app.post(
        "/runtime/tasks/{task_id}/pause",
        response_model=ScheduledTaskResponse,
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

    @app.post(
        "/runtime/tasks/{task_id}/resume",
        response_model=ScheduledTaskResponse,
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

    @app.post(
        "/runtime/tasks/{task_id}/run",
        status_code=status.HTTP_202_ACCEPTED,
    )
    async def run_task(task_id: int) -> dict[str, int]:
        """立即执行一次任务."""
        scheduler.run_now(task_id)

        return {"task_id": task_id}

    return app


def _to_response(task: ScheduledTask) -> ScheduledTaskResponse:
    """转换为 API 响应模型."""
    return ScheduledTaskResponse(
        task_id=task.task_id,
        next_run_time=task.next_run_time,
        paused=task.paused,
    )