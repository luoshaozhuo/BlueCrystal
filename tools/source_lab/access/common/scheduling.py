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


def parse_int_list_or_ramp(
    list_value: str | None,
    *,
    start: int | None,
    step: int | None,
    maximum: int | None,
    default: tuple[int, ...],
    value_name: str,
) -> tuple[int, ...]:
    """Parse an integer list first, otherwise a validated inclusive ramp."""

    if list_value is not None and list_value.strip() != "":
        values = tuple(int(item.strip()) for item in list_value.split(",") if item.strip())
        if not values:
            raise ValueError(f"{value_name} list cannot be empty")
        return values

    if start is None and step is None and maximum is None:
        return default
    if start is None or step is None or maximum is None:
        raise ValueError(
            f"{value_name} ramp requires start, step, and max when list is not provided"
        )
    if step <= 0:
        raise ValueError(f"{value_name} step must be greater than 0")
    if maximum < start:
        raise ValueError(f"{value_name} max must be greater than or equal to start")
    return tuple(iter_int_ramp(start, step, maximum))


def parse_float_list_or_ramp(
    list_value: str | None,
    *,
    start: float | None,
    step: float | None,
    maximum: float | None,
    default: tuple[float, ...],
    value_name: str,
) -> tuple[float, ...]:
    """Parse a float list first, otherwise a validated inclusive ramp."""

    if list_value is not None and list_value.strip() != "":
        values = tuple(float(item.strip()) for item in list_value.split(",") if item.strip())
        if not values:
            raise ValueError(f"{value_name} list cannot be empty")
        return values

    if start is None and step is None and maximum is None:
        return default
    if start is None or step is None or maximum is None:
        raise ValueError(
            f"{value_name} ramp requires start, step, and max when list is not provided"
        )
    if step <= 0:
        raise ValueError(f"{value_name} step must be greater than 0")
    if maximum < start:
        raise ValueError(f"{value_name} max must be greater than or equal to start")
    return tuple(iter_float_ramp(start, step, maximum))


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
