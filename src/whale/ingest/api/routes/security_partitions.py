"""Security-partition CRUD routes for ingest runtime API."""

from __future__ import annotations

from typing import Callable

from fastapi import APIRouter, Query, Request
from sqlalchemy import JSON, Column, DateTime, Integer, String, func, select
from sqlalchemy.orm import Session, sessionmaker

from whale.ingest.api.audit_middleware import build_audit_event
from whale.ingest.api.errors import conflict, denied, not_found
from whale.ingest.api.schemas import (
    PaginatedResponse,
    SecurityPartitionCreate,
    SecurityPartitionPatch,
    SecurityPartitionResponse,
)
from whale.shared.persistence import Base

router = APIRouter(prefix="/api/v1/security-partitions", tags=["security-partitions"])


class SecurityPartitionOrm(Base):
    """Lightweight security partition model for CRUD."""

    __tablename__ = "ingest_security_partition"
    __table_args__ = {"extend_existing": True}

    partition_id = Column(Integer, primary_key=True, autoincrement=True)
    partition_code = Column(String(64), nullable=False, unique=True)
    partition_name = Column(String(255), nullable=False)
    security_zone = Column(String(64), nullable=False, default="UNCLASSIFIED")
    direction = Column(String(32), nullable=False, default="READ_ONLY")
    description = Column(String(512), nullable=True)
    rules_json = Column(JSON, nullable=False, default=dict)
    record_version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


def _open_session(factory):
    return factory() if callable(factory) else factory()


def _authorize(request, action, resource_id=None):
    if not request.app.state.access_evaluator(request, action, "security_partition", resource_id):
        raise denied(action=action, resource_type="security_partition", resource_id=resource_id)


def _emit_success(request, *, action, resource_type, resource_id, http_status, **kw):
    request.app.state.audit_sink.emit(
        build_audit_event(
            request, action=action, resource_type=resource_type,
            resource_id=resource_id, decision="ALLOW", result="SUCCESS",
            http_status=http_status, **kw,
        )
    )


def _response(row) -> SecurityPartitionResponse:
    return SecurityPartitionResponse(
        partition_id=row.partition_id,
        partition_code=row.partition_code,
        partition_name=row.partition_name,
        security_zone=row.security_zone,
        direction=row.direction,
        description=row.description,
        rules_json=dict(row.rules_json),
        version=row.record_version,
    )


@router.post("", response_model=SecurityPartitionResponse, status_code=201)
def create_security_partition(
    request: Request,
    payload: SecurityPartitionCreate,
    dry_run: bool = Query(False),
) -> SecurityPartitionResponse:
    _authorize(request, "security_partition.create")
    session = _open_session(request.app.state.session_factory)
    try:
        if dry_run:
            return SecurityPartitionResponse(
                partition_id=0,
                partition_code=payload.partition_code,
                partition_name=payload.partition_name,
                security_zone=payload.security_zone,
                direction=payload.direction,
                description=payload.description,
                rules_json=dict(payload.rules_json),
                version=1,
            )
        row = SecurityPartitionOrm(
            partition_code=payload.partition_code,
            partition_name=payload.partition_name,
            security_zone=payload.security_zone,
            direction=payload.direction,
            description=payload.description,
            rules_json=dict(payload.rules_json),
            record_version=1,
        )
        session.add(row)
        session.commit()
        session.refresh(row)
        _emit_success(request, action="security_partition.create", resource_type="security_partition", resource_id=row.partition_code, http_status=201)
        return _response(row)
    finally:
        session.close()


@router.get("/{partition_id}", response_model=SecurityPartitionResponse)
def get_security_partition(partition_id: int, request: Request) -> SecurityPartitionResponse:
    _authorize(request, "security_partition.read", str(partition_id))
    session = _open_session(request.app.state.session_factory)
    try:
        row = session.get(SecurityPartitionOrm, partition_id)
        if row is None:
            raise not_found(action="security_partition.read", resource_type="security_partition", resource_id=str(partition_id))
        _emit_success(request, action="security_partition.read", resource_type="security_partition", resource_id=str(partition_id), http_status=200)
        return _response(row)
    finally:
        session.close()


@router.get("", response_model=PaginatedResponse[SecurityPartitionResponse])
def list_security_partitions(
    request: Request,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> PaginatedResponse[SecurityPartitionResponse]:
    _authorize(request, "security_partition.list")
    session = _open_session(request.app.state.session_factory)
    try:
        total = session.scalar(select(func.count()).select_from(SecurityPartitionOrm)) or 0
        rows = list(session.scalars(select(SecurityPartitionOrm).order_by(SecurityPartitionOrm.partition_id).limit(limit).offset(offset)))
        items = [_response(r) for r in rows]
        _emit_success(request, action="security_partition.list", resource_type="security_partition", resource_id=None, http_status=200, attributes={"count": len(items), "total": total})
        return PaginatedResponse(items=items, total=total, limit=limit, offset=offset)
    finally:
        session.close()


@router.patch("/{partition_id}", response_model=SecurityPartitionResponse)
def patch_security_partition(partition_id: int, request: Request, payload: SecurityPartitionPatch, dry_run: bool = Query(False)) -> SecurityPartitionResponse:
    _authorize(request, "security_partition.update", str(partition_id))
    session = _open_session(request.app.state.session_factory)
    try:
        row = session.get(SecurityPartitionOrm, partition_id)
        if row is None:
            raise not_found(action="security_partition.update", resource_type="security_partition", resource_id=str(partition_id))
        if row.record_version != payload.expected_version:
            raise conflict(action="security_partition.update", resource_type="security_partition", resource_id=str(partition_id), message="Version conflict.")
        if dry_run:
            return _response(row)
        changed_fields: list[str] = []
        for field_name, value in payload.model_dump(exclude_none=True).items():
            if field_name == "expected_version":
                continue
            setattr(row, field_name, value)
            changed_fields.append(field_name)
        row.record_version += 1
        session.commit()
        session.refresh(row)
        _emit_success(request, action="security_partition.update", resource_type="security_partition", resource_id=str(partition_id), http_status=200, after_version=row.record_version, changed_fields=changed_fields)
        return _response(row)
    finally:
        session.close()


@router.delete("/{partition_id}", status_code=204)
def delete_security_partition(partition_id: int, request: Request, expected_version: int = Query(...), dry_run: bool = Query(False)) -> None:
    _authorize(request, "security_partition.delete", str(partition_id))
    session = _open_session(request.app.state.session_factory)
    try:
        row = session.get(SecurityPartitionOrm, partition_id)
        if row is None:
            raise not_found(action="security_partition.delete", resource_type="security_partition", resource_id=str(partition_id))
        if row.record_version != expected_version:
            raise conflict(action="security_partition.delete", resource_type="security_partition", resource_id=str(partition_id), message="Version conflict.")
        if dry_run:
            return None
        session.delete(row)
        session.commit()
        _emit_success(request, action="security_partition.delete", resource_type="security_partition", resource_id=str(partition_id), http_status=204)
    finally:
        session.close()
