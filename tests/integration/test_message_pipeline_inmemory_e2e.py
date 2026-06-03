"""message_pipeline InMemory 全链路集成测试。

验证 InMemoryMessageBus + InMemoryDeadLetterSink + InMemorySchemaRegistry
的端到端协同行为：消息发布 → 消费 → DLQ 处理 → schema 注册。

被验证对象：
- whale.message_pipeline.adapters.in_memory: 全部 InMemory 实现

测试阶段：模块集成期验证 (simulator)（内存模拟，E2E 流程覆盖）。
不能证明：真实 Kafka/Pulsar broker 的网络通信、分区分配和 offset 管理。
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from whale.message_pipeline.adapters.in_memory import (
    InMemoryDeadLetterSink,
    InMemoryMessageBus,
    InMemorySchemaRegistry,
)
from whale.message_pipeline.model import (
    Envelope,
    ReplayRequest,
)


def _make_envelope(
    message_id: str = "msg-001",
    source_id: str = "source-1",
    message_type: str = "state_snapshot",
) -> Envelope:
    """构造测试用 Envelope。"""
    return Envelope(
        schema_version="1.0",
        message_id=message_id,
        message_type=message_type,
        trace_id=f"trace-{message_id}",
        source_id=source_id,
        published_at=datetime.now(tz=timezone.utc),
        items=[{"variable_key": "temp", "value": "25.5"}],
    )


class TestInMemoryMessagePipelineE2E:
    """InMemory message pipeline 全链路集成测试。"""

    @pytest.mark.asyncio
    async def test_publish_consume_schema_dlq_flow(self) -> None:
        """验证发布 → 消费 → schema 注册 → 失败 DLQ 的完整流程。

        流程：
        1. 注册 schema
        2. 发布 5 条消息
        3. 消费全部 5 条，前 3 条成功，后 2 条失败写入 DLQ
        4. 验证 schema 可查询和 DLQ 记录正确
        """
        bus = InMemoryMessageBus()
        dlq = InMemoryDeadLetterSink()
        registry = InMemorySchemaRegistry()

        # 注册 schema
        schema = {"type": "record", "name": "StateSnapshot", "fields": []}
        version = await registry.register("whale.state_snapshot", schema)
        assert version == 1

        # 发布消息
        for i in range(5):
            env = _make_envelope(message_id=f"msg-{i:03d}")
            await bus.publish(env)

        # 消费全部消息，前 3 条成功，后 2 条失败
        consumed: list[Envelope] = []
        async for env in bus.consume("whale.state_snapshot", "group-1"):
            consumed.append(env)
            if len(consumed) > 3:
                # 模拟后 2 条处理失败，写入 DLQ
                await dlq.send(env, "processing_failure", retry_count=1)

        assert len(consumed) == 5
        assert len(dlq.dead_letters) == 2

        # 验证 schema 仍然可查
        retrieved = await registry.get_schema("whale.state_snapshot")
        assert retrieved == schema

    @pytest.mark.asyncio
    async def test_multi_topic_publish_and_consume(self) -> None:
        """验证多 topic 消息发布和各自独立消费。"""
        bus = InMemoryMessageBus()

        snapshot = _make_envelope(
            message_type="state_snapshot", message_id="snap-1"
        )
        event = _make_envelope(message_type="event", message_id="evt-1")

        await bus.publish(snapshot)
        await bus.publish(event)

        snap_msgs = [e async for e in bus.consume("whale.state_snapshot", "g1")]
        evt_msgs = [e async for e in bus.consume("whale.event", "g1")]

        assert len(snap_msgs) == 1
        assert len(evt_msgs) == 1
        assert snap_msgs[0].message_type == "state_snapshot"
        assert evt_msgs[0].message_type == "event"

    @pytest.mark.asyncio
    async def test_replay_all_messages(self) -> None:
        """验证回放请求返回 topic 中所有消息。"""
        bus = InMemoryMessageBus()

        for i in range(3):
            await bus.publish(_make_envelope(message_id=f"msg-{i:03d}"))

        req = ReplayRequest(topic="whale.state_snapshot")
        replayed = [e async for e in bus.replay(req)]
        assert len(replayed) == 3

    @pytest.mark.asyncio
    async def test_consumer_group_isolation_full_flow(self) -> None:
        """验证两个 consumer group 独立消费，offset 互不干扰。"""
        bus = InMemoryMessageBus()

        for i in range(4):
            await bus.publish(_make_envelope(message_id=f"msg-{i:03d}"))

        g1 = [e async for e in bus.consume("whale.state_snapshot", "group-a")]
        g2 = [e async for e in bus.consume("whale.state_snapshot", "group-b")]

        assert len(g1) == 4
        assert len(g2) == 4
        assert g1[0].message_id == g2[0].message_id
