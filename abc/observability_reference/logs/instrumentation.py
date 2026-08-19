"""Instrumentation 事实 -> Logs."""

from __future__ import annotations

from datetime import datetime

from observability_reference.shared import get_observation_context

from .service import LogService


class LogInstrumentationHooks:
    """只实现 Logs 需要消费的 Hook."""

    def __init__(self, logs: LogService) -> None:
        self._logs = logs

    def http_request_started(self) -> None:
        context = get_observation_context()
        self._logs.debug(
            "http_request_started",
            method=context.http_method,
            path=context.http_path,
        )

    def http_request_finished(
        self,
        *,
        status_code: int,
        duration_seconds: float,
    ) -> None:
        # 2xx/3xx 正常访问默认交给 Uvicorn access log，避免重复。
        if status_code < 500:
            return

        context = get_observation_context()
        self._logs.error(
            "http_request_finished_with_server_error",
            method=context.http_method,
            path=context.http_path,
            status_code=status_code,
            duration_seconds=duration_seconds,
        )

    def http_request_failed(
        self,
        *,
        duration_seconds: float,
        exception: Exception,
    ) -> None:
        context = get_observation_context()
        self._logs.exception(
            "http_request_failed",
            exception=exception,
            method=context.http_method,
            path=context.http_path,
            duration_seconds=duration_seconds,
        )

    def scheduler_started(self) -> None:
        self._logs.info("scheduler_started")

    def scheduler_stopped(self) -> None:
        self._logs.info("scheduler_stopped")

    def scheduler_job_missed(
        self,
        *,
        scheduled_run_time: datetime,
    ) -> None:
        context = get_observation_context()
        self._logs.warning(
            "scheduler_job_missed",
            task_id=context.task_id,
            scheduled_run_time=scheduled_run_time,
        )

    def scheduler_job_max_instances(
        self,
        *,
        scheduled_run_times: tuple[datetime, ...],
    ) -> None:
        context = get_observation_context()
        self._logs.warning(
            "scheduler_job_max_instances",
            task_id=context.task_id,
            scheduled_run_times=scheduled_run_times,
        )

    def task_execution_started(self) -> None:
        context = get_observation_context()
        self._logs.info(
            "task_execution_started",
            task_id=context.task_id,
        )

    def task_execution_succeeded(
        self,
        *,
        duration_seconds: float,
    ) -> None:
        context = get_observation_context()
        self._logs.info(
            "task_execution_succeeded",
            task_id=context.task_id,
            duration_seconds=duration_seconds,
        )

    def task_execution_failed(
        self,
        *,
        duration_seconds: float,
        exception: Exception,
    ) -> None:
        context = get_observation_context()
        self._logs.exception(
            "task_execution_failed",
            exception=exception,
            task_id=context.task_id,
            duration_seconds=duration_seconds,
        )

    def task_execution_cancelled(
        self,
        *,
        duration_seconds: float,
    ) -> None:
        context = get_observation_context()
        self._logs.warning(
            "task_execution_cancelled",
            task_id=context.task_id,
            duration_seconds=duration_seconds,
        )

    def task_scheduled(self) -> None:
        self._logs.info(
            "task_scheduled",
            task_id=get_observation_context().task_id,
        )

    def task_removed(self) -> None:
        self._logs.info(
            "task_removed",
            task_id=get_observation_context().task_id,
        )

    def task_paused(self) -> None:
        self._logs.info(
            "task_paused",
            task_id=get_observation_context().task_id,
        )

    def task_resumed(self) -> None:
        self._logs.info(
            "task_resumed",
            task_id=get_observation_context().task_id,
        )

    def task_run_requested(self) -> None:
        self._logs.info(
            "task_run_requested",
            task_id=get_observation_context().task_id,
        )

    def audit_operation_succeeded(
        self,
        *,
        status_code: int | None = None,
    ) -> None:
        context = get_observation_context()
        self._logs.info(
            "audit_operation_succeeded",
            operation=context.operation,
            target_type=context.target_type,
            target_id=context.target_id,
            actor=context.actor,
            status_code=status_code,
        )

    def audit_operation_failed(
        self,
        *,
        status_code: int | None = None,
        exception: BaseException | None = None,
    ) -> None:
        context = get_observation_context()
        fields = {
            "operation": context.operation,
            "target_type": context.target_type,
            "target_id": context.target_id,
            "actor": context.actor,
            "status_code": status_code,
        }

        if isinstance(exception, Exception):
            self._logs.exception(
                "audit_operation_failed",
                exception=exception,
                **fields,
            )
        else:
            self._logs.warning(
                "audit_operation_failed",
                **fields,
            )
