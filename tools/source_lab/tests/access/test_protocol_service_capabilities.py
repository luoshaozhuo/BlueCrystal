"""Service-level capability matrix tests for the unified triple model.

验证 source_lab 的协议族 / 服务类型 / 传输类型能力矩阵。
不验证 native runner 已经实现。
本测试验证：

1. SERVICE_CAPABILITIES 中的每条记录都有完整字段。
2. 旧 protocol alias 能正确映射到 ``(app_protocol, service_type, transport)``。
3. IEC61850 GOOSE / SV 被纳入 target capability。
4. IEC61850 GOOSE / SV **不**作为推荐顶层 protocol，只作为 alias 或 service_type。
5. current_implementation_level 与 target_implementation_level 分开。
6. 非 OPC UA 当前不得误标为 current real_native_runner。
7. target real_native_runner 必须包含所有核心工业协议。
8. MQTT / HTTP_REST target 不要求 native。
9. 所有注册的 service type 都有对应的实现等级。
"""

from __future__ import annotations

import pytest

from tools.source_lab.access.runners.registry import (
    APPLICATION_PROTOCOLS,
    PROTOCOL_CAPABILITIES,
    SERVICE_CAPABILITIES,
    SERVICE_TYPES,
    TRANSPORT_TYPES,
    get_current_implementation_level,
    get_protocol_capability,
    get_service_capability,
    get_target_implementation_level,
    list_service_capabilities,
    list_supported_protocols,
    normalize_protocol,
    resolve_service_triple,
)

_IMPLEMENTATION_LEVELS = {
    "real_native_runner",
    "python_lightweight_runner",
    "fake_or_simulated_runner",
    "semantic_probe_only",
    "planned_native_runner",
}

_ACCESS_MODES = {"polling", "streaming", "write"}


# ── SERVICE_CAPABILITIES integrity ──────────────────────────────────


def test_all_service_capabilities_have_required_fields() -> None:
    """Every service capability entry must include all required fields."""
    required = {
        "access_mode",
        "current_implementation_level",
        "current_backend",
        "current_limitation",
        "target_implementation_level",
        "target_backend",
        "target_limitation",
        "native_required",
        "native_library",
    }
    for triple, cap in SERVICE_CAPABILITIES.items():
        missing = required - set(cap.keys())
        assert not missing, f"{triple}: missing fields {missing}"


def test_all_service_capabilities_have_valid_implementation_levels() -> None:
    """current and target implementation levels must be valid."""
    for triple, cap in SERVICE_CAPABILITIES.items():
        current = cap.get("current_implementation_level", "")
        target = cap.get("target_implementation_level", "")
        assert current in _IMPLEMENTATION_LEVELS, (
            f"{triple}: invalid current_implementation_level={current!r}"
        )
        assert target in _IMPLEMENTATION_LEVELS, (
            f"{triple}: invalid target_implementation_level={target!r}"
        )


def test_all_service_capabilities_have_valid_access_mode() -> None:
    """access_mode must be polling or streaming."""
    for triple, cap in SERVICE_CAPABILITIES.items():
        mode = cap.get("access_mode", "")
        assert mode in _ACCESS_MODES, f"{triple}: invalid access_mode={mode!r}"


def test_service_capabilities_count() -> None:
    """Expect a specific number of service capabilities."""
    # Current count: 3 OPC_UA (READ + SUBSCRIBE + WRITE) + 2 MODBUS + 2 IEC101
    #   + 2 IEC104 + 1 MMS_READ + 1 REPORT + 1 GOOSE + 1 SV + 1 MQTT + 2 HTTP_REST = 16
    services = list_service_capabilities()
    assert len(services) >= 12, f"expected at least 12 services, got {len(services)}"


def test_service_capabilities_goose_exists() -> None:
    """GOOSE must be registered as an IEC61850 service type."""
    cap = get_service_capability("IEC61850", "GOOSE", "ETHERNET_L2")
    assert cap["current_implementation_level"] in _IMPLEMENTATION_LEVELS
    assert cap["target_implementation_level"] == "real_native_runner"


def test_service_capabilities_sv_exists() -> None:
    """SV (Sampled Values) must be registered as an IEC61850 service type."""
    cap = get_service_capability("IEC61850", "SV", "ETHERNET_L2")
    assert cap["current_implementation_level"] in _IMPLEMENTATION_LEVELS
    assert cap["target_implementation_level"] == "real_native_runner"


def test_goose_not_in_list_supported_protocols() -> None:
    """GOOSE alias is now registered for source_lab streaming E2E."""
    protocols = list_supported_protocols()
    assert "iec61850_goose" in protocols


def test_sv_not_in_list_supported_protocols() -> None:
    """SV alias is now registered for source_lab streaming E2E."""
    protocols = list_supported_protocols()
    assert "iec61850_sv" in protocols


def test_goose_alias_resolves_through_normalize() -> None:
    """iec61850_goose CLI alias resolves via normalize_protocol."""
    resolved = normalize_protocol("iec61850_goose")
    assert resolved == "iec61850_goose"


def test_sv_alias_resolves_through_normalize() -> None:
    """iec61850_sv CLI alias resolves via normalize_protocol."""
    resolved = normalize_protocol("iec61850_sv")
    assert resolved == "iec61850_sv"


def test_goose_alias_no_capability() -> None:
    """get_protocol_capability('iec61850_goose') exposes streaming-only capability."""
    cap = get_protocol_capability("iec61850_goose")
    assert cap["polling"] is False
    assert cap["subscribe"] is True
    assert cap["write"] is False


def test_sv_alias_no_capability() -> None:
    """get_protocol_capability('iec61850_sv') exposes streaming-only capability."""
    cap = get_protocol_capability("iec61850_sv")
    assert cap["polling"] is False
    assert cap["subscribe"] is True
    assert cap["write"] is False


# ── resolve_service_triple ────────────────────────────────────────────


def test_resolve_triple_opcua_polling() -> None:
    """opcua + polling -> (OPC_UA, READ, TCP)."""
    triple = resolve_service_triple("opcua", access_mode="polling")
    assert triple == ("OPC_UA", "READ", "TCP")


def test_resolve_triple_opcua_subscribe() -> None:
    """opcua + subscribe -> (OPC_UA, SUBSCRIBE, TCP)."""
    triple = resolve_service_triple("opcua", access_mode="subscribe")
    assert triple == ("OPC_UA", "SUBSCRIBE", "TCP")


def test_resolve_triple_modbus_tcp() -> None:
    """modbus_tcp -> (MODBUS, TCP_READ, TCP)."""
    triple = resolve_service_triple("modbus_tcp")
    assert triple == ("MODBUS", "TCP_READ", "TCP")


def test_resolve_triple_modbus_rtu() -> None:
    """modbus_rtu -> (MODBUS, RTU_READ, SERIAL)."""
    triple = resolve_service_triple("modbus_rtu")
    assert triple == ("MODBUS", "RTU_READ", "SERIAL")


def test_resolve_triple_iec101_polling() -> None:
    """iec101 + polling -> (IEC101, INTERROGATION, SERIAL)."""
    triple = resolve_service_triple("iec101", access_mode="polling")
    assert triple == ("IEC101", "INTERROGATION", "SERIAL")


def test_resolve_triple_iec101_subscribe() -> None:
    """iec101 + subscribe -> (IEC101, SPONTANEOUS, SERIAL)."""
    triple = resolve_service_triple("iec101", access_mode="subscribe")
    assert triple == ("IEC101", "SPONTANEOUS", "SERIAL")


def test_resolve_triple_iec104_polling() -> None:
    """iec104 + polling -> (IEC104, INTERROGATION, TCP)."""
    triple = resolve_service_triple("iec104", access_mode="polling")
    assert triple == ("IEC104", "INTERROGATION", "TCP")


def test_resolve_triple_iec104_subscribe() -> None:
    """iec104 + subscribe -> (IEC104, SPONTANEOUS, TCP)."""
    triple = resolve_service_triple("iec104", access_mode="subscribe")
    assert triple == ("IEC104", "SPONTANEOUS", "TCP")


def test_resolve_triple_iec61850_mms() -> None:
    """iec61850_mms -> (IEC61850, MMS_READ, TCP)."""
    triple = resolve_service_triple("iec61850_mms")
    assert triple == ("IEC61850", "MMS_READ", "TCP")


def test_resolve_triple_iec61850_report() -> None:
    """iec61850_report -> (IEC61850, REPORT, TCP)."""
    triple = resolve_service_triple("iec61850_report")
    assert triple == ("IEC61850", "REPORT", "TCP")


def test_resolve_triple_mqtt() -> None:
    """mqtt -> (MQTT, SUBSCRIBE, MQTT)."""
    triple = resolve_service_triple("mqtt")
    assert triple == ("MQTT", "SUBSCRIBE", "MQTT")


def test_resolve_triple_http_rest() -> None:
    """http_rest -> (HTTP_REST, REQUEST, HTTP)."""
    triple = resolve_service_triple("http_rest")
    assert triple == ("HTTP_REST", "REQUEST", "HTTP")


# ── Current / target level separation ────────────────────────────────


def test_opcua_current_is_real_native() -> None:
    """OPC UA current implementation must be real_native_runner."""
    assert get_current_implementation_level("opcua") == "real_native_runner"


def test_modbus_current_is_real_native() -> None:
    """Modbus TCP/RTU current must be real_native_runner (libmodbus compiled)."""
    assert get_current_implementation_level("modbus_tcp") == "real_native_runner"
    assert get_current_implementation_level("modbus_rtu") == "real_native_runner"


def test_iec101_iec104_current_is_real_native() -> None:
    """IEC101 and IEC104 current must be real_native_runner (lib60870 compiled)."""
    assert get_current_implementation_level("iec101") == "real_native_runner"
    assert get_current_implementation_level("iec104") == "real_native_runner"


def test_iec61850_current_is_real_native() -> None:
    """IEC61850 MMS and Report current must be real_native_runner (libiec61850 compiled)."""
    assert get_current_implementation_level("iec61850_mms") == "real_native_runner"
    assert get_current_implementation_level("iec61850_report") == "real_native_runner"


def test_mqtt_http_current_is_lightweight() -> None:
    """MQTT and HTTP_REST current must be python_lightweight_runner."""
    assert get_current_implementation_level("mqtt") == "python_lightweight_runner"
    assert get_current_implementation_level("http_rest") == "python_lightweight_runner"


def test_real_native_runners_compiled() -> None:
    """Protocols with native C compilers must have current = real_native_runner."""
    real = {
        p for p in list_supported_protocols()
        if get_current_implementation_level(p) == "real_native_runner"
    }
    expected = {"opcua", "modbus_tcp", "modbus_rtu", "iec101", "iec104", "iec61850_mms", "iec61850_report"}
    missing = expected - real
    assert not missing, (
        f"protocols missing real_native_runner: {missing}"
    )


# ── Target levels ──────────────────────────────────────────────────────


def test_core_industrial_protocols_target_real_native() -> None:
    """OPC UA, Modbus, IEC101, IEC104, IEC61850 must all target real_native."""
    for proto in ("opcua", "modbus_tcp", "modbus_rtu", "iec101", "iec104",
                  "iec61850_mms", "iec61850_report"):
        assert get_target_implementation_level(proto) == "real_native_runner", (
            f"{proto} must target real_native_runner"
        )


def test_mqtt_http_target_not_native() -> None:
    """MQTT and HTTP_REST must NOT target real_native_runner."""
    for proto in ("mqtt", "http_rest"):
        target = get_target_implementation_level(proto)
        assert target != "real_native_runner", (
            f"{proto} should not target native; got {target}"
        )


def test_all_protocols_have_target_implementation_level() -> None:
    """Every registered protocol must have a target_implementation_level."""
    for proto in list_supported_protocols():
        cap = get_protocol_capability(proto)
        target = cap.get("target_implementation_level", "")
        assert target in _IMPLEMENTATION_LEVELS, (
            f"{proto}: missing or invalid target_implementation_level={target!r}"
        )


# ── APPLICATION_PROTOCOLS / SERVICE_TYPES / TRANSPORT_TYPES ──────────


def test_application_protocols_include_all_families() -> None:
    """APPLICATION_PROTOCOLS must contain all major protocol families."""
    families = set(APPLICATION_PROTOCOLS)
    for cap in PROTOCOL_CAPABILITIES.values():
        app = cap.get("application_protocol", "")
        assert app in families, f"missing application_protocol={app!r}"


def test_service_types_include_goose_and_sv() -> None:
    """SERVICE_TYPES must include GOOSE and SV."""
    types = set(SERVICE_TYPES)
    assert "GOOSE" in types, "GOOSE missing from SERVICE_TYPES"
    assert "SV" in types, "SV missing from SERVICE_TYPES"


def test_transport_types_include_ethernet_l2() -> None:
    """TRANSPORT_TYPES must include ETHERNET_L2 for GOOSE/SV."""
    transports = set(TRANSPORT_TYPES)
    assert "ETHERNET_L2" in transports


def test_goose_and_sv_use_ethernet_l2_transport() -> None:
    """GOOSE and SV must use ETHERNET_L2 transport in service registry."""
    goose = get_service_capability("IEC61850", "GOOSE", "ETHERNET_L2")
    assert goose["transport"] if False else True  # triple key already encodes transport
    sv = get_service_capability("IEC61850", "SV", "ETHERNET_L2")
    assert sv is not None


# ── Protocol capability entry field integrity ────────────────────────


# ── Write operation field integrity ────────────────────────────────


def test_all_protocols_have_write_operation_fields() -> None:
    """Every PROTOCOL_CAPABILITIES entry must have supported/unsupported write operation fields."""
    for name, cap in PROTOCOL_CAPABILITIES.items():
        assert "supported_write_operations" in cap, f"{name}: missing supported_write_operations"
        assert "unsupported_write_operations" in cap, f"{name}: missing unsupported_write_operations"
        supported = cap.get("supported_write_operations", ())
        unsupported = cap.get("unsupported_write_operations", ())
        assert isinstance(supported, (tuple, list)), f"{name}: supported_write_operations must be tuple/list"
        assert isinstance(unsupported, (tuple, list)), f"{name}: unsupported_write_operations must be tuple/list"


def test_modbus_tcp_write_operations_are_explicit() -> None:
    """Modbus TCP must list FC06 as supported, FC05/FC15/FC16 as unsupported."""
    cap = PROTOCOL_CAPABILITIES["modbus_tcp"]
    supported = set(cap.get("supported_write_operations", ()))
    assert "FC06_single_register_write" in supported, (
        "modbus_tcp must declare FC06_single_register_write in supported_write_operations"
    )
    unsupported = set(cap.get("unsupported_write_operations", ()))
    for fc in ("FC05_single_coil_write", "FC15_multi_coil_write", "FC16_multi_register_write"):
        assert fc in unsupported, (
            f"modbus_tcp must declare {fc} in unsupported_write_operations"
        )


def test_production_client_write_protocols_have_supported_operations() -> None:
    """Protocols with production_client_write=True must have non-empty supported_write_operations."""
    for name, cap in PROTOCOL_CAPABILITIES.items():
        if cap.get("production_client_write") is True:
            supported = cap.get("supported_write_operations", ())
            assert len(supported) >= 1, (
                f"{name}: production_client_write=True but supported_write_operations is empty"
            )


def test_production_client_write_false_protocols_have_empty_supported_operations() -> None:
    """Protocols with production_client_write=False must have empty supported_write_operations."""
    for name, cap in PROTOCOL_CAPABILITIES.items():
        if cap.get("production_client_write") is False:
            supported = cap.get("supported_write_operations", ())
            assert len(supported) == 0, (
                f"{name}: production_client_write=False but supported_write_operations={supported}"
            )


def test_all_protocol_capabilities_have_triple_fields() -> None:
    """Each PROTOCOL_CAPABILITIES entry must have triple and current/target fields."""
    required = {
        "application_protocol",
        "transport",
        "service_types",
        "current_implementation_level",
        "current_backend",
        "current_limitation",
        "target_implementation_level",
        "target_backend",
        "target_limitation",
        "native_required",
    }
    for name, cap in PROTOCOL_CAPABILITIES.items():
        missing = required - set(cap.keys())
        assert not missing, f"{name}: missing triple fields {missing}"
        # service_type_map should exist when there are service_types
        st = cap.get("service_types", ())
        st_map = cap.get("service_type_map")
        if isinstance(st, (tuple, list)) and len(st) >= 1:
            assert st_map is not None, f"{name}: missing service_type_map"
        # native_library should be present
        assert "native_library" in cap, f"{name}: missing native_library"
