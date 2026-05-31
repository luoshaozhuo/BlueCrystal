"""审计事件查询路由。

提供审计事件（IngestAuditEventOrm）的只读查询接口：
- 按 audit_id 查询单条审计事件；
- 分页查询审计事件列表，支持按 action 和 resource_type 过滤；
- 每次查询通过 access_evaluator 做权限检查；
- 查询操作本身也通过 audit_sink 记录审计事件；
- 事务边界：每次请求在 try/finally 中管理 session 生命周期。

管理资源：audit_event，路由前缀 /api/v1/audit-events。
严格只读：本模块不负责审计事件的写入（由 audit_middleware 和各路由 handler 负责）。
不负责：权限决策逻辑（access_evaluator 由 composition root 注入）、会话生命周期管理（由各 handler 自行打开/关闭）。
"""

from __future__ import annotations

from collections.abc import Callable

from fastapi import APIRouter, Query, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from whale.ingest.api.audit_middleware import build_audit_event
from whale.ingest.api.errors import denied, not_found
from whale.ingest.api.schemas import AuditEventResponse, PaginatedResponse
from whale.shared.persistence.orm import IngestAuditEventOrm

router = APIRouter(prefix="/api/v1/audit-events", tags=["audit-events"])


def _open_session(factory: Callable[[], Session]) -> Session:
    """打开数据库 session。

    调用 factory 可调用对象获取 SQLAlchemy Session。
    调用方负责在 finally 块中调用 session.close() 关闭会话，释放连接资源。

    Args:
        factory: SQLAlchemy sessionmaker 或其他返回 Session 的可调用对象。

    Returns:
        SQLAlchemy Session 对象，调用方必须关闭。

    Notes:
        不管理事务提交/回滚——本路由所有操作均为只读查询，仅做 close 释放。
        不负责权限检查或审计记录，这些逻辑由 handler 在 session 上下文内调用。
    """
    # callable() 守卫保留以兼容历史调用方可能传入已打开的 Session 对象
    return factory() if callable(factory) else factory()  # type: ignore[return-value]  # Session 分支仅用于防御性兼容，实际调用方仅传入 sessionmaker


def _authorize(request: Request, action: str, resource_id: str | None = None) -> None:
    """执行权限检查，未通过则抛出 denied 异常。

    每次审计事件查询前必须调用，确保调用方具备对 audit_event 资源的指定操作权限。
    权限判定逻辑由 access_evaluator 实现（composition root 注入），本函数仅做调用和异常转换。

    Args:
        request: FastAPI Request 对象，用于获取 app.state.access_evaluator。
        action: 操作标识，例如 "audit_event.read"、"audit_event.list"。
        resource_id: 受保护资源的主键标识，可选；未传入时检查资源类型级别的权限。

    Raises:
        denied: 当 access_evaluator 返回 False 时抛出，HTTP 状态映射由 errors.deny 决定。
    """
    if not request.app.state.access_evaluator(request, action, "audit_event", resource_id):
        raise denied(action=action, resource_type="audit_event", resource_id=resource_id)


def _response(row: IngestAuditEventOrm) -> AuditEventResponse:
    """将 IngestAuditEventOrm 转换为 API 响应模型 AuditEventResponse。

    本函数是纯数据映射，不执行以下操作：
    - 不修改 ORM 对象或数据库；
    - 不执行权限检查或审计记录；
    - 不提交事务或关闭 session。

    Args:
        row: IngestAuditEventOrm 实例，预期字段必须由 SQLAlchemy session 加载。
            映射字段：audit_id、request_id、actor、action、resource_type、
            resource_id、decision、result、reason_code、http_status、trace_id、
            client_ip、node_id、event_timestamp。

    Returns:
        AuditEventResponse 响应模型实例，event_timestamp 已转为 ISO 字符串。
    """
    return AuditEventResponse(
        audit_id=row.audit_id,
        request_id=row.request_id,
        actor=row.actor,
        action=row.action,
        resource_type=row.resource_type,
        resource_id=row.resource_id,
        decision=row.decision,
        result=row.result,
        reason_code=row.reason_code,
        http_status=row.http_status,
        trace_id=row.trace_id,
        client_ip=row.client_ip,
        node_id=row.node_id,
        event_timestamp=str(row.event_timestamp),
    )


@router.get("/{audit_id}", response_model=AuditEventResponse)
def get_audit_event(audit_id: int, request: Request) -> AuditEventResponse:
    """获取指定的资源记录。"""
    _authorize(request, "audit_event.read", str(audit_id))
    session = _open_session(request.app.state.session_factory)
    try:
        row = session.get(IngestAuditEventOrm, audit_id)
        if row is None:
            raise not_found(action="audit_event.read", resource_type="audit_event", resource_id=str(audit_id))
        request.app.state.audit_sink.emit(
            build_audit_event(request, action="audit_event.read", resource_type="audit_event", resource_id=str(audit_id), decision="ALLOW", result="SUCCESS", http_status=200)
        )
        return _response(row)
    finally:
        session.close()


@router.get("", response_model=PaginatedResponse[AuditEventResponse])
def list_audit_events(
    request: Request,
    
    action_filter: str | None = Query(None, alias="action"),
    resource_type: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> PaginatedResponse[AuditEventResponse]:
    """获取审计事件的分页列表。支持按字段过滤和分页参数。权限检查后查询。"""
    _authorize(request, "audit_event.list")
    session = _open_session(request.app.state.session_factory)
    try:
        query = select(IngestAuditEventOrm).order_by(IngestAuditEventOrm.event_timestamp.desc())
        count_query = select(func.count()).select_from(IngestAuditEventOrm)
        if action_filter:
            query = query.where(IngestAuditEventOrm.action == action_filter)
            count_query = count_query.where(IngestAuditEventOrm.action == action_filter)
        if resource_type:
            query = query.where(IngestAuditEventOrm.resource_type == resource_type)
            count_query = count_query.where(IngestAuditEventOrm.resource_type == resource_type)
        total = session.scalar(count_query) or 0
        rows = list(session.scalars(query.limit(limit).offset(offset)))
        items = [_response(r) for r in rows]
        request.app.state.audit_sink.emit(
            build_audit_event(request, action="audit_event.list", resource_type="audit_event", resource_id=None, decision="ALLOW", result="SUCCESS", http_status=200, attributes={"count": len(items), "total": total})
        )
        return PaginatedResponse(items=items, total=total, limit=limit, offset=offset)
    finally:
        session.close()
