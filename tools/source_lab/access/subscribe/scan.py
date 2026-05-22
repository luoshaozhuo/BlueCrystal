"""Protocol-agnostic orchestration for subscription scan ramps."""

from __future__ import annotations

from tools.source_lab.access.polling.model import CapacityStatus
from tools.source_lab.access.providers.base import SourceProvider
from tools.source_lab.access.runners.base import SubscriptionRunner
from tools.source_lab.access.common.scheduling import iter_int_ramp
from tools.source_lab.access.subscribe.model import (
    SubscribeLevelResult,
    SubscribeScanConfig,
    SubscribeScanResult,
)
from tools.source_lab.access.subscribe.reporter import (
    SubscribeProgressReporter,
)
from tools.source_lab.access.subscribe.worker import run_subscribe_level_once


def _run_confirmed_level(
    sources: tuple,
    *,
    config: SubscribeScanConfig,
    runner: SubscriptionRunner,
    progress: SubscribeProgressReporter,
) -> SubscribeLevelResult:
    """Run one subscription level with optional fail-confirm retries."""

    attempts = []
    for attempt_index in range(1, config.fail_confirm_runs + 1):
        progress.level_started(
            server_count=len(sources),
            attempt_index=attempt_index,
            attempt_total=config.fail_confirm_runs,
        )
        metrics = run_subscribe_level_once(sources, config=config, runner=runner)
        attempts.append(metrics)
        status = CapacityStatus.PASS if metrics.passed else CapacityStatus.FAIL
        reason = metrics.failure_reason
        progress.level_done(metrics=metrics, attempt_index=attempt_index, status=status, reason=reason)
        if metrics.passed:
            return SubscribeLevelResult(
                primary=metrics,
                attempts=tuple(attempts),
                final_status=CapacityStatus.PASS,
                final_reason="",
            )
    return SubscribeLevelResult(
        primary=attempts[-1],
        attempts=tuple(attempts),
        final_status=CapacityStatus.FAIL,
        final_reason=attempts[-1].failure_reason,
    )


def scan_source_subscriptions(
    config: SubscribeScanConfig,
    *,
    provider: SourceProvider,
    runner: SubscriptionRunner,
) -> SubscribeScanResult:
    """Run subscription scan across the configured server-count ramp."""

    progress = SubscribeProgressReporter.from_config(config, runner_name=runner.name)
    started_at = progress.scan_started()
    level_results: list[SubscribeLevelResult] = []
    try:
        for server_count in iter_int_ramp(
            config.server_count_start,
            config.server_count_step,
            config.server_count_max,
        ):
            sources = provider.build_sources(config, server_count=server_count)
            with provider.started(sources):
                result = _run_confirmed_level(tuple(sources), config=config, runner=runner, progress=progress)
                level_results.append(result)
                if (
                    config.stop_ramp_on_first_fail
                    and result.final_status in {CapacityStatus.FAIL, CapacityStatus.FLAKY, CapacityStatus.SKIP}
                ):
                    progress.stop_ramp(
                        server_count=server_count,
                        status=result.final_status,
                        reason=result.final_reason or result.final_metrics.failure_reason,
                    )
                    break
    finally:
        progress.scan_finished()
    return SubscribeScanResult(config=config, levels=tuple(level_results))
