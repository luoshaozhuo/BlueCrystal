"""Tests for source_lab simulator factory."""

from __future__ import annotations

import pytest

from tools.source_lab.opcua.open62541_source_simulator import (
    Open62541SourceSimulator,
)
from tools.source_lab.factory import build_simulator
from tools.source_lab.model import SimulatedPoint, SimulatedSource, SourceConnection


def _build_source(protocol: str = "opcua") -> SimulatedSource:
    """Build minimal simulated source for factory tests."""
    return SimulatedSource(
        connection=SourceConnection(
            name="source_001",
            ied_name="IED001",
            ld_name="LD0",
            host="127.0.0.1",
            port=4840,
            transport="tcp",
            protocol=protocol,
            namespace_uri="urn:whale:test",
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


def test_build_simulator_uses_open62541_backend_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    """OPC UA simulator construction is fixed to open62541."""
    monkeypatch.delenv("SOURCE_SIM_LOAD_SOURCE_UPDATE_ENABLED", raising=False)

    simulator = build_simulator(_build_source())

    assert isinstance(simulator, Open62541SourceSimulator)


def test_build_simulator_returns_open62541_for_opcua_sources() -> None:
    simulator = build_simulator(_build_source())

    assert type(simulator) is Open62541SourceSimulator


def test_build_simulator_rejects_unknown_protocol(monkeypatch: pytest.MonkeyPatch) -> None:
    """Unknown protocol should fail fast."""
    monkeypatch.delenv("SOURCE_SIM_LOAD_SOURCE_UPDATE_ENABLED", raising=False)
    with pytest.raises(ValueError, match="Unsupported source simulator type"):
        build_simulator(_build_source(protocol="modbus"))
