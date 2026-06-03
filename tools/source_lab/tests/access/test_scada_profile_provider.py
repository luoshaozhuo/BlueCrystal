"""SCADA sample DB provider 测试。

测试阶段：跨模块联调期验证 (integration)。
本测试通过真实 shared persistence sample SQLite 初始化，再由
`ScadaProfileProvider` 读取 16 组协议服务样例并转换为 source_lab 模型。
它证明 source_lab 已开始真实消费 shared persistence 输入基线，但不证明
所有协议 runtime、native runner 或现场设备连通性都已通过。
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.support.scada_sample_db import create_isolated_scada_sample_db
from tools.source_lab.access.providers.scada_profile import ScadaProfileProvider


def _build_provider(tmp_path: Path) -> ScadaProfileProvider:
    db_path = create_isolated_scada_sample_db(tmp_path)
    return ScadaProfileProvider(db_path=db_path)


def test_scada_profile_provider_reads_full_protocol_service_matrix(tmp_path: Path) -> None:
    """provider 应完整读取 shared persistence 中的 16 组三元组。"""

    provider = _build_provider(tmp_path)
    sources = provider.list_sources()

    observed = {
        (
            str(source.connection.application_protocol),
            str(source.connection.service_type),
            source.connection.transport,
        )
        for source in sources
    }
    expected = {
        ("OPC_UA", "READ", "TCP"),
        ("OPC_UA", "SUBSCRIBE", "TCP"),
        ("MODBUS", "TCP_READ", "TCP"),
        ("MODBUS", "RTU_READ", "SERIAL"),
        ("IEC101", "INTERROGATION", "SERIAL"),
        ("IEC101", "SPONTANEOUS", "SERIAL"),
        ("IEC104", "INTERROGATION", "TCP"),
        ("IEC104", "SPONTANEOUS", "TCP"),
        ("IEC61850", "MMS_READ", "TCP"),
        ("IEC61850", "REPORT", "TCP"),
        ("IEC61850", "GOOSE", "ETHERNET_L2"),
        ("IEC61850", "SV", "ETHERNET_L2"),
        ("MQTT", "SUBSCRIBE", "MQTT"),
        ("HTTP_REST", "REQUEST", "HTTPS"),
        ("BECKHOFF_ADS", "ADS_READ_WRITE", "TCP"),
        ("BECKHOFF_ADS", "ADS_NOTIFICATION", "TCP"),
    }

    assert observed == expected
    assert all(len(source.points) == 3 for source in sources)


def test_scada_profile_provider_maps_runtime_aliases_and_ads_boundaries(tmp_path: Path) -> None:
    """provider 应保留三元组，并补齐现有 runtime/runner 可识别的最小别名。"""

    provider = _build_provider(tmp_path)

    modbus_tcp = provider.load_source(protocol="modbus_tcp", access_mode="polling")
    assert modbus_tcp.connection.application_protocol == "MODBUS"
    assert modbus_tcp.connection.service_type == "TCP_READ"
    assert modbus_tcp.connection.params["modbus_unit_id"] == 1
    assert modbus_tcp.connection.params["modbus_start_address"] == 40001
    assert modbus_tcp.points[0].locator == "40001"
    assert modbus_tcp.points[1].locator == "40003"

    http_rest = provider.load_source(protocol="http_rest", access_mode="polling")
    assert http_rest.connection.transport == "HTTPS"
    assert http_rest.connection.protocol == "http_rest"
    assert http_rest.connection.params["http_path"] == "/points"

    mqtt = provider.load_source(protocol="mqtt", access_mode="subscribe")
    assert mqtt.connection.params["mqtt_topic"] == "whale/wtg/001/telemetry"
    assert mqtt.connection.params["mqtt_client_id"] == "whale-mqtt-wtg-001"

    ads_polling = provider.load_source(protocol="beckhoff_ads", access_mode="polling")
    assert ads_polling.connection.application_protocol == "BECKHOFF_ADS"
    assert ads_polling.connection.service_type == "ADS_READ_WRITE"
    assert ads_polling.connection.params["runtime_status"] == "available"
    assert ads_polling.connection.params["ams_net_id"] == "5.32.160.1.1.1"
    assert ads_polling.connection.params["ads_server_port"] == 851
    assert ads_polling.points[0].protocol_params["index_offset"] == 32
    assert ads_polling.points[1].protocol_params["index_offset"] == 40

    ads_notification = provider.load_source(protocol="beckhoff_ads", access_mode="subscribe")
    assert ads_notification.connection.service_type == "ADS_NOTIFICATION"
    assert ads_notification.connection.params["runtime_status"] == "available"
    assert "runtime_reason" in ads_notification.connection.params


def test_scada_profile_provider_selects_service_specific_source_for_multi_service_protocols(
    tmp_path: Path,
) -> None:
    """同一协议多 service_type 时，应按 access_mode 选中正确三元组。"""

    provider = _build_provider(tmp_path)

    opcua_polling = provider.load_source(protocol="opcua", access_mode="polling")
    opcua_streaming = provider.load_source(protocol="opcua", access_mode="subscribe")
    iec104_polling = provider.load_source(protocol="iec104", access_mode="polling")
    iec104_streaming = provider.load_source(protocol="iec104", access_mode="subscribe")

    assert opcua_polling.connection.service_type == "READ"
    assert opcua_streaming.connection.service_type == "SUBSCRIBE"
    assert iec104_polling.connection.service_type == "INTERROGATION"
    assert iec104_streaming.connection.service_type == "SPONTANEOUS"


def test_scada_profile_provider_fails_for_unknown_protocol_mapping(tmp_path: Path) -> None:
    """未登记的 protocol 映射必须 fail，避免静默落空。"""

    provider = _build_provider(tmp_path)

    with pytest.raises(ValueError, match="unsupported source_lab protocol"):
        provider.load_source(protocol="dnp3", access_mode="polling")
