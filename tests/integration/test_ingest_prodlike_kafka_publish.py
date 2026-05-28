"""Production-like Kafka publish integration tests.

Requires real Kafka reachable via WHALE_INGEST_KAFKA_BOOTSTRAP_SERVERS.
"""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from uuid import uuid4

import pytest

from whale.ingest.adapters.message.kafka_message_publisher import KafkaMessagePublisher
from whale.ingest.ports.message.message_publisher_port import (
    StateSnapshotItem,
    StateSnapshotMessage,
)
from whale.ingest.runtime.message_pipeline_settings import KafkaMessageSettings

KAFKA_BOOTSTRAP = os.environ.get("WHALE_INGEST_KAFKA_BOOTSTRAP_SERVERS", "127.0.0.1:9092")
KAFKA_TOPIC = os.environ.get("WHALE_INGEST_KAFKA_TOPIC", "whale.ingest.test")


@pytest.fixture
def kafka_settings():
    return KafkaMessageSettings(
        bootstrap_servers=tuple(s.strip() for s in KAFKA_BOOTSTRAP.split(",") if s.strip()),
        topic=KAFKA_TOPIC,
        ack_timeout_seconds=5.0,
        acks="all",
        retries=3,
        request_timeout_ms=5000,
        key_strategy="snapshot_id",
    )


def _skip_no_kafka(kafka_settings):
    try:
        from kafka import KafkaProducer

        producer = KafkaProducer(bootstrap_servers=list(kafka_settings.bootstrap_servers))
        future = producer.send(kafka_settings.topic, b"test-ping", key=b"ping")
        future.get(timeout=3)
        producer.flush()
        producer.close()
    except Exception:
        pytest.skip(f"Kafka not reachable at {kafka_settings.bootstrap_servers}")


# ── Publish state snapshot envelope ────────────────────────────────────


def test_kafka_publish_state_snapshot_envelope(kafka_settings):
    """Verify publishing a state snapshot message to Kafka."""
    _skip_no_kafka(kafka_settings)

    publisher = KafkaMessagePublisher(settings=kafka_settings)
    now = datetime.now(tz=UTC)
    msg = StateSnapshotMessage(
        message_id=str(uuid4()),
        schema_version="1.0",
        message_type="snapshot",
        source_module="ingest.test",
        snapshot_id="snap-1",
        snapshot_at=now,
        item_count=1,
        items=[
            StateSnapshotItem(
                station_id="test-station",
                device_id="src-1",
                device_code="dev-1",
                model_id="model-1",
                variable_key="point1",
                value="42",
                value_type="float",
                quality_code="GOOD",
                source_observed_at=now,
                received_at=now,
                updated_at=now,
            ),
        ],
    )
    result = publisher.publish_snapshot(msg)
    assert result.success is True
    assert result.message_id == msg.message_id
    assert result.pipeline_name == "kafka"

    # Verify by consuming back (match by message_id to avoid stale records)
    from kafka import KafkaConsumer

    consumer = KafkaConsumer(
        kafka_settings.topic,
        bootstrap_servers=list(kafka_settings.bootstrap_servers),
        auto_offset_reset="earliest",
        consumer_timeout_ms=10000,
    )
    found = None
    for record in consumer:
        try:
            payload = json.loads(record.value.decode("utf-8"))
            if payload.get("message_id") == msg.message_id:
                found = payload
                break
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
    consumer.close()

    assert found is not None, f"Message {msg.message_id} not consumed from Kafka"
    assert found["snapshot_id"] == "snap-1"


# ── Key strategy ───────────────────────────────────────────────────────


def test_kafka_publish_key_strategy_source_id(kafka_settings):
    """Verify Kafka message key can be driven by source_id strategy."""
    _skip_no_kafka(kafka_settings)

    publisher = KafkaMessagePublisher(
        settings=KafkaMessageSettings(
            bootstrap_servers=kafka_settings.bootstrap_servers,
            topic=kafka_settings.topic,
            ack_timeout_seconds=kafka_settings.ack_timeout_seconds,
            acks="all",
            retries=3,
            request_timeout_ms=5000,
            key_strategy="source_id",
        )
    )
    now = datetime.now(tz=UTC)
    msg = StateSnapshotMessage(
        message_id=str(uuid4()),
        schema_version="1.0",
        message_type="snapshot",
        source_module="ingest.test",
        snapshot_id="snap-key-test",
        snapshot_at=now,
        item_count=1,
        items=[
            StateSnapshotItem(
                station_id="test",
                device_id="src-key-test",
                device_code="dev-1",
                model_id="model-1",
                variable_key="p1",
                value="1",
                value_type="float",
                quality_code="GOOD",
                source_observed_at=now,
                received_at=now,
                updated_at=now,
            ),
        ],
    )
    result = publisher.publish_snapshot(msg)
    assert result.success is True

    from kafka import KafkaConsumer

    consumer = KafkaConsumer(
        kafka_settings.topic,
        bootstrap_servers=list(kafka_settings.bootstrap_servers),
        auto_offset_reset="earliest",
        consumer_timeout_ms=5000,
    )
    record = None
    for r in consumer:
        if b"snap-key-test" in r.value:
            record = r
            break
    consumer.close()
    assert record is not None
    assert record.key == b"src-key-test"


# ── Error classification ───────────────────────────────────────────────


def test_kafka_publish_error_is_classified(kafka_settings):
    """Verify publish to non-existent broker returns classified error."""
    bad_settings = KafkaMessageSettings(
        bootstrap_servers=("127.0.0.1:1",),
        topic="noop",
        ack_timeout_seconds=1.0,
        acks="all",
        retries=1,
        request_timeout_ms=1000,
        key_strategy="snapshot_id",
    )
    publisher = KafkaMessagePublisher(settings=bad_settings)
    now = datetime.now(tz=UTC)
    msg = StateSnapshotMessage(
        message_id=str(uuid4()),
        schema_version="1.0",
        message_type="snapshot",
        source_module="ingest.test",
        snapshot_id="snap-error",
        snapshot_at=now,
        item_count=0,
        items=[],
    )

    result = publisher.publish_snapshot(msg)
    assert result.success is False
    assert result.error_message is not None
    assert result.error_message.startswith("kafka_")
