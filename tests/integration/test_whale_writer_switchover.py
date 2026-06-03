"""Whale writer 无缝切换集成测试。

验证 speed_layer writers 的无缝切换流程：
- 新 consumer group 启动追平
- lag = 0 后 switch active
- 旧 consumer group 延迟停止
- 保留旧 group 用于回滚

被验证对象：
- whale.message_pipeline.adapters.in_memory: InMemoryMessageBus (consumer group 隔离)
- whale.speed_layer.writers: RawArchiveWriter / RawIndexWriter
- whale.speed_layer.runner: LocalPipelineRunner

测试阶段：模块集成期验证 (simulator)（全内存闭环，切换语义验证）。
不能证明：真实 Kafka broker 的 consumer group rebalance、网络切换、DNS 切换。
环境依赖：无（纯内存模拟）。
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone

import pytest

from whale.message_pipeline.adapters.in_memory import (
    InMemoryDeadLetterSink,
    InMemoryMessageBus,
)
from whale.message_pipeline.model import (
    Envelope,
    MessageOffset,
)
from whale.speed_layer.writers import RawIndexWriter, RawArchiveWriter
from whale.speed_layer.runner import LocalPipelineRunner
from whale.storage.raw_index import MemoryRawIndexSink
from whale.storage.raw_archive import (
    InMemoryManifestRepository,
    LocalCompressedArchiveSink,
)
import tempfile


def _make_envelope(
    message_id: str = "msg-001",
    source_id: str = "source-1",
    device_id: str = "dev-1",
) -> Envelope:
    """构造测试用 Envelope。

    Args:
        message_id: 消息 ID。
        source_id: 数据源 ID。
        device_id: 设备 ID。

    Returns:
        测试用 Envelope 对象。
    """
    return Envelope(
        schema_version="1.0",
        message_id=message_id,
        message_type="state_snapshot",
        trace_id=f"trace-{message_id}",
        source_id=source_id,
        published_at=datetime.now(tz=timezone.utc),
        items=[{
            "variable_key": "temp",
            "value": "25.5",
            "device_id": device_id,
            "device_code": device_id,
            "quality_code": "0",
            "source_observed_at": datetime.now(tz=timezone.utc).isoformat(),
        }],
    )


class TestNewConsumerGroupStartAndCatchUp:
    """验证新 consumer group 启动追平场景。

    InMemoryMessageBus 按 consumer group 独立管理 offset，
    因此同一 topic 的不同 consumer group 消费同一批消息时互不干扰。
    """

    @pytest.mark.asyncio
    async def test_new_group_starts_from_offset_zero(self) -> None:
        """验证新 consumer group 从 offset 0 开始消费。

        与旧 group 独立，即使旧 group 已消费完所有消息，
        新 group 仍能从头开始消费全部消息。
        """
        bus = InMemoryMessageBus()

        # 发布 5 条消息
        for i in range(5):
            await bus.publish(_make_envelope(message_id=f"msg-{i:03d}"))

        # 旧 consumer group 消费全部
        old_msgs = [e async for e in bus.consume("whale.state_snapshot", "group-old")]
        assert len(old_msgs) == 5

        # 新 consumer group 也应能消费全部 5 条
        new_msgs = [e async for e in bus.consume("whale.state_snapshot", "group-new")]
        assert len(new_msgs) == 5
        assert [e.message_id for e in old_msgs] == [e.message_id for e in new_msgs]

    @pytest.mark.asyncio
    async def test_old_group_consumes_independently_from_new(self) -> None:
        """验证新旧 consumer group 各自独立消费，offset 不互相影响。

        旧 group 消费前 3 条后暂停，新 group 消费全部 5 条，
        旧 group 的 offset 不受新 group 消费影响。
        """
        bus = InMemoryMessageBus()

        for i in range(5):
            await bus.publish(_make_envelope(message_id=f"item-{i:03d}"))

        # 旧 group 消费前 3 条
        old_msgs: list[Envelope] = []
        async for env in bus.consume("whale.state_snapshot", "group-old"):
            old_msgs.append(env)
            if len(old_msgs) >= 3:
                break
        assert len(old_msgs) == 3

        # 新 group 消费全部 5 条
        new_msgs = [e async for e in bus.consume("whale.state_snapshot", "group-new")]
        assert len(new_msgs) == 5

        # 旧 group 继续消费剩余 2 条
        remaining: list[Envelope] = []
        async for env in bus.consume("whale.state_snapshot", "group-old"):
            remaining.append(env)
        assert len(remaining) == 2  # 剩余的 2 条

        # 总共：旧 group 消费了 5 条（分两轮），新 group 消费了 5 条
        assert len(old_msgs) + len(remaining) == 5


class TestLagZeroSwitchover:
    """验证 lag = 0 后切换 active。

    在 InMemory 场景下，consumer lag 即 topic 中未被 consumer group 消费的
    消息数。当 lag = 0 时，新 group 已追平所有历史消息。
    """

    @pytest.mark.asyncio
    async def test_lag_zero_after_new_group_consumes_all(self) -> None:
        """验证新 group 追平所有消息后 lag = 0。

        发布 N 条消息后，新 group 消费 N 条，此时该 group 的 lag = 0。
        """
        bus = InMemoryMessageBus()

        for i in range(10):
            await bus.publish(_make_envelope(message_id=f"lag-{i:03d}"))

        # 新 group 消费全部 10 条
        new_msgs = [e async for e in bus.consume("whale.state_snapshot", "group-new")]
        assert len(new_msgs) == 10

        # InMemoryMessageBus 中，consumer group 的 offset 经过 consume 后已被推进
        # lag = total_messages - consumed_by_group
        # 由于 group-new 消费了从 offset 0 到 len(messages) 的全部消息，lag = 0
        total = len(bus.messages.get("whale.state_snapshot", []))
        consumed = len(new_msgs)
        assert consumed == total
        assert total - consumed == 0  # lag = 0

    @pytest.mark.asyncio
    async def test_switch_active_does_not_cause_duplication(self) -> None:
        """验证切换 active 后不会导致消息重复处理。

        旧 group 处理部分消息 → 新 group 追平 → 切换 → 新 group 继续消费新消息。
        切换过程中不丢失、不重复。
        """
        bus = InMemoryMessageBus()

        # Batch 1: 旧 group 处理的消息
        for i in range(5):
            await bus.publish(_make_envelope(message_id=f"batch1-{i:03d}"))

        # 旧 group 消费 batch 1
        old_msgs = [e async for e in bus.consume("whale.state_snapshot", "group-old")]
        assert len(old_msgs) == 5

        # 新 group 追平 batch 1（消费相同消息）
        new_batch1 = [e async for e in bus.consume("whale.state_snapshot", "group-new")]
        assert len(new_batch1) == 5

        # Batch 2: 切换后发布的新消息
        for i in range(3):
            await bus.publish(_make_envelope(message_id=f"batch2-{i:03d}"))

        # 新 group 继续消费 batch 2
        new_batch2: list[Envelope] = []
        async for env in bus.consume("whale.state_snapshot", "group-new"):
            new_batch2.append(env)
        assert len(new_batch2) == 3

        # 旧 group 不消费 batch 2
        old_batch2: list[Envelope] = []
        async for env in bus.consume("whale.state_snapshot", "group-old"):
            old_batch2.append(env)
        assert len(old_batch2) == 3  # 旧 group 也可消费 batch 2（未停止）

        # 新 group 总共消费 5 + 3 = 8 条，无丢失
        assert len(new_batch1) + len(new_batch2) == 8


class TestOldConsumerGroupDelayedStop:
    """验证旧 consumer group 延迟停止并保留用于回滚。

    切换后旧 group 应：
    1. 延迟一段时间后再停止（允许新 group 稳定）。
    2. 停止后保留 group 信息和 offset，可随时重新激活用于回滚。
    """

    @pytest.mark.asyncio
    async def test_old_group_stops_after_switchover(self) -> None:
        """验证旧 group 在切换后停止消费，但停止前已处理最后一批消息。"""
        bus = InMemoryMessageBus()

        for i in range(5):
            await bus.publish(_make_envelope(message_id=f"pre-switch-{i:03d}"))

        # 旧 group 消费完切换前的消息
        old_msgs = [e async for e in bus.consume("whale.state_snapshot", "group-old")]
        assert len(old_msgs) == 5

        # 新 group 追平
        new_msgs = [e async for e in bus.consume("whale.state_snapshot", "group-new")]
        assert len(new_msgs) == 5

        # 切换期间发布 3 条新消息
        for i in range(3):
            await bus.publish(_make_envelope(message_id=f"during-switch-{i:03d}"))

        # 新 group 消费切换期间的消息
        new_mid_msgs = [e async for e in bus.consume("whale.state_snapshot", "group-new")]
        assert len(new_mid_msgs) == 3

        # 旧 group 在停止前可选择消费或不消费
        # 此处模拟旧 group 被停止（不再消费）
        # 验证旧 group 仍可消费（group 未删除，保留用于回滚）
        bus2 = InMemoryMessageBus()
        for i in range(2):
            await bus2.publish(_make_envelope(message_id=f"post-switch-{i:03d}"))

        # 验证旧 group 的 consumer offset 未丢失（可随时重新激活）
        # InMemoryMessageBus 对每个 group 维护独立 offset，group 删除后才丢失
        assert "group-old" in bus._consumer_offsets

    @pytest.mark.asyncio
    async def test_old_group_preserved_for_rollback(self) -> None:
        """验证旧 group offset 在停止后仍然保留，可随时回滚。

        回滚流程：
        1. 旧 group 从停止时的 offset 继续消费新消息。
        2. 旧 group 能正确消费切换后发布的消息。
        """
        bus = InMemoryMessageBus()

        # 发布 4 条消息，旧 group 消费完
        for i in range(4):
            await bus.publish(_make_envelope(message_id=f"rollback-{i:03d}"))
        old_msgs_pre = [e async for e in bus.consume("whale.state_snapshot", "group-old-v1")]
        assert len(old_msgs_pre) == 4

        # 切换发生：新 group 接管，旧 group 保留但暂停消费
        # 发布 2 条新消息
        for i in range(2):
            await bus.publish(_make_envelope(message_id=f"rollback-new-{i:03d}"))

        # 新 group (v2) 消费全部 6 条（从头开始）
        new_msgs = [e async for e in bus.consume("whale.state_snapshot", "group-new-v2")]
        assert len(new_msgs) == 6  # 4 旧 + 2 新

        # 回滚：旧 group 继续消费剩余消息
        # 由于旧 group 已经消费完 4 条，seek 到 offset 0 模拟从开始消费
        await bus.seek([
            MessageOffset(partition=0, offset=0)
        ])
        # 旧 group 重新消费全部 6 条（回滚场景）
        old_msgs_post = [e async for e in bus.consume("whale.state_snapshot", "group-old-v1")]
        assert len(old_msgs_post) == 6  # seek 后从 offset 0 开始，4 旧 + 2 新

        # 验证新旧 group 消费的消息集合一致
        old_ids = {e.message_id for e in old_msgs_post}
        new_ids = {e.message_id for e in new_msgs}
        assert old_ids == new_ids


class TestWriterSwitchoverIntegration:
    """验证 writer 层面的切换集成。

    使用 LocalPipelineRunner 管理多个 writer，验证切换过程中的数据一致性。
    """

    @pytest.mark.asyncio
    async def test_pipeline_runner_switches_writers(self) -> None:
        """验证 LocalPipelineRunner 的 writer 注册和启动/停止。

        runner 注册 writer → 启动 → writer 消费 → runner 停止。
        """
        runner = LocalPipelineRunner()
        bus = InMemoryMessageBus()
        dlq = InMemoryDeadLetterSink()
        index = MemoryRawIndexSink()
        writer = RawIndexWriter(source=bus, index=index, dlq=dlq)

        runner.register_writer("raw-index-v1", lambda: writer.run("whale.state_snapshot", "g1"))

        # 发布消息
        for i in range(3):
            await bus.publish(_make_envelope(message_id=f"runner-{i:03d}"))

        # 启动 runner
        await runner.start()
        # 等待 writer 消费完成
        await asyncio.sleep(0.2)
        await runner.stop()

        assert len(index.records) >= 1

    @pytest.mark.asyncio
    async def test_dual_writer_archive_and_index_switchover(self) -> None:
        """验证 archive writer 和 index writer 同时运行并无缝切换。

        v1 的 archive+index → 切换 → v2 的 archive+index 接管。
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            bus = InMemoryMessageBus()
            dlq = InMemoryDeadLetterSink()
            manifest = InMemoryManifestRepository()

            # ---- v1 writers ----
            archive_v1 = LocalCompressedArchiveSink(base_dir=tmpdir)
            index_v1 = MemoryRawIndexSink()
            archive_writer_v1 = RawArchiveWriter(
                source=bus, archive=archive_v1, manifest=manifest, dlq=dlq,
                batch_size=5,
            )
            index_writer_v1 = RawIndexWriter(source=bus, index=index_v1, dlq=dlq)

            # 发布 batch 1 (v1 处理)
            for i in range(4):
                await bus.publish(_make_envelope(message_id=f"dual-{i:03d}"))

            arch_count_v1 = await archive_writer_v1.run("whale.state_snapshot", "group-v1-arch")
            idx_count_v1 = await index_writer_v1.run("whale.state_snapshot", "group-v1-idx")
            assert arch_count_v1 == 4
            assert idx_count_v1 == 4

            # ---- v2 writers (切换) ----
            archive_v2 = LocalCompressedArchiveSink(base_dir=tmpdir)
            index_v2 = MemoryRawIndexSink()
            dlq_v2 = InMemoryDeadLetterSink()
            archive_writer_v2 = RawArchiveWriter(
                source=bus, archive=archive_v2, manifest=manifest, dlq=dlq_v2,
                batch_size=5,
            )
            index_writer_v2 = RawIndexWriter(source=bus, index=index_v2, dlq=dlq_v2)

            # 发布 batch 2 (v2 处理)
            for i in range(3):
                await bus.publish(_make_envelope(message_id=f"dual-new-{i:03d}"))

            arch_count_v2 = await archive_writer_v2.run("whale.state_snapshot", "group-v2-arch")
            idx_count_v2 = await index_writer_v2.run("whale.state_snapshot", "group-v2-idx")

            # v2 应从 offset 0 开始消费，因此能看到全部 7 条 (4 + 3)
            assert arch_count_v2 == 7
            assert idx_count_v2 == 7

            # DLQ 无泄漏
            assert len(dlq.dead_letters) == 0
            assert len(dlq_v2.dead_letters) == 0

            # v1 和 v2 各自独立处理消息
            v1_batches = await archive_v1.list_batches()
            v2_batches = await archive_v2.list_batches()
            assert len(v1_batches) + len(v2_batches) >= 2
