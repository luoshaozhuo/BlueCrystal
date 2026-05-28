"""Write-control specific lease guard."""

from __future__ import annotations

from datetime import UTC, datetime

from whale.ingest.ports.runtime.write_lease_port import WriteLeaseDecisionData
from whale.ingest.runtime.lease import LeaseService


class WriteLeaseService:
    """Guard write/control execution with a dedicated lease scope."""

    def __init__(self, lease_service: LeaseService, ttl_seconds: int = 30) -> None:
        self._lease_service = lease_service
        self._ttl_seconds = ttl_seconds

    def acquire(
        self,
        *,
        resource_id: str,
        holder_key: str,
        requested_fencing_token: int | None = None,
    ) -> WriteLeaseDecisionData:
        """Acquire one write lease."""

        snapshot = self._lease_service.get_snapshot(lease_name=f"write:{resource_id}")
        if (
            requested_fencing_token is not None
            and snapshot is not None
            and snapshot.status == "ACTIVE"
            and snapshot.fencing_token != requested_fencing_token
        ):
            return WriteLeaseDecisionData(
                allowed=False,
                result="FENCED",
                reason_code="OLD_PRIMARY_FENCED",
                fencing_token=snapshot.fencing_token,
                expires_at=snapshot.expires_at,
            )

        result = self._lease_service.acquire(
            lease_name=f"write:{resource_id}",
            lease_scope="write",
            resource_id=resource_id,
            holder_key=holder_key,
            ttl_seconds=self._ttl_seconds,
            now=datetime.now(tz=UTC),
        )
        if not result.acquired:
            return WriteLeaseDecisionData(
                allowed=False,
                result="CONFLICT",
                reason_code=result.reason,
                fencing_token=result.fencing_token,
                expires_at=snapshot.expires_at if snapshot is not None else None,
            )
        return WriteLeaseDecisionData(
            allowed=True,
            result="ALLOW",
            reason_code=None,
            fencing_token=result.fencing_token,
            expires_at=self._lease_service.get_snapshot(lease_name=f"write:{resource_id}").expires_at,
        )

    def renew(self, *, resource_id: str, holder_key: str) -> WriteLeaseDecisionData:
        """Renew one active write lease."""

        lease = self._lease_service.renew(
            lease_name=f"write:{resource_id}",
            holder_key=holder_key,
            ttl_seconds=self._ttl_seconds,
            now=datetime.now(tz=UTC),
        )
        return WriteLeaseDecisionData(
            allowed=True,
            result="ALLOW",
            reason_code=None,
            fencing_token=lease.fencing_token,
            expires_at=lease.expires_at,
        )

    def validate(
        self,
        *,
        resource_id: str,
        holder_key: str,
        fencing_token: int,
    ) -> WriteLeaseDecisionData:
        """Validate one active write lease token."""

        allowed = self._lease_service.validate_execution(
            lease_name=f"write:{resource_id}",
            holder_key=holder_key,
            fencing_token=fencing_token,
            now=datetime.now(tz=UTC),
        )
        snapshot = self._lease_service.get_snapshot(lease_name=f"write:{resource_id}")
        if not allowed:
            return WriteLeaseDecisionData(
                allowed=False,
                result="FENCED",
                reason_code="OLD_PRIMARY_FENCED",
                fencing_token=snapshot.fencing_token if snapshot is not None else fencing_token,
                expires_at=snapshot.expires_at if snapshot is not None else None,
            )
        return WriteLeaseDecisionData(
            allowed=True,
            result="ALLOW",
            reason_code=None,
            fencing_token=fencing_token,
            expires_at=snapshot.expires_at if snapshot is not None else None,
        )

    def release(self, *, resource_id: str, holder_key: str) -> None:
        """Release one write lease."""

        self._lease_service.release(
            lease_name=f"write:{resource_id}",
            holder_key=holder_key,
        )
