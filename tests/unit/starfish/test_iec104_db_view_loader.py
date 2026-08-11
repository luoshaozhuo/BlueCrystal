"""IEC104 comm/src view loader 的参数化 SQL 契约测试。

测试替身模拟当前 Whale views，重点证明协议点位只通过 ``point_table_id`` 回连
connection，并验证 None/部分/缺失/空 IDs 语义；不连接真实 PostgreSQL。
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any, cast

import pandas as pd
import pytest
from sqlalchemy.engine import Engine

from starfish.adapters.db_views.iec104 import Iec104DbViewLoadError, Iec104DbViewLoader
from starfish.core.config_frames import SERVER_CONFIG_COLUMNS


class _Result:
    """最小 SQLAlchemy mapping result 替身。"""

    def __init__(self, rows: Iterable[dict[str, Any]]) -> None:
        self.rows = list(rows)

    def mappings(self) -> list[dict[str, Any]]:
        """返回预设 view rows。"""
        return self.rows


class _Connection:
    """按当前 view key 返回批量结果，并记录协议点位查询。"""

    def __init__(
        self,
        role: str = "CONTROLLED_STATION",
        protocol: str = "IEC104",
        *,
        tables: list[dict[str, Any]] | None = None,
        points: list[dict[str, Any]] | None = None,
    ) -> None:
        self.role = role
        self.protocol = protocol
        self.tables = tables if tables is not None else _tables(protocol)
        self.points = points if points is not None else _points()
        self.queries: list[tuple[str, dict[str, Any] | None]] = []

    def __enter__(self) -> _Connection:
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def execute(self, stmt: object, params: dict[str, Any] | None = None) -> _Result:
        """校验各 view 的真实过滤键并返回同形行。"""
        sql = str(stmt)
        self.queries.append((sql, params))
        if "SET TRANSACTION READ ONLY" in sql:
            return _Result([])
        values = params or {}
        if "vw_comm_iec104_connection" in sql:
            requested = set(values.get("connection_ids", (1, 2)))
            available = {row["connection_id"] for row in self.tables}
            return _Result(
                _connection(value, self.role, self.protocol)
                for value in sorted(requested & available)
            )
        if "vw_src_iec104_point_item" in sql:
            assert "JOIN whale.vw_src_point_table" in sql
            table_connections = {
                row["point_table_id"]: row["connection_id"] for row in self.tables
            }
            requested = set(values.get("connection_ids", (1, 2)))
            return _Result(
                {**row, "connection_id": table_connections[row["point_table_id"]]}
                for row in self.points
                if table_connections.get(row["point_table_id"]) in requested
            )
        raise AssertionError(f"loader 访问了未授权 view: {sql}")


class _Engine:
    """持有可观察的单个 view connection 替身。"""

    def __init__(
        self,
        role: str = "CONTROLLED_STATION",
        protocol: str = "IEC104",
        *,
        tables: list[dict[str, Any]] | None = None,
        points: list[dict[str, Any]] | None = None,
    ) -> None:
        self.connection = _Connection(
            role,
            protocol,
            tables=tables,
            points=points,
        )

    def connect(self) -> _Connection:
        """返回记录本次 loader 查询的 connection。"""
        return self.connection


@pytest.fixture(autouse=True)
def _read_sql_query_through_fake_connection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """让 pandas 查询走 view connection 替身以核对批量 SQL 与参数。"""

    def read_sql_query(
        stmt: object,
        conn: _Connection,
        params: dict[str, Any] | None = None,
    ) -> pd.DataFrame:
        sql = str(stmt)
        rows = conn.execute(stmt, params).mappings()
        if "vw_comm_iec104_connection" in sql:
            columns = list(_connection(1, conn.role, conn.protocol))
        else:
            columns = [*list(_point(1, 10)), "connection_id"]
        return pd.DataFrame(rows, columns=columns)

    monkeypatch.setattr(pd, "read_sql_query", read_sql_query)


def _connection(connection_id: int, role: str, protocol: str) -> dict[str, Any]:
    """生成真实 comm view 同形行。"""
    return {
        "connection_id": connection_id,
        "protocol": protocol,
        "protocol_role": role,
        "host": "127.0.0.1",
        "port": 61000 + connection_id,
        "equipment_name": "风机",
        "interface_id": connection_id,
        "interface_type": "ETHERNET_PORT",
        "equipment_id": connection_id,
        "reconnect_enabled": True,
        "reconnect_interval_ms": 5000,
        "t0_ms": 30000,
        "t1_ms": 15000,
        "t2_ms": 10000,
        "t3_ms": 20000,
        "k_value": 12,
        "w_value": 8,
    }


def _tables(protocol: str = "IEC104") -> list[dict[str, Any]]:
    """生成多 connection、多 PointTable 的总表 view 行。"""
    return [
        {"point_table_id": 10, "connection_id": 1, "protocol": protocol},
        {"point_table_id": 11, "connection_id": 1, "protocol": protocol},
        {"point_table_id": 20, "connection_id": 2, "protocol": protocol},
    ]


def _points() -> list[dict[str, Any]]:
    """生成不含 connection_id 的当前 IEC104 point view 行。"""
    return [
        _point(1, 10, "ACTIVE_POWER", 1001),
        _point(2, 11, "REACTIVE_POWER", 1002),
        _point(3, 20, "WIND_SPEED", 1003),
    ]


def _point(
    point_id: int,
    table_id: int,
    business_semantic_name: str = "ACTIVE_POWER",
    ioa: int = 1001,
) -> dict[str, Any]:
    """生成真实 src IEC104 point view 同形行，不伪造 connection_id。"""
    return {
        "point_table_id": table_id,
        "point_item_id": point_id,
        "sort_order": point_id,
        "business_semantic_identifier": business_semantic_name,
        "business_semantic_name_zh": business_semantic_name,
        "physical_quantity_category": business_semantic_name,
        "data_type": "FLOAT64",
        "unit": "MW",
        "scale_factor": 1,
        "offset_value": 0,
        "value_min": 0,
        "value_max": 5,
        "allowed_values": None,
        "value_update_mode": "PERIODIC",
        "value_update_interval_ms": 100,
        "iec104_type_id": 13,
        "iec104_type": "M_ME_NC_1",
        "common_address": 1,
        "information_object_address": ioa,
        "general_interrogation_enabled": True,
        "general_interrogation_group": None,
        "counter_interrogation_enabled": False,
        "periodic_transmission_enabled": True,
        "periodic_interval_ms": 1000,
        "spontaneous_transmission_enabled": True,
        "deadband": 0.05,
        "background_transmission_enabled": False,
        "quality_enabled": True,
    }


def test_loader_filters_and_orders_points_in_sql() -> None:
    """多连接、多点表由参数化 SQL 筛选并按 connection 升序装配。"""
    engine = _Engine()
    frame = Iec104DbViewLoader(engine=cast(Engine, engine)).load([2, 1, 2])

    assert tuple(frame.columns) == SERVER_CONFIG_COLUMNS
    assert frame["connection_id"].drop_duplicates().tolist() == [1, 2]
    assert frame.loc[frame["connection_id"] == 2, "point_table_id"].tolist() == [20]
    assert frame.loc[frame["connection_id"] == 2, "point_item_id"].tolist() == [3]
    assert frame.loc[frame["connection_id"] == 1, "point_table_id"].tolist() == [10, 11]
    assert frame.loc[frame["connection_id"] == 1, "point_item_id"].tolist() == [1, 2]
    data_queries = [
        query for query in engine.connection.queries if "SELECT" in query[0]
    ]
    assert len(data_queries) == 2
    assert all("connection_ids" in (params or {}) for _sql, params in data_queries)
    assert "JOIN whale.vw_src_point_table" in data_queries[1][0]
    assert "ORDER BY point_tables.connection_id" in data_queries[1][0]
    assert frame["general_interrogation_enabled"].all()
    assert frame["periodic_transmission_enabled"].all()
    assert frame["point_identifier"].tolist() == [
        "ACTIVE_POWER",
        "REACTIVE_POWER",
        "WIND_SPEED",
    ]


def test_loader_none_queries_all_without_where() -> None:
    """None 读取全部 connection 与 point rows，SQL 不包含 WHERE。"""
    engine = _Engine()
    frame = Iec104DbViewLoader(engine=cast(Engine, engine)).load()

    assert frame["connection_id"].drop_duplicates().tolist() == [1, 2]
    data_queries = [
        query for query in engine.connection.queries if "SELECT" in query[0]
    ]
    assert all("WHERE" not in sql for sql, _params in data_queries)
    assert all(params is None for _sql, params in data_queries)


def test_loader_rejects_missing_and_empty_ids() -> None:
    """缺失任一请求 connection 或传入空列表时返回明确错误。"""
    loader = Iec104DbViewLoader(engine=cast(Engine, _Engine()))

    with pytest.raises(Iec104DbViewLoadError, match=r"connection_id: \[999\]"):
        loader.load([1, 999])
    with pytest.raises(Iec104DbViewLoadError, match="connection_ids 不能为空"):
        loader.load([])


def test_loader_preserves_protocol_role_without_normalization() -> None:
    """数据库角色值原样透传，格式拒绝属于后续 protocol 边界职责。"""
    frame = Iec104DbViewLoader(
        engine=cast(Engine, _Engine(" controlled-station "))
    ).load([1])

    assert frame["station_role"].unique().tolist() == [" controlled-station "]
