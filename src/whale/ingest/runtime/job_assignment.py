"""任务分配逻辑。

实现调度器与 worker 之间的任务分配策略，
包括分区键路由和作业亲和性。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Callable

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from whale.shared.persistence.orm import IngestJobAssignment, IngestRuntimeJob


@dataclass(slots=True)
class RuntimeJob:
    """调度器可见的最小运行时任务。"""

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
    """最小运行时分配 DTO。"""

    job_id: str
    node_key: str
    active: bool = True
    assignment_version: int = 1
    assigned_at: datetime = field(default_factory=lambda: datetime.now(tz=UTC))


class RuntimeJobRepository:
    """持久化运行时任务供调度器发现。"""

    def __init__(self, session_factory: sessionmaker[Session] | Callable[[], Session]) -> None:
        """初始化作业仓库。Args: session_factory: 数据库会话工厂。"""
        self._session_factory = session_factory

    def upsert_job(self, job: RuntimeJob) -> IngestRuntimeJob:
        """初始化作业仓库。Args: session_factory: 数据库会话工厂。"""
        """插入或更新一条运行时任务记录。"""

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
        """返回所有已启用的任务。"""

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
        """返回单个运行时任务。"""

        session = self._session_factory()
        try:
            return session.get(IngestRuntimeJob, job_id)
        finally:
            session.close()


class JobAssignmentRepository:
    """持久化任务分配记录。"""

    def __init__(self, session_factory: sessionmaker[Session] | Callable[[], Session]) -> None:
        """初始化作业仓库。Args: session_factory: 数据库会话工厂。"""
        self._session_factory = session_factory

    def assign(self, assignment: JobAssignment) -> IngestJobAssignment:
        """初始化作业仓库。Args: session_factory: 数据库会话工厂。"""
        """插入或更新一条分配记录。"""

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
        """返回单个任务的活跃分配。"""

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
        """返回所有活跃分配。"""

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
        """停用单个任务的所有活跃分配。"""

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
