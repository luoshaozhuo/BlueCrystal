"""Kafka message_pipeline 适配器契约与配置测试。

验证 KafkaSourceAdapter 和 KafkaSinkAdapter 的配置校验、contract mode 行为和
接口契约兼容性。不连接真实 Kafka broker。

被验证对象：
- whale.message_pipeline.adapters.kafka: KafkaSourceAdapter, KafkaSinkAdapter

证据等级：L2 contract/stub（contract adapter 配置校验，不连接真实 broker）。
不能证明：真实 Kafka broker 的发布/消费/offset 管理行为。
"""

from __future__ import annotations

import pytest

from whale.message_pipeline.adapters.kafka import (
    KafkaSinkAdapter,
    KafkaSourceAdapter,
)
from whale.message_pipeline.model import (
    PartitionKeyStrategy,
    SourceIdPartitionKey,
    TopicSpec,
)
from whale.message_pipeline.ports import MessageSinkPort, MessageSourcePort, ReplayPort


class TestKafkaSourceAdapterConfig:
    """KafkaSourceAdapter 配置校验测试。"""

    def test_creates_with_valid_config(self) -> None:
        """验证有效配置下 adapter 可创建。"""
        adapter = KafkaSourceAdapter(
            bootstrap_servers=["localhost:9092"],
            group_id="test-group",
            topic_specs=[TopicSpec(name="test-topic")],
        )
        assert adapter is not None

    def test_is_message_source_port(self) -> None:
        """验证 KafkaSourceAdapter 实现 MessageSourcePort。"""
        adapter = KafkaSourceAdapter(
            bootstrap_servers=["localhost:9092"],
            group_id="test-group",
            topic_specs=[TopicSpec(name="test-topic")],
        )
        assert isinstance(adapter, MessageSourcePort)

    def test_is_replay_port(self) -> None:
        """验证 KafkaSourceAdapter 实现 ReplayPort。"""
        adapter = KafkaSourceAdapter(
            bootstrap_servers=["localhost:9092"],
            group_id="test-group",
            topic_specs=[TopicSpec(name="test-topic")],
        )
        assert isinstance(adapter, ReplayPort)

    def test_config_with_auto_offset_reset(self) -> None:
        """验证可配置 auto_offset_reset 策略。"""
        adapter = KafkaSourceAdapter(
            bootstrap_servers=["localhost:9092"],
            group_id="test-group",
            topic_specs=[TopicSpec(name="test-topic")],
            auto_offset_reset="latest",
            enable_auto_commit=True,
        )
        assert adapter._auto_offset_reset == "latest"
        assert adapter._enable_auto_commit is True

    @pytest.mark.asyncio
    async def test_consume_in_contract_mode_returns_empty(self) -> None:
        """验证 contract mode 下 consume 返回空迭代器。"""
        adapter = KafkaSourceAdapter(
            bootstrap_servers=["localhost:9092"],
            group_id="test-group",
            topic_specs=[TopicSpec(name="test-topic")],
        )
        messages = [
            e
            async for e in adapter.consume("test-topic", "test-group")
        ]
        assert len(messages) == 0

    @pytest.mark.asyncio
    async def test_replay_in_contract_mode_returns_empty(self) -> None:
        """验证 contract mode 下 replay 返回空迭代器。"""
        from whale.message_pipeline.model import ReplayRequest

        adapter = KafkaSourceAdapter(
            bootstrap_servers=["localhost:9092"],
            group_id="test-group",
            topic_specs=[TopicSpec(name="test-topic")],
        )
        req = ReplayRequest(topic="test-topic")
        messages = [e async for e in adapter.replay(req)]
        assert len(messages) == 0

    @pytest.mark.asyncio
    async def test_commit_and_seek_noop(self) -> None:
        """验证 contract mode 下 commit/seek 为空操作不报错。"""
        from whale.message_pipeline.model import MessageOffset

        adapter = KafkaSourceAdapter(
            bootstrap_servers=["localhost:9092"],
            group_id="test-group",
            topic_specs=[TopicSpec(name="test-topic")],
        )
        offset = MessageOffset(partition=0, offset=0)
        await adapter.commit([offset])
        await adapter.seek([offset])
        # 不抛异常即为通过


class TestKafkaSinkAdapterConfig:
    """KafkaSinkAdapter 配置校验测试。"""

    def test_creates_with_valid_config(self) -> None:
        """验证有效配置下 adapter 可创建。"""
        adapter = KafkaSinkAdapter(
            bootstrap_servers=["localhost:9092"],
            topic="test-topic",
        )
        assert adapter is not None

    def test_is_message_sink_port(self) -> None:
        """验证 KafkaSinkAdapter 实现 MessageSinkPort。"""
        adapter = KafkaSinkAdapter(
            bootstrap_servers=["localhost:9092"],
            topic="test-topic",
        )
        assert isinstance(adapter, MessageSinkPort)

    def test_default_key_strategy(self) -> None:
        """验证默认分区键策略为 SOURCE_ID。"""
        adapter = KafkaSinkAdapter(
            bootstrap_servers=["localhost:9092"],
            topic="test-topic",
        )
        assert isinstance(adapter._partition_key, SourceIdPartitionKey)

    def test_config_with_different_strategy(self) -> None:
        """验证可配置不同分区键策略。"""
        adapter = KafkaSinkAdapter(
            bootstrap_servers=["localhost:9092"],
            topic="test-topic",
            key_strategy=PartitionKeyStrategy.DEVICE_ID,
        )
        # DEVICE_ID 暂 fallback 到 SourceIdPartitionKey（contract mode）
        assert isinstance(adapter._partition_key, SourceIdPartitionKey)
