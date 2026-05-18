# mypy: disable-error-code=import-untyped
"""Protocol-agnostic orchestration for capacity scan ramps."""

from __future__ import annotations

from collections.abc import Sequence

from tools.source_lab.access.model import (
    CapacityLevelMetrics,
    CapacityScanConfig,
    CapacityScanResult,
    CapacityStatus,
    ConfirmedLevelResult,
)
from tools.source_lab.access.providers.base import SourceProvider, SourceRuntimeSpec
from tools.source_lab.access.reporter import (
    print_level_done,
    print_level_started,
    print_measurement_started,
    print_scan_finished,
    print_scan_started,
    print_stop_hz_ramp,
)
from tools.source_lab.access.runners.base import CapacityRunner
from tools.source_lab.access.scheduling import iter_float_ramp, iter_int_ramp
from tools.source_lab.access.worker import run_level_once


def _run_confirmed_level(
    sources: Sequence[SourceRuntimeSpec],
    *,
    target_hz: float,
    config: CapacityScanConfig,
    runner: CapacityRunner,
) -> ConfirmedLevelResult:
    """Run one level with optional fail-confirm retries."""

    attempts: list[CapacityLevelMetrics] = []
    max_attempts = max(1, config.fail_confirm_runs)
    for attempt_index in range(1, max_attempts + 1):
        print_level_started(
            config,
            server_count=len(sources),
            target_hz=target_hz,
            attempt_index=attempt_index,
            attempt_total=max_attempts,
        )
        print_measurement_started(config, server_count=len(sources), target_hz=target_hz)
        metrics = run_level_once(sources, target_hz=target_hz, config=config, runner=runner)
        attempts.append(metrics)
        if metrics.passed:
            if len(attempts) == 1:
                result = ConfirmedLevelResult(
                    primary=attempts[0],
                    attempts=tuple(attempts),
                    final_status=CapacityStatus.PASS,
                    final_reason="",
                )
                print_level_done(
                    config,
                    metrics=metrics,
                    attempt_index=attempt_index,
                    status=result.final_status,
                    reason=result.final_reason,
                )
                return result
            result = ConfirmedLevelResult(
                primary=attempts[0],
                attempts=tuple(attempts),
                final_status=CapacityStatus.FLAKY,
                final_reason=f"recovered on attempt {len(attempts)}",
            )
            print_level_done(
                config,
                metrics=metrics,
                attempt_index=attempt_index,
                status=result.final_status,
                reason=result.final_reason,
            )
            return result

        print_level_done(
            config,
            metrics=metrics,
            attempt_index=attempt_index,
            status=CapacityStatus.FAIL,
            reason=metrics.failure_reason,
        )

    return ConfirmedLevelResult(
        primary=attempts[0],
        attempts=tuple(attempts),
        final_status=CapacityStatus.FAIL,
        final_reason=attempts[-1].failure_reason,
    )


def scan_source_capacity(
    config: CapacityScanConfig,
    *,
    provider: SourceProvider,
    runner: CapacityRunner,
) -> CapacityScanResult:
    """Run capacity scan across server-count and hz ramps.

    Args:
        config: Capacity scan configuration.
        provider: Source provisioning and lifecycle adapter.
        runner: Concrete protocol runner implementation.

    Returns:
        Final scan result across all executed levels.
    """

    started_at = print_scan_started(config, runner_name=runner.name)
    level_results: list[ConfirmedLevelResult] = []

    try:
        for server_count in iter_int_ramp(
            config.server_count_start,
            config.server_count_step,
            config.server_count_max,
        ):
            sources = provider.build_sources(config, server_count=server_count)
            with provider.started(sources):
                for target_hz in iter_float_ramp(config.hz_start, config.hz_step, config.hz_max):
                    result = _run_confirmed_level(
                        sources,
                        target_hz=target_hz,
                        config=config,
                        runner=runner,
                    )
                    level_results.append(result)
                    if (
                        config.stop_hz_ramp_on_first_fail
                        and result.final_status
                        in {
                            CapacityStatus.FLAKY,
                            CapacityStatus.FAIL,
                            CapacityStatus.SKIP,
                        }
                    ):
                        print_stop_hz_ramp(
                            config,
                            server_count=server_count,
                            target_hz=target_hz,
                            status=result.final_status,
                            reason=result.final_reason or result.primary.failure_reason,
                        )
                        break
    finally:
        print_scan_finished(config, started_at=started_at)

    return CapacityScanResult(config=config, levels=tuple(level_results))
