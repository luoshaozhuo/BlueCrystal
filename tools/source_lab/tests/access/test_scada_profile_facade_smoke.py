"""shared profile -> runtime -> facade 最小 smoke。"""

from __future__ import annotations

from dataclasses import dataclass
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


@dataclass(frozen=True)
class SmokeCase:
    protocol: str
    access_mode: str
    expected_load: tuple[SimulatorStatus, ...]
    expected_start: tuple[SimulatorStatus, ...]
    start_boundary: str = ""
    expect_read: bool = False
    expect_write: bool = False
    expect_subscribe: bool = False
    expect_report: bool = False
    boundary_statuses: tuple[SimulatorStatus, ...] = ()
    boundary_message: str = ""
    explicit_not_implemented: bool = False


_SMOKE_CASES = (
    SmokeCase("opcua", "polling", (SimulatorStatus.OK,), (SimulatorStatus.OK, SimulatorStatus.ERROR), "open62541", expect_read=True, expect_write=True),
    SmokeCase("modbus_tcp", "polling", (SimulatorStatus.OK,), (SimulatorStatus.OK,), expect_read=True, expect_write=True),
    SmokeCase("modbus_rtu", "polling", (SimulatorStatus.OK,), (SimulatorStatus.OK,), expect_read=True),
    SmokeCase("iec101", "polling", (SimulatorStatus.OK,), (SimulatorStatus.OK,), expect_read=True),
    SmokeCase("iec104", "polling", (SimulatorStatus.OK,), (SimulatorStatus.OK,), expect_read=True, boundary_statuses=(SimulatorStatus.ERROR, SimulatorStatus.NOT_IMPLEMENTED), boundary_message="iec104"),
    SmokeCase("iec61850_mms", "polling", (SimulatorStatus.OK,), (SimulatorStatus.OK,), expect_read=True, expect_write=True),
    SmokeCase("http_rest", "polling", (SimulatorStatus.OK,), (SimulatorStatus.OK,), expect_read=True),
    SmokeCase("beckhoff_ads", "polling", (SimulatorStatus.OK,), (SimulatorStatus.OK,), expect_read=True, expect_write=True),
    SmokeCase("opcua", "subscribe", (SimulatorStatus.OK,), (SimulatorStatus.OK, SimulatorStatus.ERROR), "open62541", expect_subscribe=True),
    SmokeCase("iec104", "subscribe", (SimulatorStatus.OK,), (SimulatorStatus.OK,), explicit_not_implemented=True),
    SmokeCase("iec61850_report", "subscribe", (SimulatorStatus.OK,), (SimulatorStatus.OK,), expect_subscribe=True, expect_report=True, boundary_statuses=(SimulatorStatus.ERROR, SimulatorStatus.UNAVAILABLE, SimulatorStatus.NOT_IMPLEMENTED), boundary_message="report"),
    SmokeCase("iec61850_goose", "subscribe", (SimulatorStatus.NOT_IMPLEMENTED,), (SimulatorStatus.OK,), expect_subscribe=True, boundary_statuses=(SimulatorStatus.UNAVAILABLE,), boundary_message="GOOSE"),
    SmokeCase("iec61850_sv", "subscribe", (SimulatorStatus.NOT_IMPLEMENTED,), (SimulatorStatus.OK,), expect_subscribe=True, boundary_statuses=(SimulatorStatus.UNAVAILABLE,), boundary_message="SV"),
    SmokeCase("mqtt", "subscribe", (SimulatorStatus.OK,), (SimulatorStatus.OK,), expect_subscribe=True),
    SmokeCase("beckhoff_ads", "subscribe", (SimulatorStatus.OK,), (SimulatorStatus.OK,), explicit_not_implemented=True),
)


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


def _build_runtime_source(tmp_path: Path, protocol: str, access_mode: str) -> SimulatedSource:
    db_path = create_isolated_scada_sample_db(tmp_path)
    profile_provider = ScadaProfileProvider(db_path=db_path)
    provider = SimulatorSourceProvider(
        port_allocator=PortAllocator.from_range(start=58000, end=58200),
        profile_provider=profile_provider,
    )
    config = _polling_config(protocol) if access_mode == "polling" else _subscribe_config(protocol)
    return cast(SimulatedSource, provider.build_sources(config, server_count=1)[0].runtime_handle)


def _assert_boundary_message(message: str, expected: str) -> None:
    assert message
    assert expected.lower() in message.lower()


@pytest.mark.asyncio
@pytest.mark.parametrize("case", _SMOKE_CASES, ids=lambda case: f"{case.protocol}-{case.access_mode}")
async def test_scada_profile_runtime_facade_smoke(tmp_path: Path, case: SmokeCase) -> None:
    """runtime source 应能被 facade 真实消费，或返回显式不可用边界。"""

    runtime_source = _build_runtime_source(tmp_path, case.protocol, case.access_mode)
    facade = create_server_simulator(case.protocol, source=runtime_source)
    point_keys = [point.key for point in runtime_source.points]

    load_result = await facade.load_points([])
    assert load_result.status in case.expected_load

    started = await facade.start()
    assert started.status in case.expected_start
    if started.status is not SimulatorStatus.OK:
        _assert_boundary_message(started.message, case.start_boundary)
        stopped = await facade.stop()
        assert stopped.status in (SimulatorStatus.OK, SimulatorStatus.NOT_RUNNING)
        return

    try:
        health = await facade.health()
        assert health.status == SimulatorStatus.OK

        if case.explicit_not_implemented:
            subscribe_result = await facade.subscribe(point_keys)
            report_result = await facade.report(point_keys)
            assert subscribe_result.status == SimulatorStatus.NOT_IMPLEMENTED
            assert report_result.status == SimulatorStatus.NOT_IMPLEMENTED
            return

        if case.expect_read:
            read_result = await facade.read(point_keys[:2])
            if read_result.status not in (SimulatorStatus.OK, SimulatorStatus.PARTIAL_SUCCESS):
                assert read_result.status in case.boundary_statuses
                _assert_boundary_message(read_result.message, case.boundary_message)
            else:
                assert isinstance(read_result.values, dict)

        if case.expect_write:
            write_result = await facade.write({point_keys[0]: runtime_source.points[0].initial_value})
            if write_result.status is not SimulatorStatus.OK:
                assert write_result.status in (SimulatorStatus.NOT_IMPLEMENTED, *case.boundary_statuses)
                assert write_result.message

        if case.expect_subscribe:
            subscribe_result = await facade.subscribe(point_keys[:2])
            if subscribe_result.status is not SimulatorStatus.OK:
                assert subscribe_result.status in case.boundary_statuses
                _assert_boundary_message(subscribe_result.message, case.boundary_message)

        if case.expect_report:
            report_result = await facade.report(point_keys[:2])
            assert report_result.status in (
                SimulatorStatus.OK,
                SimulatorStatus.NOT_RUNNING,
                SimulatorStatus.NOT_IMPLEMENTED,
            )
    finally:
        stopped = await facade.stop()
        assert stopped.status == SimulatorStatus.OK
