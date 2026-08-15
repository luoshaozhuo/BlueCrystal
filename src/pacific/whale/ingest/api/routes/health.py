"""管理 健康检查 资源的 API 路由。

每个 handler 在请求入口做权限检查（access_evaluator），
变更操作支持 dry_run 模式和乐观并发控制（expected_version），
所有操作通过 audit_sink 记录审计事件，
事务在 try/finally 中管理 Session 生命周期。

不负责：资源的业务逻辑编排（由 use case 层负责）。

/readyz 端点已升级为模块级就绪聚合，涵盖 runtime DB、Redis/StateCache、
Kafka/MessagePublisher、audit sink、access policy、shared_source runner、
source adapter registry 和 config/runtime mode。
"""

from __future__ import annotations

from fastapi import APIRouter, Request

from pacific.whale.ingest.api.audit_middleware import build_audit_event
from pacific.whale.ingest.api.readyz import build_readyz_response, evaluate_readiness

router = APIRouter()


@router.get("/healthz")
def healthz(request: Request) -> dict[str, str]:
    """返回服务存活状态。

    轻量存活检查：仅确认进程仍在运行并接受 HTTP 请求。
    不做任何依赖检查。

    Returns:
        {"status": "ok"} — 服务正在运行。
    """
    return {"status": "ok"}


@router.get("/readyz")
def readyz(request: Request) -> dict[str, object]:
    """执行模块级就绪聚合检查。

    依次检查以下组件的就绪状态：
    - runtime_db（必需，fail-closed）
    - redis_state_cache（必需，fail-closed）
    - message_publisher（必需，fail-closed）
    - audit_sink（可选，fail-open）
    - access_policy（可选，fail-open）
    - shared_source_runner（可选，fail-open）
    - source_adapter_registry（必需，fail-closed）
    - config_runtime_mode（必需，fail-closed）

    支持 degradation：optional 组件失败不影响 overall ready，
    required 组件失败导致 overall not_ready。

    响应不泄露内部 IP、密码、token 等敏感信息。

    Side effect:
        通过 audit_sink 写入审计事件记录就绪检查操作。

    Returns:
        {"status": "ready"|"degraded"|"not_ready", "checked_at": "...",
         "components": [...], "degraded_reasons": [...], "config_mode": "..."}
    """
    app_state = request.app.state

    # 收集可用的注入组件
    audit_sink = getattr(app_state, "audit_sink", None)
    access_policy = getattr(app_state, "access_policy", None)
    session_factory = getattr(app_state, "session_factory", None)

    # 执行聚合就绪检查
    aggregate = evaluate_readiness(
        session_factory=session_factory,
        audit_sink=audit_sink,
        access_policy=access_policy,
        acquisition_registry=getattr(app_state, "acquisition_registry", None),
        write_registry=getattr(app_state, "write_registry", None),
        redis_client=getattr(app_state, "redis_client", None),
        message_publisher=getattr(app_state, "message_publisher", None),
    )

    response = build_readyz_response(aggregate)

    # 写入审计事件
    if audit_sink is not None:
        audit_sink.emit(
            build_audit_event(
                request,
                action="readyz.read",
                resource_type="health",
                resource_id="readyz",
                decision="ALLOW",
                result="SUCCESS",
                http_status=200 if aggregate.overall in ("ready", "degraded") else 503,
            )
        )

    return response
