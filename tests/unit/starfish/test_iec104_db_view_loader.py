"""IEC104 DB view loader 单元测试。

验证：
1. `vw_connection_object_full`、`vw_task_full` 和 DB 登记 point item view 可组装
   Starfish runtime config。
2. all 模式只枚举 IEC104 connection。
3. point item view 名只接受 DB 登记的安全标识。

测试阶段：P1 开发期验证。
使用的替身：内存 fake SQLAlchemy engine/connection。
外部依赖：无真实 PostgreSQL、无 IEC104 native runner。
不能证明：真实 DB schema 存在或 native runner 完整协议行为。
NOT_RUN 条件：无。
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import pytest

from starfish.adapters.db_views.iec104 import Iec104DbViewLoadError, Iec104DbViewLoader


class _FakeResult:
    """模拟 SQLAlchemy Result.mappings()。"""

    def __init__(self, rows: Iterable[dict[str, Any]]) -> None:
        self._rows = list(rows)

    def mappings(self) -> list[dict[str, Any]]:
        """返回 mapping 行。"""
        return self._rows


class _FakeConnection:
    """按 SQL 片段返回固定执行视图数据。"""

    def __init__(self, *, unsafe_view: bool = False, protocol: str = "IEC104") -> None:
        self.unsafe_view = unsafe_view
        self.protocol = protocol

    def __enter__(self) -> "_FakeConnection":
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        return None

    def execute(self, stmt: object, params: dict[str, Any] | None = None) -> _FakeResult:
        """根据查询目标返回 fake rows。"""
        sql = str(stmt)
        params = params or {}
        if "SELECT connection_id" in sql:
            return _FakeResult([{"connection_id": 1001}, {"connection_id": 1002}])
        if "vw_connection_object_full" in sql:
            view_name = "vw_iec104_point_item;drop table whale.task" if self.unsafe_view else "vw_iec104_point_item"
            return _FakeResult(
                [
                    {
                        "connection_id": params["connection_id"],
                        "asset_id": 501,
                        "asset_identifier": f"rtu-{params['connection_id']}",
                        "asset_name": "IEC104 RTU",
                        "asset_type_code": "RTU",
                        "asset_type_name": "远动终端",
                        "protocol": self.protocol,
                        "connection_params_json": {
                            "host": "0.0.0.0",
                            "port": 2404,
                            "common_address": 1,
                            "t0_ms": 30000,
                            "t1_ms": 15000,
                            "t2_ms": 10000,
                            "t3_ms": 20000,
                            "timeout_ms": 3000,
                        },
                        "point_item_view_name": view_name,
                    }
                ]
            )
        if "vw_task_full" in sql:
            return _FakeResult(
                [
                    {
                        "task_id": 9001,
                        "task_identifier": "iec104-poll",
                        "connection_id": params["connection_id"],
                        "protocol": "IEC104",
                        "task_type": "POLL",
                        "task_status": "ENABLED",
                        "task_params_json": {"timeout_ms": 3000, "retry_count": 1},
                        "point_item_ids_json": [11, 12],
                        "point_item_view_name": "vw_iec104_point_item",
                    }
                ]
            )
        if "vw_iec104_point_item" in sql:
            return _FakeResult(
                [
                    {
                        "point_item_id": 11,
                        "table_id": 7,
                        "point_identifier": "p-active-power",
                        "semantic_identifier": "active_power",
                        "semantic_name": "有功功率",
                        "unit_code": "kW",
                        "scale": 1,
                        "offset_value": 0,
                        "value_min": -1000,
                        "value_max": 1000,
                        "allowed_values": None,
                        "type_id": "M_ME_NC_1",
                        "common_address": 1,
                        "io_address": 10001,
                        "data_type": "FLOAT64",
                        "quality_descriptor_enabled": True,
                        "time_tag_enabled": True,
                    },
                    {
                        "point_item_id": 12,
                        "table_id": 7,
                        "point_identifier": "p-breaker",
                        "semantic_identifier": "breaker",
                        "semantic_name": "断路器",
                        "unit_code": "BOOL",
                        "scale": 1,
                        "offset_value": 0,
                        "value_min": None,
                        "value_max": None,
                        "allowed_values": "0,1",
                        "type_id": "M_SP_NA_1",
                        "common_address": 1,
                        "io_address": 10002,
                        "data_type": "BOOLEAN",
                        "quality_descriptor_enabled": True,
                        "time_tag_enabled": False,
                    },
                ]
            )
        raise AssertionError(f"unexpected sql: {sql}")


class _FakeEngine:
    """测试用 SQLAlchemy engine 替身。"""

    def __init__(self, *, unsafe_view: bool = False, protocol: str = "IEC104") -> None:
        self.unsafe_view = unsafe_view
        self.protocol = protocol

    def connect(self) -> _FakeConnection:
        """返回 fake connection context manager。"""
        return _FakeConnection(unsafe_view=self.unsafe_view, protocol=self.protocol)


def test_loader_builds_iec104_config_from_registered_views() -> None:
    loader = Iec104DbViewLoader(engine=_FakeEngine())

    loaded = loader.load([1001])

    assert len(loaded) == 1
    server = loaded[0]
    assert server.connection_id == 1001
    assert server.protocol == "IEC104"
    assert server.bind_host == "0.0.0.0"
    assert server.bind_port == 2404
    assert [point.point_item_id for point in server.point_items] == [11, 12]
    assert server.point_items[0].io_address == 10001
    assert server.point_items[0].type_id == "M_ME_NC_1"
    assert server.connection_params["common_address"] == 1
    assert server.tasks[0].task_type == "POLL"


def test_loader_loads_multiple_dispatched_connection_ids() -> None:
    loader = Iec104DbViewLoader(engine=_FakeEngine())

    loaded = loader.load([1001, 1002])

    assert [server.connection_id for server in loaded] == [1001, 1002]


def test_loader_rejects_non_iec104_connection() -> None:
    loader = Iec104DbViewLoader(engine=_FakeEngine(protocol="MODBUS"))

    with pytest.raises(Iec104DbViewLoadError, match="不是 IEC104"):
        loader.load([1001])


def test_loader_rejects_unsafe_point_view_name() -> None:
    loader = Iec104DbViewLoader(engine=_FakeEngine(unsafe_view=True))

    with pytest.raises(Iec104DbViewLoadError, match="非法 point_item_view_name"):
        loader.load([1001])
