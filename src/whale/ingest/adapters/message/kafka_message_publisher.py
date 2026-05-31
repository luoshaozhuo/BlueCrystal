# mypy: disable-error-code=import-untyped
"""消息发布适配器。

实现 MessagePublisherPort，将状态快照发布到消息中间件。
外部依赖：Kafka / Redis。
失败处理：失败不传播到调用方，记录 error 后继续。
"""

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
    """Kafka 发布器使用的最小发送 Future 契约。"""

    def get(self, timeout: float | None = None) -> object:
        """等待已发布消息的结果。"""


class KafkaProducerClient(Protocol):
    """发布器使用的最小 Kafka 生产者契约。"""

    def send(
        self,
        topic: str,
        key: bytes,
        value: bytes,
    ) -> KafkaSendFuture:
        """向 Kafka 发送一条消息。"""

    def flush(self) -> None:
        """Flush 生产者缓冲区，确保所有未发送消息被提交到 Kafka broker。"""


class KafkaMessagePublisher(MessagePublisherPort):
    """将状态快照消息发布到一个 Kafka topic。"""

    def __init__(
        self,
        settings: KafkaMessageSettings,
        producer: KafkaProducerClient | None = None,
    ) -> None:
        """Flush 生产者缓冲区，确保所有未发送消息被提交到 Kafka broker。"""
        self._settings = settings
        self._initialization_error: Exception | None = None
        self._producer: KafkaProducerClient | None
        if producer is not None:
            self._producer = producer
        else:
            try:
                self._producer = self._build_producer(settings)
            except Exception as exc:
                self._producer = None
                self._initialization_error = exc

    def publish_snapshot(self, message: StateSnapshotMessage) -> MessagePublishResult:
        """将单个快照消息发布到 Kafka。"""
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
        """根据配置策略构造 Kafka 分区键。"""

        if self._settings.key_strategy == "source_id" and message.items:
            source_id = message.items[0].device_id or message.items[0].device_code
            return str(source_id).encode("utf-8")
        return message.snapshot_id.encode("utf-8")

    @staticmethod
    def _build_producer(settings: KafkaMessageSettings) -> KafkaProducerClient:
        """延迟构造真实的 Kafka 生产者实例。"""
        try:
            from kafka import KafkaProducer  # type: ignore[import-untyped]  # kafka-python 无类型 stub，运行时可用
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
    """将 Kafka 失败映射为稳定的发布错误类别。"""

    lowered = str(error).lower()
    if "timeout" in lowered:
        return "kafka_timeout"
    if "no brokers" in lowered or "bootstrap" in lowered or "connection" in lowered:
        return "kafka_unavailable"
    return f"kafka_publish_failed:{type(error).__name__}"
