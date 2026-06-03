"""Beckhoff ADS simulator facade 合同测试。

测试阶段：模块集成期验证 (simulator)。
本测试只验证 `backend_kind=in_process` 的 source_lab lightweight ADS tool runtime，
不证明真实 Beckhoff ADS 协议服务端。
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from tools.source_lab.model import SimulatedPoint, SimulatedSource, SourceConnection
from tools.source_lab.protocols.common.simulator_models import SimulatorStatus
from tools.source_lab.protocols.registry import create_server_simulator


def _build_ads_source() -> SimulatedSource:
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
        SimulatedPoint(
            ln_name="ADS",
            do_name="LocalState",
            unit=None,
            data_type="BOOLEAN",
            initial_value=True,
            address="MAIN.WTG_ADS_001.LocalState",
            protocol_params={
                "symbol_name": "MAIN.WTG_ADS_001.LocalState",
                "index_group": 16416,
                "index_offset": 40,
                "data_size": 1,
                "ads_data_type": "BOOL",
            },
        ),
    )
    return SimulatedSource(
        connection=SourceConnection(
            name="beckhoff_ads_smoke",
            host="127.0.0.1",
            port=58898,
            transport="TCP",
            protocol="beckhoff_ads",
            application_protocol="BECKHOFF_ADS",
            service_type="ADS_READ_WRITE",
            namespace_uri=None,
            ied_name="ADS",
            ld_name="LD_ADS_001",
            params={
                "ams_net_id": "5.32.160.1.1.1",
                "ads_router_port": 58898,
                "ads_server_port": 851,
                "request_timeout_ms": 1000,
            },
        ),
        points=points,
    )


@pytest.mark.asyncio
async def test_beckhoff_ads_facade_lifecycle_read_write_and_readback() -> None:
    """ADS facade 应支持 start/health/read/write/readback/update_values/stop。"""

    source = _build_ads_source()
    facade = create_server_simulator("beckhoff_ads", source)

    assert (await facade.load_points([])).status == SimulatorStatus.OK
    assert (await facade.start()).status == SimulatorStatus.OK

    try:
        health = await facade.health()
        assert health.status == SimulatorStatus.OK
        assert health.points_count == 2

        before = await facade.read(["ADS.ActivePower", "ADS.LocalState"])
        assert before.status == SimulatorStatus.OK
        assert isinstance(before.values, dict)
        assert before.values["ADS.ActivePower"] == 12.5
        assert before.values["ADS.LocalState"] is True

        write_result = await facade.write({"ADS.ActivePower": 33.5, "ADS.LocalState": False})
        assert write_result.status == SimulatorStatus.OK

        after = await facade.read(["ADS.ActivePower", "ADS.LocalState"])
        assert after.status == SimulatorStatus.OK
        assert isinstance(after.values, dict)
        assert after.values["ADS.ActivePower"] == 33.5
        assert after.values["ADS.LocalState"] is False

        update = await facade.update_values({"ADS.ActivePower": 41.0})
        assert update.status == SimulatorStatus.OK
        updated = await facade.read(["ADS.ActivePower"])
        assert isinstance(updated.values, dict)
        assert updated.values["ADS.ActivePower"] == 41.0
    finally:
        assert (await facade.stop()).status == SimulatorStatus.OK


@pytest.mark.asyncio
async def test_beckhoff_ads_notification_boundaries_are_explicit() -> None:
    """ADS notification 路径未完成时必须明确 NOT_IMPLEMENTED。"""

    source = replace(_build_ads_source(), connection=replace(_build_ads_source().connection, service_type="ADS_NOTIFICATION"))
    facade = create_server_simulator("beckhoff_ads", source)
    assert (await facade.start()).status == SimulatorStatus.OK
    try:
        subscribe = await facade.subscribe(["ADS.ActivePower"])
        report = await facade.report(["ADS.ActivePower"])
        assert subscribe.status == SimulatorStatus.NOT_IMPLEMENTED
        assert report.status == SimulatorStatus.NOT_IMPLEMENTED
    finally:
        assert (await facade.stop()).status == SimulatorStatus.OK


@pytest.mark.asyncio
async def test_beckhoff_ads_invalid_size_and_address_are_rejected() -> None:
    """非法 size / index_group / index_offset 必须显式失败。"""

    bad_size_source = _build_ads_source()
    bad_size_source.points[0].protocol_params["data_size"] = 4
    bad_size_facade = create_server_simulator("beckhoff_ads", bad_size_source)
    bad_size_result = await bad_size_facade.load_points([])
    assert bad_size_result.status == SimulatorStatus.BAD_REQUEST
    assert "data_size" in bad_size_result.message

    bad_addr_source = _build_ads_source()
    bad_addr_source.points[0].protocol_params["index_group"] = -1
    bad_addr_facade = create_server_simulator("beckhoff_ads", bad_addr_source)
    bad_addr_result = await bad_addr_facade.start()
    assert bad_addr_result.status == SimulatorStatus.BAD_REQUEST
    assert "index_group" in bad_addr_result.message


@pytest.mark.asyncio
async def test_beckhoff_ads_missing_point_and_cleanup_boundaries() -> None:
    """未知点位与 cleanup 后读取都要返回显式边界。"""

    source = _build_ads_source()
    facade = create_server_simulator("beckhoff_ads", source)
    assert (await facade.start()).status == SimulatorStatus.OK

    missing = await facade.write({"ADS.Unknown": 1})
    assert missing.status == SimulatorStatus.BAD_REQUEST
    assert "point not found" in missing.message

    assert (await facade.stop()).status == SimulatorStatus.OK
    stopped_read = await facade.read(["ADS.ActivePower"])
    assert stopped_read.status == SimulatorStatus.NOT_RUNNING
