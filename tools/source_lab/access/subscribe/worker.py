"""Worker execution helpers for protocol-agnostic subscription levels."""

from __future__ import annotations

from collections.abc import Sequence
from concurrent.futures import ProcessPoolExecutor

from tools.source_lab.access.providers.base import SourceRuntimeSpec
from tools.source_lab.access.runners.base import SubscriptionRunner
from tools.source_lab.access.common.scheduling import (
    RunnerEndpointPlan,
    build_source_specs,
    partition_specs_round_robin,
    resolve_mp_context,
)
from tools.source_lab.access.subscribe.metrics import build_subscribe_level_metrics
from tools.source_lab.access.subscribe.model import SubscribeLevelMetrics, SubscribeScanConfig, SubscribeWorkerRawStats


def _run_worker_entry(
    worker_index: int,
    specs: tuple[RunnerEndpointPlan, ...],
    config: SubscribeScanConfig,
    runner: SubscriptionRunner,
) -> SubscribeWorkerRawStats:
    """Sync worker entrypoint for ``ProcessPoolExecutor`` workers."""

    return runner.run_worker(worker_index, specs, config)


def run_subscribe_level_once(
    sources: Sequence[SourceRuntimeSpec],
    *,
    config: SubscribeScanConfig,
    runner: SubscriptionRunner,
) -> SubscribeLevelMetrics:
    """Run one subscription level and build aggregate metrics."""

    specs = build_source_specs(
        sources,
        target_hz=max(0.001, 1000.0 / config.publishing_interval_ms),
    )
    partitions = partition_specs_round_robin(specs, process_count=config.process_count)
    non_empty_partitions = [(index, bucket) for index, bucket in enumerate(partitions) if bucket]

    if config.process_count == 1:
        worker_stats = [runner.run_worker(0, partitions[0], config)]
    else:
        with ProcessPoolExecutor(
            max_workers=config.process_count,
            mp_context=resolve_mp_context(),
        ) as executor:
            futures = [
                executor.submit(_run_worker_entry, index, bucket, config, runner)
                for index, bucket in non_empty_partitions
            ]
            worker_stats = [future.result() for future in futures]

    return build_subscribe_level_metrics(
        worker_stats,
        server_count=len(sources),
        config=config,
    )
