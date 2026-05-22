"""Legacy polling progress/detail helpers for profile and debug paths.

Capacity matrix output does not use this module for user-facing progress.
Capacity uses ``CapacityProgressBar`` for runtime progress and
``print_capacity_table()`` for the final summary table.
"""

from __future__ import annotations

import sys
import time
from dataclasses import dataclass
from typing import Iterable, Sequence

from .metrics import WorkerRawStats
from .model import CapacityLevelMetrics, CapacityScanConfig, CapacityScanResult, CapacityStatus, ConfirmedLevelResult


def _emit_progress_line(message: str) -> None:
    """Print one standardized source-lab progress line to stderr."""

    print(f"[source-lab] {message}", file=sys.stderr, flush=True)


def print_scan_started(config: CapacityScanConfig, *, runner_name: str) -> float:
    """Print scan start progress lines and return start timestamp.

    Args:
        config: Capacity scan configuration.
        runner_name: Injected runner label for progress reporting.

    Returns:
        ``time.perf_counter()`` start timestamp.
    """

    started_at = time.perf_counter()
    if not config.progress_enabled:
        return started_at

    _emit_progress_line(
        "capacity scan started: "
        f"mode={config.mode.value} protocol={config.protocol} runner={runner_name}"
    )
    _emit_progress_line(
        "scan range: "
        f"servers={config.server_count_start}..{config.server_count_max} step={config.server_count_step}, "
        f"hz={config.hz_start:.1f}..{config.hz_max:.1f} step={config.hz_step:.1f}, "
        f"warmup={config.warmup_s:.1f}s, duration={config.level_duration_s:.1f}s, "
        f"process_count={config.process_count}, "
        f"runner_trace_enabled={config.runner_trace_enabled}"
    )
    return started_at


def print_level_started(
    config: CapacityScanConfig,
    *,
    server_count: int,
    target_hz: float,
    attempt_index: int,
    attempt_total: int,
) -> None:
    """Print one level-attempt start line."""

    if not config.progress_enabled:
        return
    _emit_progress_line(
        "level start: "
        f"srv={server_count} hz={target_hz:.1f} attempt={attempt_index}/{attempt_total} "
        f"period={1000.0 / target_hz:.1f}ms"
    )


def print_measurement_started(
    config: CapacityScanConfig,
    *,
    server_count: int,
    target_hz: float,
) -> None:
    """Print measurement start progress."""

    if not config.progress_enabled:
        return
    _emit_progress_line(
        "measurement start: "
        f"srv={server_count} hz={target_hz:.1f} "
        f"warmup={config.warmup_s:.1f}s duration={config.level_duration_s:.1f}s"
    )


def print_measurement_progress(
    config: CapacityScanConfig,
    *,
    server_count: int,
    target_hz: float,
    elapsed_s: float,
    ticks: int,
    bad: int,
    worker_index: int | None = None,
) -> None:
    """Print periodic measurement progress."""

    if not config.progress_enabled:
        return
    worker_suffix = "" if worker_index is None else f" worker={worker_index}"
    _emit_progress_line(
        "measurement progress: "
        f"srv={server_count} hz={target_hz:.1f}{worker_suffix} "
        f"elapsed={elapsed_s:.1f}/{config.level_duration_s:.1f}s ticks={ticks} bad={bad}"
    )


def print_runner_started(
    config: CapacityScanConfig,
    *,
    runner_name: str,
    worker_index: int,
    endpoint_count: int,
    target_hz: float,
) -> None:
    """Print one worker-runner start line."""

    if not config.progress_enabled:
        return
    _emit_progress_line(
        "runner start: "
        f"runner={runner_name} worker={worker_index} endpoints={endpoint_count} hz={target_hz:.1f}"
    )


def print_worker_diagnostics(
    config: CapacityScanConfig,
    worker_stats: Sequence[WorkerRawStats],
) -> None:
    """Print parent-process worker summaries and top runner traces."""

    if not config.progress_enabled or not config.runner_trace_enabled:
        return

    summaries = [item.runner_summary for item in worker_stats if item.runner_summary is not None]
    if summaries:
        _emit_progress_line("runner summaries:")
        for summary in sorted(summaries, key=lambda item: item.worker_index):
            _emit_progress_line(
                "  "
                f"worker={summary.worker_index} endpoints={summary.endpoint_count} "
                f"total={summary.total_reads} ok={summary.ok_reads} bad={summary.bad_reads} "
                f"err={summary.read_errors} missing_ts={summary.missing_response_timestamps} "
                f"missed={summary.missed_ticks} max_lag={summary.max_lag_ms:.3f}ms "
                f"max_read={summary.max_read_ms:.3f}ms warmup_reads={summary.warmup_reads} "
                f"warmup_errors={summary.warmup_errors} "
                f"warmup_max_lag={summary.warmup_max_lag_ms:.3f}ms "
                f"warmup_max_read={summary.warmup_max_read_ms:.3f}ms"
            )

    lag_traces = sorted(
        (trace for item in worker_stats for trace in item.top_lag_traces),
        key=lambda item: item.lag_ms,
        reverse=True,
    )[: config.runner_trace_top_n]
    if lag_traces:
        _emit_progress_line("top runner lag:")
        for trace in lag_traces:
            _emit_progress_line(
                "  "
                f"worker={trace.worker_index} local={trace.local_index} global={trace.global_index} "
                f"tick={trace.tick_index} lag_ms={trace.lag_ms:.3f} read_ms={trace.read_ms:.3f}"
            )

    read_traces = sorted(
        (trace for item in worker_stats for trace in item.top_read_traces),
        key=lambda item: item.read_ms,
        reverse=True,
    )[: config.runner_trace_top_n]
    if read_traces:
        _emit_progress_line("top runner read:")
        for trace in read_traces:
            _emit_progress_line(
                "  "
                f"worker={trace.worker_index} local={trace.local_index} global={trace.global_index} "
                f"tick={trace.tick_index} lag_ms={trace.lag_ms:.3f} read_ms={trace.read_ms:.3f}"
            )


def print_level_done(
    config: CapacityScanConfig,
    *,
    metrics: CapacityLevelMetrics,
    attempt_index: int,
    status: CapacityStatus,
    reason: str,
) -> None:
    """Print one level-attempt completion line."""

    if not config.progress_enabled:
        return
    _emit_progress_line(
        "level done: "
        f"srv={metrics.server_count} hz={metrics.target_hz:.1f} attempt={attempt_index} "
        f"status={status.value} p_max={metrics.period_max_ms:.2f}ms "
        f"mean_err={metrics.period_mean_abs_error_ms:.2f}ms "
        f"bad={metrics.batch_mismatches} reason={reason or '-'}"
    )


def print_stop_hz_ramp(
    config: CapacityScanConfig,
    *,
    server_count: int,
    target_hz: float,
    status: CapacityStatus,
    reason: str,
) -> None:
    """Print stop-ramp progress."""

    if not config.progress_enabled:
        return
    _emit_progress_line(
        f"stop hz ramp: srv={server_count} hz={target_hz:.1f} status={status.value} reason={reason or '-'}"
    )


def print_scan_finished(config: CapacityScanConfig, *, started_at: float) -> None:
    """Print scan finished progress."""

    if not config.progress_enabled:
        return
    elapsed_s = time.perf_counter() - started_at
    _emit_progress_line(f"capacity scan finished: elapsed={elapsed_s:.2f}s")


@dataclass(frozen=True, slots=True)
class ServerCountSummary:
    """Summary values for one server-count ramp."""

    server_count: int
    stable_pass_hz: float | None
    first_flaky_hz: float | None
    first_fail_hz: float | None
    best_accepted_hz: float | None
    best_accepted_p_max_ms: float | None
    best_accepted_mean_err_ms: float | None
    best_accepted_conc_sum: int | None
    best_accepted_failure_reason: str


def summarize_server_count_levels(
    levels: Iterable[ConfirmedLevelResult],
    *,
    accept_flaky_as_pass: bool,
) -> tuple[ServerCountSummary, ...]:
    """Build per-server-count summary for capacity levels."""

    groups: dict[int, list[ConfirmedLevelResult]] = {}
    for level in levels:
        groups.setdefault(level.final_metrics.server_count, []).append(level)

    summaries: list[ServerCountSummary] = []
    for server_count in sorted(groups):
        bucket = sorted(groups[server_count], key=lambda item: item.final_metrics.target_hz)

        stable_pass_hz = next(
            (item.final_metrics.target_hz for item in reversed(bucket) if item.final_status == CapacityStatus.PASS),
            None,
        )
        first_flaky_hz = next(
            (item.final_metrics.target_hz for item in bucket if item.final_status == CapacityStatus.FLAKY),
            None,
        )
        first_fail_hz = next(
            (item.final_metrics.target_hz for item in bucket if item.final_status == CapacityStatus.FAIL),
            None,
        )

        accepted_statuses = {CapacityStatus.PASS}
        if accept_flaky_as_pass:
            accepted_statuses.add(CapacityStatus.FLAKY)

        accepted = [item for item in bucket if item.final_status in accepted_statuses]
        best = accepted[-1].final_metrics if accepted else None

        summaries.append(
            ServerCountSummary(
                server_count=server_count,
                stable_pass_hz=stable_pass_hz,
                first_flaky_hz=first_flaky_hz,
                first_fail_hz=first_fail_hz,
                best_accepted_hz=best.target_hz if best else None,
                best_accepted_p_max_ms=best.period_max_ms if best else None,
                best_accepted_mean_err_ms=best.period_mean_abs_error_ms if best else None,
                best_accepted_conc_sum=best.worker_conc_sum if best else None,
                best_accepted_failure_reason=best.failure_reason if best else "",
            )
        )

    return tuple(summaries)


def print_capacity_report(result: CapacityScanResult) -> None:
    """Print capacity scan detail rows and summary."""

    print()
    print("=" * 132, flush=True)
    print("source_lab capacity scan", flush=True)
    print("=" * 132, flush=True)
    print(f"mode={result.config.mode.value}", flush=True)
    print(f"protocol={result.config.protocol}", flush=True)
    print(
        f"server_count={result.config.server_count_start}:{result.config.server_count_step}:"
        f"{result.config.server_count_max}",
        flush=True,
    )
    print(f"hz={result.config.hz_start}:{result.config.hz_step}:{result.config.hz_max}", flush=True)
    print(f"process_count={result.config.process_count}", flush=True)
    print(f"runner_trace_enabled={result.config.runner_trace_enabled}", flush=True)
    print("-" * 132, flush=True)
    print(
        f"{'srv':>4} {'hz':>6} {'period':>8} {'bad':>5} {'p_n':>7} {'p_mean':>8} "
        f"{'p_max':>7} {'mean_err':>9} {'conc_sum':>9} {'status':>7} reason / warnings",
        flush=True,
    )
    print("-" * 132, flush=True)

    for level in result.levels:
        metrics = level.final_metrics
        print(
            f"{metrics.server_count:>4} {metrics.target_hz:>6.1f} {metrics.target_period_ms:>8.1f} "
            f"{metrics.batch_mismatches:>5} {metrics.period_samples:>7} {metrics.period_mean_ms:>8.2f} "
            f"{metrics.period_max_ms:>7.2f} {metrics.period_mean_abs_error_ms:>9.2f} "
            f"{metrics.worker_conc_sum:>9} {level.final_status.value:>7} "
            f"{level.final_reason or metrics.failure_reason or '-'}"
            f"{'' if not metrics.warnings else ' warnings=' + ','.join(metrics.warnings)}",
            flush=True,
        )
        if level.final_status in {CapacityStatus.FAIL, CapacityStatus.FLAKY} and metrics.top_gaps:
            print("  top response period gaps:", flush=True)
            print("    reader  gap    period_ms    prev_ts             cur_ts", flush=True)
            for gap in metrics.top_gaps:
                print(
                    f"    {gap.reader_index:>6} {gap.gap_index:>4} "
                    f"{gap.period_ms:>12.2f} {gap.previous_timestamp_s:>17.3f} "
                    f"{gap.current_timestamp_s:>17.3f}",
                    flush=True,
                )

    print("-" * 132, flush=True)
    print("summary by server_count:", flush=True)
    summaries = summarize_server_count_levels(
        result.levels,
        accept_flaky_as_pass=result.config.accept_flaky_as_pass,
    )
    for item in summaries:
        print(f"  srv={item.server_count}:", flush=True)
        print(
            f"    stable_pass_hz={item.stable_pass_hz if item.stable_pass_hz is not None else 'N/A'}",
            flush=True,
        )
        print(
            f"    first_flaky_hz={item.first_flaky_hz if item.first_flaky_hz is not None else 'N/A'}",
            flush=True,
        )
        print(
            f"    first_fail_hz={item.first_fail_hz if item.first_fail_hz is not None else 'N/A'}",
            flush=True,
        )
        print(
            f"    best_accepted_hz={item.best_accepted_hz if item.best_accepted_hz is not None else 'N/A'}",
            flush=True,
        )
        print(
            f"    p_max={item.best_accepted_p_max_ms if item.best_accepted_p_max_ms is not None else 'N/A'}",
            flush=True,
        )
        print(
            f"    mean_err={item.best_accepted_mean_err_ms if item.best_accepted_mean_err_ms is not None else 'N/A'}",
            flush=True,
        )
        print(
            f"    conc_sum={item.best_accepted_conc_sum if item.best_accepted_conc_sum is not None else 'N/A'}",
            flush=True,
        )
        print(f"    failure_reason={item.best_accepted_failure_reason or '-'}", flush=True)
    print("=" * 132, flush=True)
