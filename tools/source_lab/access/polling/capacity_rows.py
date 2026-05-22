"""Polling-specific field-capacity row builders."""

from __future__ import annotations

from typing import Protocol

from tools.source_lab.access.field_capacity import FieldCapacityRow
from tools.source_lab.access.polling.model import CapacityScanResult, CapacityStatus


class CpuSnapshot(Protocol):
    @property
    def cpu_mean_pct(self) -> float: ...

    @property
    def cpu_max_pct(self) -> float: ...

    @property
    def rss_mb(self) -> float: ...

    @property
    def warning(self) -> str: ...


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


def _summary_reason(reason: str) -> str:
    if reason.startswith("data_period_max_ms="):
        return f"max={reason.split('=', 1)[1]}"
    if reason.startswith("data_period_max="):
        return f"max={reason.split('=', 1)[1]}"
    if reason.startswith("max="):
        return reason
    return reason


def polling_row(
    result: CapacityScanResult,
    *,
    process_count: int,
    point_count: int,
    cpu: CpuSnapshot,
    source_update_enabled: bool,
) -> FieldCapacityRow:
    """Build one field-capacity polling row from an executed level."""

    level = result.levels[0]
    metrics = level.final_metrics
    reason = level.final_reason or metrics.failure_reason
    if level.final_status is CapacityStatus.PASS:
        reason = ""
    else:
        reason = _summary_reason(reason)
    return FieldCapacityRow(
        access_mode="polling",
        mode="polling",
        process_count=process_count,
        server_count=metrics.server_count,
        protocol=result.config.protocol,
        hz=metrics.target_hz,
        period_ms=metrics.target_period_ms,
        points_per_server=metrics.points_per_server,
        point_total=metrics.point_total,
        expected_values=metrics.expected_value_count,
        values=metrics.value_count,
        value_ratio=round(metrics.value_delivery_ratio, 6),
        value_miss=metrics.value_missing_count,
        bad=metrics.batch_mismatches,
        miss_ts=metrics.missing_response_timestamps,
        noise=metrics.runner_protocol_noise_count,
        reads=metrics.read_count,
        batches=metrics.batch_count,
        data_period_p95_ms=metrics.period_p95_ms,
        data_period_max_ms=metrics.period_max_ms,
        point_count=point_count,
        cpu_mean_pct=round(cpu.cpu_mean_pct, 3),
        cpu_max_pct=round(cpu.cpu_max_pct, 3),
        rss_mb=round(cpu.rss_mb, 3),
        status=level.final_status.value,
        reason=reason,
        warnings=_merge_warnings(
            metrics.warnings,
            cpu_warning=cpu.warning,
            source_update_enabled=source_update_enabled,
        ),
        runner_protocol_noise_count=metrics.runner_protocol_noise_count,
    )


def build_polling_capacity_rows(
    result: CapacityScanResult | tuple[CapacityScanResult, ...],
) -> tuple[FieldCapacityRow, ...]:
    """Build normalized capacity rows from polling scan results."""

    scan_results = result if isinstance(result, tuple) else (result,)
    rows: list[FieldCapacityRow] = []
    for scan_result in scan_results:
        for level in scan_result.levels:
            metrics = level.final_metrics
            reason = level.final_reason or metrics.failure_reason
            if level.final_status is CapacityStatus.PASS:
                reason = ""
            else:
                reason = _summary_reason(reason)
            rows.append(
                FieldCapacityRow(
                    access_mode="polling",
                    mode="polling",
                    process_count=scan_result.config.process_count,
                    server_count=metrics.server_count,
                    protocol=scan_result.config.protocol,
                    hz=metrics.target_hz,
                    period_ms=metrics.target_period_ms,
                    points_per_server=metrics.points_per_server,
                    point_total=metrics.point_total,
                    expected_values=metrics.expected_value_count,
                    values=metrics.value_count,
                    value_ratio=round(metrics.value_delivery_ratio, 6),
                    value_miss=metrics.value_missing_count,
                    bad=metrics.batch_mismatches,
                    miss_ts=metrics.missing_response_timestamps,
                    noise=metrics.runner_protocol_noise_count,
                    reads=metrics.read_count,
                    batches=metrics.batch_count,
                    data_period_p95_ms=metrics.period_p95_ms,
                    data_period_max_ms=metrics.period_max_ms,
                    point_count=metrics.point_total,
                    status=level.final_status.value,
                    reason=reason,
                    warnings=",".join(metrics.warnings),
                    runner_protocol_noise_count=metrics.runner_protocol_noise_count,
                )
            )
    return tuple(rows)


__all__ = ["build_polling_capacity_rows", "polling_row"]
