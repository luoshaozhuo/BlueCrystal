"""Scheduler configuration models for ingest runtime."""

from __future__ import annotations

from dataclasses import dataclass, field

from whale.ingest.runtime.modes import RuntimeMode


@dataclass(slots=True)
class JobStoreSettings:
    """APScheduler job store settings."""

    type: str = "memory"
    url: str | None = None


@dataclass(slots=True)
class ExecutorSettings:
    """APScheduler executor settings."""

    threadpool_max_workers: int = 8
    processpool_max_workers: int | None = None


@dataclass(slots=True)
class JobDefaultSettings:
    """Default runtime behavior for APScheduler jobs."""

    coalesce: bool = True
    max_instances: int = 1
    misfire_grace_time: int = 30


@dataclass(slots=True)
class SchedulerSettings:
    """Top-level scheduler settings."""

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
