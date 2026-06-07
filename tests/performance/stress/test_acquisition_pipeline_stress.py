"""Current-architecture stress smoke for ingest acquisition -> Redis latest-state cache."""

from __future__ import annotations

import asyncio
import socket
from contextlib import closing

import pytest

# import_source_lab_module 已移除，source_lab 目录已物理删除
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

pytestmark = pytest.mark.skip(reason="source_lab 已删除，需迁移到 Starfish facade 或 standalone simulator")


def _choose_available_port() -> int:
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _build_source(port: int) -> SimulatedSource:
    return SimulatedSource(
        connection=SourceConnection(
            name="stress-smoke-source",
            ied_name="IED_STRESS",
            ld_name="LD_STRESS",
            host="127.0.0.1",
            port=port,
            transport="tcp",
            protocol="opcua",
            namespace_uri="urn:whale:stress",
        ),
        points=(
            SimulatedPoint(
                ln_name="WPPD1",
                do_name="TotW",
                unit="kW",
                data_type="FLOAT64",
                initial_value=15.25,
            ),
        ),
    )


def _build_request(source: SimulatedSource) -> SourceAcquisitionRequest:
    connection = source.connection
    point = source.points[0]
    return SourceAcquisitionRequest(
        request_id="stress-smoke-request",
        task_id=401,
        execution=AcquisitionExecutionOptions(
            protocol="opcua",
            transport="tcp",
            acquisition_mode="READ_ONCE",
            interval_ms=100,
            max_iteration=1,
            request_timeout_ms=2_000,
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
                profile_item_id=1,
                relative_path=logical_path(connection, point),
            )
        ],
    )


@pytest.mark.stress
def test_acquisition_pipeline_stress_smoke_uses_current_open62541_and_redis_chain(
    monkeypatch: pytest.MonkeyPatch,
    real_redis_client,
    real_redis_hash_key: str,
) -> None:
    """Exercise the current READ_ONCE -> Redis production chain repeatedly."""

    if not resolve_runner_path().exists():
        pytest.skip("open62541 runner executable does not exist")

    monkeypatch.setenv("SOURCE_SIM_POLL_SOURCE_UPDATE_ENABLED", "false")
    source = _build_source(_choose_available_port())
    request = _build_request(source)
    state_cache = RedisSourceStateCache(
        settings=RedisSourceStateCacheSettings(
            host="127.0.0.1",
            port=16379,
            db=15,
            username=None,
            password=None,
            hash_key=real_redis_hash_key,
            station_id="station-stress-smoke",
        ),
        client=real_redis_client,
    )
    use_case = SourceAcquisitionUseCase(
        polling_role=PollingAcquisitionRole(
            acquisition_port=OpcUaSourceAcquisitionAdapter(),
            state_cache_port=state_cache,
        ),
        subscription_role=SubscriptionAcquisitionRole(
            acquisition_port=OpcUaSourceAcquisitionAdapter(),
            state_cache_port=state_cache,
        ),
    )

    try:
        with Open62541SourceSimulator(source) as simulator:
            for next_value in ("15.25", "16.50", "18.75"):
                simulator.writes({source.points[0].key: float(next_value)})
                asyncio.run(use_case.start(request))

        snapshot = state_cache.read_snapshot()

        assert len(snapshot) == 1
        assert snapshot[0].availability_status == "VALID"
        assert snapshot[0].unavailable_reason is None
        assert snapshot[0].values[0].node_key == "WPPD1.TotW"
        assert snapshot[0].values[0].value == "18.75"
        assert snapshot[0].last_alive_at is not None
        assert snapshot[0].last_value_updated_at is not None
    finally:
        real_redis_client.delete(real_redis_hash_key)
