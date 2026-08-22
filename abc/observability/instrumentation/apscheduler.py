"""APScheduler 3.x 技术事件 listener adapter。

第三方包没有 ``py.typed``，因此本模块用最小 Protocol 隔离动态边界；只观察
scheduler 已发生的事实，不承担调度策略或业务 Worker 日志。
"""

from __future__ import annotations

import importlib
from collections.abc import Callable, Mapping
from typing import TYPE_CHECKING, Protocol, cast

from ..context import bind_observation_context
from ..logs import get_logger

if TYPE_CHECKING:
    from ..manager import ObservabilityRuntime


class SchedulerEvent(Protocol):
    """listener 实际使用的 APScheduler event 最小契约。"""

    code: int


class JobEvent(SchedulerEvent, Protocol):
    """带 Job ID 的 APScheduler event 最小契约。"""

    job_id: str


class SchedulerTarget(Protocol):
    """支持 listener 注册与移除的 scheduler 最小契约。"""

    def add_listener(self, callback: Callable[[SchedulerEvent], None], mask: int) -> None:
        """注册 listener。"""
        ...

    def remove_listener(self, callback: Callable[[SchedulerEvent], None]) -> None:
        """移除 listener。"""
        ...


_events = importlib.import_module("apscheduler.events")
EVENT_SCHEDULER_STARTED = cast(int, _events.EVENT_SCHEDULER_STARTED)
EVENT_SCHEDULER_SHUTDOWN = cast(int, _events.EVENT_SCHEDULER_SHUTDOWN)
EVENT_JOB_SUBMITTED = cast(int, _events.EVENT_JOB_SUBMITTED)
EVENT_JOB_EXECUTED = cast(int, _events.EVENT_JOB_EXECUTED)
EVENT_JOB_ERROR = cast(int, _events.EVENT_JOB_ERROR)
EVENT_JOB_MISSED = cast(int, _events.EVENT_JOB_MISSED)
EVENT_JOB_MAX_INSTANCES = cast(int, _events.EVENT_JOB_MAX_INSTANCES)
EVENT_MASK = (
    EVENT_SCHEDULER_STARTED
    | EVENT_SCHEDULER_SHUTDOWN
    | EVENT_JOB_SUBMITTED
    | EVENT_JOB_EXECUTED
    | EVENT_JOB_ERROR
    | EVENT_JOB_MISSED
    | EVENT_JOB_MAX_INSTANCES
)
JobIdentityResolver = Callable[[JobEvent], Mapping[str, object]]


class APSchedulerInstrumentation:
    """将 APScheduler 生命周期与执行结果连接到 Runtime backend。"""

    name = "apscheduler"

    def __init__(
        self,
        scheduler: object,
        *,
        enabled: bool = True,
        identity_resolver: JobIdentityResolver | None = None,
        event_mask: int = EVENT_MASK,
    ) -> None:
        """保存 scheduler 目标；listener 仅在 Runtime 启动时注册。"""
        if not hasattr(scheduler, "add_listener") or not hasattr(
            scheduler, "remove_listener"
        ):
            raise TypeError("apscheduler target must support listener lifecycle")
        self._scheduler = cast(SchedulerTarget, scheduler)
        self._enabled = enabled
        self._identity_resolver = identity_resolver
        self._event_mask = event_mask
        self._listener: Callable[[SchedulerEvent], None] | None = None

    def install(self, runtime: ObservabilityRuntime) -> None:
        """注册 listener；重复安装不会重复订阅。"""
        if self._listener is not None or not self._enabled:
            return
        logger = get_logger(__name__)

        def listener(event: SchedulerEvent) -> None:
            """将单个第三方 event 转换为低基数指标和关联日志。"""
            event_name = _event_name(event.code)
            if runtime.metrics is not None:
                runtime.metrics.scheduler_events.labels(event=event_name).inc()
                if event.code == EVENT_SCHEDULER_STARTED:
                    runtime.metrics.scheduler_running.set(1)
                elif event.code == EVENT_SCHEDULER_SHUTDOWN:
                    runtime.metrics.scheduler_running.set(0)
            if hasattr(event, "job_id"):
                job_event = cast(JobEvent, event)
                resolved = (
                    self._identity_resolver(job_event)
                    if self._identity_resolver
                    else {}
                )
                attributes = resolved.get("attributes", {})
                if not isinstance(attributes, Mapping):
                    raise TypeError("APScheduler identity attributes must be a mapping")
                with bind_observation_context(
                    job_id=str(resolved.get("job_id", job_event.job_id)),
                    source="scheduler",
                    attributes=attributes,
                ):
                    logger.info("scheduler_event", scheduler_event=event_name)
            else:
                logger.info("scheduler_event", scheduler_event=event_name)

        self._scheduler.add_listener(listener, self._event_mask)
        self._listener = listener

    def uninstall(self) -> None:
        """移除已注册 listener；未安装时为空操作。"""
        if self._listener is None:
            return
        self._scheduler.remove_listener(self._listener)
        self._listener = None

    def start(self) -> None:
        """Listener 不拥有 scheduler 生命周期，无需启动资源。"""

    def stop(self) -> None:
        """Listener 不拥有 scheduler 生命周期，无需停止资源。"""


def _event_name(code: int) -> str:
    """把 APScheduler 位事件码映射为低基数标签。"""
    names = {
        EVENT_SCHEDULER_STARTED: "scheduler_started",
        EVENT_SCHEDULER_SHUTDOWN: "scheduler_shutdown",
        EVENT_JOB_SUBMITTED: "job_submitted",
        EVENT_JOB_EXECUTED: "job_executed",
        EVENT_JOB_ERROR: "job_error",
        EVENT_JOB_MISSED: "job_missed",
        EVENT_JOB_MAX_INSTANCES: "job_max_instances",
    }
    return names.get(code, "unknown")
