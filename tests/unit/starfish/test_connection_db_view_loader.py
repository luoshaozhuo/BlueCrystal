"""通用 connection loader 与 composition Engine 生命周期单元测试。

测试使用精确 SQLAlchemy Engine/Connection 替身验证资源所有权，不连接真实数据库；
真实 view 与协议 server 行为由 Starfish integration tests 另行覆盖。
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import Any, cast

import pandas as pd
import pytest
from sqlalchemy.engine import Engine

import starfish.composition as composition
from starfish.adapters.db_views import ConnectionDbViewLoader, DbViewLoadError
from starfish.core.config_frames import (
    CONNECTION_FRAME_COLUMNS,
    empty_server_config_frame,
    normalize_server_config_frame,
)
from starfish.core.definitions import ServerDefinition, ServerStatus


class _FakeResult:
    """提供 loader 使用的 mapping rows。"""

    def __init__(self, rows: Iterable[dict[str, Any]]) -> None:
        self._rows = list(rows)

    def mappings(self) -> list[dict[str, Any]]:
        """返回预设 rows。"""
        return self._rows


class _FakeConnection:
    """记录 SQL 调用并返回 view-shaped connection rows。"""

    def __init__(self, engine: _FakeEngine) -> None:
        self._engine = engine

    def __enter__(self) -> _FakeConnection:
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        return None

    def execute(
        self, stmt: object, params: dict[str, Any] | None = None
    ) -> _FakeResult:
        """只实现通用 connection loader 的 SQL 契约。"""
        self._engine.execute_calls += 1
        sql = str(stmt)
        self._engine.queries.append((sql, params))
        if "SET TRANSACTION READ ONLY" in sql:
            return _FakeResult([])
        if params is not None and "connection_ids" in params:
            assert "vw_comm_connection" in sql
            assert "connection_id IN" in sql
            requested = set((params or {})["connection_ids"])
            return _FakeResult(
                {
                    "connection_id": connection_id,
                    "protocol": self._engine.protocols[connection_id],
                }
                for connection_id in self._engine.connection_ids
                if connection_id in requested
            )
        if "vw_comm_connection" in sql:
            return _FakeResult(
                {
                    "connection_id": connection_id,
                    "protocol": self._engine.protocols[connection_id],
                }
                for connection_id in self._engine.connection_ids
            )
        raise AssertionError(f"unexpected sql: {sql}")


class _FakeEngine:
    """记录 connect/dispose 次数的 SQLAlchemy Engine 替身。"""

    def __init__(
        self,
        protocols: dict[int, str] | None = None,
    ) -> None:
        self.protocols = protocols if protocols is not None else {1: "IEC104", 2: "ADS"}
        self.connection_ids = list(self.protocols)
        self.connect_calls = 0
        self.execute_calls = 0
        self.dispose_calls = 0
        self.queries: list[tuple[str, dict[str, Any] | None]] = []

    def connect(self) -> _FakeConnection:
        """返回共享该 Engine 计数器的 connection。"""
        self.connect_calls += 1
        return _FakeConnection(self)

    def dispose(self) -> None:
        """记录 composition root 的确定性释放。"""
        self.dispose_calls += 1


@pytest.fixture(autouse=True)
def _read_sql_query_through_fake_connection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """让 pandas 查询走现有 SQLAlchemy connection 替身并保留 SQL 断言。"""

    def read_sql_query(
        stmt: object,
        conn: _FakeConnection,
        params: dict[str, Any] | None = None,
    ) -> pd.DataFrame:
        rows = conn.execute(stmt, params).mappings()
        columns = ["connection_id", "protocol"]
        return pd.DataFrame(rows, columns=columns)

    monkeypatch.setattr(pd, "read_sql_query", read_sql_query)


def test_connection_loader_lists_ids_and_preserves_protocol_identifiers() -> None:
    """合法 protocol identifiers 必须按数据库值原样返回。"""
    loader = ConnectionDbViewLoader(engine=cast(Engine, _FakeEngine()))

    all_connections = loader.load()
    selected = loader.load([2, 1])

    assert tuple(all_connections.columns) == CONNECTION_FRAME_COLUMNS
    assert all_connections.to_dict(orient="records") == [
        {"connection_id": 1, "protocol": "IEC104"},
        {"connection_id": 2, "protocol": "ADS"},
    ]
    assert selected["connection_id"].tolist() == [1, 2]
    assert selected["protocol"].tolist() == ["IEC104", "ADS"]


def test_connection_loader_uses_sql_filter_and_rejects_empty_ids() -> None:
    """None 不拼 WHERE，显式 IDs 参数化筛选，空列表保持公开拒绝语义。"""
    engine = _FakeEngine()
    loader = ConnectionDbViewLoader(engine=cast(Engine, engine))

    loader.load()
    loader.load([2])

    data_queries = [query for query in engine.queries if "SELECT" in query[0]]
    assert "WHERE" not in data_queries[0][0]
    assert data_queries[0][1] is None
    assert "connection_id IN" in data_queries[1][0]
    assert data_queries[1][1] == {"connection_ids": (2,)}
    with pytest.raises(DbViewLoadError, match="connection_ids 不能为空"):
        loader.load([])


def test_connection_loader_rejects_missing_id() -> None:
    """请求不存在的 ID 时返回稳定 loader 错误。"""
    loader = ConnectionDbViewLoader(engine=cast(Engine, _FakeEngine()))

    with pytest.raises(DbViewLoadError, match="未找到 connection_id"):
        loader.load([3])


class _RecordingProtocolLoader:
    """记录同一 Engine 注入及协议分组的 definition loader。"""

    def __init__(self, engine: Engine, protocol: str) -> None:
        self.engine = engine
        self.protocol = protocol
        self.calls: list[list[int]] = []

    def load(self, connection_ids: Sequence[int]) -> pd.DataFrame:
        """返回不持有 Engine 的一行一个 point 配置帧。"""
        self.calls.append(list(connection_ids))
        return pd.concat(
            [_configuration(value, self.protocol) for value in connection_ids],
            ignore_index=True,
        )


def _configuration(connection_id: int, protocol: str) -> pd.DataFrame:
    """生成 composition/factory 公共 schema 同形测试配置。"""
    return normalize_server_config_frame(
        pd.DataFrame(
            [
                {
                    "connection_id": connection_id,
                    "protocol": protocol,
                    "name": f"server-{connection_id}",
                    "bind_host": "127.0.0.1",
                    "bind_port": 20000 + connection_id,
                    "station_role": "CONTROLLED_STATION",
                    "point_table_id": connection_id * 10,
                    "point_item_id": connection_id * 100,
                    "sort_order": 1,
                }
            ]
        )
    )


@dataclass
class _LifecycleServer:
    """证明 manager 启动不再访问数据库的协议 worker。"""

    definition: ServerDefinition
    started: bool = False

    def init(self) -> None:
        """worker 初始化不访问 Engine。"""

    def start(self) -> None:
        """记录启动。"""
        self.started = True

    def stop(self) -> None:
        """记录停止。"""
        self.started = False

    def status(self) -> ServerStatus:
        """返回 core 状态快照。"""
        return ServerStatus(
            connection_id=self.definition.connection_id,
            protocol=self.definition.protocol,
            status="started" if self.started else "stopped",
            mode="fake",
            running=self.started,
            point_count=0,
        )


class _LifecycleFactory:
    """为 Engine 生命周期测试创建无外部依赖 worker。"""

    def create(self, configuration: pd.DataFrame) -> _LifecycleServer:
        """从单 connection 配置帧创建只持有 definition 的 worker。"""
        row = configuration.iloc[0]
        return _LifecycleServer(
            ServerDefinition(
                connection_id=int(row["connection_id"]),
                name=str(row["name"]),
                protocol=str(row["protocol"]),
                bind_host=str(row["bind_host"]),
                bind_port=int(row["bind_port"]),
            )
        )


def test_composition_uses_one_engine_for_all_loaders_and_disposes_before_start(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """混合 ID 按协议各批量加载一次，并保持装配与 Engine 语义。"""
    engine = _FakeEngine({1: "IEC104", 2: "ADS", 3: "IEC104", 4: "ADS"})
    create_calls: list[tuple[str, bool]] = []
    monkeypatch.setattr(
        composition,
        "create_engine",
        lambda url, future: create_calls.append((url, future)) or engine,
    )
    monkeypatch.setattr(composition, "ProtocolServerFactory", _LifecycleFactory)
    loaders: dict[str, _RecordingProtocolLoader] = {}

    def loader_factory(protocol: str):
        """记录 composition 注入的 Engine identity。"""

        def create(shared_engine: Engine) -> _RecordingProtocolLoader:
            loader = _RecordingProtocolLoader(shared_engine, protocol)
            loaders[protocol] = loader
            return loader

        return create

    manager = composition.build_server_manager_from_db(
        "postgresql://db",
        [3, 2, 1, 4, 3],
        loader_factories={
            "IEC104": loader_factory("IEC104"),
            "ADS": loader_factory("ADS"),
        },
    )

    assert create_calls == [("postgresql://db", True)]
    assert loaders["IEC104"].engine is engine
    assert loaders["ADS"].engine is engine
    assert loaders["IEC104"].calls == [[1, 3]]
    assert loaders["ADS"].calls == [[2, 4]]
    assert list(manager.servers) == [1, 2, 3, 4]
    assert engine.dispose_calls == 1
    calls_after_build = engine.connect_calls

    manager.start()
    assert engine.connect_calls == calls_after_build
    assert all(server.status().running for server in manager.servers.values())
    manager.stop()


def test_composition_disposes_engine_once_when_loader_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """protocol loader 异常不能泄漏 composition-owned Engine。"""
    engine = _FakeEngine({1: "IEC104"})
    monkeypatch.setattr(composition, "create_engine", lambda *_args, **_kwargs: engine)

    class _FailingLoader:
        """模拟 definition 加载失败。"""

        def load(self, connection_ids: Sequence[int]) -> pd.DataFrame:
            """抛出稳定测试异常。"""
            raise DbViewLoadError(f"fake load failed: {list(connection_ids)}")

    with pytest.raises(DbViewLoadError, match="fake load failed"):
        composition.build_server_manager_from_db(
            "postgresql://db",
            [1],
            loader_factories={"IEC104": lambda shared: _FailingLoader()},
        )

    assert engine.dispose_calls == 1


def test_composition_rejects_missing_definitions_and_disposes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """protocol loader 批量漏返 definition 时报错并释放共享 Engine。"""
    engine = _FakeEngine({1: "IEC104", 2: "IEC104"})
    monkeypatch.setattr(composition, "create_engine", lambda *_args, **_kwargs: engine)

    class _MissingDefinitionLoader:
        """模拟未返回任何 definition 的协议 loader。"""

        def load(self, connection_ids: Sequence[int]) -> pd.DataFrame:
            """接收整批 IDs，但故意返回空配置帧。"""
            return empty_server_config_frame()

    with pytest.raises(
        DbViewLoadError,
        match=r"protocol loader 未返回 connection configurations: \[1, 2\]",
    ):
        composition.build_server_manager_from_db(
            "postgresql://db",
            [2, 1],
            loader_factories={"IEC104": lambda shared: _MissingDefinitionLoader()},
        )

    assert engine.dispose_calls == 1


def test_composition_rejects_duplicate_configurations_and_disposes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """protocol loader 把同一 connection 归给两个协议时失败并释放 Engine。"""
    engine = _FakeEngine({1: "IEC104"})
    monkeypatch.setattr(composition, "create_engine", lambda *_args, **_kwargs: engine)

    class _DuplicateConfigurationLoader:
        """模拟同一 connection 返回两种 protocol 配置的错误 loader。"""

        def load(self, connection_ids: Sequence[int]) -> pd.DataFrame:
            """为请求 ID 返回冲突的 connection/protocol 关系。"""
            connection_id = connection_ids[0]
            return pd.concat(
                [
                    _configuration(connection_id, "IEC104"),
                    _configuration(connection_id, "ADS"),
                ],
                ignore_index=True,
            )

    with pytest.raises(
        DbViewLoadError,
        match=r"protocol loader 返回重复 connection configurations: \[1\]",
    ):
        composition.build_server_manager_from_db(
            "postgresql://db",
            [1],
            loader_factories={"IEC104": lambda shared: _DuplicateConfigurationLoader()},
        )

    assert engine.dispose_calls == 1


def test_list_helper_owns_and_disposes_its_short_lived_engine(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """独立 list helper 也不能泄漏自己创建的 Engine。"""
    engine = _FakeEngine()
    monkeypatch.setattr(composition, "create_engine", lambda *_args, **_kwargs: engine)

    frame = composition.list_connection_ids_from_db("postgresql://db")

    assert frame["connection_id"].tolist() == [1, 2]
    assert frame["protocol"].tolist() == ["IEC104", "ADS"]
    assert engine.dispose_calls == 1


def test_composition_rejects_unregistered_protocol_and_disposes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """协议未注册的异常路径仍准确释放共享 Engine。"""
    engine = _FakeEngine({2: "MODBUS_TCP"})
    monkeypatch.setattr(composition, "create_engine", lambda *_args, **_kwargs: engine)

    with pytest.raises(DbViewLoadError, match="未注册 protocol=MODBUS_TCP"):
        composition.build_server_manager_from_db("postgresql://db", [2])

    assert engine.dispose_calls == 1
