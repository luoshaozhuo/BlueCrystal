"""Metrics helpers for subscription scan evaluation."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Sequence
import math

from tools.source_lab.access.common.access_model import AccessBatch
from tools.source_lab.access.subscribe.model import (
    SubscribeEndpointDispatchTrace,
    SubscribeFlushLagTrace,
    SubscribeLevelMetrics,
    SubscribePeriodGapTrace,
    SubscribeScanConfig,
    SubscribeWorkerRawStats,
)


def _percentile(values: Sequence[float], percentile: float) -> float:
    """Compute an inclusive percentile on a non-empty float sequence."""

    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    rank = percentile * (len(ordered) - 1)
    lower = math.floor(rank)
    upper = math.ceil(rank)
    if lower == upper:
        return ordered[lower]
    fraction = rank - lower
    return ordered[lower] + ((ordered[upper] - ordered[lower]) * fraction)


def _stat_bundle(values: Sequence[float]) -> tuple[float, float, float, float]:
    """Return mean, p95, p99, and max for one value set."""

    if not values:
        return 0.0, 0.0, 0.0, 0.0
    return (
        sum(values) / len(values),
        _percentile(values, 0.95),
        _percentile(values, 0.99),
        max(values),
    )


def _periods_from_int_ns(
    batches: Sequence[AccessBatch],
    timestamp_ns_getter: Callable[[AccessBatch], int | None],
) -> list[float]:
    """Build per-endpoint adjacent periods from one integer-nanosecond timestamp."""

    grouped: dict[int, list[int]] = defaultdict(list)
    for batch in batches:
        timestamp_ns = timestamp_ns_getter(batch)
        if timestamp_ns is None:
            continue
        grouped[batch.global_index].append(timestamp_ns)

    gaps: list[float] = []
    for timestamps in grouped.values():
        ordered = sorted(timestamps)
        for previous_ns, current_ns in zip(ordered, ordered[1:]):
            gaps.append((current_ns - previous_ns) / 1_000_000.0)
    return gaps


def _publish_gaps_ms(batches: Sequence[AccessBatch]) -> list[float]:
    """Build per-endpoint publish gaps from received timestamps."""

    return _periods_from_int_ns(batches, lambda batch: batch.received_ns)


def _notify_periods_ms(batches: Sequence[AccessBatch]) -> tuple[list[float], bool]:
    """Build per-endpoint notify periods from callback timestamps when available."""

    notify_timestamp_count = sum(1 for batch in batches if batch.notify_timestamp_ns is not None)
    if notify_timestamp_count > 0:
        return (
            _periods_from_int_ns(batches, lambda batch: batch.notify_timestamp_ns),
            False,
        )
    return (_periods_from_int_ns(batches, lambda batch: batch.received_ns), bool(batches))


def _data_notify_batches(batches: Sequence[AccessBatch]) -> tuple[AccessBatch, ...]:
    """Filter batches down to real data-bearing notify events."""

    return tuple(batch for batch in batches if batch.value_count > 0)


def _notify_period_gap_traces(
    batches: Sequence[AccessBatch],
    *,
    top_n: int,
) -> tuple[tuple[SubscribePeriodGapTrace, ...], bool]:
    """Build top notify-period gap traces per endpoint using primary timestamps."""

    grouped: dict[int, list[AccessBatch]] = defaultdict(list)
    notify_timestamp_count = 0
    for batch in batches:
        if batch.notify_timestamp_ns is not None:
            notify_timestamp_count += 1
        grouped[batch.global_index].append(batch)
    use_notify_timestamp = notify_timestamp_count > 0

    traces: list[SubscribePeriodGapTrace] = []
    for endpoint_batches in grouped.values():
        if use_notify_timestamp:
            ordered = sorted(
                (batch for batch in endpoint_batches if batch.notify_timestamp_ns is not None),
                key=lambda batch: batch.notify_timestamp_ns or 0,
            )
        else:
            ordered = sorted(endpoint_batches, key=lambda batch: batch.received_ns)
        for previous_batch, current_batch in zip(ordered, ordered[1:]):
            previous_ns = previous_batch.notify_timestamp_ns if use_notify_timestamp else previous_batch.received_ns
            current_ns = current_batch.notify_timestamp_ns if use_notify_timestamp else current_batch.received_ns
            if previous_ns is None or current_ns is None:
                continue
            traces.append(
                SubscribePeriodGapTrace(
                    worker_index=current_batch.worker_index,
                    local_index=current_batch.local_index,
                    global_index=current_batch.global_index,
                    previous_notify_timestamp_ns=previous_ns,
                    notify_timestamp_ns=current_ns,
                    period_ms=(current_ns - previous_ns) / 1_000_000.0,
                )
            )
    traces = sorted(traces, key=lambda item: item.period_ms, reverse=True)
    return tuple(traces[:top_n]), not use_notify_timestamp


def _callback_to_flush_lag_values_ms(batches: Sequence[AccessBatch]) -> list[float]:
    """Build callback-to-flush lag values from same-clock monotonic timestamps."""

    values, _warnings = _callback_to_flush_lag_samples(batches)
    return values


def _callback_to_flush_lag_samples(
    batches: Sequence[AccessBatch],
) -> tuple[list[float], tuple[str, ...]]:
    """Build callback-to-flush lag samples and warnings.

    Lag is only valid when both notify and flush timestamps exist in the same
    monotonic clock domain.
    """

    values: list[float] = []
    warnings: list[str] = []
    missing_flush_seen = False
    negative_seen = False
    for batch in batches:
        if batch.notify_timestamp_ns is None:
            continue
        if batch.flush_timestamp_ns is None:
            missing_flush_seen = True
            continue
        lag_ns = batch.flush_timestamp_ns - batch.notify_timestamp_ns
        if lag_ns < 0:
            negative_seen = True
            continue
        values.append(lag_ns / 1_000_000.0)
    if missing_flush_seen:
        warnings.append("callback_to_flush_lag_unavailable")
    if negative_seen:
        warnings.append("negative_callback_to_flush_lag")
    return values, tuple(warnings)


def _top_flush_lag_traces(
    batches: Sequence[AccessBatch],
    *,
    top_n: int,
) -> tuple[SubscribeFlushLagTrace, ...]:
    """Build top callback-to-flush lag traces."""

    traces = sorted(
        (
            SubscribeFlushLagTrace(
                worker_index=batch.worker_index,
                local_index=batch.local_index,
                global_index=batch.global_index,
                notify_timestamp_ns=batch.notify_timestamp_ns,
                flush_timestamp_ns=batch.flush_timestamp_ns,
                lag_ms=(batch.flush_timestamp_ns - batch.notify_timestamp_ns) / 1_000_000.0,
            )
            for batch in batches
            if (
                batch.notify_timestamp_ns is not None
                and batch.flush_timestamp_ns is not None
                and batch.flush_timestamp_ns >= batch.notify_timestamp_ns
            )
        ),
        key=lambda item: item.lag_ms,
        reverse=True,
    )
    return tuple(traces[:top_n])


def _source_periods_ms(batches: Sequence[AccessBatch]) -> list[float]:
    """Build per-endpoint adjacent periods from source/server timestamps."""

    grouped: dict[int, list[float]] = defaultdict(list)
    for batch in batches:
        timestamp_s = batch.source_timestamp_s
        if timestamp_s is None:
            timestamp_s = batch.server_timestamp_s
        if timestamp_s is None:
            continue
        grouped[batch.global_index].append(timestamp_s)

    periods: list[float] = []
    for timestamps in grouped.values():
        ordered = sorted(timestamps)
        for previous_s, current_s in zip(ordered, ordered[1:]):
            delta_ms = (current_s - previous_s) * 1000.0
            if delta_ms >= 0:
                periods.append(delta_ms)
    return periods


def _data_periods_ms(
    batches: Sequence[AccessBatch],
) -> tuple[list[float], bool]:
    """Build data-notify periods from notify timestamps or received time."""

    return _notify_periods_ms(batches)


def _top_dispatch_gap_traces(
    worker_stats: Sequence[SubscribeWorkerRawStats],
    *,
    top_n: int,
) -> tuple[SubscribeEndpointDispatchTrace, ...]:
    """Build top per-endpoint dispatch gap diagnostics."""

    traces = sorted(
        (
            trace
            for worker in worker_stats
            for trace in worker.endpoint_diagnostics
        ),
        key=lambda item: item.max_dispatch_gap_ms,
        reverse=True,
    )
    return tuple(traces[:top_n])


def build_subscribe_level_metrics(
    worker_stats: Sequence[SubscribeWorkerRawStats],
    *,
    server_count: int,
    config: SubscribeScanConfig,
) -> SubscribeLevelMetrics:
    """Build one subscription level metrics object from worker raw stats."""

    batches = tuple(batch for worker in worker_stats for batch in worker.batches)
    expected_monitored_items = sum(worker.expected_monitored_items for worker in worker_stats)
    monitored_created = sum(worker.monitored_created for worker in worker_stats)
    monitored_failed = sum(worker.monitored_failed for worker in worker_stats)
    notification_count = sum(worker.notification_count for worker in worker_stats)
    value_count = sum(worker.value_count for worker in worker_stats)
    bad_count = sum(worker.bad_count for worker in worker_stats)
    missing_ts_count = sum(worker.missing_ts_count for worker in worker_stats)
    reserved_sequence_gap_count = sum(worker.reserved_sequence_gap_count for worker in worker_stats)
    reserved_queue_overflow_count = sum(worker.reserved_queue_overflow_count for worker in worker_stats)
    keepalive_count = sum(worker.keepalive_count for worker in worker_stats)
    keepalive_miss_count = sum(worker.keepalive_miss_count for worker in worker_stats)
    publish_timeout_count = sum(worker.publish_timeout_count for worker in worker_stats)
    reconnect_count = sum(worker.reconnect_count for worker in worker_stats)
    resubscribe_count = sum(worker.resubscribe_count for worker in worker_stats)
    resubscribe_success_count = sum(worker.resubscribe_success_count for worker in worker_stats)
    resubscribe_failure_count = sum(worker.resubscribe_failure_count for worker in worker_stats)
    unrecovered_endpoint_count = sum(worker.unrecovered_endpoint_count for worker in worker_stats)
    recovery_duration_ms = max((worker.recovery_duration_ms for worker in worker_stats), default=0.0)
    last_reconnect_reason = next(
        (worker.last_reconnect_reason for worker in reversed(tuple(worker_stats)) if worker.last_reconnect_reason),
        "",
    )
    runner_protocol_noise_count = sum(worker.runner_protocol_noise_count for worker in worker_stats)
    runner_protocol_noise_samples = tuple(
        sample
        for worker in worker_stats
        for sample in worker.runner_protocol_noise_samples
    )
    summaries = tuple(worker.summary for worker in worker_stats if worker.summary is not None)

    duration_s = max(config.duration_s, 0.001)
    point_total = expected_monitored_items
    points_per_server = int(point_total / server_count) if server_count > 0 else 0
    sample_hz = config.nominal_sample_hz if config.nominal_sample_hz is not None else (1000.0 / config.sampling_interval_ms)
    effective_data_hz = config.source_update_hz if config.source_update_enabled else sample_hz
    response_period_observable = (not config.source_update_enabled) or (config.source_update_hz >= sample_hz)
    response_period_kind = "data_notify_proxy" if response_period_observable else "unobservable"
    expected_notification_count = int(round(server_count * effective_data_hz * duration_s))
    expected_value_count = int(round(point_total * effective_data_hz * duration_s))
    value_delivery_ratio = (value_count / expected_value_count) if expected_value_count > 0 else 0.0
    value_missing_count = max(0, expected_value_count - value_count)
    data_age_values = [batch.data_age_ms for batch in batches if batch.data_age_ms is not None]
    publish_gap_values = _publish_gaps_ms(batches)
    data_batches = _data_notify_batches(batches)
    data_period_values, notify_timestamp_fallback_used = _data_periods_ms(data_batches)
    top_data_period_gap_traces, top_period_gap_uses_received = _notify_period_gap_traces(
        data_batches,
        top_n=config.runner_trace_top_n,
    )
    response_period_values = _periods_from_int_ns(data_batches, lambda batch: batch.received_ns) if response_period_observable else []
    top_period_gap_traces = top_data_period_gap_traces if response_period_observable else ()
    source_period_values = _source_periods_ms(batches)
    recv_period_values = _periods_from_int_ns(batches, lambda batch: batch.received_ns)
    callback_to_flush_lag_values, callback_to_flush_lag_warnings = _callback_to_flush_lag_samples(batches)
    endpoint_diagnostics = tuple(trace for worker in worker_stats for trace in worker.endpoint_diagnostics)
    _recv_period_mean_ms, recv_period_p95_ms, _recv_period_p99_ms, recv_period_max_ms = _stat_bundle(recv_period_values)
    (
        _callback_to_flush_lag_mean_ms,
        callback_to_flush_lag_p95_ms,
        _callback_to_flush_lag_p99_ms,
        callback_to_flush_lag_max_ms,
    ) = _stat_bundle(callback_to_flush_lag_values)
    data_age_mean_ms, data_age_p95_ms, data_age_p99_ms, data_age_max_ms = _stat_bundle(data_age_values)
    (
        publish_gap_mean_ms,
        publish_gap_p95_ms,
        publish_gap_p99_ms,
        publish_gap_max_ms,
    ) = _stat_bundle(publish_gap_values)
    (
        response_period_mean_ms,
        response_period_p95_ms,
        _response_period_p99_ms,
        response_period_max_ms,
    ) = _stat_bundle(response_period_values)
    (
        data_period_mean_ms,
        data_period_p95_ms,
        _data_period_p99_ms,
        data_period_max_ms,
    ) = _stat_bundle(data_period_values)
    (
        _source_period_mean_ms,
        source_period_p95_ms,
        _source_period_p99_ms,
        source_period_max_ms,
    ) = _stat_bundle(source_period_values)
    sample_period_ms = 1000.0 / sample_hz
    expected_data_period_ms = 1000.0 / effective_data_hz
    allowed_response_period_max_ms = sample_period_ms * (1.0 + config.data_period_max_tolerance_ratio)
    allowed_data_period_max_ms = expected_data_period_ms * (1.0 + config.data_period_max_tolerance_ratio)
    dispatch_gap_max_ms = max((trace.max_dispatch_gap_ms for trace in endpoint_diagnostics), default=0.0)
    run_iterate_duration_max_ms = max(
        (trace.max_run_iterate_duration_ms for trace in endpoint_diagnostics),
        default=0.0,
    )

    warnings: list[str] = []
    if not config.source_update_enabled:
        warnings.append("source_update_disabled")
    if keepalive_count > 0 and notification_count == 0:
        warnings.append("server_keepalive_only")
    if keepalive_count > 0:
        warnings.append("keepalive_seen")
    if keepalive_miss_count > 0:
        warnings.append("keepalive_miss_seen")
    if publish_timeout_count > 0:
        warnings.append("publish_timeout_seen")
    if reconnect_count > 0:
        warnings.append("reconnect_seen")
    if resubscribe_count > 0:
        warnings.append("resubscribe_seen")
    if config.publish_gap_p95_limit_ms is not None and publish_gap_p95_ms > config.publish_gap_p95_limit_ms:
        warnings.append("high_publish_gap_p95")
    if config.publish_gap_p99_limit_ms is not None and publish_gap_p99_ms > config.publish_gap_p99_limit_ms:
        warnings.append("high_publish_gap_p99")
    if config.data_age_p95_limit_ms is not None and data_age_p95_ms > config.data_age_p95_limit_ms:
        warnings.append("high_data_age_p95")
    if config.data_age_p99_limit_ms is not None and data_age_p99_ms > config.data_age_p99_limit_ms:
        warnings.append("high_data_age_p99")
    if bad_count > 0 and bad_count < value_count:
        warnings.append("partial_bad_status")
    if runner_protocol_noise_count > 0:
        warnings.append("runner_protocol_noise")
    if notify_timestamp_fallback_used:
        warnings.append("notify_timestamp_missing_fallback_received_ns")
    if top_period_gap_uses_received:
        warnings.append("notify_period_gap_traces_use_received_ns")
    warnings.extend(callback_to_flush_lag_warnings)
    if not response_period_observable:
        warnings.append("subscription_response_period_unobservable")
    if notification_count > 0 and response_period_observable and not response_period_values:
        warnings.append("insufficient_response_period_samples")
    if notification_count > 0 and not data_period_values:
        warnings.append("insufficient_notify_period_samples")
    if endpoint_diagnostics and dispatch_gap_max_ms > (sample_period_ms / 2.0):
        warnings.append("endpoint_dispatch_gap_over_half_period")
    if response_period_values and response_period_max_ms > allowed_response_period_max_ms:
        warnings.append("high_response_period_max")
    if resubscribe_count > 0 and resubscribe_success_count == resubscribe_count and unrecovered_endpoint_count == 0:
        warnings.append("recovered_after_resubscribe")

    reasons: list[str] = []
    if monitored_created != expected_monitored_items:
        reasons.append(f"created_items={monitored_created}<{expected_monitored_items}")
    if monitored_failed > 0:
        reasons.append("monitored_item_failed")
    if notification_count <= 0:
        reasons.append("no_notification")
    if value_count <= 0:
        reasons.append("no_data")
    if bad_count > 0:
        reasons.append("bad_status_code")
    if missing_ts_count > 0:
        reasons.append("missing_source_timestamp")
    if runner_protocol_noise_count > 0:
        reasons.append("runner_protocol_noise")
    if unrecovered_endpoint_count > 0:
        reasons.append("unrecovered_endpoint")
    if resubscribe_failure_count > 0:
        reasons.append("resubscribe_failed")
    if data_period_values and data_period_max_ms > allowed_data_period_max_ms:
        reasons.append(f"data_period_max_ms={data_period_max_ms:.2f}>{allowed_data_period_max_ms:.2f}")

    top_data_age_traces = tuple(
        sorted(
            (trace for worker in worker_stats for trace in worker.top_data_age_traces),
            key=lambda item: item.data_age_ms,
            reverse=True,
        )[: config.runner_trace_top_n]
    )
    if not config.runner_trace_enabled:
        top_data_age_traces = ()

    return SubscribeLevelMetrics(
        server_count=server_count,
        process_count=config.process_count,
        publishing_interval_ms=config.publishing_interval_ms,
        sampling_interval_ms=config.sampling_interval_ms,
        effective_source_update_hz=config.source_update_hz,
        queue_size=config.queue_size,
        expected_monitored_items=expected_monitored_items,
        monitored_created=monitored_created,
        monitored_failed=monitored_failed,
        notification_count=notification_count,
        value_count=value_count,
        bad_count=bad_count,
        missing_ts_count=missing_ts_count,
        reserved_sequence_gap_count=reserved_sequence_gap_count,
        reserved_queue_overflow_count=reserved_queue_overflow_count,
        keepalive_count=keepalive_count,
        publish_timeout_count=publish_timeout_count,
        reconnect_count=reconnect_count,
        keepalive_miss_count=keepalive_miss_count,
        resubscribe_count=resubscribe_count,
        resubscribe_success_count=resubscribe_success_count,
        resubscribe_failure_count=resubscribe_failure_count,
        unrecovered_endpoint_count=unrecovered_endpoint_count,
        recovery_duration_ms=round(recovery_duration_ms, 3),
        last_reconnect_reason=last_reconnect_reason,
        notification_rate=notification_count / duration_s,
        value_rate=value_count / duration_s,
        publish_gap_mean_ms=round(publish_gap_mean_ms, 3),
        publish_gap_p95_ms=round(publish_gap_p95_ms, 3),
        publish_gap_p99_ms=round(publish_gap_p99_ms, 3),
        publish_gap_max_ms=round(publish_gap_max_ms, 3),
        data_age_mean_ms=round(data_age_mean_ms, 3),
        data_age_p95_ms=round(data_age_p95_ms, 3),
        data_age_p99_ms=round(data_age_p99_ms, 3),
        data_age_max_ms=round(data_age_max_ms, 3),
        response_period_samples=len(response_period_values),
        response_period_mean_ms=round(response_period_mean_ms, 3),
        response_period_p95_ms=round(response_period_p95_ms, 3),
        response_period_max_ms=round(response_period_max_ms, 3),
        allowed_response_period_max_ms=round(allowed_response_period_max_ms, 3),
        data_period_samples=len(data_period_values),
        data_period_mean_ms=round(data_period_mean_ms, 3),
        data_period_p95_ms=round(data_period_p95_ms, 3),
        data_period_max_ms=round(data_period_max_ms, 3),
        allowed_data_period_max_ms=round(allowed_data_period_max_ms, 3),
        response_period_observable=response_period_observable,
        response_period_kind=response_period_kind,
        passed=not reasons,
        failure_reason="; ".join(dict.fromkeys(reasons)),
        points_per_server=points_per_server,
        point_total=point_total,
        expected_notification_count=expected_notification_count,
        expected_value_count=expected_value_count,
        value_delivery_ratio=round(value_delivery_ratio, 6),
        value_missing_count=value_missing_count,
        source_period_p95_ms=round(source_period_p95_ms, 3),
        source_period_max_ms=round(source_period_max_ms, 3),
        recv_period_p95_ms=round(recv_period_p95_ms, 3),
        recv_period_max_ms=round(recv_period_max_ms, 3),
        callback_to_flush_lag_p95_ms=round(callback_to_flush_lag_p95_ms, 3),
        callback_to_flush_lag_max_ms=round(callback_to_flush_lag_max_ms, 3),
        dispatch_gap_max_ms=round(dispatch_gap_max_ms, 3),
        run_iterate_duration_max_ms=round(run_iterate_duration_max_ms, 3),
        warnings=tuple(dict.fromkeys(warnings)),
        batches=batches,
        summaries=summaries,
        top_data_age_traces=top_data_age_traces,
        top_period_gap_traces=top_period_gap_traces if config.runner_trace_enabled else (),
        top_data_period_gap_traces=top_data_period_gap_traces if config.runner_trace_enabled else (),
        top_flush_lag_traces=_top_flush_lag_traces(batches, top_n=config.runner_trace_top_n)
        if config.runner_trace_enabled
        else (),
        top_dispatch_gap_traces=_top_dispatch_gap_traces(worker_stats, top_n=config.runner_trace_top_n)
        if config.runner_trace_enabled
        else (),
        runner_protocol_noise_count=runner_protocol_noise_count,
        runner_protocol_noise_samples=runner_protocol_noise_samples[: config.runner_trace_top_n],
    )
