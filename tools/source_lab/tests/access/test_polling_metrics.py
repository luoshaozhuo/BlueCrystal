"""Tests for polling delivery and data-period aggregation semantics."""

from __future__ import annotations

import pytest

from tools.source_lab.access.polling.metrics import WorkerRawStats, build_level_metrics
from tools.source_lab.access.polling.model import CapacityMode, CapacityScanConfig


def _config() -> CapacityScanConfig:
    return CapacityScanConfig(
        mode=CapacityMode.SIMULATOR,
        protocol="opcua",
        endpoints=(),
        points=(),
        server_count_start=1,
        server_count_step=1,
        server_count_max=2,
        hz_start=10.0,
        hz_step=10.0,
        hz_max=10.0,
        process_count=1,
        level_duration_s=2.0,
        period_max_tolerance_ratio=0.2,
        period_mean_error_ratio=0.05,
    )


def test_polling_expected_value_and_ratio_metrics() -> None:
    config = _config()
    worker_stats = (
        WorkerRawStats(
            worker_index=0,
            reader_count=2,
            batch_mismatches=0,
            read_errors=0,
            missing_response_timestamps=0,
            response_timestamps_by_reader=((1.0, 1.1, 1.2), (1.0, 1.1, 1.2)),
            max_observed_concurrent_reads=1,
            total_reads=40,
            ok_reads=40,
            value_count=360,
        ),
    )

    metrics = build_level_metrics(
        worker_stats,
        server_count=2,
        point_total=20,
        target_hz=10.0,
        config=config,
    )

    assert metrics.points_per_server == 10
    assert metrics.point_total == 20
    assert metrics.expected_value_count == 400
    assert metrics.value_count == 360
    assert metrics.value_delivery_ratio == pytest.approx(0.9)
    assert metrics.value_missing_count == 40
    assert metrics.read_count == 40
    assert metrics.batch_count == 40


def test_polling_data_period_metrics_use_response_timestamp_diffs() -> None:
    config = _config()
    worker_stats = (
        WorkerRawStats(
            worker_index=0,
            reader_count=1,
            batch_mismatches=0,
            read_errors=0,
            missing_response_timestamps=0,
            response_timestamps_by_reader=((1.0, 1.1, 1.21, 1.33),),
            max_observed_concurrent_reads=1,
            total_reads=4,
            ok_reads=4,
            value_count=4,
        ),
    )

    metrics = build_level_metrics(
        worker_stats,
        server_count=1,
        point_total=1,
        target_hz=10.0,
        config=config,
    )

    assert metrics.period_mean_ms == pytest.approx(110.0, abs=0.01)
    assert metrics.period_p95_ms == pytest.approx(119.0, abs=0.01)
    assert metrics.period_max_ms == pytest.approx(120.0, abs=0.01)


def test_polling_low_ratio_does_not_change_pass_fail_by_default() -> None:
    config = _config()
    worker_stats = (
        WorkerRawStats(
            worker_index=0,
            reader_count=1,
            batch_mismatches=0,
            read_errors=0,
            missing_response_timestamps=0,
            response_timestamps_by_reader=((1.0, 1.1, 1.2),),
            max_observed_concurrent_reads=1,
            total_reads=20,
            ok_reads=20,
            value_count=1,
        ),
    )

    metrics = build_level_metrics(
        worker_stats,
        server_count=1,
        point_total=10,
        target_hz=10.0,
        config=config,
    )

    assert metrics.value_delivery_ratio == pytest.approx(0.005)
    assert metrics.value_missing_count == 199
    assert metrics.passed is True
