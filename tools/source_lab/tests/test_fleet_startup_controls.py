"""Tests for fleet startup concurrency and stagger controls."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from tools.source_lab.fleet import SourceSimulatorFleet
from tools.source_lab.model import SimulatedPoint, SimulatedSource, SourceConnection, UpdateConfig


def _source(index: int) -> SimulatedSource:
    return SimulatedSource(
        connection=SourceConnection(
            name=f"s{index}",
            ied_name=f"IED{index}",
            ld_name="LD0",
            host="127.0.0.1",
            port=54000 + index,
            transport="tcp",
            protocol="opcua",
            namespace_uri=f"urn:test:{index}",
        ),
        points=(SimulatedPoint(ln_name="LN0", do_name="Do", unit=None, data_type="FLOAT64"),),
    )


def test_create_reads_startup_controls_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SOURCE_SIM_FLEET_START_CONCURRENCY", "4")
    monkeypatch.setenv("SOURCE_SIM_FLEET_START_STAGGER_MS", "15")

    fleet = SourceSimulatorFleet.create(
        (_source(1),),
        update_config=UpdateConfig(),
    )

    assert fleet.start_concurrency == 4
    assert fleet.start_stagger_ms == 15


@dataclass
class _FakeEvent:
    is_ready: bool = False

    def set(self) -> None:
        self.is_ready = True

    def is_set(self) -> bool:
        return self.is_ready

    def wait(self, timeout: float) -> bool:
        return self.is_ready


class _FakeQueue:
    def get_nowait(self) -> str:
        raise Exception("queue empty")

    def close(self) -> None:
        return None

    def join_thread(self) -> None:
        return None


class _FakeProcess:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.name = kwargs.get("name", "fake")
        self.exitcode: int | None = None
        self._started = False
        self.pid: int | None = None

    def start(self) -> None:
        self._started = True
        self.pid = 1234

    def is_alive(self) -> bool:
        return self._started


class _FakeContext:
    def Queue(self) -> _FakeQueue:
        return _FakeQueue()

    def Event(self) -> _FakeEvent:
        return _FakeEvent()

    def Process(self, *args: Any, **kwargs: Any) -> _FakeProcess:
        return _FakeProcess(*args, **kwargs)


def test_start_processes_applies_concurrency_and_stagger(monkeypatch: pytest.MonkeyPatch) -> None:
    fleet = SourceSimulatorFleet.create(
        (_source(1), _source(2), _source(3)),
        update_config=UpdateConfig(enabled=False),
        startup_timeout_seconds=10.0,
        start_concurrency=2,
        start_stagger_ms=10,
    )

    monkeypatch.setattr("tools.source_lab.fleet.multiprocessing.get_context", lambda: _FakeContext())

    sleep_calls: list[float] = []
    monkeypatch.setattr("tools.source_lab.fleet.time.sleep", lambda seconds: sleep_calls.append(seconds))

    wait_calls: list[set[int] | None] = []

    def _fake_wait_until_ready(
        *,
        pending_indices: set[int] | None = None,
        deadline: float | None = None,
    ) -> None:
        wait_calls.append(None if pending_indices is None else set(pending_indices))

    monkeypatch.setattr(fleet, "_wait_until_ready", _fake_wait_until_ready)

    fleet._start_processes()

    assert wait_calls[0] == {0, 1}
    assert wait_calls[1] == {2}
    assert wait_calls[2] is None
    assert sleep_calls == [0.01, 0.01, 0.01]
