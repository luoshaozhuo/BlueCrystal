"""Runner interfaces used by protocol-agnostic capacity worker orchestration."""

from __future__ import annotations

from typing import Protocol

from tools.source_lab.access.metrics import WorkerRawStats
from tools.source_lab.access.model import CapacityScanConfig
from tools.source_lab.access.scheduling import RunnerEndpointPlan


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
