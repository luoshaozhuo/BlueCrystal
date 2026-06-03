"""source_lab 消费 shared persistence SCADA sample DB 的集成测试。

测试阶段：跨模块联调期验证 (integration)。
本测试通过真实 sample SQLite -> `ScadaProfileProvider` -> `SimulatorSourceProvider`
-> `ServerSimulatorFacade` 验证 source_lab 已不再手工拼装样例，而是实际消费
shared persistence 输入基线。它不证明 native runner 或现场设备环境已就绪。
"""

from __future__ import annotations

from pathlib import Path
from typing import cast

import pytest

from tests.support.scada_sample_db import create_isolated_scada_sample_db
from tools.source_lab.access.polling.model import CapacityMode, CapacityScanConfig
from tools.source_lab.access.providers.scada_profile import ScadaProfileProvider
from tools.source_lab.access.providers.simulator import SimulatorSourceProvider
from tools.source_lab.access.subscribe.model import SubscribeScanConfig
from tools.source_lab.model import SimulatedSource
from tools.source_lab.protocols.common.simulator_models import SimulatorStatus
from tools.source_lab.protocols.registry import create_server_simulator
from tools.source_lab.sources import PortAllocator


def _polling_config(protocol: str) -> CapacityScanConfig:
    return CapacityScanConfig(
        mode=CapacityMode.FIELD,
        protocol=protocol,
        endpoints=(),
        points=(),
        server_count_start=1,
        server_count_step=1,
        server_count_max=1,
        hz_start=1.0,
        hz_step=1.0,
        hz_max=1.0,
        process_count=1,
        progress_enabled=False,
    )


def _subscribe_config(protocol: str) -> SubscribeScanConfig:
    return SubscribeScanConfig(
        mode=CapacityMode.FIELD,
        protocol=protocol,
        server_count_start=1,
        server_count_step=1,
        server_count_max=1,
        process_count=1,
        publishing_interval_ms=1000.0,
        sampling_interval_ms=1000.0,
        nominal_sample_hz=1.0,
        queue_size=1,
        progress_enabled=False,
    )


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("protocol", "access_mode"),
    (
        ("http_rest", "polling"),
        ("mqtt", "subscribe"),
    ),
)
async def test_source_lab_simulator_facade_consumes_scada_sample_db_sources(
    tmp_path: Path,
    protocol: str,
    access_mode: str,
) -> None:
    """代表性 facade 应能直接消费从 shared persistence DB 转出的 source。"""

    db_path = create_isolated_scada_sample_db(tmp_path)
    profile_provider = ScadaProfileProvider(db_path=db_path)
    provider = SimulatorSourceProvider(
        port_allocator=PortAllocator.from_range(start=54000, end=54100),
        profile_provider=profile_provider,
    )

    config = _polling_config(protocol) if access_mode == "polling" else _subscribe_config(protocol)
    runtime_specs = provider.build_sources(config, server_count=1)
    runtime_source = cast(SimulatedSource, runtime_specs[0].runtime_handle)

    facade = create_server_simulator(protocol, source=runtime_source)
    load_result = await facade.load_points([])
    assert load_result.status == SimulatorStatus.OK, load_result.message
    started = await facade.start()
    assert started.status == SimulatorStatus.OK, started.message

    try:
        health = await facade.health()
        assert health.status == SimulatorStatus.OK

        if access_mode == "subscribe":
            point_keys = [point.key for point in runtime_source.points]
            subscribe_result = await facade.subscribe(point_keys)
            assert subscribe_result.status == SimulatorStatus.OK, subscribe_result.message
    finally:
        stopped = await facade.stop()
        assert stopped.status == SimulatorStatus.OK
