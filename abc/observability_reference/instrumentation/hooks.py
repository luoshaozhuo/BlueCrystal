"""Instrumentation 到 Observability Core 的窄接口.

本模块不实现 Logs/Metrics/Diagnostics/Audit，只定义 Instrumentation 可以报告的
技术事实和少量业务语义事实。后续由 Composition Root 注入真正的实现。
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol, runtime_checkable


@runtime_checkable
class InstrumentationHooks(Protocol):
    """自动埋点层使用的最小观测接口."""

    # FastAPI / HTTP -----------------------------------------------------
    def http_request_started(self, *, method: str, path: str) -> None:
        """HTTP 请求开始."""

    def http_request_finished(
        self,
        *,
        method: str,
        path: str,
        status_code: int,
        duration_seconds: float,
    ) -> None:
        """HTTP 请求正常完成."""

    def http_request_failed(
        self,
        *,
        method: str,
        path: str,
        duration_seconds: float,
        exception: Exception,
    ) -> None:
        """HTTP 请求因未处理异常失败."""

    # APScheduler --------------------------------------------------------
    def scheduler_started(self) -> None:
        """APScheduler 已启动."""

    def scheduler_stopped(self) -> None:
        """APScheduler 已停止."""

    def scheduler_job_missed(
        self,
        *,
        task_id: int,
        scheduled_run_time: datetime,
    ) -> None:
        """周期 Task 的一次计划执行发生 misfire."""

    def scheduler_job_max_instances(
        self,
        *,
        task_id: int,
        scheduled_run_times: tuple[datetime, ...],
    ) -> None:
        """Task 因 max_instances 限制未被提交执行."""

    # TaskRunner ---------------------------------------------------------
    def task_execution_started(self, *, task_id: int) -> None:
        """Task 实际执行开始."""

    def task_execution_succeeded(
        self,
        *,
        task_id: int,
        duration_seconds: float,
    ) -> None:
        """Task 实际执行成功."""

    def task_execution_failed(
        self,
        *,
        task_id: int,
        duration_seconds: float,
        exception: Exception,
    ) -> None:
        """Task 实际执行失败."""

    def task_execution_cancelled(
        self,
        *,
        task_id: int,
        duration_seconds: float,
    ) -> None:
        """Task 实际执行被取消."""

    # Semantic hooks -----------------------------------------------------
    def task_scheduled(self, *, task_id: int) -> None:
        """BlueCrystal Task 已成功注册/更新到调度器."""

    def task_removed(self, *, task_id: int) -> None:
        """BlueCrystal Task 已成功从调度器移除."""

    def task_paused(self, *, task_id: int) -> None:
        """BlueCrystal Task 已成功暂停."""

    def task_resumed(self, *, task_id: int) -> None:
        """BlueCrystal Task 已成功恢复."""

    def task_run_requested(self, *, task_id: int) -> None:
        """收到并成功提交一次立即执行请求."""


class NullInstrumentationHooks:
    """空实现.

    用于 Observability 尚未装配或测试只关注业务行为的场景。所有方法都是 no-op，
    从而使 Instrumentation 的接入可以保持可选。
    """

    def http_request_started(self, *, method: str, path: str) -> None:
        pass

    def http_request_finished(
        self,
        *,
        method: str,
        path: str,
        status_code: int,
        duration_seconds: float,
    ) -> None:
        pass

    def http_request_failed(
        self,
        *,
        method: str,
        path: str,
        duration_seconds: float,
        exception: Exception,
    ) -> None:
        pass

    def scheduler_started(self) -> None:
        pass

    def scheduler_stopped(self) -> None:
        pass

    def scheduler_job_missed(
        self,
        *,
        task_id: int,
        scheduled_run_time: datetime,
    ) -> None:
        pass

    def scheduler_job_max_instances(
        self,
        *,
        task_id: int,
        scheduled_run_times: tuple[datetime, ...],
    ) -> None:
        pass

    def task_execution_started(self, *, task_id: int) -> None:
        pass

    def task_execution_succeeded(
        self,
        *,
        task_id: int,
        duration_seconds: float,
    ) -> None:
        pass

    def task_execution_failed(
        self,
        *,
        task_id: int,
        duration_seconds: float,
        exception: Exception,
    ) -> None:
        pass

    def task_execution_cancelled(
        self,
        *,
        task_id: int,
        duration_seconds: float,
    ) -> None:
        pass

    def task_scheduled(self, *, task_id: int) -> None:
        pass

    def task_removed(self, *, task_id: int) -> None:
        pass

    def task_paused(self, *, task_id: int) -> None:
        pass

    def task_resumed(self, *, task_id: int) -> None:
        pass

    def task_run_requested(self, *, task_id: int) -> None:
        pass


def safe_observe(callback, /, *args, **kwargs) -> None:
    """执行一次观测回调，但绝不让观测失败覆盖业务行为.

    这里故意不再调用项目日志系统记录自身失败，避免 Observability 故障形成递归。
    后续如需要 fallback，可单独接入 stderr/health degradation 策略。
    """
    try:
        callback(*args, **kwargs)
    except Exception:
        pass
