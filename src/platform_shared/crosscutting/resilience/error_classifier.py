"""Stable error classification models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True, slots=True)
class ClassifiedError:
    """Normalized error shape used across retry, metrics, and logging flows."""

    error_code: str
    category: str
    retryable: bool
    message: str
    attributes: dict[str, str] = field(default_factory=dict)


class ErrorClassifier(Protocol):
    """Normalize exceptions into stable, machine-readable error shapes."""

    def classify(self, error: Exception) -> ClassifiedError:
        """Return one stable classification for the provided exception."""
