"""Data-classification markers for audit and storage policy decisions."""

from __future__ import annotations

from enum import StrEnum


class DataClassification(StrEnum):
    """Simple classification labels for operational data."""

    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"

