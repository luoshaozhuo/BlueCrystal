"""Identity models for access control decisions."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class Principal:
    """Authenticated or system identity requesting one operation."""

    principal_id: str
    principal_type: str
    roles: tuple[str, ...] = ()
    attributes: dict[str, str] = field(default_factory=dict)

