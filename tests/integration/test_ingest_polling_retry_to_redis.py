"""Integration tests for polling retry semantics against Redis latest-state cache."""

from __future__ import annotations

import asyncio
import socket
from collections.abc import Callable
from contextlib import closing
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any, Protocol

import pytest

from tests.support.source_lab_runtime import import_source_lab_module
from whale.ingest.adapters.source.opcua_source_acquisition_adapter import (
    OpcUaSourceAcquisitionAdapter,
)
from whale.ingest.adapters.state.redis_source_state_cache import (
    RedisHashClient,
    RedisPipeline,
    RedisSourceStateCache,
    RedisSourceStateCacheSettings,
)
from whale.ingest.ports.source.source_acquisition_port import (
    SourceAcquisitionPort,
    SourceBatchMismatchError,
    SourceReadError,
    SourceSubscriptionHandle,
    SubscriptionStateHandler,
)
from whale.ingest.usecases import SourceAcquisitionUseCase
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
from whale.ingest.usecases.roles.polling_acquisition_role import PollingAcquisitionRole
from whale.ingest.usecases.roles.subscription_acquisition_role import (
    SubscriptionAcquisitionRole,
)

_MODEL_MODULE = import_source_lab_module("tools.source_lab.model")
_ADDRESS_SPACE_MODULE = import_source_lab_module("tools.source_lab.protocols.opcua.address_space")
_SIMULATOR_MODULE = import_source_lab_module("tools.source_lab.protocols.opcua.open62541_source_simulator")

SimulatedPoint = _MODEL_MODULE.SimulatedPoint
SimulatedSource = _MODEL_MODULE.SimulatedSource
SourceConnection = _MODEL_MODULE.SourceConnection
logical_path = _ADDRESS_SPACE_MODULE.logical_path
Open62541SourceSimulator = _SIMULATOR_MODULE.Open62541SourceSimulator
resolve_runner_path = _SIMULATOR_MODULE.resolve_runner_path


class _SimulatedConnectionLike(Protocol):
    host: str
    port: int
    ied_name: str
    ld_name: str
    namespace_uri: str | None


class _SimulatedPointLike(Protocol):
    key: str


class _SimulatedSourceLike(Protocol):
    connection: _SimulatedConnectionLike
    points: tuple[_SimulatedPointLike, ...]


def _require_runner() -> None:
    if not resolve_runner_path().exists():
        pytest.skip("open62541 runner executable does not exist")


def _choose_available_port() -> int:
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _build_source(name: str, ld_name: str, port: int, *, initial_value: float = 12.5) -> Any:
    return SimulatedSource(
        connection=SourceConnection(
            name=name,
            ied_name=f"{name}_IED",
            ld_name=ld_name,
            host="127.0.0.1",
            port=port,
            transport="tcp",
            protocol="opcua",
            namespace_uri=f"urn:whale:{name}",
        ),
        points=(
            SimulatedPoint(
                ln_name="WPPD1",
                do_name="TotW",
                unit="kW",
                data_type="FLOAT64",
                initial_value=initial_value,
            ),
        ),
    )


def _build_request(
    sources: list[_SimulatedSourceLike],
    *,
    acquisition_mode: str,
    max_iteration: int | None,
    interval_ms: int = 100,
) -> SourceAcquisitionRequest:
    items = [
        AcquisitionItemData(
            key=sources[0].points[0].key,
            profile_item_id=1,
            relative_path=logical_path(sources[0].connection, sources[0].points[0]),
        )
    ]
    return SourceAcquisitionRequest(
        request_id=f"polling-{acquisition_mode.lower()}",
        task_id=11,
        execution=AcquisitionExecutionOptions(
            protocol="opcua",
            transport="tcp",
            acquisition_mode=acquisition_mode,
            interval_ms=interval_ms,
            max_iteration=max_iteration,
            request_timeout_ms=2_000,
            freshness_timeout_ms=30_000,
            alive_timeout_ms=60_000,
            polling_max_concurrent_connections=4,
        ),
        connections=[
            SourceConnectionData(
                host=source.connection.host,
                port=source.connection.port,
                ied_name=source.connection.ied_name,
                ld_name=source.connection.ld_name,
                namespace_uri=source.connection.namespace_uri or "",
            )
            for source in sources
        ],
        items=items,
    )


def _build_redis_cache(
    redis_client: RedisHashClient,
    *,
    station_id: str,
    hash_key: str,
) -> RedisSourceStateCache:
    return RedisSourceStateCache(
        settings=RedisSourceStateCacheSettings(
            host="127.0.0.1",
            port=16379,
            db=15,
            username=None,
            password=None,
            hash_key=hash_key,
            station_id=station_id,
        ),
        client=redis_client,
    )


def _build_use_case(
    *,
    acquisition_port: SourceAcquisitionPort,
    state_cache: RedisSourceStateCache,
) -> SourceAcquisitionUseCase:
    return SourceAcquisitionUseCase(
        polling_role=PollingAcquisitionRole(
            acquisition_port=acquisition_port,
            state_cache_port=state_cache,
        ),
        subscription_role=SubscriptionAcquisitionRole(
            acquisition_port=acquisition_port,
            state_cache_port=state_cache,
        ),
    )


async def _wait_for_snapshot(
    cache: RedisSourceStateCache,
    predicate: Callable[[list[Any]], bool],
    *,
    timeout_seconds: float = 8.0,
) -> list[Any]:
    deadline = asyncio.get_running_loop().time() + timeout_seconds
    while asyncio.get_running_loop().time() < deadline:
        snapshot = cache.read_snapshot()
        if predicate(snapshot):
            return snapshot
        await asyncio.sleep(0.1)
    pytest.fail("snapshot did not reach expected state within timeout")


@pytest.mark.integration
def test_polling_offline_online_offline_recovered_with_real_simulator(
    monkeypatch: pytest.MonkeyPatch,
    real_redis_client: Any,
    real_redis_hash_key: str,
) -> None:
    """Cover device offline at startup, online recovery, mid-run offline, and recovery."""

    _require_runner()
    monkeypatch.setenv("SOURCE_SIM_POLL_SOURCE_UPDATE_ENABLED", "false")
    source = _build_source("wf-source-a", "LD_A", _choose_available_port())
    cache = _build_redis_cache(
        real_redis_client,
        station_id="station-polling-retry",
        hash_key=real_redis_hash_key,
    )
    use_case = _build_use_case(
        acquisition_port=OpcUaSourceAcquisitionAdapter(),
        state_cache=cache,
    )
    request = _build_request([source], acquisition_mode="POLLING", max_iteration=None)

    async def _run() -> None:
        result = await use_case.start(request)
        session = result.sessions[0]
        try:
            offline_snapshot = await _wait_for_snapshot(
                cache,
                lambda rows: len(rows) == 1 and rows[0].availability_status == "ERROR",
            )
            assert offline_snapshot[0].unavailable_reason in {
                "source_read_failed",
                "runner_not_available",
            }

            simulator = Open62541SourceSimulator(source)
            simulator.start()
            try:
                online_snapshot = await _wait_for_snapshot(
                    cache,
                    lambda rows: len(rows) == 1
                    and rows[0].availability_status == "VALID"
                    and rows[0].values
                    and rows[0].values[0].value == "12.5",
                )
                assert online_snapshot[0].unavailable_reason is None

                simulator.writes({source.points[0].key: 18.75})
                await _wait_for_snapshot(
                    cache,
                    lambda rows: rows[0].values and rows[0].values[0].value == "18.75",
                )
                simulator.stop()

                offline_again_snapshot = await _wait_for_snapshot(
                    cache,
                    lambda rows: rows[0].availability_status == "ERROR",
                )
                assert offline_again_snapshot[0].values[0].value == "18.75"

                simulator.start()
                recovered_snapshot = await _wait_for_snapshot(
                    cache,
                    lambda rows: rows[0].availability_status == "VALID"
                    and rows[0].values
                    and rows[0].values[0].value == "12.5",
                )
                assert recovered_snapshot[0].unavailable_reason is None
            finally:
                simulator.stop()
        finally:
            await session.close()

    try:
        asyncio.run(_run())
    finally:
        real_redis_client.delete(real_redis_hash_key)


@pytest.mark.integration
def test_polling_multi_device_partial_failure_isolated_per_connection(
    real_redis_client: Any,
    real_redis_hash_key: str,
) -> None:
    """Keep healthy devices valid when one device fails in the same polling round."""

    cache = _build_redis_cache(
        real_redis_client,
        station_id="station-polling-partial",
        hash_key=real_redis_hash_key,
    )
    now = datetime(2026, 5, 22, 11, 0, tzinfo=UTC)
    use_case = _build_use_case(
        acquisition_port=FakeAcquisitionPortByLd(
            {
                "LD_1": _batch("11.0", server_timestamp=now),
                "LD_2": _batch("12.0", server_timestamp=now + timedelta(seconds=1)),
                "LD_3": SourceReadError("raw read failed: read_failed"),
            }
        ),
        state_cache=cache,
    )
    request = SourceAcquisitionRequest(
        request_id="polling-multi-device",
        task_id=31,
        execution=AcquisitionExecutionOptions(
            protocol="opcua",
            transport="tcp",
            acquisition_mode="READ_ONCE",
            interval_ms=100,
            max_iteration=1,
            request_timeout_ms=500,
            freshness_timeout_ms=30_000,
            alive_timeout_ms=60_000,
        ),
        connections=[
            SourceConnectionData(
                host="127.0.0.1",
                port=4840,
                ied_name="IED_1",
                ld_name="LD_1",
                namespace_uri="urn:test",
            ),
            SourceConnectionData(
                host="127.0.0.1",
                port=4841,
                ied_name="IED_2",
                ld_name="LD_2",
                namespace_uri="urn:test",
            ),
            SourceConnectionData(
                host="127.0.0.1",
                port=4842,
                ied_name="IED_3",
                ld_name="LD_3",
                namespace_uri="urn:test",
            ),
        ],
        items=[AcquisitionItemData(key="TotW", profile_item_id=1, relative_path="TotW")],
    )

    try:
        asyncio.run(use_case.start(request))

        snapshot_by_ld = {row.ld_name: row for row in cache.read_snapshot()}

        assert snapshot_by_ld["LD_1"].availability_status == "VALID"
        assert snapshot_by_ld["LD_2"].availability_status == "VALID"
        assert snapshot_by_ld["LD_3"].availability_status == "ERROR"
        assert snapshot_by_ld["LD_3"].unavailable_reason == "source_read_failed"
    finally:
        real_redis_client.delete(real_redis_hash_key)


class FakeSequenceAcquisitionPort(SourceAcquisitionPort):
    """Return pre-seeded outcomes for polling integration-light scenarios."""

    def __init__(self, outcomes: list[AcquiredNodeStateBatch | Exception]) -> None:
        self._outcomes = outcomes

    def supports_subscription(
        self,
        execution: AcquisitionExecutionOptions,
        connection: SourceConnectionData,
    ) -> bool:
        del execution, connection
        return False

    async def read(
        self,
        execution: AcquisitionExecutionOptions,
        connection: SourceConnectionData,
        items: list[AcquisitionItemData],
    ) -> AcquiredNodeStateBatch:
        del execution, connection, items
        outcome = self._outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    async def start_subscription(
        self,
        execution: AcquisitionExecutionOptions,
        connection: SourceConnectionData,
        items: list[AcquisitionItemData],
        *,
        state_received: SubscriptionStateHandler,
    ) -> SourceSubscriptionHandle:
        del execution, connection, items, state_received
        raise AssertionError("subscription should not be used in polling integration tests")


class FakeAcquisitionPortByLd(SourceAcquisitionPort):
    """Return one configured outcome for each LD name."""

    def __init__(self, outcomes: dict[str, AcquiredNodeStateBatch | Exception]) -> None:
        self._outcomes = outcomes

    def supports_subscription(
        self,
        execution: AcquisitionExecutionOptions,
        connection: SourceConnectionData,
    ) -> bool:
        del execution, connection
        return False

    async def read(
        self,
        execution: AcquisitionExecutionOptions,
        connection: SourceConnectionData,
        items: list[AcquisitionItemData],
    ) -> AcquiredNodeStateBatch:
        del execution, items
        outcome = self._outcomes[connection.ld_name]
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    async def start_subscription(
        self,
        execution: AcquisitionExecutionOptions,
        connection: SourceConnectionData,
        items: list[AcquisitionItemData],
        *,
        state_received: SubscriptionStateHandler,
    ) -> SourceSubscriptionHandle:
        del execution, connection, items, state_received
        raise AssertionError("subscription should not be used in polling integration tests")


def _one_connection_request(mode: str = "READ_ONCE") -> SourceAcquisitionRequest:
    return SourceAcquisitionRequest(
        request_id="polling-sequence",
        task_id=12,
        execution=AcquisitionExecutionOptions(
            protocol="opcua",
            transport="tcp",
            acquisition_mode=mode,
            interval_ms=100,
            max_iteration=1,
            request_timeout_ms=500,
            freshness_timeout_ms=30_000,
            alive_timeout_ms=60_000,
        ),
        connections=[
            SourceConnectionData(
                host="127.0.0.1",
                port=4840,
                ied_name="IED_1",
                ld_name="LD_SEQ",
                namespace_uri="urn:test",
            )
        ],
        items=[AcquisitionItemData(key="TotW", profile_item_id=1, relative_path="TotW")],
    )


def _batch(value: str, *, server_timestamp: datetime) -> AcquiredNodeStateBatch:
    return AcquiredNodeStateBatch(
        source_id="LD_SEQ",
        batch_observed_at=server_timestamp,
        client_received_at=server_timestamp,
        client_processed_at=server_timestamp,
        values=[
            AcquiredNodeValue(
                node_key="TotW",
                value=value,
                quality="GOOD",
                server_timestamp=server_timestamp,
            )
        ],
    )


@pytest.mark.integration
def test_polling_batch_mismatch_and_stale_update_keep_retry_semantics(
    real_redis_client: Any,
    real_redis_hash_key: str,
) -> None:
    """Cover protocol error and stale update behavior against the Redis cache."""

    cache = _build_redis_cache(
        real_redis_client,
        station_id="station-polling-sequence",
        hash_key=real_redis_hash_key,
    )
    now = datetime(2026, 5, 22, 12, 0, tzinfo=UTC)

    try:
        first_use_case = _build_use_case(
            acquisition_port=FakeSequenceAcquisitionPort([_batch("10.0", server_timestamp=now)]),
            state_cache=cache,
        )
        asyncio.run(first_use_case.start(_one_connection_request()))
        first_snapshot = cache.read_snapshot()[0]
        first_updated_at = first_snapshot.last_value_updated_at

        cache.mark_unavailable(
            ld_name="LD_SEQ",
            status="ERROR",
            observed_at=now + timedelta(seconds=1),
            reason="runner_not_available",
        )

        mismatch_use_case = _build_use_case(
            acquisition_port=FakeSequenceAcquisitionPort(
                [SourceBatchMismatchError("item_count_mismatch")]
            ),
            state_cache=cache,
        )
        with pytest.raises(Exception):
            asyncio.run(mismatch_use_case.start(_one_connection_request()))

        mismatch_snapshot = cache.read_snapshot()[0]
        assert mismatch_snapshot.availability_status == "ERROR"
        assert mismatch_snapshot.unavailable_reason == "batch_mismatch"

        stale_use_case = _build_use_case(
            acquisition_port=FakeSequenceAcquisitionPort(
                [_batch("9.0", server_timestamp=now - timedelta(seconds=5))]
            ),
            state_cache=cache,
        )
        asyncio.run(stale_use_case.start(_one_connection_request()))

        stale_snapshot = cache.read_snapshot()[0]
        assert stale_snapshot.availability_status == "ERROR"
        assert stale_snapshot.values[0].value == "10.0"
        assert stale_snapshot.last_value_updated_at == first_updated_at
    finally:
        real_redis_client.delete(real_redis_hash_key)


@dataclass
class FakePipeline(RedisPipeline):
    """Transaction pipeline fake for Redis write failure scenarios."""

    store: dict[str, str]
    execute_error: Exception | None = None
    staged: list[tuple[str, str, str]] = field(default_factory=list)

    def hset(self, name: str, key: str, value: str) -> object:
        self.staged.append((name, key, value))
        return 1

    def execute(self) -> object:
        if self.execute_error is not None:
            raise self.execute_error
        for _, key, value in self.staged:
            self.store[key] = value
        self.staged.clear()
        return None


@dataclass
class FakeRedisClient(RedisHashClient):
    """Redis hash fake with toggled pipeline failures."""

    store: dict[str, str] = field(default_factory=dict)
    pipeline_error: Exception | None = None

    def hset(self, name: str, key: str, value: str) -> int:
        del name
        self.store[key] = value
        return 1

    def hget(self, name: str, key: str) -> str | bytes | None:
        del name
        return self.store.get(key)

    def hgetall(self, name: str) -> dict[str, str]:
        del name
        return dict(self.store)

    def pipeline(self, transaction: bool = True) -> RedisPipeline:
        assert transaction is True
        return FakePipeline(
            self.store,
            execute_error=self.pipeline_error,
        )


@pytest.mark.integration
def test_polling_redis_write_failures_and_oom_do_not_advance_alive_state() -> None:
    """Cover Redis write failure and Redis OOM classification behavior."""

    client = FakeRedisClient()
    cache = RedisSourceStateCache(
        settings=RedisSourceStateCacheSettings(
            host="127.0.0.1",
            port=6379,
            db=0,
            username=None,
            password=None,
            hash_key="whale:integration:fake-redis",
            station_id="station-fake",
        ),
        client=client,
    )
    baseline = _batch("10.0", server_timestamp=datetime(2026, 5, 22, 13, 0, tzinfo=UTC))
    cache.update(ld_name="LD_SEQ", batch=baseline)
    initial_snapshot = cache.read_snapshot()[0]
    initial_alive_at = initial_snapshot.last_alive_at
    initial_value_updated_at = initial_snapshot.last_value_updated_at

    client.pipeline_error = RuntimeError("OOM command not allowed when used memory > 'maxmemory'")
    oom_use_case = _build_use_case(
        acquisition_port=FakeSequenceAcquisitionPort(
            [_batch("11.0", server_timestamp=datetime(2026, 5, 22, 13, 1, tzinfo=UTC))]
        ),
        state_cache=cache,
    )
    with pytest.raises(Exception):
        asyncio.run(oom_use_case.start(_one_connection_request()))

    oom_snapshot = cache.read_snapshot()[0]
    assert oom_snapshot.availability_status == "VALID"
    assert oom_snapshot.last_alive_at == initial_alive_at
    assert oom_snapshot.last_value_updated_at == initial_value_updated_at

    client.pipeline_error = RuntimeError("READONLY You can't write against a read only replica.")
    readonly_use_case = _build_use_case(
        acquisition_port=FakeSequenceAcquisitionPort(
            [_batch("12.0", server_timestamp=datetime(2026, 5, 22, 13, 2, tzinfo=UTC))]
        ),
        state_cache=cache,
    )
    with pytest.raises(Exception):
        asyncio.run(readonly_use_case.start(_one_connection_request()))

    readonly_snapshot = cache.read_snapshot()[0]
    assert readonly_snapshot.last_alive_at == initial_alive_at
    assert readonly_snapshot.last_value_updated_at == initial_value_updated_at
