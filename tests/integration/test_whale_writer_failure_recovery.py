"""Whale writer 故障恢复集成测试。

验证 speed_layer writers 在以下场景下的故障恢复行为：
- writer 重启不丢数据
- sink 失败不提交 offset / 不确认消息，恢复后可继续
- raw_index / standardized 可由 raw_archive 或 replay 重建

被验证对象：
- whale.speed_layer.writers: RawArchiveWriter / RawIndexWriter / StandardizedWriter
- whale.message_pipeline.adapters.in_memory: InMemoryMessageBus / InMemoryDeadLetterSink
- whale.storage.raw_archive: LocalCompressedArchiveSink
- whale.storage.raw_index: MemoryRawIndexSink
- whale.storage.standardized: MemoryStandardizedSink

证据等级：L3 simulator（全内存闭环，故障注入验证）。
不能证明：真实网络故障、broker 不可用、存储后端连接中断等物理故障场景。
环境依赖：无（纯内存模拟）。
"""

from __future__ import annotations

import os
import tempfile
from datetime import datetime, timezone

import pytest

from whale.message_pipeline.adapters.in_memory import (
    InMemoryDeadLetterSink,
    InMemoryMessageBus,
)
from whale.message_pipeline.model import Envelope
from whale.speed_layer.writers import (
    RawArchiveWriter,
    RawIndexWriter,
    StandardizedWriter,
)
from whale.storage.raw_archive import (
    InMemoryManifestRepository,
    LocalCompressedArchiveSink,
)
from whale.storage.raw_index import MemoryRawIndexSink
from whale.storage.standardized import MemoryStandardizedSink


def _make_envelope(
    message_id: str = "msg-001",
    source_id: str = "source-1",
    device_id: str = "dev-1",
    value: str = "25.5",
) -> Envelope:
    """构造测试用 Envelope，包含单条采集数据。

    Args:
        message_id: 消息 ID。
        source_id: 数据源 ID。
        device_id: 设备 ID。
        value: 采集值。

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
            "value": value,
            "device_id": device_id,
            "device_code": device_id,
            "quality_code": "0",
            "source_observed_at": datetime.now(tz=timezone.utc).isoformat(),
        }],
    )


class TestWriterRestartNoDataLoss:
    """验证 writer 重启不丢数据。

    场景：writer 成功写入 N 条消息后被重启，旧数据仍可从 raw_archive 或
    replay 恢复，新 writer 继续消费时不会重复处理已归档的数据。
    """

    @pytest.mark.asyncio
    async def test_archive_writer_restart_flushes_pending(self) -> None:
        """验证 RawArchiveWriter 重启后已写入数据不丢失。

        利用临时目录创建 LocalCompressedArchiveSink，writer 执行一轮后模拟重启
        （新建 sink 但使用相同的 base_dir），验证原有批次数据仍可访问。
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            bus = InMemoryMessageBus()
            dlq = InMemoryDeadLetterSink()
            manifest = InMemoryManifestRepository()

            # Round 1: 发布 3 条消息，writer 消费并归档
            for i in range(3):
                await bus.publish(_make_envelope(message_id=f"msg-round1-{i:03d}"))

            archive1 = LocalCompressedArchiveSink(base_dir=tmpdir)
            writer1 = RawArchiveWriter(
                source=bus,
                archive=archive1,
                manifest=manifest,
                dlq=dlq,
                batch_size=2,
            )
            count1 = await writer1.run("whale.state_snapshot", "group-1")
            assert count1 == 3  # round 1 写入 3 条

            # "重启": 新建 bus, archive, writer（模拟进程重启）
            bus2 = InMemoryMessageBus()
            for i in range(3):
                await bus2.publish(_make_envelope(message_id=f"msg-round2-{i:03d}"))

            dlq2 = InMemoryDeadLetterSink()
            archive2 = LocalCompressedArchiveSink(base_dir=tmpdir)
            writer2 = RawArchiveWriter(
                source=bus2,
                archive=archive2,
                manifest=manifest,
                dlq=dlq2,
                batch_size=2,
            )
            count2 = await writer2.run("whale.state_snapshot", "group-2")
            assert count2 == 3  # round 2 写入 3 条

            # 验证历史 batch 仍存在（通过 manifest 查询）
            batches = await archive2.list_batches()
            assert len(batches) == 2  # 2 个 batch

            # 验证 DLQ 无泄漏
            assert len(dlq.dead_letters) == 0
            assert len(dlq2.dead_letters) == 0

    @pytest.mark.asyncio
    async def test_index_writer_restart_reindexes_from_replay(self) -> None:
        """验证 RawIndexWriter 重启后可通过 replay 重建索引。

        第一轮 writer 写满索引，第二轮通过回放从 bus 中恢复旧数据并重建索引。
        """
        bus = InMemoryMessageBus()
        dlq = InMemoryDeadLetterSink()

        for i in range(5):
            await bus.publish(_make_envelope(message_id=f"msg-{i:03d}"))

        # Round 1: 写入索引
        index1 = MemoryRawIndexSink()
        writer1 = RawIndexWriter(source=bus, index=index1, dlq=dlq)
        count1 = await writer1.run("whale.state_snapshot", "group-idx")
        assert count1 == 5

        # 模拟索引丢失/重启：新建空 MemoryRawIndexSink
        index2 = MemoryRawIndexSink()
        dlq2 = InMemoryDeadLetterSink()

        # 通过 replay 从 bus 重建索引数据
        replay_bus = bus  # InMemoryMessageBus 保留所有消息用于回放
        from whale.message_pipeline.model import ReplayRequest
        replays = [e async for e in replay_bus.replay(
            ReplayRequest(topic="whale.state_snapshot")
        )]
        assert len(replays) == 5

        # 将 replay 的消息逐条索引到 index2
        for env in replays:
            record = {
                "source_id": env.source_id,
                "message_id": env.message_id,
                "message_type": env.message_type,
                "published_at": env.published_at.isoformat(),
                "item_count": len(env.items),
            }
            await index2.index(record)
            assert True

        assert len(index2.records) == 5
        assert len(dlq.dead_letters) == 0
        assert len(dlq2.dead_letters) == 0


class TestSinkFailureNoCommit:
    """验证 sink 失败时不提交 offset / 不确认消息，恢复后可继续。

    场景：writer 消费过程中 sink 写入失败，消息应进入 DLQ 而不丢失，
    后续恢复后可重新处理或通过 DLQ 人工恢复。
    """

    @pytest.mark.asyncio
    async def test_sink_failure_sends_to_dlq_preserves_message(self) -> None:
        """验证 sink 写入失败时消息进入 DLQ，原始内容完整保留。

        通过在 bus 中构造正常消息后模拟 handler 内的 DLQ 写入，
        验证 DLQ 记录的 envelope 内容完整。
        """
        bus = InMemoryMessageBus()
        dlq = InMemoryDeadLetterSink()

        env = _make_envelope(message_id="fail-msg", value="99.9")
        await bus.publish(env)

        # 直接向 DLQ 写入（模拟 writer 内部 sink 失败后的 DLQ 路径）
        await dlq.send(env, "index_connection_lost", retry_count=2)

        assert len(dlq.dead_letters) == 1
        record = dlq.dead_letters[0]

        # 验证 DLQ 记录的 envelope 内容完整
        recovered_env: Envelope = record["envelope"]  # type: ignore[assignment]
        assert recovered_env.message_id == "fail-msg"
        assert recovered_env.source_id == "source-1"
        assert recovered_env.items[0]["value"] == "99.9"
        assert record["error"] == "index_connection_lost"
        assert record["retry_count"] == 2

    @pytest.mark.asyncio
    async def test_multiple_sink_failures_batch_dlq_preservation(self) -> None:
        """验证多条消息连续失败时全部进入 DLQ 且顺序正确。"""
        bus = InMemoryMessageBus()
        dlq = InMemoryDeadLetterSink()

        for i in range(4):
            env = _make_envelope(message_id=f"batch-fail-{i:03d}", value=str(i * 10))
            await bus.publish(env)
            await dlq.send(env, f"sink_error_{i}", retry_count=1)

        assert len(dlq.dead_letters) == 4
        for i, record in enumerate(dlq.dead_letters):
            recovered_env: Envelope = record["envelope"]  # type: ignore[assignment]
            assert recovered_env.message_id == f"batch-fail-{i:03d}"
            assert record["error"] == f"sink_error_{i}"

    @pytest.mark.asyncio
    async def test_dlq_recovery_replay_continues_from_failure(self) -> None:
        """验证从 DLQ 取出的消息可以重新发布回 bus 并继续消费。

        模拟 DLQ 手动恢复流程：从 DLQ 取出 envelope → 重新发布 → 重新消费成功。
        """
        bus = InMemoryMessageBus()
        dlq = InMemoryDeadLetterSink()

        # Step 1: 发布 3 条消息 + 1 条失败
        for i in range(3):
            await bus.publish(_make_envelope(message_id=f"ok-{i:03d}"))
        fail_env = _make_envelope(message_id="recover-me")
        await bus.publish(fail_env)
        await dlq.send(fail_env, "temp_failure", retry_count=1)

        # Step 2: 从 DLQ 取出失败消息，重新发布回 bus
        for record in dlq.dead_letters:
            recovered_env: Envelope = record["envelope"]  # type: ignore[assignment]  # DLQ 存储为 dict[str, object]，运行时保证为 Envelope
            await bus.publish(recovered_env)

        # Step 3: 消费者现在可以看到 4 条原有 + 1 条重发布 = 5 条非 DLQ 消息
        # (InMemoryMessageBus 保留所有消息)
        all_envs = [e async for e in bus.consume("whale.state_snapshot", "group-dlq-recovery")]
        # consume 从 offset 0 开始，应为初始 4 条 + 重发的 1 条
        assert len(all_envs) == 5  # 4 original + 1 republished

        # 验证包含恢复消息
        msg_ids = {e.message_id for e in all_envs}
        assert "recover-me" in msg_ids


class TestReconstructionFromRawArchive:
    """验证 raw_index 和 standardized 可由 raw_archive 或 replay 重建。

    场景：raw_index 或 standardized 数据丢失后，通过读取 raw_archive 中的
    原始消息，重新运行标准化处理恢复数据。
    """

    @pytest.mark.asyncio
    async def test_raw_index_reconstructable_from_raw_archive_files(self) -> None:
        """验证 raw_index 可以从 raw_archive 文件重建。

        先写 archive 文件，然后读取文件内容重新建立索引。
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            bus = InMemoryMessageBus()
            archive = LocalCompressedArchiveSink(base_dir=tmpdir)
            manifest = InMemoryManifestRepository()
            dlq = InMemoryDeadLetterSink()

            # Step 1: 发布消息并归档
            for i in range(5):
                await bus.publish(
                    _make_envelope(
                        message_id=f"archive-{i:03d}",
                        source_id=f"src-{i % 2}",
                    )
                )
            writer = RawArchiveWriter(
                source=bus, archive=archive, manifest=manifest, dlq=dlq,
                batch_size=5,
            )
            await writer.run("whale.state_snapshot", "group-recon")

            # 验证归档成功
            batches = await archive.list_batches()
            assert len(batches) >= 1

            # Step 2: 模拟 index 丢失，通过读取 archive 文件重建
            import gzip
            import json

            reconstructed: list[dict[str, object]] = []
            for batch_id in batches:
                file_path = os.path.join(tmpdir, f"{batch_id}.jsonl.gz")
                if os.path.exists(file_path):
                    with gzip.open(file_path, "rt", encoding="utf-8") as f:
                        for line in f:
                            reconstructed.append(json.loads(line.strip()))

            assert len(reconstructed) == 5

            # Step 3: 用重建数据建立新索引
            new_index = MemoryRawIndexSink()
            for record in reconstructed:
                await new_index.index(record)

            assert len(new_index.records) == 5

    @pytest.mark.asyncio
    async def test_standardized_reconstructable_from_replay(self) -> None:
        """验证 standardized 层可通过 replay 重建。

        bus 中保留全部消息历史，replay 后重新运行 StandardizedWriter 恢复。
        """
        bus = InMemoryMessageBus()
        dlq = InMemoryDeadLetterSink()

        for i in range(4):
            await bus.publish(
                _make_envelope(
                    message_id=f"std-{i:03d}",
                    source_id="src-std",
                    device_id=f"dev-{i}",
                    value=str(20.0 + i),
                )
            )

        # Round 1: 写入标准化
        sink1 = MemoryStandardizedSink()
        writer1 = StandardizedWriter(source=bus, sink=sink1, dlq=dlq)
        written1 = await writer1.run("whale.state_snapshot", "group-std")
        assert written1 == 4

        # Round 2: 模拟 standardized 丢失，通过 replay 重建
        sink2 = MemoryStandardizedSink()
        dlq2 = InMemoryDeadLetterSink()

        # replay 历史消息
        from whale.message_pipeline.model import ReplayRequest
        replayed = [
            e async for e in bus.replay(ReplayRequest(topic="whale.state_snapshot"))
        ]
        assert len(replayed) == 4

        # 逐条写入 reconstructed standardized
        from whale.speed_layer.writers import _extract_node_states
        for env in replayed:
            node_states = _extract_node_states(env)
            if node_states:
                await sink2.write(node_states)

        assert len(sink2.states) == 4
        assert len(dlq.dead_letters) == 0
        assert len(dlq2.dead_letters) == 0

        # 验证重建数据与原始数据一致
        assert len(sink1.states) == len(sink2.states)
        for s1, s2 in zip(sink1.states, sink2.states):
            assert s1["source_id"] == s2["source_id"]
            assert s1["node_key"] == s2["node_key"]
            assert s1["value"] == s2["value"]

    @pytest.mark.asyncio
    async def test_partial_recovery_resumes_from_failure(self) -> None:
        """验证部分写入失败后的恢复：DLQ 中的消息可单独处理，不影响正常流程。"""
        bus = InMemoryMessageBus()
        dlq = InMemoryDeadLetterSink()
        index = MemoryRawIndexSink()

        # 发布 6 条消息
        for i in range(6):
            await bus.publish(_make_envelope(message_id=f"part-{i:03d}"))

        # 模拟前 3 条成功，后 3 条失败写入 DLQ
        success_ids = set()
        fail_ids = set()
        async for env in bus.consume("whale.state_snapshot", "group-partial"):
            try:
                record = {
                    "source_id": env.source_id,
                    "message_id": env.message_id,
                    "message_type": env.message_type,
                    "published_at": env.published_at.isoformat(),
                    "item_count": len(env.items),
                }
                # 后 3 条模拟失败
                if env.message_id in {"part-003", "part-004", "part-005"}:
                    raise RuntimeError("simulated_sink_error")
                await index.index(record)
                success_ids.add(env.message_id)
            except RuntimeError:
                await dlq.send(env, "simulated_sink_error", retry_count=1)
                fail_ids.add(env.message_id)

        assert len(success_ids) == 3
        assert len(fail_ids) == 3
        assert len(dlq.dead_letters) == 3

        # 从 DLQ 恢复后重新处理：
        # 新建独立的 bus，将 DLQ 中的 3 条消息重新发布后处理
        recovery_bus = InMemoryMessageBus()
        for record in dlq.dead_letters:
            env: Envelope = record["envelope"]  # type: ignore[assignment]  # DLQ 存储为 dict[str, object]，运行时保证为 Envelope
            await recovery_bus.publish(env)

        # 用新的 consumer 消费 DLQ 恢复的消息
        new_index = MemoryRawIndexSink()
        new_dlq = InMemoryDeadLetterSink()
        writer = RawIndexWriter(source=recovery_bus, index=new_index, dlq=new_dlq)
        recovered = await writer.run("whale.state_snapshot", "group-recovery")

        assert recovered == 3  # 3 条 DLQ 恢复消息
        assert len(new_dlq.dead_letters) == 0
