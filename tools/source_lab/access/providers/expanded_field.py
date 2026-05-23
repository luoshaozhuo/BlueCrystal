"""Decorator provider that expands field-export templates into simulator-backed sources."""

from __future__ import annotations

import time
from contextlib import contextmanager
from dataclasses import replace
from typing import Callable, Iterator

from whale.shared.source.access.model import SourceEndpointSpec, SourcePointSpec  # type: ignore[import-untyped]

from tools.source_lab.access.polling.model import CapacityScanConfig
from tools.source_lab.access.providers.base import SourceProvider, SourceRuntimeSpec
from tools.source_lab.access.subscribe.model import SubscribeScanConfig
from tools.source_lab.fleet import SourceSimulatorFleet
from tools.source_lab.model import SimulatedPoint, SimulatedSource, SourceConnection, UpdateConfig
from tools.source_lab.sources import PortAllocator

_DEFAULT_PORT_END = 65000


class ExpandedFieldSourceProvider(SourceProvider):
    """Expand validated field-export sources into localhost simulator sources."""

    def __init__(
        self,
        base_sources: tuple[SourceRuntimeSpec, ...],
        *,
        port_start: int | None = None,
        port_end: int | None = None,
        host: str = "127.0.0.1",
        port_allocator: PortAllocator | None = None,
        fleet_factory: Callable[..., SourceSimulatorFleet] | None = None,
    ) -> None:
        if not base_sources:
            raise ValueError("expanded field provider requires at least one base source")
        self._base_sources = base_sources
        self._host = host
        if port_allocator is not None:
            self._port_allocator = port_allocator
        else:
            if port_start is not None:
                # Explicit port_start provided; use it with port_end
                resolved_end = port_end if port_end is not None else _DEFAULT_PORT_END
                self._port_allocator = PortAllocator.from_range(
                    start=port_start,
                    end=resolved_end,
                )
            else:
                # No port_start provided; use env defaults (50000-65000)
                self._port_allocator = PortAllocator.from_env()
        self._active_config: CapacityScanConfig | SubscribeScanConfig | None = None
        self._fleet_factory = fleet_factory or SourceSimulatorFleet.create

    def build_sources(
        self,
        config: CapacityScanConfig | SubscribeScanConfig,
        *,
        server_count: int,
    ) -> tuple[SourceRuntimeSpec, ...]:
        """Build expanded sources for one server-count level."""

        if server_count <= 0:
            raise ValueError("expanded field provider requires server_count > 0")
        self._active_config = config
        ports = self._port_allocator.allocate_many(server_count, host=self._host)
        expanded: list[SourceRuntimeSpec] = []
        for index in range(server_count):
            template = self._base_sources[index % len(self._base_sources)]
            endpoint = template.endpoint
            endpoint_id = f"{endpoint.name}-{index + 1:03d}"
            cloned_endpoint = replace(
                endpoint,
                name=endpoint_id,
                host=self._host,
                port=ports[index],
                ied_name=f"{endpoint.ied_name or endpoint.name}_{index + 1:03d}",
                params={
                    **dict(endpoint.params),
                    "profile_id": str(endpoint.params.get("profile_id", "")),
                    "template_endpoint_id": endpoint.name,
                },
            )
            cloned_points = tuple(
                replace(
                    point,
                    address=(
                        f"{cloned_endpoint.ied_name}.{cloned_endpoint.ld_name}.{point.ln_name}.{point.do_name}"
                        if point.ln_name and point.do_name
                        else point.address
                    ),
                )
                for point in template.points
            )
            runtime_source = SourceRuntimeSpec(
                endpoint=cloned_endpoint,
                points=cloned_points,
                runtime_handle=self._to_simulated_source(cloned_endpoint, cloned_points),
            )
            expanded.append(runtime_source)
        return tuple(expanded)

    @contextmanager
    def started(self, sources: tuple[SourceRuntimeSpec, ...]) -> Iterator[None]:
        """Start a simulator fleet for expanded sources."""

        if self._active_config is None:
            raise RuntimeError("provider config not initialized; call build_sources first")
        simulated_sources = tuple(
            item.runtime_handle
            for item in sources
            if isinstance(item.runtime_handle, SimulatedSource)
        )
        if len(simulated_sources) != len(sources):
            raise ValueError("expanded field provider expected SimulatedSource runtime handles")
        update_interval_s = 1.0 / self._active_config.source_update_hz
        update_interval_ms = max(1, round(update_interval_s * 1000.0))
        simulated_sources = tuple(
            replace(
                source,
                connection=replace(
                    source.connection,
                    params={
                        **source.connection.params,
                        "source_update_enabled": self._active_config.source_update_enabled,
                        "source_update_hz": self._active_config.source_update_hz,
                        "open62541_startup_timeout_seconds": self._active_config.fleet_startup_timeout_s,
                        "open62541_internal_update_enabled": self._active_config.source_update_enabled,
                        "open62541_internal_update_interval_ms": update_interval_ms,
                    },
                ),
            )
            for source in simulated_sources
        )
        fleet = self._fleet_factory(
            sources=simulated_sources,
            update_config=UpdateConfig(
                enabled=self._active_config.source_update_enabled,
                interval_seconds=update_interval_s,
                update_count=len(sources[0].points) if sources else None,
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

    def _to_simulated_source(
        self,
        endpoint: SourceEndpointSpec,
        points: tuple[SourcePointSpec, ...],
    ) -> SimulatedSource:
        connection = SourceConnection(
            name=str(endpoint.name),
            ied_name=str(endpoint.ied_name or endpoint.name),
            ld_name=str(endpoint.ld_name or "LD0"),
            host=str(endpoint.host),
            port=int(endpoint.port),
            transport=str(endpoint.transport),
            protocol=str(endpoint.protocol),
            namespace_uri=endpoint.namespace_uri,
            params=dict(endpoint.params),
        )
        simulated_points = tuple(
            SimulatedPoint(
                ln_name=str(point.ln_name or "LN0"),
                do_name=str(point.do_name or point.name or point.address),
                unit=point.unit,
                data_type=str(point.data_type),
                initial_value=0.0,
            )
            for point in points
        )
        return SimulatedSource(connection=connection, points=simulated_points)
