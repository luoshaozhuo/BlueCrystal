"""Starfish CLI 的 DB selector 与生命周期测试。"""

from __future__ import annotations

from typing import Any

import pytest

import pacific.starfish.__main__ as starfish_cli
from pacific.starfish.__main__ import main
from starfish.adapters.db_views import DbViewLoadError


class _FakeManager:
    """记录 CLI 装配参数和生命周期调用。"""

    calls: list[dict[str, Any]] = []
    instances: list["_FakeManager"] = []
    fail = False

    def __init__(self) -> None:
        self.started = False
        self.stopped = False
        self.instances.append(self)

    @classmethod
    def build(
        cls,
        db_url: str,
        connection_ids: list[int] | None,
    ) -> "_FakeManager":
        cls.calls.append({"db_url": db_url, "connection_ids": connection_ids})
        if cls.fail:
            raise DbViewLoadError("fake load failed")
        return cls()

    @property
    def server_count(self) -> int:
        return 1

    def describe(self) -> dict[str, Any]:
        return {
            "server_count": 1,
            "servers": [
                {
                    "connection_id": 1001,
                    "name": "IEC104 Server",
                    "protocol": "IEC104",
                    "bind_host": "127.0.0.1",
                    "bind_port": 2404,
                    "point_count": 1,
                    "capabilities": ["IEC104_SIMULATOR"],
                }
            ],
        }

    def start(self) -> None:
        self.started = True

    def stop(self) -> None:
        self.stopped = True


def _build_fake_manager(
    db_url: str,
    connection_ids: list[int] | None,
) -> _FakeManager:
    """以 composition function 契约调用 fake manager factory。"""
    return _FakeManager.build(db_url, connection_ids)


@pytest.fixture(autouse=True)
def _reset_fake_manager() -> None:
    _FakeManager.calls.clear()
    _FakeManager.instances.clear()
    _FakeManager.fail = False


@pytest.mark.parametrize(
    "argv, expected",
    [
        (["run", "-id", "1001", "--duration", "0"], [1001]),
        (["run", "-a", "--duration", "0"], None),
    ],
)
def test_run_uses_whale_db_url(
    argv: list[str],
    expected: list[int] | None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("WHALE_DB_URL", "postgresql://db")
    monkeypatch.setattr(
        starfish_cli, "build_server_manager_from_db", _build_fake_manager
    )

    assert main(argv) == 0
    assert _FakeManager.calls == [
        {"db_url": "postgresql://db", "connection_ids": expected}
    ]
    assert _FakeManager.instances[0].started is True
    assert _FakeManager.instances[0].stopped is True


def test_run_requires_one_selector(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WHALE_DB_URL", "postgresql://db")
    monkeypatch.setattr(
        starfish_cli, "build_server_manager_from_db", _build_fake_manager
    )

    assert main(["run"]) == 1
    assert main(["run", "-id", "1", "-a"]) == 1
    assert _FakeManager.calls == []


def test_run_requires_db_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("WHALE_DB_URL", raising=False)
    monkeypatch.setattr(
        starfish_cli, "build_server_manager_from_db", _build_fake_manager
    )

    assert main(["run", "-id", "1", "--duration", "0"]) == 1


def test_run_reports_db_load_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WHALE_DB_URL", "postgresql://db")
    monkeypatch.setattr(
        starfish_cli, "build_server_manager_from_db", _build_fake_manager
    )
    _FakeManager.fail = True

    assert main(["run", "-id", "1", "--duration", "0"]) == 1


def test_only_run_command_is_exposed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        starfish_cli, "build_server_manager_from_db", _build_fake_manager
    )

    with pytest.raises(SystemExit):
        main(["read"])
