# mypy: disable-error-code=import-untyped
"""Worker execution helpers for protocol-agnostic capacity levels."""

from __future__ import annotations

from collections.abc import Sequence
from concurrent.futures import ProcessPoolExecutor

from tools.source_lab.access.metrics import WorkerRawStats, build_level_metrics
from tools.source_lab.access.model import CapacityLevelMetrics, CapacityScanConfig
from tools.source_lab.access.providers.base import SourceRuntimeSpec
from tools.source_lab.access.reporter import print_runner_started, print_worker_diagnostics
from tools.source_lab.access.runners.base import CapacityRunner
from tools.source_lab.access.scheduling import (
    RunnerEndpointPlan,
    build_source_specs,
    partition_specs_round_robin,
    resolve_mp_context,
)


def _run_worker_entry(
    worker_index: int,
    specs: tuple[RunnerEndpointPlan, ...],
    target_hz: float,
    config: CapacityScanConfig,
    runner: CapacityRunner,
) -> WorkerRawStats:
    """Sync worker entrypoint for ``ProcessPoolExecutor`` workers."""

    return runner.run_worker(worker_index, specs, target_hz, config)


def run_worker_level(
    specs: Sequence[RunnerEndpointPlan],
    *,
    target_hz: float,
    worker_index: int,
    config: CapacityScanConfig,
    runner: CapacityRunner,
) -> WorkerRawStats:
    """Run one worker bucket with the injected capacity runner.

    Args:
        specs: Endpoint plans for this worker.
        target_hz: Requested per-endpoint polling rate.
        worker_index: Zero-based worker slot.
        config: Capacity scan configuration.
        runner: Concrete runner implementation.

    Returns:
        Raw worker metrics for the bucket.
    """

    return runner.run_worker(worker_index, tuple(specs), target_hz, config)


def run_level_once(
    sources: Sequence[SourceRuntimeSpec],
    *,
    target_hz: float,
    config: CapacityScanConfig,
    runner: CapacityRunner,
) -> CapacityLevelMetrics:
    """Run one ``(server_count, hz)`` level and build aggregate metrics.

    Args:
        sources: Runtime source specs for this level.
        target_hz: Requested per-endpoint polling rate.
        config: Capacity scan configuration.
        runner: Concrete runner implementation.

    Returns:
        Aggregate metrics for the level.
    """

    specs = build_source_specs(sources, target_hz=target_hz)
    partitions = partition_specs_round_robin(specs, process_count=config.process_count)
    non_empty_partitions = [(index, bucket) for index, bucket in enumerate(partitions) if bucket]

    for index, bucket in non_empty_partitions:
        print_runner_started(
            config,
            runner_name=runner.name,
            worker_index=index,
            endpoint_count=len(bucket),
            target_hz=target_hz,
        )

    if config.process_count == 1:
        worker_stats = [runner.run_worker(0, partitions[0], target_hz, config)]
    else:
        with ProcessPoolExecutor(
            max_workers=config.process_count,
            mp_context=resolve_mp_context(),
        ) as executor:
            futures = [
                executor.submit(_run_worker_entry, index, bucket, target_hz, config, runner)
                for index, bucket in non_empty_partitions
            ]
            worker_stats = [future.result() for future in futures]

    print_worker_diagnostics(config, worker_stats)

    return build_level_metrics(
        worker_stats,
        server_count=len(sources),
        target_hz=target_hz,
        config=config,
    )
