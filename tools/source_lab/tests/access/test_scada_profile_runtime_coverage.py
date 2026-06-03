"""shared profile -> source_lab runtime 覆盖矩阵测试。"""

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
from tools.source_lab.protocols.registry import create_server_simulator
from tools.source_lab.sources import PortAllocator


@dataclass(frozen=True)
class RuntimeCase:
    protocol: str
    access_mode: str
    application_protocol: str
    service_type: str
    runtime_protocol: str | None
    expect_pending: bool = False
    expect_subscribe: bool = False
    expect_report: bool = False
    expect_read: bool = False
    expect_write: bool = False


_RUNTIME_CASES = (
    RuntimeCase("opcua", "polling", "OPC_UA", "READ", "opcua", expect_read=True, expect_write=True),
    RuntimeCase("opcua", "subscribe", "OPC_UA", "SUBSCRIBE", "opcua", expect_read=True, expect_write=True, expect_subscribe=True),
    RuntimeCase("modbus_tcp", "polling", "MODBUS", "TCP_READ", "modbus_tcp", expect_read=True, expect_write=True),
    RuntimeCase("modbus_rtu", "polling", "MODBUS", "RTU_READ", "modbus_rtu", expect_read=True),
    RuntimeCase("iec101", "polling", "IEC101", "INTERROGATION", "iec101", expect_read=True),
    RuntimeCase("iec101", "subscribe", "IEC101", "SPONTANEOUS", "iec101", expect_read=True),
    RuntimeCase("iec104", "polling", "IEC104", "INTERROGATION", "iec104", expect_read=True),
    RuntimeCase("iec104", "subscribe", "IEC104", "SPONTANEOUS", "iec104", expect_read=True),
    RuntimeCase("iec61850_mms", "polling", "IEC61850", "MMS_READ", "iec61850_mms", expect_read=True, expect_write=True),
    RuntimeCase("iec61850_report", "subscribe", "IEC61850", "REPORT", "iec61850_report", expect_subscribe=True, expect_report=True),
    RuntimeCase("iec61850_goose", "subscribe", "IEC61850", "GOOSE", "iec61850_goose", expect_subscribe=True),
    RuntimeCase("iec61850_sv", "subscribe", "IEC61850", "SV", "iec61850_sv", expect_subscribe=True),
    RuntimeCase("mqtt", "subscribe", "MQTT", "SUBSCRIBE", "mqtt", expect_subscribe=True),
    RuntimeCase("http_rest", "polling", "HTTP_REST", "REQUEST", "http_rest", expect_read=True),
    RuntimeCase("beckhoff_ads", "polling", "BECKHOFF_ADS", "ADS_READ_WRITE", "beckhoff_ads", expect_read=True, expect_write=True),
    RuntimeCase("beckhoff_ads", "subscribe", "BECKHOFF_ADS", "ADS_NOTIFICATION", "beckhoff_ads"),
)


def _build_provider(tmp_path: Path) -> ScadaProfileProvider:
    db_path = create_isolated_scada_sample_db(tmp_path)
    return ScadaProfileProvider(db_path=db_path)


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


def test_scada_profile_runtime_matrix_declares_supported_and_pending_sources(tmp_path: Path) -> None:
    """16 组 protocol-service 必须映射到可消费 runtime 或显式 pending。"""

    provider = _build_provider(tmp_path)
    sources = {
        (str(source.connection.application_protocol), str(source.connection.service_type)): source
        for source in provider.list_sources()
    }

    assert len(sources) == 16

    for case in _RUNTIME_CASES:
        source = sources[(case.application_protocol, case.service_type)]
        assert len(source.points) == 3

        runtime_status = str(source.connection.params.get("runtime_status", ""))
        if case.expect_pending:
            assert runtime_status == "pending"
            assert "runtime_reason" in source.connection.params
            with pytest.raises(ValueError, match="unsupported protocol"):
                create_server_simulator(source.connection.protocol, source=source)
            continue

        assert runtime_status == "available"
        assert source.connection.protocol == case.runtime_protocol
        if case.application_protocol == "BECKHOFF_ADS":
            assert source.connection.params.get("backend_kind") == "in_process"

        facade = create_server_simulator(case.runtime_protocol or "", source=None)
        caps = facade.capabilities
        assert caps.read >= case.expect_read
        assert caps.write >= case.expect_write
        assert caps.subscribe >= case.expect_subscribe
        assert caps.report >= case.expect_report


@pytest.mark.parametrize(
    ("protocol", "access_mode"),
    tuple(
        (case.protocol, case.access_mode)
        for case in _RUNTIME_CASES
        if not case.expect_pending
    ),
)
def test_simulator_source_provider_builds_runtime_sources_from_scada_profile(
    tmp_path: Path,
    protocol: str,
    access_mode: str,
) -> None:
    """runtime provider 应把 shared profile source 重写成可本地消费的 simulator source。"""

    profile_provider = _build_provider(tmp_path)
    provider = SimulatorSourceProvider(
        port_allocator=PortAllocator.from_range(start=57000, end=57200),
        profile_provider=profile_provider,
    )
    config = _polling_config(protocol) if access_mode == "polling" else _subscribe_config(protocol)

    runtime_spec = provider.build_sources(config, server_count=1)[0]
    runtime_source = cast(SimulatedSource, runtime_spec.runtime_handle)

    assert runtime_source.connection.host == "127.0.0.1"
    assert int(runtime_source.connection.port or 0) > 0
    assert "source_lab_original_host" in runtime_source.connection.params
    assert "source_lab_original_port" in runtime_source.connection.params
    assert len(runtime_source.points) == 3
    assert all(point.locator for point in runtime_source.points)
