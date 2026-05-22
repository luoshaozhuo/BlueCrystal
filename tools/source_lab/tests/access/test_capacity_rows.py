"""Tests for final-attempt metric selection in capacity rows."""

from __future__ import annotations

from tools.source_lab.access.capacity import (
    SubscribeCapacityComboResult,
    SubscribeCapacityResult,
    build_polling_capacity_rows,
    build_subscribe_capacity_rows,
)
from tools.source_lab.access.polling.model import (
    CapacityLevelMetrics,
    CapacityMode,
    CapacityScanConfig,
    CapacityScanResult,
    CapacityStatus,
    ConfirmedLevelResult,
)
from tools.source_lab.access.subscribe.model import (
    SubscribeLevelMetrics,
    SubscribeLevelResult,
)


def _polling_config() -> CapacityScanConfig:
    return CapacityScanConfig(
        mode=CapacityMode.SIMULATOR,
        protocol="opcua",
        endpoints=(),
        points=(),
        server_count_start=40,
        server_count_step=1,
        server_count_max=40,
        hz_start=30.0,
        hz_step=30.0,
        hz_max=30.0,
        process_count=3,
        progress_enabled=False,
    )


def _polling_metrics(
    *,
    server_count: int,
    target_hz: float,
    p95_ms: float,
    max_ms: float,
    failure_reason: str,
    passed: bool,
) -> CapacityLevelMetrics:
    return CapacityLevelMetrics(
        server_count=server_count,
        target_hz=target_hz,
        target_period_ms=round(1000.0 / target_hz, 1),
        allowed_period_max_ms=round((1000.0 / target_hz) * 1.2, 1),
        allowed_period_mean_abs_error_ms=round((1000.0 / target_hz) * 0.05, 2),
        read_errors=0,
        batch_mismatches=0,
        missing_response_timestamps=0,
        period_samples=10,
        period_mean_ms=round(1000.0 / target_hz, 2),
        period_p95_ms=p95_ms,
        period_max_ms=max_ms,
        period_mean_abs_error_ms=0.0,
        missed_ticks=0,
        runner_max_lag_ms=0.0,
        runner_max_read_ms=0.0,
        worker_conc_sum=3,
        worker_conc_max=1,
        worker_conc_by_worker=(1, 1, 1),
        value_count_ok=True,
        period_max_ok=passed,
        period_mean_ok=True,
        passed=passed,
        failure_reason=failure_reason,
        points_per_server=3,
        point_total=server_count * 3,
        expected_value_count=100,
        value_count=90,
        value_delivery_ratio=0.9,
        value_missing_count=10,
        read_count=100,
        batch_count=100,
        worst_gap=None,
        top_gaps=(),
        warnings=(),
    )


def _subscribe_metrics(
    *,
    data_period_p95_ms: float,
    data_period_max_ms: float,
    source_period_p95_ms: float = 0.0,
    source_period_max_ms: float = 0.0,
    passed: bool,
    failure_reason: str,
    value_ratio: float = 0.1,
) -> SubscribeLevelMetrics:
    return SubscribeLevelMetrics(
        server_count=10,
        process_count=1,
        publishing_interval_ms=100.0,
        sampling_interval_ms=100.0,
        effective_source_update_hz=10.0,
        queue_size=1,
        expected_monitored_items=30,
        monitored_created=30,
        monitored_failed=0,
        notification_count=250,
        value_count=75,
        bad_count=0,
        missing_ts_count=0,
        reserved_sequence_gap_count=0,
        reserved_queue_overflow_count=0,
        keepalive_count=0,
        publish_timeout_count=0,
        reconnect_count=0,
        notification_rate=25.0,
        value_rate=7.5,
        publish_gap_mean_ms=110.0,
        publish_gap_p95_ms=120.0,
        publish_gap_p99_ms=125.0,
        publish_gap_max_ms=130.0,
        data_age_mean_ms=10.0,
        data_age_p95_ms=15.0,
        data_age_p99_ms=16.0,
        data_age_max_ms=17.0,
        data_period_samples=20,
        data_period_mean_ms=100.0,
        data_period_p95_ms=data_period_p95_ms,
        data_period_max_ms=data_period_max_ms,
        allowed_data_period_max_ms=120.0,
        passed=passed,
        failure_reason=failure_reason,
        points_per_server=3,
        point_total=30,
        expected_notification_count=300,
        expected_value_count=750,
        value_delivery_ratio=value_ratio,
        value_missing_count=675,
        source_period_p95_ms=source_period_p95_ms,
        source_period_max_ms=source_period_max_ms,
        warnings=(),
        batches=(),
        summaries=(),
        top_data_age_traces=(),
        runner_protocol_noise_count=0,
        runner_protocol_noise_samples=(),
    )


def test_polling_flaky_row_uses_recovered_attempt_metrics() -> None:
    first = _polling_metrics(
        server_count=40,
        target_hz=30.0,
        p95_ms=2100.0,
        max_ms=2729.49,
        failure_reason="data_period_max_ms=2729.49>40.00",
        passed=False,
    )
    second = _polling_metrics(
        server_count=40,
        target_hz=30.0,
        p95_ms=34.0,
        max_ms=35.0,
        failure_reason="",
        passed=True,
    )
    result = CapacityScanResult(
        config=_polling_config(),
        levels=(
            ConfirmedLevelResult(
                primary=first,
                attempts=(first, second),
                final_status=CapacityStatus.FLAKY,
                final_reason="recovered on attempt 2",
            ),
        ),
    )

    row = build_polling_capacity_rows(result)[0]

    assert row.status == "FLAKY"
    assert row.reason == "recovered on attempt 2"
    assert row.data_period_p95_ms == 34.0
    assert row.data_period_max_ms == 35.0


def test_polling_fail_row_uses_final_failed_attempt_metrics() -> None:
    first = _polling_metrics(
        server_count=20,
        target_hz=55.0,
        p95_ms=20.0,
        max_ms=50.0,
        failure_reason="data_period_max_ms=50.00>48.00",
        passed=False,
    )
    second = _polling_metrics(
        server_count=20,
        target_hz=55.0,
        p95_ms=22.0,
        max_ms=55.0,
        failure_reason="data_period_max_ms=55.00>48.00",
        passed=False,
    )
    result = CapacityScanResult(
        config=_polling_config(),
        levels=(
            ConfirmedLevelResult(
                primary=first,
                attempts=(first, second),
                final_status=CapacityStatus.FAIL,
        final_reason="data_period_max_ms=55.00>48.00",
            ),
        ),
    )

    row = build_polling_capacity_rows(result)[0]

    assert row.status == "FAIL"
    assert row.reason == "max=55.00>48.00"
    assert row.data_period_max_ms == 55.0
    assert row.data_period_p95_ms == 22.0


def test_polling_pass_row_uses_pass_attempt_metrics() -> None:
    metrics = _polling_metrics(
        server_count=10,
        target_hz=5.0,
        p95_ms=198.0,
        max_ms=201.0,
        failure_reason="",
        passed=True,
    )
    result = CapacityScanResult(
        config=_polling_config(),
        levels=(
            ConfirmedLevelResult(
                primary=metrics,
                attempts=(metrics,),
                final_status=CapacityStatus.PASS,
                final_reason="",
            ),
        ),
    )

    row = build_polling_capacity_rows(result)[0]

    assert row.status == "PASS"
    assert row.reason == ""
    assert row.data_period_max_ms == 201.0


def test_subscribe_row_uses_final_metrics_and_not_value_ratio_for_status() -> None:
    final_metrics = _subscribe_metrics(
        data_period_p95_ms=101.0,
        data_period_max_ms=119.0,
        source_period_p95_ms=400.0,
        source_period_max_ms=400.0,
        passed=True,
        failure_reason="",
        value_ratio=0.02,
    )
    combo = SubscribeCapacityComboResult(
        process_count=1,
        server_count=10,
        sample_hz=10.0,
        effective_source_update_hz=10.0,
        result=SubscribeLevelResult(
            primary=final_metrics,
            attempts=(final_metrics,),
            final_status=CapacityStatus.PASS,
            final_reason="",
        ),
        status=CapacityStatus.PASS,
        reason="",
    )
    rows = build_subscribe_capacity_rows(
        SubscribeCapacityResult(combos=(combo,), limit_summaries=()),
        protocol="opcua",
    )

    row = rows[0]
    assert row.status == "PASS"
    assert row.reason == ""
    assert row.value_ratio == 0.02
    assert row.data_period_max_ms == 119.0
    assert row.source_period_max_ms == 400.0
