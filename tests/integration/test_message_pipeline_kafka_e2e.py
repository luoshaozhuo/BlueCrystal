"""message_pipeline Kafka 集成测试（contract-only）。

验证 KafkaSourceAdapter 和 KafkaSinkAdapter 在 contract mode 下的接口契约
和配置校验。如果 Kafka broker 可用，可扩展为真实连接测试。

被验证对象：
- whale.message_pipeline.adapters.kafka: KafkaSourceAdapter, KafkaSinkAdapter

测试阶段：开发期验证 (contract/stub)（contract adapter 配置校验和接口契约验证）。
当环境变量 WHALE_KAFKA_BROKERS 存在且真实 Kafka 可用时，为跨模块联调期验证 (integration)。
当前默认为 contract-only。

不能证明（contract mode）：真实 Kafka broker 的发布/消费/offset 管理行为。
"""

from __future__ import annotations

import os
import socket
from datetime import datetime, timezone

import pytest

from whale.message_pipeline.adapters.kafka import (
    KafkaSinkAdapter,
    KafkaSourceAdapter,
)
from whale.message_pipeline.model import (
    Envelope,
    PartitionKeyStrategy,
    ReplayRequest,
    TopicSpec,
)


def _kafka_reachable(
    host: str = "localhost",
    port: int = 9092,
    timeout: float = 1.0,
) -> bool:
    """检测 Kafka broker 是否可达（TCP connect 探测）。

    当环境变量 WHALE_KAFKA_BROKERS 存在，或 localhost:9092 可连接时，
    认为真实 Kafka 可用，应 skip contract sentinel 断言测试。
    """
    if os.environ.get("WHALE_KAFKA_BROKERS"):
        return True
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


KAFKA_AVAILABLE = _kafka_reachable()


def _make_envelope(
    message_id: str = "msg-001",
    source_id: str = "source-1",
) -> Envelope:
    """构造测试用 Envelope。"""
    return Envelope(
        schema_version="1.0",
        message_id=message_id,
        message_type="state_snapshot",
        trace_id=f"trace-{message_id}",
        source_id=source_id,
        published_at=datetime.now(tz=timezone.utc),
        items=[{"variable_key": "temp", "value": "25.5"}],
    )


class TestKafkaE2EContract:
    """Kafka E2E contract 验证测试。"""

    def test_source_adapter_config_validation(self) -> None:
        """验证 KafkaSourceAdapter 配置可正常创建。"""
        adapter = KafkaSourceAdapter(
            bootstrap_servers=["localhost:9092"],
            group_id="e2e-test-group",
            topic_specs=[
                TopicSpec(name="test-topic", partitions=1, replication_factor=1)
            ],
            auto_offset_reset="earliest",
            enable_auto_commit=False,
        )
        assert adapter is not None
        assert adapter._bootstrap_servers == ["localhost:9092"]
        assert adapter._group_id == "e2e-test-group"

    def test_sink_adapter_config_validation(self) -> None:
        """验证 KafkaSinkAdapter 配置可正常创建。"""
        adapter = KafkaSinkAdapter(
            bootstrap_servers=["localhost:9092"],
            topic="test-topic",
            key_strategy=PartitionKeyStrategy.SOURCE_ID,
            acks="all",
            retries=3,
            request_timeout_ms=60000,
        )
        assert adapter is not None
        assert adapter._topic == "test-topic"
        assert adapter._acks == "all"

    @pytest.mark.asyncio
    async def test_source_consume_contract_empty(self) -> None:
        """验证 contract mode 下 consume 返回空迭代器。"""
        adapter = KafkaSourceAdapter(
            bootstrap_servers=["localhost:9092"],
            group_id="test-group",
            topic_specs=[TopicSpec(name="test-topic")],
        )
        messages = [
            e async for e in adapter.consume("test-topic", "test-group")
        ]
        assert messages == []

    @pytest.mark.asyncio
    async def test_source_replay_contract_empty(self) -> None:
        """验证 contract mode 下 replay 返回空迭代器。"""
        adapter = KafkaSourceAdapter(
            bootstrap_servers=["localhost:9092"],
            group_id="test-group",
            topic_specs=[TopicSpec(name="test-topic")],
        )
        req = ReplayRequest(topic="test-topic")
        messages = [e async for e in adapter.replay(req)]
        assert messages == []

    @pytest.mark.skipif(KAFKA_AVAILABLE, reason="Real Kafka available, skip contract sentinel tests")
    @pytest.mark.asyncio
    async def test_sink_publish_contract_returns_sentinel(self) -> None:
        """验证 contract mode 下 publish 返回 sentinel offset。"""
        adapter = KafkaSinkAdapter(
            bootstrap_servers=["localhost:9092"],
            topic="test-topic",
        )
        env = _make_envelope()
        offset = await adapter.publish(env)
        assert offset.partition == -1
        assert offset.offset == -1

    @pytest.mark.skipif(KAFKA_AVAILABLE, reason="Real Kafka available, skip contract sentinel tests")
    @pytest.mark.asyncio
    async def test_full_contract_flow(self) -> None:
        """验证完整的 Kafka contract flow：source+replay+sink 组合。"""
        source = KafkaSourceAdapter(
            bootstrap_servers=["localhost:9092"],
            group_id="test-group",
            topic_specs=[TopicSpec(name="test-topic")],
        )
        sink = KafkaSinkAdapter(
            bootstrap_servers=["localhost:9092"],
            topic="test-topic",
        )

        # 发布（contract mode）
        env = _make_envelope()
        offset = await sink.publish(env)
        assert offset.offset == -1  # sentinel

        # 消费（contract mode）
        messages = [e async for e in source.consume("test-topic", "test-group")]
        assert messages == []

        # 回放（contract mode）
        req = ReplayRequest(topic="test-topic")
        replayed = [e async for e in source.replay(req)]
        assert replayed == []
