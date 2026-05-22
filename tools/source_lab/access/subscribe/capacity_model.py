"""Subscribe capacity result models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from tools.source_lab.access.polling.model import CapacityStatus
from tools.source_lab.access.subscribe.model import SubscribeLevelResult

SubscribeFailureStage = Literal["runtime", "recovery", "protocol"]


@dataclass(frozen=True, slots=True)
class SubscribeCapacityComboResult:
    """One subscribe capacity matrix combination outcome."""

    process_count: int
    server_count: int
    sample_hz: float
    effective_source_update_hz: float
    result: SubscribeLevelResult | None
    status: CapacityStatus
    reason: str
    queue_size: int = 1
    executed: bool = True
    failure_stage: SubscribeFailureStage | None = None


@dataclass(frozen=True, slots=True)
class SubscribeCapacityLimitSummary:
    """One subscribe capacity limit summary row."""

    process_count: int
    server_count: int
    queue_size: int
    effective_source_update_hz: float
    max_pass_sample_hz: float | None
    first_fail_sample_hz: float | None
    reason: str


@dataclass(frozen=True, slots=True)
class SubscribeCapacityResult:
    """Collection of subscribe capacity matrix outcomes."""

    combos: tuple[SubscribeCapacityComboResult, ...]
    limit_summaries: tuple[SubscribeCapacityLimitSummary, ...]
