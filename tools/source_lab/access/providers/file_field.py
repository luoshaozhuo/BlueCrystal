"""File-backed field source provider that only exposes validated runtime sources."""

from __future__ import annotations

from contextlib import AbstractContextManager, nullcontext

from tools.source_lab.access.polling.model import CapacityScanConfig
from tools.source_lab.access.providers.base import SourceProvider, SourceRuntimeSpec
from tools.source_lab.access.subscribe.model import SubscribeScanConfig
from tools.source_lab.access.common.utils import normalize_protocol


class FieldFileSourceProvider(SourceProvider):
    """Build runtime specs directly from validated field input files."""

    def __init__(
        self,
        sources: tuple[SourceRuntimeSpec, ...],
        *,
        protocol: str | None = None,
    ) -> None:
        """Initialize the provider.

        Args:
            sources: Pre-built runtime sources bound by ``profile_id``.
            protocol: Optional protocol filter applied at provider boundary.
        """

        requested = normalize_protocol(protocol) if protocol is not None else None
        self._sources = tuple(
            source
            for source in sources
            if requested is None or normalize_protocol(source.endpoint.protocol) == requested
        )
        self._protocol = requested

    def build_sources(
        self,
        config: CapacityScanConfig | SubscribeScanConfig,
        *,
        server_count: int,
    ) -> tuple[SourceRuntimeSpec, ...]:
        """Build runtime specs for one server-count level.

        Args:
            config: Capacity scan configuration for the current level.
            server_count: Number of sources requested for this level.

        Returns:
            The first ``server_count`` validated runtime sources.

        Raises:
            ValueError: If the requested count exceeds the filtered source pool
                or the config protocol conflicts with the provider protocol.
        """

        if server_count > len(self._sources):
            raise ValueError(
                "field file provider server_count exceeds available endpoints: "
                f"server_count={server_count}, available={len(self._sources)}"
            )
        if self._protocol is not None and normalize_protocol(config.protocol) != self._protocol:
            raise ValueError(
                "field file provider protocol mismatch: "
                f"provider={self._protocol}, config={normalize_protocol(config.protocol)}"
            )
        return self._sources[:server_count]

    def started(self, sources: tuple[SourceRuntimeSpec, ...]) -> AbstractContextManager[None]:
        """Return no-op lifecycle context for field mode."""

        return nullcontext()


def build_field_source_provider(
    sources: tuple[SourceRuntimeSpec, ...],
    *,
    protocol: str | None = None,
    default_port_start: int = 45000,
) -> SourceProvider:
    """Build the appropriate field provider for real or simulator-backed fixtures."""

    requested = normalize_protocol(protocol) if protocol is not None else None
    filtered_sources = tuple(
        source
        for source in sources
        if requested is None or normalize_protocol(source.endpoint.protocol) == requested
    )
    if filtered_sources and all(source.endpoint.params.get("source_lab_runtime") == "simulator" for source in filtered_sources):
        from tools.source_lab.access.providers.expanded_field import ExpandedFieldSourceProvider

        port_start = min(source.endpoint.port for source in filtered_sources)
        if port_start <= 0:
            port_start = default_port_start
        return ExpandedFieldSourceProvider(filtered_sources, port_start=port_start)
    return FieldFileSourceProvider(sources, protocol=protocol)
