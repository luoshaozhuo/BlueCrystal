"""Runtime job and assignment models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Callable

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from whale.shared.persistence.orm import IngestJobAssignment, IngestRuntimeJob


@dataclass(slots=True)
class RuntimeJob:
    """Minimal scheduler-visible runtime job."""

    job_id: str
    job_type: str
    partition_key: str | None = None
    priority: int = 100
    enabled: bool = True
    task_id: int | None = None
    version: int = 1
    config: dict[str, object] = field(default_factory=dict)


@dataclass(slots=True)
class JobAssignment:
    """Minimal runtime assignment DTO."""

    job_id: str
    node_key: str
    active: bool = True
    assignment_version: int = 1
    assigned_at: datetime = field(default_factory=lambda: datetime.now(tz=UTC))


class RuntimeJobRepository:
    """Persist runtime jobs for scheduler discovery."""

    def __init__(self, session_factory: sessionmaker[Session] | Callable[[], Session]) -> None:
        self._session_factory = session_factory

    def upsert_job(self, job: RuntimeJob) -> IngestRuntimeJob:
        """Insert or update one runtime job row."""

        session = self._session_factory()
        try:
            row = session.get(IngestRuntimeJob, job.job_id)
            if row is None:
                row = IngestRuntimeJob(
                    job_id=job.job_id,
                    job_type=job.job_type,
                    task_id=job.task_id,
                    partition_key=job.partition_key,
                    enabled=job.enabled,
                    priority=job.priority,
                    version=job.version,
                    config_json=dict(job.config),
                )
                session.add(row)
            else:
                row.job_type = job.job_type
                row.task_id = job.task_id
                row.partition_key = job.partition_key
                row.enabled = job.enabled
                row.priority = job.priority
                row.version = job.version
                row.config_json = dict(job.config)
            session.commit()
            session.refresh(row)
            return row
        finally:
            session.close()

    def list_enabled_jobs(self) -> list[IngestRuntimeJob]:
        """Return all enabled jobs."""

        session = self._session_factory()
        try:
            return list(
                session.scalars(
                    select(IngestRuntimeJob)
                    .where(IngestRuntimeJob.enabled.is_(True))
                    .order_by(IngestRuntimeJob.priority, IngestRuntimeJob.job_id)
                )
            )
        finally:
            session.close()

    def get(self, job_id: str) -> IngestRuntimeJob | None:
        """Return one runtime job."""

        session = self._session_factory()
        try:
            return session.get(IngestRuntimeJob, job_id)
        finally:
            session.close()


class JobAssignmentRepository:
    """Persist job assignment rows."""

    def __init__(self, session_factory: sessionmaker[Session] | Callable[[], Session]) -> None:
        self._session_factory = session_factory

    def assign(self, assignment: JobAssignment) -> IngestJobAssignment:
        """Insert or update one assignment."""

        session = self._session_factory()
        try:
            row = session.execute(
                select(IngestJobAssignment).where(
                    IngestJobAssignment.job_id == assignment.job_id,
                    IngestJobAssignment.node_key == assignment.node_key,
                )
            ).scalar_one_or_none()
            if row is None:
                row = IngestJobAssignment(
                    job_id=assignment.job_id,
                    node_key=assignment.node_key,
                    active=assignment.active,
                    assignment_version=assignment.assignment_version,
                    assigned_at=assignment.assigned_at,
                )
                session.add(row)
            else:
                row.active = assignment.active
                row.assignment_version = assignment.assignment_version
                row.assigned_at = assignment.assigned_at
            session.commit()
            session.refresh(row)
            return row
        finally:
            session.close()

    def get_active_assignment(self, job_id: str) -> IngestJobAssignment | None:
        """Return the active assignment for one job."""

        session = self._session_factory()
        try:
            return session.execute(
                select(IngestJobAssignment)
                .where(
                    IngestJobAssignment.job_id == job_id,
                    IngestJobAssignment.active.is_(True),
                )
                .order_by(IngestJobAssignment.assignment_id.desc())
            ).scalar_one_or_none()
        finally:
            session.close()

    def list_active_assignments(self) -> list[IngestJobAssignment]:
        """Return all active assignments."""

        session = self._session_factory()
        try:
            return list(
                session.scalars(
                    select(IngestJobAssignment)
                    .where(IngestJobAssignment.active.is_(True))
                    .order_by(IngestJobAssignment.job_id, IngestJobAssignment.node_key)
                )
            )
        finally:
            session.close()

    def deactivate_job(self, job_id: str) -> None:
        """Deactivate all active assignments for one job."""

        session = self._session_factory()
        try:
            rows = list(
                session.scalars(
                    select(IngestJobAssignment).where(
                        IngestJobAssignment.job_id == job_id,
                        IngestJobAssignment.active.is_(True),
                    )
                )
            )
            for row in rows:
                row.active = False
                row.assignment_version += 1
            session.commit()
        finally:
            session.close()
