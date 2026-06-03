"""Final source_lab protocol matrix gates for Round 5-5.

These tests guard against overclaiming simulator closure as production
readiness. GOOSE/SV L2 true-pass remains permission-gated by the dedicated
streaming E2E tests.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tools.source_lab.access.runners.registry import PROTOCOL_CAPABILITIES
from tools.source_lab.protocols.common.simulator_models import SimulatorStatus
from tools.source_lab.protocols.registry import (
    create_server_simulator,
    get_server_simulator_capabilities,
)


FINAL_PROTOCOLS = (
    "opcua",
    "modbus_tcp",
    "modbus_rtu",
    "iec101",
    "iec104",
    "iec61850_mms",
    "iec61850_report",
    "iec61850_goose",
    "iec61850_sv",
    "mqtt",
    "http_rest",
)

POLLING_E2E_PROTOCOLS = {
    "modbus_tcp",
    "iec61850_mms",
    "iec104",
    "opcua",
    "iec101",
    "modbus_rtu",
    "http_rest",
}

STREAMING_E2E_PROTOCOLS = {
    "mqtt",
    "opcua",
    "iec61850_report",
    "iec61850_goose",
    "iec61850_sv",
}


def test_final_protocol_capability_matrix_no_overclaim() -> None:
    """Final capability matrix must not overclaim unsupported operations."""
    missing = set(FINAL_PROTOCOLS) - set(PROTOCOL_CAPABILITIES)
    assert not missing, f"missing final protocol capability rows: {sorted(missing)}"

    for protocol in FINAL_PROTOCOLS:
        registry_cap = PROTOCOL_CAPABILITIES[protocol]
        facade_cap = get_server_simulator_capabilities(protocol)

        assert facade_cap.read is bool(registry_cap.get("polling", False)), protocol
        assert facade_cap.write is bool(registry_cap.get("write", False)), protocol
        if protocol in STREAMING_E2E_PROTOCOLS:
            assert facade_cap.subscribe is True, protocol
        elif facade_cap.subscribe:
            assert registry_cap.get("subscribe") is True, protocol

    for protocol in ("iec61850_goose", "iec61850_sv"):
        registry_cap = PROTOCOL_CAPABILITIES[protocol]
        facade_cap = get_server_simulator_capabilities(protocol)
        assert facade_cap.read is False
        assert facade_cap.write is False
        assert facade_cap.subscribe is True
        assert facade_cap.report is False
        assert facade_cap.update_values is True
        assert registry_cap["transport"] == "ETHERNET_L2"
        assert registry_cap["production_client_subscribe"] is False
        assert "CAP_NET_RAW" in str(registry_cap["limitation"])

    mqtt_cap = get_server_simulator_capabilities("mqtt")
    assert mqtt_cap.read is False
    assert mqtt_cap.write is False
    assert mqtt_cap.subscribe is True
    assert PROTOCOL_CAPABILITIES["mqtt"]["production_client_write"] is False

    http_cap = get_server_simulator_capabilities("http_rest")
    assert http_cap.read is True
    assert http_cap.write is False
    assert http_cap.subscribe is False
    assert PROTOCOL_CAPABILITIES["http_rest"]["production_client_write"] is False

    assert "not_implemented" in str(PROTOCOL_CAPABILITIES["modbus_rtu"]["write_limitation"]).lower()
    assert "not_implemented" in str(PROTOCOL_CAPABILITIES["iec101"]["write_limitation"]).lower()


def test_supported_capabilities_have_tests() -> None:
    """Supported polling/streaming capabilities must have smoke or E2E gates."""
    test_dir = Path(__file__).resolve().parent
    evidence_files = {
        "polling": (
            test_dir / "test_server_simulator_facade_capacity_profile_e2e.py",
            test_dir / "test_server_simulator_facade_real_protocol_smoke.py",
        ),
        "streaming": (
            test_dir / "test_server_simulator_facade_capacity_profile_e2e.py",
            test_dir / "test_iec61850_goose_sv_streaming_e2e.py",
        ),
    }
    for files in evidence_files.values():
        for file in files:
            assert file.exists(), f"missing evidence test file: {file}"

    for protocol in POLLING_E2E_PROTOCOLS:
        cap = PROTOCOL_CAPABILITIES[protocol]
        assert cap.get("polling") is True, f"{protocol}: polling E2E without capability"

    for protocol in STREAMING_E2E_PROTOCOLS:
        cap = PROTOCOL_CAPABILITIES[protocol]
        assert cap.get("subscribe") is True, f"{protocol}: streaming E2E without capability"


@pytest.mark.asyncio
async def test_not_implemented_boundaries() -> None:
    """Unsupported final-matrix operations must return NOT_IMPLEMENTED."""
    for protocol in ("iec61850_goose", "iec61850_sv"):
        facade = create_server_simulator(protocol, source=None)
        assert (await facade.read([])).status is SimulatorStatus.NOT_IMPLEMENTED
        assert (await facade.write({})).status is SimulatorStatus.NOT_IMPLEMENTED
        assert (await facade.report([])).status is SimulatorStatus.NOT_IMPLEMENTED

    mqtt = create_server_simulator("mqtt", source=None)
    assert (await mqtt.read([])).status is SimulatorStatus.NOT_IMPLEMENTED
    assert (await mqtt.write({})).status is SimulatorStatus.NOT_IMPLEMENTED
    assert (await mqtt.report([])).status is SimulatorStatus.NOT_IMPLEMENTED

    http_rest = create_server_simulator("http_rest", source=None)
    assert (await http_rest.write({})).status is SimulatorStatus.NOT_IMPLEMENTED
    assert (await http_rest.subscribe([])).status is SimulatorStatus.NOT_IMPLEMENTED
    assert (await http_rest.report([])).status is SimulatorStatus.NOT_IMPLEMENTED
