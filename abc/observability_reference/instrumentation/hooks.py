"""Instrumentation 到 Observability capability 的统一事实接口."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol, runtime_checkable


@runtime_checkable
class InstrumentationHooks(Protocol):
    """Producer-facing 完整 Hook Contract.

    规则：
    - “当前是谁 / 当前在哪条链路”从 ObservationContext 获取；
    - Hook 参数只携带“本次事件发生了什么”的事件载荷。
    """

    # HTTP -----------------------------------------------------------------
    def http_request_started(self) -> None:
        ...

    def http_request_finished(
        self,
        *,
        status_code: int,
        duration_seconds: float,
    ) -> None:
        ...

    def http_request_failed(
        self,
        *,
        duration_seconds: float,
        exception: Exception,
    ) -> None:
        ...

    # APScheduler ----------------------------------------------------------
    def scheduler_started(self) -> None:
        ...

    def scheduler_stopped(self) -> None:
        ...

    def scheduler_job_missed(
        self,
        *,
        scheduled_run_time: datetime,
    ) -> None:
        ...

    def scheduler_job_max_instances(
        self,
        *,
        scheduled_run_times: tuple[datetime, ...],
    ) -> None:
        ...

    # TaskRunner -----------------------------------------------------------
    def task_execution_started(self) -> None:
        ...

    def task_execution_succeeded(
        self,
        *,
        duration_seconds: float,
    ) -> None:
        ...

    def task_execution_failed(
        self,
        *,
        duration_seconds: float,
        exception: Exception,
    ) -> None:
        ...

    def task_execution_cancelled(
        self,
        *,
        duration_seconds: float,
    ) -> None:
        ...

    # Task semantic facts --------------------------------------------------
    def task_scheduled(self) -> None:
        ...

    def task_removed(self) -> None:
        ...

    def task_paused(self) -> None:
        ...

    def task_resumed(self) -> None:
        ...

    def task_run_requested(self) -> None:
        ...

    # Audit operation facts ------------------------------------------------
    def audit_operation_succeeded(
        self,
        *,
        status_code: int | None = None,
    ) -> None:
        ...

    def audit_operation_failed(
        self,
        *,
        status_code: int | None = None,
        exception: BaseException | None = None,
    ) -> None:
        ...


class NullInstrumentationHooks:
    """完整 no-op 实现."""

    def http_request_started(self) -> None:
        pass

    def http_request_finished(
        self, *, status_code: int, duration_seconds: float
    ) -> None:
        pass

    def http_request_failed(
        self, *, duration_seconds: float, exception: Exception
    ) -> None:
        pass

    def scheduler_started(self) -> None:
        pass

    def scheduler_stopped(self) -> None:
        pass

    def scheduler_job_missed(self, *, scheduled_run_time: datetime) -> None:
        pass

    def scheduler_job_max_instances(
        self, *, scheduled_run_times: tuple[datetime, ...]
    ) -> None:
        pass

    def task_execution_started(self) -> None:
        pass

    def task_execution_succeeded(self, *, duration_seconds: float) -> None:
        pass

    def task_execution_failed(
        self, *, duration_seconds: float, exception: Exception
    ) -> None:
        pass

    def task_execution_cancelled(self, *, duration_seconds: float) -> None:
        pass

    def task_scheduled(self) -> None:
        pass

    def task_removed(self) -> None:
        pass

    def task_paused(self) -> None:
        pass

    def task_resumed(self) -> None:
        pass

    def task_run_requested(self) -> None:
        pass

    def audit_operation_succeeded(
        self, *, status_code: int | None = None
    ) -> None:
        pass

    def audit_operation_failed(
        self,
        *,
        status_code: int | None = None,
        exception: BaseException | None = None,
    ) -> None:
        pass


def safe_observe(callback, /, *args, **kwargs) -> None:
    """执行一次观测回调，观测故障不得覆盖业务结果."""

    try:
        callback(*args, **kwargs)
    except Exception:
        pass
