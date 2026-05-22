"""Unified capacity façade that dispatches by access mode."""

from __future__ import annotations

from dataclasses import replace

from tools.source_lab.access.field_capacity import (
    FieldCapacityArtifacts,
    FieldCapacityRequest,
    FieldCapacityRow,
    FieldCapacityServiceResult,
    build_polling_capacity_rows,
    build_subscribe_capacity_rows,
    print_capacity_summary,
    print_capacity_table,
    run_field_capacity,
    run_field_capacity_from_files,
    write_capacity_reports,
)
from tools.source_lab.access.common.scheduling import iter_float_ramp, iter_int_ramp
from tools.source_lab.access.common.progress import CapacityProgressBar
from tools.source_lab.access.polling.capacity import scan_source_capacity
from tools.source_lab.access.polling.model import CapacityMode, CapacityScanConfig, CapacityScanResult, CapacityStatus
from tools.source_lab.access.providers.base import SourceProvider
from tools.source_lab.access.runners.base import CapacityRunner, SubscriptionRunner
from tools.source_lab.access.subscribe.capacity_model import (
    SubscribeCapacityComboResult,
    SubscribeCapacityLimitSummary,
    SubscribeCapacityResult,
)
from tools.source_lab.access.subscribe.capacity_plan import SubscribeCapacityMatrixPlan
from tools.source_lab.access.subscribe.capacity_scan import scan_subscribe_capacity
from tools.source_lab.access.subscribe.model import SubscribeScanConfig, SubscribeScanResult
from tools.source_lab.access.subscribe.scan import scan_source_subscriptions


def _polling_server_counts(config: CapacityScanConfig) -> tuple[int, ...]:
    return tuple(iter_int_ramp(config.server_count_start, config.server_count_step, config.server_count_max))


def _polling_hz_values(config: CapacityScanConfig) -> tuple[float, ...]:
    return tuple(iter_float_ramp(config.hz_start, config.hz_step, config.hz_max))


def _explicit_subscribe_source_update_hz(
    config: SubscribeScanConfig,
    explicit_source_update_hz: float | None,
) -> float | None:
    """Resolve whether subscribe capacity should use an explicit fixed source update rate."""

    if explicit_source_update_hz is not None:
        return explicit_source_update_hz
    if config.source_update_hz_explicit:
        return config.source_update_hz
    return None


def scan_capacity(
    access_mode: str,
    *,
    config: CapacityScanConfig | SubscribeScanConfig,
    provider: SourceProvider,
    runner: CapacityRunner | SubscriptionRunner,
    process_counts: tuple[int, ...] | None = None,
    sample_hz_values: tuple[float, ...] | None = None,
    queue_sizes: tuple[int, ...] | None = None,
    source_update_hz_values: tuple[float, ...] | None = None,
    explicit_publishing_interval_ms: float | None = None,
    explicit_source_update_hz: float | None = None,
    stop_on_first_fail_per_server: bool = True,
) -> CapacityScanResult | tuple[CapacityScanResult, ...] | SubscribeCapacityResult | SubscribeScanResult:
    """Run capacity workloads for polling or subscribe."""

    if access_mode == "polling":
        if not isinstance(config, CapacityScanConfig):
            raise TypeError("polling capacity requires CapacityScanConfig")
        if not isinstance(runner, CapacityRunner):
            raise TypeError("polling capacity requires CapacityRunner")
        if not process_counts:
            return scan_source_capacity(config, provider=provider, runner=runner)
        process_values = process_counts or (config.process_count,)
        server_counts = _polling_server_counts(config)
        hz_values = _polling_hz_values(config)
        progress = CapacityProgressBar(
            "polling",
            total=len(process_values) * len(server_counts) * len(hz_values),
        )
        current = 0
        results: list[CapacityScanResult] = []
        try:
            for process_count in process_values:
                level_results = []
                process_config = replace(config, process_count=process_count)
                for server_count in server_counts:
                    stop_hz_ramp_for_current_server = False
                    for hz in hz_values:
                        polling_run_config = replace(
                            process_config,
                            process_count=process_count,
                            server_count_start=server_count,
                            server_count_step=1,
                            server_count_max=server_count,
                            hz_start=hz,
                            hz_step=hz,
                            hz_max=hz,
                            progress_enabled=False,
                        )
                        polling_result = scan_source_capacity(polling_run_config, provider=provider, runner=runner)
                        polling_level = polling_result.levels[0]
                        level_results.append(polling_level)
                        current += 1
                        progress.update(
                            process_count=process_count,
                            process_max=process_values[-1],
                            server_count=server_count,
                            server_max=server_counts[-1],
                            hz=hz,
                            hz_max=hz_values[-1],
                            current=current,
                        )
                        if (
                            config.stop_hz_ramp_on_first_fail
                            and polling_level.final_status
                            in {CapacityStatus.FLAKY, CapacityStatus.FAIL, CapacityStatus.SKIP}
                        ):
                            stop_hz_ramp_for_current_server = True
                            break
                    if stop_hz_ramp_for_current_server:
                        continue
                results.append(CapacityScanResult(config=process_config, levels=tuple(level_results)))
        finally:
            progress.close()
        return tuple(results)

    if access_mode != "subscribe":
        raise ValueError(f"unsupported access_mode: {access_mode}")
    if not isinstance(config, SubscribeScanConfig):
        raise TypeError("subscribe capacity requires SubscribeScanConfig")
    if not isinstance(runner, SubscriptionRunner):
        raise TypeError("subscribe capacity requires SubscriptionRunner")
    if (
        process_counts is None
        and sample_hz_values is None
        and queue_sizes is None
        and source_update_hz_values is None
        and explicit_publishing_interval_ms is None
        and explicit_source_update_hz is None
    ):
        return scan_source_subscriptions(replace(config, progress_enabled=False), provider=provider, runner=runner)

    resolved_sample_hz_values = sample_hz_values or (
        config.nominal_sample_hz if config.nominal_sample_hz is not None else 1000.0 / config.sampling_interval_ms,
    )
    resolved_queue_sizes = queue_sizes or (config.queue_size,)
    resolved_source_update_hz_values = source_update_hz_values
    if not resolved_source_update_hz_values:
        explicit_update_hz = _explicit_subscribe_source_update_hz(config, explicit_source_update_hz)
        if explicit_update_hz is not None:
            resolved_source_update_hz_values = (explicit_update_hz,)
        else:
            resolved_source_update_hz_values = (config.source_update_hz,)
    return scan_subscribe_capacity(
        config,
        provider=provider,
        runner=runner,
        plan=SubscribeCapacityMatrixPlan(
            process_counts=process_counts or (config.process_count,),
            server_counts=tuple(iter_int_ramp(config.server_count_start, config.server_count_step, config.server_count_max)),
            source_update_hz_values=resolved_source_update_hz_values,
            sample_hz_values=resolved_sample_hz_values,
            queue_sizes=resolved_queue_sizes,
        ),
        explicit_publishing_interval_ms=explicit_publishing_interval_ms,
        stop_on_runtime_fail=stop_on_first_fail_per_server,
        stop_on_recovery_fail=stop_on_first_fail_per_server,
        scan_runner=scan_source_subscriptions,
    )


__all__ = [
    "CapacityMode",
    "CapacityScanConfig",
    "CapacityScanResult",
    "CapacityStatus",
    "FieldCapacityArtifacts",
    "FieldCapacityRequest",
    "FieldCapacityRow",
    "FieldCapacityServiceResult",
    "SubscribeCapacityComboResult",
    "SubscribeCapacityLimitSummary",
    "SubscribeCapacityResult",
    "build_polling_capacity_rows",
    "build_subscribe_capacity_rows",
    "print_capacity_summary",
    "print_capacity_table",
    "run_field_capacity",
    "run_field_capacity_from_files",
    "scan_capacity",
    "scan_source_capacity",
    "scan_source_subscriptions",
    "write_capacity_reports",
]
