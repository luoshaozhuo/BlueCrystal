"""Legacy subscribe progress/detail helpers for profile and debug paths.

Capacity matrix output does not use this module for progress or table rendering.
Capacity uses ``CapacityProgressBar`` for runtime progress and
``print_capacity_table()`` for the final summary table.
"""

from __future__ import annotations

import sys
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

from tools.source_lab.access.polling.model import CapacityStatus
from tools.source_lab.access.subscribe.model import SubscribeLevelMetrics, SubscribeScanConfig, SubscribeScanResult

if TYPE_CHECKING:
    from tools.source_lab.access.capacity import SubscribeCapacityResult

_ProgressMode = Literal["inline", "quiet"]
_INLINE_PROGRESS_WIDTH = 144


@dataclass(slots=True)
class SubscribeProgressReporter:
    """Render subscribe scan progress as one inline TTY line or stay quiet."""

    config: SubscribeScanConfig
    runner_name: str
    mode: _ProgressMode
    started_at: float = 0.0
    _last_width: int = 0

    @classmethod
    def from_config(cls, config: SubscribeScanConfig, *, runner_name: str) -> "SubscribeProgressReporter":
        mode: _ProgressMode = "inline" if config.progress_enabled and sys.stderr.isatty() else "quiet"
        return cls(config=config, runner_name=runner_name, mode=mode)

    def scan_started(self) -> float:
        self.started_at = time.perf_counter()
        if self.mode == "quiet":
            return self.started_at
        self._render_inline(
            "[source-lab] subscribe capacity "
            f"proc={self.config.process_count} srv={self.config.server_count_start} "
            f"hz={self.config.sampling_interval_ms and 1000.0 / self.config.sampling_interval_ms:.1f} "
            f"queue={self.config.queue_size} running 0.0s"
        )
        return self.started_at

    def level_started(self, *, server_count: int, attempt_index: int, attempt_total: int) -> None:
        if self.mode == "quiet":
            return
        self._render_inline(
            "[source-lab] subscribe capacity "
            f"proc={self.config.process_count} srv={server_count} "
            f"hz={1000.0 / self.config.sampling_interval_ms:.1f} queue={self.config.queue_size} "
            f"running {time.perf_counter() - self.started_at:.1f}s"
        )

    def level_done(
        self,
        *,
        metrics: SubscribeLevelMetrics,
        attempt_index: int,
        status: CapacityStatus,
        reason: str,
    ) -> None:
        if self.mode == "quiet":
            return
        self._render_inline(
            "[source-lab] subscribe capacity "
            f"proc={self.config.process_count} srv={metrics.server_count} "
            f"hz={1000.0 / self.config.sampling_interval_ms:.1f} queue={self.config.queue_size} "
            f"{status.value} notify={metrics.notification_count} age_p95={metrics.data_age_p95_ms:.1f}ms "
            f"gap_p95={metrics.publish_gap_p95_ms:.1f}ms reason={reason or '-'}"
        )

    def stop_ramp(self, *, server_count: int, status: CapacityStatus, reason: str) -> None:
        if self.mode == "quiet":
            return
        self._render_inline(
            "[source-lab] subscribe capacity "
            f"proc={self.config.process_count} srv={server_count} "
            f"hz={1000.0 / self.config.sampling_interval_ms:.1f} queue={self.config.queue_size} "
            f"stop {status.value} reason={reason or '-'}"
        )

    def scan_finished(self) -> None:
        if self.mode == "quiet":
            return
        self._clear_inline()

    def _render_inline(self, message: str) -> None:
        padded = message.ljust(max(_INLINE_PROGRESS_WIDTH, len(message), self._last_width))
        sys.stderr.write("\r" + padded)
        sys.stderr.flush()
        self._last_width = len(padded)

    def _clear_inline(self) -> None:
        if self._last_width <= 0:
            return
        sys.stderr.write("\r" + (" " * self._last_width) + "\r")
        sys.stderr.flush()
        self._last_width = 0


def print_subscribe_scan_started(config: SubscribeScanConfig, *, runner_name: str) -> float:
    """Print subscription scan start progress lines and return start timestamp."""

    return SubscribeProgressReporter.from_config(config, runner_name=runner_name).scan_started()


def print_subscribe_level_started(
    config: SubscribeScanConfig,
    *,
    server_count: int,
    attempt_index: int,
    attempt_total: int,
) -> None:
    """Print one subscription level-attempt start line."""

    SubscribeProgressReporter.from_config(config, runner_name="subscription").level_started(
        server_count=server_count,
        attempt_index=attempt_index,
        attempt_total=attempt_total,
    )


def print_subscribe_level_done(
    config: SubscribeScanConfig,
    *,
    metrics: SubscribeLevelMetrics,
    attempt_index: int,
    status: CapacityStatus,
    reason: str,
) -> None:
    """Print one subscription level-attempt completion line."""

    SubscribeProgressReporter.from_config(config, runner_name="subscription").level_done(
        metrics=metrics,
        attempt_index=attempt_index,
        status=status,
        reason=reason,
    )


def print_subscribe_stop_ramp(
    config: SubscribeScanConfig,
    *,
    server_count: int,
    status: CapacityStatus,
    reason: str,
) -> None:
    """Print one subscription stop-ramp progress line."""

    SubscribeProgressReporter.from_config(config, runner_name="subscription").stop_ramp(
        server_count=server_count,
        status=status,
        reason=reason,
    )


def print_subscribe_scan_finished(config: SubscribeScanConfig, *, started_at: float) -> None:
    """Print subscription scan finished progress."""

    if not config.progress_enabled:
        return
    SubscribeProgressReporter.from_config(config, runner_name="subscription").scan_finished()


def print_subscribe_capacity_table(result: "SubscribeCapacityResult") -> None:
    """Compatibility helper that forwards to the unified capacity summary table."""
    from tools.source_lab.access.capacity import build_subscribe_capacity_rows, print_capacity_table

    print_capacity_table(build_subscribe_capacity_rows(result, protocol="opcua"))


def print_subscribe_report(result: SubscribeScanResult) -> None:
    """Print subscription scan detail rows and summary."""

    border = "=" * 132
    print()
    print(border, flush=True)
    print("source_lab subscribe scan", flush=True)
    print(border, flush=True)
    print(f"mode={result.config.mode.value}", flush=True)
    print(f"protocol={result.config.protocol}", flush=True)
    print(
        f"server_count={result.config.server_count_start}:{result.config.server_count_step}:{result.config.server_count_max}",
        flush=True,
    )
    print(
        "publishing_interval_ms="
        f"{result.config.publishing_interval_ms} sampling_interval_ms={result.config.sampling_interval_ms} "
        f"source_update_hz={result.config.source_update_hz} queue_size={result.config.queue_size}",
        flush=True,
    )
    print("-" * 132, flush=True)
    print(
        f"{'srv':>4} {'notify':>8} {'value':>8} {'bad':>5} "
        f"{'data_p95':>10} {'data_max':>10} {'src_p95':>10} {'src_max':>10} "
        f"{'recv_p95':>10} {'lag_p95':>10} {'dispatch':>10} {'keepalive':>9} "
        f"{'timeout':>8} {'resub':>7} {'resub_ok':>9} {'resub_fail':>11} "
        f"{'unrecov':>8} {'recovery_ms':>11} {'status':>7} reason / warnings",
        flush=True,
    )
    print("-" * 132, flush=True)
    for level in result.levels:
        metrics = level.final_metrics
        warnings = "" if not metrics.warnings else " warnings=" + ",".join(metrics.warnings)
        print(
            f"{metrics.server_count:>4} {metrics.notification_count:>8} {metrics.value_count:>8} {metrics.bad_count:>5} "
            f"{metrics.data_period_p95_ms:>10.3f} {metrics.data_period_max_ms:>10.3f} "
            f"{metrics.source_period_p95_ms:>10.3f} {metrics.source_period_max_ms:>10.3f} "
            f"{metrics.recv_period_p95_ms:>10.3f} {metrics.callback_to_flush_lag_p95_ms:>10.3f} "
            f"{metrics.dispatch_gap_max_ms:>10.3f} {metrics.keepalive_count:>9} "
            f"{metrics.publish_timeout_count:>8} {metrics.resubscribe_count:>7} "
            f"{metrics.resubscribe_success_count:>9} {metrics.resubscribe_failure_count:>11} "
            f"{metrics.unrecovered_endpoint_count:>8} {metrics.recovery_duration_ms:>11.3f} {level.final_status.value:>7} "
            f"{level.final_reason or metrics.failure_reason or '-'}{warnings}",
            flush=True,
        )
        if metrics.last_reconnect_reason:
            print(f"last_reconnect_reason={metrics.last_reconnect_reason}", flush=True)
        if metrics.top_period_gap_traces:
            print("top response gaps:", flush=True)
            for gap_trace in metrics.top_period_gap_traces:
                print(
                    f"  global={gap_trace.global_index} local={gap_trace.local_index} "
                    f"prev_ns={gap_trace.previous_notify_timestamp_ns} curr_ns={gap_trace.notify_timestamp_ns} "
                    f"period_ms={gap_trace.period_ms:.3f}",
                    flush=True,
                )
        if metrics.top_data_period_gap_traces:
            print("top data notify gaps:", flush=True)
            for gap_trace in metrics.top_data_period_gap_traces:
                print(
                    f"  global={gap_trace.global_index} local={gap_trace.local_index} "
                    f"prev_ns={gap_trace.previous_notify_timestamp_ns} curr_ns={gap_trace.notify_timestamp_ns} "
                    f"period_ms={gap_trace.period_ms:.3f}",
                    flush=True,
                )
        if metrics.top_flush_lag_traces:
            print("top callback_to_flush lag:", flush=True)
            for lag_trace in metrics.top_flush_lag_traces:
                print(
                    f"  global={lag_trace.global_index} local={lag_trace.local_index} "
                    f"notify_ns={lag_trace.notify_timestamp_ns} flush_ns={lag_trace.flush_timestamp_ns} lag_ms={lag_trace.lag_ms:.3f}",
                    flush=True,
                )
        if metrics.top_dispatch_gap_traces:
            print("top endpoint dispatch gaps:", flush=True)
            for dispatch_trace in metrics.top_dispatch_gap_traces:
                print(
                    f"  global={dispatch_trace.global_index} local={dispatch_trace.local_index} "
                    f"notify={dispatch_trace.notification_count} iterate={dispatch_trace.run_iterate_count} "
                    f"dispatch_gap_ms={dispatch_trace.max_dispatch_gap_ms:.3f} "
                    f"iterate_max_ms={dispatch_trace.max_run_iterate_duration_ms:.3f} "
                    f"revised_pub_ms={dispatch_trace.revised_publishing_interval_ms:.3f} "
                    f"revised_sample_ms={dispatch_trace.revised_sampling_interval_ms:.3f}",
                    flush=True,
                )
