"""Subscribe capacity matrix execution."""

from __future__ import annotations

from dataclasses import replace
from collections.abc import Callable

from tools.source_lab.access.common.progress import CapacityProgressBar
from tools.source_lab.access.providers.base import SourceProvider
from tools.source_lab.access.runners.base import SubscriptionRunner
from tools.source_lab.access.subscribe.capacity_model import (
    SubscribeCapacityComboResult,
    SubscribeCapacityLimitSummary,
    SubscribeCapacityResult,
    SubscribeFailureStage,
)
from tools.source_lab.access.subscribe.capacity_plan import SubscribeCapacityMatrixPlan
from tools.source_lab.access.subscribe.capacity_rows import sample_hz_to_interval_ms, status_for_subscribe_level
from tools.source_lab.access.subscribe.model import (
    SubscribeLevelResult,
    SubscribeScanConfig,
    SubscribeScanResult,
)
from tools.source_lab.access.subscribe.scan import scan_source_subscriptions


def scan_subscribe_capacity(
    config: SubscribeScanConfig,
    *,
    provider: SourceProvider,
    runner: SubscriptionRunner,
    plan: SubscribeCapacityMatrixPlan,
    explicit_publishing_interval_ms: float | None = None,
    stop_on_runtime_fail: bool = True,
    stop_on_recovery_fail: bool = True,
    scan_runner: Callable[..., SubscribeScanResult] | None = None,
) -> SubscribeCapacityResult:
    """Run the subscribe capacity matrix without collapsing higher subscribe rates."""

    execute_scan = scan_source_subscriptions if scan_runner is None else scan_runner
    plan.validate()
    progress = CapacityProgressBar(
        "subscribe",
        total=plan.combo_count(),
    )
    current = 0
    combos: list[SubscribeCapacityComboResult] = []
    limit_summaries: list[SubscribeCapacityLimitSummary] = []
    try:
        for process_count in plan.process_counts:
            for queue_size in plan.queue_sizes:
                for server_count in plan.server_counts:
                    for source_update_hz in plan.source_update_hz_values:
                        max_pass_sample_hz: float | None = None
                        first_fail_sample_hz: float | None = None
                        first_fail_reason = ""
                        for sample_hz in plan.sample_hz_values:
                            current += 1
                            interval_ms = sample_hz_to_interval_ms(sample_hz)
                            runtime_interval_ms = (
                                min(interval_ms, (1000.0 / source_update_hz) / 2.0)
                                if config.source_update_enabled and sample_hz > source_update_hz
                                else interval_ms
                            )
                            subscribe_run_config = replace(
                                config,
                                process_count=process_count,
                                server_count_start=server_count,
                                server_count_step=1,
                                server_count_max=server_count,
                                queue_size=queue_size,
                                nominal_sample_hz=sample_hz,
                                sampling_interval_ms=runtime_interval_ms,
                                publishing_interval_ms=(
                                    explicit_publishing_interval_ms
                                    if explicit_publishing_interval_ms is not None
                                    else runtime_interval_ms
                                ),
                                source_update_hz=source_update_hz,
                                source_update_hz_explicit=True,
                                progress_enabled=False,
                            )
                            scan_result = execute_scan(
                                subscribe_run_config,
                                provider=provider,
                                runner=runner,
                            )
                            level = scan_result.levels[0]
                            status, reason = status_for_subscribe_level(level)
                            failure_stage = _failure_stage(level)
                            combos.append(
                                SubscribeCapacityComboResult(
                                    process_count=process_count,
                                    server_count=server_count,
                                    queue_size=queue_size,
                                    sample_hz=sample_hz,
                                    effective_source_update_hz=source_update_hz,
                                    executed=True,
                                    failure_stage=failure_stage,
                                    result=level,
                                    status=status,
                                    reason=reason,
                                )
                            )
                            progress.update(
                                process_count=process_count,
                                process_max=plan.process_counts[-1],
                                server_count=server_count,
                                server_max=plan.server_counts[-1],
                                hz=sample_hz,
                                hz_max=plan.sample_hz_values[-1],
                                current=current,
                            )
                            if status.value == "PASS":
                                max_pass_sample_hz = sample_hz
                                continue
                            if first_fail_sample_hz is None:
                                first_fail_sample_hz = sample_hz
                                first_fail_reason = reason
                        limit_summaries.append(
                            SubscribeCapacityLimitSummary(
                                process_count=process_count,
                                server_count=server_count,
                                queue_size=queue_size,
                                effective_source_update_hz=source_update_hz,
                                max_pass_sample_hz=max_pass_sample_hz,
                                first_fail_sample_hz=first_fail_sample_hz,
                                reason=first_fail_reason,
                            )
                        )
    finally:
        progress.close()
    if len(combos) != plan.combo_count():
        raise RuntimeError(
            "subscribe capacity matrix lost combinations: "
            f"expected {plan.combo_count()} rows, got {len(combos)}"
        )
    return SubscribeCapacityResult(combos=tuple(combos), limit_summaries=tuple(limit_summaries))


def _failure_stage(level: SubscribeLevelResult) -> SubscribeFailureStage | None:
    """Map runtime diagnostics into a capacity failure stage label."""

    metrics = level.final_metrics
    if metrics.runner_protocol_noise_count > 0:
        return "protocol"
    if metrics.unrecovered_endpoint_count > 0 or metrics.resubscribe_failure_count > 0:
        return "recovery"
    if metrics.passed:
        return None
    return "runtime"
