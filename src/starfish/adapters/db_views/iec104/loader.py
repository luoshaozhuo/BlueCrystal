"""IEC104 simulator 的 Whale DB view loader。

本 adapter 只负责读取 `vw_connection_object_full`、`vw_task_full` 和 DB
登记的 IEC104 point item view，并映射为 core `ServerDefinition`。它不
推导 point view 名、不创建 native server、不写入数据库。
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterable, Mapping, Sequence
from decimal import Decimal
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
    """IEC104 DB view 配置加载失败。

    该异常表示执行视图缺失、字段不符合 IEC104 server 启动契约，或数据库访问
    失败。调用方应把它转换成 CLI/API 的稳定错误信息。
    """


class Iec104DbViewLoader:
    """从 Whale 执行视图加载 IEC104 simulator definitions。

    Args:
        db_url: SQLAlchemy 可识别的数据库连接 URL，通常来自 `WHALE_DB_URL`。
        engine: 测试可注入的 SQLAlchemy engine；传入后不再使用 `db_url`
            创建新 engine。
    """

    def __init__(self, db_url: str | None = None, *, engine: Engine | None = None) -> None:
        if engine is None and not db_url:
            raise Iec104DbViewLoadError("缺少 WHALE_DB_URL，无法加载 IEC104 simulator 配置")
        self._engine = engine or create_engine(str(db_url), future=True)

    def load(self, connection_ids: Sequence[int]) -> list[ServerDefinition]:
        """加载已分派给 IEC104 的 connection definitions。"""
        normalized_ids = list(dict.fromkeys(int(value) for value in connection_ids))
        if not normalized_ids:
            raise Iec104DbViewLoadError("IEC104 connection_ids 不能为空")
        return self._load(normalized_ids)

    def _load(self, connection_ids: Sequence[int]) -> list[ServerDefinition]:
        """读取连接、任务、点位视图并组装 ServerDefinition。"""
        definitions: list[ServerDefinition] = []
        with self._engine.connect() as conn:
            for connection_id in connection_ids:
                connection_row = _single_mapping(
                    conn.execute(
                        text(
                            """
                            SELECT *
                            FROM whale.vw_connection_object_full
                            WHERE connection_id = :connection_id
                            """
                        ),
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
                        text(
                            """
                            SELECT *
                            FROM whale.vw_task_full
                            WHERE connection_id = :connection_id
                              AND protocol = :protocol
                            ORDER BY task_id
                            """
                        ),
                        {"connection_id": connection_id, "protocol": _IEC104_PROTOCOL},
                    ).mappings()
                )
                if not task_rows:
                    raise Iec104DbViewLoadError(
                        f"connection_id={connection_id} 没有可用于初始化的 IEC104 task"
                    )

                point_view_name = _view_name_from_rows(connection_row, task_rows)
                point_ids = _point_ids_from_tasks(task_rows)
                if not point_ids:
                    raise Iec104DbViewLoadError(
                        f"connection_id={connection_id} 的 vw_task_full.point_item_ids_json 为空"
                    )

                point_rows = _load_point_rows(conn, point_view_name, point_ids)
                if len(point_rows) != len(set(point_ids)):
                    found = {int(row["point_item_id"]) for row in point_rows}
                    missing = sorted(set(point_ids) - found)
                    raise Iec104DbViewLoadError(
                        f"connection_id={connection_id} 的点位视图缺少 point_item_id: {missing}"
                    )

                definitions.append(_build_definition(connection_row, task_rows, point_rows))
        return definitions


def _single_mapping(rows: Iterable[Mapping[str, Any]], missing_message: str) -> Mapping[str, Any]:
    """取单行 mapping；缺失时报稳定加载错误。"""
    for row in rows:
        return row
    raise Iec104DbViewLoadError(missing_message)


def _normalize_protocol(protocol: Any) -> str:
    """把 DB 协议 code 归一为大写下划线形式。"""
    return str(protocol or "").strip().upper().replace("-", "_").replace(" ", "_")


def _json_value(value: Any) -> Any:
    """兼容 psycopg/测试替身返回的 JSONB dict/list 或 JSON 字符串。"""
    if isinstance(value, str):
        return json.loads(value)
    return value


def _json_dict(value: Any, *, field_name: str) -> dict[str, Any]:
    """将 JSONB 字段收敛为 dict。"""
    data = _json_value(value)
    if not isinstance(data, dict):
        raise Iec104DbViewLoadError(f"{field_name} 应为 JSON object")
    return data


def _json_list(value: Any, *, field_name: str) -> list[Any]:
    """将 JSONB 字段收敛为 list。"""
    data = _json_value(value)
    if not isinstance(data, list):
        raise Iec104DbViewLoadError(f"{field_name} 应为 JSON array")
    return data


def _view_name_from_rows(
    connection_row: Mapping[str, Any],
    task_rows: Sequence[Mapping[str, Any]],
) -> str:
    """从 DB 返回字段确认点位执行视图名。"""
    connection_view = str(connection_row.get("point_item_view_name") or "").strip()
    if not connection_view:
        raise Iec104DbViewLoadError("vw_connection_object_full.point_item_view_name 为空")
    validated_connection_view = _validate_view_name(connection_view)
    for task in task_rows:
        task_view = str(task.get("point_item_view_name") or "").strip()
        if task_view and task_view != connection_view:
            raise Iec104DbViewLoadError(
                "vw_task_full.point_item_view_name 与 connection view 不一致: "
                f"{task_view} != {connection_view}"
            )
    return validated_connection_view


def _validate_view_name(raw_view_name: str) -> str:
    """校验 DB 登记的 view 名，返回可安全拼入 SQL 的 `schema.view`。"""
    parts = raw_view_name.split(".")
    if len(parts) == 1:
        schema = "whale"
        view = parts[0]
    elif len(parts) == 2:
        schema, view = parts
    else:
        raise Iec104DbViewLoadError(f"非法 point_item_view_name: {raw_view_name}")
    if schema != "whale" or not _IDENTIFIER_RE.fullmatch(view):
        raise Iec104DbViewLoadError(f"非法 point_item_view_name: {raw_view_name}")
    return f"{schema}.{view}"


def _point_ids_from_tasks(task_rows: Sequence[Mapping[str, Any]]) -> list[int]:
    """按任务顺序合并并去重 point_item_id。"""
    result: list[int] = []
    seen: set[int] = set()
    for task in task_rows:
        for raw_id in _json_list(
            task.get("point_item_ids_json", []),
            field_name="vw_task_full.point_item_ids_json",
        ):
            point_id = int(raw_id)
            if point_id not in seen:
                seen.add(point_id)
                result.append(point_id)
    return result


def _load_point_rows(
    conn: Any,
    point_view_name: str,
    point_ids: Sequence[int],
) -> list[Mapping[str, Any]]:
    """从 DB 登记的点位执行视图读取 IEC104 点位。"""
    stmt = (
        text(
            f"""
            SELECT *
            FROM {point_view_name}
            WHERE point_item_id IN :point_ids
            ORDER BY point_item_id
            """
        )
        .bindparams(bindparam("point_ids", expanding=True))
    )
    return list(conn.execute(stmt, {"point_ids": list(point_ids)}).mappings())


def _build_definition(
    connection_row: Mapping[str, Any],
    task_rows: Sequence[Mapping[str, Any]],
    point_rows: Sequence[Mapping[str, Any]],
) -> ServerDefinition:
    """将 IEC104 DB rows 映射成 core ServerDefinition。"""
    connection_id = int(connection_row["connection_id"])
    params = _json_dict(
        connection_row.get("connection_params_json", {}),
        field_name="vw_connection_object_full.connection_params_json",
    )
    host = str(params.get("host") or "127.0.0.1")
    port = int(params.get("port") or 2404)
    name = str(connection_row.get("asset_name") or f"iec104_connection_{connection_id}")
    return ServerDefinition(
        connection_id=connection_id,
        name=name,
        protocol=_IEC104_PROTOCOL,
        bind_host=host,
        bind_port=port,
        connection_params=params,
        tasks=tuple(_task_definition(row) for row in task_rows),
        point_items=tuple(_point_definition(row) for row in point_rows),
        capabilities=tuple(_capabilities(task_rows)),
        metadata={
            "asset_id": connection_row.get("asset_id"),
            "asset_identifier": connection_row.get("asset_identifier"),
            "asset_type_code": connection_row.get("asset_type_code"),
            "asset_type_name": connection_row.get("asset_type_name"),
        },
    )


def _task_definition(row: Mapping[str, Any]) -> TaskDefinition:
    """将 `vw_task_full` 行映射成 TaskDefinition。"""
    return TaskDefinition(
        task_id=int(row["task_id"]),
        task_identifier=str(row.get("task_identifier") or ""),
        task_type=str(row.get("task_type") or ""),
        task_status=str(row.get("task_status") or ""),
        params=_json_dict(row.get("task_params_json", {}), field_name="vw_task_full.task_params_json"),
        point_item_ids=tuple(
            int(raw_id)
            for raw_id in _json_list(
                row.get("point_item_ids_json", []),
                field_name="vw_task_full.point_item_ids_json",
            )
        ),
    )


def _point_definition(row: Mapping[str, Any]) -> PointItemDefinition:
    """将 `vw_iec104_point_item` 行转换为 PointItemDefinition。"""
    point_item_id = int(row["point_item_id"])
    point_identifier = str(row.get("point_identifier") or point_item_id)
    return PointItemDefinition(
        point_item_id=point_item_id,
        point_identifier=point_identifier,
        semantic_name=str(row.get("semantic_name") or point_identifier),
        data_type=str(row.get("data_type") or "FLOAT64"),
        type_id=str(row.get("type_id") or ""),
        io_address=row.get("io_address") or "",
        initial_value=_initial_value(row),
        metadata={
            "table_id": row.get("table_id"),
            "semantic_identifier": row.get("semantic_identifier"),
            "unit_code": row.get("unit_code"),
            "scale": row.get("scale"),
            "offset_value": row.get("offset_value"),
            "value_min": row.get("value_min"),
            "value_max": row.get("value_max"),
            "allowed_values": row.get("allowed_values"),
            "common_address": row.get("common_address"),
            "quality_descriptor_enabled": row.get("quality_descriptor_enabled"),
            "time_tag_enabled": row.get("time_tag_enabled"),
        },
    )


def _capabilities(task_rows: Sequence[Mapping[str, Any]]) -> list[str]:
    """从任务类型生成 server capability 声明。"""
    task_types = {
        str(task.get("task_type") or "").strip().upper()
        for task in task_rows
        if str(task.get("task_type") or "").strip()
    }
    return ["IEC104_SIMULATOR", *sorted(task_types)]


def _initial_value(row: Mapping[str, Any]) -> Any:
    """为 simulator 内部状态生成保守初始值。"""
    allowed_values = str(row.get("allowed_values") or "").strip()
    if allowed_values:
        return _coerce_scalar(allowed_values.split(",", maxsplit=1)[0].strip())
    value_min = row.get("value_min")
    value_max = row.get("value_max")
    if value_min is not None and value_max is not None:
        lower = float(value_min)
        upper = float(value_max)
        if lower <= 0 <= upper:
            return 0.0
        return lower
    return 0.0


def _coerce_scalar(value: str) -> Any:
    """把 allowed_values 文本值转换成简单 Python 标量。"""
    lowered = value.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(Decimal(value))
    except Exception:
        return value


__all__ = ["Iec104DbViewLoadError", "Iec104DbViewLoader"]
