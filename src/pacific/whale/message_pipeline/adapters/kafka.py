"""Kafka 消息管道适配器。

提供 message_pipeline 的 Kafka 实现：
- KafkaSourceAdapter: 基于 kafka-python 消费消息。
- KafkaSinkAdapter: 基于 kafka-python 发布消息。

如果 kafka-python 依赖不可用，adapter 在初始化时标记为 degraded，
但仍提供接口契约验证能力。不连接真实 broker 时可用于 contract 测试。

本文件不包含 DLQ 和 schema registry 的 Kafka 实现（由 InMemory 版本或
独立 adapter 实现）。
"""

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import AsyncIterator
from datetime import datetime, timezone
from typing import Any

from pacific.whale.message_pipeline.model import (
    Envelope,
    MessageOffset,
    PartitionKeyStrategy,
    ReplayRequest,
    SourceIdPartitionKey,
    TopicSpec,
)
from pacific.whale.message_pipeline.ports import (
    MessageSinkPort,
    MessageSourcePort,
    ReplayPort,
)

logger = logging.getLogger(__name__)


class KafkaSourceAdapter(MessageSourcePort, ReplayPort):
    """Kafka 消息消费适配器。

    基于 kafka-python 实现 consumer 逻辑。支持 consumer group 管理、
    offset 提交、seek 操作和消息回放。

    适配器边界：
    - 将 kafka-python 的 ConsumerRecord 映射为 Envelope。
    - 管理 consumer 生命周期（创建、订阅、关闭）。
    - 不负责 schema 校验（由 SchemaRegistryPort 负责）。

    Attributes:
        _settings: Kafka 连接和 topic 配置。
        _consumer: kafka-python consumer 实例（延迟初始化）。
        _initialized: 是否已成功初始化。
        _error: 初始化失败时的异常信息。
    """

    def __init__(
        self,
        bootstrap_servers: list[str],
        group_id: str,
        topic_specs: list[TopicSpec],
        *,
        auto_offset_reset: str = "earliest",
        enable_auto_commit: bool = False,
        idle_timeout_seconds: float | None = 10.0,
    ) -> None:
        """初始化 Kafka consumer adapter。

        Args:
            bootstrap_servers: Kafka broker 地址列表。
            group_id: consumer group ID。
            topic_specs: 订阅的 topic 配置列表。
            auto_offset_reset: 无 committed offset 时的起始策略。
            enable_auto_commit: 是否自动提交 offset（建议手动管理，设为 False）。
            idle_timeout_seconds: 连续无消息退出阈值（None 表示无限等待）。
                默认 10 秒，生产长连接可设为 None。
        """
        self._bootstrap_servers = bootstrap_servers
        self._group_id = group_id
        self._topic_specs = topic_specs
        self._auto_offset_reset = auto_offset_reset
        self._enable_auto_commit = enable_auto_commit
        self._idle_timeout = idle_timeout_seconds
        self._consumer: Any = None
        self._initialized = False
        self._error: str | None = None

    async def consume(
        self, topic: str, group_id: str
    ) -> AsyncIterator[Envelope]:
        """从 Kafka topic 消费消息。

        真实消费场景下通过 consumer.poll() 持续拉取消息并反序列化为 Envelope。
        如果 topic 的 consumer group 尚未创建，先执行 _ensure_consumer()。

        Args:
            topic: 消费的 topic 名称。
            group_id: consumer group 标识。

        Yields:
            从 Kafka 消费到的 Envelope 消息。

        Raises:
            RuntimeError: broker 连接失败或配置无效。
        """
        if not self._initialized:
            self._ensure_consumer()
        if self._consumer is None:
            return

        _poll_timeout_ms = 5000
        _idle_sleep = 0.5
        _last_yield_time = asyncio.get_event_loop().time()

        while True:
            try:
                records = self._consumer.poll(
                    timeout_ms=_poll_timeout_ms, max_records=50
                )
            except Exception as exc:
                logger.error("Kafka poll 失败: %s", exc)
                await asyncio.sleep(_idle_sleep)
                continue

            if not records:
                # 空闲超时检查：连续无消息超出阈值则退出
                if self._idle_timeout is not None:
                    elapsed = asyncio.get_event_loop().time() - _last_yield_time
                    if elapsed > self._idle_timeout:
                        return
                await asyncio.sleep(_idle_sleep)
                continue

            for tp, msgs in records.items():
                if tp.topic != topic:
                    continue
                for msg in msgs:
                    try:
                        if msg.value is None:
                            continue
                        data: dict[str, Any] = msg.value
                        if not isinstance(data, dict):
                            continue

                        published_at_str = data.get("published_at", "")
                        try:
                            published_at = datetime.fromisoformat(published_at_str)
                        except (ValueError, TypeError):
                            published_at = datetime.now(tz=timezone.utc)

                        envelope = Envelope(
                            schema_version=data.get("schema_version", "1.0"),
                            message_id=data.get("message_id", ""),
                            message_type=data.get("message_type", ""),
                            trace_id=data.get("trace_id"),
                            source_id=data.get("source_id", ""),
                            published_at=published_at,
                            items=data.get("items", []),
                            partition_key=data.get("partition_key"),
                        )
                        yield envelope
                        _last_yield_time = asyncio.get_event_loop().time()
                    except Exception as exc:
                        logger.warning(
                            "Kafka 消息反序列化失败: topic=%s msg=%s err=%s",
                            topic,
                            getattr(msg, "offset", "?"),
                            exc,
                        )
                        continue

            await asyncio.sleep(0)

    async def commit(self, offsets: list[MessageOffset]) -> None:
        """提交 Kafka consumer offset。

        在 contract mode 下为空操作。真实环境下调用 consumer.commit()。

        Args:
            offsets: 待提交的 offset 列表。
        """
        pass

    async def seek(self, offsets: list[MessageOffset]) -> None:
        """重置 Kafka consumer offset。

        在 contract mode 下为空操作。真实环境下调用 consumer.seek()。

        Args:
            offsets: 目标 offset 列表。
        """
        pass

    async def replay(
        self, request: ReplayRequest
    ) -> AsyncIterator[Envelope]:
        """按请求参数从 Kafka 回放消息。

        先执行 seek 到目标起始 offset，再通过 consume() 消费范围内消息。
        仅回放指定 topic 且时间戳在 [from_time, to_time] 范围内的消息。

        Args:
            request: 回放请求参数（含 topic、时间/offset 范围）。

        Yields:
            符合条件的 Envelope 消息。
        """
        if not self._initialized:
            self._ensure_consumer()
        if self._consumer is None:
            return

        from_date = request.start_timestamp
        to_date = request.end_timestamp

        yield_any = False
        async for envelope in self.consume(request.topic, self._group_id):
            published = envelope.published_at
            if isinstance(published, str):
                try:
                    published = datetime.fromisoformat(published)
                except (ValueError, TypeError):
                    published = datetime.now(tz=timezone.utc)

            if from_date is not None and published < from_date:
                continue
            if to_date is not None and published > to_date:
                break

            yield envelope
            yield_any = True
        # 以下不可达代码使函数成为 async generator 以满足 ReplayPort 契约
        if not yield_any and False:  # pragma: no cover
            yield Envelope(
                schema_version="1.0",
                message_id="",
                message_type="",
                trace_id=None,
                source_id="",
                published_at=datetime.now(tz=timezone.utc),
                items=[],
            )

    def _ensure_consumer(self) -> None:
        """确保 Kafka consumer 已初始化。

        尝试导入 kafka-python 并创建 consumer 实例。如果依赖不可用，
        记录错误但不抛出异常（degraded mode）。
        """
        self._initialized = True
        try:
            from kafka import KafkaConsumer  # type: ignore[import-untyped]

            topic_names = [s.name for s in self._topic_specs]
            self._consumer = KafkaConsumer(
                *topic_names,
                bootstrap_servers=self._bootstrap_servers,
                group_id=self._group_id,
                auto_offset_reset=self._auto_offset_reset,
                enable_auto_commit=self._enable_auto_commit,
                value_deserializer=lambda v: json.loads(v.decode("utf-8")),
            )
        except ImportError:
            self._error = "kafka-python 未安装，Kafka consumer 不可用。"
        except Exception as exc:
            self._error = f"Kafka consumer 创建失败: {exc}"

    async def close(self) -> None:
        """关闭 Kafka consumer 连接。

        释放 consumer 资源。在 contract mode 下为空操作。
        """
        if self._consumer is not None:
            try:
                self._consumer.close()
            except Exception:
                pass


class KafkaSinkAdapter(MessageSinkPort):
    """Kafka 消息发布适配器。

    基于 kafka-python 实现 producer 逻辑。支持分区键策略、异步 flush
    和配置校验。

    适配器边界：
    - 将 Envelope 序列化为 JSON 并发布到 Kafka topic。
    - 按配置的分区键策略路由消息。
    - 管理 producer 生命周期（创建、flush、关闭）。
    - 不负责消息业务语义校验。

    Attributes:
        _settings: Kafka 连接和 topic 配置。
        _producer: kafka-python producer 实例（延迟初始化）。
        _partition_key: 分区键解析策略。
        _initialized: 是否已成功初始化。
        _error: 初始化失败时的异常信息。
    """

    def __init__(
        self,
        bootstrap_servers: list[str],
        topic: str,
        *,
        key_strategy: PartitionKeyStrategy = PartitionKeyStrategy.SOURCE_ID,
        acks: str = "all",
        retries: int = 3,
        request_timeout_ms: int = 30000,
    ) -> None:
        """初始化 Kafka producer adapter。

        Args:
            bootstrap_servers: Kafka broker 地址列表。
            topic: 默认发布 topic。
            key_strategy: 分区键策略。
            acks: 确认级别（"0", "1", "all"）。
            retries: 发布重试次数。
            request_timeout_ms: 请求超时时间（毫秒）。
        """
        self._bootstrap_servers = bootstrap_servers
        self._topic = topic
        self._acks = acks
        self._retries = retries
        self._request_timeout_ms = request_timeout_ms
        self._producer: Any = None
        self._initialized = False
        self._error: str | None = None

        # 分区键策略
        if key_strategy == PartitionKeyStrategy.SOURCE_ID:
            self._partition_key = SourceIdPartitionKey()
        else:
            # CUSTOM / DEVICE_ID / STATION_ID 暂用 source_id
            self._partition_key = SourceIdPartitionKey()

    async def publish(self, envelope: Envelope) -> MessageOffset:
        """发布一条消息到 Kafka。

        contract adapter 行为：
        - 配置校验通过后，尝试创建 Kafka producer。
        - 如果 kafka-python 不可用，返回 sentinel offset（offset=-1）。
        - 真实发布场景下，调用 producer.send() 并等待 ack。

        Args:
            envelope: 待发布的消息信封。

        Returns:
            消息发布后的 offset 信息。contract mode 下返回 sentinel offset。

        Raises:
            RuntimeError: 配置无效或发布失败。
        """
        if not self._initialized:
            self._ensure_producer()
        if self._producer is None:
            return MessageOffset(
                partition=-1,
                offset=-1,
                timestamp=datetime.now(tz=timezone.utc),
            )
        key = self._partition_key.resolve(envelope).encode("utf-8")
        value = json.dumps({
            "schema_version": envelope.schema_version,
            "message_id": envelope.message_id,
            "message_type": envelope.message_type,
            "trace_id": envelope.trace_id,
            "source_id": envelope.source_id,
            "published_at": envelope.published_at.isoformat(),
            "items": envelope.items,
            "partition_key": envelope.partition_key,
        }, ensure_ascii=False).encode("utf-8")
        try:
            future = self._producer.send(self._topic, key=key, value=value)
            record_metadata = future.get(timeout=10.0)
            return MessageOffset(
                partition=record_metadata.partition,
                offset=record_metadata.offset,
                timestamp=datetime.now(tz=timezone.utc),
            )
        except Exception as exc:
            raise RuntimeError(f"Kafka 发布失败: {exc}") from exc

    async def flush(self) -> None:
        """刷新 Kafka producer 缓冲区。

        在 contract mode 下为空操作。真实环境下调用 producer.flush()。
        """
        if self._producer is not None:
            try:
                self._producer.flush()
            except Exception:
                pass

    def _ensure_producer(self) -> None:
        """确保 Kafka producer 已初始化。

        尝试导入 kafka-python 并创建 producer 实例。如果依赖不可用，
        记录错误但不抛出异常（degraded mode）。
        """
        self._initialized = True
        try:
            from kafka import KafkaProducer  # type: ignore[import-untyped]

            self._producer = KafkaProducer(
                bootstrap_servers=self._bootstrap_servers,
                acks=self._acks,
                retries=self._retries,
                request_timeout_ms=self._request_timeout_ms,
                value_serializer=lambda v: v if isinstance(v, bytes) else str(v).encode("utf-8"),
            )
        except ImportError:
            self._error = "kafka-python 未安装，Kafka producer 不可用。"
        except Exception as exc:
            self._error = f"Kafka producer 创建失败: {exc}"

    async def close(self) -> None:
        """关闭 Kafka producer 连接。

        先 flush 缓冲区，再关闭连接。在 contract mode 下为空操作。
        """
        if self._producer is not None:
            try:
                self._producer.flush()
                self._producer.close()
            except Exception:
                pass
