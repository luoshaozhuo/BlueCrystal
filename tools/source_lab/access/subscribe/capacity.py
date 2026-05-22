"""Subscribe capacity service facade and public exports.

This module is the stable subscribe-capacity entrypoint for callers that need
matrix planning plus execution in one call.
"""

from __future__ import annotations

from tools.source_lab.access.common.scheduling import iter_int_ramp
from tools.source_lab.access.providers.base import SourceProvider
from tools.source_lab.access.runners.base import SubscriptionRunner
from tools.source_lab.access.subscribe.capacity_model import (
    SubscribeCapacityComboResult,
    SubscribeCapacityLimitSummary,
    SubscribeCapacityResult,
)
from tools.source_lab.access.subscribe.capacity_plan import SubscribeCapacityMatrixPlan
from tools.source_lab.access.subscribe.capacity_scan import scan_subscribe_capacity
from tools.source_lab.access.subscribe.model import SubscribeScanConfig


def scan_subscribe_capacity_service(
    config: SubscribeScanConfig,
    *,
    provider: SourceProvider,
    runner: SubscriptionRunner,
    process_counts: tuple[int, ...],
    sample_hz_values: tuple[float, ...],
    queue_sizes: tuple[int, ...],
    source_update_hz_values: tuple[float, ...] | None = None,
    explicit_publishing_interval_ms: float | None = None,
    stop_on_first_fail_per_server: bool = True,
) -> SubscribeCapacityResult:
    """Build a subscribe capacity matrix plan and execute it.

    Args:
        config: Base subscribe scan config.
        provider: Source provider used to build runtime sources.
        runner: Subscription runner implementation.
        process_counts: Process-count dimension for matrix scan.
        sample_hz_values: Subscribe sample-hz dimension for matrix scan.
        queue_sizes: Queue-size dimension for matrix scan.
        source_update_hz_values: Optional explicit source-update-hz dimension.
        explicit_publishing_interval_ms: Optional fixed publishing interval override.
        stop_on_first_fail_per_server: Stop on first runtime/recovery failure per server.

    Returns:
        Subscribe capacity matrix result.
    """

    return scan_subscribe_capacity(
        config,
        provider=provider,
        runner=runner,
        plan=SubscribeCapacityMatrixPlan(
            process_counts=process_counts,
            server_counts=tuple(iter_int_ramp(config.server_count_start, config.server_count_step, config.server_count_max)),
            source_update_hz_values=source_update_hz_values or (config.source_update_hz,),
            sample_hz_values=sample_hz_values,
            queue_sizes=queue_sizes,
        ),
        explicit_publishing_interval_ms=explicit_publishing_interval_ms,
        stop_on_runtime_fail=stop_on_first_fail_per_server,
        stop_on_recovery_fail=stop_on_first_fail_per_server,
    )


__all__ = [
    "SubscribeCapacityComboResult",
    "SubscribeCapacityLimitSummary",
    "SubscribeCapacityResult",
    "scan_subscribe_capacity",
    "scan_subscribe_capacity_service",
]
