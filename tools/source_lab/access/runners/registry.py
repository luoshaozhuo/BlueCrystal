"""Multi-protocol runner registry with unified triple capability model.

The capability model has been upgraded from protocol-only to a triple of
``(application_protocol, service_type, transport)``.  CLI flags and
fixtures that still use legacy protocol names (e.g. ``--protocol modbus_tcp``)
continue to work via a backward-compatibility mapping layer that resolves
old names to the canonical triple.

Structure
---------
- ``PROTOCOL_CAPABILITIES``
    Per-protocol-name registry dict (backward-compat source of truth for
    tests that read ``implementation_level``, ``backend``, access-mode flags).
    Each entry now carries ``application_protocol``, ``transport``,
    ``service_types``, ``current_*`` / ``target_*`` fields.

- ``SERVICE_CAPABILITIES``
    New canonical dict keyed by ``(app_protocol, service_type, transport)``.
    Each entry describes a single service-level capability with its own
    current/target implementation levels, backend, limitation, and native
    requirements.

- ``_PROTOCOL_ALIASES``
    Flat lookup that maps any CLI-visible protocol string (including
    deprecated forms like ``iec61850_goose``) to a canonical key.

Level definitions
-----------------
    real_native_runner         — real C runner via subprocess
    python_lightweight_runner  — Python socket / http / mqtt
    fake_or_simulated_runner   — simulated runner for test closure
    semantic_probe_only        — minimum protocol-semantic probe
    planned_native_runner      — planned but not yet implemented
"""

from __future__ import annotations

from typing import Final

from tools.source_lab.access.runners.base import CapacityRunner, SubscriptionRunner
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

PROTOCOL_CAPABILITIES: Final[dict[str, _ProtoCap]] = {
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
        "production_client_write": False,
        "simulator_write_injection": False,
        "supported_write_operations": (),
        "unsupported_write_operations": ("FC05_single_coil_write", "FC06_single_register_write", "FC15_multi_coil_write", "FC16_multi_register_write"),
        "write_limitation": "Modbus write (FC05/06/15/16) not implemented yet.",
        "implementation_level": "real_native_runner",
        "backend": "libmodbus executable runner",
        "limitation": "",
        "application_protocol": "MODBUS",
        "transport": "SERIAL",
        "service_types": ("RTU_READ",),
        "service_type_map": {"polling": "RTU_READ"},
        "access_modes": ("polling",),
        "current_implementation_level": "real_native_runner",
        "current_backend": "libmodbus executable runner",
        "current_limitation": "",
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
        "production_client_write": False,
        "simulator_write_injection": False,
        "supported_write_operations": (),
        "unsupported_write_operations": ("C_SC", "C_SE", "C_BO"),
        "write_limitation": "IEC 101 C_SC/C_SE/C_BO not implemented yet.",
        "implementation_level": "real_native_runner",
        "backend": "lib60870-C executable runner",
        "limitation": "",
        "application_protocol": "IEC101",
        "transport": "SERIAL",
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
        "cli_aliases": ("iec101", "iec-101"),
    },
    # ── IEC 104 ────────────────────────────────────────────────────
    "iec104": {
        "polling": True,
        "subscribe": True,
        "probe": True,
        "write": False,
        "production_client_write": False,
        "simulator_write_injection": False,
        "supported_write_operations": (),
        "unsupported_write_operations": ("C_SC", "C_SE", "C_BO"),
        "write_limitation": "IEC 104 C_SC/C_SE/C_BO not implemented yet.",
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
        "write": False,
        "production_client_write": False,
        "simulator_write_injection": False,
        "supported_write_operations": (),
        "unsupported_write_operations": ("Oper_select", "Oper_cancel", "Oper_execute"),
        "write_limitation": "IEC 61850 MMS control (Oper/Select/Cancel) not implemented yet.",
        "implementation_level": "real_native_runner",
        "backend": "libiec61850 executable runner",
        "limitation": "",
        "application_protocol": "IEC61850",
        "transport": "TCP",
        "service_types": ("MMS_READ",),
        "service_type_map": {"polling": "MMS_READ"},
        "access_modes": ("polling",),
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
        "production_client_write": False,
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
        "current_backend": "libiec61850 executable runner",
        "current_limitation": "",
        "target_implementation_level": "real_native_runner",
        "target_backend": "libiec61850 executable runner",
        "target_limitation": "",
        "native_required": True,
        "native_library": "libiec61850",
        "cli_aliases": ("iec61850_report", "iec61850report"),
    },
    # ── MQTT ───────────────────────────────────────────────────────
    "mqtt": {
        "polling": False,
        "subscribe": True,
        "probe": True,
        "write": False,
        "production_client_write": False,
        "simulator_write_injection": False,
        "supported_write_operations": (),
        "unsupported_write_operations": ("MQTT_publish",),
        "write_limitation": "MQTT publish (write) not implemented yet.",
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
        "simulator_write_injection": False,
        "supported_write_operations": (),
        "unsupported_write_operations": ("HTTP_POST", "HTTP_PUT", "HTTP_PATCH", "HTTP_DELETE"),
        "write_limitation": "HTTP REST POST/PUT/PATCH (write) not implemented yet.",
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
}

# ── Derived lists (computed from PROTOCOL_CAPABILITIES) ────────────────

_POLLING_PROTOCOLS: Final[tuple[str, ...]] = tuple(
    name for name, cap in PROTOCOL_CAPABILITIES.items() if cap["polling"]
)

_SUBSCRIBE_PROTOCOLS: Final[tuple[str, ...]] = tuple(
    name for name, cap in PROTOCOL_CAPABILITIES.items() if cap["subscribe"]
)

_POLLING_PROBE_PROTOCOLS: Final[tuple[str, ...]] = _POLLING_PROTOCOLS
_STREAMING_PROBE_PROTOCOLS: Final[tuple[str, ...]] = (
    "mqtt",
    "iec61850_report",
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
    # ── IEC 61850 Report ───────────────────────────────────────────
    ("IEC61850", "REPORT", "TCP"): {
        "access_mode": "streaming",
        "current_implementation_level": "real_native_runner",
        "current_backend": "libiec61850 executable runner",
        "current_limitation": "",
        "target_implementation_level": "real_native_runner",
        "target_backend": "libiec61850 executable runner",
        "target_limitation": "",
        "native_required": True,
        "native_library": "libiec61850",
    },
    # ── IEC 61850 GOOSE ────────────────────────────────────────────
    ("IEC61850", "GOOSE", "ETHERNET_L2"): {
        "access_mode": "streaming",
        "current_implementation_level": "planned_native_runner",
        "current_backend": "not implemented",
        "current_limitation": "Not yet implemented; planned via libiec61850.",
        "target_implementation_level": "real_native_runner",
        "target_backend": "libiec61850 GOOSE executable runner",
        "target_limitation": "",
        "native_required": True,
        "native_library": "libiec61850",
    },
    # ── IEC 61850 Sampled Values ───────────────────────────────────
    ("IEC61850", "SV", "ETHERNET_L2"): {
        "access_mode": "streaming",
        "current_implementation_level": "planned_native_runner",
        "current_backend": "not implemented",
        "current_limitation": "Not yet implemented; planned via libiec61850.",
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
    # Deprecated aliases — resolve to IEC61850 family stub names
    # These do NOT have PROTOCOL_CAPABILITIES entries (no standalone runner).
    # They document that GOOSE/SV are IEC61850 service types, not top-level
    # protocols.  Attempts to call get_protocol_capability() on them will
    # raise ValueError with a clear message.
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
        Canonical key in ``PROTOCOL_CAPABILITIES``.

    Raises:
        ValueError: Protocol string not recognised.
    """
    key = _normalize_alias_key(value)
    if key not in _PROTOCOL_ALIASES:
        raise ValueError(f"unsupported protocol: {value}")
    return _PROTOCOL_ALIASES[key]


def list_supported_protocols() -> tuple[str, ...]:
    """Return the list of fully registered protocol names.

    Deprecated aliases (iec61850_goose, iec61850_sv) are **not** included;
    they resolve through ``normalize_protocol()`` but have no standalone
    runner implementation.
    """
    return tuple(PROTOCOL_CAPABILITIES.keys())


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
    cap = PROTOCOL_CAPABILITIES.get(normalized)
    if cap is None:
        msg = (
            f"protocol {normalized!r} is defined as an alias but has no "
            f"capability entry (deprecated alias or planned service type)."
        )
        if normalized in ("iec61850_goose", "iec61850_sv"):
            msg += (
                f" {normalized} is a deprecated alias for IEC61850 service type. "
                f"Use --protocol IEC61850 with --service-type (planned CLI extension) instead."
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
    cap = PROTOCOL_CAPABILITIES.get(normalized)
    if cap is None:
        return False
    mode = access_mode.strip().lower()
    val = cap.get(mode, False)
    assert isinstance(val, bool)
    return val


def probe_mode_for_protocol(protocol: str) -> str | None:
    """Return the probe mode (``polling`` or ``streaming``) for a protocol."""
    normalized = normalize_protocol(protocol)
    cap = PROTOCOL_CAPABILITIES.get(normalized)
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
    cap = PROTOCOL_CAPABILITIES.get(normalized)
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


# ── Runner factories ─────────────────────────────────────────────────

def build_capacity_runner(protocol: str) -> CapacityRunner:
    """Build a polling/capacity runner.

    Returns a native runner if the native executable is compiled and available;
    otherwise falls back to the Python lightweight runner.
    """
    normalized = normalize_protocol(protocol)

    # ── Native runner lookup ────────────────────────────────────────────
    from tools.source_lab.access.runners.native_runner_map import NATIVE_CAPACITY_RUNNERS
    native_cls = NATIVE_CAPACITY_RUNNERS.get(normalized)
    if native_cls is not None:
        try:
            return native_cls()
        except RuntimeError:
            pass  # fall through to Python lightweight

    # ── Python lightweight fallback ─────────────────────────────────────
    if normalized == "opcua":
        return OpcUaOpen62541CapacityRunner()
    if normalized == "modbus_tcp":
        from tools.source_lab.access.runners.modbus_tcp_polling import ModbusTcpPollingRunner
        return ModbusTcpPollingRunner()
    if normalized == "modbus_rtu":
        from tools.source_lab.access.runners.modbus_rtu_polling import ModbusRtuPollingRunner
        return ModbusRtuPollingRunner()
    if normalized == "iec101":
        from tools.source_lab.access.runners.iec101_polling import Iec101PollingRunner
        return Iec101PollingRunner()
    if normalized == "iec104":
        from tools.source_lab.access.runners.iec104_polling import Iec104PollingRunner
        return Iec104PollingRunner()
    if normalized == "iec61850_mms":
        from tools.source_lab.access.runners.iec61850_mms_polling import Iec61850MmsPollingRunner
        return Iec61850MmsPollingRunner()
    if normalized == "http_rest":
        from tools.source_lab.access.runners.http_rest_polling import HttpRestPollingRunner
        return HttpRestPollingRunner()
    raise ValueError(f"protocol {normalized} does not support polling/capacity")


def build_subscription_runner(protocol: str) -> SubscriptionRunner:
    """Build a subscribe runner."""
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
    if normalized == "mqtt":
        from tools.source_lab.access.runners.mqtt_subscription import MqttSubscriptionRunner
        return MqttSubscriptionRunner()
    raise ValueError(f"protocol {normalized} does not support subscribe")
