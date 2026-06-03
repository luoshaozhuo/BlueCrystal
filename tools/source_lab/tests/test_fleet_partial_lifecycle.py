"""Fleet 局部生命周期测试。

验证设备群（fleet）的部分设备启动、停止和状态转换。
测试阶段：开发期验证-L2。
"""
from __future__ import annotations

import random
import socket
import time

from whale.shared.source.access.model import SourceEndpointSpec, SourcePointSpec
from tools.source_lab.access.common.scheduling import RunnerEndpointPlan
from tools.source_lab.access.polling.model import CapacityMode, CapacityScanConfig
from tools.source_lab.access.providers.base import SourceRuntimeSpec
from tools.source_lab.access.runners.modbus_tcp_polling import ModbusTcpPollingRunner
from tools.source_lab.fleet import SourceSimulatorFleet
from tools.source_lab.model import SimulatedPoint, SimulatedSource, SourceConnection, UpdateConfig


def _choose_port() -> int:
    rng = random.SystemRandom()
    for _ in range(100):
        port = rng.randint(43000, 47000)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind(("127.0.0.1", port))
            except OSError:
                continue
            return port
    raise RuntimeError("no available port")


def _build_modbus_source(index: int, port: int) -> SimulatedSource:
    return SimulatedSource(
        connection=SourceConnection(
            name=f"modbus-{index}",
            host="127.0.0.1",
            port=port,
            transport="tcp",
            protocol="modbus_tcp",
            ied_name="",
            ld_name="",
            namespace_uri=None,
        ),
        points=(
            SimulatedPoint(ln_name="holding", do_name="0", unit=None, data_type="INT32"),
            SimulatedPoint(ln_name="holding", do_name="1", unit=None, data_type="INT32"),
        ),
    )


def _runtime_spec(source: SimulatedSource) -> SourceRuntimeSpec:
    return SourceRuntimeSpec(
        endpoint=SourceEndpointSpec(
            name=source.connection.name,
            host=source.connection.host,
            port=source.connection.port,
            protocol=source.connection.protocol,
            transport=source.connection.transport,
            params={"modbus_start_address": 0},
        ),
        points=tuple(
            SourcePointSpec(
                address=point.key,
                name=point.key,
                data_type=point.data_type,
                ln_name=point.ln_name,
                do_name=point.do_name,
                unit=point.unit,
            )
            for point in source.points
        ),
    )


def _read_ok(spec: SourceRuntimeSpec) -> bool:
    runner = ModbusTcpPollingRunner()
    config = CapacityScanConfig(
        mode=CapacityMode.SIMULATOR,
        protocol="modbus_tcp",
        endpoints=(spec.endpoint,),
        points=spec.points,
        server_count_start=1,
        server_count_step=1,
        server_count_max=1,
        hz_start=1.0,
        hz_step=1.0,
        hz_max=1.0,
        process_count=1,
        read_timeout_s=1.0,
        level_duration_s=0.1,
    )
    sample = runner.read_once(
        RunnerEndpointPlan(global_index=0, source=spec, offset_ns=0),
        target_hz=1.0,
        config=config,
    )
    return sample.ok and sample.value_count == len(spec.points)


def test_fleet_stop_one_source_keeps_other_sources_running() -> None:
    sources = (_build_modbus_source(1, _choose_port()), _build_modbus_source(2, _choose_port()))
    specs = tuple(_runtime_spec(source) for source in sources)
    fleet = SourceSimulatorFleet.create(sources, update_config=UpdateConfig(enabled=False))
    try:
        fleet.start()
        time.sleep(0.3)
        assert _read_ok(specs[0]) is True
        assert _read_ok(specs[1]) is True

        fleet.stop_source(0)
        time.sleep(0.2)

        assert fleet.status_source(0) == "stopped"
        assert _read_ok(specs[1]) is True
    finally:
        fleet.stop()


def test_fleet_restart_one_source_keeps_other_sources_running() -> None:
    sources = (_build_modbus_source(1, _choose_port()), _build_modbus_source(2, _choose_port()))
    specs = tuple(_runtime_spec(source) for source in sources)
    fleet = SourceSimulatorFleet.create(sources, update_config=UpdateConfig(enabled=False))
    try:
        fleet.start()
        time.sleep(0.3)

        fleet.restart_source(0)
        time.sleep(0.3)

        assert fleet.status_source(0) == "running"
        assert _read_ok(specs[0]) is True
        assert _read_ok(specs[1]) is True
    finally:
        fleet.stop()


def test_fleet_status_source() -> None:
    source = _build_modbus_source(1, _choose_port())
    fleet = SourceSimulatorFleet.create((source,), update_config=UpdateConfig(enabled=False))
    try:
        assert fleet.status_source(0) == "stopped"
        fleet.start_source(0)
        time.sleep(0.2)
        assert fleet.status_source(0) == "running"
        fleet.stop_source(0)
        assert fleet.status_source(0) == "stopped"
    finally:
        fleet.stop()
