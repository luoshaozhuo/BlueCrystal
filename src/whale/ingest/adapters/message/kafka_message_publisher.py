# mypy: disable-error-code=import-untyped
"""Kafka publisher for ingest state snapshot messages."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Protocol, cast

from whale.ingest.ports.message import MessagePublisherPort
from whale.ingest.ports.message.message_publisher_port import (
    MessagePublishResult,
    StateSnapshotMessage,
)
from whale.ingest.runtime.message_pipeline_settings import KafkaMessageSettings


class KafkaSendFuture(Protocol):
    """Minimal send future contract used by the Kafka publisher."""

    def get(self, timeout: float | None = None) -> object:
        """Wait for the published message result."""


class KafkaProducerClient(Protocol):
    """Minimal Kafka producer contract used by the publisher."""

    def send(
        self,
        topic: str,
        key: bytes,
        value: bytes,
    ) -> KafkaSendFuture:
        """Send one message to Kafka."""

    def flush(self) -> None:
        """Flush producer buffers."""


class KafkaMessagePublisher(MessagePublisherPort):
    """Publish snapshot messages into one Kafka topic."""

    def __init__(
        self,
        settings: KafkaMessageSettings,
        producer: KafkaProducerClient | None = None,
    ) -> None:
        """Store Kafka settings and an optional injected producer."""
        self._settings = settings
        self._initialization_error: Exception | None = None
        if producer is not None:
            self._producer = producer
        else:
            try:
                self._producer = self._build_producer(settings)
            except Exception as exc:
                self._producer = None
                self._initialization_error = exc

    def publish_snapshot(self, message: StateSnapshotMessage) -> MessagePublishResult:
        """Publish one snapshot message into Kafka."""
        payload = message.to_json().encode("utf-8")
        if self._initialization_error is not None or self._producer is None:
            return MessagePublishResult(
                pipeline_name="kafka",
                success=False,
                message_id=message.message_id,
                message_count=0,
                published_at=datetime.now(tz=UTC),
                error_message=_classify_kafka_error(
                    self._initialization_error or RuntimeError("producer_not_initialized")
                ),
            )
        try:
            future = self._producer.send(
                self._settings.topic,
                key=self._build_key(message),
                value=payload,
            )
            future.get(timeout=self._settings.ack_timeout_seconds)
            self._producer.flush()
            return MessagePublishResult(
                pipeline_name="kafka",
                success=True,
                message_id=message.message_id,
                message_count=1,
                published_at=datetime.now(tz=UTC),
            )
        except Exception as exc:
            return MessagePublishResult(
                pipeline_name="kafka",
                success=False,
                message_id=message.message_id,
                message_count=0,
                published_at=datetime.now(tz=UTC),
                error_message=_classify_kafka_error(exc),
            )

    def _build_key(self, message: StateSnapshotMessage) -> bytes:
        """Build one Kafka partition key from the configured strategy."""

        if self._settings.key_strategy == "source_id" and message.items:
            source_id = message.items[0].device_id or message.items[0].device_code
            return str(source_id).encode("utf-8")
        return message.snapshot_id.encode("utf-8")

    @staticmethod
    def _build_producer(settings: KafkaMessageSettings) -> KafkaProducerClient:
        """Build one real Kafka producer lazily."""
        try:
            from kafka import KafkaProducer  # type: ignore[import-untyped]
        except ImportError as exc:
            raise RuntimeError(
                "Kafka publishing requires the `kafka-python` package to be installed."
            ) from exc

        return cast(
            KafkaProducerClient,
            KafkaProducer(
                bootstrap_servers=list(settings.bootstrap_servers),
                acks=settings.acks,
                retries=settings.retries,
                request_timeout_ms=settings.request_timeout_ms,
            ),
        )


def _classify_kafka_error(error: Exception) -> str:
    """Map Kafka failures into stable publish error categories."""

    lowered = str(error).lower()
    if "timeout" in lowered:
        return "kafka_timeout"
    if "no brokers" in lowered or "bootstrap" in lowered or "connection" in lowered:
        return "kafka_unavailable"
    return f"kafka_publish_failed:{type(error).__name__}"
