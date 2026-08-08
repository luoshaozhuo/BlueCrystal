"""从 Whale 当前执行视图加载 IEC104 运行定义。

本 adapter 只读取五个公开 view 中与运行装配有关的三个：
`vw_connection_object_full`、`vw_task_full`、`vw_task_point_item`，以及连接
登记的 `vw_iec104_point_item`。它不访问基础表，也不根据旧版聚合 JSON
字段猜测任务成员。
"""

from __future__ import annotations

import ipaddress
import json
import re
from collections.abc import Iterable, Mapping, Sequence
from decimal import Decimal, InvalidOperation
from typing import Any

from sqlalchemy import bindparam, create_engine, text
from sqlalchemy.engine import Engine

from starfish.adapters.db_views.errors import DbViewLoadError
from starfish.core.definitions import (
    PointItemDefinition,
    ServerDefinition,
    TaskDefinition,
)

_IEC104_PROTOCOL = "IEC104"
_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class Iec104DbViewLoadError(DbViewLoadError):
    """IEC104 执行视图缺失或违反运行契约。"""


class Iec104DbViewLoader:
    """从 Whale view 加载 IEC104 server/client definitions。"""

    def __init__(self, db_url: str | None = None, *, engine: Engine | None = None) -> None:
        if engine is None and not db_url:
            raise Iec104DbViewLoadError("缺少 WHALE_DB_URL，无法加载 IEC104 simulator 配置")
        self._engine = engine or create_engine(str(db_url), future=True)

    def load(self, connection_ids: Sequence[int]) -> list[ServerDefinition]:
        """加载并保持调用方给定的 connection 顺序。"""
        normalized_ids = list(dict.fromkeys(int(value) for value in connection_ids))
        if not normalized_ids:
            raise Iec104DbViewLoadError("IEC104 connection_ids 不能为空")
        with self._engine.connect() as conn:
            return [self._load_one(conn, connection_id) for connection_id in normalized_ids]

    def _load_one(self, conn: Any, connection_id: int) -> ServerDefinition:
        """加载单个 connection 的连接、任务、成员和点位。"""
        connection_row = _single_mapping(
            conn.execute(
                text("""
                    SELECT *
                    FROM whale.vw_connection_object_full
                    WHERE connection_id = :connection_id
                    """),
                {"connection_id": connection_id},
            ).mappings(),
            f"未找到 connection_id={connection_id}",
        )
        if _normalize_protocol(connection_row.get("protocol")) != _IEC104_PROTOCOL:
            raise Iec104DbViewLoadError(
                f"connection_id={connection_id} 不是 IEC104 协议，"
                f"实际 protocol={connection_row.get('protocol')}"
            )

        task_rows = list(
            conn.execute(
                text("""
                    SELECT *
                    FROM whale.vw_task_full
                    WHERE conn_id = :connection_id
                      AND protocol = :protocol
                    ORDER BY task_id
                    """),
                {"connection_id": connection_id, "protocol": _IEC104_PROTOCOL},
            ).mappings()
        )
        if not task_rows:
            raise Iec104DbViewLoadError(f"connection_id={connection_id} 没有 IEC104 task")

        point_view_name = _validate_view_name(str(connection_row.get("point_item_view_name") or ""))
        task_members = _load_task_members(conn, task_rows)
        point_ids = list(
            dict.fromkeys(
                member[0]
                for row in task_rows
                for member in task_members[int(row["task_point_table_id"])]
            )
        )
        point_rows = _load_point_rows(conn, point_view_name, point_ids)
        found = {int(row["point_item_id"]) for row in point_rows}
        missing = sorted(set(point_ids) - found)
        if missing:
            raise Iec104DbViewLoadError(
                f"connection_id={connection_id} 的点位 view 缺少 point_item_id: {missing}"
            )
        return _build_definition(connection_row, task_rows, task_members, point_rows)


def _load_task_members(
    conn: Any,
    task_rows: Sequence[Mapping[str, Any]],
) -> dict[int, tuple[tuple[int, str], ...]]:
    """经 `vw_task_point_item` 还原每个 task point table 的成员。"""
    table_ids = list(dict.fromkeys(int(row["task_point_table_id"]) for row in task_rows))
    stmt = text("""
        SELECT task_point_table_id, protocol_point_item_id, point_role, scan_order
        FROM whale.vw_task_point_item
        WHERE protocol = :protocol
          AND task_point_table_id IN :table_ids
        ORDER BY task_point_table_id, scan_order, task_point_item_id
        """).bindparams(bindparam("table_ids", expanding=True))
    rows = conn.execute(
        stmt,
        {"protocol": _IEC104_PROTOCOL, "table_ids": table_ids},
    ).mappings()
    members: dict[int, list[tuple[int, str]]] = {table_id: [] for table_id in table_ids}
    for row in rows:
        members[int(row["task_point_table_id"])].append(
            (int(row["protocol_point_item_id"]), str(row.get("point_role") or ""))
        )
    return {table_id: tuple(items) for table_id, items in members.items()}


def _load_point_rows(
    conn: Any,
    point_view_name: str,
    point_ids: Sequence[int],
) -> list[Mapping[str, Any]]:
    """从已登记且校验过的 IEC104 point view 加载成员并集。"""
    if not point_ids:
        return []
    stmt = text(f"""
        SELECT *
        FROM {point_view_name}
        WHERE point_item_id IN :point_ids
        ORDER BY table_id, common_address, io_address
        """).bindparams(bindparam("point_ids", expanding=True))
    return list(conn.execute(stmt, {"point_ids": list(point_ids)}).mappings())


def _build_definition(
    connection_row: Mapping[str, Any],
    task_rows: Sequence[Mapping[str, Any]],
    task_members: Mapping[int, tuple[tuple[int, str], ...]],
    point_rows: Sequence[Mapping[str, Any]],
) -> ServerDefinition:
    """将 view rows 收敛成不依赖 SQLAlchemy 的 core definitions。"""
    connection_id = int(connection_row["connection_id"])
    params = _coerce_mapping(
        _json_dict(
            connection_row.get("connection_params_json", {}),
            field_name="vw_connection_object_full.connection_params_json",
        )
    )
    station_role = (
        str(connection_row.get("station_role") or params.get("station_role") or "").strip().upper()
    )
    if station_role not in {"CONTROLLED_STATION", "CONTROLLING_STATION"}:
        raise Iec104DbViewLoadError(
            f"connection_id={connection_id} station_role 非法: {station_role}"
        )
    host_key = "listen_host" if station_role == "CONTROLLED_STATION" else "remote_host"
    port_key = "listen_port" if station_role == "CONTROLLED_STATION" else "remote_port"
    host = _normalize_host(params.get(host_key) or params.get("host") or "127.0.0.1")
    port = int(params.get(port_key) or params.get("port") or 2404)
    tasks = tuple(
        _task_definition(row, task_members[int(row["task_point_table_id"])]) for row in task_rows
    )
    return ServerDefinition(
        connection_id=connection_id,
        name=str(connection_row.get("asset_name") or f"iec104_connection_{connection_id}"),
        protocol=_IEC104_PROTOCOL,
        bind_host=host,
        bind_port=port,
        connection_params=params,
        tasks=tasks,
        point_items=tuple(_point_definition(row) for row in point_rows),
        capabilities=("IEC104_SIMULATOR", *sorted(task.task_type for task in tasks)),
        metadata={
            "asset_id": connection_row.get("asset_id"),
            "asset_identifier": connection_row.get("asset_identifier"),
            "connection_identifier": connection_row.get("connection_identifier"),
            "point_item_view_name": connection_row.get("point_item_view_name"),
        },
        station_role=station_role,
    )


def _task_definition(
    row: Mapping[str, Any],
    members: tuple[tuple[int, str], ...],
) -> TaskDefinition:
    """映射当前 `vw_task_full` 契约。"""
    operation_identifier = str(row.get("operation_identifier") or "")
    return TaskDefinition(
        task_id=int(row["task_id"]),
        task_identifier=str(row.get("task_identifier") or ""),
        task_type=operation_identifier,
        task_status=str(row.get("task_status") or ""),
        params=_coerce_mapping(
            _json_dict(
                row.get("task_params_json", {}),
                field_name="vw_task_full.task_params_json",
            )
        ),
        point_item_ids=tuple(point_id for point_id, _ in members),
        task_role=str(row.get("task_role") or ""),
        task_point_table_id=int(row["task_point_table_id"]),
        point_roles={point_id: role for point_id, role in members},
    )


def _point_definition(row: Mapping[str, Any]) -> PointItemDefinition:
    """映射 `vw_iec104_point_item` 的完整运行字段。"""
    point_item_id = int(row["point_item_id"])
    identifier = str(row.get("point_identifier") or point_item_id)
    metadata_fields = (
        "table_id",
        "semantic_identifier",
        "unit_code",
        "scale",
        "offset_value",
        "value_min",
        "value_max",
        "allowed_values",
        "type_id_value",
        "type_category",
        "information_value_type",
        "time_tag_type",
        "point_registration_supported",
        "general_interrogation_supported",
        "counter_interrogation_supported",
        "periodic_transmission_supported",
        "spontaneous_transmission_supported",
        "command_mode_supported",
        "related_io_supported",
        "common_address",
        "command_mode",
        "report_ms",
        "spontaneous_deadband",
        "spontaneous_min_interval_ms",
        "related_io_address",
        "related_io_autoreturn",
        "quality_descriptor_enabled",
    )
    return PointItemDefinition(
        point_item_id=point_item_id,
        point_identifier=identifier,
        semantic_name=str(row.get("semantic_name_zh") or identifier),
        data_type=str(row.get("data_type") or ""),
        type_id=str(row.get("type_id") or ""),
        io_address=int(row["io_address"]),
        initial_value=_initial_value(row),
        metadata={field: row.get(field) for field in metadata_fields},
    )


def _single_mapping(
    rows: Iterable[Mapping[str, Any]],
    missing_message: str,
) -> Mapping[str, Any]:
    """取单行 mapping，缺失时转换为稳定 loader 异常。"""
    for row in rows:
        return row
    raise Iec104DbViewLoadError(missing_message)


def _validate_view_name(raw_view_name: str) -> str:
    """只允许 Whale schema 下的安全 view 标识。"""
    parts = raw_view_name.split(".")
    if len(parts) == 1:
        schema, view = "whale", parts[0]
    elif len(parts) == 2:
        schema, view = parts
    else:
        raise Iec104DbViewLoadError(f"非法 point_item_view_name: {raw_view_name}")
    if schema != "whale" or not _IDENTIFIER_RE.fullmatch(view):
        raise Iec104DbViewLoadError(f"非法 point_item_view_name: {raw_view_name}")
    return f"{schema}.{view}"


def _normalize_protocol(value: Any) -> str:
    """把 DB protocol code 归一为 registry key。"""
    return str(value or "").strip().upper().replace("-", "_").replace(" ", "_")


def _normalize_host(value: Any) -> str:
    """把 PostgreSQL INET 的 CIDR 文本转换为 c104 接受的 IP。"""
    raw = str(value).strip()
    try:
        return str(ipaddress.ip_interface(raw).ip)
    except ValueError as exc:
        raise Iec104DbViewLoadError(f"IEC104 host 非法: {raw}") from exc


def _json_dict(value: Any, *, field_name: str) -> dict[str, Any]:
    """兼容 JSONB mapping 与测试中的 JSON 字符串。"""
    data = json.loads(value) if isinstance(value, str) else value
    if not isinstance(data, dict):
        raise Iec104DbViewLoadError(f"{field_name} 应为 JSON object")
    return dict(data)


def _coerce_mapping(value: Mapping[str, Any]) -> dict[str, Any]:
    """将 view 中按契约保存的文本参数转换为基础 Python 类型。"""
    return {key: _coerce_scalar(item) for key, item in value.items()}


def _coerce_scalar(value: Any) -> Any:
    """转换 bool、整数和小数文本，其他值原样保留。"""
    if not isinstance(value, str):
        return value
    stripped = value.strip()
    lowered = stripped.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    try:
        return int(stripped)
    except ValueError:
        pass
    try:
        return float(Decimal(stripped))
    except (InvalidOperation, ValueError, OverflowError):
        return value


def _initial_value(row: Mapping[str, Any]) -> Any:
    """依据离散域或数值范围生成可注册的保守初值。"""
    allowed_values = str(row.get("allowed_values") or "").strip()
    if allowed_values:
        return _coerce_scalar(allowed_values.split(",", maxsplit=1)[0].strip())
    lower = row.get("value_min")
    upper = row.get("value_max")
    if lower is not None and upper is not None:
        low, high = float(lower), float(upper)
        return 0.0 if low <= 0 <= high else low
    return 0


__all__ = ["Iec104DbViewLoadError", "Iec104DbViewLoader"]
