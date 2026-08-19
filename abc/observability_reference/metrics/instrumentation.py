"""Instrumentation 事实 -> Metrics."""

from __future__ import annotations

from datetime import datetime

from .service import MetricService


class MetricInstrumentationHooks:
    """Metrics 只接收低基数字段；ID 从 Context 读取也不作为 label."""

    def __init__(self, metrics: MetricService) -> None:
        self._metrics = metrics

    def http_request_started(self) -> None:
        self._metrics.add_gauge("http_requests_in_flight", 1.0)

    def http_request_finished(
        self,
        *,
        status_code: int,
        duration_seconds: float,
    ) -> None:
        self._metrics.add_gauge("http_requests_in_flight", -1.0)
        self._metrics.increment(
            "http_requests_total",
            labels={
                "result": "success" if status_code < 500 else "server_error",
                "status_class": f"{status_code // 100}xx",
            },
        )
        self._metrics.observe(
            "http_request_duration_seconds",
            duration_seconds,
        )

    def http_request_failed(
        self,
        *,
        duration_seconds: float,
        exception: Exception,
    ) -> None:
        self._metrics.add_gauge("http_requests_in_flight", -1.0)
        self._metrics.increment(
            "http_requests_total",
            labels={"result": "exception"},
        )
        self._metrics.observe(
            "http_request_duration_seconds",
            duration_seconds,
            labels={"result": "exception"},
        )

    def scheduler_started(self) -> None:
        self._metrics.set_gauge("scheduler_running", 1.0)

    def scheduler_stopped(self) -> None:
        self._metrics.set_gauge("scheduler_running", 0.0)

    def scheduler_job_missed(
        self,
        *,
        scheduled_run_time: datetime,
    ) -> None:
        self._metrics.increment("scheduler_job_missed_total")

    def scheduler_job_max_instances(
        self,
        *,
        scheduled_run_times: tuple[datetime, ...],
    ) -> None:
        self._metrics.increment(
            "scheduler_job_max_instances_total",
            amount=float(max(1, len(scheduled_run_times))),
        )

    def task_execution_started(self) -> None:
        self._metrics.add_gauge("task_executions_in_flight", 1.0)

    def task_execution_succeeded(
        self,
        *,
        duration_seconds: float,
    ) -> None:
        self._finish_execution(
            result="success",
            duration_seconds=duration_seconds,
        )

    def task_execution_failed(
        self,
        *,
        duration_seconds: float,
        exception: Exception,
    ) -> None:
        self._finish_execution(
            result="failure",
            duration_seconds=duration_seconds,
        )

    def task_execution_cancelled(
        self,
        *,
        duration_seconds: float,
    ) -> None:
        self._finish_execution(
            result="cancelled",
            duration_seconds=duration_seconds,
        )

    def task_scheduled(self) -> None:
        self._task_operation("scheduled")

    def task_removed(self) -> None:
        self._task_operation("removed")

    def task_paused(self) -> None:
        self._task_operation("paused")

    def task_resumed(self) -> None:
        self._task_operation("resumed")

    def task_run_requested(self) -> None:
        self._task_operation("run_requested")

    def audit_operation_succeeded(
        self,
        *,
        status_code: int | None = None,
    ) -> None:
        self._metrics.increment(
            "audit_operations_total",
            labels={"result": "success"},
        )

    def audit_operation_failed(
        self,
        *,
        status_code: int | None = None,
        exception: BaseException | None = None,
    ) -> None:
        self._metrics.increment(
            "audit_operations_total",
            labels={"result": "failure"},
        )

    def _finish_execution(
        self,
        *,
        result: str,
        duration_seconds: float,
    ) -> None:
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

    def _task_operation(self, operation: str) -> None:
        self._metrics.increment(
            "task_operations_total",
            labels={"operation": operation},
        )
