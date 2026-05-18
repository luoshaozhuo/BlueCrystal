"""Metrics helpers for capacity scan evaluation."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from tools.source_lab.access.model import (
    CapacityLevelMetrics,
    CapacityScanConfig,
    CapacityStatus,
    ConfirmedLevelResult,
    PeriodGap,
    ResponsePeriodStats,
    TickResult,
)


@dataclass(slots=True)
class ReaderStats:
    """Accumulated reader stats for one worker run."""

    total_reads: int = 0
    ok_reads: int = 0
    read_errors: int = 0
    batch_mismatches: int = 0
    missing_response_timestamps: int = 0
    response_timestamps: list[float] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class RunnerTrace:
    """One runner trace row retained for diagnostics."""

    worker_index: int
    local_index: int
    global_index: int
    tick_index: int
    lag_ms: float
    read_ms: float


@dataclass(frozen=True, slots=True)
class RunnerSummary:
    """One parsed runner summary retained for diagnostics."""

    worker_index: int
    endpoint_count: int
    total_reads: int
    ok_reads: int
    bad_reads: int
    read_errors: int
    missing_response_timestamps: int
    missed_ticks: int
    max_lag_ms: float
    max_read_ms: float
    warmup_reads: int
    warmup_errors: int
    warmup_max_lag_ms: float
    warmup_max_read_ms: float


@dataclass(frozen=True, slots=True)
class WorkerRawStats:
    """Raw metrics from one worker process."""

    worker_index: int
    reader_count: int
    batch_mismatches: int
    read_errors: int
    missing_response_timestamps: int
    response_timestamps_by_reader: tuple[tuple[float, ...], ...]
    max_observed_concurrent_reads: int
    runner_summary: RunnerSummary | None = None
    top_lag_traces: tuple[RunnerTrace, ...] = ()
    top_read_traces: tuple[RunnerTrace, ...] = ()


def record_tick(stats: ReaderStats, result: TickResult) -> None:
    """Record one tick result into aggregated reader stats."""

    stats.total_reads += 1
    if result.error == "batch_mismatch":
        stats.batch_mismatches += 1
        return
    if result.error == "missing_response_timestamp":
        stats.missing_response_timestamps += 1
        return
    if not result.ok:
        stats.read_errors += 1
        return
    stats.ok_reads += 1
    if result.response_timestamp_s is not None:
        stats.response_timestamps.append(result.response_timestamp_s)


def evaluate_response_periods(
    response_timestamps_by_reader: Sequence[Sequence[float]],
    *,
    target_period_ms: float,
    top_n: int,
) -> ResponsePeriodStats:
    """Evaluate response period stats and largest gaps."""

    gaps: list[PeriodGap] = []
    for reader_index, timestamps in enumerate(response_timestamps_by_reader):
        ordered = sorted(timestamps)
        for gap_index, (previous, current) in enumerate(zip(ordered, ordered[1:])):
            delta_ms = (current - previous) * 1000.0
            if delta_ms >= 0:
                gaps.append(
                    PeriodGap(
                        reader_index=reader_index,
                        gap_index=gap_index,
                        previous_timestamp_s=previous,
                        current_timestamp_s=current,
                        period_ms=delta_ms,
                    )
                )

    if not gaps:
        return ResponsePeriodStats(
            samples=0,
            mean_ms=0.0,
            max_ms=0.0,
            mean_abs_error_ms=0.0,
            worst_gap=None,
            top_gaps=(),
        )

    values = [item.period_ms for item in gaps]
    mean_ms = sum(values) / len(values)
    top_gaps = tuple(sorted(gaps, key=lambda item: item.period_ms, reverse=True)[:top_n])
    return ResponsePeriodStats(
        samples=len(values),
        mean_ms=mean_ms,
        max_ms=max(values),
        mean_abs_error_ms=abs(mean_ms - target_period_ms),
        worst_gap=top_gaps[0] if top_gaps else None,
        top_gaps=top_gaps,
    )


def build_level_metrics(
    worker_stats: Sequence[WorkerRawStats],
    *,
    server_count: int,
    target_hz: float,
    config: CapacityScanConfig,
) -> CapacityLevelMetrics:
    """Build one level metrics object from worker raw stats."""

    read_errors = sum(item.read_errors for item in worker_stats)
    batch_mismatches = sum(item.batch_mismatches for item in worker_stats)
    missing_response_timestamps = sum(item.missing_response_timestamps for item in worker_stats)
    response_timestamps_by_reader = tuple(
        timestamps for worker in worker_stats for timestamps in worker.response_timestamps_by_reader
    )
    summaries = [item.runner_summary for item in worker_stats if item.runner_summary is not None]
    worker_conc_by_worker = tuple(item.max_observed_concurrent_reads for item in worker_stats)
    worker_conc_sum = sum(worker_conc_by_worker)
    worker_conc_max = max(worker_conc_by_worker, default=0)
    missed_ticks = sum(item.missed_ticks for item in summaries)
    runner_max_lag_ms = max((item.max_lag_ms for item in summaries), default=0.0)
    runner_max_read_ms = max((item.max_read_ms for item in summaries), default=0.0)

    target_period_ms = 1000.0 / target_hz
    period_stats = evaluate_response_periods(
        response_timestamps_by_reader,
        target_period_ms=target_period_ms,
        top_n=config.top_gap_count,
    )
    allowed_period_max_ms = target_period_ms * (1.0 + config.period_max_tolerance_ratio)
    allowed_period_mean_abs_error_ms = target_period_ms * config.period_mean_error_ratio

    value_count_ok = batch_mismatches == 0
    period_max_ok = period_stats.samples > 0 and period_stats.max_ms <= allowed_period_max_ms
    period_mean_ok = (
        period_stats.samples > 0 and period_stats.mean_abs_error_ms <= allowed_period_mean_abs_error_ms
    )

    reasons: list[str] = []
    if not value_count_ok:
        reasons.append(f"bad={batch_mismatches}")
    if period_stats.samples <= 0:
        reasons.append("p_n=0")
    else:
        if not period_max_ok:
            reasons.append(f"pmax={period_stats.max_ms:.2f}>{allowed_period_max_ms:.2f}")
        if not period_mean_ok:
            reasons.append(
                f"mean_err={period_stats.mean_abs_error_ms:.2f}>{allowed_period_mean_abs_error_ms:.2f}"
            )

    return CapacityLevelMetrics(
        server_count=server_count,
        target_hz=target_hz,
        target_period_ms=round(target_period_ms, 1),
        allowed_period_max_ms=round(allowed_period_max_ms, 1),
        allowed_period_mean_abs_error_ms=round(allowed_period_mean_abs_error_ms, 2),
        read_errors=read_errors,
        batch_mismatches=batch_mismatches,
        missing_response_timestamps=missing_response_timestamps,
        period_samples=period_stats.samples,
        period_mean_ms=round(period_stats.mean_ms, 2),
        period_max_ms=round(period_stats.max_ms, 2),
        period_mean_abs_error_ms=round(period_stats.mean_abs_error_ms, 2),
        missed_ticks=missed_ticks,
        runner_max_lag_ms=round(runner_max_lag_ms, 3),
        runner_max_read_ms=round(runner_max_read_ms, 3),
        worker_conc_sum=worker_conc_sum,
        worker_conc_max=worker_conc_max,
        worker_conc_by_worker=worker_conc_by_worker,
        value_count_ok=value_count_ok,
        period_max_ok=period_max_ok,
        period_mean_ok=period_mean_ok,
        passed=value_count_ok and period_max_ok and period_mean_ok,
        failure_reason="; ".join(reasons),
        worst_gap=period_stats.worst_gap,
        top_gaps=period_stats.top_gaps,
    )


def build_skip_result(
    *,
    server_count: int,
    target_hz: float,
    reason: str,
    config: CapacityScanConfig,
) -> ConfirmedLevelResult:
    """Build a SKIP result preserving current metrics semantics."""

    target_period_ms = 1000.0 / target_hz
    metrics = CapacityLevelMetrics(
        server_count=server_count,
        target_hz=target_hz,
        target_period_ms=round(target_period_ms, 1),
        allowed_period_max_ms=round(target_period_ms * (1.0 + config.period_max_tolerance_ratio), 1),
        allowed_period_mean_abs_error_ms=round(target_period_ms * config.period_mean_error_ratio, 2),
        read_errors=0,
        batch_mismatches=0,
        missing_response_timestamps=0,
        period_samples=0,
        period_mean_ms=0.0,
        period_max_ms=0.0,
        period_mean_abs_error_ms=0.0,
        missed_ticks=0,
        runner_max_lag_ms=0.0,
        runner_max_read_ms=0.0,
        worker_conc_sum=0,
        worker_conc_max=0,
        worker_conc_by_worker=(),
        value_count_ok=True,
        period_max_ok=False,
        period_mean_ok=False,
        passed=False,
        failure_reason=reason,
        worst_gap=None,
        top_gaps=(),
    )
    return ConfirmedLevelResult(
        primary=metrics,
        attempts=(metrics,),
        final_status=CapacityStatus.SKIP,
        final_reason=reason,
    )
