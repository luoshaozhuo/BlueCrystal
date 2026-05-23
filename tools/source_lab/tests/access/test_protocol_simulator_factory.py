"""Protocol simulator factory tests."""

from __future__ import annotations

import socket

from tools.source_lab.factory import build_simulator
from tools.source_lab.model import SimulatedPoint, SimulatedSource, SourceConnection


def _free_tcp_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _simulated_source(protocol: str) -> SimulatedSource:
    return SimulatedSource(
        connection=SourceConnection(
            name=f"src-{protocol}",
            ied_name="IED1",
            ld_name="LD0",
            host="127.0.0.1",
            port=_free_tcp_port(),
            transport="tcp",
            protocol=protocol,
            params={"base_path": "/points"},
        ),
        points=(
            SimulatedPoint(
                ln_name="WPPD1",
                do_name="TotW",
                unit="kW",
                data_type="FLOAT64",
                initial_value=1.0,
            ),
        ),
    )


def test_non_opcua_protocol_simulators_can_be_built_and_lifecycle_started() -> None:
    """All non-OPCUA protocols should map to concrete simulator backends."""

    protocols = (
        "modbus_tcp",
        "modbus_rtu",
        "iec101",
        "iec104",
        "iec61850_mms",
        "iec61850_report",
        "mqtt",
        "http_rest",
    )

    for protocol in protocols:
        simulator = build_simulator(_simulated_source(protocol))
        simulator.start()
        simulator.writes({"WPPD1.TotW": 2.0})
        simulator.stop()
