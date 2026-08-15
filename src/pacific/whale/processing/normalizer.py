"""Raw batch normalization for scenario1."""

from __future__ import annotations

from typing import Any

from whale.models import NUMERIC_VALUE_TYPES, NormalizedPoint, PointMeta
from pacific.whale.shared.enums.quality import RunState
from pacific.whale.shared.utils.time import parse_iso_datetime


class NormalizationError(ValueError):
    """Raised when raw payload cannot be normalized."""


def normalize_batch(
    raw_batch: Any,
    registry_by_node: dict[str, PointMeta],
    registry_by_code: dict[str, PointMeta] | None = None,
) -> list[NormalizedPoint]:
    """Normalize one raw batch into stable internal measurement points.

    Args:
        raw_batch: Raw batch model produced by the collector stage.
        registry_by_node: Registry lookup keyed by OPC UA node id.
        registry_by_code: Optional fallback lookup keyed by internal point code.

    Returns:
        Normalized points ready for cleaning and persistence.

    Raises:
        NormalizationError: If the payload shape is invalid or a measurement
            cannot be mapped to registry metadata.
    """
    if "measurements" not in raw_batch.raw_payload:
        raise NormalizationError("Raw batch payload missing measurements.")

    event_time = parse_iso_datetime(str(raw_batch.raw_payload.get("event_time")))
    measurements = raw_batch.raw_payload["measurements"]
    if not isinstance(measurements, list):
        raise NormalizationError("Raw batch measurements must be a list.")

    normalized: list[NormalizedPoint] = []
    registry_by_code = registry_by_code or {}
    for measurement in measurements:
        if not isinstance(measurement, dict):
            raise NormalizationError("Measurement entry must be a dict.")

        meta = _resolve_meta(measurement, registry_by_node, registry_by_code)
        source_status = str(measurement.get("status", "GOOD"))
        value = _normalize_value(measurement.get("value"), meta)
        point_event_time = measurement.get("event_time")
        normalized.append(
            NormalizedPoint(
                event_time=parse_iso_datetime(point_event_time) if point_event_time else event_time,
                ingest_time=raw_batch.recv_time,
                turbine_id=raw_batch.turbine_id,
                point_code=meta.point_code,
                value=value,
                value_type=meta.value_type,
                unit=meta.unit,
                source_status=source_status,
                source_node_id=meta.opcua_node_id,
            )
        )
    return normalized


def _resolve_meta(
    measurement: dict[str, Any],
    registry_by_node: dict[str, PointMeta],
    registry_by_code: dict[str, PointMeta],
) -> PointMeta:
    """Resolve point metadata from a measurement."""
    node_id = measurement.get("node_id")
    point_code = measurement.get("point_code")
    if node_id and node_id in registry_by_node:
        return registry_by_node[str(node_id)]
    if point_code and point_code in registry_by_code:
        return registry_by_code[str(point_code)]
    raise NormalizationError(
        f"Measurement mapping missing for node={node_id!r}, point={point_code!r}"
    )


def _normalize_value(value: Any, meta: PointMeta) -> float | int | str | RunState | None:
    """Normalize one raw value based on registry metadata."""
    if value is None:
        return None
    if meta.point_code == "run_state":
        if not isinstance(value, str):
            raise NormalizationError("run_state value must be a string.")
        return RunState(value) if value in RunState._value2member_map_ else RunState.UNKNOWN
    if meta.value_type == "float":
        return float(value)
    if meta.value_type == "int":
        return int(value)
    if meta.value_type in NUMERIC_VALUE_TYPES:
        return float(value)
    if meta.value_type == "str":
        return str(value)
    if meta.value_type == "enum":
        return str(value)
    raise NormalizationError(f"Unsupported value_type: {meta.value_type}")
