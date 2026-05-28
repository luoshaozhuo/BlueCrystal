"""Decorator objects for SourceWritePort crosscutting concerns."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from whale.ingest.domain.write_security_profile import WriteSecurityProfile
from whale.ingest.ports.source.source_write_port import SourceWritePort
from whale.ingest.usecases.dtos.source_connection_data import SourceConnectionData
from whale.ingest.usecases.dtos.source_write_request import (
    SourceWriteExecutionOptions,
    SourceWriteItemData,
)
from whale.ingest.usecases.dtos.source_write_result import SourceWriteResult
from whale.shared.crosscutting.auth import AccessPolicyPort, Permission, Principal

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class AuthorizedSourceWritePort(SourceWritePort):
    """Enforce access-policy and security-profile decisions before write.

    Wraps an inner ``SourceWritePort`` and rejects write operations when:
    - The protocol is not allowed by the ``WriteSecurityProfile``.
    - The ``AccessPolicyPort`` denies the principal's permission.

    Usage in composition root::

        port = AuthorizedSourceWritePort(
            inner=OpcUaSourceWriteAdapter(),
            principal=resolved_principal,
            access_policy=resolved_access_policy,
            security_profile=profile,
        )
    """

    inner: SourceWritePort
    principal: Principal
    access_policy: AccessPolicyPort
    security_profile: WriteSecurityProfile = WriteSecurityProfile()

    async def write(
        self,
        execution: SourceWriteExecutionOptions,
        connection: SourceConnectionData,
        items: list[SourceWriteItemData],
    ) -> SourceWriteResult:
        protocol = execution.protocol.strip().lower()
        resource_id = connection.ied_name or connection.ld_name or "unknown"
        self._require_write_allowed(protocol, resource_id)
        return await self.inner.write(execution, connection, items)

    def _require_write_allowed(self, protocol: str, resource_id: str) -> None:
        profile = self.security_profile.profile_for(protocol)
        if not profile.allowed:
            raise PermissionError(
                f"Write not allowed for protocol '{protocol}'. "
                "Enable it in WriteSecurityProfile.protocols."
            )

        decision = self.access_policy.evaluate(
            self.principal,
            Permission(
                resource_type="source_write",
                resource_id=resource_id,
                action=f"write:{protocol}",
            ),
        )
        if not decision.allowed:
            raise PermissionError(
                decision.reason or f"Access denied for write:{protocol} on {resource_id}"
            )
