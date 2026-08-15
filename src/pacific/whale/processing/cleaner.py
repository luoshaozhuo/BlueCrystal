"""Cleaning rules for scenario1 normalized points."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime

from whale.models import CleanResult, NormalizedPoint, PointMeta
from pacific.whale.shared.enums.quality import CleanAction, QualityCode, RunState


class PointCleaner:
    """Apply the fixed scenario1 cleaning chain to normalized points.

    The cleaner keeps per-point history so deadband and rate-of-change rules can
    compare the current value with the last retained value for the same turbine
    and point code.
    """

    def __init__(self) -> None:
        """Initialize cleaner state."""
        self._last_values: dict[tuple[str, str], float | int | str | RunState | None] = {}
        self._last_times: dict[tuple[str, str], datetime] = {}

    def clean(self, point: NormalizedPoint, meta: PointMeta) -> CleanResult:
        """Clean one normalized point with the scenario1 rule order.

        Args:
            point: Normalized point produced by the normalization stage.
            meta: Registry metadata that defines engineering constraints.

        Returns:
            The clean result after applying null/type, range, deadband, and
            rate-of-change checks in order.
        """
        key = (point.turbine_id, point.point_code)
        type_result = self._validate_null_and_type(point)
        if type_result is not None:
            return type_result

        range_result = self._apply_range_rule(point, meta)
        point = range_result.normalized_point
        if range_result.clean_action in {CleanAction.CLAMP, CleanAction.DROP}:
            self._last_values[key] = point.value
            self._last_times[key] = point.event_time
            return range_result

        deadband_result = self._apply_deadband_rule(point, meta, key)
        point = deadband_result.normalized_point
        if deadband_result.clean_action == CleanAction.HOLD_LAST:
            return deadband_result

        rate_result = self._apply_rate_rule(point, meta, key)
        self._last_values[key] = rate_result.normalized_point.value
        self._last_times[key] = rate_result.normalized_point.event_time
        return rate_result

    def _validate_null_and_type(self, point: NormalizedPoint) -> CleanResult | None:
        """Apply null and type validation."""
        if point.value is None:
            return CleanResult(
                normalized_point=point,
                quality_code=QualityCode.BAD,
                clean_action=CleanAction.DROP,
                clean_reason="value is null",
            )

        if point.point_code == "run_state":
            if not isinstance(point.value, RunState):
                return CleanResult(
                    normalized_point=point,
                    quality_code=QualityCode.BAD,
                    clean_action=CleanAction.DROP,
                    clean_reason="run_state type mismatch",
                )
            return None

        if point.value_type == "float" and not isinstance(point.value, (int, float)):
            return CleanResult(
                normalized_point=point,
                quality_code=QualityCode.BAD,
                clean_action=CleanAction.DROP,
                clean_reason="float type mismatch",
            )
        if point.value_type == "int" and not isinstance(point.value, int):
            return CleanResult(
                normalized_point=point,
                quality_code=QualityCode.BAD,
                clean_action=CleanAction.DROP,
                clean_reason="int type mismatch",
            )
        return None

    def _apply_range_rule(self, point: NormalizedPoint, meta: PointMeta) -> CleanResult:
        """Clamp or keep value according to engineering range."""
        if not isinstance(point.value, (int, float)):
            return CleanResult(point, QualityCode.GOOD, CleanAction.KEEP, "within range")

        if meta.min_value is not None and point.value < meta.min_value:
            return CleanResult(
                normalized_point=replace(point, value=float(meta.min_value)),
                quality_code=QualityCode.CORRECTED,
                clean_action=CleanAction.CLAMP,
                clean_reason=f"below min_value {meta.min_value}",
            )
        if meta.max_value is not None and point.value > meta.max_value:
            return CleanResult(
                normalized_point=replace(point, value=float(meta.max_value)),
                quality_code=QualityCode.CORRECTED,
                clean_action=CleanAction.CLAMP,
                clean_reason=f"above max_value {meta.max_value}",
            )
        return CleanResult(point, QualityCode.GOOD, CleanAction.KEEP, "within range")

    def _apply_deadband_rule(
        self,
        point: NormalizedPoint,
        meta: PointMeta,
        key: tuple[str, str],
    ) -> CleanResult:
        """Apply deadband handling using last retained value."""
        if meta.deadband is None or not isinstance(point.value, (int, float)):
            return CleanResult(point, QualityCode.GOOD, CleanAction.KEEP, "deadband skipped")

        previous = self._last_values.get(key)
        if (
            isinstance(previous, (int, float))
            and abs(float(point.value) - float(previous)) < meta.deadband
        ):
            return CleanResult(
                normalized_point=replace(point, value=float(previous)),
                quality_code=QualityCode.CORRECTED,
                clean_action=CleanAction.HOLD_LAST,
                clean_reason=f"within deadband {meta.deadband}",
            )
        return CleanResult(point, QualityCode.GOOD, CleanAction.KEEP, "deadband passed")

    def _apply_rate_rule(
        self,
        point: NormalizedPoint,
        meta: PointMeta,
        key: tuple[str, str],
    ) -> CleanResult:
        """Apply rate-of-change validation."""
        if meta.max_rate_of_change is None or not isinstance(point.value, (int, float)):
            return CleanResult(point, QualityCode.GOOD, CleanAction.KEEP, "rate check skipped")

        previous = self._last_values.get(key)
        previous_time = self._last_times.get(key)
        if isinstance(previous, (int, float)) and previous_time is not None:
            delta_seconds = max((point.event_time - previous_time).total_seconds(), 0.0)
            effective_delta = max(delta_seconds, 1.0)
            rate = abs(float(point.value) - float(previous)) / effective_delta
            if rate > meta.max_rate_of_change:
                return CleanResult(
                    normalized_point=point,
                    quality_code=QualityCode.SUSPECT,
                    clean_action=CleanAction.KEEP,
                    clean_reason=f"rate {rate:.3f} exceeds {meta.max_rate_of_change}",
                )
        return CleanResult(point, QualityCode.GOOD, CleanAction.KEEP, "rate passed")
