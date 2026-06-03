"""source_lab 消费 PostgreSQL shared persistence 样例库的集成测试。

测试阶段：跨模块联调期验证 (integration)。
本测试通过真实 PostgreSQL 临时样例库验证 `ScadaProfileProvider` 已经可以直接
消费 shared persistence 输入基线，并保留 ADS lightweight runtime 的显式边界。
它不证明 Beckhoff ADS 真实协议服务端或 shared_source production backend。
"""

from __future__ import annotations

import pytest

from tests.support.scada_sample_db import postgres_scada_sample_db
from tools.source_lab.access.providers.scada_profile import ScadaProfileProvider

_EXPECTED_MATRIX = {
    ("OPC_UA", "READ"),
    ("OPC_UA", "SUBSCRIBE"),
    ("MODBUS", "TCP_READ"),
    ("MODBUS", "RTU_READ"),
    ("IEC101", "INTERROGATION"),
    ("IEC101", "SPONTANEOUS"),
    ("IEC104", "INTERROGATION"),
    ("IEC104", "SPONTANEOUS"),
    ("IEC61850", "MMS_READ"),
    ("IEC61850", "REPORT"),
    ("IEC61850", "GOOSE"),
    ("IEC61850", "SV"),
    ("MQTT", "SUBSCRIBE"),
    ("HTTP_REST", "REQUEST"),
    ("BECKHOFF_ADS", "ADS_READ_WRITE"),
    ("BECKHOFF_ADS", "ADS_NOTIFICATION"),
}


@pytest.mark.integration
def test_scada_profile_provider_reads_16_sources_from_safe_postgres_sample_db() -> None:
    """provider 应从 PostgreSQL 样例库读取完整 16 组 protocol-service。"""

    try:
        with postgres_scada_sample_db() as sample_db:
            provider = ScadaProfileProvider(database_url=sample_db.database_url)
            sources = provider.list_sources()
    except RuntimeError as exc:
        message = str(exc)
        if (
            "requires env vars" in message
            or "test environment unavailable" in message
        ):
            pytest.skip(f"environment-pending: shared persistence PostgreSQL test env unavailable: {message}")
        raise

    source_matrix = {
        (str(source.connection.application_protocol), str(source.connection.service_type))
        for source in sources
    }
    runtime_status_by_service = {
        (str(source.connection.application_protocol), str(source.connection.service_type)): str(
            source.connection.params.get("runtime_status", "")
        )
        for source in sources
    }
    backend_kind_by_service = {
        (str(source.connection.application_protocol), str(source.connection.service_type)): str(
            source.connection.params.get("backend_kind", "")
        )
        for source in sources
        if "backend_kind" in source.connection.params
    }
    runtime_reason = {
        (str(source.connection.application_protocol), str(source.connection.service_type)): str(
            source.connection.params.get("runtime_reason", "")
        )
        for source in sources
        if "runtime_reason" in source.connection.params
    }

    assert source_matrix == _EXPECTED_MATRIX
    assert len(sources) == 16
    assert all(len(source.points) == 3 for source in sources)
    assert runtime_status_by_service[("BECKHOFF_ADS", "ADS_READ_WRITE")] == "available"
    assert runtime_status_by_service[("BECKHOFF_ADS", "ADS_NOTIFICATION")] == "available"
    assert backend_kind_by_service[("BECKHOFF_ADS", "ADS_READ_WRITE")] == "in_process"
    assert backend_kind_by_service[("BECKHOFF_ADS", "ADS_NOTIFICATION")] == "in_process"
    assert "not implemented" in runtime_reason[("BECKHOFF_ADS", "ADS_NOTIFICATION")].lower()
