"""Tests for subscription metric aggregation and pass/fail evaluation."""

from __future__ import annotations

from dataclasses import replace
from typing import Any, cast

from tools.source_lab.access.common.access_model import AccessBatch, AccessMode, AccessRunSummary
from tools.source_lab.access.polling.model import CapacityMode
from tools.source_lab.access.subscribe.metrics import build_subscribe_level_metrics
from tools.source_lab.access.subscribe.model import (
    SubscribeEndpointDispatchTrace,
    SubscribeScanConfig,
    SubscribeWorkerRawStats,
)


def _config(**overrides: object) -> SubscribeScanConfig:
    config = SubscribeScanConfig(
        mode=CapacityMode.SIMULATOR,
        protocol="opcua",
        server_count_start=1,
        server_count_step=1,
        server_count_max=1,
        process_count=1,
        publishing_interval_ms=100.0,
        sampling_interval_ms=100.0,
        queue_size=1,
        duration_s=10.0,
        source_update_enabled=True,
    )
    return replace(config, **cast(dict[str, Any], overrides))


def _batch(
    *,
    sequence: int = 1,
    endpoint_index: int = 0,
    value_count: int = 1,
    bad_count: int = 0,
    missing_timestamp_count: int = 0,
    received_ns: int = 1_000_000_000,
    notify_timestamp_ns: int | None = None,
    flush_timestamp_ns: int | None = None,
    publish_ts_s: float | None = 1712345678.0,
    data_age_ms: float | None = 5.0,
) -> AccessBatch:
    return AccessBatch(
        endpoint_id=f"ep-{endpoint_index}",
        profile_id="pf-1",
        protocol="opcua",
        access_mode=AccessMode.SUBSCRIBE,
        worker_index=0,
        local_index=endpoint_index,
        global_index=endpoint_index,
        batch_index=sequence - 1,
        sequence=sequence,
        scheduled_ns=None,
        started_ns=None,
        received_ns=received_ns,
        source_timestamp_s=publish_ts_s,
        server_timestamp_s=publish_ts_s,
        value_count=value_count,
        expected_count=1,
        bad_count=bad_count,
        missing_timestamp_count=missing_timestamp_count,
        error_code=None,
        data_age_ms=data_age_ms,
        period_ms=None,
        notify_timestamp_ns=notify_timestamp_ns,
        flush_timestamp_ns=flush_timestamp_ns,
    )


def _stats(
    *,
    batches: tuple[AccessBatch, ...],
    monitored_created: int = 1,
    expected_monitored_items: int = 1,
    monitored_failed: int = 0,
    bad_count: int = 0,
    missing_ts_count: int = 0,
    keepalive_count: int = 0,
    keepalive_miss_count: int = 0,
    publish_timeout_count: int = 0,
    resubscribe_count: int = 0,
    resubscribe_success_count: int = 0,
    resubscribe_failure_count: int = 0,
    unrecovered_endpoint_count: int = 0,
    endpoint_diagnostics: tuple[SubscribeEndpointDispatchTrace, ...] = (),
    runner_protocol_noise_count: int = 0,
    runner_protocol_noise_samples: tuple[str, ...] = (),
) -> SubscribeWorkerRawStats:
    return SubscribeWorkerRawStats(
        worker_index=0,
        endpoint_count=1,
        expected_monitored_items=expected_monitored_items,
        monitored_created=monitored_created,
        monitored_failed=monitored_failed,
        batches=batches,
        notification_count=len(batches),
        value_count=sum(batch.value_count for batch in batches),
        bad_count=bad_count,
        missing_ts_count=missing_ts_count,
        reserved_sequence_gap_count=0,
        reserved_queue_overflow_count=0,
        keepalive_count=keepalive_count,
        publish_timeout_count=publish_timeout_count,
        reconnect_count=0,
        keepalive_miss_count=keepalive_miss_count,
        resubscribe_count=resubscribe_count,
        resubscribe_success_count=resubscribe_success_count,
        resubscribe_failure_count=resubscribe_failure_count,
        unrecovered_endpoint_count=unrecovered_endpoint_count,
        summary=AccessRunSummary(
            access_mode=AccessMode.SUBSCRIBE,
            worker_index=0,
            endpoint_count=1,
            expected_point_count=expected_monitored_items,
            batch_count=len(batches),
            value_count=sum(batch.value_count for batch in batches),
            bad_count=bad_count,
            missing_timestamp_count=missing_ts_count,
            error_count=monitored_failed,
        ),
        endpoint_diagnostics=endpoint_diagnostics,
        runner_protocol_noise_count=runner_protocol_noise_count,
        runner_protocol_noise_samples=runner_protocol_noise_samples,
    )


def test_subscribe_data_period_metrics_use_notify_receive_diffs_per_server() -> None:
    metrics = build_subscribe_level_metrics(
        (
            _stats(
                batches=(
                    _batch(sequence=1, endpoint_index=0, publish_ts_s=10.0, received_ns=0),
                    _batch(sequence=2, endpoint_index=0, publish_ts_s=10.4, received_ns=100_000_000),
                    _batch(sequence=3, endpoint_index=0, publish_ts_s=10.8, received_ns=200_000_000),
                    _batch(sequence=1, endpoint_index=1, publish_ts_s=20.0, received_ns=0),
                    _batch(sequence=2, endpoint_index=1, publish_ts_s=20.4, received_ns=100_000_000),
                    _batch(sequence=3, endpoint_index=1, publish_ts_s=20.8, received_ns=250_000_000),
                )
            ),
        ),
        server_count=2,
        config=_config(
            source_update_hz=2.5,
            data_period_max_tolerance_ratio=0.6,
            runner_trace_enabled=True,
            runner_trace_top_n=2,
        ),
    )

    assert metrics.data_period_samples == 4
    assert metrics.data_period_p95_ms == 142.5
    assert metrics.data_period_max_ms == 150.0
    assert metrics.source_period_max_ms == 400.0
    assert metrics.passed is True


def test_subscribe_data_period_metrics_prefer_notify_timestamp_over_received_ns() -> None:
    metrics = build_subscribe_level_metrics(
        (
            _stats(
                batches=(
                    _batch(sequence=1, endpoint_index=0, publish_ts_s=10.0, notify_timestamp_ns=0, received_ns=0),
                    _batch(
                        sequence=2,
                        endpoint_index=0,
                        publish_ts_s=10.4,
                        notify_timestamp_ns=100_000_000,
                        received_ns=180_000_000,
                    ),
                    _batch(
                        sequence=3,
                        endpoint_index=0,
                        publish_ts_s=10.8,
                        notify_timestamp_ns=200_000_000,
                        received_ns=360_000_000,
                    ),
                    _batch(sequence=1, endpoint_index=1, publish_ts_s=20.0, notify_timestamp_ns=0, received_ns=0),
                    _batch(
                        sequence=2,
                        endpoint_index=1,
                        publish_ts_s=20.4,
                        notify_timestamp_ns=100_000_000,
                        received_ns=200_000_000,
                    ),
                    _batch(
                        sequence=3,
                        endpoint_index=1,
                        publish_ts_s=20.8,
                        notify_timestamp_ns=250_000_000,
                        received_ns=400_000_000,
                    ),
                )
            ),
        ),
        server_count=2,
        config=_config(
            source_update_hz=2.5,
            data_period_max_tolerance_ratio=0.6,
            runner_trace_enabled=True,
            runner_trace_top_n=2,
        ),
    )

    assert metrics.data_period_samples == 4
    assert metrics.data_period_p95_ms == 142.5
    assert metrics.data_period_max_ms == 150.0
    assert metrics.recv_period_max_ms == 200.0
    assert metrics.callback_to_flush_lag_max_ms == 0.0
    assert metrics.data_period_max_ms != 200.0
    assert "notify_timestamp_missing_fallback_received_ns" not in metrics.warnings
    assert "callback_to_flush_lag_unavailable" in metrics.warnings
    assert metrics.top_period_gap_traces == ()
    assert metrics.top_data_period_gap_traces[0].period_ms == 150.0
    assert metrics.top_flush_lag_traces == ()


def test_subscribe_data_period_falls_back_to_received_ns_when_notify_timestamp_missing() -> None:
    metrics = build_subscribe_level_metrics(
        (
            _stats(
                batches=(
                    _batch(sequence=1, endpoint_index=0, publish_ts_s=None, received_ns=0),
                    _batch(sequence=2, endpoint_index=0, publish_ts_s=None, received_ns=180_000_000),
                    _batch(sequence=3, endpoint_index=0, publish_ts_s=None, received_ns=360_000_000),
                )
            ),
        ),
        server_count=1,
        config=_config(data_period_max_tolerance_ratio=1.0),
    )

    assert metrics.data_period_max_ms == 180.0
    assert "notify_timestamp_missing_fallback_received_ns" in metrics.warnings


def test_low_value_delivery_ratio_does_not_fail_by_default() -> None:
    metrics = build_subscribe_level_metrics(
        (
            _stats(
                batches=(
                    _batch(sequence=1, publish_ts_s=10.0, value_count=1),
                    _batch(sequence=2, publish_ts_s=10.1, value_count=0),
                )
            ),
        ),
        server_count=1,
        config=_config(duration_s=20.0, sampling_interval_ms=100.0),
    )

    assert metrics.expected_value_count == 200
    assert metrics.value_count == 1
    assert metrics.value_delivery_ratio == 0.005
    assert metrics.value_missing_count == 199
    assert metrics.passed is True


def test_data_period_max_within_tolerance_passes() -> None:
    metrics = build_subscribe_level_metrics(
        (
            _stats(
                batches=(
                    _batch(sequence=1, publish_ts_s=None, received_ns=0),
                    _batch(sequence=2, publish_ts_s=None, received_ns=100_000_000),
                    _batch(sequence=3, publish_ts_s=None, received_ns=219_000_000),
                )
            ),
        ),
        server_count=1,
        config=_config(),
    )

    assert metrics.allowed_data_period_max_ms == 120.0
    assert metrics.data_period_max_ms == 119.0
    assert metrics.passed is True


def test_data_period_max_over_tolerance_fails() -> None:
    metrics = build_subscribe_level_metrics(
        (
            _stats(
                batches=(
                    _batch(sequence=1, publish_ts_s=None, received_ns=0),
                    _batch(sequence=2, publish_ts_s=None, received_ns=100_000_000),
                    _batch(sequence=3, publish_ts_s=None, received_ns=245_200_000),
                )
            ),
        ),
        server_count=1,
        config=_config(),
    )

    assert metrics.passed is False
    assert "data_period_max_ms=145.20>120.00" in metrics.failure_reason


def test_data_period_tolerance_ratio_changes_reason_limit() -> None:
    strict = build_subscribe_level_metrics(
        (
            _stats(
                batches=(
                    _batch(sequence=1, publish_ts_s=None, received_ns=0),
                    _batch(sequence=2, publish_ts_s=None, received_ns=100_000_000),
                    _batch(sequence=3, publish_ts_s=None, received_ns=245_000_000),
                )
            ),
        ),
        server_count=1,
        config=_config(),
    )
    relaxed = build_subscribe_level_metrics(
        (
            _stats(
                batches=(
                    _batch(sequence=1, publish_ts_s=None, received_ns=0),
                    _batch(sequence=2, publish_ts_s=None, received_ns=100_000_000),
                    _batch(sequence=3, publish_ts_s=None, received_ns=245_000_000),
                )
            ),
        ),
        server_count=1,
        config=_config(data_period_max_tolerance_ratio=0.5),
    )

    assert strict.allowed_data_period_max_ms == 120.0
    assert strict.passed is False
    assert "120.00" in strict.failure_reason
    assert relaxed.allowed_data_period_max_ms == 150.0
    assert relaxed.data_period_max_ms == 145.0
    assert relaxed.passed is True


def test_allowed_data_period_uses_source_update_hz_when_sample_hz_is_higher() -> None:
    metrics = build_subscribe_level_metrics(
        (
            _stats(
                batches=(
                    _batch(sequence=1, notify_timestamp_ns=0, received_ns=0),
                    _batch(sequence=2, notify_timestamp_ns=100_000_000, received_ns=50_000_000),
                    _batch(sequence=3, notify_timestamp_ns=200_000_000, received_ns=100_000_000),
                )
            ),
        ),
        server_count=1,
        config=_config(
            sampling_interval_ms=50.0,
            nominal_sample_hz=20.0,
            source_update_hz=10.0,
            data_period_max_tolerance_ratio=0.2,
        ),
    )

    assert metrics.allowed_data_period_max_ms == 120.0
    assert metrics.data_period_max_ms == 100.0
    assert metrics.passed is True


def test_source_period_remains_detail_only_diagnostic() -> None:
    metrics = build_subscribe_level_metrics(
        (
            _stats(
                batches=(
                    _batch(sequence=1, publish_ts_s=10.0, received_ns=0, value_count=1),
                    _batch(sequence=2, publish_ts_s=10.4, received_ns=100_000_000, value_count=0),
                    _batch(sequence=3, publish_ts_s=10.8, received_ns=200_000_000, value_count=0),
                )
            ),
        ),
        server_count=1,
        config=_config(duration_s=30.0),
    )

    assert metrics.data_period_max_ms == 0.0
    assert metrics.source_period_max_ms == 400.0
    assert metrics.value_delivery_ratio < 0.1
    assert metrics.passed is True


def test_source_period_stays_separate_from_notify_period() -> None:
    metrics = build_subscribe_level_metrics(
        (
            _stats(
                batches=(
                    _batch(sequence=1, publish_ts_s=10.0, notify_timestamp_ns=0, received_ns=0),
                    _batch(sequence=2, publish_ts_s=10.4, notify_timestamp_ns=100_000_000, received_ns=180_000_000),
                    _batch(sequence=3, publish_ts_s=10.8, notify_timestamp_ns=200_000_000, received_ns=360_000_000),
                )
            ),
        ),
        server_count=1,
        config=_config(source_update_hz=10.0, sampling_interval_ms=50.0, nominal_sample_hz=20.0),
    )

    assert metrics.data_period_max_ms == 100.0
    assert metrics.source_period_max_ms == 400.0


def test_response_period_limit_only_warns_and_does_not_fail() -> None:
    metrics = build_subscribe_level_metrics(
        (
            _stats(
                batches=(
                    _batch(sequence=1, notify_timestamp_ns=0, received_ns=0),
                    _batch(sequence=2, notify_timestamp_ns=100_000_000, received_ns=150_000_000),
                    _batch(sequence=3, notify_timestamp_ns=200_000_000, received_ns=300_000_000),
                )
            ),
        ),
        server_count=1,
        config=_config(source_update_enabled=True, source_update_hz=10.0, sampling_interval_ms=100.0),
    )

    assert metrics.data_period_max_ms == 100.0
    assert metrics.response_period_max_ms == 150.0
    assert "high_response_period_max" in metrics.warnings
    assert metrics.passed is True


def test_keepalive_only_batches_do_not_contribute_to_data_period() -> None:
    metrics = build_subscribe_level_metrics(
        (
            _stats(
                batches=(
                    _batch(sequence=1, value_count=0, publish_ts_s=10.0, notify_timestamp_ns=0, received_ns=0),
                    _batch(sequence=2, value_count=0, publish_ts_s=10.2, notify_timestamp_ns=200_000_000, received_ns=200_000_000),
                ),
                keepalive_count=2,
            ),
        ),
        server_count=1,
        config=_config(),
    )

    assert metrics.data_period_samples == 0
    assert metrics.data_period_max_ms == 0.0
    assert "keepalive_seen" in metrics.warnings


def test_resubscribe_success_only_warns() -> None:
    metrics = build_subscribe_level_metrics(
        (
            _stats(
                batches=(
                    _batch(sequence=1, notify_timestamp_ns=0, received_ns=0),
                    _batch(sequence=2, notify_timestamp_ns=100_000_000, received_ns=100_000_000),
                ),
                resubscribe_count=1,
                resubscribe_success_count=1,
            ),
        ),
        server_count=1,
        config=_config(),
    )

    assert metrics.passed is True
    assert "recovered_after_resubscribe" in metrics.warnings


def test_unrecovered_endpoint_fails() -> None:
    metrics = build_subscribe_level_metrics(
        (
            _stats(
                batches=(
                    _batch(sequence=1, notify_timestamp_ns=0, received_ns=0),
                    _batch(sequence=2, notify_timestamp_ns=100_000_000, received_ns=100_000_000),
                ),
                resubscribe_count=1,
                resubscribe_failure_count=1,
                unrecovered_endpoint_count=1,
            ),
        ),
        server_count=1,
        config=_config(),
    )

    assert metrics.passed is False
    assert "unrecovered_endpoint" in metrics.failure_reason


def test_insufficient_data_period_samples_only_warns() -> None:
    metrics = build_subscribe_level_metrics(
        (_stats(batches=(_batch(sequence=1, publish_ts_s=10.0),)),),
        server_count=1,
        config=_config(),
    )

    assert metrics.passed is True
    assert "insufficient_notify_period_samples" in metrics.warnings


def test_no_data_fails() -> None:
    metrics = build_subscribe_level_metrics(
        (_stats(batches=()),),
        server_count=1,
        config=_config(),
    )

    assert metrics.passed is False
    assert "no_data" in metrics.failure_reason


def test_created_items_is_hard_failure() -> None:
    metrics = build_subscribe_level_metrics(
        (
            _stats(
                batches=(
                    _batch(sequence=1, publish_ts_s=10.0),
                    _batch(sequence=2, publish_ts_s=10.1),
                ),
                monitored_created=0,
                expected_monitored_items=1,
                monitored_failed=1,
            ),
        ),
        server_count=1,
        config=_config(),
    )

    assert metrics.passed is False
    assert "created_items=0<1" in metrics.failure_reason


def test_bad_missing_timestamp_and_noise_are_hard_failures() -> None:
    metrics = build_subscribe_level_metrics(
        (
            _stats(
                batches=(
                    _batch(sequence=1, publish_ts_s=10.0, bad_count=1, missing_timestamp_count=1),
                    _batch(sequence=2, publish_ts_s=10.1),
                ),
                bad_count=1,
                missing_ts_count=1,
                runner_protocol_noise_count=1,
                runner_protocol_noise_samples=("noise",),
            ),
        ),
        server_count=1,
        config=_config(),
    )

    assert metrics.passed is False
    assert "bad_status_code" in metrics.failure_reason
    assert "missing_source_timestamp" in metrics.failure_reason
    assert "runner_protocol_noise" in metrics.failure_reason


def test_callback_to_flush_lag_uses_flush_timestamp_and_not_received_ns() -> None:
    metrics = build_subscribe_level_metrics(
        (
            _stats(
                batches=(
                    _batch(
                        sequence=1,
                        notify_timestamp_ns=1_000_000_000,
                        flush_timestamp_ns=1_001_000_000,
                        received_ns=1_002_000_000,
                    ),
                    _batch(
                        sequence=2,
                        notify_timestamp_ns=1_100_000_000,
                        flush_timestamp_ns=1_101_500_000,
                        received_ns=1_103_000_000,
                    ),
                )
            ),
        ),
        server_count=1,
        config=_config(runner_trace_enabled=True, runner_trace_top_n=2),
    )

    assert metrics.callback_to_flush_lag_p95_ms == 1.475
    assert metrics.callback_to_flush_lag_max_ms == 1.5
    assert metrics.recv_period_max_ms == 101.0
    assert metrics.callback_to_flush_lag_max_ms != 3.0
    assert metrics.top_flush_lag_traces[0].lag_ms == 1.5


def test_callback_to_flush_lag_warns_when_flush_timestamp_missing() -> None:
    metrics = build_subscribe_level_metrics(
        (
            _stats(
                batches=(
                    _batch(sequence=1, notify_timestamp_ns=1_000_000_000, received_ns=1_002_000_000),
                    _batch(sequence=2, notify_timestamp_ns=1_100_000_000, received_ns=1_103_000_000),
                )
            ),
        ),
        server_count=1,
        config=_config(runner_trace_enabled=True, runner_trace_top_n=2),
    )

    assert metrics.callback_to_flush_lag_p95_ms == 0.0
    assert metrics.callback_to_flush_lag_max_ms == 0.0
    assert "callback_to_flush_lag_unavailable" in metrics.warnings
    assert metrics.top_flush_lag_traces == ()


def test_callback_to_flush_lag_warns_on_negative_samples() -> None:
    metrics = build_subscribe_level_metrics(
        (
            _stats(
                batches=(
                    _batch(
                        sequence=1,
                        notify_timestamp_ns=1_000_000_000,
                        flush_timestamp_ns=999_000_000,
                        received_ns=1_002_000_000,
                    ),
                    _batch(
                        sequence=2,
                        notify_timestamp_ns=1_100_000_000,
                        flush_timestamp_ns=1_101_000_000,
                        received_ns=1_103_000_000,
                    ),
                )
            ),
        ),
        server_count=1,
        config=_config(runner_trace_enabled=True, runner_trace_top_n=2),
    )

    assert metrics.callback_to_flush_lag_p95_ms == 1.0
    assert metrics.callback_to_flush_lag_max_ms == 1.0
    assert "negative_callback_to_flush_lag" in metrics.warnings
    assert len(metrics.top_flush_lag_traces) == 1


def test_dispatch_gap_diagnostics_flow_into_metrics_and_warnings() -> None:
    metrics = build_subscribe_level_metrics(
        (
            _stats(
                batches=(
                    _batch(sequence=1, notify_timestamp_ns=1_000_000_000, received_ns=1_000_000_000),
                    _batch(sequence=2, notify_timestamp_ns=1_100_000_000, received_ns=1_100_000_000),
                ),
                endpoint_diagnostics=(
                    SubscribeEndpointDispatchTrace(
                        worker_index=0,
                        local_index=0,
                        global_index=0,
                        notification_count=2,
                        run_iterate_count=20,
                        max_dispatch_gap_ms=60.0,
                        max_run_iterate_duration_ms=0.25,
                        revised_publishing_interval_ms=100.0,
                        revised_sampling_interval_ms=100.0,
                    ),
                ),
            ),
        ),
        server_count=1,
        config=_config(runner_trace_enabled=True, runner_trace_top_n=2),
    )

    assert metrics.dispatch_gap_max_ms == 60.0
    assert metrics.run_iterate_duration_max_ms == 0.25
    assert metrics.top_dispatch_gap_traces[0].run_iterate_count == 20
    assert "endpoint_dispatch_gap_over_half_period" in metrics.warnings
