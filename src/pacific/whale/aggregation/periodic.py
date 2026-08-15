"""Periodic 1-minute DWS aggregation."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime

from whale.models import DwdRecord, DwsPeriodicAggregate
from pacific.whale.shared.enums.quality import QualityCode
from pacific.whale.shared.utils.time import floor_to_minute


def aggregate_periodic(records: list[DwdRecord]) -> list[DwsPeriodicAggregate]:
    """Aggregate DWD records into one-minute DWS buckets.

    Args:
        records: Cleaned DWD records spanning one or more turbines.

    Returns:
        Minute-level DWS aggregates ordered by bucket time.
    """
    grouped: dict[tuple[str, datetime], list[DwdRecord]] = defaultdict(list)
    for record in sorted(records, key=lambda item: item.ts):
        grouped[(record.turbine_id, floor_to_minute(record.ts))].append(record)

    results: list[DwsPeriodicAggregate] = []
    for (turbine_id, bucket_time), bucket_records in sorted(
        grouped.items(), key=lambda item: item[0][1]
    ):
        power_records = _point_records(bucket_records, "active_power_kw")
        pitch_records = _point_records(bucket_records, "pitch_angle_deg")
        results.append(
            DwsPeriodicAggregate(
                bucket_time=bucket_time,
                turbine_id=turbine_id,
                energy_increment_kwh=_estimate_energy_increment(power_records),
                avg_active_power_kw=_average(power_records),
                avg_pitch_angle_deg=_average(pitch_records),
            )
        )
    return results


def _point_records(records: list[DwdRecord], point_code: str) -> list[DwdRecord]:
    """Filter non-bad records by point code."""
    return [
        record
        for record in records
        if record.point_code == point_code
        and record.quality_code != QualityCode.BAD
        and isinstance(record.value, (int, float))
    ]


def _average(records: list[DwdRecord]) -> float | None:
    """Compute average for numeric record values."""
    if not records:
        return None
    values = [float(record.value) for record in records if isinstance(record.value, (int, float))]
    return sum(values) / len(values) if values else None


def _estimate_energy_increment(records: list[DwdRecord]) -> float:
    """Estimate energy increment with a simple piecewise-constant rule."""
    if len(records) < 2:
        return 0.0

    energy_kwh = 0.0
    sorted_records = sorted(records, key=lambda item: item.ts)
    for left, right in zip(sorted_records, sorted_records[1:]):
        if not isinstance(left.value, (int, float)):
            continue
        delta_hours = max((right.ts - left.ts).total_seconds(), 0.0) / 3600.0
        energy_kwh += float(left.value) * delta_hours
    return energy_kwh
