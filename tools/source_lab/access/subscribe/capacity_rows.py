"""Subscribe-specific capacity row builders and status helpers."""

from __future__ import annotations

from typing import Protocol

from tools.source_lab.access.field_capacity import FieldCapacityRow
from tools.source_lab.access.polling.model import CapacityStatus
from tools.source_lab.access.subscribe.capacity_model import SubscribeCapacityComboResult, SubscribeCapacityResult
from tools.source_lab.access.subscribe.model import SubscribeLevelResult


class CpuSnapshot(Protocol):
    @property
    def cpu_mean_pct(self) -> float: ...

    @property
    def cpu_max_pct(self) -> float: ...

    @property
    def rss_mb(self) -> float: ...

    @property
    def warning(self) -> str: ...


def sample_hz_to_interval_ms(sample_hz: float) -> float:
    """Convert sample frequency to interval milliseconds."""

    return 1000.0 / sample_hz


def status_for_subscribe_level(level: SubscribeLevelResult) -> tuple[CapacityStatus, str]:
    """Return normalized subscribe status and reason for one executed level."""

    metrics = level.final_metrics
    if metrics.runner_protocol_noise_count > 0 or metrics.runner_protocol_noise_samples:
        return CapacityStatus.FAIL, "runner_protocol_noise"
    if metrics.unrecovered_endpoint_count > 0:
        return CapacityStatus.FAIL, level.final_reason or metrics.failure_reason or "unrecovered_endpoint"
    if metrics.resubscribe_failure_count > 0:
        return CapacityStatus.FAIL, level.final_reason or metrics.failure_reason or "resubscribe_failed"
    if not metrics.passed:
        return CapacityStatus.FAIL, level.final_reason or metrics.failure_reason
    return CapacityStatus.PASS, ""


def _summary_reason(reason: str) -> str:
    if reason.startswith("data_period_max_ms="):
        return f"max={reason.split('=', 1)[1]}"
    if reason.startswith("max="):
        return reason
    return reason


def _merge_warnings(
    base: tuple[str, ...],
    *,
    cpu_warning: str,
    source_update_enabled: bool,
) -> str:
    warnings = list(base)
    if not source_update_enabled:
        warnings.append("source_update_disabled")
    if cpu_warning:
        warnings.append(cpu_warning)
    return ",".join(dict.fromkeys(warnings))


def subscribe_row(
    combo: SubscribeCapacityComboResult,
    *,
    protocol: str,
    point_count_per_server: int,
    cpu: CpuSnapshot,
    source_update_enabled: bool,
) -> FieldCapacityRow:
    """Build one field-capacity subscribe row from one matrix combination."""

    metrics = combo.result.final_metrics if combo.result is not None else None
    sub_ms = round(sample_hz_to_interval_ms(combo.sample_hz), 3)
    src_ms = round(1000.0 / combo.effective_source_update_hz, 3)
    if metrics is None:
        return FieldCapacityRow(
            access_mode="subscribe",
            mode="subscribe",
            process_count=combo.process_count,
            server_count=combo.server_count,
            protocol=protocol,
            hz=combo.sample_hz,
            sample_hz=combo.sample_hz,
            period_ms=sub_ms,
            effective_source_update_hz=combo.effective_source_update_hz,
            point_count=point_count_per_server * combo.server_count,
            cpu_mean_pct=round(cpu.cpu_mean_pct, 3),
            cpu_max_pct=round(cpu.cpu_max_pct, 3),
            rss_mb=round(cpu.rss_mb, 3),
            status=combo.status.value,
            reason=_summary_reason(combo.reason),
            warnings=_merge_warnings((), cpu_warning=cpu.warning, source_update_enabled=source_update_enabled),
            sub_hz=combo.sample_hz,
            src_hz=combo.effective_source_update_hz,
            sub_ms=sub_ms,
            src_ms=src_ms,
        )

    reason = "" if combo.status is CapacityStatus.PASS else _summary_reason(combo.reason)
    return FieldCapacityRow(
        access_mode="subscribe",
        mode="subscribe",
        process_count=combo.process_count,
        server_count=combo.server_count,
        protocol=protocol,
        hz=combo.sample_hz,
        sample_hz=combo.sample_hz,
        period_ms=sub_ms,
        points_per_server=metrics.points_per_server,
        point_total=metrics.point_total,
        expected_values=metrics.expected_value_count,
        values=metrics.value_count,
        value_ratio=round(metrics.value_delivery_ratio, 6),
        value_miss=metrics.value_missing_count,
        bad=metrics.bad_count,
        miss_ts=metrics.missing_ts_count,
        noise=metrics.runner_protocol_noise_count,
        notify=metrics.notification_count,
        expected_notifications=metrics.expected_notification_count,
        expected_items=metrics.expected_monitored_items,
        created_items=metrics.monitored_created,
        batches=metrics.notification_count,
        publishing_interval_ms=metrics.publishing_interval_ms,
        sampling_interval_ms=metrics.sampling_interval_ms,
        effective_source_update_hz=metrics.effective_source_update_hz,
        queue_size=metrics.queue_size,
        publish_gap_p95_ms=metrics.publish_gap_p95_ms,
        publish_gap_max_ms=metrics.publish_gap_max_ms,
        data_age_p95_ms=metrics.data_age_p95_ms,
        data_age_max_ms=metrics.data_age_max_ms,
        response_period_p95_ms=metrics.response_period_p95_ms,
        response_period_max_ms=metrics.response_period_max_ms,
        data_period_p95_ms=metrics.data_period_p95_ms,
        data_period_max_ms=metrics.data_period_max_ms,
        source_period_p95_ms=metrics.source_period_p95_ms,
        source_period_max_ms=metrics.source_period_max_ms,
        point_count=point_count_per_server * combo.server_count,
        cpu_mean_pct=round(cpu.cpu_mean_pct, 3),
        cpu_max_pct=round(cpu.cpu_max_pct, 3),
        rss_mb=round(cpu.rss_mb, 3),
        status=combo.status.value,
        reason=reason,
        warnings=_merge_warnings(
            metrics.warnings,
            cpu_warning=cpu.warning,
            source_update_enabled=source_update_enabled,
        ),
        runner_protocol_noise_count=metrics.runner_protocol_noise_count,
        sub_hz=combo.sample_hz,
        src_hz=metrics.effective_source_update_hz,
        sub_ms=sub_ms,
        src_ms=src_ms,
    )


def build_subscribe_capacity_rows(
    result: SubscribeCapacityResult,
    *,
    protocol: str,
) -> tuple[FieldCapacityRow, ...]:
    """Build normalized capacity rows from subscribe capacity results."""

    rows: list[FieldCapacityRow] = []
    for combo in result.combos:
        metrics = combo.result.final_metrics if combo.result is not None else None
        if metrics is None:
            sub_ms = sample_hz_to_interval_ms(combo.sample_hz)
            src_ms = 1000.0 / combo.effective_source_update_hz
            rows.append(
                FieldCapacityRow(
                    access_mode="subscribe",
                    mode="subscribe",
                    process_count=combo.process_count,
                    server_count=combo.server_count,
                    protocol=protocol,
                    hz=combo.sample_hz,
                    sample_hz=combo.sample_hz,
                    period_ms=round(sub_ms, 3),
                    effective_source_update_hz=combo.effective_source_update_hz,
                    status=combo.status.value,
                    reason=_summary_reason(combo.reason),
                    sub_hz=combo.sample_hz,
                    src_hz=combo.effective_source_update_hz,
                    sub_ms=round(sub_ms, 3),
                    src_ms=round(src_ms, 3),
                )
            )
            continue

        reason = "" if combo.status is CapacityStatus.PASS else _summary_reason(combo.reason)
        rows.append(
            FieldCapacityRow(
                access_mode="subscribe",
                mode="subscribe",
                process_count=combo.process_count,
                server_count=combo.server_count,
                protocol=protocol,
                hz=combo.sample_hz,
                sample_hz=combo.sample_hz,
                period_ms=round(sample_hz_to_interval_ms(combo.sample_hz), 3),
                points_per_server=metrics.points_per_server,
                point_total=metrics.point_total,
                expected_values=metrics.expected_value_count,
                values=metrics.value_count,
                value_ratio=round(metrics.value_delivery_ratio, 6),
                value_miss=metrics.value_missing_count,
                bad=metrics.bad_count,
                miss_ts=metrics.missing_ts_count,
                noise=metrics.runner_protocol_noise_count,
                notify=metrics.notification_count,
                expected_notifications=metrics.expected_notification_count,
                expected_items=metrics.expected_monitored_items,
                created_items=metrics.monitored_created,
                batches=metrics.notification_count,
                publishing_interval_ms=metrics.publishing_interval_ms,
                sampling_interval_ms=metrics.sampling_interval_ms,
                effective_source_update_hz=metrics.effective_source_update_hz,
                queue_size=metrics.queue_size,
                publish_gap_p95_ms=metrics.publish_gap_p95_ms,
                publish_gap_max_ms=metrics.publish_gap_max_ms,
                data_age_p95_ms=metrics.data_age_p95_ms,
                data_age_max_ms=metrics.data_age_max_ms,
                response_period_p95_ms=metrics.response_period_p95_ms,
                response_period_max_ms=metrics.response_period_max_ms,
                data_period_p95_ms=metrics.data_period_p95_ms,
                data_period_max_ms=metrics.data_period_max_ms,
                source_period_p95_ms=metrics.source_period_p95_ms,
                source_period_max_ms=metrics.source_period_max_ms,
                point_count=metrics.point_total,
                status=combo.status.value,
                reason=reason,
                warnings=",".join(metrics.warnings),
                runner_protocol_noise_count=metrics.runner_protocol_noise_count,
                sub_hz=combo.sample_hz,
                src_hz=metrics.effective_source_update_hz,
                sub_ms=round(sample_hz_to_interval_ms(combo.sample_hz), 3),
                src_ms=round(1000.0 / metrics.effective_source_update_hz, 3),
            )
        )
    return tuple(rows)
