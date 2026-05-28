"""DB-backed lease helpers for scheduler jobs and write control."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Callable

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from whale.shared.persistence.orm import IngestJobLease

from whale.ingest.runtime.fencing import FencingTokenRepository


@dataclass(frozen=True, slots=True)
class LeaseAcquireResult:
    """Result of one lease acquisition attempt."""

    acquired: bool
    lease_name: str
    holder_key: str
    fencing_token: int
    lease_id: int | None = None
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class JobLease:
    """Runtime lease snapshot returned by the lease service."""

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
        """Return whether the lease is already expired."""

        return self.expires_at <= datetime.now(tz=UTC)


class LeaseRepository:
    """Persist leases into the runtime DB."""

    def __init__(self, session_factory: sessionmaker[Session] | Callable[[], Session]) -> None:
        self._session_factory = session_factory

    def get(self, lease_name: str) -> IngestJobLease | None:
        """Return one lease row by name."""

        session = self._session_factory()
        try:
            return session.execute(
                select(IngestJobLease).where(IngestJobLease.lease_name == lease_name)
            ).scalar_one_or_none()
        finally:
            session.close()

    def list_active(self) -> list[IngestJobLease]:
        """Return all active leases."""

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
    """Acquire, renew, release, and expire runtime leases."""

    def __init__(
        self,
        session_factory: sessionmaker[Session] | Callable[[], Session],
        fencing_tokens: FencingTokenRepository,
    ) -> None:
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
        """Acquire one lease when absent or expired."""

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
            session.commit()
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
        """Renew one active lease held by the current holder."""

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
        """Release one active lease held by the given holder."""

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
        """Mark all overdue active leases as expired."""

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
        """Force one lease into the expired state for failover paths."""

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
        """Return one normalized lease snapshot."""

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
        """Return whether a holder may execute under the given fencing token."""

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
    """Normalize SQLAlchemy/SQLite datetimes into aware UTC timestamps."""

    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
