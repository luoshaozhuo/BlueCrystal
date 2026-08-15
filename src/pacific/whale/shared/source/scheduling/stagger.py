"""Deterministic stagger-offset helpers for worker-local source polling.

This module only calculates stable offsets. It does not schedule tasks, does
not manage polling loops, and is not an APScheduler replacement. The helpers
are protocol-agnostic and are intended to be used by runtime/worker layers
before they register jobs with the worker-local polling scheduler.

Relationship to outer orchestration:
- APScheduler or another external orchestrator may decide when a runtime is
  started or reloaded, but it should not compute per-read wake-up offsets;
- for multi-process acquisition, global smoothing should ideally be calculated
  before work is sharded across workers;
- recalculating offsets independently inside each worker can recreate bursts
  and is therefore best avoided for high-frequency acquisition.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeVar

T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class StaggerAssignment:
    """One deterministic stagger assignment.

    Attributes:
        index: Stable global index, starting from zero.
        total: Total number of items in the stagger group.
        offset_seconds: Offset from the common group start time.
    """

    index: int
    total: int
    offset_seconds: float


def build_even_stagger_offsets(
    *,
    count: int,
    interval_seconds: float,
    base_offset_seconds: float = 0.0,
) -> tuple[float, ...]:
    """Build evenly distributed offsets within one polling interval.

    Args:
        count: Number of polling jobs to distribute.
        interval_seconds: Polling interval in seconds.
        base_offset_seconds: Common base offset added to every generated
            offset.

    Returns:
        Tuple of offsets in seconds. Returns an empty tuple when ``count`` is
        not positive.

    Raises:
        ValueError: If ``interval_seconds`` is not greater than zero.
    """

    if count <= 0:
        return ()

    if interval_seconds <= 0:
        raise ValueError("interval_seconds must be greater than 0")

    spacing = interval_seconds / count
    return tuple(base_offset_seconds + spacing * index for index in range(count))


def build_stagger_assignments(
    *,
    count: int,
    interval_seconds: float,
    base_offset_seconds: float = 0.0,
) -> tuple[StaggerAssignment, ...]:
    """Build deterministic stagger assignments for a fixed-size group.

    Args:
        count: Number of polling jobs to distribute.
        interval_seconds: Polling interval in seconds.
        base_offset_seconds: Common base offset added to every generated
            offset.

    Returns:
        Tuple of stagger assignment objects in stable index order.
    """

    offsets = build_even_stagger_offsets(
        count=count,
        interval_seconds=interval_seconds,
        base_offset_seconds=base_offset_seconds,
    )

    return tuple(
        StaggerAssignment(
            index=index,
            total=count,
            offset_seconds=offset,
        )
        for index, offset in enumerate(offsets)
    )


def assign_even_stagger(
    items: tuple[T, ...],
    *,
    interval_seconds: float,
    base_offset_seconds: float = 0.0,
) -> tuple[tuple[T, StaggerAssignment], ...]:
    """Attach deterministic stagger assignments while preserving item order.

    Args:
        items: Input items in the order that should define stable global
            staggering.
        interval_seconds: Polling interval in seconds.
        base_offset_seconds: Common base offset added to every generated
            offset.

    Returns:
        Tuple pairing each input item with its deterministic stagger
        assignment.
    """

    assignments = build_stagger_assignments(
        count=len(items),
        interval_seconds=interval_seconds,
        base_offset_seconds=base_offset_seconds,
    )

    return tuple(zip(items, assignments))
