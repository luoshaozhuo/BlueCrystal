"""Deadline models for bounded operations."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class Deadline:
    """Absolute deadline for one operation."""

    expires_at: datetime
