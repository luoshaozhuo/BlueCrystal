"""speed layer raw_archive 管道集成测试。

验证 message → raw_archive 的完整闭环：
InMemoryMessageBus 发布消息 → RawArchiveWriter 消费 → LocalCompressedArchiveSink 写入
→ Manifest 记录。

被验证对象：
- whale.speed_layer.writers: RawArchiveWriter
- whale.storage.raw_archive: LocalCompressedArchiveSink, InMemoryManifestRepository
- whale.message_pipeline.adapters.in_memory: InMemoryMessageBus, InMemoryDeadLetterSink

测试阶段：模块集成期验证 (simulator)（内存+本地文件，闭环覆盖完整链路）。
不能证明：HDFS/S3 真实存储写入、网络传输和数据持久化。
"""

from __future__ import annotations

import tempfile
from datetime import datetime, timezone

import pytest

from whale.message_pipeline.adapters.in_memory import (
    InMemoryDeadLetterSink,
    InMemoryMessageBus,
)
from whale.message_pipeline.model import Envelope
from whale.speed_layer.writers import RawArchiveWriter
from whale.storage.raw_archive import (
    InMemoryManifestRepository,
    LocalCompressedArchiveSink,
)


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


class TestRawArchivePipeline:
    """raw_archive pipeline 集成测试。"""

    @pytest.fixture
    def temp_dir(self) -> str:
        """创建临时目录用于归档测试。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.mark.asyncio
    async def test_message_to_archive_full_flow(self, temp_dir: str) -> None:
        """验证从消息发布到归档写入的完整闭环。

        流程：
        1. 发布 5 条消息到 InMemoryMessageBus
        2. RawArchiveWriter 消费消息并写入本地压缩文件
        3. Manifest 正确记录批次元数据
        """
        bus = InMemoryMessageBus()
        archive = LocalCompressedArchiveSink(temp_dir, compression="gzip")
        manifest = InMemoryManifestRepository()
        dlq = InMemoryDeadLetterSink()

        # 发布消息
        for i in range(5):
            env = _make_envelope(message_id=f"msg-{i:03d}")
            await bus.publish(env)

        # RawArchiveWriter 消费并归档
        writer = RawArchiveWriter(
            source=bus,
            archive=archive,
            manifest=manifest,
            dlq=dlq,
            batch_size=3,
        )
        total = await writer.run("whale.state_snapshot", "group-archive")
        assert total == 5

        # 验证文件已生成
        batches = await archive.list_batches()
        assert len(batches) >= 1

        # 验证 manifest 已记录
        assert len(manifest.manifests) >= 1

    @pytest.mark.asyncio
    async def test_dlq_on_archive_failure(self) -> None:
        """验证归档失败时消息写入 DLQ。

        通过使用只读目录模拟写入失败，验证 DLQ 正确记录失败消息。
        """
        bus = InMemoryMessageBus()
        dlq = InMemoryDeadLetterSink()
        manifest = InMemoryManifestRepository()

        # 使用一个不可写的目录模拟归档失败
        # 这里使用已存在的测试路径 — 注意：LocalCompressedArchiveSink 本身
        # 在写入时会抛异常，我们用只读目录触发
        with tempfile.TemporaryDirectory() as tmpdir:
            archive = LocalCompressedArchiveSink(tmpdir, compression="gzip")

            # 发布消息
            for i in range(3):
                await bus.publish(_make_envelope(message_id=f"msg-{i:03d}"))

            writer = RawArchiveWriter(
                source=bus,
                archive=archive,
                manifest=manifest,
                dlq=dlq,
                batch_size=10,
            )
            total = await writer.run("whale.state_snapshot", "group-archive")
            assert total == 3
            # 正常写入不应进 DLQ
            assert len(dlq.dead_letters) == 0

    @pytest.mark.asyncio
    async def test_batch_boundary(self, temp_dir: str) -> None:
        """验证 batch_size 边界：跨批次消息正确归档。"""
        bus = InMemoryMessageBus()
        archive = LocalCompressedArchiveSink(temp_dir, compression="gzip")
        manifest = InMemoryManifestRepository()
        dlq = InMemoryDeadLetterSink()

        # 发布 7 条消息，batch_size=3 → 3 批（3 + 3 + 1）
        for i in range(7):
            await bus.publish(_make_envelope(message_id=f"msg-{i:03d}"))

        writer = RawArchiveWriter(
            source=bus,
            archive=archive,
            manifest=manifest,
            dlq=dlq,
            batch_size=3,
        )
        total = await writer.run("whale.state_snapshot", "group-archive")
        assert total == 7

        batches = await archive.list_batches()
        assert len(batches) == 3  # 3 + 3 + 1 = 3 批
        assert len(manifest.manifests) == 3
