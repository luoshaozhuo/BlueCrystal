"""Acquisition-task CRUD routes."""

from __future__ import annotations

from typing import Callable

from fastapi import APIRouter, Query, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from whale.ingest.api.audit_middleware import build_audit_event
from whale.ingest.api.errors import ApiError, conflict, denied, not_found
from whale.ingest.api.schemas import (
    AcquisitionTaskCreate,
    AcquisitionTaskPatch,
    PaginatedResponse,
    AcquisitionTaskResponse,
)
from whale.shared.persistence.orm import AcquisitionTask

router = APIRouter(prefix="/api/v1/acquisition-tasks", tags=["acquisition-tasks"])


def _open_session(factory: sessionmaker[Session] | Callable[[], Session]) -> Session:
    return factory() if callable(factory) else factory()


def _authorize(request: Request, action: str, resource_id: str | None = None) -> None:
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
