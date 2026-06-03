"""Pulsar 消息管道适配器（contract adapter）。

提供 message_pipeline 的 Pulsar 端口契约适配器：
- PulsarSourceAdapter: Pulsar consumer 契约适配器。
- PulsarSinkAdapter: Pulsar producer 契约适配器。

Pulsar 依赖标记为 optional（extras_require: pulsar）。当前为 contract adapter，
仅验证配置和接口契约，不连接真实 Pulsar broker。

在 pulsar-client 可用时，adapter 可切换为真实连接模式。
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import datetime, timezone
from typing import Any

from whale.message_pipeline.model import (
    Envelope,
    MessageOffset,
    PartitionKeyStrategy,
    ReplayRequest,
    SourceIdPartitionKey,
    TopicSpec,
)
from whale.message_pipeline.ports import (
    MessageSinkPort,
    MessageSourcePort,
    ReplayPort,
)


class PulsarSourceAdapter(MessageSourcePort, ReplayPort):
    """Pulsar 消息消费 contract adapter。

    提供符合 MessageSourcePort 契约的 Pulsar consumer 适配器。
    当前为 contract-only 模式，验证配置正确性但不连接真实 broker。

    environment-pending: 需要 Pulsar broker 环境和 pulsar-client 依赖。

    Attributes:
        _service_url: Pulsar service URL。
        _topic_specs: 订阅的 topic 配置列表。
        _config_valid: 配置是否通过基本校验。
    """

    def __init__(
        self,
        service_url: str,
        topic_specs: list[TopicSpec],
        *,
        subscription_name: str = "whale-speed-layer",
        subscription_type: str = "Shared",
    ) -> None:
        """初始化 Pulsar consumer contract adapter。

        校验 service_url 非空和 topic_specs 非空，标记 environment-pending。

        Args:
            service_url: Pulsar broker 服务地址（如 pulsar://localhost:6650）。
            topic_specs: 订阅的 topic 配置列表。
            subscription_name: Pulsar 订阅名称。
            subscription_type: 订阅类型（Exclusive/Shared/Failover/Key_Shared）。
        """
        self._service_url = service_url
        self._topic_specs = topic_specs
        self._subscription_name = subscription_name
        self._subscription_type = subscription_type
        self._config_valid = bool(service_url and topic_specs)
        # environment-pending: Pulsar broker 环境依赖
        self._consumer: Any = None
        self._error: str | None = (
            None if self._config_valid else "service_url 或 topic_specs 无效"
        )

    async def consume(
        self, topic: str, group_id: str
    ) -> AsyncIterator[Envelope]:
        """从 Pulsar topic 消费消息（contract-only 模式）。

        environment-pending: 返回空迭代器。真实环境下通过 pulsar-client
        的 reader/consumer API 实现。

        Args:
            topic: 消费的 topic 名称。
            group_id: consumer group / subscription 标识。

        Yields:
            environment-pending 时返回空。
        """
        # environment-pending: 无消息可消费
        return
        # 以下不可达代码使函数成为 async generator，匹配 MessageSourcePort 接口契约
        # 真实 Pulsar 环境下替换为 pulsar-client consumer 逻辑
        if False:  # pragma: no cover
            yield Envelope(
                schema_version="1.0",
                message_id="",
                message_type="",
                trace_id=None,
                source_id="",
                published_at=datetime.now(tz=timezone.utc),
                items=[],
            )

    async def commit(self, offsets: list[MessageOffset]) -> None:
        """提交 Pulsar consumer offset（contract-only 模式）。

        environment-pending: 空操作。

        Args:
            offsets: 待提交的 offset 列表。
        """
        pass

    async def seek(self, offsets: list[MessageOffset]) -> None:
        """重置 Pulsar consumer offset（contract-only 模式）。

        environment-pending: 空操作。

        Args:
            offsets: 目标 offset 列表。
        """
        pass

    async def replay(
        self, request: ReplayRequest
    ) -> AsyncIterator[Envelope]:
        """按请求参数从 Pulsar 回放消息（contract-only 模式）。

        environment-pending: 返回空迭代器。

        Args:
            request: 回放请求参数。

        Yields:
            environment-pending 时返回空。
        """
        # environment-pending: 无消息可回放
        return
        # 以下不可达代码使函数成为 async generator，匹配 ReplayPort 接口契约
        if False:  # pragma: no cover
            yield Envelope(
                schema_version="1.0",
                message_id="",
                message_type="",
                trace_id=None,
                source_id="",
                published_at=datetime.now(tz=timezone.utc),
                items=[],
            )

    async def close(self) -> None:
        """关闭 Pulsar consumer 连接。

        environment-pending: 空操作。
        """
        pass


class PulsarSinkAdapter(MessageSinkPort):
    """Pulsar 消息发布 contract adapter。

    提供符合 MessageSinkPort 契约的 Pulsar producer 适配器。
    当前为 contract-only 模式，验证配置正确性但不连接真实 broker。

    environment-pending: 需要 Pulsar broker 环境和 pulsar-client 依赖。

    Attributes:
        _service_url: Pulsar service URL。
        _topic: 发布 topic。
        _config_valid: 配置是否通过基本校验。
    """

    def __init__(
        self,
        service_url: str,
        topic: str,
        *,
        key_strategy: PartitionKeyStrategy = PartitionKeyStrategy.SOURCE_ID,
    ) -> None:
        """初始化 Pulsar producer contract adapter。

        校验 service_url 和 topic 非空，标记 environment-pending。

        Args:
            service_url: Pulsar broker 服务地址。
            topic: 发布 topic。
            key_strategy: 分区键策略。
        """
        self._service_url = service_url
        self._topic = topic
        self._config_valid = bool(service_url and topic)
        self._partition_key = SourceIdPartitionKey()
        # environment-pending: Pulsar broker 环境依赖
        self._producer: Any = None
        self._error: str | None = (
            None if self._config_valid else "service_url 或 topic 无效"
        )

    async def publish(self, envelope: Envelope) -> MessageOffset:
        """发布一条消息到 Pulsar（contract-only 模式）。

        environment-pending: 返回 sentinel offset。真实环境下通过 pulsar-client
        的 producer API 实现。

        Args:
            envelope: 待发布的消息信封。

        Returns:
            sentinel MessageOffset（offset=-1, partition=-1）。
        """
        return MessageOffset(
            partition=-1,
            offset=-1,
            timestamp=datetime.now(tz=timezone.utc),
        )

    async def flush(self) -> None:
        """刷新 Pulsar producer 缓冲区（contract-only 模式）。

        environment-pending: 空操作。
        """
        pass

    async def close(self) -> None:
        """关闭 Pulsar producer 连接。

        environment-pending: 空操作。
        """
        pass
