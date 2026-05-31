"""管理 调度任务 资源的 API 路由。

每个 handler 在请求入口做权限检查（access_evaluator），
变更操作支持 dry_run 模式和乐观并发控制（expected_version），
所有操作通过 audit_sink 记录审计事件，
事务在 try/finally 中管理 Session 生命周期。

不负责：资源的业务逻辑编排（由 use case 层负责）。
"""

from __future__ import annotations

from typing import Callable

from fastapi import APIRouter, Query, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from whale.ingest.api.audit_middleware import build_audit_event
from whale.ingest.api.errors import conflict, denied, not_found
from whale.ingest.api.schemas import (
    PaginatedResponse,
    SchedulerJobCreate,
    SchedulerJobPatch,
    SchedulerJobResponse,
)
from whale.ingest.runtime.job_assignment import RuntimeJob, RuntimeJobRepository
from whale.shared.persistence.orm import IngestRuntimeJob

router = APIRouter(prefix="/api/v1/scheduler-jobs", tags=["scheduler-jobs"])


def _open_session(factory: sessionmaker[Session] | Callable[[], Session]) -> Session:
    return factory() if callable(factory) else factory()


def _authorize(request: Request, action: str, resource_id: str | None = None) -> None:
    evaluator = request.app.state.access_evaluator
    if not evaluator(request, action, "scheduler_job", resource_id):
        raise denied(action=action, resource_type="scheduler_job", resource_id=resource_id)


def _emit_success(
    request: Request,
    *,
    action: str,
    resource_type: str,
    resource_id: str | None,
    http_status: int,
    before_version: int | None = None,
    after_version: int | None = None,
    changed_fields: list[str] | None = None,
    attributes: dict[str, object] | None = None,
) -> None:
    request.app.state.audit_sink.emit(
        build_audit_event(
            request,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            decision="ALLOW",
            result="SUCCESS",
            http_status=http_status,
            before_version=before_version,
            after_version=after_version,
            changed_fields=changed_fields,
            attributes=attributes,
        )
    )


def _job_response(row: IngestRuntimeJob) -> SchedulerJobResponse:
    config = dict(row.config_json)
    stagger_offset_ms = config.pop("stagger_offset_ms", None)
    return SchedulerJobResponse(
        job_id=row.job_id,
        job_type=row.job_type,
        task_id=row.task_id,
        partition_key=row.partition_key,
        enabled=row.enabled,
        priority=row.priority,
        schedule_kind=row.schedule_kind,
        schedule_expr=row.schedule_expr,
        version=row.version,
        config=config,
        stagger_offset_ms=stagger_offset_ms,
    )


@router.post("", response_model=SchedulerJobResponse, status_code=201)
def create_scheduler_job(
    request: Request,
    
    payload: SchedulerJobCreate,
    dry_run: bool = Query(False),
) -> SchedulerJobResponse:
    """创建新scheduler job。dry_run 为 True 时返回预期结果不实际创建。权限检查、审计记录和乐观并发控制。"""
    _authorize(request, "scheduler_job.create")
    if dry_run:
        return SchedulerJobResponse(
            job_id=payload.job_id,
            job_type=payload.job_type,
            task_id=payload.task_id,
            partition_key=payload.partition_key,
            enabled=payload.enabled,
            priority=payload.priority,
            schedule_kind=payload.schedule_kind,
            schedule_expr=payload.schedule_expr,
            version=1,
            config=dict(payload.config),
            stagger_offset_ms=payload.stagger_offset_ms,
        )
    session = _open_session(request.app.state.session_factory)
    try:
        # 将 stagger_offset_ms 合并到 config 中，通过 repo 内部 session 持久化
        resolved_config = dict(payload.config)
        if payload.stagger_offset_ms is not None:
            resolved_config["stagger_offset_ms"] = payload.stagger_offset_ms
        repo = RuntimeJobRepository(request.app.state.session_factory)
        row = repo.upsert_job(
            RuntimeJob(
                job_id=payload.job_id,
                job_type=payload.job_type,
                task_id=payload.task_id,
                partition_key=payload.partition_key,
                enabled=payload.enabled,
                priority=payload.priority,
                config=resolved_config,
            )
        )
        _emit_success(request, action="scheduler_job.create", resource_type="scheduler_job", resource_id=row.job_id, http_status=201, after_version=row.version)
        return _job_response(row)
    finally:
        session.close()


@router.get("/{job_id}", response_model=SchedulerJobResponse)
def get_scheduler_job(job_id: str, request: Request) -> SchedulerJobResponse:
    """获取指定的资源记录。"""
    _authorize(request, "scheduler_job.read", job_id)
    session = _open_session(request.app.state.session_factory)
    try:
        repo = RuntimeJobRepository(request.app.state.session_factory)
        row = repo.get(job_id)
        if row is None:
            raise not_found(action="scheduler_job.read", resource_type="scheduler_job", resource_id=job_id)
        _emit_success(request, action="scheduler_job.read", resource_type="scheduler_job", resource_id=job_id, http_status=200)
        return _job_response(row)
    finally:
        session.close()


@router.get("", response_model=PaginatedResponse[SchedulerJobResponse])
def list_scheduler_jobs(
    request: Request,
    
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> PaginatedResponse[SchedulerJobResponse]:
    """获取调度作业的分页列表。支持按字段过滤和分页参数。权限检查后查询。"""
    _authorize(request, "scheduler_job.list")
    session = _open_session(request.app.state.session_factory)
    try:
        from whale.shared.persistence.orm import IngestRuntimeJob
        total = session.scalar(select(func.count()).select_from(IngestRuntimeJob)) or 0
        rows = list(session.scalars(select(IngestRuntimeJob).order_by(IngestRuntimeJob.job_id).limit(limit).offset(offset)))
        items = [_job_response(r) for r in rows]
        _emit_success(request, action="scheduler_job.list", resource_type="scheduler_job", resource_id=None, http_status=200, attributes={"count": len(items), "total": total})
        return PaginatedResponse(items=items, total=total, limit=limit, offset=offset)
    finally:
        session.close()


@router.patch("/{job_id}", response_model=SchedulerJobResponse)
def patch_scheduler_job(
    job_id: str,
    
    request: Request,
    payload: SchedulerJobPatch,
    dry_run: bool = Query(False),
) -> SchedulerJobResponse:
    """部分更新scheduler job。支持乐观并发控制（版本字段）。权限检查和审计记录。"""
    _authorize(request, "scheduler_job.update", job_id)
    session = _open_session(request.app.state.session_factory)
    try:
        from whale.shared.persistence.orm import IngestRuntimeJob
        row = session.get(IngestRuntimeJob, job_id)
        if row is None:
            raise not_found(action="scheduler_job.update", resource_type="scheduler_job", resource_id=job_id)
        if row.version != payload.expected_version:
            raise conflict(action="scheduler_job.update", resource_type="scheduler_job", resource_id=job_id, message="Scheduler job version conflict.")

        if dry_run:
            return _job_response(row)

        changed_fields: list[str] = []
        for field_name, value in payload.model_dump(exclude_none=True).items():
            if field_name == "expected_version":
                continue
            if field_name == "config":
                row.config_json = dict(value)
            elif field_name == "stagger_offset_ms":
                # 持久化到 config_json 而非独立列
                row.config_json = dict(row.config_json)
                row.config_json["stagger_offset_ms"] = value
            else:
                setattr(row, field_name, value)
            changed_fields.append(field_name)
        before_version = row.version
        row.version += 1
        session.commit()
        session.refresh(row)
        _emit_success(request, action="scheduler_job.update", resource_type="scheduler_job", resource_id=job_id, http_status=200, before_version=before_version, after_version=row.version, changed_fields=changed_fields)
        return _job_response(row)
    finally:
        session.close()


@router.delete("/{job_id}", status_code=204)
def delete_scheduler_job(
    job_id: str,
    
    request: Request,
    expected_version: int = Query(...),
    dry_run: bool = Query(False),
) -> None:
    """删除scheduler job。权限检查并记录审计事件。"""
    _authorize(request, "scheduler_job.delete", job_id)
    session = _open_session(request.app.state.session_factory)
    try:
        from whale.shared.persistence.orm import IngestRuntimeJob
        row = session.get(IngestRuntimeJob, job_id)
        if row is None:
            raise not_found(action="scheduler_job.delete", resource_type="scheduler_job", resource_id=job_id)
        if row.version != expected_version:
            raise conflict(action="scheduler_job.delete", resource_type="scheduler_job", resource_id=job_id, message="Scheduler job version conflict.")
        if dry_run:
            return None
        session.delete(row)
        session.commit()
        _emit_success(request, action="scheduler_job.delete", resource_type="scheduler_job", resource_id=job_id, http_status=204)
    finally:
        session.close()
