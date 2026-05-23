"""Retention policy model."""

from __future__ import annotations

from dataclasses import dataclass

from whale.shared.crosscutting.compliance.data_classification import DataClassification


@dataclass(frozen=True, slots=True)
class RetentionPolicy:
    """Retention rules for one data stream or event category."""

    classification: DataClassification
    retention_days: int
    purge_required: bool = False

