"""speed layer DLQ 与 replay 语义集成测试。

验证 DLQ 写入、消息回放和故障恢复的 end-to-end 语义。

被验证对象：
- whale.message_pipeline.adapters.in_memory: InMemoryMessageBus, InMemoryDeadLetterSink
- whale.speed_layer.writers: writers 的 DLQ 处理行为

证据等级：L3 simulator（全内存闭环，DLQ/replay 语义覆盖）。
不能证明：真实 broker 的 DLQ topic、replay offset 管理和 fault tolerance。
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from whale.message_pipeline.adapters.in_memory import (
    InMemoryDeadLetterSink,
    InMemoryMessageBus,
)
from whale.message_pipeline.model import (
    Envelope,
    MessageOffset,
    ReplayRequest,
)
from whale.storage.raw_index import MemoryRawIndexSink
from whale.speed_layer.writers import RawIndexWriter


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
        items=[{"variable_key": "temp", "value": "25.5", "device_id": "dev-1"}],
    )


class TestDLQSemantics:
    """DLQ 语义集成测试。"""

    @pytest.mark.asyncio
    async def test_dlq_records_envelope_and_error_context(self) -> None:
        """验证 DLQ 记录包含完整的 envelope、错误信息和重试计数。"""
        dlq = InMemoryDeadLetterSink()
        env = _make_envelope(message_id="failed-msg")

        await dlq.send(env, "write_timeout", retry_count=3)

        assert len(dlq.dead_letters) == 1
        record = dlq.dead_letters[0]
        assert record["envelope"].message_id == "failed-msg"
        assert record["error"] == "write_timeout"
        assert record["retry_count"] == 3

    @pytest.mark.asyncio
    async def test_multiple_failures_to_dlq(self) -> None:
        """验证多条失败消息按序写入 DLQ。"""
        dlq = InMemoryDeadLetterSink()
        for i in range(5):
            env = _make_envelope(message_id=f"msg-{i:03d}")
            await dlq.send(env, f"error-{i % 2}", retry_count=1)

        assert len(dlq.dead_letters) == 5
        ids = [r["envelope"].message_id for r in dlq.dead_letters]
        assert ids == [f"msg-{i:03d}" for i in range(5)]

    @pytest.mark.asyncio
    async def test_raw_index_writer_sends_to_dlq_on_success(self) -> None:
        """验证 RawIndexWriter 正常写入时 DLQ 保持空。"""
        bus = InMemoryMessageBus()
        index = MemoryRawIndexSink()
        dlq = InMemoryDeadLetterSink()

        for i in range(3):
            await bus.publish(_make_envelope(message_id=f"msg-{i:03d}"))

        writer = RawIndexWriter(source=bus, index=index, dlq=dlq)
        count = await writer.run("whale.state_snapshot", "group-dlq-test")
        assert count == 3
        assert len(dlq.dead_letters) == 0

    @pytest.mark.asyncio
    async def test_dlq_contains_original_envelope_for_recovery(self) -> None:
        """验证 DLQ 中的 envelope 保持原始内容，可用于恢复。"""
        dlq = InMemoryDeadLetterSink()
        env = _make_envelope(
            message_id="recoverable-msg",
            source_id="restore-src",
        )
        await dlq.send(env, "temporary_failure", retry_count=1)

        # 从 DLQ 恢复：取出原始 envelope
        recovered = dlq.dead_letters[0]["envelope"]
        assert recovered.message_id == "recoverable-msg"
        assert recovered.source_id == "restore-src"
        assert recovered.items[0]["value"] == "25.5"


class TestReplaySemantics:
    """消息回放语义集成测试。"""

    @pytest.mark.asyncio
    async def test_replay_returns_all_messages_in_topic(self) -> None:
        """验证回放返回 topic 中所有消息。"""
        bus = InMemoryMessageBus()
        for i in range(4):
            t = datetime(2026, 6, 2, 10, i, 0, tzinfo=timezone.utc)
            env = Envelope(
                schema_version="1.0",
                message_id=f"msg-{i:03d}",
                message_type="state_snapshot",
                trace_id=None,
                source_id="src-1",
                published_at=t,
                items=[],
            )
            await bus.publish(env)

        req = ReplayRequest(topic="whale.state_snapshot")
        replayed = [e async for e in bus.replay(req)]
        assert len(replayed) == 4

    @pytest.mark.asyncio
    async def test_replay_with_timestamp_filter(self) -> None:
        """验证按时间窗口回放只返回范围内的消息。"""
        bus = InMemoryMessageBus()
        t1 = datetime(2026, 6, 1, tzinfo=timezone.utc)
        t2 = datetime(2026, 6, 2, tzinfo=timezone.utc)
        t3 = datetime(2026, 6, 3, tzinfo=timezone.utc)

        for msg_id, ts in [("early", t1), ("mid", t2), ("late", t3)]:
            await bus.publish(
                Envelope(
                    schema_version="1.0",
                    message_id=msg_id,
                    message_type="state_snapshot",
                    trace_id=None,
                    source_id="src-1",
                    published_at=ts,
                    items=[],
                )
            )

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
    async def test_replay_empty_topic_returns_nothing(self) -> None:
        """验证空 topic 回放返回空结果。"""
        bus = InMemoryMessageBus()
        req = ReplayRequest(topic="whale.nonexistent")
        replayed = [e async for e in bus.replay(req)]
        assert len(replayed) == 0

    @pytest.mark.asyncio
    async def test_seek_and_replay_flow(self) -> None:
        """验证 seek 重置 offset 后重新消费等同于回放。"""
        bus = InMemoryMessageBus()
        for i in range(3):
            await bus.publish(_make_envelope(message_id=f"msg-{i:03d}"))

        # 第一轮消费
        first = [e async for e in bus.consume("whale.state_snapshot", "g1")]
        assert len(first) == 3

        # seek 回起点
        await bus.seek([MessageOffset(partition=0, offset=0)])
        # 第二轮消费（模拟回放）
        second = [e async for e in bus.consume("whale.state_snapshot", "g1")]
        assert len(second) == 3
        assert [e.message_id for e in first] == [e.message_id for e in second]
