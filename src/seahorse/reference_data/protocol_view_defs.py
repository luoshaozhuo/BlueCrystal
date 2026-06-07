"""协议端点参数展平视图定义 —— seahorse 参考数据。

这些视图用于把第一范式的端点参数值按协议分类展开，便于 Navicat 查询、
报表和人工核对；它们不替代表结构，也不承担写入职责。

本文件已从 whale.shared.persistence.template 迁移至 seahorse.reference_data。
"""
from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.engine import Engine

_VALUE_EXPR = (
    "COALESCE("
    "pv.value_text, "
    "CAST(pv.value_int AS TEXT), "
    "CAST(pv.value_float AS TEXT), "
    "CAST(pv.value_bool AS TEXT)"
    ")"
)


def _build_protocol_view(where_sql: str, *, include_namespace: bool = False, include_security: bool = False) -> str:
    """生成统一格式的协议视图 SQL."""

    extra_columns: list[str] = []
    if include_namespace:
        extra_columns.append("ep.namespace_uri AS namespace_uri")
    if include_security:
        extra_columns.extend(
            [
                "ep.security_policy AS security_policy",
                "ep.security_mode AS security_mode",
                "ep.auth_type AS auth_type",
            ]
        )
    extra_columns_sql = ",\n            ".join(extra_columns)
    extra_select = f",\n            {extra_columns_sql}" if extra_columns_sql else ""
    return f"""
        SELECT
            ep.endpoint_id,
            ep.ied_id,
            ep.application_protocol,
            ep.service_type,
            ep.transport,
            ep.host,
            ep.port{extra_select},
            p.param_key,
            {_VALUE_EXPR} AS param_value
        FROM scada_communication_endpoint AS ep
        LEFT JOIN scada_endpoint_param_value AS pv ON pv.endpoint_id = ep.endpoint_id
        LEFT JOIN scada_protocol_param_def AS p ON p.param_def_id = pv.param_def_id
        WHERE {where_sql}
    """


# fmt: off
_PROTOCOL_VIEW_DEFS: dict[str, str] = {
    "v_scada_endpoint_opcua": _build_protocol_view(
        "ep.application_protocol = 'OPC_UA'",
        include_namespace=True,
        include_security=True,
    ),
    "v_scada_endpoint_modbus_tcp": _build_protocol_view(
        "ep.application_protocol = 'MODBUS' "
        "AND (ep.service_type IS NULL OR ep.service_type = 'TCP_READ') "
        "AND ep.transport = 'TCP'"
    ),
    "v_scada_endpoint_modbus_rtu": _build_protocol_view(
        "ep.application_protocol = 'MODBUS' "
        "AND (ep.service_type IS NULL OR ep.service_type = 'RTU_READ') "
        "AND ep.transport = 'SERIAL'"
    ),
    "v_scada_endpoint_iec101": _build_protocol_view("ep.application_protocol = 'IEC101'"),
    "v_scada_endpoint_iec104": _build_protocol_view("ep.application_protocol = 'IEC104'"),
    "v_scada_endpoint_iec61850_mms": _build_protocol_view(
        "ep.application_protocol = 'IEC61850' "
        "AND ep.service_type IN ('MMS_READ', 'REPORT')"
    ),
    "v_scada_endpoint_iec61850_goose": _build_protocol_view(
        "ep.application_protocol = 'IEC61850' AND ep.service_type = 'GOOSE'"
    ),
    "v_scada_endpoint_iec61850_sv": _build_protocol_view(
        "ep.application_protocol = 'IEC61850' AND ep.service_type = 'SV'"
    ),
    "v_scada_endpoint_mqtt": _build_protocol_view("ep.application_protocol = 'MQTT'"),
    "v_scada_endpoint_http_rest": _build_protocol_view("ep.application_protocol = 'HTTP_REST'"),
    "v_scada_endpoint_beckhoff_ads": _build_protocol_view(
        "ep.application_protocol = 'BECKHOFF_ADS'",
        include_security=True,
    ),
}
# fmt: on


def ensure_protocol_views(*, bind: Engine) -> None:
    """创建或重建所有协议专用只读视图."""

    for view_name, view_sql in _PROTOCOL_VIEW_DEFS.items():
        with bind.begin() as conn:
            conn.execute(text(f"DROP VIEW IF EXISTS {view_name}"))
            conn.execute(text(f"CREATE VIEW {view_name} AS {view_sql}"))


__all__ = ["_PROTOCOL_VIEW_DEFS", "ensure_protocol_views"]
