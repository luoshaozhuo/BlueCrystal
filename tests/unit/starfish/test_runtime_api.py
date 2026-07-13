"""Starfish manager 与 IEC104 worker 生命周期测试。"""

from __future__ import annotations

from dataclasses import dataclass
import pytest

from starfish.adapters.db_views import DbViewLoadError
from starfish.composition import build_server_manager_from_db
from starfish.core import StarfishServerManager
from starfish.core.definitions import ServerDefinition, ServerStatus


@dataclass
class _FakeServer:
    """记录 manager 生命周期调用的 server worker。"""

    definition: ServerDefinition
    fail_start: bool = False

    def __post_init__(self) -> None:
        self.calls: list[str] = []

    def init(self) -> None:
        self.calls.append("init")

    def start(self) -> None:
        self.calls.append("start")
        if self.fail_start:
            raise RuntimeError("start failed")

    def stop(self) -> None:
        self.calls.append("stop")

    def status(self) -> ServerStatus:
        return ServerStatus(
            connection_id=self.definition.connection_id,
            protocol="IEC104",
            status="started" if "start" in self.calls else "stopped",
            mode="fake",
            running="start" in self.calls and "stop" not in self.calls,
            point_count=len(self.definition.point_items),
        )


def _definition(connection_id: int) -> ServerDefinition:
    return ServerDefinition(
        connection_id=connection_id,
        name=f"server-{connection_id}",
        protocol="IEC104",
        bind_host="127.0.0.1",
        bind_port=2404,
    )


def test_manager_controls_server_workers() -> None:
    first = _FakeServer(_definition(1))
    second = _FakeServer(_definition(2))
    manager = StarfishServerManager([first, second])

    manager.start()

    assert manager.server_count == 2
    assert first.calls == ["init", "start"]
    assert second.calls == ["init", "start"]
    assert manager.status()["servers"][1]["running"] is True

    manager.stop()
    assert first.calls[-1] == "stop"
    assert second.calls[-1] == "stop"


def test_manager_rejects_duplicate_connection_id() -> None:
    with pytest.raises(ValueError, match="重复 connection_id"):
        StarfishServerManager([_FakeServer(_definition(1)), _FakeServer(_definition(1))])


def test_manager_rolls_back_started_workers() -> None:
    first = _FakeServer(_definition(1))
    second = _FakeServer(_definition(2), fail_start=True)
    manager = StarfishServerManager([first, second])

    with pytest.raises(RuntimeError, match="start failed"):
        manager.start()

    assert first.calls == ["init", "start", "stop"]
    assert second.calls == ["init", "start"]


def test_manager_has_no_data_read_write_api() -> None:
    manager = StarfishServerManager([_FakeServer(_definition(1))])

    assert not hasattr(manager, "read")
    assert not hasattr(manager, "write")


def test_composition_requires_connection_ids() -> None:
    with pytest.raises(DbViewLoadError, match="connection_ids 不能为空"):
        build_server_manager_from_db("sqlite://", [])
