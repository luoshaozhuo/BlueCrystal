"""Kafka container E2E for source -> cache -> message.

If Docker/testcontainers is unavailable, this test is skipped with CI guidance.
"""

from __future__ import annotations

import asyncio
import json
import socket
from contextlib import closing
from datetime import UTC, datetime
from typing import Any

import pytest

from tests.support.source_lab_runtime import import_source_lab_module
from whale.ingest.adapters.message.kafka_message_publisher import KafkaMessagePublisher
from whale.ingest.adapters.source.opcua_source_acquisition_adapter import (
    OpcUaSourceAcquisitionAdapter,
)
from whale.ingest.adapters.state.redis_source_state_cache import (
    RedisSourceStateCache,
    RedisSourceStateCacheSettings,
)
from whale.ingest.runtime.message_pipeline_settings import KafkaMessageSettings
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
from whale.ingest.usecases.roles.subscription_acquisition_role import SubscriptionAcquisitionRole
from whale.ingest.usecases.state_snapshot_publish_use_case import StateSnapshotPublishUseCase

_MODEL_MODULE = import_source_lab_module("tools.source_lab.model")
_ADDRESS_SPACE_MODULE = import_source_lab_module("tools.source_lab.protocols.opcua.address_space")
_SIMULATOR_MODULE = import_source_lab_module("tools.source_lab.protocols.opcua.open62541_source_simulator")

SimulatedPoint = _MODEL_MODULE.SimulatedPoint
SimulatedSource = _MODEL_MODULE.SimulatedSource
SourceConnection = _MODEL_MODULE.SourceConnection
logical_path = _ADDRESS_SPACE_MODULE.logical_path
Open62541SourceSimulator = _SIMULATOR_MODULE.Open62541SourceSimulator
resolve_runner_path = _SIMULATOR_MODULE.resolve_runner_path


def _choose_available_port() -> int:
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _require_testcontainers() -> tuple[Any, Any]:
    try:
        from kafka import KafkaConsumer
        from testcontainers.kafka import KafkaContainer
    except Exception:
        pytest.skip(
            "testcontainers/kafka-python unavailable; CI command: "
            "pytest tests/integration/test_ingest_source_cache_message_kafka_e2e.py -q"
        )
    return KafkaContainer, KafkaConsumer


@pytest.mark.integration
def test_source_cache_message_kafka_e2e(
    monkeypatch: pytest.MonkeyPatch,
    real_redis_client: Any,
    real_redis_hash_key: str,
) -> None:
    if not resolve_runner_path().exists():
        pytest.skip("open62541 runner executable does not exist")
    KafkaContainer, KafkaConsumer = _require_testcontainers()

    monkeypatch.setenv("SOURCE_SIM_POLL_SOURCE_UPDATE_ENABLED", "false")
    port = _choose_available_port()
    source = SimulatedSource(
        connection=SourceConnection(
            name="ingest_kafka_e2e",
            ied_name="IED001",
            ld_name="LD0",
            host="127.0.0.1",
            port=port,
            transport="tcp",
            protocol="opcua",
            namespace_uri="urn:whale:ingest:kafka:e2e",
        ),
        points=(SimulatedPoint(ln_name="WPPD1", do_name="TotW", unit="kW", data_type="FLOAT64", initial_value=12.5),),
    )
    request = SourceAcquisitionRequest(
        request_id="ingest-kafka-e2e",
        task_id=1,
        execution=AcquisitionExecutionOptions(
            protocol="opcua",
            transport="tcp",
            acquisition_mode="READ_ONCE",
            interval_ms=100,
            max_iteration=1,
            request_timeout_ms=3000,
            freshness_timeout_ms=30_000,
            alive_timeout_ms=60_000,
        ),
        connections=[
            SourceConnectionData(
                host=source.connection.host,
                port=source.connection.port,
                ied_name=source.connection.ied_name,
                ld_name=source.connection.ld_name,
                namespace_uri=source.connection.namespace_uri or "",
            )
        ],
        items=[
            AcquisitionItemData(
                key=source.points[0].key,
                profile_item_id=1,
                relative_path=logical_path(source.connection, source.points[0]),
            )
        ],
    )

    state_cache = RedisSourceStateCache(
        settings=RedisSourceStateCacheSettings(
            host="127.0.0.1",
            port=16379,
            db=15,
            username=None,
            password=None,
            hash_key=real_redis_hash_key,
            station_id="station-kafka-e2e",
        ),
        client=real_redis_client,
    )
    adapter = OpcUaSourceAcquisitionAdapter()
    acq = SourceAcquisitionUseCase(
        polling_role=PollingAcquisitionRole(acquisition_port=adapter, state_cache_port=state_cache),
        subscription_role=SubscriptionAcquisitionRole(acquisition_port=adapter, state_cache_port=state_cache),
    )

    topic = "whale.ingest.snapshot.e2e"
    with KafkaContainer() as kafka:
        publisher = KafkaMessagePublisher(
            settings=KafkaMessageSettings(
                bootstrap_servers=(kafka.get_bootstrap_server(),),
                topic=topic,
                ack_timeout_seconds=5.0,
            )
        )
        publish = StateSnapshotPublishUseCase(reader=state_cache, publisher=publisher, station_id="station-kafka-e2e")

        try:
            with Open62541SourceSimulator(source):
                asyncio.run(acq.start(request))
            result = publish.execute(StateSnapshotPublishRequest(trace_id="trace-kafka-e2e"))
            assert result.status in {PublishStatus.SUCCESS, PublishStatus.PARTIAL}
            consumer = KafkaConsumer(
                topic,
                bootstrap_servers=[kafka.get_bootstrap_server()],
                auto_offset_reset="earliest",
                enable_auto_commit=False,
                consumer_timeout_ms=8000,
            )
            records = list(consumer)
            assert records, "No Kafka records consumed"
            payload = json.loads(records[0].value.decode("utf-8"))
            assert payload["schema_version"] == "1.0"
            assert payload["trace_id"] == "trace-kafka-e2e"
            assert payload["message_id"]
            assert payload["item_count"] >= 1
            item = payload["items"][0]
            assert item["device_code"]
            assert item["variable_key"] == "WPPD1.TotW"
            assert item["value"] == "12.5"
            assert item["quality_code"] is not None
            assert item["source_observed_at"] is not None
            assert datetime.fromisoformat(item["source_observed_at"]).tzinfo is not None
        finally:
            real_redis_client.delete(real_redis_hash_key)
