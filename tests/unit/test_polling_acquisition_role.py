"""PollingAcquisitionRole 单元测试。

这些测试覆盖连接级隔离、read-once 和可靠关闭语义。
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import cast

import pytest

from whale.ingest.ports.source.source_acquisition_port import (
    SourceReadError,
    SourceReadOnceFailedError,
    SourceSubscriptionHandle,
    SubscriptionStateHandler,
)
from whale.ingest.ports.state import SourceStateCacheWriteError
from whale.ingest.usecases.dtos.acquired_node_state import (
    AcquiredNodeStateBatch,
    AcquiredNodeValue,
)
from whale.ingest.usecases.dtos.source_acquisition_request import (
    AcquisitionExecutionOptions,
    AcquisitionItemData,
    SourceAcquisitionRequest,
)
from whale.ingest.usecases.dtos.source_connection_data import SourceConnectionData
from whale.ingest.usecases.roles.polling_acquisition_role import (
    PollingAcquisitionRole,
    PollingAcquisitionSession,
)


@dataclass
class FakeStateCachePort:
    """记录状态缓存调用的假对象。"""

    updates: list[tuple[str, AcquiredNodeStateBatch]] = field(default_factory=list)
    alive_marks: list[tuple[str, datetime]] = field(default_factory=list)
    unavailable_marks: list[tuple[str, str, str | None]] = field(default_factory=list)
    update_error: Exception | None = None

    def update(self, *, ld_name: str, batch: AcquiredNodeStateBatch) -> int:
        if self.update_error is not None:
            raise self.update_error
        self.updates.append((ld_name, batch))
        return len(batch.values)

    def mark_alive(self, *, ld_name: str, observed_at: datetime) -> None:
        self.alive_marks.append((ld_name, observed_at))

    def mark_unavailable(
        self,
        *,
        ld_name: str,
        status: str,
        observed_at: datetime,
        reason: str | None = None,
    ) -> None:
        del observed_at
        self.unavailable_marks.append((ld_name, status, reason))


class FakeAcquisitionPort:
    """按 LD 名称返回预置结果的假采集端口。"""

    def __init__(self, results: dict[str, AcquiredNodeStateBatch | Exception]) -> None:
        self.results = results

    def supports_subscription(
        self,
        execution: AcquisitionExecutionOptions,
        connection: SourceConnectionData,
    ) -> bool:
        """返回 polling 测试中永远不会走到的订阅能力。"""

        del execution, connection
        return False

    async def read(
        self,
        execution: AcquisitionExecutionOptions,
        connection: SourceConnectionData,
        items: list[AcquisitionItemData],
    ) -> AcquiredNodeStateBatch:
        del execution, items
        result = self.results[connection.ld_name]
        if isinstance(result, Exception):
            raise result
        return result

    async def start_subscription(
        self,
        execution: AcquisitionExecutionOptions,
        connection: SourceConnectionData,
        items: list[AcquisitionItemData],
        *,
        state_received: SubscriptionStateHandler,
    ) -> SourceSubscriptionHandle:
        del execution, connection, items, state_received
        raise AssertionError("start_subscription should not be used in polling tests")


def _request(
    *,
    acquisition_mode: str | None = None,
    max_iteration: int | None = 1,
    connections: list[SourceConnectionData] | None = None,
) -> SourceAcquisitionRequest:
    return SourceAcquisitionRequest(
        request_id="request-1",
        task_id=1,
        execution=AcquisitionExecutionOptions(
            protocol="opcua",
            transport="tcp",
            acquisition_mode=acquisition_mode or ("POLLING" if max_iteration is None else "READ_ONCE"),
            interval_ms=10,
            max_iteration=max_iteration,
            request_timeout_ms=500,
            freshness_timeout_ms=30_000,
            alive_timeout_ms=60_000,
        ),
        connections=connections
        or [
            SourceConnectionData(
                host="127.0.0.1",
                port=4840,
                ied_name="IED_01",
                ld_name="LD_01",
                namespace_uri="urn:test",
            )
        ],
        items=[AcquisitionItemData(key="TotW", profile_item_id=1, relative_path="TotW")],
    )


def _batch(ld_name: str, *, values: list[AcquiredNodeValue] | None = None) -> AcquiredNodeStateBatch:
    now = datetime.now(tz=UTC)
    return AcquiredNodeStateBatch(
        source_id=ld_name,
        batch_observed_at=now,
        client_received_at=now,
        client_processed_at=now,
        values=(
            values
            if values is not None
            else [AcquiredNodeValue(node_key="TotW", value="1", quality="GOOD")]
        ),
    )


def test_single_connection_success_updates_cache_and_marks_alive() -> None:
    state_cache = FakeStateCachePort()
    role = PollingAcquisitionRole(
        acquisition_port=FakeAcquisitionPort({"LD_01": _batch("LD_01")}),
        state_cache_port=state_cache,
    )

    async def _run() -> None:
        result = role.start(_request(acquisition_mode="POLLING", max_iteration=1))
        session = cast(PollingAcquisitionSession, result.sessions[0])
        await session.task

    asyncio.run(_run())

    assert len(state_cache.updates) == 1
    assert state_cache.updates[0][0] == "LD_01"
    assert len(state_cache.alive_marks) == 1
    assert state_cache.unavailable_marks == []


def test_empty_batch_does_not_update_cache_or_mark_alive() -> None:
    state_cache = FakeStateCachePort()
    role = PollingAcquisitionRole(
        acquisition_port=FakeAcquisitionPort({"LD_01": _batch("LD_01", values=[])}),
        state_cache_port=state_cache,
    )

    async def _run() -> None:
        result = role.start(_request(acquisition_mode="POLLING", max_iteration=1))
        session = cast(PollingAcquisitionSession, result.sessions[0])
        await session.task

    asyncio.run(_run())

    assert state_cache.updates == []
    assert state_cache.alive_marks == []


def test_read_failure_marks_connection_unavailable() -> None:
    state_cache = FakeStateCachePort()
    role = PollingAcquisitionRole(
        acquisition_port=FakeAcquisitionPort({"LD_01": SourceReadError("runner_not_available")}),
        state_cache_port=state_cache,
    )

    async def _run() -> None:
        result = role.start(_request(acquisition_mode="POLLING", max_iteration=1))
        session = cast(PollingAcquisitionSession, result.sessions[0])
        await session.task

    asyncio.run(_run())

    assert state_cache.updates == []
    assert state_cache.alive_marks == []
    assert state_cache.unavailable_marks == [("LD_01", "ERROR", "runner_not_available")]


def test_read_once_all_failed_raises_aggregate_error() -> None:
    state_cache = FakeStateCachePort()
    role = PollingAcquisitionRole(
        acquisition_port=FakeAcquisitionPort({"LD_01": SourceReadError("runner_not_available")}),
        state_cache_port=state_cache,
    )

    async def _run() -> None:
        result = role.start(_request())
        session = cast(PollingAcquisitionSession, result.sessions[0])
        await session.task

    with pytest.raises(SourceReadOnceFailedError, match="all connections failed in read_once"):
        asyncio.run(_run())

    assert state_cache.unavailable_marks == [("LD_01", "ERROR", "runner_not_available")]


def test_cache_write_failure_does_not_mark_connection_alive_or_unavailable() -> None:
    state_cache = FakeStateCachePort(update_error=SourceStateCacheWriteError("redis_oom"))
    role = PollingAcquisitionRole(
        acquisition_port=FakeAcquisitionPort({"LD_01": _batch("LD_01")}),
        state_cache_port=state_cache,
    )

    async def _run() -> None:
        result = role.start(_request(acquisition_mode="POLLING", max_iteration=1))
        session = cast(PollingAcquisitionSession, result.sessions[0])
        await session.task

    asyncio.run(_run())

    assert state_cache.updates == []
    assert state_cache.alive_marks == []
    assert state_cache.unavailable_marks == []


def test_one_connection_failure_does_not_block_other_connections() -> None:
    connections = [
        SourceConnectionData(
            host="127.0.0.1",
            port=4840,
            ied_name="IED_01",
            ld_name="LD_01",
            namespace_uri="urn:test",
        ),
        SourceConnectionData(
            host="127.0.0.2",
            port=4841,
            ied_name="IED_02",
            ld_name="LD_02",
            namespace_uri="urn:test",
        ),
    ]
    state_cache = FakeStateCachePort()
    role = PollingAcquisitionRole(
        acquisition_port=FakeAcquisitionPort(
            {
                "LD_01": _batch("LD_01"),
                "LD_02": SourceReadError("raw read failed: read_failed"),
            }
        ),
        state_cache_port=state_cache,
    )

    async def _run() -> None:
        result = role.start(_request(connections=connections))
        session = cast(PollingAcquisitionSession, result.sessions[0])
        await session.task

    asyncio.run(_run())

    assert [ld_name for ld_name, _ in state_cache.updates] == ["LD_01"]
    assert [ld_name for ld_name, _ in state_cache.alive_marks] == ["LD_01"]
    assert state_cache.unavailable_marks == [("LD_02", "ERROR", "source_read_failed")]


def test_max_iteration_one_finishes_normally() -> None:
    state_cache = FakeStateCachePort()
    role = PollingAcquisitionRole(
        acquisition_port=FakeAcquisitionPort({"LD_01": _batch("LD_01")}),
        state_cache_port=state_cache,
    )

    async def _run() -> tuple[bool, bool]:
        result = role.start(_request(max_iteration=1))
        session = cast(PollingAcquisitionSession, result.sessions[0])
        await session.task
        return session.task.done(), session.task.cancelled()

    done, cancelled = asyncio.run(_run())

    assert done is True
    assert cancelled is False


def test_close_stops_long_running_polling_session() -> None:
    state_cache = FakeStateCachePort()
    role = PollingAcquisitionRole(
        acquisition_port=FakeAcquisitionPort({"LD_01": _batch("LD_01")}),
        state_cache_port=state_cache,
    )

    async def _run_close() -> None:
        result = role.start(_request(max_iteration=None))
        session = cast(PollingAcquisitionSession, result.sessions[0])
        await asyncio.sleep(0.02)
        await session.close()
        assert session.closed is True
        assert session.task.done()

    asyncio.run(_run_close())
