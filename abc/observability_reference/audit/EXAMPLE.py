"""Audit capability 完整示例.

覆盖内容：
1. SQLiteAuditStore；
2. AuditService；
3. AuditInstrumentationHooks；
4. CompositeInstrumentationHooks；
5. HTTP Middleware 注入 request_id / actor / source；
6. @audit_action 声明 operation / target_type / target_arg / detail_args；
7. AuditedAPIRoute 自动判断 SUCCESS / FAILURE；
8. target_id 自动解析；
9. detail_args 白名单采集；
10. HTTP 异常自动写 error_type / error_message；
11. AuditQuery 各类筛选；
12. flush / close 生命周期；
13. AuditService 对敏感 detail 的脱敏能力；
14. AuditService.success()/failure() 底层 API 示例。

注意：
- Router 不显式调用 audit.success()/audit.failure()；
- direct service API 仅放在 ``demonstrate_low_level_api()`` 中展示底层能力。
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException, Query
from fastapi.encoders import jsonable_encoder

from observability_reference.audit import (
    AuditInstrumentationHooks,
    AuditQuery,
    AuditResult,
    AuditService,
    audit_action,
    install_fastapi_audit,
)
from observability_reference.audit.adapters import SQLiteAuditStore
from observability_reference.instrumentation import (
    CompositeInstrumentationHooks,
    install_fastapi_instrumentation,
)
from observability_reference.shared import (
    bind_observation_context,
    initialize_runtime_context,
)


# ---------------------------------------------------------------------------
# 1. Runtime Context
# ---------------------------------------------------------------------------

initialize_runtime_context(
    runtime_id="audit-example",
    node_id="local",
)


# ---------------------------------------------------------------------------
# 2. Store + Service + Hook
# ---------------------------------------------------------------------------

store = SQLiteAuditStore(
    Path("data/audit-example/audit.sqlite3")
)

audit = AuditService(
    [store],
    strict=False,
)

hooks = CompositeInstrumentationHooks(
    [
        AuditInstrumentationHooks(audit),
    ]
)


# ---------------------------------------------------------------------------
# 3. Minimal fake business state
# ---------------------------------------------------------------------------

TASKS: dict[int, dict[str, object]] = {
    1: {
        "paused": False,
        "mode": "normal",
    },
    2: {
        "paused": False,
        "mode": "normal",
    },
}


# ---------------------------------------------------------------------------
# 4. Lifecycle
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 展示底层 API；生产 Router 不应直接这么调用。
    demonstrate_low_level_api()

    try:
        yield
    finally:
        audit.flush()
        audit.close()


app = FastAPI(
    title="Audit Full Example",
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# 5. Install HTTP context first, then Audit route adapter
# ---------------------------------------------------------------------------

install_fastapi_instrumentation(
    app,
    hooks,
)

install_fastapi_audit(
    app,
    hooks,
)


# ---------------------------------------------------------------------------
# 6. Declarative SUCCESS
# ---------------------------------------------------------------------------

@app.post("/tasks/{task_id}/pause")
@audit_action(
    operation="task.pause",
    target_type="task",
    target_arg="task_id",
    detail_args=("reason", "ticket"),
)
async def pause_task(
    task_id: int,
    reason: str = Query("manual"),
    ticket: str | None = Query(None),
) -> dict[str, object]:
    """成功时自动产生 AuditResult.SUCCESS.

    示例：
        POST /tasks/1/pause?reason=maintenance&ticket=WO-001
        X-Actor: operator-a
        X-Request-ID: req-001
    """

    task = TASKS.get(task_id)
    if task is None:
        raise HTTPException(
            status_code=404,
            detail="task not found",
        )

    task["paused"] = True

    return {
        "task_id": task_id,
        "paused": True,
    }


# ---------------------------------------------------------------------------
# 7. Declarative HTTP failure: response.status_code >= 400
# ---------------------------------------------------------------------------

@app.post("/tasks/{task_id}/resume")
@audit_action(
    operation="task.resume",
    target_type="task",
    target_arg="task_id",
    detail_args=("reason",),
)
async def resume_task(
    task_id: int,
    reason: str = Query("manual"),
) -> dict[str, object]:
    """不存在的 task 会产生 FAILURE Audit."""

    task = TASKS.get(task_id)
    if task is None:
        raise HTTPException(
            status_code=404,
            detail="task not found",
        )

    task["paused"] = False

    return {
        "task_id": task_id,
        "paused": False,
    }


# ---------------------------------------------------------------------------
# 8. Declarative exception failure
# ---------------------------------------------------------------------------

@app.post("/tasks/{task_id}/explode")
@audit_action(
    operation="task.explode",
    target_type="task",
    target_arg="task_id",
    detail_args=("reason",),
)
async def explode_task(
    task_id: int,
    reason: str = Query("test"),
) -> None:
    """未处理异常自动写入 error_type/error_message."""

    raise RuntimeError(
        f"simulated failure for task {task_id}"
    )


# ---------------------------------------------------------------------------
# 9. target_arg can come from query parameter
# ---------------------------------------------------------------------------

@app.post("/tasks/select")
@audit_action(
    operation="task.select",
    target_type="task",
    target_arg="task_id",
    detail_args=("mode",),
)
async def select_task(
    task_id: int,
    mode: str = Query("normal"),
) -> dict[str, object]:
    """target_id 也可以从 query param 解析."""

    if task_id not in TASKS:
        raise HTTPException(
            status_code=404,
            detail="task not found",
        )

    TASKS[task_id]["mode"] = mode

    return {
        "task_id": task_id,
        "mode": mode,
    }


# ---------------------------------------------------------------------------
# 10. No decorator => no AuditRecord
# ---------------------------------------------------------------------------

@app.get("/health")
async def health() -> dict[str, bool]:
    """没有 @audit_action，因此不会产生审计记录."""

    return {"ok": True}


# ---------------------------------------------------------------------------
# 11. Query API: demonstrate all AuditQuery filters
# ---------------------------------------------------------------------------

@app.get("/audit")
async def query_audit(
    actor: str | None = None,
    source: str | None = None,
    operation: str | None = None,
    target_type: str | None = None,
    target_id: str | None = None,
    result: AuditResult | None = None,
    request_id: str | None = None,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    limit: int = 100,
):
    records = audit.query(
        AuditQuery(
            start_time=start_time,
            end_time=end_time,
            actor=actor,
            source=source,
            operation=operation,
            target_type=target_type,
            target_id=target_id,
            result=result,
            request_id=request_id,
            limit=limit,
        )
    )

    return jsonable_encoder(records)


# ---------------------------------------------------------------------------
# 12. Low-level API demonstration
# ---------------------------------------------------------------------------

def demonstrate_low_level_api() -> None:
    """展示 AuditService 底层能力，不是推荐的 Router 写法."""

    with bind_observation_context(
        request_id="bootstrap-audit-example",
        actor="system",
        source="startup",
        operation="runtime.bootstrap",
        target_type="runtime",
        target_id="audit-example",
    ):
        # success()
        success_record = audit.success(
            actor="system",
            source="startup",
            operation="runtime.bootstrap",
            target_type="runtime",
            target_id="audit-example",
            detail={
                "phase": "startup",
                # 将被 AuditService 自动脱敏。
                "api_key": "must-not-be-persisted",
                "nested": {
                    "password": "secret",
                    "safe": "visible",
                },
            },
        )

        print(
            "low-level success:",
            success_record.audit_id,
            dict(success_record.detail),
        )

        # failure()
        failure_record = audit.failure(
            actor="system",
            source="startup",
            operation="runtime.self_test",
            target_type="runtime",
            target_id="audit-example",
            detail={
                "phase": "self-test",
            },
            exception=RuntimeError(
                "simulated self-test failure"
            ),
        )

        print(
            "low-level failure:",
            failure_record.audit_id,
            failure_record.error_type,
            failure_record.error_message,
        )


# ---------------------------------------------------------------------------
# 13. Run
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
    )
