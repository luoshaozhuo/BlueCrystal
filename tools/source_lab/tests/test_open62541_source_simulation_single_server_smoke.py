"""Smoke test for open62541 OPC UA source simulator backend."""

from __future__ import annotations

import asyncio
from dataclasses import replace
import random
import socket
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_SRC_ROOT = _PROJECT_ROOT / "src"
for _path in (str(_PROJECT_ROOT), str(_SRC_ROOT)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

import pytest

from whale.shared.source.access import SourceEndpointSpec, SourcePointSpec, build_source_access_adapter
from whale.shared.source.access.model import TickResult
from tools.source_lab.protocols.opcua.address_space import logical_path
from tools.source_lab.protocols.opcua.open62541_source_simulator import (
    Open62541SourceSimulator,
    resolve_runner_path,
)
from tools.source_lab.model import (
    SimulatedPoint,
    SimulatedSource,
    SourceConnection,
    UpdateConfig,
)
from tools.source_lab.fleet import SourceSimulatorFleet


def _choose_available_port(
    *,
    host: str = "127.0.0.1",
    minimum_port: int = 40001,
    maximum_port: int = 59999,
) -> int:
    rng = random.SystemRandom()
    tried: set[int] = set()
    while True:
        candidate = rng.randint(minimum_port, maximum_port)
        if candidate in tried:
            continue
        tried.add(candidate)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind((host, candidate))
            except OSError:
                if len(tried) >= maximum_port - minimum_port + 1:
                    raise RuntimeError("No available TCP ports found")
                continue
            return candidate


def _build_source() -> SimulatedSource:
    port = _choose_available_port()
    return SimulatedSource(
        connection=SourceConnection(
            name="open62541_smoke_source",
            ied_name="IED001",
            ld_name="LD0",
            host="127.0.0.1",
            port=port,
            transport="tcp",
            protocol="opcua",
            namespace_uri="urn:whale:open62541:smoke",
        ),
        points=(
            SimulatedPoint(ln_name="WPPD1", do_name="TotW", unit="kW", data_type="FLOAT64", initial_value=12.5),
            SimulatedPoint(ln_name="WPPD1", do_name="DevSt", unit=None, data_type="BOOLEAN", initial_value=True),
            SimulatedPoint(ln_name="WPPD1", do_name="OpCnt", unit=None, data_type="INT32", initial_value=7),
            SimulatedPoint(
                ln_name="WPPD1",
                do_name="StrVal",
                unit=None,
                data_type="STRING",
                initial_value="initial",
            ),
        ),
    )


async def _read_tick(source: SimulatedSource) -> TickResult:
    endpoint = SourceEndpointSpec(
        name=source.connection.name,
        host=source.connection.host,
        port=source.connection.port,
        protocol="opcua",
        transport=source.connection.transport,
        namespace_uri=source.connection.namespace_uri,
        ied_name=source.connection.ied_name,
        ld_name=source.connection.ld_name,
    )
    points = tuple(
        SourcePointSpec(
            address=logical_path(source.connection, point),
            name=point.key,
            data_type=point.data_type,
        )
        for point in source.points
    )
    adapter = build_source_access_adapter(
        "opcua",
        endpoint,
        points,
        read_timeout_s=4.0,
    )
    await adapter.connect()
    try:
        await adapter.prepare_read()
        return await adapter.read_tick(expected_value_count=len(points))
    finally:
        await adapter.close()


def _assert_tick_ok(tick: TickResult, *, expected_count: int) -> None:
    assert tick.ok
    assert tick.value_count == expected_count
    assert tick.response_timestamp_s is not None


def _require_runner() -> None:
    runner_path = resolve_runner_path()
    if not runner_path.exists():
        pytest.skip(
            "open62541 runner executable does not exist. "
            "Build it with CMake before running this smoke test."
        )


@pytest.mark.load
def test_open62541_source_simulation_single_server_smoke(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _require_runner()
    monkeypatch.setenv("SOURCE_SIM_POLL_SOURCE_UPDATE_ENABLED", "false")

    source = _build_source()
    fleet = SourceSimulatorFleet.create(
        sources=(source,),
        update_config=UpdateConfig(enabled=False, interval_seconds=1.0, update_count=len(source.points)),
    )

    with fleet:
        tick = asyncio.run(_read_tick(source))

    _assert_tick_ok(tick, expected_count=len(source.points))


@pytest.mark.load
def test_open62541_source_simulator_writes_smoke(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _require_runner()
    monkeypatch.setenv("SOURCE_SIM_POLL_SOURCE_UPDATE_ENABLED", "false")
    source = _build_source()

    with Open62541SourceSimulator(source) as simulator:
        assert simulator.protocol_noise_count == 0
        assert simulator.protocol_noise_samples == ()
        _assert_tick_ok(asyncio.run(_read_tick(source)), expected_count=len(source.points))
        simulator.writes(
            {
                "WPPD1.TotW": 88.5,
                "WPPD1.OpCnt": 42,
                "WPPD1.DevSt": False,
                "WPPD1.StrVal": "updated",
            }
        )
        asyncio.run(asyncio.sleep(0.1))
        _assert_tick_ok(asyncio.run(_read_tick(source)), expected_count=len(source.points))


@pytest.mark.load
def test_open62541_source_simulator_rejects_invalid_write_string(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _require_runner()
    monkeypatch.setenv("SOURCE_SIM_POLL_SOURCE_UPDATE_ENABLED", "false")
    source = _build_source()

    with Open62541SourceSimulator(source) as simulator:
        with pytest.raises(ValueError, match="unsupported control character"):
            simulator.writes({"WPPD1.StrVal": "bad\tvalue"})


def test_open62541_source_simulator_prefers_runtime_update_params() -> None:
    source = _build_source()
    source = replace(
        source,
        connection=replace(
            source.connection,
            params={
                **source.connection.params,
                "open62541_internal_update_enabled": True,
                "open62541_internal_update_interval_ms": 50,
            },
        ),
    )
    simulator = Open62541SourceSimulator(source)

    assert simulator._runner_config_records()["update_enabled"] == "true"
    assert simulator._runner_config_records()["update_interval_ms"] == "50"


@pytest.mark.load
def test_open62541_source_simulator_internal_updates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _require_runner()
    monkeypatch.setenv("SOURCE_SIM_POLL_SOURCE_UPDATE_ENABLED", "true")
    monkeypatch.setenv("SOURCE_SIM_POLL_SOURCE_UPDATE_HZ", "10")
    source = _build_source()

    with Open62541SourceSimulator(source):
        # stdout is a control/protocol channel; startup should be noise-free.
        initial_tick = asyncio.run(_read_tick(source))
        asyncio.run(asyncio.sleep(0.3))
        updated_tick = asyncio.run(_read_tick(source))

    _assert_tick_ok(initial_tick, expected_count=len(source.points))
    _assert_tick_ok(updated_tick, expected_count=len(source.points))


@pytest.mark.load
def test_open62541_fleet_internal_updates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _require_runner()
    monkeypatch.setenv("SOURCE_SIM_POLL_SOURCE_UPDATE_ENABLED", "true")
    monkeypatch.setenv("SOURCE_SIM_POLL_SOURCE_UPDATE_HZ", "10")

    source = _build_source()
    fleet = SourceSimulatorFleet.create(
        sources=(source,),
        update_config=UpdateConfig(enabled=True, interval_seconds=0.1, update_count=4),
    )

    with fleet:
        initial_tick = asyncio.run(_read_tick(source))
        asyncio.run(asyncio.sleep(0.3))
        updated_tick = asyncio.run(_read_tick(source))

    _assert_tick_ok(initial_tick, expected_count=len(source.points))
    _assert_tick_ok(updated_tick, expected_count=len(source.points))
