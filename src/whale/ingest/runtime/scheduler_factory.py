"""调度器工厂。

根据配置创建和配置 APScheduler 实例，
包括线程池大小、任务存储、时区等设置。
"""

from __future__ import annotations

from apscheduler.executors.pool import (  # type: ignore[import-untyped]
    ProcessPoolExecutor,
    ThreadPoolExecutor,
)
from apscheduler.jobstores.memory import MemoryJobStore  # type: ignore[import-untyped]
from apscheduler.jobstores.sqlalchemy import (  # type: ignore[import-untyped]
    SQLAlchemyJobStore,
)
from apscheduler.schedulers.background import (  # type: ignore[import-untyped]
    BackgroundScheduler,
)
from apscheduler.schedulers.base import BaseScheduler  # type: ignore[import-untyped]
from apscheduler.schedulers.blocking import (  # type: ignore[import-untyped]
    BlockingScheduler,
)

from whale.ingest.runtime.scheduler_settings import SchedulerSettings


def build_scheduler(settings: SchedulerSettings) -> BaseScheduler:
    """根据运行时设置构造 APScheduler 实例。"""
    scheduler_type = settings.scheduler_type.lower()
    scheduler_cls: type[BaseScheduler]

    if scheduler_type == "blocking":
        scheduler_cls = BlockingScheduler
    elif scheduler_type == "background":
        scheduler_cls = BackgroundScheduler
    else:
        raise ValueError(f"Unsupported scheduler_type: {settings.scheduler_type}")

    jobstores = {"default": _build_jobstore(settings)}
    executors = _build_executors(settings)
    job_defaults = {
        "coalesce": settings.job_defaults.coalesce,
        "max_instances": settings.job_defaults.max_instances,
        "misfire_grace_time": settings.job_defaults.misfire_grace_time,
    }

    return scheduler_cls(
        jobstores=jobstores,
        executors=executors,
        job_defaults=job_defaults,
        timezone=settings.timezone,
    )


def _build_jobstore(settings: SchedulerSettings) -> MemoryJobStore | SQLAlchemyJobStore:
    """构造默认的 APScheduler 任务存储。"""
    jobstore_type = settings.jobstore.type.lower()

    if jobstore_type == "memory":
        return MemoryJobStore()

    if jobstore_type == "sqlalchemy":
        if not settings.jobstore.url:
            raise ValueError("SQLAlchemy job store requires a non-empty url")
        return SQLAlchemyJobStore(url=settings.jobstore.url)

    raise ValueError(f"Unsupported jobstore type: {settings.jobstore.type}")


def _build_executors(
    settings: SchedulerSettings,
) -> dict[str, ThreadPoolExecutor | ProcessPoolExecutor]:
    """构建 APScheduler 执行器配置字典。返回线程池和进程池的执行器参数。"""
    executors: dict[str, ThreadPoolExecutor | ProcessPoolExecutor] = {
        "default": ThreadPoolExecutor(settings.executors.threadpool_max_workers),
    }

    if settings.executors.processpool_max_workers is not None:
        executors["processpool"] = ProcessPoolExecutor(
            settings.executors.processpool_max_workers,
        )

    return executors
