"""分布式租约管理。

提供节点和写入操作的租约获取、续期和释放。
与 fencing 协作确保资源独占访问。

并发语义：
- fencing token 递增通过 FencingTokenRepository 的原子 UPSERT 保证无竞态条件。
- 租约表 INSERT 在并发场景下可能触发 IntegrityError（双节点同时创建同名租约），
  acquire 中将 IntegrityError 转换为 LEASE_CONFLICT 并回滚，避免未处理异常。
- 租约到期自动释放，防止死节点占用资源。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Callable

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from pacific.whale.shared.persistence.orm import IngestJobLease

from pacific.whale.ingest.runtime.fencing import FencingTokenRepository


@dataclass(frozen=True, slots=True)
class LeaseAcquireResult:
    """单次租约获取尝试的结果。"""

    acquired: bool
    lease_name: str
    holder_key: str
    fencing_token: int
    lease_id: int | None = None
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class JobLease:
    """租约服务返回的运行时租约快照。"""

    lease_name: str
    lease_scope: str
    resource_id: str
    holder_key: str
    fencing_token: int
    acquired_at: datetime
    renewed_at: datetime
    expires_at: datetime
    status: str

    @property
    def is_expired(self) -> bool:
        """返回租约是否已过期。"""

        return self.expires_at <= datetime.now(tz=UTC)


class LeaseRepository:
    """将租约持久化到运行时数据库。"""

    def __init__(self, session_factory: sessionmaker[Session] | Callable[[], Session]) -> None:
        """初始化租约仓库。Args: session_factory: 数据库会话工厂。"""
        self._session_factory = session_factory

    def get(self, lease_name: str) -> IngestJobLease | None:
        """初始化租约仓库。Args: session_factory: 数据库会话工厂。"""
        """按名称返回单行租约记录。"""

        session = self._session_factory()
        try:
            return session.execute(
                select(IngestJobLease).where(IngestJobLease.lease_name == lease_name)
            ).scalar_one_or_none()
        finally:
            session.close()

    def list_active(self) -> list[IngestJobLease]:
        """返回所有活跃租约。"""

        session = self._session_factory()
        try:
            return list(
                session.scalars(
                    select(IngestJobLease).where(IngestJobLease.status == "ACTIVE")
                )
            )
        finally:
            session.close()


class LeaseService:
    """运行时租约的获取、续期、释放和过期管理。

    并发安全：
    - fencing token 递增由 FencingTokenRepository.next_value 的原子 UPSERT 保证。
    - 租约 INSERT 在双节点并发时可能触发 IntegrityError（唯一约束冲突），
      acquire 捕获该异常并回滚，转换为 LEASE_CONFLICT 返回。
    - renew / release / expire_due_leases 使用显式寻址（lease_name），更新非 INSERT，
      不触发唯一约束冲突。
    """

    def __init__(
        self,
        session_factory: sessionmaker[Session] | Callable[[], Session],
        fencing_tokens: FencingTokenRepository,
    ) -> None:
        """初始化租约服务。

        Args:
            session_factory: 数据库会话工厂，每次调用返回独立 Session。
            fencing_tokens: 防脑裂 fencing token 仓库。
        """
        self._session_factory = session_factory
        self._fencing_tokens = fencing_tokens

    def acquire(
        self,
        *,
        lease_name: str,
        lease_scope: str,
        resource_id: str,
        holder_key: str,
        ttl_seconds: int,
        now: datetime | None = None,
    ) -> LeaseAcquireResult:
        """在租约不存在或已过期时获取租约。

        并发场景：双节点同时首次获取同一 lease_name 时，
        fencing token 递增由原子 UPSERT 保证无竞态条件；
        租约行 INSERT 若触发 IntegrityError（另一节点已抢占），
        则回滚并返回 LEASE_CONFLICT。

        Args:
            lease_name: 租约名称（如 write:resource-1）。
            lease_scope: 租约作用域（job / write）。
            resource_id: 资源标识。
            holder_key: 持有者标识（如节点 ID 或写入主键）。
            ttl_seconds: 租约 TTL，单位为秒。
            now: 当前时间，None 时使用 UTC 当前时间。

        Returns:
            LeaseAcquireResult，包含 acquired 状态、fencing_token、reason 等信息。
        """
        resolved_now = now or datetime.now(tz=UTC)
        session = self._session_factory()
        try:
            row = session.execute(
                select(IngestJobLease).where(IngestJobLease.lease_name == lease_name)
            ).scalar_one_or_none()
            if row is not None and row.status == "ACTIVE" and _as_utc(row.expires_at) > resolved_now:
                if row.holder_key != holder_key:
                    return LeaseAcquireResult(
                        acquired=False,
                        lease_name=lease_name,
                        holder_key=holder_key,
                        fencing_token=row.fencing_token,
                        reason="LEASE_CONFLICT",
                    )
                # 同一持有者重复 acquire 等同于 renew
                row.renewed_at = resolved_now
                row.expires_at = resolved_now + timedelta(seconds=ttl_seconds)
                row.version += 1
                session.commit()
                return LeaseAcquireResult(
                    acquired=True,
                    lease_name=lease_name,
                    holder_key=holder_key,
                    fencing_token=row.fencing_token,
                    lease_id=row.lease_id,
                )

            token = self._fencing_tokens.next_value(lease_name)
            if row is None:
                # 全新租约：INSERT。并发场景下另一节点可能已抢占此 lease_name，
                # 触发 IntegrityError，转换为 LEASE_CONFLICT。
                row = IngestJobLease(
                    lease_name=lease_name,
                    lease_scope=lease_scope,
                    resource_id=resource_id,
                    holder_key=holder_key,
                    status="ACTIVE",
                    fencing_token=token.value,
                    acquired_at=resolved_now,
                    renewed_at=resolved_now,
                    expires_at=resolved_now + timedelta(seconds=ttl_seconds),
                )
                session.add(row)
            else:
                # 过期的旧租约：UPDATE 复用现有行。此路径不会触发唯一约束冲突。
                row.lease_scope = lease_scope
                row.resource_id = resource_id
                row.holder_key = holder_key
                row.status = "ACTIVE"
                row.fencing_token = token.value
                row.acquired_at = resolved_now
                row.renewed_at = resolved_now
                row.expires_at = resolved_now + timedelta(seconds=ttl_seconds)
                row.released_at = None
                row.version += 1
            try:
                session.commit()
            except IntegrityError:
                session.rollback()
                return LeaseAcquireResult(
                    acquired=False,
                    lease_name=lease_name,
                    holder_key=holder_key,
                    fencing_token=token.value,
                    reason="LEASE_CONFLICT",
                )
            return LeaseAcquireResult(
                acquired=True,
                lease_name=lease_name,
                holder_key=holder_key,
                fencing_token=row.fencing_token,
                lease_id=row.lease_id,
            )
        finally:
            session.close()

    def renew(
        self,
        *,
        lease_name: str,
        holder_key: str,
        ttl_seconds: int,
        now: datetime | None = None,
    ) -> JobLease:
        """续期当前持有者的一个活跃租约。"""

        resolved_now = now or datetime.now(tz=UTC)
        session = self._session_factory()
        try:
            row = session.execute(
                select(IngestJobLease).where(IngestJobLease.lease_name == lease_name)
            ).scalar_one_or_none()
            if row is None or row.status != "ACTIVE":
                raise ValueError(f"Lease `{lease_name}` is not active.")
            if row.holder_key != holder_key:
                raise ValueError("Lease holder mismatch.")
            if _as_utc(row.expires_at) <= resolved_now:
                row.status = "EXPIRED"
                session.commit()
                raise ValueError("Lease already expired.")
            row.renewed_at = resolved_now
            row.expires_at = resolved_now + timedelta(seconds=ttl_seconds)
            row.version += 1
            session.commit()
            session.refresh(row)
            return _row_to_job_lease(row)
        finally:
            session.close()

    def release(
        self,
        *,
        lease_name: str,
        holder_key: str,
        now: datetime | None = None,
    ) -> JobLease:
        """释放指定持有者的一个活跃租约。"""

        resolved_now = now or datetime.now(tz=UTC)
        session = self._session_factory()
        try:
            row = session.execute(
                select(IngestJobLease).where(IngestJobLease.lease_name == lease_name)
            ).scalar_one_or_none()
            if row is None:
                raise ValueError(f"Lease `{lease_name}` does not exist.")
            if row.holder_key != holder_key:
                raise ValueError("Lease holder mismatch.")
            row.status = "RELEASED"
            row.released_at = resolved_now
            row.expires_at = resolved_now
            row.version += 1
            session.commit()
            session.refresh(row)
            return _row_to_job_lease(row)
        finally:
            session.close()

    def expire_due_leases(self, *, now: datetime | None = None) -> int:
        """将所有超期的活跃租约标记为已过期。"""

        resolved_now = now or datetime.now(tz=UTC)
        session = self._session_factory()
        try:
            rows = list(
                session.scalars(
                    select(IngestJobLease).where(
                        IngestJobLease.status == "ACTIVE",
                        IngestJobLease.expires_at <= resolved_now,
                    )
                )
            )
            for row in rows:
                row.status = "EXPIRED"
                row.version += 1
            session.commit()
            return len(rows)
        finally:
            session.close()

    def force_expire(self, *, lease_name: str, now: datetime | None = None) -> JobLease:
        """强制将一个租约置为过期状态，用于故障切换路径。"""

        resolved_now = now or datetime.now(tz=UTC)
        session = self._session_factory()
        try:
            row = session.execute(
                select(IngestJobLease).where(IngestJobLease.lease_name == lease_name)
            ).scalar_one_or_none()
            if row is None:
                raise ValueError(f"Lease `{lease_name}` does not exist.")
            row.status = "EXPIRED"
            row.expires_at = resolved_now
            row.released_at = resolved_now
            row.version += 1
            session.commit()
            session.refresh(row)
            return _row_to_job_lease(row)
        finally:
            session.close()

    def get_snapshot(self, *, lease_name: str) -> JobLease | None:
        """返回规范化后的租约快照。"""

        row = LeaseRepository(self._session_factory).get(lease_name)
        return None if row is None else _row_to_job_lease(row)

    def validate_execution(
        self,
        *,
        lease_name: str,
        holder_key: str,
        fencing_token: int,
        now: datetime | None = None,
    ) -> bool:
        """返回持有者是否可在给定 fencing token 下执行。"""

        resolved_now = now or datetime.now(tz=UTC)
        lease = self.get_snapshot(lease_name=lease_name)
        if lease is None:
            return False
        if lease.status != "ACTIVE":
            return False
        if lease.holder_key != holder_key:
            return False
        if lease.fencing_token != fencing_token:
            return False
        if lease.expires_at <= resolved_now:
            return False
        return True


def _row_to_job_lease(row: IngestJobLease) -> JobLease:
    return JobLease(
        lease_name=row.lease_name,
        lease_scope=row.lease_scope,
        resource_id=row.resource_id,
        holder_key=row.holder_key,
        fencing_token=row.fencing_token,
        acquired_at=_as_utc(row.acquired_at),
        renewed_at=_as_utc(row.renewed_at),
        expires_at=_as_utc(row.expires_at),
        status=row.status,
    )


def _as_utc(value: datetime) -> datetime:
    """将 SQLAlchemy/SQLite 日期时间规范化为 aware UTC 时间戳。"""

    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
