"""Field-mode source provider for real endpoints without simulator lifecycle."""

from __future__ import annotations

from contextlib import AbstractContextManager, nullcontext

from tools.source_lab.access.polling.model import CapacityScanConfig
from tools.source_lab.access.providers.base import SourceProvider, SourceRuntimeSpec
from tools.source_lab.access.subscribe.model import SubscribeScanConfig


class FieldSourceProvider(SourceProvider):
    """Build runtime specs directly from field endpoints and static points."""

    def build_sources(
        self,
        config: CapacityScanConfig | SubscribeScanConfig,
        *,
        server_count: int,
    ) -> tuple[SourceRuntimeSpec, ...]:
        """Build field runtime specs for one server_count level."""

        if not isinstance(config, CapacityScanConfig):
            raise ValueError("field source provider only supports capacity configs")
        if not config.endpoints:
            raise ValueError("field mode requires endpoints")
        if not config.points:
            raise ValueError("field mode requires points")
        if server_count > len(config.endpoints):
            raise ValueError(
                "field mode server_count exceeds available endpoints: "
                f"server_count={server_count}, available={len(config.endpoints)}"
            )

        selected = config.endpoints[:server_count]
        return tuple(
            SourceRuntimeSpec(endpoint=endpoint, points=config.points)
            for endpoint in selected
        )

    def started(self, sources: tuple[SourceRuntimeSpec, ...]) -> AbstractContextManager[None]:
        """Return no-op lifecycle context for field mode."""

        return nullcontext()
