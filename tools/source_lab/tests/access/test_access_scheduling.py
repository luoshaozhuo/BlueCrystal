"""Tests for access scheduling helpers."""

from __future__ import annotations

from whale.shared.source.access.model import SourceEndpointSpec, SourcePointSpec
from tools.source_lab.access.providers.base import SourceRuntimeSpec
from tools.source_lab.access.common.scheduling import (
    RunnerEndpointPlan,
    build_source_specs,
    iter_float_ramp,
    iter_int_ramp,
    parse_float_list_or_ramp,
    parse_int_list_or_ramp,
    partition_specs_round_robin,
)


def _runtime_spec(index: int) -> SourceRuntimeSpec:
    endpoint = SourceEndpointSpec(
        name=f"s{index}",
        host="127.0.0.1",
        port=48000 + index,
        protocol="opcua",
    )
    points = (SourcePointSpec(address="IED.LD.LN.DO"),)
    return SourceRuntimeSpec(endpoint=endpoint, points=points)


def test_iter_int_ramp() -> None:
    assert tuple(iter_int_ramp(1, 4, 10)) == (1, 5, 9)


def test_iter_float_ramp() -> None:
    assert tuple(iter_float_ramp(5.0, 5.0, 15.0)) == (5.0, 10.0, 15.0)


def test_partition_specs_round_robin() -> None:
    specs = tuple(build_source_specs(tuple(_runtime_spec(i) for i in range(5)), target_hz=10.0))
    buckets = partition_specs_round_robin(specs, process_count=2)

    assert len(buckets) == 2
    assert len(buckets[0]) == 3
    assert len(buckets[1]) == 2
    assert all(isinstance(item, RunnerEndpointPlan) for bucket in buckets for item in bucket)


def test_build_source_specs_offset_distribution() -> None:
    target_hz = 10.0
    period_ns = round((1.0 / target_hz) * 1_000_000_000)
    specs = build_source_specs(tuple(_runtime_spec(i) for i in range(4)), target_hz=target_hz)

    assert len(specs) == 4
    assert tuple(spec.global_index for spec in specs) == (0, 1, 2, 3)
    assert tuple(spec.offset_ns for spec in specs) == (0, 25_000_000, 50_000_000, 75_000_000)
    for spec in specs:
        assert 0 <= spec.offset_ns < period_ns


def test_build_source_specs_returns_empty_for_empty_sources() -> None:
    assert build_source_specs((), target_hz=10.0) == ()


def test_parse_int_list_or_ramp_prefers_list() -> None:
    values = parse_int_list_or_ramp(
        "1,3,5",
        start=2,
        step=2,
        maximum=8,
        default=(9,),
        value_name="server_count",
    )

    assert values == (1, 3, 5)


def test_parse_int_list_or_ramp_uses_ramp_when_list_missing() -> None:
    values = parse_int_list_or_ramp(
        None,
        start=1,
        step=2,
        maximum=5,
        default=(9,),
        value_name="server_count",
    )

    assert values == (1, 3, 5)


def test_parse_float_list_or_ramp_defaults_when_no_inputs() -> None:
    values = parse_float_list_or_ramp(
        None,
        start=None,
        step=None,
        maximum=None,
        default=(10.0,),
        value_name="hz",
    )

    assert values == (10.0,)


def test_parse_float_list_or_ramp_rejects_invalid_step() -> None:
    try:
        parse_float_list_or_ramp(
            None,
            start=5.0,
            step=0.0,
            maximum=10.0,
            default=(10.0,),
            value_name="hz",
        )
    except ValueError as exc:
        assert "step must be greater than 0" in str(exc)
    else:  # pragma: no cover - assertion guard
        raise AssertionError("expected ValueError")


def test_parse_int_list_or_ramp_rejects_partial_ramp() -> None:
    try:
        parse_int_list_or_ramp(
            None,
            start=1,
            step=None,
            maximum=3,
            default=(1,),
            value_name="process_count",
        )
    except ValueError as exc:
        assert "requires start, step, and max" in str(exc)
    else:  # pragma: no cover - assertion guard
        raise AssertionError("expected ValueError")
