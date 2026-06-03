"""Multi-protocol runner registry with unified triple capability model.

The capability model has been upgraded from protocol-only to a triple of
``(application_protocol, service_type, transport)``.  CLI flags and
fixtures that still use legacy protocol names (e.g. ``--protocol modbus_tcp``)
continue to work via a backward-compatibility mapping layer that resolves
old names to the canonical triple.

Structure
---------
- ``DECLARED_PROTOCOL_CAPABILITIES``
    Per-protocol-name registry dict of **static declared capability metadata only**.
    Each entry carries ``application_protocol``, ``transport``,
    ``service_types``, ``current_*`` / ``target_*`` fields.
    **IMPORTANT**: This dict only describes *declared* capability — it does
    NOT represent *actual runtime readiness*.  Callers must use
    ``describe_protocol_runtime_readiness()`` (which checks native binary
    availability at runtime) to gate production/readiness decisions.
    Tests that read ``implementation_level``, ``backend``, access-mode flags
    should still use this dict but must annotate their evidence level
    appropriately (static/declared vs runtime/actual).

- ``SERVICE_CAPABILITIES``
    New canonical dict keyed by ``(app_protocol, service_type, transport)``.
    Each entry describes a single service-level capability with its own
    current/target implementation levels, backend, limitation, and native
    requirements.

- ``_PROTOCOL_ALIASES``
    Flat lookup that maps any CLI-visible protocol string (including
    deprecated forms like ``iec61850_goose``) to a canonical key.

- ``PROTOCOL_CAPABILITIES``
    Backward-compatibility alias for ``DECLARED_PROTOCOL_CAPABILITIES``.
    **DEPRECATED**: new code should use ``DECLARED_PROTOCOL_CAPABILITIES``
    for static metadata access and ``describe_protocol_runtime_readiness()``
    for runtime readiness decisions.

Level definitions
-----------------
    real_native_runner         — real C runner via subprocess
    python_lightweight_runner  — Python socket / http / mqtt
    fake_or_simulated_runner   — simulated runner for test closure
    semantic_probe_only        — minimum protocol-semantic probe
    planned_native_runner      — planned but not yet implemented
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Final

from tools.source_lab.access.runners.base import CapacityRunner, SubscriptionRunner
from tools.source_lab.access.subscribe.model import SubscribeScanConfig, SubscribeWorkerRawStats
from tools.source_lab.access.runners.open62541_serial_polling import OpcUaOpen62541CapacityRunner
from tools.source_lab.access.runners.open62541_subscription import OpcUaOpen62541SubscribeRunner

# ── Registry type alias ────────────────────────────────────────────────
# One protocol capability entry dict.
_ProtoCap = dict[str, object]

_IMPLEMENTATION_LEVELS: Final[tuple[str, ...]] = (
    "real_native_runner",
    "python_lightweight_runner",
    "fake_or_simulated_runner",
    "semantic_probe_only",
    "planned_native_runner",
)

# ── Protocol capability metadata (legacy per-name registry) ──────────
# README protocol matrix, test matrix all take this as source of truth.
# The ``implementation_level`` key is kept as a backward-compat alias for
# ``current_implementation_level``.

DECLARED_PROTOCOL_CAPABILITIES: Final[dict[str, _ProtoCap]] = {
    # ── OPC UA ─────────────────────────────────────────────────────
    "opcua": {
        # Legacy access-mode flags
        "polling": True,
        "subscribe": True,
        "probe": True,
        # Write capability flags
        "write": True,
        "production_client_write": True,
        "simulator_write_injection": True,
        "supported_write_operations": ("write_variable",),
        "unsupported_write_operations": (),
        "write_limitation": "OPC UA production write via open62541 native runner WRITE command (2026-05-23).",
        # Legacy summary aliases (backward compat)
        "implementation_level": "real_native_runner",
        "backend": "open62541 executable runner",
        "limitation": "",
        # New triple fields
        "application_protocol": "OPC_UA",
        "transport": "TCP",
        "service_types": ("READ", "SUBSCRIBE", "WRITE"),
        "service_type_map": {"polling": "READ", "subscribe": "SUBSCRIBE", "write": "WRITE"},
        "access_modes": ("polling", "streaming"),
        # Current implementation
        "current_implementation_level": "real_native_runner",
        "current_backend": "open62541 executable runner",
        "current_limitation": "",
        # Target implementation
        "target_implementation_level": "real_native_runner",
        "target_backend": "open62541 executable runner",
        "target_limitation": "",
        # Native requirement
        "native_required": True,
        "native_library": "open62541",
        # CLI names
        "cli_aliases": ("opcua", "opc-ua"),
    },
    # ── Modbus TCP ─────────────────────────────────────────────────
    "modbus_tcp": {
        "polling": True,
        "subscribe": False,
        "probe": True,
        "write": True,
        "production_client_write": True,
        "simulator_write_injection": True,
        "supported_write_operations": ("FC06_single_register_write",),
        "unsupported_write_operations": ("FC05_single_coil_write", "FC15_multi_coil_write", "FC16_multi_register_write"),
        "write_limitation": "Modbus TCP write via FC06 (single register) through native runner WRITE command (2026-05-24). FC05/FC15/FC16 not implemented.",
        "implementation_level": "real_native_runner",
        "backend": "libmodbus executable runner",
        "limitation": "",
        "application_protocol": "MODBUS",
        "transport": "TCP",
        "service_types": ("TCP_READ", "TCP_WRITE"),
        "service_type_map": {"polling": "TCP_READ", "write": "TCP_WRITE"},
        "access_modes": ("polling",),
        "current_implementation_level": "real_native_runner",
        "current_backend": "libmodbus executable runner",
        "current_limitation": "",
        "target_implementation_level": "real_native_runner",
        "target_backend": "libmodbus executable runner",
        "target_limitation": "",
        "native_required": True,
        "native_library": "libmodbus",
        "cli_aliases": ("modbus_tcp", "modbustcp"),
    },
    # ── Modbus RTU ─────────────────────────────────────────────────
    "modbus_rtu": {
        "polling": True,
        "subscribe": False,
        "probe": True,
        "write": False,
        "production_client_read": True,
        "production_client_write": False,
        "simulator_write_injection": True,
        "supported_write_operations": (),
        "unsupported_write_operations": ("FC05_single_coil_write", "FC06_single_register_write", "FC15_multi_coil_write", "FC16_multi_register_write"),
        "write_limitation": "Modbus RTU write NOT_IMPLEMENTED. Read-only acquisition via python_lightweight_runner serial backend (FC03). Serial port via Python os/termios, not C native runner.",
        "implementation_level": "python_lightweight_runner",
        "backend": "Python os/termios serial Modbus RTU (FC03)",
        "limitation": "Python lightweight serial implementation; real RS-485 serial environment not validated.",
        "application_protocol": "MODBUS",
        "transport": "SERIAL",
        "service_types": ("RTU_READ",),
        "service_type_map": {"polling": "RTU_READ"},
        "access_modes": ("polling",),
        "current_implementation_level": "python_lightweight_runner",
        "current_backend": "Python os/termios serial Modbus RTU (FC03)",
        "current_limitation": "Python lightweight serial implementation via standard library termios/os; no pyserial dependency. Real RS-485 serial port environment pending. Target is C native libmodbus runner.",
        "target_implementation_level": "real_native_runner",
        "target_backend": "libmodbus executable runner",
        "target_limitation": "",
        "native_required": True,
        "native_library": "libmodbus",
        "cli_aliases": ("modbus_rtu", "modbusrtu"),
    },
    # ── IEC 101 ────────────────────────────────────────────────────
    "iec101": {
        "polling": True,
        "subscribe": True,
        "probe": True,
        "write": False,
        "production_client_read": True,
        "production_client_write": False,
        "simulator_write_injection": True,
        "supported_write_operations": (),
        "unsupported_write_operations": ("C_SC", "C_SE", "C_BO"),
        "write_limitation": "IEC101 write NOT_IMPLEMENTED. Read-only interrogation via python_lightweight_runner serial backend. Serial port via Python os/termios, not C native runner.",
        "implementation_level": "python_lightweight_runner",
        "backend": "Python os/termios serial IEC 101 (FT1.2 + ASDU parsing)",
        "limitation": "Python lightweight serial implementation; real RS-232 serial environment not validated.",
        "application_protocol": "IEC101",
        "transport": "SERIAL",
        "service_types": ("INTERROGATION", "SPONTANEOUS"),
        "service_type_map": {
            "polling": "INTERROGATION",
            "subscribe": "SPONTANEOUS",
        },
        "access_modes": ("polling", "streaming"),
        "current_implementation_level": "python_lightweight_runner",
        "current_backend": "Python os/termios serial IEC 101 (FT1.2 + ASDU parsing)",
        "current_limitation": "Python lightweight serial implementation via standard library termios/os; no pyserial dependency. Real RS-232 serial port environment pending. Spontaneous data path is framework-only, not full event engine. Target is C native lib60870 runner.",
        "target_implementation_level": "real_native_runner",
        "target_backend": "lib60870-C executable runner",
        "target_limitation": "",
        "native_required": True,
        "native_library": "lib60870",
        "cli_aliases": ("iec101", "iec-101"),
    },
    # ── IEC 104 ────────────────────────────────────────────────────
    "iec104": {
        "polling": True,
        "subscribe": True,
        "probe": True,
        "write": True,
        "production_client_write": True,
        "simulator_write_injection": False,
        "supported_write_operations": ("C_SC_NA_1", "C_SE_NC_1"),
        "unsupported_write_operations": ("C_BO",),
        "write_limitation": "IEC 104 C_SC_NA_1 (single command) and C_SE_NC_1 (set point command) via native runner WRITE command (2026-06-02). C_BO (bitstring command) not implemented yet.",
        "implementation_level": "real_native_runner",
        "backend": "lib60870-C executable runner",
        "limitation": "",
        "application_protocol": "IEC104",
        "transport": "TCP",
        "service_types": ("INTERROGATION", "SPONTANEOUS"),
        "service_type_map": {
            "polling": "INTERROGATION",
            "subscribe": "SPONTANEOUS",
        },
        "access_modes": ("polling", "streaming"),
        "current_implementation_level": "real_native_runner",
        "current_backend": "lib60870-C executable runner",
        "current_limitation": "",
        "target_implementation_level": "real_native_runner",
        "target_backend": "lib60870-C executable runner",
        "target_limitation": "",
        "native_required": True,
        "native_library": "lib60870",
        "cli_aliases": ("iec104", "iec-104"),
    },
    # ── IEC 61850 MMS ──────────────────────────────────────────────
    "iec61850_mms": {
        "polling": True,
        "subscribe": False,
        "probe": True,
        "write": True,
        "production_client_write": True,
        "simulator_write_injection": True,
        "supported_write_operations": ("mms_direct_write",),
        "unsupported_write_operations": (
            "select_before_operate",
            "operate_on_select",
            "command_termination",
            "enhanced_security_control",
            "report_control_block_write",
            "goose",
            "sv",
        ),
        "write_limitation": "IEC 61850 MMS direct write via libiec61850 native runner WRITE command (2026-05-24). "
        "Only SP (set point) and CF (configuration) FC data attributes. "
        "Verified write types: BOOLEAN, INT32, UINT32, INT64, FLOAT32, FLOAT64, VISIBLE_STRING (all 7 types verified via integration write_then_readback). "
        "No SBO/Oper/Select/Cancel control models. No GOOSE/SV/Report write.",
        "implementation_level": "real_native_runner",
        "backend": "libiec61850 executable runner",
        "limitation": "",
        "application_protocol": "IEC61850",
        "transport": "TCP",
        "service_types": ("MMS_READ", "MMS_WRITE"),
        "service_type_map": {"polling": "MMS_READ", "write": "MMS_WRITE"},
        "access_modes": ("polling", "write"),
        "current_implementation_level": "real_native_runner",
        "current_backend": "libiec61850 executable runner",
        "current_limitation": "",
        "target_implementation_level": "real_native_runner",
        "target_backend": "libiec61850 executable runner",
        "target_limitation": "",
        "native_required": True,
        "native_library": "libiec61850",
        "cli_aliases": ("iec61850_mms", "iec61850mms"),
    },
    # ── IEC 61850 Report ───────────────────────────────────────────
    "iec61850_report": {
        "polling": False,
        "subscribe": True,
        "probe": True,
        "write": False,
        "production_client_read": False,
        "production_client_write": False,
        "production_client_subscribe": True,
        "supported_subscription_operations": ("report_subscription",),
        "unsupported_subscription_operations": (
            "polling_read", "goose", "sv", "brcb", "buffered_report",
        ),
        "simulator_write_injection": False,
        "supported_write_operations": (),
        "unsupported_write_operations": ("report_write",),
        "write_limitation": "IEC 61850 report subscription is read-only.",
        "implementation_level": "real_native_runner",
        "backend": "libiec61850 executable runner",
        "limitation": "",
        "application_protocol": "IEC61850",
        "transport": "TCP",
        "service_types": ("REPORT",),
        "service_type_map": {"subscribe": "REPORT"},
        "access_modes": ("streaming",),
        "current_implementation_level": "real_native_runner",
        "current_backend": "libiec61850 executable runner (report_runner via stdin/stdout, 2026-05-24)",
        "current_limitation": "订阅模式。通过 iec61850_report_runner C 子进程实现。已接入 composition。支持最小 reconnect（最多2次）。只支持 URCB，不支持 BRCB。无动态 DataSet 发现。无 GOOSE/SV。",
        "target_implementation_level": "real_native_runner",
        "target_backend": "libiec61850 executable runner",
        "target_limitation": "",
        "native_required": True,
        "native_library": "libiec61850",
        "cli_aliases": ("iec61850_report", "iec61850report"),
    },
    # ── IEC 61850 GOOSE ────────────────────────────────────────────
    "iec61850_goose": {
        "polling": False,
        "subscribe": True,
        "probe": True,
        "write": False,
        "production_client_read": False,
        "production_client_write": False,
        "production_client_subscribe": False,
        "supported_subscription_operations": ("goose_event",),
        "unsupported_subscription_operations": ("polling_read", "mms_write", "report", "sv"),
        "simulator_write_injection": True,
        "supported_write_operations": (),
        "unsupported_write_operations": ("goose_write", "mms_direct_write"),
        "write_limitation": "IEC 61850 GOOSE is event-only in source_lab simulator facade; write/control semantics are not implemented.",
        "implementation_level": "real_native_runner",
        "backend": "libiec61850 GOOSE publisher/subscriber runners",
        "limitation": "Requires Linux L2 raw socket permissions (CAP_NET_RAW) and a usable interface.",
        "application_protocol": "IEC61850",
        "transport": "ETHERNET_L2",
        "service_types": ("GOOSE",),
        "service_type_map": {"subscribe": "GOOSE"},
        "access_modes": ("streaming",),
        "current_implementation_level": "real_native_runner",
        "current_backend": "libiec61850 GOOSE publisher/subscriber runners",
        "current_limitation": "Requires CAP_NET_RAW/raw socket and interface selection; not an ingest production client.",
        "target_implementation_level": "real_native_runner",
        "target_backend": "libiec61850 GOOSE executable runner",
        "target_limitation": "",
        "native_required": True,
        "native_library": "libiec61850",
        "cli_aliases": ("iec61850_goose", "iec61850goose"),
    },
    # ── IEC 61850 Sampled Values ───────────────────────────────────
    "iec61850_sv": {
        "polling": False,
        "subscribe": True,
        "probe": True,
        "write": False,
        "production_client_read": False,
        "production_client_write": False,
        "production_client_subscribe": False,
        "supported_subscription_operations": ("sampled_value",),
        "unsupported_subscription_operations": ("polling_read", "mms_write", "report", "goose"),
        "simulator_write_injection": True,
        "supported_write_operations": (),
        "unsupported_write_operations": ("sv_write", "mms_direct_write"),
        "write_limitation": "IEC 61850 SV is sampled-value streaming only in source_lab simulator facade; write/control semantics are not implemented.",
        "implementation_level": "real_native_runner",
        "backend": "libiec61850 SV publisher/subscriber runners",
        "limitation": "Requires Linux L2 raw socket permissions (CAP_NET_RAW) and a usable interface.",
        "application_protocol": "IEC61850",
        "transport": "ETHERNET_L2",
        "service_types": ("SV",),
        "service_type_map": {"subscribe": "SV"},
        "access_modes": ("streaming",),
        "current_implementation_level": "real_native_runner",
        "current_backend": "libiec61850 SV publisher/subscriber runners",
        "current_limitation": "Requires CAP_NET_RAW/raw socket and interface selection; not an ingest production client.",
        "target_implementation_level": "real_native_runner",
        "target_backend": "libiec61850 SV executable runner",
        "target_limitation": "",
        "native_required": True,
        "native_library": "libiec61850",
        "cli_aliases": ("iec61850_sv", "iec61850sv"),
    },
    # ── MQTT ───────────────────────────────────────────────────────
    "mqtt": {
        "polling": False,
        "subscribe": True,
        "probe": True,
        "write": False,
        "production_client_write": False,
        "simulator_write_injection": True,
        "supported_write_operations": (),
        "unsupported_write_operations": ("MQTT_publish",),
        "write_limitation": "MQTT publish (write) not implemented yet. Simulator write injection via update_values is available.",
        "implementation_level": "python_lightweight_runner",
        "backend": "Python socket (MQTT handshake)",
        "limitation": "Python lightweight implementation, does not use Paho C native backend.",
        "application_protocol": "MQTT",
        "transport": "MQTT",
        "service_types": ("SUBSCRIBE",),
        "service_type_map": {"subscribe": "SUBSCRIBE"},
        "access_modes": ("streaming",),
        "current_implementation_level": "python_lightweight_runner",
        "current_backend": "Python socket (MQTT handshake)",
        "current_limitation": "Python lightweight implementation, does not use Paho C native backend.",
        "target_implementation_level": "python_lightweight_runner",
        "target_backend": "Python MQTT runner (mature client library)",
        "target_limitation": "MQTT/HTTP_REST are not required to be native C runners.",
        "native_required": False,
        "native_library": None,
        "cli_aliases": ("mqtt",),
    },
    # ── HTTP REST ──────────────────────────────────────────────────
    "http_rest": {
        "polling": True,
        "subscribe": False,
        "probe": True,
        "write": False,
        "production_client_write": False,
        "simulator_write_injection": True,
        "supported_write_operations": (),
        "unsupported_write_operations": ("HTTP_POST", "HTTP_PUT", "HTTP_PATCH", "HTTP_DELETE"),
        "write_limitation": "HTTP REST POST/PUT/PATCH (write) not implemented yet. Simulator write injection via update_values is available.",
        "implementation_level": "python_lightweight_runner",
        "backend": "Python urllib (HTTP GET)",
        "limitation": "Python lightweight implementation, not yet validated against full HTTP REST standard.",
        "application_protocol": "HTTP_REST",
        "transport": "HTTP",
        "service_types": ("REQUEST",),
        "service_type_map": {"polling": "REQUEST"},
        "access_modes": ("polling",),
        "current_implementation_level": "python_lightweight_runner",
        "current_backend": "Python urllib (HTTP GET)",
        "current_limitation": "Python lightweight implementation, not yet validated against full HTTP REST standard.",
        "target_implementation_level": "python_lightweight_runner",
        "target_backend": "Python HTTP runner (mature HTTP library)",
        "target_limitation": "HTTP_REST is not required to be native C runner.",
        "native_required": False,
        "native_library": None,
        "cli_aliases": ("http_rest", "http", "httprest"),
    },
    # ── Beckhoff ADS ──────────────────────────────────────────────
    "beckhoff_ads": {
        "polling": True,
        "subscribe": False,
        "probe": True,
        "write": False,
        "production_client_write": False,
        "simulator_write_injection": True,
        "supported_write_operations": ("ads_direct_write",),
        "unsupported_write_operations": ("ads_notification",),
        "write_limitation": "source_lab Beckhoff ADS 当前仅提供工具层 simulator/readback 闭环，不代表 shared_source production ADS backend。",
        "implementation_level": "python_lightweight_runner",
        "backend": "Python in-memory ADS simulator/client with optional AdsLib native preflight",
        "limitation": "ADS_NOTIFICATION remains NOT_IMPLEMENTED in source_lab runtime.",
        "application_protocol": "BECKHOFF_ADS",
        "transport": "TCP",
        "service_types": ("ADS_READ_WRITE", "ADS_NOTIFICATION"),
        "service_type_map": {"polling": "ADS_READ_WRITE", "subscribe": "ADS_NOTIFICATION"},
        "access_modes": ("polling",),
        "current_implementation_level": "python_lightweight_runner",
        "current_backend": "Python in-memory ADS simulator/client with optional AdsLib native preflight",
        "current_limitation": "ADS_READ_WRITE available in source_lab tool runtime; ADS_NOTIFICATION is NOT_IMPLEMENTED.",
        "target_implementation_level": "real_native_runner",
        "target_backend": "AdsLib executable runner",
        "target_limitation": "Tool-layer only; must not be reused as shared_source production backend.",
        "native_required": False,
        "native_library": "AdsLib",
        "cli_aliases": ("beckhoff_ads", "beckhoffads", "ads"),
    },
}

# ── Backward-compatibility alias ──────────────────────────────────────
# DEPRECATED: 新代码应使用 DECLARED_PROTOCOL_CAPABILITIES 获取静态元数据，
# 使用 describe_protocol_runtime_readiness() 判断运行时真实就绪状态。
# 不要将静态 declared capability 误认为 actual runtime readiness。
PROTOCOL_CAPABILITIES = DECLARED_PROTOCOL_CAPABILITIES

# ── Derived lists (computed from DECLARED_PROTOCOL_CAPABILITIES) ────────────────

_POLLING_PROTOCOLS: Final[tuple[str, ...]] = tuple(
    name for name, cap in DECLARED_PROTOCOL_CAPABILITIES.items() if cap["polling"]
)

_SUBSCRIBE_PROTOCOLS: Final[tuple[str, ...]] = tuple(
    name for name, cap in DECLARED_PROTOCOL_CAPABILITIES.items() if cap["subscribe"]
)

_POLLING_PROBE_PROTOCOLS: Final[tuple[str, ...]] = _POLLING_PROTOCOLS
_STREAMING_PROBE_PROTOCOLS: Final[tuple[str, ...]] = (
    "mqtt",
    "iec61850_report",
    "iec61850_goose",
    "iec61850_sv",
)


# ── Service-level capability registry (canonical triple store) ─────────
# Each key is ``(application_protocol, service_type, transport)``.

SERVICE_CAPABILITIES: Final[dict[tuple[str, str, str], _ProtoCap]] = {
    # ── OPC UA ─────────────────────────────────────────────────────
    ("OPC_UA", "READ", "TCP"): {
        "access_mode": "polling",
        "current_implementation_level": "real_native_runner",
        "current_backend": "open62541 executable runner",
        "current_limitation": "",
        "target_implementation_level": "real_native_runner",
        "target_backend": "open62541 executable runner",
        "target_limitation": "",
        "native_required": True,
        "native_library": "open62541",
    },
    ("OPC_UA", "SUBSCRIBE", "TCP"): {
        "access_mode": "streaming",
        "current_implementation_level": "real_native_runner",
        "current_backend": "open62541 executable runner",
        "current_limitation": "",
        "target_implementation_level": "real_native_runner",
        "target_backend": "open62541 executable runner",
        "target_limitation": "",
        "native_required": True,
        "native_library": "open62541",
    },
    ("OPC_UA", "WRITE", "TCP"): {
        "access_mode": "write",
        "current_implementation_level": "real_native_runner",
        "current_backend": "open62541 executable runner via stdin WRITE command",
        "current_limitation": "Single-node writes only. Batch writes are sequential. No subscription-based write.",
        "target_implementation_level": "real_native_runner",
        "target_backend": "open62541 executable runner via stdin WRITE command",
        "target_limitation": "",
        "native_required": True,
        "native_library": "open62541",
    },
    # ── Modbus ─────────────────────────────────────────────────────
    ("MODBUS", "TCP_READ", "TCP"): {
        "access_mode": "polling",
        "current_implementation_level": "real_native_runner",
        "current_backend": "libmodbus executable runner",
        "current_limitation": "",
        "target_implementation_level": "real_native_runner",
        "target_backend": "libmodbus executable runner",
        "target_limitation": "",
        "native_required": True,
        "native_library": "libmodbus",
    },
    ("MODBUS", "TCP_WRITE", "TCP"): {
        "access_mode": "write",
        "current_implementation_level": "real_native_runner",
        "current_backend": "libmodbus executable runner via stdin WRITE command (FC06)",
        "current_limitation": "Single-register writes only (FC06). No FC05/FC15/FC16 support yet.",
        "target_implementation_level": "real_native_runner",
        "target_backend": "libmodbus executable runner via stdin WRITE command",
        "target_limitation": "",
        "native_required": True,
        "native_library": "libmodbus",
    },
    ("MODBUS", "RTU_READ", "SERIAL"): {
        "access_mode": "polling",
        "current_implementation_level": "real_native_runner",
        "current_backend": "libmodbus executable runner",
        "current_limitation": "",
        "target_implementation_level": "real_native_runner",
        "target_backend": "libmodbus executable runner",
        "target_limitation": "",
        "native_required": True,
        "native_library": "libmodbus",
    },
    # ── IEC 101 ────────────────────────────────────────────────────
    ("IEC101", "INTERROGATION", "SERIAL"): {
        "access_mode": "polling",
        "current_implementation_level": "real_native_runner",
        "current_backend": "lib60870-C executable runner",
        "current_limitation": "",
        "target_implementation_level": "real_native_runner",
        "target_backend": "lib60870-C executable runner",
        "target_limitation": "",
        "native_required": True,
        "native_library": "lib60870",
    },
    ("IEC101", "SPONTANEOUS", "SERIAL"): {
        "access_mode": "streaming",
        "current_implementation_level": "real_native_runner",
        "current_backend": "lib60870-C executable runner",
        "current_limitation": "",
        "target_implementation_level": "real_native_runner",
        "target_backend": "lib60870-C executable runner",
        "target_limitation": "",
        "native_required": True,
        "native_library": "lib60870",
    },
    # ── IEC 104 ────────────────────────────────────────────────────
    ("IEC104", "INTERROGATION", "TCP"): {
        "access_mode": "polling",
        "current_implementation_level": "real_native_runner",
        "current_backend": "lib60870-C executable runner",
        "current_limitation": "",
        "target_implementation_level": "real_native_runner",
        "target_backend": "lib60870-C executable runner",
        "target_limitation": "",
        "native_required": True,
        "native_library": "lib60870",
    },
    ("IEC104", "SPONTANEOUS", "TCP"): {
        "access_mode": "streaming",
        "current_implementation_level": "real_native_runner",
        "current_backend": "lib60870-C executable runner",
        "current_limitation": "",
        "target_implementation_level": "real_native_runner",
        "target_backend": "lib60870-C executable runner",
        "target_limitation": "",
        "native_required": True,
        "native_library": "lib60870",
    },
    # ── IEC 61850 MMS Read ─────────────────────────────────────────
    ("IEC61850", "MMS_READ", "TCP"): {
        "access_mode": "polling",
        "current_implementation_level": "real_native_runner",
        "current_backend": "libiec61850 executable runner",
        "current_limitation": "",
        "target_implementation_level": "real_native_runner",
        "target_backend": "libiec61850 executable runner",
        "target_limitation": "",
        "native_required": True,
        "native_library": "libiec61850",
    },
    # ── IEC 61850 MMS Write ────────────────────────────────────────
    ("IEC61850", "MMS_WRITE", "TCP"): {
        "access_mode": "write",
        "current_implementation_level": "real_native_runner",
        "current_backend": "libiec61850 executable runner via stdin WRITE command",
        "current_limitation": "Direct MMS write only (SP/CF attributes). All 7 types verified: BOOLEAN, INT32, UINT32, INT64, FLOAT32, FLOAT64, VISIBLE_STRING. No SBO/Oper/Select/Cancel.",
        "target_implementation_level": "real_native_runner",
        "target_backend": "libiec61850 executable runner via stdin WRITE command",
        "target_limitation": "",
        "native_required": True,
        "native_library": "libiec61850",
    },
    # ── IEC 61850 Report ───────────────────────────────────────────
    ("IEC61850", "REPORT", "TCP"): {
        "access_mode": "streaming",
        "current_implementation_level": "real_native_runner",
        "current_backend": "libiec61850 report_runner via stdin/stdout",
        "current_limitation": "URCB only, no BRCB. Minimal reconnect (max 2 attempts). No dynamic DataSet discovery.",
        "target_implementation_level": "real_native_runner",
        "target_backend": "libiec61850 executable runner",
        "target_limitation": "",
        "native_required": True,
        "native_library": "libiec61850",
    },
    # ── IEC 61850 GOOSE ────────────────────────────────────────────
    ("IEC61850", "GOOSE", "ETHERNET_L2"): {
        "access_mode": "streaming",
        "current_implementation_level": "real_native_runner",
        "current_backend": "libiec61850 GOOSE publisher/subscriber runners",
        "current_limitation": "Requires Linux L2 raw socket permissions (CAP_NET_RAW) and a usable interface.",
        "target_implementation_level": "real_native_runner",
        "target_backend": "libiec61850 GOOSE executable runner",
        "target_limitation": "",
        "native_required": True,
        "native_library": "libiec61850",
    },
    # ── IEC 61850 Sampled Values ───────────────────────────────────
    ("IEC61850", "SV", "ETHERNET_L2"): {
        "access_mode": "streaming",
        "current_implementation_level": "real_native_runner",
        "current_backend": "libiec61850 SV publisher/subscriber runners",
        "current_limitation": "Requires Linux L2 raw socket permissions (CAP_NET_RAW) and a usable interface.",
        "target_implementation_level": "real_native_runner",
        "target_backend": "libiec61850 SV executable runner",
        "target_limitation": "",
        "native_required": True,
        "native_library": "libiec61850",
    },
    # ── MQTT ───────────────────────────────────────────────────────
    ("MQTT", "SUBSCRIBE", "MQTT"): {
        "access_mode": "streaming",
        "current_implementation_level": "python_lightweight_runner",
        "current_backend": "Python socket (MQTT handshake)",
        "current_limitation": "Python lightweight, no Paho C native backend.",
        "target_implementation_level": "python_lightweight_runner",
        "target_backend": "Python MQTT runner (mature client library)",
        "target_limitation": "MQTT is not required to be native C runner.",
        "native_required": False,
        "native_library": None,
    },
    # ── HTTP REST ──────────────────────────────────────────────────
    ("HTTP_REST", "REQUEST", "HTTP"): {
        "access_mode": "polling",
        "current_implementation_level": "python_lightweight_runner",
        "current_backend": "Python urllib (HTTP GET)",
        "current_limitation": "Python lightweight, not validated against full HTTP REST standard.",
        "target_implementation_level": "python_lightweight_runner",
        "target_backend": "Python HTTP runner (mature HTTP library)",
        "target_limitation": "HTTP_REST is not required to be native C runner.",
        "native_required": False,
        "native_library": None,
    },
    ("HTTP_REST", "REQUEST", "HTTPS"): {
        "access_mode": "polling",
        "current_implementation_level": "python_lightweight_runner",
        "current_backend": "Python urllib (HTTP GET)",
        "current_limitation": "Python lightweight; HTTPS not yet validated.",
        "target_implementation_level": "python_lightweight_runner",
        "target_backend": "Python HTTP runner (mature HTTP library)",
        "target_limitation": "HTTP_REST is not required to be native C runner.",
        "native_required": False,
        "native_library": None,
    },
    ("BECKHOFF_ADS", "ADS_READ_WRITE", "TCP"): {
        "access_mode": "polling",
        "current_implementation_level": "python_lightweight_runner",
        "current_backend": "Python in-memory ADS simulator/client with optional AdsLib native preflight",
        "current_limitation": "source_lab tool runtime only; not a production ADS client.",
        "target_implementation_level": "real_native_runner",
        "target_backend": "AdsLib executable runner",
        "target_limitation": "",
        "native_required": False,
        "native_library": "AdsLib",
    },
    ("BECKHOFF_ADS", "ADS_NOTIFICATION", "TCP"): {
        "access_mode": "streaming",
        "current_implementation_level": "planned_native_runner",
        "current_backend": "notification runner not implemented",
        "current_limitation": "ADS notification path is NOT_IMPLEMENTED in source_lab runtime.",
        "target_implementation_level": "real_native_runner",
        "target_backend": "AdsLib notification runner",
        "target_limitation": "",
        "native_required": True,
        "native_library": "AdsLib",
    },
}

# ── Canonical application protocol constants ──────────────────────────

APPLICATION_PROTOCOLS: Final[tuple[str, ...]] = (
    "OPC_UA",
    "MODBUS",
    "IEC101",
    "IEC104",
    "IEC61850",
    "MQTT",
    "HTTP_REST",
    "BECKHOFF_ADS",
)

SERVICE_TYPES: Final[tuple[str, ...]] = (
    "READ",
    "SUBSCRIBE",
    "TCP_READ",
    "TCP_WRITE",
    "RTU_READ",
    "INTERROGATION",
    "SPONTANEOUS",
    "MMS_READ",
    "REPORT",
    "GOOSE",
    "SV",
    "REQUEST",
    "ADS_READ_WRITE",
    "ADS_NOTIFICATION",
)

TRANSPORT_TYPES: Final[tuple[str, ...]] = (
    "TCP",
    "SERIAL",
    "ETHERNET_L2",
    "MQTT",
    "HTTP",
    "HTTPS",
)

# ── Protocol aliases ──────────────────────────────────────────────────

_PROTOCOL_ALIASES: Final[dict[str, str]] = {
    # OPC UA
    "opcua": "opcua",
    # Modbus
    "modbustcp": "modbus_tcp",
    "modbus_tcp": "modbus_tcp",
    "modbusrtu": "modbus_rtu",
    "modbus_rtu": "modbus_rtu",
    # IEC 101
    "iec101": "iec101",
    # IEC 104
    "iec104": "iec104",
    # IEC 61850 MMS
    "iec61850mms": "iec61850_mms",
    "iec61850_mms": "iec61850_mms",
    # IEC 61850 Report
    "iec61850report": "iec61850_report",
    "iec61850_report": "iec61850_report",
    # MQTT
    "mqtt": "mqtt",
    # HTTP REST
    "http": "http_rest",
    "httprest": "http_rest",
    "http_rest": "http_rest",
    # Beckhoff ADS
    "beckhoffads": "beckhoff_ads",
    "beckhoff_ads": "beckhoff_ads",
    "ads": "beckhoff_ads",
    # IEC 61850 L2 streaming aliases.
    "iec61850goose": "iec61850_goose",
    "iec61850_goose": "iec61850_goose",
    "iec61850sv": "iec61850_sv",
    "iec61850_sv": "iec61850_sv",
}


def _normalize_alias_key(value: str) -> str:
    """Strip whitespace, lower-case, remove all separators."""
    return value.strip().lower().replace("-", "").replace("_", "")


# ── Legacy name resolution (backward compat) ─────────────────────────

def normalize_protocol(value: str) -> str:
    """Normalise an arbitrary protocol string to a canonical registry key.

    Args:
        value: Raw protocol name from CLI or fixture.

    Returns:
        Canonical key in ``DECLARED_PROTOCOL_CAPABILITIES``.

    Raises:
        ValueError: Protocol string not recognised.
    """
    key = _normalize_alias_key(value)
    if key not in _PROTOCOL_ALIASES:
        raise ValueError(f"unsupported protocol: {value}")
    return _PROTOCOL_ALIASES[key]


def list_supported_protocols() -> tuple[str, ...]:
    """返回所有已注册协议名的不可变元组。

    Returns:
        已注册协议名的元组，顺序与 DECLARED_PROTOCOL_CAPABILITIES 的键一致。
    """
    return tuple(DECLARED_PROTOCOL_CAPABILITIES.keys())


def get_protocol_capability(protocol: str) -> dict[str, object]:
    """Return full capability metadata dict for a protocol name.

    Args:
        protocol: Normalised protocol name.

    Returns:
        Dict with implementation-level, backend, access-mode, triple fields.

    Raises:
        ValueError: Protocol not in registry.
    """
    normalized = normalize_protocol(protocol)
    cap = DECLARED_PROTOCOL_CAPABILITIES.get(normalized)
    if cap is None:
        msg = (
            f"protocol {normalized!r} is defined as an alias but has no "
            f"capability entry (deprecated alias or planned service type)."
        )
        raise ValueError(msg)
    return cap


# ── Legacy implementation-level access (backward compat) ──────────────

def get_implementation_level(protocol: str) -> str:
    """Return the **current** implementation level for a protocol.

    This is a backward-compat alias for ``get_current_implementation_level()``.
    """
    cap = get_protocol_capability(protocol)
    level = cap.get("implementation_level")
    if level is None:
        level = cap.get("current_implementation_level", "")
    assert isinstance(level, str)
    return level


def get_backend(protocol: str) -> str:
    """Return the current backend description (backward compat)."""
    cap = get_protocol_capability(protocol)
    backend = cap.get("backend")
    if backend is None:
        backend = cap.get("current_backend", "")
    assert isinstance(backend, str)
    return backend


def get_limitation(protocol: str) -> str:
    """Return the current limitation description (backward compat)."""
    cap = get_protocol_capability(protocol)
    limitation = cap.get("limitation")
    if limitation is None:
        limitation = cap.get("current_limitation", "")
    assert isinstance(limitation, str)
    return limitation


# ── Current / target implementation level accessors ───────────────────

def get_current_implementation_level(protocol: str) -> str:
    """Return the **current** implementation level for a protocol."""
    cap = get_protocol_capability(protocol)
    level = cap.get("current_implementation_level", "")
    assert isinstance(level, str)
    return level


def get_target_implementation_level(protocol: str) -> str:
    """Return the **target** implementation level for a protocol."""
    cap = get_protocol_capability(protocol)
    level = cap.get("target_implementation_level", "")
    assert isinstance(level, str)
    return level


# ── Access mode helpers ──────────────────────────────────────────────

def supports_access_mode(protocol: str, access_mode: str) -> bool:
    """Check whether a protocol supports a given access mode."""
    normalized = normalize_protocol(protocol)
    cap = DECLARED_PROTOCOL_CAPABILITIES.get(normalized)
    if cap is None:
        return False
    mode = access_mode.strip().lower()
    val = cap.get(mode, False)
    assert isinstance(val, bool)
    return val


def probe_mode_for_protocol(protocol: str) -> str | None:
    """Return the probe mode (``polling`` or ``streaming``) for a protocol."""
    normalized = normalize_protocol(protocol)
    cap = DECLARED_PROTOCOL_CAPABILITIES.get(normalized)
    if cap is None:
        return None
    polling_val = cap.get("polling", False)
    subscribe_val = cap.get("subscribe", False)
    if isinstance(polling_val, bool) and polling_val:
        return "polling"
    if isinstance(subscribe_val, bool) and subscribe_val:
        return "streaming"
    return None


# ── Service triple helpers ───────────────────────────────────────────

def list_service_capabilities() -> tuple[tuple[str, str, str], ...]:
    """Return all registered ``(app_protocol, service_type, transport)`` triples."""
    return tuple(SERVICE_CAPABILITIES.keys())


def get_service_capability(
    app_protocol: str,
    service_type: str,
    transport: str,
) -> dict[str, object]:
    """Return the capability dict for a service triple.

    Raises:
        ValueError: Triple not registered.
    """
    key = (app_protocol, service_type, transport)
    cap = SERVICE_CAPABILITIES.get(key)
    if cap is None:
        raise ValueError(
            f"no service capability for ({app_protocol}, {service_type}, {transport})"
        )
    return cap


def resolve_service_triple(
    protocol: str,
    access_mode: str | None = None,
) -> tuple[str, str, str] | None:
    """Resolve a legacy protocol name (+optional access mode) to a canonical triple.

    Returns ``(app_protocol, service_type, transport)`` or ``None`` if the
    protocol has no matching service capability.

    The ``access_mode`` parameter is used only when the protocol supports
    multiple service types; it is ignored (but still accepted) for protocols
    that have exactly one service type.
    """
    normalized = normalize_protocol(protocol)
    cap = DECLARED_PROTOCOL_CAPABILITIES.get(normalized)
    if cap is None:
        return None
    app_protocol = cap.get("application_protocol", "")
    transport = cap.get("transport", "")
    assert isinstance(app_protocol, str)
    assert isinstance(transport, str)

    # Use service_type_map when access_mode is given
    service_type_map = cap.get("service_type_map")
    if isinstance(service_type_map, dict) and access_mode is not None:
        st = service_type_map.get(access_mode)
        if st is not None:
            assert isinstance(st, str)
            return (app_protocol, st, transport)

    # Fall back to the first service type
    service_types = cap.get("service_types")
    if isinstance(service_types, (tuple, list)) and service_types:
        st = str(service_types[0])
        return (app_protocol, st, transport)

    return None


# ── RunnerInfo — runtime implementation-level metadata ────────────────


class RunnerInfo:
    """运行时 runner 构建结果，包含实际实现级别和声明的实现级别。

    用于区分 ``declared_implementation_level``（来自 DECLARED_PROTOCOL_CAPABILITIES
    静态注册表）与 ``actual_implementation_level``（当前运行时实际可用的实现级别）。
    当 native binary 不存在或不可执行时，``actual_implementation_level`` 为
    ``python_lightweight``，而 ``declared_implementation_level`` 仍保持
    ``real_native_runner``。

    readiness gate 必须使用 ``is_native_ready`` 和 ``actual_runtime_availability``
    判断真实可用性，不得仅依赖 DECLARED_PROTOCOL_CAPABILITIES 静态值。

    Args:
        runner: 实际构建的 CapacityRunner 实例。
        actual_implementation_level: 运行时实际实现级别。
        declared_implementation_level: DECLARED_PROTOCOL_CAPABILITIES 声明的目标级别。
        fallback_reason: 如果发生了 fallback，说明 fallback 原因；否则为 None。
        native_check_error: native 不可用时的检测错误信息。无错误时为 None。
            native 可用时此字段为 None。
    """

    def __init__(
        self,
        runner: CapacityRunner,
        actual_implementation_level: str,
        declared_implementation_level: str,
        fallback_reason: str | None = None,
        native_check_error: str | None = None,
    ) -> None:
        self._runner = runner
        self.actual_implementation_level = actual_implementation_level
        self.declared_implementation_level = declared_implementation_level
        self.fallback_reason = fallback_reason
        # native 检测失败的错误信息，用于 readiness gate 诊断
        self.native_check_error: str | None = native_check_error

    @property
    def runner(self) -> CapacityRunner:
        """返回底层 CapacityRunner 实例。"""
        return self._runner

    @property
    def actual_runner(self) -> str:
        """返回实际使用的 runner 名称（如 "opcua_open62541"、"python_lightweight"）。

        供 readiness gate 诊断：能清楚区分当前实际使用哪个 runner，
        而不是仅显示实现级别标签。
        """
        return getattr(self._runner, "name", self._runner.__class__.__name__)

    @property
    def actual_runtime_availability(self) -> str:
        """返回运行时可用性标签。

        Returns:
            ``"available_native"`` — native runner 运行时可用。
            ``"degraded_python_fallback"`` — native 不可用，已降级为 Python fallback。
            ``"unavailable"`` — 无可用 runner（runner 为 None 的边界情况）。

        readiness gate 必须检查此字段，不得仅依赖
        DECLARED_PROTOCOL_CAPABILITIES 静态声明。
        """
        if self.actual_implementation_level == "real_native_runner":
            return "available_native"
        if self._runner is not None:
            return "degraded_python_fallback"
        return "unavailable"

    def __getattr__(self, name: str) -> Any:
        """将未定义属性访问委派给底层 runner，保持向后兼容。

        使得调用方可以通过 RunnerInfo 实例直接访问 CapacityRunner
        的属性和方法（如 .name、.run_worker() 等），无需显式拆包。
        """
        return getattr(self._runner, name)

    @property
    def is_native_ready(self) -> bool:
        """返回 native runner 是否在运行时真实可用。

        readiness gate 应使用此属性判断，而非直接读取
        DECLARED_PROTOCOL_CAPABILITIES 中的静态 implementation_level。
        """
        return self.actual_implementation_level == "real_native_runner"

    def __repr__(self) -> str:
        return (
            f"RunnerInfo("
            f"actual={self.actual_implementation_level}, "
            f"declared={self.declared_implementation_level}, "
            f"runner={self.actual_runner}, "
            f"availability={self.actual_runtime_availability}, "
            f"fallback={self.fallback_reason!r}, "
            f"native_error={self.native_check_error!r})"
        )


@dataclass(frozen=True, slots=True)
class RuntimeReadiness:
    """Protocol runtime readiness snapshot for one access mode."""

    protocol: str
    access_mode: str
    runner: CapacityRunner | SubscriptionRunner
    declared_implementation_level: str
    actual_implementation_level: str
    actual_runtime_availability: str
    runtime_constraint_tags: tuple[str, ...] = ()
    fallback_reason: str | None = None
    native_check_error: str | None = None

    @property
    def is_native_ready(self) -> bool:
        """Whether the runtime is truly using a native runner right now."""
        return self.actual_implementation_level == "real_native_runner"


class _UnavailableSubscriptionRunner:
    """用于显式表达未实现订阅路径的占位 runner。"""

    def __init__(self, name: str) -> None:
        self.name = name

    def run_worker(
        self,
        worker_index: int,
        specs: tuple,
        config: SubscribeScanConfig,
    ) -> SubscribeWorkerRawStats:
        """占位 runner 不提供真实订阅，调用即显式失败。"""
        raise RuntimeError(f"{self.name} is not implemented")


def _capacity_runtime_readiness(protocol: str) -> RuntimeReadiness:
    info = build_capacity_runner(protocol)
    return RuntimeReadiness(
        protocol=normalize_protocol(protocol),
        access_mode="polling",
        runner=info.runner,
        declared_implementation_level=info.declared_implementation_level,
        actual_implementation_level=info.actual_implementation_level,
        actual_runtime_availability=info.actual_runtime_availability,
        fallback_reason=info.fallback_reason,
        native_check_error=info.native_check_error,
    )


def _subscription_runtime_readiness(protocol: str) -> RuntimeReadiness:
    normalized = normalize_protocol(protocol)
    declared_level = get_current_implementation_level(normalized)
    runner = build_subscription_runner(normalized)

    if normalized == "opcua":
        from tools.source_lab.access.runners.open62541_subscription import _resolve_runner_path

        runner_path = _resolve_runner_path()
        if runner_path.exists():
            return RuntimeReadiness(
                protocol=normalized,
                access_mode="streaming",
                runner=runner,
                declared_implementation_level=declared_level,
                actual_implementation_level="real_native_runner",
                actual_runtime_availability="available_native",
            )
        return RuntimeReadiness(
            protocol=normalized,
            access_mode="streaming",
            runner=runner,
            declared_implementation_level=declared_level,
            actual_implementation_level="unavailable",
            actual_runtime_availability="unavailable",
            fallback_reason="native binary not available",
            native_check_error=f"open62541 subscription runner missing: {runner_path}",
        )

    if normalized == "iec61850_report":
        from tools.source_lab.access.runners.iec61850_report import _resolve_runner_path

        runner_path = _resolve_runner_path()
        native_hint = (
            "native report runner requires endpoint opt-in via use_native_report_runner=true"
        )
        if runner_path.exists():
            return RuntimeReadiness(
                protocol=normalized,
                access_mode="streaming",
                runner=runner,
                declared_implementation_level=declared_level,
                actual_implementation_level="python_lightweight_runner",
                actual_runtime_availability="degraded_runtime",
                runtime_constraint_tags=("native_optional", "endpoint_opt_in_required"),
                fallback_reason=native_hint,
            )
        return RuntimeReadiness(
            protocol=normalized,
            access_mode="streaming",
            runner=runner,
            declared_implementation_level=declared_level,
            actual_implementation_level="python_lightweight_runner",
            actual_runtime_availability="degraded_runtime",
            runtime_constraint_tags=("native_optional", "endpoint_opt_in_required"),
            fallback_reason=native_hint,
            native_check_error=f"iec61850_report_runner missing: {runner_path}",
        )

    if normalized in {"iec61850_goose", "iec61850_sv"}:
        from tools.source_lab.access.runners.iec61850_l2_streaming import _find_executable

        executable_name = getattr(runner, "executable_name", "")
        native_path = _find_executable(executable_name) if executable_name else None
        tags = ("controlled_l2_environment", "cap_net_raw_required")
        if native_path is not None:
            return RuntimeReadiness(
                protocol=normalized,
                access_mode="streaming",
                runner=runner,
                declared_implementation_level=declared_level,
                actual_implementation_level="real_native_runner",
                actual_runtime_availability="available_native",
                runtime_constraint_tags=tags,
            )
        return RuntimeReadiness(
            protocol=normalized,
            access_mode="streaming",
            runner=runner,
            declared_implementation_level=declared_level,
            actual_implementation_level="unavailable",
            actual_runtime_availability="unavailable",
            runtime_constraint_tags=tags,
            fallback_reason="native L2 subscriber binary not available",
            native_check_error=f"{executable_name or normalized} missing under native build",
        )

    if normalized in {"iec101", "iec104"}:
        return RuntimeReadiness(
            protocol=normalized,
            access_mode="streaming",
            runner=runner,
            declared_implementation_level=declared_level,
            actual_implementation_level="fake_or_simulated_runner",
            actual_runtime_availability="degraded_runtime",
            runtime_constraint_tags=("gateway_mode", "semantic_probe_only"),
            fallback_reason=(
                "streaming path is currently a lightweight semantic probe, "
                "not a full native spontaneous event engine"
            ),
        )

    if normalized == "mqtt":
        return RuntimeReadiness(
            protocol=normalized,
            access_mode="streaming",
            runner=runner,
            declared_implementation_level=declared_level,
            actual_implementation_level="python_lightweight_runner",
            actual_runtime_availability="available_runtime",
        )

    if normalized == "beckhoff_ads":
        return RuntimeReadiness(
            protocol=normalized,
            access_mode="streaming",
            runner=_UnavailableSubscriptionRunner("beckhoff_ads_notification_runner"),
            declared_implementation_level=declared_level,
            actual_implementation_level="unavailable",
            actual_runtime_availability="unavailable",
            runtime_constraint_tags=("notification_not_implemented",),
            fallback_reason="ADS_NOTIFICATION is not implemented in source_lab runtime",
            native_check_error="AdsLib notification runner is not available in this repository",
        )

    return RuntimeReadiness(
        protocol=normalized,
        access_mode="streaming",
        runner=runner,
        declared_implementation_level=declared_level,
        actual_implementation_level=declared_level,
        actual_runtime_availability="available_runtime",
    )


def describe_protocol_runtime_readiness(protocol: str, access_mode: str) -> RuntimeReadiness:
    """Describe declared vs actual runtime readiness for one protocol/access mode."""

    normalized_mode = access_mode.strip().lower()
    if normalized_mode == "polling":
        return _capacity_runtime_readiness(protocol)
    if normalized_mode in {"subscribe", "streaming"}:
        return _subscription_runtime_readiness(protocol)
    raise ValueError(f"unsupported access mode for runtime readiness: {access_mode}")


# ── Runner factories ─────────────────────────────────────────────────

def build_capacity_runner(protocol: str) -> RunnerInfo:
    """构建一个轮询/capacity runner，返回 RunnerInfo。

    Returns:
        RunnerInfo 包含实际构建的 runner、实际实现级别、声明实现级别。
        调用方应使用 ``info.actual_implementation_level`` 判断真实能力，
        而非仅依赖 DECLARED_PROTOCOL_CAPABILITIES 静态字典。

    Note:
        当 native runner 不可用时，返回 ``python_lightweight`` 的 fallback runner，
        并在 ``fallback_reason`` 中给出原因。返回的 RunnerInfo 的
        ``actual_implementation_level`` 不等于 ``real_native_runner``。
    """
    import logging
    _log = logging.getLogger(__name__)
    normalized = normalize_protocol(protocol)
    declared_level = get_current_implementation_level(normalized)

    # ── Native runner lookup ────────────────────────────────────────────
    from tools.source_lab.access.runners.native_cmd import NativeRunnerUnavailableError
    from tools.source_lab.access.runners.native_runner_map import NATIVE_CAPACITY_RUNNERS
    native_cls = NATIVE_CAPACITY_RUNNERS.get(normalized)
    native_check_error: str | None = None
    if native_cls is not None:
        try:
            native_runner = native_cls()
            native_runner.check_available()
            return RunnerInfo(
                runner=native_runner,
                actual_implementation_level="real_native_runner",
                declared_implementation_level=declared_level,
                fallback_reason=None,
                native_check_error=None,
            )
        except NativeRunnerUnavailableError as exc:
            native_check_error = str(exc)
            _log.warning(
                "Native capacity runner for %s unavailable: %s. "
                "Falling back to Python lightweight runner. "
                "The returned runner does not provide real_native_runner capability.",
                normalized,
                exc,
            )
        except Exception as exc:
            native_check_error = f"{type(exc).__name__}: {exc}"
            _log.warning(
                "Native capacity runner for %s failed check_available with "
                "unexpected error: %s. "
                "Falling back to Python lightweight runner.",
                normalized,
                exc,
            )

    # ── Python lightweight fallback ─────────────────────────────────────
    fallback_reason = "native binary not available"
    runner: CapacityRunner
    if normalized == "opcua":
        runner = OpcUaOpen62541CapacityRunner()
    elif normalized == "modbus_tcp":
        from tools.source_lab.access.runners.modbus_tcp_polling import ModbusTcpPollingRunner
        runner = ModbusTcpPollingRunner()
    elif normalized == "modbus_rtu":
        from tools.source_lab.access.runners.modbus_rtu_polling import ModbusRtuPollingRunner
        runner = ModbusRtuPollingRunner()
    elif normalized == "iec101":
        from tools.source_lab.access.runners.iec101_polling import Iec101PollingRunner
        runner = Iec101PollingRunner()
    elif normalized == "iec104":
        from tools.source_lab.access.runners.iec104_polling import Iec104PollingRunner
        runner = Iec104PollingRunner()
    elif normalized == "iec61850_mms":
        from tools.source_lab.access.runners.iec61850_mms_polling import Iec61850MmsPollingRunner
        runner = Iec61850MmsPollingRunner()
    elif normalized == "http_rest":
        from tools.source_lab.access.runners.http_rest_polling import HttpRestPollingRunner
        runner = HttpRestPollingRunner()
    elif normalized == "beckhoff_ads":
        from tools.source_lab.access.runners.beckhoff_ads_polling import BeckhoffAdsPollingRunner
        runner = BeckhoffAdsPollingRunner()
    else:
        raise ValueError(f"protocol {normalized} does not support polling/capacity")

    return RunnerInfo(
        runner=runner,
        actual_implementation_level="python_lightweight_runner",
        declared_implementation_level=declared_level,
        fallback_reason=fallback_reason,
        native_check_error=native_check_error,
    )


def build_subscription_runner(protocol: str) -> SubscriptionRunner:
    """按协议名称构建订阅 runner。

    Args:
        protocol: 归一化的协议名，如 "opcua"、"iec61850_goose"、"mqtt" 等。

    Returns:
        对应协议的 SubscriptionRunner 实例。

    Raises:
        ValueError: 协议不支持订阅模式。
    """
    normalized = normalize_protocol(protocol)
    if normalized == "opcua":
        return OpcUaOpen62541SubscribeRunner()
    if normalized == "iec101":
        from tools.source_lab.access.runners.iec101_event import Iec101EventRunner
        return Iec101EventRunner()
    if normalized == "iec104":
        from tools.source_lab.access.runners.iec104_event import Iec104EventRunner
        return Iec104EventRunner()
    if normalized == "iec61850_report":
        from tools.source_lab.access.runners.iec61850_report import Iec61850ReportRunner
        return Iec61850ReportRunner()
    if normalized == "iec61850_goose":
        from tools.source_lab.access.runners.iec61850_l2_streaming import (
            Iec61850GooseStreamingRunner,
        )
        return Iec61850GooseStreamingRunner()
    if normalized == "iec61850_sv":
        from tools.source_lab.access.runners.iec61850_l2_streaming import (
            Iec61850SvStreamingRunner,
        )
        return Iec61850SvStreamingRunner()
    if normalized == "mqtt":
        from tools.source_lab.access.runners.mqtt_subscription import MqttSubscriptionRunner
        return MqttSubscriptionRunner()
    if normalized == "beckhoff_ads":
        return _UnavailableSubscriptionRunner("beckhoff_ads_notification_runner")
    raise ValueError(f"protocol {normalized} does not support subscribe")
