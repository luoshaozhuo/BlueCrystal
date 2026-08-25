"""APScheduler 3.x 技术事件与执行上下文 adapter。

第三方包没有 ``py.typed``，因此本模块用最小 Protocol 隔离动态边界；只观察
scheduler 已发生的事实，并在 Executor 的真实执行入口恢复上下文；不承担调度策略
或业务 Worker 日志。仅适配 AsyncIOExecutor 与 APScheduler ThreadPoolExecutor。
"""

from __future__ import annotations

import importlib
import sys
from collections.abc import Callable, Mapping
from threading import Lock
from typing import TYPE_CHECKING, Any, Protocol, cast

from apscheduler.executors.asyncio import AsyncIOExecutor
from apscheduler.executors.base import run_coroutine_job, run_job
from apscheduler.executors.pool import BasePoolExecutor, ThreadPoolExecutor
from apscheduler.util import iscoroutinefunction_partial

from ..context import (
    ObservationContext,
    bind_observation_context,
    bind_scheduler_execution_context,
)
from ..context.manager import resolve_parent_context
from ..logs import get_logger

if TYPE_CHECKING:
    from ..runtime import ObservabilityRuntime


class SchedulerEvent(Protocol):
    """listener 实际使用的 APScheduler event 最小契约。"""

    code: int


class JobEvent(SchedulerEvent, Protocol):
    """带 Job ID 的 APScheduler event 最小契约。"""

    job_id: str
    jobstore: str


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
EVENT_JOB_ADDED = cast(int, _events.EVENT_JOB_ADDED)
EVENT_JOB_REMOVED = cast(int, _events.EVENT_JOB_REMOVED)
EVENT_MASK = (
    EVENT_SCHEDULER_STARTED
    | EVENT_SCHEDULER_SHUTDOWN
    | EVENT_JOB_SUBMITTED
    | EVENT_JOB_EXECUTED
    | EVENT_JOB_ERROR
    | EVENT_JOB_MISSED
    | EVENT_JOB_MAX_INSTANCES
    | EVENT_JOB_ADDED
    | EVENT_JOB_REMOVED
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
        # 上下文快照依赖 add/remove 事件；调用方的日志事件过滤不能关闭传播基础设施。
        self._event_mask = event_mask | EVENT_JOB_ADDED | EVENT_JOB_REMOVED
        self._listener: Callable[[SchedulerEvent], None] | None = None
        self._runtime_context: ObservationContext | None = None
        self._job_contexts: dict[tuple[str, str], ObservationContext] = {}
        self._contexts_lock = Lock()
        self._context_executors_installed = False

    def install(self, runtime: ObservabilityRuntime) -> None:
        """注册 listener 并在 scheduler 启动前替换受支持的 Executor。"""
        if self._listener is not None or not self._enabled:
            return
        self._runtime_context = runtime.context
        self._install_context_executors()
        logger = get_logger(__name__)

        def listener(event: SchedulerEvent) -> None:
            """将单个第三方 event 转换为低基数指标和关联日志。"""
            event_name = _event_name(event.code)
            if event.code == EVENT_JOB_ADDED:
                job_event = cast(JobEvent, event)
                self._remember_job_context(
                    job_event.jobstore,
                    job_event.job_id,
                    resolve_parent_context(runtime.context),
                )
            elif event.code == EVENT_JOB_REMOVED:
                job_event = cast(JobEvent, event)
                self._forget_job_context(job_event.jobstore, job_event.job_id)
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
                    parent_context=resolve_parent_context(runtime.context),
                    job_id=str(resolved.get("job_id", job_event.job_id)),
                    source="scheduler",
                    attributes=attributes,
                ):
                    logger.info("scheduler_event", scheduler_event=event_name)
            else:
                with bind_observation_context(
                    parent_context=resolve_parent_context(runtime.context),
                    source="scheduler",
                ):
                    logger.info("scheduler_event", scheduler_event=event_name)

        self._scheduler.add_listener(listener, self._event_mask)
        self._listener = listener

    def uninstall(self) -> None:
        """移除 listener 并停用 Executor 上下文恢复；不接管 scheduler 生命周期。"""
        if self._listener is not None:
            self._scheduler.remove_listener(self._listener)
            self._listener = None
        self._runtime_context = None
        with self._contexts_lock:
            self._job_contexts.clear()

    def start(self) -> None:
        """Listener 不拥有 scheduler 生命周期，无需启动资源。"""

    def stop(self) -> None:
        """Listener 不拥有 scheduler 生命周期，无需停止资源。"""

    def status_details(self) -> dict[str, object]:
        """返回 Scheduler listener 与当前任务数的只读摘要。"""
        get_jobs = getattr(self._scheduler, "get_jobs", None)
        job_count = len(get_jobs()) if callable(get_jobs) else None
        return {
            "enabled": self._enabled,
            "listener_installed": self._listener is not None,
            "scheduler_running": bool(getattr(self._scheduler, "running", False)),
            "job_count": job_count,
            "context_executors_installed": self._context_executors_installed,
        }

    def _install_context_executors(self) -> None:
        """在启动前用共享底层资源的上下文版本替换受支持 Executor。"""
        scheduler = cast(Any, self._scheduler)
        if bool(getattr(scheduler, "running", False)):
            raise RuntimeError(
                "APScheduler context instrumentation must be installed before start"
            )
        executors = getattr(scheduler, "_executors", None)
        executors_lock = getattr(scheduler, "_executors_lock", None)
        create_default = getattr(scheduler, "_create_default_executor", None)
        if not isinstance(executors, dict) or executors_lock is None:
            # listener/status 的轻量替身没有 Executor 边界，仍可保留事件观测能力。
            return

        with executors_lock:
            if "default" not in executors:
                if not callable(create_default):
                    raise TypeError("apscheduler target cannot create its default executor")
                executors["default"] = create_default()
            for alias, executor in tuple(executors.items()):
                if isinstance(executor, _ContextAsyncIOExecutor) or isinstance(
                    executor, _ContextThreadPoolExecutor
                ):
                    continue
                if isinstance(executor, AsyncIOExecutor):
                    executors[alias] = _ContextAsyncIOExecutor(self._execution_context)
                    self._context_executors_installed = True
                elif isinstance(executor, ThreadPoolExecutor):
                    executors[alias] = _ContextThreadPoolExecutor(
                        cast(Any, executor)._pool,
                        self._execution_context,
                    )
                    self._context_executors_installed = True

    def _remember_job_context(
        self,
        jobstore: str,
        job_id: str,
        context: ObservationContext,
    ) -> None:
        """保存 add/replace job 调用流的不可变上下文快照。"""
        with self._contexts_lock:
            self._job_contexts[(jobstore, job_id)] = context

    def _forget_job_context(self, jobstore: str, job_id: str) -> None:
        """删除已移除 Job 的快照；已提交 Executor 的调用已持有自己的引用。"""
        with self._contexts_lock:
            self._job_contexts.pop((jobstore, job_id), None)

    def _execution_context(self, jobstore: str, job_id: str) -> ObservationContext | None:
        """为一次 Executor 提交返回快照，停用后返回 None 以恢复原生行为。"""
        runtime_context = self._runtime_context
        if runtime_context is None:
            return None
        with self._contexts_lock:
            return self._job_contexts.get((jobstore, job_id), runtime_context)


ExecutionContextProvider = Callable[[str, str], ObservationContext | None]


def _run_job_with_context(
    context: ObservationContext | None,
    job: Any,
    jobstore_alias: str,
    run_times: list[object],
    logger_name: str,
) -> list[object]:
    """在线程 Executor 入口恢复上下文，并保留 APScheduler 原始事件语义。"""
    if context is None:
        return cast(list[object], run_job(job, jobstore_alias, run_times, logger_name))
    with bind_scheduler_execution_context(
        parent_context=context,
        job_id=str(job.id),
    ):
        return cast(list[object], run_job(job, jobstore_alias, run_times, logger_name))


async def _run_coroutine_job_with_context(
    context: ObservationContext | None,
    job: Any,
    jobstore_alias: str,
    run_times: list[object],
    logger_name: str,
) -> list[object]:
    """在 asyncio Task 内恢复上下文，并保持取消与 JobEvent 生成方式不变。"""
    if context is None:
        return cast(
            list[object],
            await run_coroutine_job(job, jobstore_alias, run_times, logger_name),
        )
    with bind_scheduler_execution_context(
        parent_context=context,
        job_id=str(job.id),
    ):
        return cast(
            list[object],
            await run_coroutine_job(job, jobstore_alias, run_times, logger_name),
        )


class _ContextThreadPoolExecutor(BasePoolExecutor):
    """复用 APScheduler 线程池，并在工作线程中绑定调度执行上下文。
    
    因为当前 _ContextThreadPoolExecutor 继承的是 BasePoolExecutor，不是 APScheduler 
    已经实现好的 ThreadPoolExecutor一旦覆写 _do_submit_job()，就必须重复 APScheduler 原实现中的整套逻辑：
    - 提交 run_job
    - 注册 Future callback
    - 提取 Future 异常和 traceback
    - 调用 _run_job_error()
    - 调用 _run_job_success()
    - 将 JobEvent 交还给 Scheduler
    """

    def __init__(self, pool: object, context_provider: ExecutionContextProvider) -> None:
        """保存既有线程池，避免改变用户配置的 worker 数量与线程参数。"""
        super().__init__(pool)
        self._context_provider = context_provider

    def _do_submit_job(self, job: Any, run_times: list[object]) -> None:
        """提交带显式上下文参数的 run_job，并沿用 APScheduler 完成回调。"""
        context = self._context_provider(job._jobstore_alias, job.id)

        def callback(future: Any) -> None:
            """把 Future 结果转换回 APScheduler Executor 生命周期回调。"""
            exception, traceback = (
                future.exception_info()
                if hasattr(future, "exception_info")
                else (
                    future.exception(),
                    getattr(future.exception(), "__traceback__", None),
                )
            )
            if exception:
                self._run_job_error(job.id, exception, traceback)
            else:
                self._run_job_success(job.id, future.result())

        future = self._pool.submit(
            _run_job_with_context,
            context,
            job,
            job._jobstore_alias,
            run_times,
            self._logger.name,
        )
        future.add_done_callback(callback)


class _ContextAsyncIOExecutor(AsyncIOExecutor):
    """覆盖 AsyncIOExecutor 的协程 Task 与同步默认线程池两条执行路径。"""

    def __init__(self, context_provider: ExecutionContextProvider) -> None:
        """保存 Job 上下文提供器；event loop 仍由 scheduler.start() 注入。"""
        super().__init__()
        self._context_provider = context_provider

    def _do_submit_job(self, job: Any, run_times: list[object]) -> None:
        """按 Job 类型选择 Task 或线程池，并在真正执行时恢复上下文。"""
        context = self._context_provider(job._jobstore_alias, job.id)

        def callback(future: Any) -> None:
            """保持 AsyncIOExecutor 的 pending 集合与结果分派语义。"""
            self._pending_futures.discard(future)
            try:
                events = future.result()
            except BaseException:
                self._run_job_error(job.id, *sys.exc_info()[1:])
            else:
                self._run_job_success(job.id, events)

        if iscoroutinefunction_partial(job.func):
            coroutine = _run_coroutine_job_with_context(
                context,
                job,
                job._jobstore_alias,
                run_times,
                self._logger.name,
            )
            future = self._eventloop.create_task(coroutine)
        else:
            future = self._eventloop.run_in_executor(
                None,
                _run_job_with_context,
                context,
                job,
                job._jobstore_alias,
                run_times,
                self._logger.name,
            )
        future.add_done_callback(callback)
        self._pending_futures.add(future)


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
        EVENT_JOB_ADDED: "job_added",
        EVENT_JOB_REMOVED: "job_removed",
    }
    return names.get(code, "unknown")
