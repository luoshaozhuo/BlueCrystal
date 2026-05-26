"""Integration test for source -> cache -> message chain."""

from __future__ import annotations

import asyncio
import json
import socket
from contextlib import closing
from dataclasses import dataclass, field
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
from whale.ingest.ports.message.message_publisher_port import (
    MessagePublishResult,
    MessagePublisherPort,
    StateSnapshotMessage,
)
from whale.ingest.usecases import SourceAcquisitionUseCase
from whale.ingest.usecases.dtos.source_acquisition_request import (
    AcquisitionExecutionOptions,
    AcquisitionItemData,
    SourceAcquisitionRequest,
)
from whale.ingest.usecases.dtos.source_connection_data import SourceConnectionData
from whale.ingest.usecases.dtos.state_publish_request import StateSnapshotPublishRequest
from whale.ingest.usecases.dtos.state_publish_result import PublishStatus
from whale.ingest.usecases.roles.polling_acquisition_role import PollingAcquisitionRole
from whale.ingest.usecases.roles.subscription_acquisition_role import (
    SubscriptionAcquisitionRole,
)
from whale.ingest.usecases.state_snapshot_publish_use_case import (
    StateSnapshotPublishUseCase,
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


@dataclass
class _VerifiablePublisher(MessagePublisherPort):
    messages: list[StateSnapshotMessage] = field(default_factory=list)
    fail: bool = False

    def publish_snapshot(self, message: StateSnapshotMessage) -> MessagePublishResult:
        self.messages.append(message)
        if self.fail:
            raise RuntimeError("kafka_unavailable")
        from datetime import UTC, datetime

        return MessagePublishResult(
            pipeline_name="verifiable",
            success=True,
            message_id=message.message_id,
            message_count=1,
            published_at=datetime.now(tz=UTC),
        )


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
            name="ingest_source_cache_msg",
            ied_name="IED001",
            ld_name="LD0",
            host="127.0.0.1",
            port=port,
            transport="tcp",
            protocol="opcua",
            namespace_uri="urn:whale:ingest:source-cache-message",
        ),
        points=(
            SimulatedPoint(
                ln_name="WPPD1",
                do_name="TotW",
                unit="kW",
                data_type="FLOAT64",
                initial_value=12.5,
            ),
        ),
    )


def _build_request(source: _SimulatedSourceLike) -> SourceAcquisitionRequest:
    connection = source.connection
    return SourceAcquisitionRequest(
        request_id="ingest-source-cache-message",
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
def test_source_cache_message_chain_e2e(
    monkeypatch: pytest.MonkeyPatch,
    real_redis_client: Any,
    real_redis_hash_key: str,
) -> None:
    _require_runner()
    monkeypatch.setenv("SOURCE_SIM_POLL_SOURCE_UPDATE_ENABLED", "false")
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
    adapter = OpcUaSourceAcquisitionAdapter()
    acq = SourceAcquisitionUseCase(
        polling_role=PollingAcquisitionRole(acquisition_port=adapter, state_cache_port=state_cache),
        subscription_role=SubscriptionAcquisitionRole(
            acquisition_port=adapter, state_cache_port=state_cache
        ),
    )
    publisher = _VerifiablePublisher()
    publish = StateSnapshotPublishUseCase(
        reader=state_cache, publisher=publisher, station_id="station-integration-e2e"
    )
    try:
        with Open62541SourceSimulator(source):
            asyncio.run(acq.start(request))
        result = publish.execute(StateSnapshotPublishRequest(trace_id="trace-e2e-001"))
        assert result.status == PublishStatus.SUCCESS
        assert result.published_count > 0
        assert len(publisher.messages) == 1
        payload = json.loads(publisher.messages[0].to_json())
        assert payload["schema_version"] == "1.0"
        assert payload["trace_id"] == "trace-e2e-001"
        assert payload["message_id"]
        assert payload["item_count"] == 1
        item = payload["items"][0]
        assert item["device_code"]
        assert item["variable_key"] == "WPPD1.TotW"
        assert item["value"] == "12.5"
        assert item["quality_code"] is not None
        assert item["source_observed_at"] is not None
    finally:
        real_redis_client.delete(real_redis_hash_key)


@pytest.mark.integration
def test_publish_failure_does_not_corrupt_cached_state(
    monkeypatch: pytest.MonkeyPatch,
    real_redis_client: Any,
    real_redis_hash_key: str,
) -> None:
    _require_runner()
    monkeypatch.setenv("SOURCE_SIM_POLL_SOURCE_UPDATE_ENABLED", "false")
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
    adapter = OpcUaSourceAcquisitionAdapter()
    acq = SourceAcquisitionUseCase(
        polling_role=PollingAcquisitionRole(acquisition_port=adapter, state_cache_port=state_cache),
        subscription_role=SubscriptionAcquisitionRole(
            acquisition_port=adapter, state_cache_port=state_cache
        ),
    )
    publish = StateSnapshotPublishUseCase(
        reader=state_cache, publisher=_VerifiablePublisher(fail=True), station_id="station"
    )
    try:
        with Open62541SourceSimulator(source):
            asyncio.run(acq.start(request))
        before = state_cache.read_snapshot()
        result = publish.execute(StateSnapshotPublishRequest(trace_id="trace-pub-fail"))
        after = state_cache.read_snapshot()
        assert result.status == PublishStatus.FAILED
        assert "Publish failed" in (result.error or "")
        assert len(before) == 1
        assert len(after) == 1
        assert after[0].values[0].node_key == before[0].values[0].node_key
        assert after[0].values[0].value == before[0].values[0].value
    finally:
        real_redis_client.delete(real_redis_hash_key)
