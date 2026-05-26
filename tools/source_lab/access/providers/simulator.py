# mypy: disable-error-code=import-untyped
"""Simulator-mode source provider for polling and subscribe scans."""

from __future__ import annotations

import time
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import replace

from whale.shared.source.access.model import SourceEndpointSpec, SourcePointSpec  # type: ignore[import-untyped]
from whale.ingest.adapters.config.source_runtime_config_repository import SourceRuntimeConfigRepository  # type: ignore[import-untyped]
from tools.source_lab.access.polling.model import CapacityScanConfig
from tools.source_lab.access.providers.base import SourceProvider, SourceRuntimeSpec
from tools.source_lab.access.runners.registry import normalize_protocol
from tools.source_lab.access.subscribe.model import SubscribeScanConfig
from tools.source_lab.fleet import SourceSimulatorFleet
from tools.source_lab.model import SourceConnection, SimulatedPoint, SimulatedSource, UpdateConfig
from tools.source_lab.protocols.opcua.address_space import logical_path
from tools.source_lab.protocols.registry import list_server_simulator_protocols
from tools.source_lab.sources import (
    PortAllocator,
    build_multi_sources,
)


class SimulatorSourceProvider(SourceProvider):
    """Build and start simulator-backed source runtime specs."""

    def __init__(self, *, port_allocator: PortAllocator | None = None) -> None:
        self._port_allocator = port_allocator or PortAllocator.from_env()
        self._active_config: CapacityScanConfig | SubscribeScanConfig | None = None

    @classmethod
    def from_env(cls) -> SimulatorSourceProvider:
        """Create provider using environment-derived port allocator settings."""

        return cls(port_allocator=PortAllocator.from_env())

    def build_sources(
        self,
        config: CapacityScanConfig | SubscribeScanConfig,
        *,
        server_count: int,
    ) -> tuple[SourceRuntimeSpec, ...]:
        """Build simulator runtime specs for one server_count level."""

        protocol = normalize_protocol(config.protocol)

        # 通过 facade registry 验证协议支持
        if protocol not in list_server_simulator_protocols():
            raise ValueError(f"unsupported simulator protocol: {config.protocol}")

        self._active_config = config

        min_expected_point_count = config.min_expected_point_count
        max_expected_point_count = config.max_expected_point_count
        if isinstance(config, SubscribeScanConfig):
            base_source = self._build_source_from_repository(
                protocol=protocol,
                min_expected_point_count=1,
                max_expected_point_count=max(10_000, max_expected_point_count),
            )
            if len(base_source.points) < min_expected_point_count:
                raise ValueError(
                    "subscribe simulator point count is lower than requested minimum: "
                    f"available={len(base_source.points)} minimum={min_expected_point_count}"
                )
            base_source = replace(
                base_source,
                points=base_source.points[:max_expected_point_count],
            )
        else:
            base_source = self._build_source_from_repository(
                protocol=protocol,
                min_expected_point_count=min_expected_point_count,
                max_expected_point_count=max_expected_point_count,
            )

        ports = self._port_allocator.allocate_many(server_count, host=base_source.connection.host)
        sources = build_multi_sources(base_source, server_count=server_count, ports=ports)

        # 兼容 OPC UA 的启动超时参数名
        timeout_key = (
            "open62541_startup_timeout_seconds"
            if protocol == "opcua"
            else "startup_timeout_seconds"
        )
        sources = tuple(
            replace(
                source,
                connection=replace(
                    source.connection,
                    params={
                        **source.connection.params,
                        timeout_key: config.fleet_startup_timeout_s,
                    },
                ),
            )
            for source in sources
        )

        return tuple(self._runtime_from_simulated(source) for source in sources)

    def _build_source_from_repository(
        self,
        protocol: str,
        *,
        min_expected_point_count: int,
        max_expected_point_count: int,
    ) -> SimulatedSource:
        """从运行时配置仓库构建指定协议的模拟源。"""
        from tools.source_lab.access.runners.registry import PROTOCOL_CAPABILITIES

        runtime_repo = SourceRuntimeConfigRepository()
        server_rows = runtime_repo.list_servers()

        # 将归一化协议名映射到数据库 application_protocol
        cap = PROTOCOL_CAPABILITIES.get(protocol)
        if cap is None:
            raise ValueError(f"no capability entry for protocol: {protocol}")
        app_protocol = cap.get("application_protocol", "")
        assert isinstance(app_protocol, str) and app_protocol

        filtered = [s for s in server_rows if s.application_protocol == app_protocol]
        if not filtered:
            raise ValueError(
                f"No repository servers found for protocol {protocol} "
                f"(application_protocol={app_protocol})"
            )
        server = filtered[0]

        point_rows = runtime_repo.list_profile_items(server.signal_profile_id)
        point_count = len(point_rows)

        if not min_expected_point_count <= point_count <= max_expected_point_count:
            raise AssertionError(
                f"Expected {min_expected_point_count}-{max_expected_point_count} "
                f"profile items per server, got {point_count}"
            )

        points = tuple(
            SimulatedPoint(
                ln_name=(row.ln_name or "").strip(),
                do_name=(row.do_name or "").strip(),
                unit=row.unit.strip() if row.unit is not None else None,
                data_type=(row.data_type or "FLOAT64").strip(),
            )
            for row in point_rows
        )

        host = (server.host or "").strip()
        namespace_uri = (server.namespace_uri or "").strip() or None
        transport = (server.transport or "").strip()
        port = int(server.port or 0)
        if not host:
            raise ValueError(f"Repository server host is required for {protocol} source simulation")
        if port <= 0:
            raise ValueError(f"Repository server port is required for {protocol} source simulation")
        if not transport:
            raise ValueError(f"Repository transport is required for {protocol} source simulation")

        return SimulatedSource(
            connection=SourceConnection(
                name=(
                    server.asset_code
                    or server.ld_name
                    or server.ied_name
                    or f"source_{server.endpoint_id}"
                ).strip(),
                ied_name=server.ied_name.strip(),
                ld_name=server.ld_name.strip(),
                host=host,
                port=port,
                transport=transport,
                protocol=protocol,
                namespace_uri=namespace_uri,
            ),
            points=points,
        )

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
        update_interval_ms = max(1, round(update_interval_s * 1000.0))

        # 根据协议构建更新参数
        protocol = normalize_protocol(self._active_config.protocol)
        update_params: dict[str, object] = {
            "source_update_enabled": self._active_config.source_update_enabled,
            "source_update_hz": self._active_config.source_update_hz,
        }
        if protocol == "opcua":
            update_params["open62541_internal_update_enabled"] = self._active_config.source_update_enabled
            update_params["open62541_internal_update_interval_ms"] = update_interval_ms
        else:
            update_params["internal_update_enabled"] = self._active_config.source_update_enabled
            update_params["internal_update_interval_ms"] = update_interval_ms

        simulated_sources = tuple(
            replace(
                source,
                connection=replace(
                    source.connection,
                    params={
                        **source.connection.params,
                        **update_params,
                    },
                ),
            )
            for source in simulated_sources
        )

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
        protocol = normalize_protocol(source.connection.protocol)
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
        # OPC UA 使用 logical_path 构造地址，其他协议使用点 key
        if protocol == "opcua":
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
        else:
            points = tuple(
                SourcePointSpec(
                    address=point.key,
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
