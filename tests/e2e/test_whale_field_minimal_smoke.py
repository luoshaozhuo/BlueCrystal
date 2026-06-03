"""Whale 现场最小链路 E2E smoke 测试。

验证 ingest → message_pipeline → speed_layer → storage 的全链路最小部署
在 InMemory 模式下的端到端行为：
- 启动本地 pipeline runner
- 注入测试消息到 InMemory bus
- 验证 raw_archive 本地文件写入
- 验证 raw_index / standardized memory sink
- 验证 DLQ 收集失败消息
- 验证 metrics collector 输出 checkpoint/lag

被验证对象：
- whale.message_pipeline: InMemoryMessageBus, InMemoryDeadLetterSink
- whale.speed_layer: LocalPipelineRunner, RawArchiveWriter, RawIndexWriter,
  StandardizedWriter, ServingCacheUpdater
- whale.speed_layer.metrics: InMemoryMetricsCollector
- whale.storage: LocalCompressedArchiveSink, MemoryRawIndexSink,
  MemoryStandardizedSink, InMemoryServingCache, InMemoryManifestRepository

证据等级：L3 simulator（全内存闭环，完整 E2E 流程覆盖）。
不能证明：真实 Kafka/Pulsar broker、TDengine、HDFS/S3、Flink 的真实环境行为。
环境依赖：无（纯内存模拟，不需要 docker compose）。
"""

from __future__ import annotations

import asyncio
import os
import tempfile
from datetime import datetime, timezone

import pytest

from whale.message_pipeline.adapters.in_memory import (
    InMemoryDeadLetterSink,
    InMemoryMessageBus,
)
from whale.message_pipeline.model import Envelope
from whale.speed_layer.metrics import InMemoryMetricsCollector
from whale.speed_layer.runner import LocalPipelineRunner
from whale.speed_layer.writers import (
    RawArchiveWriter,
    RawIndexWriter,
    StandardizedWriter,
    ServingCacheUpdater,
)
from whale.storage.raw_archive import (
    InMemoryManifestRepository,
    LocalCompressedArchiveSink,
)
from whale.storage.raw_index import MemoryRawIndexSink
from whale.storage.serving_cache import InMemoryServingCache
from whale.storage.standardized import MemoryStandardizedSink


def _make_envelope(
    message_id: str = "msg-001",
    source_id: str = "source-1",
    device_id: str = "dev-1",
    variable_key: str = "temp",
    value: str = "25.5",
    quality_code: str = "0",
) -> Envelope:
    """构造测试用 Envelope，模拟 ingest 发布的单条采集消息。

    Args:
        message_id: 消息 ID。
        source_id: 数据源 ID。
        device_id: 设备 ID。
        variable_key: 变量名。
        value: 采集值。
        quality_code: 质量码。

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
            "variable_key": variable_key,
            "value": value,
            "device_id": device_id,
            "device_code": device_id,
            "quality_code": quality_code,
            "source_observed_at": datetime.now(tz=timezone.utc).isoformat(),
        }],
    )


class TestFieldMinimalSmokePipeline:
    """Whale 现场最小链路 E2E smoke 测试。

    覆盖从消息注入到各存储层写入的完整闭环。
    """

    @pytest.mark.asyncio
    async def test_full_pipeline_inject_to_raw_archive(self) -> None:
        """验证消息注入 → raw_archive 本地文件写入的完整流程。

        流程：
        1. 构造 InMemoryMessageBus 并注入 5 条测试消息。
        2. RawArchiveWriter 消费并写入本地压缩文件。
        3. 验证文件生成、manifest 记录和 DLQ 为空。
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # 初始化 pipeline 组件
            bus = InMemoryMessageBus()
            archive = LocalCompressedArchiveSink(base_dir=tmpdir)
            manifest = InMemoryManifestRepository()
            dlq = InMemoryDeadLetterSink()

            # 注入测试消息（模拟 ingest 发布）
            test_messages = [
                _make_envelope(
                    message_id=f"field-{i:03d}",
                    source_id=f"src-{i % 3}",
                    device_id=f"dev-{i % 2}",
                    variable_key="temp" if i % 2 == 0 else "press",
                    value=str(20.0 + i * 1.5),
                )
                for i in range(5)
            ]
            for msg in test_messages:
                await bus.publish(msg)

            # archive writer 消费并归档
            writer = RawArchiveWriter(
                source=bus,
                archive=archive,
                manifest=manifest,
                dlq=dlq,
                batch_size=3,
            )
            written = await writer.run("whale.state_snapshot", "group-field-archive")
            assert written == 5

            # 验证 batch 已提交
            batches = await archive.list_batches()
            assert len(batches) >= 1

            # 验证 manifest 已记录
            assert len(manifest.manifests) >= 1
            for _, m in manifest.manifests.items():
                assert m["status"] == "committed"
                assert m["message_count"] > 0

            # 验证 DLQ 无泄漏
            assert len(dlq.dead_letters) == 0

            # 验证压缩文件存在且可读
            import gzip
            import json
            found_count = 0
            for batch_id in batches:
                file_path = os.path.join(tmpdir, f"{batch_id}.jsonl.gz")
                if os.path.exists(file_path):
                    with gzip.open(file_path, "rt", encoding="utf-8") as f:
                        for line in f:
                            record = json.loads(line.strip())
                            assert "message_id" in record
                            assert "source_id" in record
                            found_count += 1
            assert found_count == 5

    @pytest.mark.asyncio
    async def test_full_pipeline_inject_to_raw_index_and_standardized(self) -> None:
        """验证消息注入 → raw_index → standardized 的完整流程。

        流程：
        1. 注入 4 条消息到 InMemory bus。
        2. RawIndexWriter 消费并索引。
        3. StandardizedWriter 消费并写入标准化层。
        4. 验证两者数据一致性和 DLQ 为空。
        """
        bus = InMemoryMessageBus()
        dlq = InMemoryDeadLetterSink()

        # 组件初始化
        index = MemoryRawIndexSink()
        standardized = MemoryStandardizedSink()

        # 注入测试消息
        for i in range(4):
            await bus.publish(
                _make_envelope(
                    message_id=f"idx-std-{i:03d}",
                    source_id="src-field",
                    device_id=f"dev-{i % 2}",
                    variable_key="current" if i % 2 == 0 else "voltage",
                    value=str(100.0 + i * 10),
                    quality_code="0" if i < 3 else "1",  # 最后一条质量异常
                )
            )

        # raw_index writer 消费
        idx_writer = RawIndexWriter(source=bus, index=index, dlq=dlq)
        indexed_count = await idx_writer.run("whale.state_snapshot", "group-field-idx")
        assert indexed_count == 4
        assert len(index.records) == 4

        # 重新注入相同消息用于 standardized writer（需要新一轮消费）
        bus2 = InMemoryMessageBus()
        dlq2 = InMemoryDeadLetterSink()
        for i in range(4):
            await bus2.publish(
                _make_envelope(
                    message_id=f"idx-std-{i:03d}",
                    source_id="src-field",
                    device_id=f"dev-{i % 2}",
                    variable_key="current" if i % 2 == 0 else "voltage",
                    value=str(100.0 + i * 10),
                    quality_code="0" if i < 3 else "1",
                )
            )

        # standardized writer 消费
        std_writer = StandardizedWriter(source=bus2, sink=standardized, dlq=dlq2)
        std_count = await std_writer.run("whale.state_snapshot", "group-field-std")
        assert std_count == 4
        assert len(standardized.states) == 4

        # 验证 DLQ 无泄漏
        assert len(dlq.dead_letters) == 0
        assert len(dlq2.dead_letters) == 0

        # 验证 raw_index 和 standardized 数据一致
        assert len(index.records) == len(standardized.states)

    @pytest.mark.asyncio
    async def test_dlq_collects_failed_messages(self) -> None:
        """验证 DLQ 收集失败消息。

        流程：
        1. 注入 3 条正常 + 2 条模拟失败消息。
        2. 正常消息被消耗，失败消息进入 DLQ。
        3. 验证 DLQ 包含完整的 envelope 和错误上下文。
        """
        bus = InMemoryMessageBus()
        dlq = InMemoryDeadLetterSink()

        # 注入 5 条消息
        for i in range(5):
            await bus.publish(_make_envelope(message_id=f"dlq-test-{i:03d}"))

        # 消费：前 3 条成功，后 2 条模拟失败写入 DLQ
        consumed = 0
        async for env in bus.consume("whale.state_snapshot", "group-dlq-field"):
            consumed += 1
            if consumed > 3:
                # 后 2 条模拟处理失败
                await dlq.send(env, "simulated_processing_error", retry_count=2)

        assert consumed == 5
        assert len(dlq.dead_letters) == 2

        # 验证 DLQ 记录完整性
        for record in dlq.dead_letters:
            recovered_env: Envelope = record["envelope"]  # type: ignore[assignment]
            assert recovered_env.message_id.startswith("dlq-test-")
            assert record["error"] == "simulated_processing_error"
            assert record["retry_count"] == 2
            assert recovered_env.source_id == "source-1"

    @pytest.mark.asyncio
    async def test_metrics_collector_checkpoint_and_lag(self) -> None:
        """验证 metrics collector 输出 checkpoint 和 lag 指标。

        流程：
        1. 初始化 InMemoryMetricsCollector。
        2. 记录 checkpoint position 和 consumer lag。
        3. 记录 sink success/failure 和 latency。
        4. 验证 dump() 输出包含所有预期指标。
        """
        metrics = InMemoryMetricsCollector()

        # 记录 checkpoint
        await metrics.record_checkpoint("raw-archive", "whale.state_snapshot", 0, 42)
        await metrics.record_checkpoint("raw-index", "whale.state_snapshot", 0, 42)
        await metrics.record_checkpoint("standardized", "whale.state_snapshot", 0, 42)

        # 记录 lag
        await metrics.record_lag("raw-archive", "whale.state_snapshot", 0, 5)
        await metrics.record_lag("raw-index", "whale.state_snapshot", 0, 3)
        await metrics.record_lag("standardized", "whale.state_snapshot", 0, 0)

        # 记录 latency
        await metrics.record_latency("raw-archive", 12.5)
        await metrics.record_latency("raw-archive", 8.3)
        await metrics.record_latency("raw-index", 5.1)

        # 记录 sink 成功
        await metrics.record_sink_success("raw-archive")
        await metrics.record_sink_success("raw-archive")
        await metrics.record_sink_success("raw-index")

        # 记录 sink 失败
        await metrics.record_sink_failure("raw-archive", "disk_full")

        # 验证指标导出
        dump = metrics.dump()

        # checkpoint
        assert "checkpoints" in dump
        assert dump["checkpoints"]["raw-archive"]["whale.state_snapshot"][0] == 42
        assert dump["checkpoints"]["standardized"]["whale.state_snapshot"][0] == 42

        # lag
        assert "lags" in dump
        assert dump["lags"]["raw-archive"]["whale.state_snapshot"][0] == 5
        assert dump["lags"]["standardized"]["whale.state_snapshot"][0] == 0

        # latency
        assert "latencies" in dump
        assert len(dump["latencies"].get("raw-archive", [])) == 2

        # sink counts
        assert metrics.get_success_count("raw-archive") == 2
        assert metrics.get_failure_count("raw-archive") == 1
        assert metrics.get_success_count("raw-index") == 1

        # average latency
        avg_lat = metrics.get_avg_latency("raw-archive")
        assert abs(avg_lat - 10.4) < 0.01  # (12.5 + 8.3) / 2

        # snapshot timestamp
        assert "snapshot_at" in dump

    @pytest.mark.asyncio
    async def test_serving_cache_update_pipeline(self) -> None:
        """验证 serving cache 更新管道的完整流程。

        流程：
        1. 注入 3 条消息。
        2. ServingCacheUpdater 消费并更新 InMemoryServingCache。
        3. 验证缓存键正确、值完整、TTL 生效。
        """
        bus = InMemoryMessageBus()
        dlq = InMemoryDeadLetterSink()
        cache = InMemoryServingCache(default_ttl_seconds=300)

        # 注入测试消息（不同 source/device）
        for i in range(3):
            await bus.publish(
                _make_envelope(
                    message_id=f"cache-{i:03d}",
                    source_id=f"src-cache-{i % 2}",
                    device_id=f"dev-cache-{i}",
                    variable_key="power",
                    value=str(500.0 + i * 100),
                )
            )

        updater = ServingCacheUpdater(source=bus, cache=cache, dlq=dlq, default_ttl=60)
        updated = await updater.run("whale.state_snapshot", "group-cache-field")
        assert updated == 3

        # 验证缓存条目
        assert cache.size() == 3

        # 按 key 查询
        for i in range(3):
            src_id = f"src-cache-{i % 2}"
            dev_id = f"dev-cache-{i}"
            cache_key = f"{src_id}:{dev_id}:power"
            cached = await cache.get(cache_key)
            assert cached is not None
            assert cached["source_id"] == src_id
            assert cached["variable_key"] == "power"
            assert cached["value"] == str(500.0 + i * 100)

        # 验证 DLQ 无泄漏
        assert len(dlq.dead_letters) == 0

    @pytest.mark.asyncio
    async def test_pipeline_runner_lifecycle(self) -> None:
        """验证 LocalPipelineRunner 的生命周期：注册 → 启动 → 运行 → 停止。

        注册多个 writer，启动 runner 并注入消息，验证所有 writer 正常运行后停止。
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            bus = InMemoryMessageBus()
            dlq = InMemoryDeadLetterSink()
            manifest = InMemoryManifestRepository()
            archive = LocalCompressedArchiveSink(base_dir=tmpdir)
            index = MemoryRawIndexSink()
            standardized = MemoryStandardizedSink()
            cache = InMemoryServingCache(default_ttl_seconds=300)

            # 注入 8 条消息
            for i in range(8):
                await bus.publish(
                    _make_envelope(
                        message_id=f"runner-{i:03d}",
                        source_id="src-runner",
                        device_id=f"dev-{i % 4}",
                        variable_key="freq",
                        value=str(50.0 + i * 0.1),
                    )
                )

            # 创建 writers
            archive_writer = RawArchiveWriter(
                source=bus, archive=archive, manifest=manifest, dlq=dlq,
                batch_size=4,
            )
            index_writer = RawIndexWriter(source=bus, index=index, dlq=dlq)
            std_writer = StandardizedWriter(source=bus, sink=standardized, dlq=dlq)
            cache_writer = ServingCacheUpdater(
                source=bus, cache=cache, dlq=dlq, default_ttl=60,
            )

            # 注册到 runner（使用 async wrapper 忽略返回值以匹配 register_writer 签名）
            runner = LocalPipelineRunner()

            async def _run_archive() -> None:
                """运行 archive writer 一轮，忽略返回值。"""
                await archive_writer.run("whale.state_snapshot", "g-runner")

            async def _run_index() -> None:
                """运行 index writer 一轮，忽略返回值。"""
                await index_writer.run("whale.state_snapshot", "g-runner")

            async def _run_std() -> None:
                """运行 standardized writer 一轮，忽略返回值。"""
                await std_writer.run("whale.state_snapshot", "g-runner")

            async def _run_cache() -> None:
                """运行 cache updater 一轮，忽略返回值。"""
                await cache_writer.run("whale.state_snapshot", "g-runner")

            runner.register_writer("raw-archive", _run_archive)
            runner.register_writer("raw-index", _run_index)
            runner.register_writer("standardized", _run_std)
            runner.register_writer("serving-cache", _run_cache)

            assert runner.writer_count == 4

            # 启动 runner
            await runner.start()

            # 等待 writer 消费完成
            await asyncio.sleep(0.3)

            # 检查健康状态
            health = await runner.health()
            assert any(health.values())  # 至少有一个 writer 健康

            # 停止 runner
            await runner.stop()

            # 验证所有 writer 正常工作
            batches = await archive.list_batches()
            assert len(batches) >= 1
            assert len(index.records) > 0
            assert len(standardized.states) > 0
            assert cache.size() > 0
            assert len(dlq.dead_letters) == 0

    @pytest.mark.asyncio
    async def test_end_to_end_from_ingest_simulated_injection(self) -> None:
        """验证从 simulate ingest 注入到全部存储层写出的完整闭环。

        模拟 ingest 发布 10 条不同 source/device/variable 的消息，
        消费者全部处理完成后归档、索引、标准化、缓存各层数据一致。
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            bus = InMemoryMessageBus()
            dlq = InMemoryDeadLetterSink()
            manifest = InMemoryManifestRepository()
            archive = LocalCompressedArchiveSink(base_dir=tmpdir)
            index = MemoryRawIndexSink()
            standardized = MemoryStandardizedSink()
            cache = InMemoryServingCache(default_ttl_seconds=3600)

            # 模拟 ingest 发布 10 条消息
            sources = ["plant-a", "plant-b", "plant-c"]
            variables = ["temp", "press", "flow", "level"]
            for i in range(10):
                await bus.publish(
                    _make_envelope(
                        message_id=f"e2e-{i:03d}",
                        source_id=sources[i % 3],
                        device_id=f"dev-e2e-{i % 4}",
                        variable_key=variables[i % 4],
                        value=str(25.0 + i * 3.0),
                        quality_code="0" if i < 9 else "3",
                    )
                )

            # archive writer
            arch_writer = RawArchiveWriter(
                source=bus, archive=archive, manifest=manifest, dlq=dlq,
                batch_size=5,
            )
            arch_count = await arch_writer.run("whale.state_snapshot", "g-e2e")
            assert arch_count == 10

            # 重新注入用于 index/standardized/cache (不同 consumer 需要新 bus)
            bus2 = InMemoryMessageBus()
            dlq2 = InMemoryDeadLetterSink()
            for i in range(10):
                await bus2.publish(
                    _make_envelope(
                        message_id=f"e2e-{i:03d}",
                        source_id=sources[i % 3],
                        device_id=f"dev-e2e-{i % 4}",
                        variable_key=variables[i % 4],
                        value=str(25.0 + i * 3.0),
                        quality_code="0" if i < 9 else "3",
                    )
                )

            idx_writer = RawIndexWriter(source=bus2, index=index, dlq=dlq2)
            idx_count = await idx_writer.run("whale.state_snapshot", "g-e2e-idx")
            assert idx_count == 10

            bus3 = InMemoryMessageBus()
            dlq3 = InMemoryDeadLetterSink()
            for i in range(10):
                await bus3.publish(
                    _make_envelope(
                        message_id=f"e2e-{i:03d}",
                        source_id=sources[i % 3],
                        device_id=f"dev-e2e-{i % 4}",
                        variable_key=variables[i % 4],
                        value=str(25.0 + i * 3.0),
                        quality_code="0" if i < 9 else "3",
                    )
                )

            std_writer = StandardizedWriter(source=bus3, sink=standardized, dlq=dlq3)
            std_count = await std_writer.run("whale.state_snapshot", "g-e2e-std")
            assert std_count == 10

            bus4 = InMemoryMessageBus()
            dlq4 = InMemoryDeadLetterSink()
            for i in range(10):
                await bus4.publish(
                    _make_envelope(
                        message_id=f"e2e-{i:03d}",
                        source_id=sources[i % 3],
                        device_id=f"dev-e2e-{i % 4}",
                        variable_key=variables[i % 4],
                        value=str(25.0 + i * 3.0),
                        quality_code="0" if i < 9 else "3",
                    )
                )

            cache_writer = ServingCacheUpdater(source=bus4, cache=cache, dlq=dlq4, default_ttl=60)
            cache_count = await cache_writer.run("whale.state_snapshot", "g-e2e-cache")
            assert cache_count == 10

            # 跨层一致性验证
            e2e_batches = await archive.list_batches()
            assert len(e2e_batches) >= 1
            assert len(index.records) == 10
            assert len(standardized.states) == 10
            assert cache.size() == 10  # 10 条消息，每条 1 item，10 个唯一 key

            # 验证 raw_index 和 standardized 的内容一致
            idx_src_ids = {r["source_id"] for r in index.records}
            std_src_ids = {s["source_id"] for s in standardized.states}
            assert idx_src_ids == std_src_ids

            # DLQ 全部为空
            assert len(dlq.dead_letters) == 0
            assert len(dlq2.dead_letters) == 0
            assert len(dlq3.dead_letters) == 0
            assert len(dlq4.dead_letters) == 0

            # manifest 记录完整
            total_msg_count = sum(
                m["message_count"] for m in manifest.manifests.values()
            )
            assert total_msg_count == 10
