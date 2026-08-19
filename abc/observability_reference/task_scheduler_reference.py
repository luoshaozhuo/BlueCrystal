"""当前 BlueCrystal TaskScheduler 公共 API 的独立 Reference 版本."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import datetime

from apscheduler.jobstores.base import JobLookupError
from apscheduler.schedulers.asyncio import AsyncIOScheduler


TaskRunner = Callable[[int], Awaitable[None]]


class ScheduledTaskNotFoundError(LookupError):
    pass


@dataclass(frozen=True, slots=True)
class ScheduledTask:
    task_id: int
    next_run_time: datetime | None
    paused: bool


class TaskScheduler:
    JOB_ID_PREFIX = "task:"

    def __init__(self, runner: TaskRunner) -> None:
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
        return self._scheduler.running

    @property
    def apscheduler(self) -> AsyncIOScheduler:
        return self._scheduler

    def start(self) -> None:
        if not self._scheduler.running:
            self._scheduler.start()

    def stop(self) -> None:
        if self._scheduler.running:
            self._scheduler.shutdown(wait=False)

    def schedule_interval(self, task_id: int, interval_ms: int) -> ScheduledTask:
        if interval_ms <= 0:
            raise ValueError("interval_ms must be greater than 0")

        self._scheduler.add_job(
            self._runner,
            trigger="interval",
            seconds=interval_ms / 1000.0,
            id=self._job_id(task_id),
            name=f"Ingest Task {task_id}",
            args=(task_id,),
            replace_existing=True,
        )
        return self.get(task_id)

    def remove(self, task_id: int) -> None:
        try:
            self._scheduler.remove_job(self._job_id(task_id))
        except JobLookupError as exc:
            raise ScheduledTaskNotFoundError(task_id) from exc

    def pause(self, task_id: int) -> ScheduledTask:
        try:
            self._scheduler.pause_job(self._job_id(task_id))
        except JobLookupError as exc:
            raise ScheduledTaskNotFoundError(task_id) from exc
        return self.get(task_id)

    def resume(self, task_id: int) -> ScheduledTask:
        try:
            self._scheduler.resume_job(self._job_id(task_id))
        except JobLookupError as exc:
            raise ScheduledTaskNotFoundError(task_id) from exc
        return self.get(task_id)

    def run_now(self, task_id: int) -> None:
        self._scheduler.add_job(self._runner, args=(task_id,))

    def get(self, task_id: int) -> ScheduledTask:
        job = self._scheduler.get_job(self._job_id(task_id))
        if job is None:
            raise ScheduledTaskNotFoundError(task_id)
        return ScheduledTask(
            task_id=task_id,
            next_run_time=job.next_run_time,
            paused=job.next_run_time is None,
        )

    def list(self) -> list[ScheduledTask]:
        result: list[ScheduledTask] = []
        for job in self._scheduler.get_jobs():
            if not job.id.startswith(self.JOB_ID_PREFIX):
                continue
            task_id = int(job.id.removeprefix(self.JOB_ID_PREFIX))
            result.append(
                ScheduledTask(
                    task_id=task_id,
                    next_run_time=job.next_run_time,
                    paused=job.next_run_time is None,
                )
            )
        return result

    @classmethod
    def _job_id(cls, task_id: int) -> str:
        return f"{cls.JOB_ID_PREFIX}{task_id}"
