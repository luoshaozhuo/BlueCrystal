"""Backoff policy helpers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class BackoffPolicy:
    """Exponential backoff settings with an optional maximum delay."""

    initial_delay_seconds: float = 0.0
    multiplier: float = 2.0
    max_delay_seconds: float | None = None

    def delay_for(self, attempt: int) -> float:
        """Return the delay for a one-based retry attempt number."""

        if attempt <= 1:
            delay = self.initial_delay_seconds
        else:
            delay = self.initial_delay_seconds * (self.multiplier ** (attempt - 1))
        if self.max_delay_seconds is None:
            return delay
        return min(delay, self.max_delay_seconds)

