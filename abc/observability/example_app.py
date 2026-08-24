"""FastAPI、APScheduler 与 Worker 的单机完整可观测性示例。

HTTP 指标和 span 由现有第三方 instrumentation 产生；本模块只负责组合真实
scheduler、业务 Worker、显式管理边界及查询 API。所有线程和 telemetry 资源都
绑定到 FastAPI lifespan，模块导入不会启动 scheduler 或创建数据库。
"""

from __future__ import annotations

import os
import importlib
from collections.abc import AsyncGenerator, Callable, Mapping
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from threading import Lock
from typing import Any, TypeVar, cast

import uvicorn
from fastapi import FastAPI, HTTPException, Query, Request

from .audit import AuditQuery, AuditRecord, AuditResult, audit_action
from .audit.fastapi import install_audit_routes
from .instrumentation import observe_scheduler_action
from .instrumentation.fastapi import DEFAULT_ACTOR_RESOLVER, resolve_actor_resolver
from .logs import get_logger
from .runtime import create_observability

R = TypeVar("R")
DEFAULT_CONFIG_PATH = Path(__file__).parent / "config" / "observability.yaml"
# APScheduler 3.x 未发布 py.typed；动态边界只保留两个示例实际构造器。
BackgroundScheduler = cast(
    Any,
    importlib.import_module("apscheduler.schedulers.background").BackgroundScheduler,
)
DateTrigger = cast(
    Any,
    importlib.import_module("apscheduler.triggers.date").DateTrigger,
)


@dataclass(slots=True)
class _ExecutionState:
    """保存示例 scheduler 执行结果；锁只保护演示状态，不参与业务调度。"""

    succeeded: int = 0
    failed: int = 0
    last_task_id: int | None = None
    _lock: Lock = field(default_factory=Lock)

    def record(self, task_id: int, *, succeeded: bool) -> None:
        """记录一次已结束的 scheduler Worker 执行。

        Args:
            task_id: 已执行的业务任务标识。
            succeeded: Worker 是否成功返回。
        """
        with self._lock:
            if succeeded:
                self.succeeded += 1
            else:
                self.failed += 1
            self.last_task_id = task_id

    def snapshot(self) -> dict[str, int | None]:
        """返回不会暴露内部锁的状态快照。

        Returns:
            成功数、失败数和最后任务标识。
        """
        with self._lock:
            return {
                "succeeded": self.succeeded,
                "failed": self.failed,
                "last_task_id": self.last_task_id,
            }


def business_runner(
    task_id: int,
    *,
    job_id: str | None = None,
    fail: bool = False,
) -> int:
    """执行示例业务，并由业务代码自行记录步骤日志。

    Args:
        task_id: 示例业务任务标识。
        job_id: 可选调度任务标识，仅用于业务日志补充信息。
        fail: 是否触发代表性业务失败。

    Returns:
        原样返回任务标识。

    Raises:
        ValueError: ``fail`` 为真时模拟业务校验失败。
    """
    logger = get_logger(__name__)
    logger.info("business_task_started", task_id=task_id, scheduled_job_id=job_id)
    if fail:
        logger.error(
            "business_task_failed",
            task_id=task_id,
            scheduled_job_id=job_id,
            failure_reason="requested_example_failure",
        )
        raise ValueError("requested example failure")
    logger.info("business_task_completed", task_id=task_id, scheduled_job_id=job_id)
    return task_id


def create_app(config_path: str | Path) -> FastAPI:
    """从 YAML 创建完整示例应用，但把资源启动推迟到 lifespan。

    Args:
        config_path: observability YAML 路径；SQLite 相对路径以该文件目录为基准。

    Returns:
        已安装结构 instrumentation、尚未启动运行资源的 FastAPI 应用。
    """
    runtime = create_observability(config_path)
    actor_strategy = (
        runtime.config.instrumentation.get_options("fastapi").options.get(
            "actor_resolver", DEFAULT_ACTOR_RESOLVER
        )
    )
    selected_actor_resolver = resolve_actor_resolver(actor_strategy)
    scheduler = BackgroundScheduler()
    execution_state = _ExecutionState()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        """依次启动 Runtime/scheduler，并在退出时严格逆序释放。

        Args:
            app: 当前 FastAPI 应用；生命周期资源已由闭包持有。

        Yields:
            scheduler 正在运行的应用生命周期阶段。
        """
        scheduler_started = False
        await runtime.start()
        try:
            scheduler.start()
            scheduler_started = True
            yield
        finally:
            try:
                if scheduler_started:
                    scheduler.shutdown(wait=True)
            finally:
                await runtime.close()

    app = FastAPI(
        title="Observability Complete Example",
        description=(
            "本地展示 HTTP、Scheduler、Worker、Logging、Metrics、Trace 与 Audit。"
        ),
        lifespan=lifespan,
    )
    if runtime.audit is not None:
        install_audit_routes(
            app,
            runtime.audit,
            actor_resolver=selected_actor_resolver,
        )

    runner = runtime.instrument_worker(
        "example.task.execute",
        business_runner,
        resolver=lambda task_id, job_id=None, fail=False: {
            "job_id": job_id or f"direct:{task_id}",
            "attributes": {
                "example.task.id": task_id,
                "example.task.fail": fail,
            },
        },
    )

    def scheduled_entrypoint(task_id: int, job_id: str, fail: bool) -> int:
        """从 APScheduler 进入同一 Worker wrapper，并记录演示状态。

        Args:
            task_id: 业务任务标识。
            job_id: APScheduler job 标识。
            fail: 是否请求代表性业务失败。

        Returns:
            Worker 原始返回值。
        """
        try:
            result = runner(task_id, job_id=job_id, fail=fail)
        except Exception:
            # APScheduler 仍接收原异常并产生 job_error listener 事件。
            execution_state.record(task_id, succeeded=False)
            raise
        execution_state.record(task_id, succeeded=True)
        return result

    def scheduler_action(
        *,
        operation: str,
        job_id: str,
        action: Callable[[], R],
        detail: Mapping[str, object] | None = None,
    ) -> R:
        """把示例管理 API 收敛到通用 scheduler trace/audit 边界。

        Args:
            operation: 稳定管理操作名。
            job_id: 被管理 job 标识。
            action: 实际 APScheduler 管理调用。
            detail: 写入审计的低风险结构化详情。

        Returns:
            原管理调用返回值。
        """
        observed = observe_scheduler_action(
            runtime,
            operation=operation,
            target_type="job",
            target_id=job_id,
            action=action,
            detail=detail,
        )
        return observed()

    @app.get("/")
    def describe_example() -> dict[str, object]:
        """列出单机闭环能力和主要观察入口。

        Returns:
            示例名称、HTTP 入口和进程输出说明。
        """
        return {
            "name": "observability-complete-example",
            "endpoints": {
                "direct_worker": "POST /tasks/{task_id}/run",
                "create_schedule": "POST /schedules/{job_id}",
                "run_now": "POST /schedules/{job_id}/run-now",
                "audit": "GET /audit",
                "metrics": "GET /metrics",
                "health": "GET /health",
            },
            "process_output": ["structured business logs", "console OTel spans"],
        }

    @app.get("/health")
    def health() -> dict[str, object]:
        """返回应用、scheduler 与示例执行状态。

        Returns:
            scheduler 运行状态、待执行 job 和本地执行计数。
        """
        return {
            "status": "ok",
            "scheduler_running": scheduler.running,
            "scheduled_jobs": [job.id for job in scheduler.get_jobs()],
            "scheduler_executions": execution_state.snapshot(),
        }

    @app.post("/tasks/{task_id}/run")
    @audit_action(
        operation="task.run",
        target_type="task",
        target_arg="task_id",
        detail_args=("fail",),
    )
    def run_task(task_id: int, fail: bool = False) -> dict[str, int]:
        """直接触发经过 instrumentation 的业务 Worker。

        Args:
            task_id: 业务任务标识。
            fail: 是否请求示例失败。

        Returns:
            Worker 返回的任务标识。
        """
        return {"task_id": runner(task_id, fail=fail)}

    @app.post("/schedules/{job_id}")
    def create_schedule(
        job_id: str,
        task_id: int,
        delay_seconds: float = Query(default=30.0, gt=0, le=86_400),
        fail: bool = False,
    ) -> dict[str, object]:
        """创建一次性真实 APScheduler 任务。

        Args:
            job_id: 新 job 的稳定标识。
            task_id: 传给 Worker 的业务标识。
            delay_seconds: 首次执行前等待秒数。
            fail: 是否让被调度 Worker 模拟失败。

        Returns:
            job 标识与计划执行时间。
        """
        run_date = datetime.now(timezone.utc) + timedelta(seconds=delay_seconds)
        detail = {
            "task_id": task_id,
            "delay_seconds": delay_seconds,
            "fail": fail,
        }
        job = scheduler_action(
            operation="schedule.create",
            job_id=job_id,
            detail=detail,
            action=lambda: scheduler.add_job(
                scheduled_entrypoint,
                trigger=DateTrigger(run_date=run_date),
                id=job_id,
                args=(task_id, job_id, fail),
            ),
        )
        return {
            "job_id": job.id,
            "next_run_time": job.next_run_time.isoformat(),
        }

    @app.post("/schedules/{job_id}/run-now")
    def run_schedule_now(job_id: str) -> dict[str, str]:
        """把现有任务的下次执行时间调整为当前时刻。

        Args:
            job_id: 待触发 job 标识。

        Returns:
            已接受触发的状态。
        """
        scheduler_action(
            operation="schedule.run_now",
            job_id=job_id,
            action=lambda: scheduler.modify_job(
                job_id,
                next_run_time=datetime.now(timezone.utc),
            ),
        )
        return {"job_id": job_id, "status": "triggered"}

    @app.post("/schedules/{job_id}/pause")
    def pause_schedule(job_id: str) -> dict[str, str]:
        """暂停现有任务并记录管理审计。

        Args:
            job_id: 待暂停 job 标识。

        Returns:
            暂停状态。
        """
        scheduler_action(
            operation="schedule.pause",
            job_id=job_id,
            action=lambda: scheduler.pause_job(job_id),
        )
        return {"job_id": job_id, "status": "paused"}

    @app.post("/schedules/{job_id}/resume")
    def resume_schedule(job_id: str) -> dict[str, str]:
        """恢复已暂停任务并记录管理审计。

        Args:
            job_id: 待恢复 job 标识。

        Returns:
            恢复状态。
        """
        scheduler_action(
            operation="schedule.resume",
            job_id=job_id,
            action=lambda: scheduler.resume_job(job_id),
        )
        return {"job_id": job_id, "status": "resumed"}

    @app.delete("/schedules/{job_id}")
    def remove_schedule(job_id: str) -> dict[str, str]:
        """移除现有任务并记录管理审计。

        Args:
            job_id: 待移除 job 标识。

        Returns:
            移除状态。
        """
        scheduler_action(
            operation="schedule.remove",
            job_id=job_id,
            action=lambda: scheduler.remove_job(job_id),
        )
        return {"job_id": job_id, "status": "removed"}

    @app.get("/audit")
    def query_audit(
        operation: str | None = None,
        target_type: str | None = None,
        target_id: str | None = None,
        actor: str | None = None,
        result: AuditResult | None = None,
        limit: int = Query(default=100, gt=0, le=1_000),
    ) -> list[dict[str, object]]:
        """按小型过滤条件查询本地 SQLite 审计记录。

        Args:
            operation: 可选操作名。
            target_type: 可选目标类型。
            target_id: 可选目标标识。
            actor: 可选操作者。
            result: 可选成功或失败结果。
            limit: 有上限的返回数量。

        Returns:
            可直接编码为 JSON 的审计记录列表。
        """
        if runtime.audit is None:
            raise HTTPException(status_code=503, detail="audit backend is disabled")
        records = runtime.audit.query(
            AuditQuery(
                operation=operation,
                target_type=target_type,
                target_id=target_id,
                actor=actor,
                result=result,
                limit=limit,
            )
        )
        return [_audit_record_payload(record) for record in records]

    runtime.instrument_fastapi(app, actor_resolver=selected_actor_resolver)
    runtime.instrument_apscheduler(scheduler)
    app.state.observability = runtime
    app.state.scheduler = scheduler
    app.state.scheduler_execution_state = execution_state
    return app


def _audit_record_payload(record: AuditRecord) -> dict[str, object]:
    """把不可变 AuditRecord 转为稳定的 HTTP JSON 结构。

    Args:
        record: 领域审计记录。

    Returns:
        时间、枚举和只读映射均已转换的响应字典。
    """
    return {
        "audit_id": record.audit_id,
        "timestamp": record.timestamp.isoformat(),
        "service_name": record.service_name,
        "service_instance_id": record.service_instance_id,
        "request_id": record.request_id,
        "actor": record.actor,
        "source": record.source,
        "operation": record.operation,
        "target_type": record.target_type,
        "target_id": record.target_id,
        "result": record.result.value,
        "detail": dict(record.detail),
        "error_type": record.error_type,
        "error_message": record.error_message,
    }


def create_default_app() -> FastAPI:
    """使用环境变量覆盖路径或包内示例 YAML 创建 Uvicorn factory。

    Returns:
        尚未进入 lifespan 的完整示例应用。
    """
    config_path = Path(os.getenv("OBSERVABILITY_CONFIG_PATH", DEFAULT_CONFIG_PATH))
    return create_app(config_path)


def main() -> None:
    """以正确 factory 模式启动示例，供 ``python -m`` 直接运行。"""
    reload_enabled = os.getenv("OBSERVABILITY_EXAMPLE_RELOAD", "false").lower() in {
        "1",
        "true",
        "yes",
    }
    uvicorn.run(
        "observability.example_app:create_default_app",
        factory=True,
        reload=reload_enabled,
        host=os.getenv("OBSERVABILITY_EXAMPLE_HOST", "127.0.0.1"),
        port=int(os.getenv("OBSERVABILITY_EXAMPLE_PORT", "8000")),
    )


if __name__ == "__main__":
    main()
