"""Source providers used by protocol-agnostic polling and subscribe scans."""

from __future__ import annotations

from contextlib import AbstractContextManager
from dataclasses import dataclass
from typing import Protocol

from whale.shared.source.access.model import SourceEndpointSpec, SourcePointSpec  # type: ignore[import-untyped]
from tools.source_lab.access.polling.model import CapacityScanConfig
from tools.source_lab.access.subscribe.model import SubscribeScanConfig


@dataclass(frozen=True, slots=True)
class SourceRuntimeSpec:
    """Runtime source details consumed by capacity scanner internals."""

    endpoint: SourceEndpointSpec
    points: tuple[SourcePointSpec, ...]
    runtime_handle: object | None = None


class SourceProvider(Protocol):
    """Protocol for scanner source provisioning and lifecycle management."""

    def build_sources(
        self,
        config: CapacityScanConfig | SubscribeScanConfig,
        *,
        server_count: int,
    ) -> tuple[SourceRuntimeSpec, ...]:
        """Build source runtime specs for one server_count level."""

    def started(self, sources: tuple[SourceRuntimeSpec, ...]) -> AbstractContextManager[None]:
        """Return context manager that starts/stops runtime resources for sources."""
