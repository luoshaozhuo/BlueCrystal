"""Write security profile domain model.

Controls which protocols are allowed to perform write/control operations,
what readback strategy is used, and what authorization is required.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class ReadbackStrategy(Enum):
    """How write readback verification is performed."""

    DISABLED = "disabled"
    IMMEDIATE_READBACK = "immediate_readback"
    ASYNC_CONFIRMATION = "async_confirmation"


@dataclass(frozen=True, slots=True)
class ProtocolWriteProfile:
    """Security configuration for write operations on one protocol."""

    allowed: bool = False
    readback_strategy: ReadbackStrategy = ReadbackStrategy.DISABLED
    required_roles: tuple[str, ...] = field(default_factory=lambda: ("admin",))
    max_items_per_write: int = 100


@dataclass(frozen=True, slots=True)
class WriteSecurityProfile:
    """Security profile for write/control operations.

    Controls which protocols may write, what readback strategy to use,
    and what authorization level is required.

    The default profile denies all protocols. Each protocol must be
    explicitly enabled in ``protocols``.

    Example::

        profile = WriteSecurityProfile(protocols={
            "opcua": ProtocolWriteProfile(
                allowed=True,
                readback_strategy=ReadbackStrategy.IMMEDIATE_READBACK,
            ),
            "modbus_tcp": ProtocolWriteProfile(
                allowed=True,
                readback_strategy=ReadbackStrategy.DISABLED,
            ),
        })
    """

    default_readback_strategy: ReadbackStrategy = ReadbackStrategy.DISABLED
    default_required_roles: tuple[str, ...] = field(default_factory=lambda: ("admin",))
    default_max_items_per_write: int = 100
    protocols: dict[str, ProtocolWriteProfile] = field(default_factory=dict)

    def profile_for(self, protocol: str) -> ProtocolWriteProfile:
        """Get the resolved profile for *protocol*.

        Returns a protocol-specific entry if one is configured, otherwise
        the implicit default (deny-all).
        """
        normalized = protocol.strip().lower()
        if normalized in self.protocols:
            return self.protocols[normalized]
        return ProtocolWriteProfile()

    def is_write_allowed(self, protocol: str) -> bool:
        """Return whether write is allowed for *protocol*."""
        return self.profile_for(protocol).allowed
