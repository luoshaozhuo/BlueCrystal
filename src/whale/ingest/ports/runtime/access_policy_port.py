"""Access policy port for ingest runtime API authorization."""

from __future__ import annotations

from typing import Protocol

from starlette.requests import Request


class AccessPolicyPort(Protocol):
    """Evaluate whether a request is authorized for a given action and resource.

    Implementations can use request headers (x-actor, x-roles), the action
    being performed, and the target resource to make an allow/deny decision.
    """

    def authorize(
        self,
        request: Request,
        action: str,
        resource_type: str,
        resource_id: str | None = None,
    ) -> bool:
        """Return True if the request is allowed, False to deny."""
