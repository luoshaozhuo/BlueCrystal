# mypy: disable-error-code=import-untyped
"""Simulator-mode source provider。

本 provider 只负责编排 source_lab simulator 所需的本地运行态 source 定义。
shared persistence 数据库读取被收敛到 `scada_profile.py`，这里不再直接查询
ingest runtime repository。
"""

from __future__ import annotations

import time
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import replace

from whale.shared.source.access.model import SourceEndpointSpec, SourcePointSpec  # type: ignore[import-untyped]
from tools.source_lab.access.polling.model import CapacityScanConfig
from tools.source_lab.access.providers.base import SourceProvider, SourceRuntimeSpec
from tools.source_lab.access.providers.scada_profile import ScadaProfileProvider
from tools.source_lab.access.runners.registry import normalize_protocol
from tools.source_lab.access.subscribe.model import SubscribeScanConfig
from tools.source_lab.fleet import SourceSimulatorFleet
from tools.source_lab.model import SimulatedSource, UpdateConfig
from tools.source_lab.protocols.opcua.address_space import logical_path
from tools.source_lab.protocols.registry import list_server_simulator_protocols
from tools.source_lab.sources import (
    PortAllocator,
    build_multi_sources,
)


class SimulatorSourceProvider(SourceProvider):
    """构建并启动基于 shared persistence 样例的 simulator runtime 源。"""

    def __init__(
        self,
        *,
        port_allocator: PortAllocator | None = None,
        profile_provider: ScadaProfileProvider | None = None,
    ) -> None:
        self._port_allocator = port_allocator or PortAllocator.from_env()
        self._profile_provider = profile_provider or ScadaProfileProvider()
        self._active_config: CapacityScanConfig | SubscribeScanConfig | None = None

    @classmethod
    def from_env(cls) -> SimulatorSourceProvider:
        """使用环境变量端口范围创建 provider。"""

        return cls(port_allocator=PortAllocator.from_env())

    def build_sources(
        self,
        config: CapacityScanConfig | SubscribeScanConfig,
        *,
        server_count: int,
    ) -> tuple[SourceRuntimeSpec, ...]:
        """为当前 server_count 级别构造 simulator runtime sources。"""

        protocol = normalize_protocol(config.protocol)

        # 这里只接受 source_lab 已注册 facade 的协议；未注册协议必须在 provider
        # 侧标记 pending/unavailable，不能伪装成已支持 runtime。
        if protocol not in list_server_simulator_protocols():
            raise ValueError(f"unsupported simulator protocol: {config.protocol}")

        self._active_config = config

        # shared persistence sample DB 当前只有 3 个共享 profile items；
        # source_lab 这里验证的是“真实消费输入契约”，不是容量点数规模。
        min_expected_point_count = 1
        max_expected_point_count = max(10_000, config.max_expected_point_count)
        if isinstance(config, SubscribeScanConfig):
            base_source = self._build_source_from_scada_db(
                protocol=protocol,
                access_mode="subscribe",
                min_expected_point_count=1,
                max_expected_point_count=max_expected_point_count,
            )
            base_source = replace(
                base_source,
                points=base_source.points[:max_expected_point_count],
            )
        else:
            base_source = self._build_source_from_scada_db(
                protocol=protocol,
                access_mode="polling",
                min_expected_point_count=min_expected_point_count,
                max_expected_point_count=max_expected_point_count,
            )

        ports = self._port_allocator.allocate_many(server_count, host="127.0.0.1")
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

    def _build_source_from_scada_db(
        self,
        protocol: str,
        *,
        access_mode: str,
        min_expected_point_count: int,
        max_expected_point_count: int,
    ) -> SimulatedSource:
        """从 shared persistence SCADA sample DB 构建指定协议的模拟源。"""

        source = self._profile_provider.load_source(protocol=protocol, access_mode=access_mode)
        point_count = len(source.points)

        if not min_expected_point_count <= point_count <= max_expected_point_count:
            raise AssertionError(
                f"Expected {min_expected_point_count}-{max_expected_point_count} "
                f"profile items per server, got {point_count}"
            )

        params = {
            **dict(source.connection.params),
            "source_lab_original_host": source.connection.host or "",
            "source_lab_original_port": source.connection.port,
        }
        return replace(
            source,
            connection=replace(
                source.connection,
                host="127.0.0.1",
                port=max(1, int(source.connection.port or 1)),
                protocol=protocol,
                params=params,
            ),
        )

    @contextmanager
    def started(self, sources: tuple[SourceRuntimeSpec, ...]) -> Iterator[None]:
        """启动给定 runtime specs 对应的 simulator fleet。"""

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

        # source_lab simulator 的动态更新参数仍在本地 runtime 层注入，不回写 DB。
        protocol = normalize_protocol(self._active_config.protocol)
        update_params: dict[str, str | int | float | bool] = {
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
        # OPC UA runner 使用 address_space 逻辑路径；其他协议优先消费 provider
        # 生成的 locator/address，避免丢失点位级协议寻址信息。
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
                    address=point.locator,
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
