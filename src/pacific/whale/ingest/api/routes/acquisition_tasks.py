"""采集任务 CRUD 路由。

管理 ingestion 采集任务（AcquisitionTask）的全生命周期：
- 创建/查询/更新/删除任务；
- 权限检查通过 access_evaluator 统一拦截；
- 每次变更通过 audit_sink 记录审计事件；
- dry_run 参数支持试运行模式，跳过持久化但返回预期结果；
- 更新/删除使用 expected_version 做乐观并发控制，版本冲突返回 409；
- 每个请求在 try/finally 中管理 SQLAlchemy session 生命周期，确保连接归还。

不负责：任务的实际调度执行（由 scheduler/worker 负责），
协议层的采集适配器调用（由 usecase 层完成）。
"""

from __future__ import annotations

from typing import Callable

from fastapi import APIRouter, Query, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from pacific.whale.ingest.api.audit_middleware import build_audit_event
from pacific.whale.ingest.api.errors import conflict, denied, not_found
from pacific.whale.ingest.api.schemas import (
    AcquisitionTaskCreate,
    AcquisitionTaskPatch,
    PaginatedResponse,
    AcquisitionTaskResponse,
)
from pacific.whale.shared.persistence.orm import AcquisitionTask

router = APIRouter(prefix="/api/v1/acquisition-tasks", tags=["acquisition-tasks"])


def _open_session(factory: sessionmaker[Session] | Callable[[], Session]) -> Session:
    """打开数据库 session，兼容 sessionmaker 和 callable 两种工厂。

    调用方必须在 finally 块中 close session。
    """
    return factory() if callable(factory) else factory()


def _authorize(request: Request, action: str, resource_id: str | None = None) -> None:
    """调用 access_evaluator 做权限检查，未通过则抛出 denied 异常。

    Args:
        request: FastAPI Request，其 app.state.access_evaluator 提供权限判断。
        action: 操作名，如 "acquisition_task.create"。
        resource_id: 资源标识，可为 None。
    """
    evaluator = request.app.state.access_evaluator
    allowed = evaluator(request, action, "acquisition_task", resource_id)
    if not allowed:
        raise denied(action=action, resource_type="acquisition_task", resource_id=resource_id)


@router.post("", response_model=AcquisitionTaskResponse, status_code=201)
def create_acquisition_task(
    request: Request,
    payload: AcquisitionTaskCreate,
    dry_run: bool = Query(False),
) -> AcquisitionTaskResponse:
    """创建采集任务。

    权限检查：调用 _authorize 验证 acquisition_task.create 权限。
    审计记录：成功创建后通过 audit_sink.emit 记录审计事件，包含 changed_fields 和 after_version。
    dry_run：为 True 时返回预期结果（task_id=0, version=1），但不持久化也不记录审计。
    事务边界：在 try/finally 中管理 session；commit 后 refresh。
    冲突处理：task_name 重复返回 409。
    """
    _authorize(request, "acquisition_task.create")
    session = _open_session(request.app.state.session_factory)
    try:
        existing = session.execute(
            select(AcquisitionTask).where(AcquisitionTask.task_name == payload.task_name)
        ).scalar_one_or_none()
        if existing is not None:
            raise conflict(
                action="acquisition_task.create",
                resource_type="acquisition_task",
                resource_id=existing.task_name,
                message=f"Acquisition task `{payload.task_name}` already exists.",
            )
        if dry_run:
            return AcquisitionTaskResponse(
                task_id=0,
                task_name=payload.task_name,
                ld_instance_id=payload.ld_instance_id,
                acquisition_mode=payload.acquisition_mode,
                task_status="STOPPED",
                request_timeout_ms=payload.request_timeout_ms,
                poll_interval_ms=payload.poll_interval_ms,
                enabled=payload.enabled,
                priority=payload.priority,
                partition_key=payload.partition_key,
                assignment_policy=payload.assignment_policy,
                protocol_params=dict(payload.protocol_params),
                version=1,
            )
        row = AcquisitionTask(
            task_name=payload.task_name,
            ld_instance_id=payload.ld_instance_id,
            acquisition_mode=payload.acquisition_mode,
            task_status="STOPPED",
            request_timeout_ms=payload.request_timeout_ms,
            poll_interval_ms=payload.poll_interval_ms,
            enabled=payload.enabled,
            priority=payload.priority,
            partition_key=payload.partition_key,
            assignment_policy=payload.assignment_policy,
            protocol_params=dict(payload.protocol_params),
            version=1,
        )
        session.add(row)
        session.commit()
        session.refresh(row)
        request.app.state.audit_sink.emit(
            build_audit_event(
                request,
                action="acquisition_task.create",
                resource_type="acquisition_task",
                resource_id=str(row.task_id),
                decision="ALLOW",
                result="SUCCESS",
                http_status=201,
                after_version=row.version,
                changed_fields=list(payload.model_dump().keys()),
            )
        )
        return AcquisitionTaskResponse.from_orm_row(row)
    finally:
        session.close()


@router.get("/{task_id}", response_model=AcquisitionTaskResponse)
def get_acquisition_task(task_id: int, request: Request) -> AcquisitionTaskResponse:
    """查询单个采集任务。

    权限检查：验证 acquisition_task.read 权限。
    审计记录：成功读取后记录审计事件，包含 after_version。
    事务边界：try/finally 管理 session 生命周期。
    错误处理：任务不存在返回 404。
    """
    _authorize(request, "acquisition_task.read", str(task_id))
    session = _open_session(request.app.state.session_factory)
    try:
        row = session.get(AcquisitionTask, task_id)
        if row is None:
            raise not_found(
                action="acquisition_task.read",
                resource_type="acquisition_task",
                resource_id=str(task_id),
            )
        request.app.state.audit_sink.emit(
            build_audit_event(
                request,
                action="acquisition_task.read",
                resource_type="acquisition_task",
                resource_id=str(task_id),
                decision="ALLOW",
                result="SUCCESS",
                http_status=200,
                after_version=row.version,
            )
        )
        return AcquisitionTaskResponse.from_orm_row(row)
    finally:
        session.close()


@router.get("", response_model=PaginatedResponse[AcquisitionTaskResponse])
def list_acquisition_tasks(
    request: Request,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> PaginatedResponse[AcquisitionTaskResponse]:
    """分页查询采集任务列表。

    权限检查：验证 acquisition_task.list 权限。
    审计记录：记录查询审计事件，包含 count、total、limit、offset。
    事务边界：try/finally 管理 session。
    """
    _authorize(request, "acquisition_task.list")
    session = _open_session(request.app.state.session_factory)
    try:
        total = session.scalar(select(func.count()).select_from(AcquisitionTask)) or 0
        rows = list(
            session.scalars(
                select(AcquisitionTask)
                .order_by(AcquisitionTask.task_id)
                .limit(limit)
                .offset(offset)
            )
        )
        request.app.state.audit_sink.emit(
            build_audit_event(
                request,
                action="acquisition_task.list",
                resource_type="acquisition_task",
                resource_id=None,
                decision="ALLOW",
                result="SUCCESS",
                http_status=200,
                attributes={"count": len(rows), "total": total, "limit": limit, "offset": offset},
            )
        )
        return PaginatedResponse(
            items=[AcquisitionTaskResponse.from_orm_row(row) for row in rows],
            total=total,
            limit=limit,
            offset=offset,
        )
    finally:
        session.close()


@router.patch("/{task_id}", response_model=AcquisitionTaskResponse)
def patch_acquisition_task(
    task_id: int,
    payload: AcquisitionTaskPatch,
    request: Request,
    dry_run: bool = Query(False),
) -> AcquisitionTaskResponse:
    """更新采集任务（部分字段）。

    权限检查：验证 acquisition_task.update 权限。
    乐观并发：通过 expected_version 做版本检查，版本不匹配返回 409。
    dry_run：为 True 时跳过持久化，返回当前行不做修改。
    审计记录：成功更新后记录 before_version、after_version、changed_fields。
    事务边界：try/finally 管理 session；commit 前 version += 1，commit 后 refresh。
    错误处理：任务不存在返回 404，版本冲突返回 409。
    """
    _authorize(request, "acquisition_task.update", str(task_id))
    session = _open_session(request.app.state.session_factory)
    try:
        row = session.get(AcquisitionTask, task_id)
        if row is None:
            raise not_found(
                action="acquisition_task.update",
                resource_type="acquisition_task",
                resource_id=str(task_id),
            )
        if row.version != payload.expected_version:
            raise conflict(
                action="acquisition_task.update",
                resource_type="acquisition_task",
                resource_id=str(task_id),
                message="Acquisition task version conflict.",
                changed_fields=list(payload.model_dump(exclude_none=True).keys()),
            )
        if dry_run:
            return AcquisitionTaskResponse.from_orm_row(row)
        changed_fields: list[str] = []
        for field_name, value in payload.model_dump(exclude_none=True).items():
            if field_name == "expected_version":
                continue
            setattr(row, field_name, value)
            changed_fields.append(field_name)
        before_version = row.version
        row.version += 1
        session.commit()
        session.refresh(row)
        request.app.state.audit_sink.emit(
            build_audit_event(
                request,
                action="acquisition_task.update",
                resource_type="acquisition_task",
                resource_id=str(task_id),
                decision="ALLOW",
                result="SUCCESS",
                http_status=200,
                before_version=before_version,
                after_version=row.version,
                changed_fields=changed_fields,
            )
        )
        return AcquisitionTaskResponse.from_orm_row(row)
    finally:
        session.close()


@router.delete("/{task_id}", status_code=204)
def delete_acquisition_task(
    task_id: int,
    request: Request,
    expected_version: int = Query(...),
    dry_run: bool = Query(False),
) -> None:
    """删除采集任务。

    权限检查：验证 acquisition_task.delete 权限。
    乐观并发：必须提供 expected_version，版本不匹配返回 409。
    dry_run：为 True 时不执行删除，直接返回 None。
    审计记录：成功删除后记录审计事件，包含 before_version。
    事务边界：try/finally 管理 session；commit 后不 refresh（行已删除）。
    错误处理：任务不存在返回 404，版本冲突返回 409。
    """
    _authorize(request, "acquisition_task.delete", str(task_id))
    session = _open_session(request.app.state.session_factory)
    try:
        row = session.get(AcquisitionTask, task_id)
        if row is None:
            raise not_found(
                action="acquisition_task.delete",
                resource_type="acquisition_task",
                resource_id=str(task_id),
            )
        if row.version != expected_version:
            raise conflict(
                action="acquisition_task.delete",
                resource_type="acquisition_task",
                resource_id=str(task_id),
                message="Acquisition task version conflict.",
            )
        if dry_run:
            return None
        before_version = row.version
        session.delete(row)
        session.commit()
        request.app.state.audit_sink.emit(
            build_audit_event(
                request,
                action="acquisition_task.delete",
                resource_type="acquisition_task",
                resource_id=str(task_id),
                decision="ALLOW",
                result="SUCCESS",
                http_status=204,
                before_version=before_version,
            )
        )
    finally:
        session.close()
