"""Retry-policy models shared by wrappers and adapters."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    """Simple retry configuration for one outbound operation."""

    max_attempts: int = 1
    retryable_error_codes: frozenset[str] = frozenset()


@dataclass(frozen=True, slots=True)
class RetryDecision:
    """Decision produced for one retry evaluation."""

    should_retry: bool
    error_code: str | None = None
    delay_seconds: float = 0.0

