"""Write lease port used by SourceCommandUseCase."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True, slots=True)
class WriteLeaseDecisionData:
    """Result returned by a write lease guard."""

    allowed: bool
    result: str
    reason_code: str | None
    fencing_token: int | None
    expires_at: datetime | None = None


class WriteLeasePort(Protocol):
    """Guard real write/control execution with a dedicated lease."""

    def acquire(
        self,
        *,
        resource_id: str,
        holder_key: str,
        requested_fencing_token: int | None = None,
    ) -> WriteLeaseDecisionData:
        """Acquire one write lease."""

    def renew(self, *, resource_id: str, holder_key: str) -> WriteLeaseDecisionData:
        """Renew one write lease."""

    def validate(
        self,
        *,
        resource_id: str,
        holder_key: str,
        fencing_token: int,
    ) -> WriteLeaseDecisionData:
        """Validate one write lease token."""

    def release(self, *, resource_id: str, holder_key: str) -> None:
        """Release one write lease."""
