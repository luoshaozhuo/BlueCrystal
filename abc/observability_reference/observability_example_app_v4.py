"""FastAPI + APScheduler + Observability Reference v0_8.

关键规则：
1. Context 只在 Middleware / Wrapper / Route Adapter / semantic helper 边界注入；
2. Hook 不再重复传 request_id/task_id/method/path/actor 等 Context 数据；
3. Audit 进入统一 CompositeInstrumentationHooks。
"""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.encoders import jsonable_encoder

from observability_reference.audit import (
    AuditInstrumentationHooks,
    AuditQuery,
    AuditService,
    audit_action,
    install_fastapi_audit,
)
from observability_reference.audit.adapters import SQLiteAuditStore
from observability_reference.diagnostics import (
    DiagnosticInstrumentationHooks,
    DiagnosticService,
    InMemoryDiagnosticStore,
)
from observability_reference.instrumentation import (
    CompositeInstrumentationHooks,
    install_apscheduler_instrumentation,
    install_fastapi_instrumentation,
    instrument_task_runner,
    instrument_task_scheduler,
)
from observability_reference.logs import LogInstrumentationHooks, LogService
from observability_reference.logs.adapters import ConsoleLogSink, RollingFileLogSink
from observability_reference.metrics import (
    InMemoryMetricRegistry,
    MetricInstrumentationHooks,
    MetricService,
)
from observability_reference.shared import initialize_runtime_context
from observability_reference.task_scheduler_reference import (
    ScheduledTaskNotFoundError,
    TaskScheduler,
)


TASK_ID = 1
RECURRING_JOB_ID = f"task:{TASK_ID}"

initialize_runtime_context(
    runtime_id="observability-reference-demo",
    node_id="local",
)

logs = LogService(
    [
        ConsoleLogSink(),
        RollingFileLogSink(
            Path("data/observability-reference/app.log"),
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
            Path("data/observability-reference/audit.sqlite3")
        )
    ],
    strict=False,
)

hooks = CompositeInstrumentationHooks(
    [
        LogInstrumentationHooks(logs),
        MetricInstrumentationHooks(metrics),
        DiagnosticInstrumentationHooks(diagnostics),
        AuditInstrumentationHooks(audit),
    ]
)


async def demo_task(task_id: int) -> None:
    """真实业务 Task 不主动操作 ObservationContext."""

    print(f"demo task running: task_id={task_id}")
    await asyncio.sleep(1)


observed_task = instrument_task_runner(
    demo_task,
    hooks,
)

raw_scheduler = TaskScheduler(observed_task)

install_apscheduler_instrumentation(
    raw_scheduler.apscheduler,
    hooks,
)

scheduler = instrument_task_scheduler(
    raw_scheduler,
    hooks,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    diagnostics.runtime_starting()

    scheduler.schedule_interval(
        TASK_ID,
        interval_ms=5000,
    )

    scheduler.start()
    diagnostics.runtime_started()

    try:
        yield
    finally:
        diagnostics.runtime_stopping()

        if scheduler.running:
            scheduler.stop()

        diagnostics.runtime_stopped()
        audit.flush()
        audit.close()
        logs.flush()
        logs.close()


app = FastAPI(
    title="Observability Reference v0_8",
    lifespan=lifespan,
)

# 统一 HTTP Middleware 同时建立：
# request_id / method / path / actor / source
install_fastapi_instrumentation(
    app,
    hooks,
)

# Audit Adapter 不再持有 AuditService，只产生统一 Hook。
install_fastapi_audit(
    app,
    hooks,
)


@app.get("/")
async def root() -> dict[str, object]:
    return {
        "name": "observability-reference-v0_8",
        "task_id": TASK_ID,
        "interval_seconds": 5,
    }


@app.post("/tasks/{task_id}/run")
@audit_action(
    operation="task.run",
    target_type="task",
    target_arg="task_id",
)
async def run_task_once(task_id: int) -> dict[str, object]:
    scheduler.run_now(task_id)

    return {
        "task_id": task_id,
        "submitted": True,
    }


@app.post("/tasks/{task_id}/pause")
@audit_action(
    operation="task.pause",
    target_type="task",
    target_arg="task_id",
)
async def pause_task(task_id: int) -> dict[str, object]:
    try:
        scheduler.pause(task_id)
    except ScheduledTaskNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail="task not found",
        ) from exc


    return {
        "task_id": task_id,
        "paused": True,
    }


@app.post("/tasks/{task_id}/resume")
@audit_action(
    operation="task.resume",
    target_type="task",
    target_arg="task_id",
)
async def resume_task(task_id: int) -> dict[str, object]:
    try:
        scheduler.resume(task_id)
    except ScheduledTaskNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail="task not found",
        ) from exc


    return {
        "task_id": task_id,
        "paused": False,
    }


@app.get("/metrics")
async def get_metrics():
    return jsonable_encoder(metrics.snapshot())


@app.get("/diagnostics/runtime")
async def get_runtime_diagnostic():
    return jsonable_encoder(diagnostics.runtime())


@app.get("/diagnostics/scheduler")
async def get_scheduler_diagnostic():
    return jsonable_encoder(diagnostics.scheduler())


@app.get("/diagnostics/tasks/{task_id}")
async def get_task_diagnostic(task_id: int):
    diagnostic = diagnostics.task(task_id)

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
