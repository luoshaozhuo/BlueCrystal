"""Instrumentation 技术事实到 Metrics 的映射."""

from __future__ import annotations

from datetime import datetime

from .service import MetricService


class MetricInstrumentationHooks:
    """把 InstrumentationHooks 的事实映射为聚合指标.

    不把 request_id/task_id/connection_id/raw path 作为 label，避免高基数。
    """

    def __init__(self, metrics: MetricService) -> None:
        self._metrics = metrics

    def http_request_started(self, *, method: str, path: str) -> None:
        self._metrics.add_gauge(
            "http_requests_in_flight",
            1.0,
            labels={"method": method.upper()},
        )

    def http_request_finished(
        self,
        *,
        method: str,
        path: str,
        status_code: int,
        duration_seconds: float,
    ) -> None:
        labels = {
            "method": method.upper(),
            "status_class": f"{status_code // 100}xx",
        }
        self._metrics.add_gauge(
            "http_requests_in_flight",
            -1.0,
            labels={"method": method.upper()},
        )
        self._metrics.increment("http_requests_total", labels=labels)
        self._metrics.observe(
            "http_request_duration_seconds",
            duration_seconds,
            labels=labels,
        )

    def http_request_failed(
        self,
        *,
        method: str,
        path: str,
        duration_seconds: float,
        exception: Exception,
    ) -> None:
        labels = {"method": method.upper(), "status_class": "exception"}
        self._metrics.add_gauge(
            "http_requests_in_flight",
            -1.0,
            labels={"method": method.upper()},
        )
        self._metrics.increment("http_requests_total", labels=labels)
        self._metrics.increment(
            "http_request_failures_total",
            labels={"method": method.upper()},
        )
        self._metrics.observe(
            "http_request_duration_seconds",
            duration_seconds,
            labels=labels,
        )

    def scheduler_started(self) -> None:
        self._metrics.set_gauge("scheduler_running", 1.0)

    def scheduler_stopped(self) -> None:
        self._metrics.set_gauge("scheduler_running", 0.0)

    def scheduler_job_missed(
        self,
        *,
        task_id: int,
        scheduled_run_time: datetime,
    ) -> None:
        self._metrics.increment("task_misfires_total")

    def scheduler_job_max_instances(
        self,
        *,
        task_id: int,
        scheduled_run_times: tuple[datetime, ...],
    ) -> None:
        self._metrics.increment(
            "task_max_instances_skips_total",
            amount=float(max(1, len(scheduled_run_times))),
        )

    def task_execution_started(self, *, task_id: int) -> None:
        self._metrics.add_gauge("task_executions_in_flight", 1.0)

    def task_execution_succeeded(
        self,
        *,
        task_id: int,
        duration_seconds: float,
    ) -> None:
        self._finish_task_execution("success", duration_seconds)

    def task_execution_failed(
        self,
        *,
        task_id: int,
        duration_seconds: float,
        exception: Exception,
    ) -> None:
        self._finish_task_execution("failure", duration_seconds)
        self._metrics.increment("task_execution_failures_total")

    def task_execution_cancelled(
        self,
        *,
        task_id: int,
        duration_seconds: float,
    ) -> None:
        self._finish_task_execution("cancelled", duration_seconds)
        self._metrics.increment("task_execution_cancellations_total")

    def task_scheduled(self, *, task_id: int) -> None:
        self._scheduler_operation("schedule")

    def task_removed(self, *, task_id: int) -> None:
        self._scheduler_operation("remove")

    def task_paused(self, *, task_id: int) -> None:
        self._scheduler_operation("pause")

    def task_resumed(self, *, task_id: int) -> None:
        self._scheduler_operation("resume")

    def task_run_requested(self, *, task_id: int) -> None:
        self._scheduler_operation("run_now")

    def _finish_task_execution(self, result: str, duration_seconds: float) -> None:
        self._metrics.add_gauge("task_executions_in_flight", -1.0)
        self._metrics.increment(
            "task_executions_total",
            labels={"result": result},
        )
        self._metrics.observe(
            "task_execution_duration_seconds",
            duration_seconds,
            labels={"result": result},
        )

    def _scheduler_operation(self, operation: str) -> None:
        self._metrics.increment(
            "scheduler_task_operations_total",
            labels={"operation": operation},
        )
