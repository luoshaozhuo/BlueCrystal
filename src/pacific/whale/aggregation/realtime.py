"""Realtime 5-second DWS aggregation."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta

from whale.models import DwdRecord, DwsRealtimeAggregate
from pacific.whale.shared.enums.quality import QualityCode, RunState
from pacific.whale.shared.utils.time import floor_to_second, window_start


def aggregate_realtime(records: list[DwdRecord]) -> list[DwsRealtimeAggregate]:
    """Aggregate DWD records into five-second sliding realtime windows.

    Args:
        records: Cleaned DWD records spanning one or more turbines.

    Returns:
        Realtime aggregates ordered by turbine-local processing sequence.
    """
    grouped: dict[str, list[DwdRecord]] = defaultdict(list)
    for record in sorted(records, key=lambda item: item.ts):
        grouped[record.turbine_id].append(record)

    results: list[DwsRealtimeAggregate] = []
    for turbine_id, turbine_records in grouped.items():
        start = floor_to_second(turbine_records[0].ts)
        end = floor_to_second(turbine_records[-1].ts)
        current = start
        while current <= end:
            start_time = window_start(current, 5)
            window_records = [
                record for record in turbine_records if start_time <= record.ts <= current
            ]
            if window_records:
                results.append(_aggregate_window(turbine_id, current, window_records))
            current = current + timedelta(seconds=1)
    return results


def _aggregate_window(
    turbine_id: str,
    window_end_time: datetime,
    records: list[DwdRecord],
) -> DwsRealtimeAggregate:
    """Aggregate one realtime window."""
    active_power = _numeric_values(records, "active_power_kw")
    wind_speed = _numeric_values(records, "wind_speed_ms")
    temp = _numeric_values(records, "generator_bearing_temp_c")
    run_states = [
        record
        for record in records
        if record.point_code == "run_state" and isinstance(record.value, RunState)
    ]
    bad_count = sum(
        1 for record in records if record.quality_code in {QualityCode.BAD, QualityCode.SUSPECT}
    )
    last_state = run_states[-1].value if run_states else RunState.UNKNOWN
    assert isinstance(last_state, RunState)

    return DwsRealtimeAggregate(
        window_end_time=window_end_time,
        turbine_id=turbine_id,
        avg_active_power_kw=_average(active_power),
        avg_wind_speed_ms=_average(wind_speed),
        max_generator_bearing_temp_c=max(temp) if temp else None,
        run_state_last=last_state,
        bad_quality_ratio=bad_count / len(records),
    )


def _numeric_values(records: list[DwdRecord], point_code: str) -> list[float]:
    """Return numeric non-bad values for one point code."""
    values: list[float] = []
    for record in records:
        if record.point_code != point_code or record.quality_code == QualityCode.BAD:
            continue
        if isinstance(record.value, (int, float)):
            values.append(float(record.value))
    return values


def _average(values: list[float]) -> float | None:
    """Return average for a numeric list."""
    if not values:
        return None
    return sum(values) / len(values)
