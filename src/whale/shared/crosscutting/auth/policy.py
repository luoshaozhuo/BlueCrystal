"""Access-policy port abstractions."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from whale.shared.crosscutting.auth.authorizer import AccessDecision
from whale.shared.crosscutting.auth.identity import Principal


@dataclass(frozen=True, slots=True)
class Permission:
    """Requested action against one protected resource."""

    resource_type: str
    action: str
    resource_id: str | None = None
    attributes: dict[str, str] = field(default_factory=dict)


class AccessPolicyPort(Protocol):
    """Evaluate whether a principal may perform one permissioned action."""

    def evaluate(self, principal: Principal, permission: Permission) -> AccessDecision:
        """Return the access decision for the requested action."""

