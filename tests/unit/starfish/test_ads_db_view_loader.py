"""ADS comm/src view loader 的参数化 SQL 契约测试。

测试替身模拟当前 Whale views，证明 ADS 点位只通过 ``point_table_id`` 回连
connection，并验证 None/部分/缺失/空 IDs 语义；不连接真实 PostgreSQL。
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any, cast

import pandas as pd
import pytest
from sqlalchemy.engine import Engine

from starfish.adapters.db_views.ads import AdsDbViewLoadError, AdsDbViewLoader
from starfish.core.config_frames import SERVER_CONFIG_COLUMNS


class _Result:
    """最小 SQLAlchemy mapping result 替身。"""

    def __init__(self, rows: Iterable[dict[str, Any]]) -> None:
        self.rows = list(rows)

    def mappings(self) -> list[dict[str, Any]]:
        """返回预设 view rows。"""
        return self.rows


class _Connection:
    """按当前 ADS view key 返回批量结果，并记录协议点位查询。"""

    def __init__(
        self,
        protocol: str = "ADS",
        role: str = "SERVER",
        *,
        tables: list[dict[str, Any]] | None = None,
        points: list[dict[str, Any]] | None = None,
    ) -> None:
        self.protocol = protocol
        self.role = role
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
        if "vw_comm_ads_connection" in sql:
            requested = set(values.get("connection_ids", (3, 4)))
            available = {row["connection_id"] for row in self.tables}
            return _Result(
                _connection(value, self.protocol, self.role)
                for value in sorted(requested & available)
            )
        if "vw_src_ads_point_item" in sql:
            assert "JOIN whale.vw_src_point_table" in sql
            table_connections = {
                row["point_table_id"]: row["connection_id"] for row in self.tables
            }
            requested = set(values.get("connection_ids", (3, 4)))
            return _Result(
                {**row, "connection_id": table_connections[row["point_table_id"]]}
                for row in self.points
                if table_connections.get(row["point_table_id"]) in requested
            )
        raise AssertionError(f"loader 访问了未授权 view: {sql}")


class _Engine:
    """持有可观察的单个 ADS view connection 替身。"""

    def __init__(
        self,
        protocol: str = "ADS",
        role: str = "SERVER",
        *,
        tables: list[dict[str, Any]] | None = None,
        points: list[dict[str, Any]] | None = None,
    ) -> None:
        self.connection = _Connection(
            protocol,
            role,
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
        if "vw_comm_ads_connection" in sql:
            columns = list(_connection(3, conn.protocol, conn.role))
        else:
            columns = [*list(_point(7, 30)), "connection_id"]
        return pd.DataFrame(rows, columns=columns)

    monkeypatch.setattr(pd, "read_sql_query", read_sql_query)


def _connection(
    connection_id: int,
    protocol: str,
    role: str = "SERVER",
) -> dict[str, Any]:
    """生成真实 ADS comm view 同形行。"""
    return {
        "connection_id": connection_id,
        "protocol": protocol,
        "protocol_role": role,
        "host": "127.0.0.1",
        "port": 48895 + connection_id,
        "ams_net_id": f"127.0.0.1.1.{connection_id}",
        "ams_port": 851,
        "equipment_name": "PLC",
        "interface_id": connection_id,
        "interface_type": "ETHERNET_PORT",
        "equipment_id": connection_id,
        "reconnect_enabled": True,
        "reconnect_interval_ms": 3000,
    }


def _tables(protocol: str = "ADS") -> list[dict[str, Any]]:
    """生成多 connection、多 PointTable 的总表 view 行。"""
    return [
        {"point_table_id": 30, "connection_id": 3, "protocol": protocol},
        {"point_table_id": 31, "connection_id": 3, "protocol": protocol},
        {"point_table_id": 40, "connection_id": 4, "protocol": protocol},
    ]


def _points() -> list[dict[str, Any]]:
    """生成不含 connection_id 的当前 ADS point view 行。"""
    return [
        _point(7, 30, "MAIN.ActivePower"),
        _point(8, 31, "MAIN.ReactivePower"),
        _point(9, 40, "MAIN.RotorSpeed"),
    ]


def _point(
    point_id: int, table_id: int, symbol: str = "MAIN.ActivePower"
) -> dict[str, Any]:
    """生成真实 src ADS point view 同形行，不伪造 connection_id。"""
    return {
        "point_table_id": table_id,
        "point_item_id": point_id,
        "sort_order": point_id,
        "business_semantic_identifier": symbol.rsplit(".", 1)[-1].upper(),
        "business_semantic_name_zh": symbol.rsplit(".", 1)[-1].upper(),
        "physical_quantity_category": "ACTIVE_POWER",
        "data_type": "FLOAT64",
        "unit": "MW",
        "scale_factor": 1,
        "offset_value": 0,
        "value_min": 0,
        "value_max": 5,
        "allowed_values": None,
        "value_update_mode": "PERIODIC",
        "value_update_interval_ms": 50,
        "addressing_mode": "SYMBOL",
        "ads_data_type": "LREAL",
        "symbol_name": symbol,
        "index_group": None,
        "index_offset": None,
        "notification_mode": "CYCLIC",
        "cycle_time_ms": 50,
        "max_delay_ms": 100,
    }


def test_loader_filters_and_orders_points_in_sql() -> None:
    """多连接、多点表由参数化 SQL 筛选并按 connection 升序装配。"""
    engine = _Engine()
    frame = AdsDbViewLoader(engine=cast(Engine, engine)).load([4, 3, 4])

    assert tuple(frame.columns) == SERVER_CONFIG_COLUMNS
    assert frame["connection_id"].drop_duplicates().tolist() == [3, 4]
    assert frame.loc[frame["connection_id"] == 4, "point_table_id"].tolist() == [40]
    assert frame.loc[frame["connection_id"] == 4, "point_identifier"].tolist() == [
        "MAIN.RotorSpeed"
    ]
    assert frame.loc[frame["connection_id"] == 3, "point_table_id"].tolist() == [30, 31]
    assert frame.loc[frame["connection_id"] == 3, "point_identifier"].tolist() == [
        "MAIN.ActivePower",
        "MAIN.ReactivePower",
    ]
    data_queries = [
        query for query in engine.connection.queries if "SELECT" in query[0]
    ]
    assert len(data_queries) == 2
    assert all("connection_ids" in (params or {}) for _sql, params in data_queries)
    assert "JOIN whale.vw_src_point_table" in data_queries[1][0]
    assert "ORDER BY point_tables.connection_id" in data_queries[1][0]
    assert (
        frame.loc[frame["connection_id"] == 3, "ams_net_id"].eq("127.0.0.1.1.3").all()
    )


def test_loader_none_queries_all_without_where() -> None:
    """None 读取全部 connection 与 point rows，SQL 不包含 WHERE。"""
    engine = _Engine()
    frame = AdsDbViewLoader(engine=cast(Engine, engine)).load()

    assert frame["connection_id"].drop_duplicates().tolist() == [3, 4]
    data_queries = [
        query for query in engine.connection.queries if "SELECT" in query[0]
    ]
    assert all("WHERE" not in sql for sql, _params in data_queries)
    assert all(params is None for _sql, params in data_queries)


def test_loader_rejects_missing_and_empty_ids() -> None:
    """缺失任一请求 connection 或传入空列表时返回明确错误。"""
    loader = AdsDbViewLoader(engine=cast(Engine, _Engine()))

    with pytest.raises(AdsDbViewLoadError, match=r"connection_id: \[999\]"):
        loader.load([3, 999])
    with pytest.raises(AdsDbViewLoadError, match="connection_ids 不能为空"):
        loader.load([])


def test_loader_preserves_protocol_role_without_normalization() -> None:
    """数据库角色值原样透传，格式拒绝属于后续 protocol 边界职责。"""
    frame = AdsDbViewLoader(engine=cast(Engine, _Engine(role=" ads-server "))).load([3])

    assert frame["station_role"].unique().tolist() == [" ads-server "]
