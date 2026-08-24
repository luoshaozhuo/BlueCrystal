"""每个 Runtime 独占的 Prometheus registry 与指标集合。

模块导入不会注册 collector；因此同一进程可以安全创建多个 Runtime。

metrics 并不会持久化，而是暴露给 Prometheus 进行实时抓取。

"""

from __future__ import annotations

from typing import Any, cast

from prometheus_client import Counter, Gauge, Histogram

from ..config import ServiceConfig, MetricsConfig


class MetricsBackend:
    """持有 Prometheus registry 和内置 instrumentation 指标。"""

    def __init__(
        self,
        service: ServiceConfig,
        config: MetricsConfig,
    ) -> None:
        """创建隔离 registry，避免默认全局 registry 重复注册。"""
        if config.provider != "prometheus":
            raise ValueError(f"metrics.provider: unsupported provider {config.provider!r}")
        controlled = {"namespace", "subsystem"}
        conflict = controlled.intersection(config.provider_options)
        if conflict:
            raise ValueError(
                "metrics.provider_options conflicts with runtime-controlled keys: "
                + ", ".join(sorted(conflict))
            )
        common = {
            "namespace": service.name,
            "subsystem": config.subsystem,
        }
        # provider_options 是刻意保留的第三方动态边界；prometheus_client
        # 没有为可扩展 kwargs 暴露稳定 TypedDict。
        counter_factory = cast(Any, Counter)
        histogram_factory = cast(Any, Histogram)
        gauge_factory = cast(Any, Gauge)
        self.worker_executions = counter_factory(
            "worker_executions_total",
            "Worker executions by operation and result",
            ("operation", "result"),
            **common,
            **config.provider_options,
        )
        self.worker_duration = histogram_factory(
            "worker_execution_duration_seconds",
            "Worker execution duration by operation and result",
            ("operation", "result"),
            **common,
        )
        self.worker_in_flight = gauge_factory(
            "worker_executions_in_flight",
            "Current worker executions by operation",
            ("operation",),
            **common,
        )
        self.scheduler_running = gauge_factory(
            "scheduler_running",
            "Whether the scheduler is running",
            **common,
        )
        self.scheduler_events = counter_factory(
            "scheduler_events_total",
            "APScheduler events by result",
            ("event",),
            **common,
        )
