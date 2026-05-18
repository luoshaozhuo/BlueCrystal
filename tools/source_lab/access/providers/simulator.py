# mypy: disable-error-code=import-untyped
"""Simulator-mode source provider for capacity scanning."""

from __future__ import annotations

import time
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import replace

from whale.shared.source.access.model import SourceEndpointSpec, SourcePointSpec
from tools.source_lab.access.model import CapacityScanConfig
from tools.source_lab.access.providers.base import SourceProvider, SourceRuntimeSpec
from tools.source_lab.fleet import SourceSimulatorFleet
from tools.source_lab.model import SimulatedSource, UpdateConfig
from tools.source_lab.opcua.address_space import logical_path
from tools.source_lab.access.utils import normalize_protocol
from tools.source_lab.sources import (
    PortAllocator,
    build_multi_sources,
    build_opcua_source_from_repository,
)


class SimulatorSourceProvider(SourceProvider):
    """Build and start simulator-backed source runtime specs."""

    def __init__(self, *, port_allocator: PortAllocator | None = None) -> None:
        self._port_allocator = port_allocator or PortAllocator.from_env()
        self._active_config: CapacityScanConfig | None = None

    @classmethod
    def from_env(cls) -> SimulatorSourceProvider:
        """Create provider using environment-derived port allocator settings."""

        return cls(port_allocator=PortAllocator.from_env())

    def build_sources(
        self,
        config: CapacityScanConfig,
        *,
        server_count: int,
    ) -> tuple[SourceRuntimeSpec, ...]:
        """Build simulator runtime specs for one server_count level."""

        protocol = normalize_protocol(config.protocol)
        if protocol != "opcua":
            raise ValueError(f"unsupported simulator protocol: {config.protocol}")

        self._active_config = config

        base_source = build_opcua_source_from_repository(
            min_expected_point_count=config.min_expected_point_count,
            max_expected_point_count=config.max_expected_point_count,
        )
        ports = self._port_allocator.allocate_many(server_count, host=base_source.connection.host)
        sources = build_multi_sources(base_source, server_count=server_count, ports=ports)
        sources = tuple(
            replace(
                source,
                connection=replace(
                    source.connection,
                    params={
                        **source.connection.params,
                        "open62541_startup_timeout_seconds": config.fleet_startup_timeout_s,
                    },
                ),
            )
            for source in sources
        )

        return tuple(self._runtime_from_simulated(source) for source in sources)

    @contextmanager
    def started(self, sources: tuple[SourceRuntimeSpec, ...]) -> Iterator[None]:
        """Start source simulator fleet for provided runtime specs."""

        if self._active_config is None:
            raise RuntimeError("provider config not initialized; call build_sources first")

        simulated_sources = tuple(
            item.runtime_handle
            for item in sources
            if isinstance(item.runtime_handle, SimulatedSource)
        )
        if len(simulated_sources) != len(sources):
            raise ValueError("simulator provider expected SimulatedSource runtime handles")

        vars_per_server = len(sources[0].points) if sources else 0
        update_interval_s = 1.0
        if vars_per_server > 0 and self._active_config.source_update_hz > 0:
            update_interval_s = 1.0 / self._active_config.source_update_hz

        fleet = SourceSimulatorFleet.create(
            sources=simulated_sources,
            update_config=UpdateConfig(
                enabled=self._active_config.source_update_enabled,
                interval_seconds=update_interval_s,
                update_count=vars_per_server,
            ),
            startup_timeout_seconds=self._active_config.fleet_startup_timeout_s,
        )
        try:
            with fleet:
                yield
        finally:
            grace = self._active_config.fleet_stop_grace_s
            if grace > 0:
                time.sleep(grace)

    def _runtime_from_simulated(self, source: SimulatedSource) -> SourceRuntimeSpec:
        endpoint = SourceEndpointSpec(
            name=source.connection.name,
            host=source.connection.host,
            port=source.connection.port,
            protocol=source.connection.protocol,
            transport=source.connection.transport,
            namespace_uri=source.connection.namespace_uri,
            ied_name=source.connection.ied_name,
            ld_name=source.connection.ld_name,
            params=dict(source.connection.params),
        )
        points = tuple(
            SourcePointSpec(
                address=logical_path(source.connection, point),
                name=point.key,
                data_type=point.data_type,
                ln_name=point.ln_name,
                do_name=point.do_name,
                unit=point.unit,
            )
            for point in source.points
        )
        return SourceRuntimeSpec(
            endpoint=endpoint,
            points=points,
            runtime_handle=source,
        )
