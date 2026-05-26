"""Integration test for source server -> Redis latest-state cache."""

from __future__ import annotations

import asyncio
import socket
from contextlib import closing
from typing import Any, Protocol

import pytest

from tests.support.source_lab_runtime import import_source_lab_module
from whale.ingest.adapters.source.opcua_source_acquisition_adapter import (
    OpcUaSourceAcquisitionAdapter,
)
from whale.ingest.adapters.state.redis_source_state_cache import (
    RedisSourceStateCache,
    RedisSourceStateCacheSettings,
)
from whale.ingest.usecases import SourceAcquisitionUseCase
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


def _build_source(port: int) -> Any:
    return SimulatedSource(
        connection=SourceConnection(
            name="ingest_e2e_source",
            ied_name="IED001",
            ld_name="LD0",
            host="127.0.0.1",
            port=port,
            transport="tcp",
            protocol="opcua",
            namespace_uri="urn:whale:ingest:e2e",
        ),
        points=(
            SimulatedPoint(
                ln_name="WPPD1",
                do_name="TotW",
                unit="kW",
                data_type="FLOAT64",
                initial_value=12.5,
            ),
            SimulatedPoint(
                ln_name="WROT1",
                do_name="Spd",
                unit="rpm",
                data_type="FLOAT64",
                initial_value=6.75,
            ),
        ),
    )


def _build_request(source: _SimulatedSourceLike) -> SourceAcquisitionRequest:
    connection = source.connection
    return SourceAcquisitionRequest(
        request_id="ingest-e2e-redis",
        task_id=1,
        execution=AcquisitionExecutionOptions(
            protocol="opcua",
            transport="tcp",
            acquisition_mode="READ_ONCE",
            interval_ms=100,
            max_iteration=1,
            request_timeout_ms=3_000,
            freshness_timeout_ms=30_000,
            alive_timeout_ms=60_000,
        ),
        connections=[
            SourceConnectionData(
                host=connection.host,
                port=connection.port,
                ied_name=connection.ied_name,
                ld_name=connection.ld_name,
                namespace_uri=connection.namespace_uri or "",
            )
        ],
        items=[
            AcquisitionItemData(
                key=point.key,
                profile_item_id=index + 1,
                relative_path=logical_path(connection, point),
            )
            for index, point in enumerate(source.points)
        ],
    )


@pytest.mark.integration
def test_source_acquisition_read_once_updates_redis_cache_with_real_values(
    monkeypatch: pytest.MonkeyPatch,
    real_redis_client: Any,
    real_redis_hash_key: str,
    real_redis_url: str,
) -> None:
    """Verify the real source simulator -> open62541 backend -> Redis chain."""

    _require_runner()
    monkeypatch.setenv("SOURCE_SIM_POLL_SOURCE_UPDATE_ENABLED", "false")
    assert "fakeredis" not in type(real_redis_client).__module__.lower()

    port = _choose_available_port()
    source = _build_source(port)
    request = _build_request(source)
    state_cache = RedisSourceStateCache(
        settings=RedisSourceStateCacheSettings(
            host="127.0.0.1",
            port=16379,
            db=15,
            username=None,
            password=None,
            hash_key=real_redis_hash_key,
            station_id="station-integration-e2e",
        ),
        client=real_redis_client,
    )
    assert "redis://" in real_redis_url
    adapter = OpcUaSourceAcquisitionAdapter()
    use_case = SourceAcquisitionUseCase(
        polling_role=PollingAcquisitionRole(
            acquisition_port=adapter,
            state_cache_port=state_cache,
        ),
        subscription_role=SubscriptionAcquisitionRole(
            acquisition_port=adapter,
            state_cache_port=state_cache,
        ),
    )

    try:
        with Open62541SourceSimulator(source):
            asyncio.run(use_case.start(request))

        snapshot = state_cache.read_snapshot()

        assert len(snapshot) == 1
        assert snapshot[0].ld_name == source.connection.ld_name
        assert snapshot[0].availability_status == "VALID"
        assert snapshot[0].unavailable_reason is None
        assert len(snapshot[0].values) == len(request.items)
        assert [value.node_key for value in snapshot[0].values] == sorted(
            item.key for item in request.items
        )
        values_by_key = {value.node_key: value for value in snapshot[0].values}
        assert values_by_key["WPPD1.TotW"].value == "12.5"
        assert values_by_key["WPPD1.TotW"].value != "True"
        assert values_by_key["WROT1.Spd"].value == "6.75"
        assert values_by_key["WPPD1.TotW"].quality is not None
        assert (
            values_by_key["WPPD1.TotW"].server_timestamp is not None
            or values_by_key["WPPD1.TotW"].source_timestamp is not None
        )
        assert snapshot[0].last_alive_at is not None
        assert snapshot[0].last_value_updated_at is not None
    finally:
        real_redis_client.delete(real_redis_hash_key)
