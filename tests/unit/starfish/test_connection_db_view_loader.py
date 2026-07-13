"""通用 connection view loader 与 composition protocol 分派测试。"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Any

import pytest

import starfish.composition as composition
from starfish.adapters.db_views import ConnectionDbViewLoader, DbViewLoadError
from starfish.core.definitions import ServerDefinition


class _FakeResult:
    def __init__(self, rows: Iterable[dict[str, Any]]) -> None:
        self._rows = list(rows)

    def mappings(self) -> list[dict[str, Any]]:
        return self._rows


class _FakeConnection:
    def __enter__(self) -> "_FakeConnection":
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        return None

    def execute(self, stmt: object, params: dict[str, Any] | None = None) -> _FakeResult:
        sql = str(stmt)
        if "SELECT connection_id, protocol" in sql:
            requested = set((params or {})["connection_ids"])
            rows = [
                {"connection_id": 1, "protocol": "iec104"},
                {"connection_id": 2, "protocol": "modbus-tcp"},
            ]
            return _FakeResult(row for row in rows if row["connection_id"] in requested)
        if "SELECT connection_id" in sql:
            return _FakeResult([{"connection_id": 1}, {"connection_id": 2}])
        raise AssertionError(f"unexpected sql: {sql}")


class _FakeEngine:
    def connect(self) -> _FakeConnection:
        return _FakeConnection()


def test_connection_loader_lists_ids_and_protocols() -> None:
    loader = ConnectionDbViewLoader(engine=_FakeEngine())

    assert loader.list_connection_ids() == [1, 2]
    assert loader.load_protocols([2, 1]) == {1: "IEC104", 2: "MODBUS_TCP"}


def test_connection_loader_rejects_missing_id() -> None:
    loader = ConnectionDbViewLoader(engine=_FakeEngine())

    with pytest.raises(DbViewLoadError, match="未找到 connection_id"):
        loader.load_protocols([3])


class _FakeConnectionIndex:
    def __init__(self, db_url: str) -> None:
        assert db_url == "db://test"

    def load_protocols(self, connection_ids: Sequence[int]) -> dict[int, str]:
        return {connection_id: "IEC104" for connection_id in connection_ids}


class _RecordingProtocolLoader:
    def __init__(self, db_url: str) -> None:
        assert db_url == "db://test"
        self.calls: list[list[int]] = []

    def load(self, connection_ids: Sequence[int]) -> list[ServerDefinition]:
        self.calls.append(list(connection_ids))
        return [
            ServerDefinition(
                connection_id=value,
                name=f"server-{value}",
                protocol="IEC104",
                bind_host="127.0.0.1",
                bind_port=2404,
            )
            for value in connection_ids
        ]


def test_composition_dispatches_ids_to_protocol_loader(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(composition, "ConnectionDbViewLoader", _FakeConnectionIndex)
    loader = _RecordingProtocolLoader("db://test")

    manager = composition.build_server_manager_from_db(
        "db://test",
        [2, 1, 2],
        loader_factories={"IEC104": lambda _url: loader},
    )

    assert loader.calls == [[2, 1]]
    assert list(manager.servers) == [2, 1]


class _UnsupportedConnectionIndex(_FakeConnectionIndex):
    def load_protocols(self, connection_ids: Sequence[int]) -> dict[int, str]:
        return {connection_id: "MODBUS_TCP" for connection_id in connection_ids}


def test_composition_rejects_unregistered_protocol(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        composition,
        "ConnectionDbViewLoader",
        _UnsupportedConnectionIndex,
    )

    with pytest.raises(DbViewLoadError, match="未注册 protocol=MODBUS_TCP"):
        composition.build_server_manager_from_db("db://test", [2])
