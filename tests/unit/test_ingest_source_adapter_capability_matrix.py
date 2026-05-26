"""Ingest adapter capability matrix guard."""

from __future__ import annotations

import pytest

from whale.ingest.adapters.source.iec104_source_acquisition_adapter import (
    Iec104SourceAcquisitionAdapter,
)
from whale.ingest.adapters.source.iec61850_report_source_acquisition_adapter import (
    Iec61850ReportSourceAcquisitionAdapter,
)
from whale.ingest.adapters.source.iec61850_source_acquisition_adapter import (
    Iec61850MmsSourceAcquisitionAdapter,
)
from whale.ingest.adapters.source.modbus_source_acquisition_adapter import (
    ModbusSourceAcquisitionAdapter,
)
from whale.ingest.adapters.source.opcua_source_acquisition_adapter import (
    OpcUaSourceAcquisitionAdapter,
)
from whale.ingest.adapters.source.static_source_acquisition_port_registry import (
    StaticSourceAcquisitionPortRegistry,
)
from whale.ingest.adapters.source.static_source_write_port_registry import (
    StaticSourceWritePortRegistry,
)
from whale.ingest.adapters.source.iec104_source_write_adapter import Iec104SourceWriteAdapter
from whale.ingest.adapters.source.iec61850_source_write_adapter import Iec61850MmsSourceWriteAdapter
from whale.ingest.adapters.source.modbus_source_write_adapter import ModbusSourceWriteAdapter
from whale.ingest.adapters.source.opcua_source_write_adapter import OpcUaSourceWriteAdapter


def test_acquisition_capability_matrix_no_overclaim() -> None:
    registry = StaticSourceAcquisitionPortRegistry(
        ports_by_protocol={
            "opcua": OpcUaSourceAcquisitionAdapter(),
            "modbus_tcp": ModbusSourceAcquisitionAdapter(),
            "iec104": Iec104SourceAcquisitionAdapter(),
            "iec61850_mms": Iec61850MmsSourceAcquisitionAdapter(),
            "iec61850_report": Iec61850ReportSourceAcquisitionAdapter(),
        }
    )
    for protocol in ("opcua", "modbus_tcp", "iec104", "iec61850_mms", "iec61850_report"):
        assert registry.get(protocol) is not None

    for unsupported in ("iec101", "modbus_rtu", "mqtt", "http_rest", "iec61850_goose", "iec61850_sv"):
        with pytest.raises(ValueError, match="Unsupported acquisition protocol"):
            registry.get(unsupported)


def test_write_capability_matrix_no_overclaim() -> None:
    registry = StaticSourceWritePortRegistry(
        ports_by_protocol={
            "opcua": OpcUaSourceWriteAdapter(),
            "modbus_tcp": ModbusSourceWriteAdapter(),
            "iec104": Iec104SourceWriteAdapter(),
            "iec61850_mms": Iec61850MmsSourceWriteAdapter(),
        }
    )
    for protocol in ("opcua", "modbus_tcp", "iec104", "iec61850_mms"):
        assert registry.get(protocol) is not None

    for unsupported in ("iec101", "modbus_rtu", "mqtt", "http_rest", "iec61850_report", "iec61850_goose", "iec61850_sv"):
        with pytest.raises(ValueError, match="Unsupported write protocol"):
            registry.get(unsupported)
