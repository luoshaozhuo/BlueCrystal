"""Kafka fault injection and recovery tests for prodlike ingest runtime."""

from __future__ import annotations

import json
import time
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest

from tests.support.ingest_prodlike_runtime import ensure_prodlike_stack, start_service, stop_prodlike_stack, stop_service
from whale.ingest.adapters.message.kafka_message_publisher import KafkaMessagePublisher
from whale.ingest.adapters.observability.file_sinks import JsonlIngestMetricsSink
from whale.ingest.adapters.state.redis_source_state_cache import (
    RedisSourceStateCache,
    RedisSourceStateCacheSettings,
)
from whale.ingest.ports.message.message_publisher_port import StateSnapshotItem, StateSnapshotMessage
from whale.ingest.runtime.message_pipeline_settings import KafkaMessageSettings
from whale.ingest.usecases.dtos.acquired_node_state import AcquiredNodeStateBatch, AcquiredNodeValue
from whale.ingest.usecases.dtos.state_publish_request import StateSnapshotPublishRequest
from whale.ingest.usecases.state_snapshot_publish_use_case import StateSnapshotPublishUseCase


def _publisher() -> KafkaMessagePublisher:
    return KafkaMessagePublisher(
        settings=KafkaMessageSettings(
            bootstrap_servers=("127.0.0.1:9092",),
            topic="whale.ingest.kafka.fault",
            ack_timeout_seconds=2.0,
            acks="all",
            retries=1,
            request_timeout_ms=1500,
            key_strategy="source_id",
        )
    )


def _message() -> StateSnapshotMessage:
    now = datetime.now(tz=UTC)
    return StateSnapshotMessage(
        message_id=str(uuid4()),
        schema_version="1.0",
        message_type="state_snapshot",
        source_module="ingest.test",
        snapshot_id="kafka-fault",
        snapshot_at=now,
        trace_id="trace-kafka-fault",
        item_count=1,
        items=[
            StateSnapshotItem(
                station_id="whale-prod",
                device_id="source-1",
                device_code="source-1",
                model_id="model-1",
                variable_key="TotW",
                value="42",
                value_type="float",
                quality_code="GOOD",
                source_observed_at=now,
                received_at=now,
                updated_at=now,
            )
        ],
    )


def _cache() -> RedisSourceStateCache:
    return RedisSourceStateCache(
        settings=RedisSourceStateCacheSettings(
            redis_url="redis://127.0.0.1:16379/3",
            host="127.0.0.1",
            port=16379,
            db=3,
            username=None,
            password=None,
            hash_key="whale:ingest:kafka:fault",
            station_id="whale-prod",
            socket_connect_timeout_seconds=0.5,
        )
    )


def _batch() -> AcquiredNodeStateBatch:
    now = datetime.now(tz=UTC)
    return AcquiredNodeStateBatch(
        source_id="source-1",
        batch_observed_at=now,
        client_received_at=now,
        client_processed_at=now,
        values=[
            AcquiredNodeValue(
                node_key="TotW",
                value="42",
                quality="GOOD",
                source_timestamp=now,
                server_timestamp=now,
            )
        ],
    )


@pytest.fixture(scope="module", autouse=True)
def prodlike_kafka_stack():
    ensure_prodlike_stack()
    yield
    stop_prodlike_stack()


@pytest.mark.integration
def test_kafka_publish_failure_classified_without_blocking_cache() -> None:
    cache = _cache()
    cache.update(ld_name="LD0", batch=_batch())

    stop_service("kafka")
    try:
        result = _publisher().publish_snapshot(_message())
    finally:
        start_service("kafka")

    assert result.success is False
    assert result.error_message is not None
    assert result.error_message.startswith("kafka_")
    assert cache.read_snapshot()


@pytest.mark.integration
def test_kafka_publish_recovers_after_broker_restart() -> None:
    stop_service("kafka")
    start_service("kafka")
    time.sleep(5)

    result = _publisher().publish_snapshot(_message())
    assert result.success is True


@pytest.mark.integration
def test_kafka_publish_retry_metrics_emitted(tmp_path: Path) -> None:
    cache = _cache()
    cache.update(ld_name="LD0", batch=_batch())
    metrics_path = tmp_path / "kafka-failure-metrics.jsonl"
    use_case = StateSnapshotPublishUseCase(
        reader=cache,
        publisher=_publisher(),
        station_id="whale-prod",
        metrics_port=JsonlIngestMetricsSink(metrics_path),
    )

    stop_service("kafka")
    try:
        use_case.execute(StateSnapshotPublishRequest(trace_id="trace-kafka-metrics"))
    finally:
        start_service("kafka")

    lines = metrics_path.read_text(encoding="utf-8").splitlines()
    assert lines
    payload = json.loads(lines[-1])
    assert payload["operation"] == "snapshot_publish"
    assert payload["status"] in {"FAILED", "PARTIAL"}


@pytest.mark.integration
def test_kafka_backpressure_does_not_unbounded_queue() -> None:
    stop_service("kafka")
    try:
        publisher = _publisher()
        started = time.monotonic()
        for _ in range(20):
            result = publisher.publish_snapshot(_message())
            assert result.success is False
        elapsed = time.monotonic() - started
    finally:
        start_service("kafka")

    assert elapsed < 20, f"publish loop too slow under Kafka outage: {elapsed}s"
