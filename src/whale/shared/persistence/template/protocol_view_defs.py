"""协议端点参数视图 — 以 endpoint 为中心，将范式的参数值表展平为视图.

每个视图将 scada_endpoint_param_value 中的值通过 scada_protocol_param_def.param_key
转换为列。方便查询和报表，不替代底层范式表。
"""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.engine import Engine

# fmt: off
_PROTOCOL_VIEW_DEFS: dict[str, str] = {
    "v_scada_endpoint_opcua": """
        SELECT
            ep.endpoint_id,
            ep.ied_id,
            ep.application_protocol,
            ep.service_type,
            ep.transport,
            ep.host,
            ep.port,
            ep.namespace_uri,
            ep.security_policy,
            ep.security_mode,
            p.param_key,
            COALESCE(pv.value_text, CAST(pv.value_int AS TEXT), CAST(pv.value_float AS TEXT), CAST(pv.value_bool AS TEXT)) AS param_value
        FROM scada_communication_endpoint AS ep
        LEFT JOIN scada_endpoint_param_value AS pv ON pv.endpoint_id = ep.endpoint_id
        LEFT JOIN scada_protocol_param_def AS p ON p.param_def_id = pv.param_def_id
        WHERE ep.application_protocol = 'OPC_UA'
    """,
    "v_scada_endpoint_modbus_tcp": """
        SELECT
            ep.endpoint_id,
            ep.ied_id,
            ep.application_protocol,
            ep.service_type,
            ep.transport,
            ep.host,
            ep.port,
            p.param_key,
            COALESCE(pv.value_text, CAST(pv.value_int AS TEXT), CAST(pv.value_float AS TEXT), CAST(pv.value_bool AS TEXT)) AS param_value
        FROM scada_communication_endpoint AS ep
        LEFT JOIN scada_endpoint_param_value AS pv ON pv.endpoint_id = ep.endpoint_id
        LEFT JOIN scada_protocol_param_def AS p ON p.param_def_id = pv.param_def_id
        WHERE ep.application_protocol = 'MODBUS' AND (ep.service_type IS NULL OR ep.service_type = 'TCP_READ')
          AND ep.transport = 'TCP'
    """,
    "v_scada_endpoint_modbus_rtu": """
        SELECT
            ep.endpoint_id, ep.ied_id, ep.application_protocol, ep.service_type, ep.transport,
            ep.host, ep.port,
            p.param_key,
            COALESCE(pv.value_text, CAST(pv.value_int AS TEXT), CAST(pv.value_float AS TEXT), CAST(pv.value_bool AS TEXT)) AS param_value
        FROM scada_communication_endpoint AS ep
        LEFT JOIN scada_endpoint_param_value AS pv ON pv.endpoint_id = ep.endpoint_id
        LEFT JOIN scada_protocol_param_def AS p ON p.param_def_id = pv.param_def_id
        WHERE ep.application_protocol = 'MODBUS' AND (ep.service_type IS NULL OR ep.service_type = 'RTU_READ')
          AND ep.transport = 'SERIAL'
    """,
    "v_scada_endpoint_iec101": """
        SELECT
            ep.endpoint_id, ep.ied_id, ep.application_protocol, ep.service_type, ep.transport,
            ep.host, ep.port,
            p.param_key,
            COALESCE(pv.value_text, CAST(pv.value_int AS TEXT), CAST(pv.value_float AS TEXT), CAST(pv.value_bool AS TEXT)) AS param_value
        FROM scada_communication_endpoint AS ep
        LEFT JOIN scada_endpoint_param_value AS pv ON pv.endpoint_id = ep.endpoint_id
        LEFT JOIN scada_protocol_param_def AS p ON p.param_def_id = pv.param_def_id
        WHERE ep.application_protocol = 'IEC101'
    """,
    "v_scada_endpoint_iec104": """
        SELECT
            ep.endpoint_id, ep.ied_id, ep.application_protocol, ep.service_type, ep.transport,
            ep.host, ep.port,
            p.param_key,
            COALESCE(pv.value_text, CAST(pv.value_int AS TEXT), CAST(pv.value_float AS TEXT), CAST(pv.value_bool AS TEXT)) AS param_value
        FROM scada_communication_endpoint AS ep
        LEFT JOIN scada_endpoint_param_value AS pv ON pv.endpoint_id = ep.endpoint_id
        LEFT JOIN scada_protocol_param_def AS p ON p.param_def_id = pv.param_def_id
        WHERE ep.application_protocol = 'IEC104'
    """,
    "v_scada_endpoint_iec61850_mms": """
        SELECT
            ep.endpoint_id, ep.ied_id, ep.application_protocol, ep.service_type, ep.transport,
            ep.host, ep.port,
            p.param_key,
            COALESCE(pv.value_text, CAST(pv.value_int AS TEXT), CAST(pv.value_float AS TEXT), CAST(pv.value_bool AS TEXT)) AS param_value
        FROM scada_communication_endpoint AS ep
        LEFT JOIN scada_endpoint_param_value AS pv ON pv.endpoint_id = ep.endpoint_id
        LEFT JOIN scada_protocol_param_def AS p ON p.param_def_id = pv.param_def_id
        WHERE ep.application_protocol = 'IEC61850' AND ep.service_type IN ('MMS_READ', 'REPORT')
    """,
    "v_scada_endpoint_iec61850_goose": """
        SELECT
            ep.endpoint_id, ep.ied_id, ep.application_protocol, ep.service_type, ep.transport,
            ep.host, ep.port,
            p.param_key,
            COALESCE(pv.value_text, CAST(pv.value_int AS TEXT), CAST(pv.value_float AS TEXT), CAST(pv.value_bool AS TEXT)) AS param_value
        FROM scada_communication_endpoint AS ep
        LEFT JOIN scada_endpoint_param_value AS pv ON pv.endpoint_id = ep.endpoint_id
        LEFT JOIN scada_protocol_param_def AS p ON p.param_def_id = pv.param_def_id
        WHERE ep.application_protocol = 'IEC61850' AND ep.service_type = 'GOOSE'
    """,
    "v_scada_endpoint_iec61850_sv": """
        SELECT
            ep.endpoint_id, ep.ied_id, ep.application_protocol, ep.service_type, ep.transport,
            ep.host, ep.port,
            p.param_key,
            COALESCE(pv.value_text, CAST(pv.value_int AS TEXT), CAST(pv.value_float AS TEXT), CAST(pv.value_bool AS TEXT)) AS param_value
        FROM scada_communication_endpoint AS ep
        LEFT JOIN scada_endpoint_param_value AS pv ON pv.endpoint_id = ep.endpoint_id
        LEFT JOIN scada_protocol_param_def AS p ON p.param_def_id = pv.param_def_id
        WHERE ep.application_protocol = 'IEC61850' AND ep.service_type = 'SV'
    """,
    "v_scada_endpoint_mqtt": """
        SELECT
            ep.endpoint_id, ep.ied_id, ep.application_protocol, ep.service_type, ep.transport,
            ep.host, ep.port,
            p.param_key,
            COALESCE(pv.value_text, CAST(pv.value_int AS TEXT), CAST(pv.value_float AS TEXT), CAST(pv.value_bool AS TEXT)) AS param_value
        FROM scada_communication_endpoint AS ep
        LEFT JOIN scada_endpoint_param_value AS pv ON pv.endpoint_id = ep.endpoint_id
        LEFT JOIN scada_protocol_param_def AS p ON p.param_def_id = pv.param_def_id
        WHERE ep.application_protocol = 'MQTT'
    """,
    "v_scada_endpoint_http_rest": """
        SELECT
            ep.endpoint_id, ep.ied_id, ep.application_protocol, ep.service_type, ep.transport,
            ep.host, ep.port,
            p.param_key,
            COALESCE(pv.value_text, CAST(pv.value_int AS TEXT), CAST(pv.value_float AS TEXT), CAST(pv.value_bool AS TEXT)) AS param_value
        FROM scada_communication_endpoint AS ep
        LEFT JOIN scada_endpoint_param_value AS pv ON pv.endpoint_id = ep.endpoint_id
        LEFT JOIN scada_protocol_param_def AS p ON p.param_def_id = pv.param_def_id
        WHERE ep.application_protocol = 'HTTP_REST'
    """,
}


def ensure_protocol_views(*, bind: Engine) -> None:
    """Create all protocol-specific endpoint views."""
    for view_name, view_sql in _PROTOCOL_VIEW_DEFS.items():
        with bind.begin() as conn:
            conn.execute(text(f"DROP VIEW IF EXISTS {view_name}"))
            conn.execute(text(f"CREATE VIEW {view_name} AS {view_sql}"))


__all__ = ["_PROTOCOL_VIEW_DEFS", "ensure_protocol_views"]
