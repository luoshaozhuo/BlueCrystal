"""Stable enums shared across scenario pipelines."""

from __future__ import annotations

from enum import Enum


class RunState(str, Enum):
    """Supported turbine run states for scenario1."""

    STOPPED = "STOPPED"
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    DERATED = "DERATED"
    FAULT = "FAULT"
    UNKNOWN = "UNKNOWN"


class QualityCode(str, Enum):
    """Supported data quality codes."""

    GOOD = "GOOD"
    BAD = "BAD"
    CORRECTED = "CORRECTED"
    SUSPECT = "SUSPECT"


class CleanAction(str, Enum):
    """Supported clean actions."""

    KEEP = "KEEP"
    CLAMP = "CLAMP"
    DROP = "DROP"
    HOLD_LAST = "HOLD_LAST"
