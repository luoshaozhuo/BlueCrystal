"""Instrumentation 技术事实到 Logs 的映射."""

from __future__ import annotations

from datetime import datetime

from deploy.observability.shared import bind_observation_context

from .service import LogService


class LogInstrumentationHooks:
    """把 InstrumentationHooks 的事实映射为结构化日志.

    该类采用结构化 typing：不需要继承 InstrumentationHooks；只要方法签名满足
    Protocol 即可。当前它只实现 Logs 维度，Metrics/Diagnostics/Audit 将由各自
    的 hook 实现处理，后续通过 CompositeInstrumentationHooks 统一 fan-out。
    """

    def __init__(self, logs: LogService) -> None:
        self._logs = logs

    # HTTP ---------------------------------------------------------------
    def http_request_started(self, *, method: str, path: str) -> None:
        # 不复制 Uvicorn 正常 access log；正常请求主要进入 Metrics。
        pass

    def http_request_finished(
        self,
        *,
        method: str,
        path: str,
        status_code: int,
        duration_seconds: float,
    ) -> None:
        # 仅服务端错误写业务日志，避免与 access log 重复。
        if status_code < 500:
            return

        self._logs.error(
            component="runtime.web",
            event="management_request_failed",
            message="Management API returned server error",
            fields={
                "method": method,
                "path": path,
                "status_code": status_code,
                "duration_seconds": duration_seconds,
            },
        )

    def http_request_failed(
        self,
        *,
        method: str,
        path: str,
        duration_seconds: float,
        exception: Exception,
    ) -> None:
        self._logs.error(
            component="runtime.web",
            event="management_request_failed",
            message="Management API request raised an unhandled exception",
            fields={
                "method": method,
                "path": path,
                "duration_seconds": duration_seconds,
            },
            exception=exception,
        )

    # APScheduler --------------------------------------------------------
    def scheduler_started(self) -> None:
        self._logs.info(
            component="runtime.scheduler",
            event="scheduler_started",
            message="Task scheduler started",
        )

    def scheduler_stopped(self) -> None:
        self._logs.info(
            component="runtime.scheduler",
            event="scheduler_stopped",
            message="Task scheduler stopped",
        )

    def scheduler_job_missed(
        self,
        *,
        task_id: int,
        scheduled_run_time: datetime,
    ) -> None:
        with bind_observation_context(task_id=task_id):
            self._logs.warning(
                component="runtime.scheduler",
                event="task_missed",
                message="Scheduled task execution was missed",
                fields={
                    "scheduled_run_time": scheduled_run_time.isoformat(),
                },
            )

    def scheduler_job_max_instances(
        self,
        *,
        task_id: int,
        scheduled_run_times: tuple[datetime, ...],
    ) -> None:
        with bind_observation_context(task_id=task_id):
            self._logs.warning(
                component="runtime.scheduler",
                event="task_max_instances_reached",
                message="Task execution was skipped because max_instances was reached",
                fields={
                    "scheduled_run_times": [
                        value.isoformat() for value in scheduled_run_times
                    ],
                },
            )

    # TaskRunner ---------------------------------------------------------
    def task_execution_started(self, *, task_id: int) -> None:
        # ObservedTaskRunner 已绑定 task_id；再次绑定使独立调用此 hook 时也保持正确。
        with bind_observation_context(task_id=task_id):
            self._logs.info(
                component="runtime.task_runner",
                event="task_execution_started",
                message="Task execution started",
            )

    def task_execution_succeeded(
        self,
        *,
        task_id: int,
        duration_seconds: float,
    ) -> None:
        with bind_observation_context(task_id=task_id):
            self._logs.info(
                component="runtime.task_runner",
                event="task_execution_succeeded",
                message="Task execution succeeded",
                fields={"duration_seconds": duration_seconds},
            )

    def task_execution_failed(
        self,
        *,
        task_id: int,
        duration_seconds: float,
        exception: Exception,
    ) -> None:
        with bind_observation_context(task_id=task_id):
            self._logs.error(
                component="runtime.task_runner",
                event="task_execution_failed",
                message="Task execution failed",
                fields={"duration_seconds": duration_seconds},
                exception=exception,
            )

    def task_execution_cancelled(
        self,
        *,
        task_id: int,
        duration_seconds: float,
    ) -> None:
        with bind_observation_context(task_id=task_id):
            self._logs.warning(
                component="runtime.task_runner",
                event="task_execution_cancelled",
                message="Task execution was cancelled",
                fields={"duration_seconds": duration_seconds},
            )

    # Semantic hooks -----------------------------------------------------
    def task_scheduled(self, *, task_id: int) -> None:
        self._task_info(task_id, "task_scheduled", "Task scheduled")

    def task_removed(self, *, task_id: int) -> None:
        self._task_info(task_id, "task_removed", "Task removed")

    def task_paused(self, *, task_id: int) -> None:
        self._task_info(task_id, "task_paused", "Task paused")

    def task_resumed(self, *, task_id: int) -> None:
        self._task_info(task_id, "task_resumed", "Task resumed")

    def task_run_requested(self, *, task_id: int) -> None:
        self._task_info(task_id, "task_run_requested", "Immediate task run requested")

    def _task_info(self, task_id: int, event: str, message: str) -> None:
        with bind_observation_context(task_id=task_id):
            self._logs.info(
                component="runtime.scheduler",
                event=event,
                message=message,
            )
