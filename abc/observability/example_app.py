"""observability_third_party 最小组合示例。"""
from __future__ import annotations
import asyncio
from fastapi import FastAPI
from .audit import AuditService,SQLiteAuditStore,audit_action
from .audit.fastapi import install_audit_routes
from .instrumentation import install_http_observability,wrap_task_runner
from .logs import configure_logging
from .shared import initialize_runtime_context
from .status import StatusService
from .trace import TraceManager,TracePolicy,configure_trace

async def business_runner(task_id:int)->None:
    await asyncio.sleep(0.01)
    if task_id==13: raise RuntimeError("simulated task failure")

def create_app()->FastAPI:
    configure_logging(level="INFO",log_file="./logs/bluecrystal.jsonl")
    initialize_runtime_context(node_id="node-01")
    policy=TracePolicy(normal_sample_rate=0.001)
    configure_trace(service_name="bluecrystal-ingest",policy=policy)
    trace=TraceManager(policy); status=StatusService(); audit=AuditService(SQLiteAuditStore("./audit.db"))
    runner=wrap_task_runner(business_runner,status=status,trace=trace)
    app=FastAPI(title="BlueCrystal Observability Third Party")
    install_audit_routes(app,audit,actor_resolver=lambda request:request.headers.get("x-actor"))
    install_http_observability(app,trace_policy=policy)
    @app.get("/health")
    async def health(): return {"status":"ok"}
    @app.post("/tasks/{task_id}/run")
    @audit_action(operation="task.run",target_type="task",target_arg="task_id")
    async def run_task(task_id:int): await runner(task_id); return {"task_id":task_id}
    @app.get("/status/tasks/{task_id}")
    async def task_status(task_id:int): return status.task(task_id)
    return app
app=create_app()
