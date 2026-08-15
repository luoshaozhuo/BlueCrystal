"""ADS business aggregations for scenario1."""

from __future__ import annotations

import csv
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

from whale.models import (
    AdsAvailability,
    AdsPowerCurveDeviation,
    DwdRecord,
    DwsPeriodicAggregate,
)
from pacific.whale.shared.enums.quality import QualityCode, RunState
from pacific.whale.shared.utils.time import floor_to_minute


def load_power_curve(path: str | Path) -> dict[float, float]:
    """Load the theoretical power curve lookup table used by ADS aggregation.

    Args:
        path: CSV file that maps `wind_speed_bin` to `theoretical_power_kw`.

    Returns:
        A lookup table keyed by wind-speed bin in meters per second.
    """
    curve: dict[float, float] = {}
    with Path(path).open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            curve[float(row["wind_speed_bin"])] = float(row["theoretical_power_kw"])
    return curve


def aggregate_power_curve_deviation(
    dwd_records: list[DwdRecord],
    periodic_results: list[DwsPeriodicAggregate],
    power_curve: dict[float, float],
) -> list[AdsPowerCurveDeviation]:
    """Build minute-level power-curve deviation results for ADS.

    Args:
        dwd_records: Cleaned detail records that still contain wind-speed measurements.
        periodic_results: Minute-level DWS aggregates that provide actual average power.
        power_curve: Theoretical power lookup keyed by wind-speed bin.

    Returns:
        ADS records for buckets where both average wind speed and actual power are available.
    """
    avg_wind_by_bucket = _average_wind_by_bucket(dwd_records)
    results: list[AdsPowerCurveDeviation] = []
    for periodic in periodic_results:
        avg_wind = avg_wind_by_bucket.get((periodic.turbine_id, periodic.bucket_time))
        if avg_wind is None or periodic.avg_active_power_kw is None:
            continue
        wind_bin = round(avg_wind * 2.0) / 2.0
        theoretical = power_curve.get(wind_bin, 0.0)
        actual = periodic.avg_active_power_kw
        results.append(
            AdsPowerCurveDeviation(
                bucket_time=periodic.bucket_time,
                turbine_id=periodic.turbine_id,
                wind_speed_bin=wind_bin,
                actual_power_kw=actual,
                theoretical_power_kw=theoretical,
                deviation_kw=actual - theoretical,
            )
        )
    return results


def aggregate_availability(dwd_records: list[DwdRecord]) -> list[AdsAvailability]:
    """Estimate turbine availability ratios from run-state records.

    Args:
        dwd_records: Cleaned detail records that may include `run_state` measurements.

    Returns:
        One ADS availability record per turbine and minute bucket.
    """
    grouped: dict[tuple[str, datetime], list[DwdRecord]] = defaultdict(list)
    for record in sorted(dwd_records, key=lambda item: item.ts):
        if record.point_code == "run_state":
            grouped[(record.turbine_id, floor_to_minute(record.ts))].append(record)

    results: list[AdsAvailability] = []
    for (turbine_id, bucket_time), records in sorted(grouped.items(), key=lambda item: item[0][1]):
        run_time_sec = _estimate_run_time(records)
        bad_ratio = sum(
            1 for record in records if record.quality_code in {QualityCode.BAD, QualityCode.SUSPECT}
        ) / len(records)
        availability = min(max(run_time_sec / 60.0, 0.0), 1.0)
        results.append(
            AdsAvailability(
                bucket_time=bucket_time,
                turbine_id=turbine_id,
                availability_ratio=availability,
                run_time_sec=run_time_sec,
                bad_quality_ratio=bad_ratio,
            )
        )
    return results


def _average_wind_by_bucket(dwd_records: list[DwdRecord]) -> dict[tuple[str, datetime], float]:
    """Calculate average wind speed for each minute bucket."""
    grouped: dict[tuple[str, datetime], list[float]] = defaultdict(list)
    for record in dwd_records:
        if (
            record.point_code == "wind_speed_ms"
            and record.quality_code != QualityCode.BAD
            and isinstance(record.value, (int, float))
        ):
            grouped[(record.turbine_id, floor_to_minute(record.ts))].append(float(record.value))
    return {key: sum(values) / len(values) for key, values in grouped.items() if values}


def _estimate_run_time(records: list[DwdRecord]) -> float:
    """Estimate running duration within a one-minute bucket."""
    if not records:
        return 0.0

    run_time_sec = 0.0
    sorted_records = sorted(records, key=lambda item: item.ts)
    bucket_end = floor_to_minute(sorted_records[0].ts) + timedelta(minutes=1)
    for index, record in enumerate(sorted_records):
        next_ts = sorted_records[index + 1].ts if index + 1 < len(sorted_records) else bucket_end
        if record.value in {RunState.RUNNING, RunState.DERATED}:
            run_time_sec += max((next_ts - record.ts).total_seconds(), 0.0)
    return run_time_sec
