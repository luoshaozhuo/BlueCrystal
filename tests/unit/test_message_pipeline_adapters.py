"""message_pipeline InMemory 适配器单元测试。

验证 InMemoryMessageBus、InMemoryDeadLetterSink、InMemorySchemaRegistry
的行为正确性：消息发布/消费/回放、DLQ 写入、schema 注册/查询。

被验证对象：
- whale.message_pipeline.adapters.in_memory: InMemoryMessageBus,
  InMemoryDeadLetterSink, InMemorySchemaRegistry

所属生命周期阶段：开发期验证（纯内存测试，fake 实现，不连接任何 broker）。
不能证明：真实 Kafka/Pulsar broker 的发布/消费/回放行为。
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
    MessageOffset,
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
        trace_id=None,
        source_id=source_id,
        published_at=datetime.now(tz=timezone.utc),
        items=[{"variable_key": "temp", "value": "25.5"}],
    )


class TestInMemoryMessageBus:
    """InMemoryMessageBus 单元测试。"""

    @pytest.mark.asyncio
    async def test_publish_and_consume_single_message(self) -> None:
        """验证发布一条消息后可消费到该消息。"""
        bus = InMemoryMessageBus()
        env = _make_envelope()

        offset = await bus.publish(env)
        assert offset.partition == 0
        assert offset.offset >= 0

        consumed: list[Envelope] = []
        async for e in bus.consume("whale.state_snapshot", "group-1"):
            consumed.append(e)

        assert len(consumed) == 1
        assert consumed[0].message_id == "msg-001"

    @pytest.mark.asyncio
    async def test_publish_and_consume_multiple_messages(self) -> None:
        """验证发布多条消息后可全部消费。"""
        bus = InMemoryMessageBus()
        for i in range(5):
            env = _make_envelope(message_id=f"msg-{i:03d}")
            await bus.publish(env)

        consumed: list[Envelope] = []
        async for e in bus.consume("whale.state_snapshot", "group-1"):
            consumed.append(e)

        assert len(consumed) == 5

    @pytest.mark.asyncio
    async def test_consumer_group_isolation(self) -> None:
        """验证不同 consumer group 独立消费（不互相影响 offset）。"""
        bus = InMemoryMessageBus()
        for i in range(3):
            await bus.publish(_make_envelope(message_id=f"msg-{i:03d}"))

        # Group 1 消费全部 3 条
        g1_msgs = [e async for e in bus.consume("whale.state_snapshot", "g1")]
        assert len(g1_msgs) == 3

        # Group 2 也能消费全部 3 条（独立 offset）
        g2_msgs = [e async for e in bus.consume("whale.state_snapshot", "g2")]
        assert len(g2_msgs) == 3

    @pytest.mark.asyncio
    async def test_replay_by_timestamp(self) -> None:
        """验证按时间范围回放消息。"""
        bus = InMemoryMessageBus()
        t1 = datetime(2026, 6, 1, tzinfo=timezone.utc)
        t2 = datetime(2026, 6, 2, tzinfo=timezone.utc)
        t3 = datetime(2026, 6, 3, tzinfo=timezone.utc)

        env1 = _make_envelope(message_id="early")
        env1 = Envelope(
            schema_version=env1.schema_version,
            message_id=env1.message_id,
            message_type=env1.message_type,
            trace_id=env1.trace_id,
            source_id=env1.source_id,
            published_at=t1,
            items=env1.items,
        )
        env2 = _make_envelope(message_id="mid")
        env2 = Envelope(
            schema_version=env2.schema_version,
            message_id=env2.message_id,
            message_type=env2.message_type,
            trace_id=env2.trace_id,
            source_id=env2.source_id,
            published_at=t2,
            items=env2.items,
        )
        env3 = _make_envelope(message_id="late")
        env3 = Envelope(
            schema_version=env3.schema_version,
            message_id=env3.message_id,
            message_type=env3.message_type,
            trace_id=env3.trace_id,
            source_id=env3.source_id,
            published_at=t3,
            items=env3.items,
        )
        await bus.publish(env1)
        await bus.publish(env2)
        await bus.publish(env3)

        req = ReplayRequest(
            topic="whale.state_snapshot",
            start_timestamp=t2,
            end_timestamp=t3,
        )
        replayed = [e async for e in bus.replay(req)]
        assert len(replayed) == 2
        ids = {e.message_id for e in replayed}
        assert ids == {"mid", "late"}

    @pytest.mark.asyncio
    async def test_flush_is_noop(self) -> None:
        """验证 flush 是空操作但不报错。"""
        bus = InMemoryMessageBus()
        await bus.flush()  # 不应抛异常

    @pytest.mark.asyncio
    async def test_seek_resets_offset(self) -> None:
        """验证 seek 可重置消费位置。"""
        bus = InMemoryMessageBus()
        for i in range(3):
            await bus.publish(_make_envelope(message_id=f"msg-{i:03d}"))

        # 消费 2 条
        g1_msgs = [e async for e in bus.consume("whale.state_snapshot", "g1")]
        assert len(g1_msgs) == 3

        # seek 回到起始
        await bus.seek([MessageOffset(partition=0, offset=0)])
        g1_again = [e async for e in bus.consume("whale.state_snapshot", "g1")]
        assert len(g1_again) == 3


class TestInMemoryDeadLetterSink:
    """InMemoryDeadLetterSink 单元测试。"""

    @pytest.mark.asyncio
    async def test_send_records_to_dlq(self) -> None:
        """验证 DLQ 正确记录失败消息和上下文。"""
        dlq = InMemoryDeadLetterSink()
        env = _make_envelope()

        await dlq.send(env, "kafka_timeout", retry_count=3)

        assert len(dlq.dead_letters) == 1
        record = dlq.dead_letters[0]
        assert record["envelope"] == env
        assert record["error"] == "kafka_timeout"
        assert record["retry_count"] == 3

    @pytest.mark.asyncio
    async def test_multiple_dlq_entries(self) -> None:
        """验证多条 DLQ 记录按顺序保存。"""
        dlq = InMemoryDeadLetterSink()
        for i in range(3):
            env = _make_envelope(message_id=f"msg-{i:03d}")
            await dlq.send(env, f"error-{i}", retry_count=i + 1)

        assert len(dlq.dead_letters) == 3
        assert dlq.dead_letters[2]["error"] == "error-2"


class TestInMemorySchemaRegistry:
    """InMemorySchemaRegistry 单元测试。"""

    @pytest.mark.asyncio
    async def test_register_and_get_schema(self) -> None:
        """验证注册 schema 后可查询到。"""
        registry = InMemorySchemaRegistry()
        schema = {"type": "record", "name": "test"}

        version = await registry.register("test-topic", schema)
        assert version == 1

        retrieved = await registry.get_schema("test-topic")
        assert retrieved == schema

    @pytest.mark.asyncio
    async def test_get_unregistered_schema_returns_none(self) -> None:
        """验证查询未注册 schema 返回 None。"""
        registry = InMemorySchemaRegistry()
        result = await registry.get_schema("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_register_overwrites_existing(self) -> None:
        """验证重复注册会覆盖已有 schema。"""
        registry = InMemorySchemaRegistry()
        schema_v1 = {"version": 1}
        schema_v2 = {"version": 2}

        await registry.register("test-topic", schema_v1)
        await registry.register("test-topic", schema_v2)

        retrieved = await registry.get_schema("test-topic")
        assert retrieved == schema_v2
