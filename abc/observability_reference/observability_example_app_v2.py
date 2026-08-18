"""FastAPI + APScheduler + Observability 最小完整示例（声明式 Audit）."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

import uvicorn
from apscheduler.jobstores.base import JobLookupError
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, HTTPException
from fastapi.encoders import jsonable_encoder

from deploy.observability.audit import (
    AuditQuery,
    AuditService,
    audit_action,
    install_fastapi_audit,
)
from deploy.observability.audit.adapters import SQLiteAuditStore
from deploy.observability.diagnostics import (
    DiagnosticInstrumentationHooks,
    DiagnosticService,
    InMemoryDiagnosticStore,
)
from deploy.observability.instrumentation import (
    CompositeInstrumentationHooks,
    install_apscheduler_instrumentation,
    install_fastapi_instrumentation,
    instrument_task_runner,
    safe_observe,
)
from deploy.observability.logs import LogInstrumentationHooks, LogService
from deploy.observability.logs.adapters import ConsoleLogSink, RollingFileLogSink
from deploy.observability.metrics import (
    InMemoryMetricRegistry,
    MetricInstrumentationHooks,
    MetricService,
)
from deploy.observability.shared import initialize_runtime_context


TASK_ID = 1
RECURRING_JOB_ID = f"task:{TASK_ID}"

initialize_runtime_context(
    runtime_id="observability-demo",
    node_id="local",
)

logs = LogService(
    [
        ConsoleLogSink(),
        RollingFileLogSink(
            Path("data/observability-demo/app.log"),
            max_bytes=5 * 1024 * 1024,
            backup_count=3,
        ),
    ]
)

metrics = MetricService(InMemoryMetricRegistry())
diagnostics = DiagnosticService(InMemoryDiagnosticStore())

audit = AuditService(
    [
        SQLiteAuditStore(
            Path("data/observability-demo/audit.sqlite3")
        )
    ],
    strict=False,
)

hooks = CompositeInstrumentationHooks(
    [
        LogInstrumentationHooks(logs),
        MetricInstrumentationHooks(metrics),
        DiagnosticInstrumentationHooks(diagnostics),
    ]
)


async def demo_task(task_id: int) -> None:
    """示例业务任务：不依赖 Observability."""
    print(f"demo task running: task_id={task_id}")
    await asyncio.sleep(1)


observed_task = instrument_task_runner(
    demo_task,
    hooks,
)

scheduler = AsyncIOScheduler()

install_apscheduler_instrumentation(
    scheduler,
    hooks,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    diagnostics.runtime_starting()

    scheduler.add_job(
        observed_task,
        trigger="interval",
        seconds=5,
        id=RECURRING_JOB_ID,
        args=(TASK_ID,),
        max_instances=1,
        coalesce=False,
        replace_existing=True,
    )
    safe_observe(
        hooks.task_scheduled,
        task_id=TASK_ID,
    )

    scheduler.start()
    diagnostics.runtime_started()

    try:
        yield
    finally:
        diagnostics.runtime_stopping()

        if scheduler.running:
            scheduler.shutdown(wait=False)

        diagnostics.runtime_stopped()

        audit.flush()
        audit.close()
        logs.flush()
        logs.close()


app = FastAPI(
    title="Observability Minimal Example",
    lifespan=lifespan,
)

# 先安装通用 HTTP Observability，再安装声明式 Audit。
# 两者都必须在需要 Audit 的 Route 注册之前完成。
install_fastapi_instrumentation(
    app,
    hooks,
)

install_fastapi_audit(
    app,
    audit,
)


@app.get("/")
async def root() -> dict[str, object]:
    return {
        "name": "observability-minimal-example",
        "task_id": TASK_ID,
        "interval_seconds": 5,
    }


@app.post("/tasks/1/run")
@audit_action(
    operation="task.run",
    target_type="task",
    target_arg=None,
)
async def run_task_once() -> dict[str, object]:
    scheduler.add_job(
        observed_task,
        trigger="date",
        run_date=datetime.now(timezone.utc),
        args=(TASK_ID,),
    )

    safe_observe(
        hooks.task_run_requested,
        task_id=TASK_ID,
    )

    return {
        "task_id": TASK_ID,
        "submitted": True,
    }


@app.post("/tasks/1/pause")
@audit_action(
    operation="task.pause",
    target_type="task",
    target_arg=None,
)
async def pause_task() -> dict[str, object]:
    try:
        scheduler.pause_job(RECURRING_JOB_ID)
    except JobLookupError as exc:
        raise HTTPException(
            status_code=404,
            detail="task not found",
        ) from exc

    safe_observe(
        hooks.task_paused,
        task_id=TASK_ID,
    )

    return {
        "task_id": TASK_ID,
        "paused": True,
    }


@app.post("/tasks/1/resume")
@audit_action(
    operation="task.resume",
    target_type="task",
    target_arg=None,
)
async def resume_task() -> dict[str, object]:
    try:
        scheduler.resume_job(RECURRING_JOB_ID)
    except JobLookupError as exc:
        raise HTTPException(
            status_code=404,
            detail="task not found",
        ) from exc

    safe_observe(
        hooks.task_resumed,
        task_id=TASK_ID,
    )

    return {
        "task_id": TASK_ID,
        "paused": False,
    }


@app.get("/metrics")
async def get_metrics():
    return jsonable_encoder(
        metrics.snapshot()
    )


@app.get("/diagnostics/runtime")
async def get_runtime_diagnostic():
    return jsonable_encoder(
        diagnostics.runtime()
    )


@app.get("/diagnostics/scheduler")
async def get_scheduler_diagnostic():
    return jsonable_encoder(
        diagnostics.scheduler()
    )


@app.get("/diagnostics/tasks/1")
async def get_task_diagnostic():
    diagnostic = diagnostics.task(TASK_ID)

    if diagnostic is None:
        raise HTTPException(
            status_code=404,
            detail="task diagnostic not found",
        )

    return jsonable_encoder(diagnostic)


@app.get("/audit")
async def get_audit():
    return jsonable_encoder(
        audit.query(
            AuditQuery(limit=100)
        )
    )


if __name__ == "__main__":
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
    )
