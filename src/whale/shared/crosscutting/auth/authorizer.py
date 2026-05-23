"""Authorization decision models."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class AccessDecision:
    """Result returned by an access-policy evaluation."""

    allowed: bool
    reason: str | None = None
    obligations: tuple[str, ...] = ()
    attributes: dict[str, str] = field(default_factory=dict)

