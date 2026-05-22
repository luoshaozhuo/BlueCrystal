"""Runner interfaces used by protocol-agnostic access worker orchestration."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from tools.source_lab.access.polling.metrics import WorkerRawStats
from tools.source_lab.access.polling.model import CapacityScanConfig
from tools.source_lab.access.subscribe.model import SubscribeScanConfig, SubscribeWorkerRawStats
from tools.source_lab.access.common.scheduling import RunnerEndpointPlan


@runtime_checkable
class CapacityRunner(Protocol):
    """Capacity runner interface used by protocol-agnostic worker orchestration."""

    @property
    def name(self) -> str:
        """Return a stable runner name for progress reporting."""

    def run_worker(
        self,
        worker_index: int,
        specs: tuple[RunnerEndpointPlan, ...],
        target_hz: float,
        config: CapacityScanConfig,
    ) -> WorkerRawStats:
        """Run one worker partition and return raw worker metrics.

        Args:
            worker_index: Zero-based worker slot.
            specs: Endpoint plans assigned to this worker.
            target_hz: Requested per-endpoint polling rate.
            config: Capacity scan configuration for this level.

        Returns:
            Raw worker metrics from the concrete protocol runner.
        """


@runtime_checkable
class SubscriptionRunner(Protocol):
    """Subscription runner interface used by protocol-agnostic worker orchestration."""

    @property
    def name(self) -> str:
        """Return a stable runner name for progress reporting."""

    def run_worker(
        self,
        worker_index: int,
        specs: tuple[RunnerEndpointPlan, ...],
        config: SubscribeScanConfig,
    ) -> SubscribeWorkerRawStats:
        """Run one worker partition and return raw subscription metrics.

        Args:
            worker_index: Zero-based worker slot.
            specs: Endpoint plans assigned to this worker.
            config: Subscription scan configuration for this level.

        Returns:
            Raw worker metrics from the concrete protocol runner.
        """
