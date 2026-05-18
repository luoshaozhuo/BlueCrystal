# mypy: disable-error-code=import-untyped
"""Scheduling helpers for capacity scan orchestration."""

from __future__ import annotations

import multiprocessing as mp
from collections.abc import Iterator, Sequence
from dataclasses import dataclass

from tools.source_lab.access.providers.base import SourceRuntimeSpec


@dataclass(frozen=True, slots=True)
class RunnerEndpointPlan:
    """One endpoint assigned to the runner with a fixed C-side offset."""

    global_index: int
    source: SourceRuntimeSpec
    offset_ns: int


def iter_int_ramp(start: int, step: int, maximum: int) -> Iterator[int]:
    """Yield integer ramp values from start to maximum, inclusive."""

    current = start
    while current <= maximum:
        yield current
        current += step


def iter_float_ramp(start: float, step: float, maximum: float) -> Iterator[float]:
    """Yield float ramp values from start to maximum with numeric tolerance."""

    current = start
    while current <= maximum + 1e-12:
        yield round(current, 10)
        current += step


def build_source_specs(
    sources: Sequence[SourceRuntimeSpec],
    *,
    target_hz: float,
) -> tuple[RunnerEndpointPlan, ...]:
    """Build globally staggered endpoint plans for one level."""

    count = len(sources)
    if count == 0:
        return ()

    period_ns = max(1, round(1_000_000_000 / target_hz))
    return tuple(
        RunnerEndpointPlan(
            global_index=index,
            source=source,
            offset_ns=min(period_ns - 1, max(0, round(period_ns * index / count))),
        )
        for index, source in enumerate(sources)
    )


def partition_specs_round_robin(
    specs: Sequence[RunnerEndpointPlan],
    *,
    process_count: int,
) -> tuple[tuple[RunnerEndpointPlan, ...], ...]:
    """Partition source specs with round-robin distribution across workers."""

    buckets: list[list[RunnerEndpointPlan]] = [[] for _ in range(process_count)]
    for index, spec in enumerate(specs):
        buckets[index % process_count].append(spec)
    return tuple(tuple(bucket) for bucket in buckets)


def resolve_mp_context() -> mp.context.BaseContext:
    """Resolve multiprocessing context, preferring fork when available."""

    methods = mp.get_all_start_methods()
    if "fork" in methods:
        return mp.get_context("fork")
    return mp.get_context()
