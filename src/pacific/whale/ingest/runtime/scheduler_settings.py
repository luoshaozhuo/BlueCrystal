"""调度器配置。

定义调度器行为的可配置参数。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from pacific.whale.ingest.runtime.modes import RuntimeMode


@dataclass(slots=True)
class JobStoreSettings:
    """APScheduler 任务存储设置。"""

    type: str = "memory"
    url: str | None = None


@dataclass(slots=True)
class ExecutorSettings:
    """APScheduler 执行器配置。定义线程池/进程池的名称、类型和参数。"""

    threadpool_max_workers: int = 8
    processpool_max_workers: int | None = None


@dataclass(slots=True)
class JobDefaultSettings:
    """APScheduler 执行器配置。定义线程池/进程池执行器参数。"""

    coalesce: bool = True
    max_instances: int = 1
    misfire_grace_time: int = 30


@dataclass(slots=True)
class SchedulerSettings:
    """调度器配置。

定义调度器行为的可配置参数。"""

    scheduler_type: str = "blocking"
    timezone: str = "UTC"
    runtime_mode: RuntimeMode = RuntimeMode.STANDALONE
    node_key: str = "node-1"
    heartbeat_interval_seconds: int = 10
    heartbeat_timeout_seconds: int = 30
    lease_ttl_seconds: int = 30
    pull_max_in_flight: int = 8
    jobstore: JobStoreSettings = field(default_factory=JobStoreSettings)
    executors: ExecutorSettings = field(default_factory=ExecutorSettings)
    job_defaults: JobDefaultSettings = field(default_factory=JobDefaultSettings)
