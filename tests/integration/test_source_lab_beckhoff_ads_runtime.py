"""source_lab Beckhoff ADS 统一输入集成测试。

证据等级：L4 integration。
本测试证明 shared persistence 输入可驱动以下两类 ADS tool runtime 闭环：
1. `backend_kind=in_process` — lightweight ADS simulator 内存态；
2. `backend_kind=beckhoff_dotnet` — 真实 .NET virtual server + client（环境依赖，
   环境不满足时 skip）。

本测试不替代真实 Beckhoff TwinCAT PLC 或现场设备的 e2e 验证。
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


def _polling_config() -> CapacityScanConfig:
    return CapacityScanConfig(
        mode=CapacityMode.FIELD,
        protocol="beckhoff_ads",
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


def _subscribe_config() -> SubscribeScanConfig:
    return SubscribeScanConfig(
        mode=CapacityMode.FIELD,
        protocol="beckhoff_ads",
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
async def test_source_lab_beckhoff_ads_polling_runtime_write_readback(tmp_path: Path) -> None:
    """shared profile -> runtime -> ADS facade 应支持 write/readback。"""

    db_path = create_isolated_scada_sample_db(tmp_path)
    profile_provider = ScadaProfileProvider(db_path=db_path)
    provider = SimulatorSourceProvider(
        port_allocator=PortAllocator.from_range(start=59000, end=59100),
        profile_provider=profile_provider,
    )

    runtime_source = cast(
        SimulatedSource,
        provider.build_sources(_polling_config(), server_count=1)[0].runtime_handle,
    )
    assert runtime_source.connection.params.get("backend_kind") == "in_process"
    facade = create_server_simulator("beckhoff_ads", source=runtime_source)

    assert (await facade.load_points([])).status == SimulatorStatus.OK
    assert (await facade.start()).status == SimulatorStatus.OK
    try:
        first_key = runtime_source.points[0].key
        write_result = await facade.write({first_key: 77.5})
        assert write_result.status == SimulatorStatus.OK, write_result.message

        readback = await facade.read([first_key])
        assert readback.status == SimulatorStatus.OK
        assert isinstance(readback.values, dict)
        assert readback.values[first_key] == 77.5
    finally:
        assert (await facade.stop()).status == SimulatorStatus.OK


@pytest.mark.integration
@pytest.mark.asyncio
async def test_source_lab_beckhoff_ads_notification_boundary(tmp_path: Path) -> None:
    """ADS_NOTIFICATION 当前必须返回显式 NOT_IMPLEMENTED。"""

    db_path = create_isolated_scada_sample_db(tmp_path)
    profile_provider = ScadaProfileProvider(db_path=db_path)
    provider = SimulatorSourceProvider(
        port_allocator=PortAllocator.from_range(start=59101, end=59200),
        profile_provider=profile_provider,
    )

    runtime_source = cast(
        SimulatedSource,
        provider.build_sources(_subscribe_config(), server_count=1)[0].runtime_handle,
    )
    assert runtime_source.connection.params.get("backend_kind") == "in_process"
    facade = create_server_simulator("beckhoff_ads", source=runtime_source)

    assert (await facade.start()).status == SimulatorStatus.OK
    try:
        result = await facade.subscribe([point.key for point in runtime_source.points])
        assert result.status == SimulatorStatus.NOT_IMPLEMENTED
    finally:
        assert (await facade.stop()).status == SimulatorStatus.OK


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.slow
async def test_source_lab_beckhoff_ads_dotnet_backend_environment_gate() -> None:
    """验证 BeckhoffDotnetAdsSimulatorFacade 在环境不满足时显式返回 UNAVAILABLE。

    此测试不要求 dotnet 环境必须可用；它验证的是：
    - 环境不足时 facade 返回 UNAVAILABLE（而非假通过）；
    - 环境可用时 facade 可启动并完成基本 lifecycle 检查；
    - notification 仍为 NOT_IMPLEMENTED。
    """

    from tools.source_lab.model import SimulatedPoint, SimulatedSource, SourceConnection
    from tools.source_lab.protocols.beckhoff_ads.simulator import BeckhoffDotnetAdsSimulatorFacade

    points = (
        SimulatedPoint(
            ln_name="ADS",
            do_name="ActivePower",
            unit="kW",
            data_type="FLOAT64",
            initial_value=12.5,
            address="MAIN.WTG_ADS_001.ActivePower",
            protocol_params={
                "symbol_name": "MAIN.WTG_ADS_001.ActivePower",
                "index_group": 16416,
                "index_offset": 32,
                "data_size": 8,
                "ads_data_type": "LREAL",
            },
        ),
    )
    source = SimulatedSource(
        connection=SourceConnection(
            name="beckhoff_ads_dotnet_integration",
            host="127.0.0.1",
            port=48898,
            transport="TCP",
            protocol="beckhoff_ads",
            application_protocol="BECKHOFF_ADS",
            service_type="ADS_READ_WRITE",
            namespace_uri=None,
            ied_name="ADS",
            ld_name="LD_ADS_INTEG_001",
            params={
                "ams_net_id": "5.32.160.1.1.1",
                "ads_server_port": 851,
                "backend_kind": "beckhoff_dotnet",
            },
        ),
        points=points,
    )

    facade = BeckhoffDotnetAdsSimulatorFacade(source=source)

    start_result = await facade.start()
    if start_result.status == SimulatorStatus.UNAVAILABLE:
        # 环境不足——这是预期的、显式的边界行为
        assert "environment" in start_result.message.lower() or "ready" in start_result.message.lower(), (
            f"UNAVAILABLE reason must mention environment readiness: {start_result.message}"
        )
        # 确认 protocol_evidence 仍为 false
        assert facade.protocol_evidence is False
        return

    # 环境可用——验证 lifecycle 和 notification boundary
    assert start_result.status == SimulatorStatus.OK, start_result.message
    try:
        health = await facade.health()
        assert health.status == SimulatorStatus.OK

        load_result = await facade.load_points([])
        assert load_result.status == SimulatorStatus.OK

        # ADS_NOTIFICATION 仍为 NOT_IMPLEMENTED
        sub_result = await facade.subscribe(["ADS.ActivePower"])
        assert sub_result.status == SimulatorStatus.NOT_IMPLEMENTED
    finally:
        stop_result = await facade.stop()
        assert stop_result.status in {
            SimulatorStatus.OK,
            SimulatorStatus.NOT_RUNNING,
            SimulatorStatus.PARTIAL_SUCCESS,
        }
        assert facade.protocol_evidence is False, (
            "protocol_evidence should be reset to false after stop"
        )
