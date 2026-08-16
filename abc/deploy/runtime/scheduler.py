"""运行时任务调度."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import datetime

from apscheduler.jobstores.base import JobLookupError
from apscheduler.schedulers.asyncio import AsyncIOScheduler


TaskRunner = Callable[[int], Awaitable[None]]


class ScheduledTaskNotFoundError(LookupError):
    """指定的运行时任务不存在."""


@dataclass(frozen=True, slots=True)
class ScheduledTask:
    """运行时调度任务快照."""

    task_id: int
    next_run_time: datetime | None
    paused: bool


class TaskScheduler:
    """Ingest 运行时调度器."""

    JOB_ID_PREFIX = "task:"

    def __init__(self, runner: TaskRunner) -> None:
        """初始化调度器.

        Args:
            runner: 实际执行一个 Ingest Task 的异步函数.
        """
        self._runner = runner

        self._scheduler = AsyncIOScheduler(
            timezone="UTC",
            job_defaults={
                "coalesce": True,
                "max_instances": 1,
                "misfire_grace_time": 30,
            },
        )

    @property
    def running(self) -> bool:
        """调度器是否正在运行."""
        return self._scheduler.running

    def start(self) -> None:
        """启动调度器."""
        if not self._scheduler.running:
            self._scheduler.start()
        print("scheduler start")

    def stop(self) -> None:
        """停止调度器."""
        if self._scheduler.running:
            self._scheduler.shutdown(wait=False)
        print("scheduler stop")

    def schedule_interval(
        self,
        task_id: int,
        interval_ms: int,
    ) -> ScheduledTask:
        """创建或更新周期任务.

        Args:
            task_id: Whale 中的任务标识.
            interval_ms: 调度周期，单位毫秒.

        Returns:
            当前调度任务快照.
        """
        if interval_ms <= 0:
            raise ValueError("interval_ms must be greater than 0")

        job_id = self._job_id(task_id)

        self._scheduler.add_job(
            self._runner,
            trigger="interval",
            seconds=interval_ms / 1000.0,
            id=job_id,
            name=f"Ingest Task {task_id}",
            args=(task_id,),
            replace_existing=True,
        )

        return self.get(task_id)

    def remove(self, task_id: int) -> None:
        """移除任务."""
        try:
            self._scheduler.remove_job(self._job_id(task_id))
        except JobLookupError as exc:
            raise ScheduledTaskNotFoundError(task_id) from exc

    def pause(self, task_id: int) -> ScheduledTask:
        """暂停任务."""
        try:
            self._scheduler.pause_job(self._job_id(task_id))
        except JobLookupError as exc:
            raise ScheduledTaskNotFoundError(task_id) from exc

        return self.get(task_id)

    def resume(self, task_id: int) -> ScheduledTask:
        """恢复任务."""
        try:
            self._scheduler.resume_job(self._job_id(task_id))
        except JobLookupError as exc:
            raise ScheduledTaskNotFoundError(task_id) from exc

        return self.get(task_id)

    def run_now(self, task_id: int) -> None:
        """立即执行一次任务"""
        self._scheduler.add_job(
            self._runner,
            args=(task_id,),
        )

    def get(self, task_id: int) -> ScheduledTask:
        """获取任务."""
        job = self._scheduler.get_job(self._job_id(task_id))

        if job is None:
            raise ScheduledTaskNotFoundError(task_id)

        return ScheduledTask(
            task_id=task_id,
            next_run_time=job.next_run_time,
            paused=job.next_run_time is None,
        )

    def list(self) -> list[ScheduledTask]:
        """获取全部 Ingest 调度任务."""
        tasks: list[ScheduledTask] = []

        for job in self._scheduler.get_jobs():
            if not job.id.startswith(self.JOB_ID_PREFIX):
                continue

            task_id = int(job.id.removeprefix(self.JOB_ID_PREFIX))

            tasks.append(
                ScheduledTask(
                    task_id=task_id,
                    next_run_time=job.next_run_time,
                    paused=job.next_run_time is None,
                )
            )

        return tasks

    @classmethod
    def _job_id(cls, task_id: int) -> str:
        """生成 APScheduler Job ID."""
        return f"{cls.JOB_ID_PREFIX}{task_id}"