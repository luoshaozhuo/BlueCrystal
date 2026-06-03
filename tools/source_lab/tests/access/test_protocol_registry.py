"""协议注册表测试。"""

from __future__ import annotations

import pytest

from tools.source_lab.access.runners.registry import (
    build_capacity_runner,
    build_subscription_runner,
    get_implementation_level,
    get_protocol_capability,
    list_supported_protocols,
    normalize_protocol,
    probe_mode_for_protocol,
    supports_access_mode,
)


def test_normalize_protocol_aliases() -> None:
    """协议别名应归一到标准协议名。"""

    assert normalize_protocol("opc-ua") == "opcua"
    assert normalize_protocol("modbusTcp") == "modbus_tcp"
    assert normalize_protocol("iec-104") == "iec104"
    assert normalize_protocol("http") == "http_rest"


def test_list_supported_protocols_contains_required_entries() -> None:
    """支持协议列表应覆盖目标协议集合。"""

    assert list_supported_protocols() == (
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
        "beckhoff_ads",
    )


def test_support_matrix() -> None:
    """协议访问模式矩阵应符合预期。"""

    assert supports_access_mode("opcua", "polling") is True
    assert supports_access_mode("opcua", "subscribe") is True
    assert supports_access_mode("http_rest", "polling") is True
    assert supports_access_mode("http_rest", "subscribe") is False
    assert supports_access_mode("mqtt", "subscribe") is True
    assert supports_access_mode("mqtt", "polling") is False


def test_probe_mode_mapping() -> None:
    """probe 模式映射应与协议能力一致。"""

    assert probe_mode_for_protocol("opcua") == "polling"
    assert probe_mode_for_protocol("modbus_tcp") == "polling"
    assert probe_mode_for_protocol("mqtt") == "streaming"
    assert probe_mode_for_protocol("iec61850_report") == "streaming"
    assert probe_mode_for_protocol("iec61850_goose") == "streaming"
    assert probe_mode_for_protocol("iec61850_sv") == "streaming"


def test_build_runner_factories() -> None:
    """runner 工厂应返回对应实现。"""

    assert build_capacity_runner("opcua").name == "opcua_open62541_serial_runner"
    assert build_capacity_runner("modbus_tcp").name == "modbus_tcp_native_runner"
    assert build_subscription_runner("opcua").name == "opcua_open62541_subscription_runner"
    assert build_subscription_runner("mqtt").name == "mqtt_subscription_runner"
    assert build_subscription_runner("iec61850_goose").name == "iec61850_goose_subscriber_runner"
    assert build_subscription_runner("iec61850_sv").name == "iec61850_sv_subscriber_runner"


def test_unsupported_protocol_raises() -> None:
    """未知协议应明确失败。"""

    with pytest.raises(ValueError, match="unsupported protocol"):
        normalize_protocol("dnp3")


def test_opcua_is_real_native_runner() -> None:
    """OPC UA 应标注为 real_native_runner（唯一真实 C runner）。"""

    assert get_implementation_level("opcua") == "real_native_runner"
    cap = get_protocol_capability("opcua")
    assert "open62541 executable" in str(cap["backend"])


def test_iec61850_is_real_native_runner() -> None:
    """IEC61850 MMS 和 Report 现已支持 real_native_runner。"""

    assert get_implementation_level("iec61850_mms") == "real_native_runner"
    assert get_implementation_level("iec61850_report") == "real_native_runner"


def test_iec104_is_real_native_runner() -> None:
    """IEC104 是 real_native_runner（C lib60870 子进程）。"""

    assert get_implementation_level("iec104") == "real_native_runner"


def test_modbus_rtu_iec101_are_python_lightweight_runner() -> None:
    """Modbus RTU 和 IEC101 是 python_lightweight_runner（标准库 serial，非 C native）。"""

    assert get_implementation_level("modbus_rtu") == "python_lightweight_runner"
    assert get_implementation_level("iec101") == "python_lightweight_runner"


def test_all_registered_protocols_have_implementation_level() -> None:
    """所有注册协议都必须有明确的 implementation_level。"""

    valid_levels = {
        "real_native_runner",
        "python_lightweight_runner",
        "fake_or_simulated_runner",
        "semantic_probe_only",
        "planned_native_runner",
    }
    for protocol in list_supported_protocols():
        level = get_implementation_level(protocol)
        assert level in valid_levels, (
            f"{protocol}: unexpected implementation_level={level!r}"
        )


def test_no_protocol_falsely_claims_real_native_runner() -> None:
    """本机 C runner 编译通过的协议方可标注为 real_native_runner。"""

    real_native_protocols = {
        p for p in list_supported_protocols() if get_implementation_level(p) == "real_native_runner"
    }
    assert real_native_protocols == {"opcua", "modbus_tcp", "iec104", "iec61850_mms", "iec61850_report", "iec61850_goose", "iec61850_sv"}, (
        f"unexpected real_native_runner set: {real_native_protocols}"
    )
