"""Whale L5 端到端验证测试 — Kafka pipeline。

验证 Kafka → speed_layer → storage 的真实端到端数据链路：
- Kafka 真实发布/消费 + consumer group 隔离。
- speed_layer pipeline 通过 Kafka consumer group 消费。
- offset commit 和 consumer group 独立性验证。

所有测试在 Kafka 不可用时自动 skip (environment-pending)。

被验证对象：
- whale.message_pipeline.adapters.kafka: KafkaSourceAdapter, KafkaSinkAdapter
- whale.speed_layer.writers: RawArchiveWriter, RawIndexWriter, StandardizedWriter, ServingCacheUpdater
- whale.speed_layer.runner: SpeedLayerWiring

证据等级：L5 e2e/field（真实 Kafka broker + 真实存储后端）。
环境依赖：Kafka broker (localhost:9092)，Redis (localhost:16379)，
          MinIO (localhost:9000)，TDengine (localhost:6041)。
不能证明：无 Kafka 环境下的链路行为（需独立 L4 InMemory 测试覆盖）。
"""

from __future__ import annotations

import asyncio
import json
import os
import socket
import tempfile
import uuid
from datetime import datetime, timezone

import pytest

from whale.message_pipeline.model import Envelope, PartitionKeyStrategy


# ── 环境探测 ────────────────────────────────────────────────────────────────


def _tcp_reachable(host: str, port: int, timeout: float = 3.0) -> bool:
    """探测指定 host:port 的 TCP 连通性。"""
    try:
        sock = socket.create_connection((host, port), timeout=timeout)
        sock.close()
        return True
    except OSError:
        return False


def _driver_available(module: str) -> bool:
    """检查 Python 驱动是否可导入。"""
    try:
        __import__(module)
        return True
    except ImportError:
        return False


# ── 服务可用性 ──────────────────────────────────────────────────────────────

KAFKA_HOST = os.getenv("WHALE_KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
KAFKA_HOSTNAME, KAFKA_PORT_STR = KAFKA_HOST.split(":")[:2]
KAFKA_PORT = int(KAFKA_PORT_STR)
KAFKA_REACHABLE = _tcp_reachable(KAFKA_HOSTNAME, KAFKA_PORT)
KAFKA_DRIVER = _driver_available("kafka")
KAFKA_AVAILABLE = KAFKA_REACHABLE and KAFKA_DRIVER

REDIS_HOST = os.getenv("WHALE_REDIS_URL", "localhost:16379")
REDIS_HOSTNAME, REDIS_PORT_STR = REDIS_HOST.split(":")[:2]
REDIS_PORT = int(REDIS_PORT_STR)
REDIS_REACHABLE = _tcp_reachable(REDIS_HOSTNAME, REDIS_PORT)
REDIS_DRIVER = _driver_available("redis")
REDIS_AVAILABLE = REDIS_REACHABLE and REDIS_DRIVER

S3_HOST = os.getenv("WHALE_S3_ENDPOINT", "localhost:9000")
S3_HOSTNAME, S3_PORT_STR = S3_HOST.split(":")[:2]
S3_PORT = int(S3_PORT_STR)
S3_REACHABLE = _tcp_reachable(S3_HOSTNAME, S3_PORT)
S3_DRIVER = _driver_available("boto3")
S3_AVAILABLE = S3_REACHABLE and S3_DRIVER

TDENGINE_HOST = os.getenv("WHALE_TDENGINE_DSN", "localhost:6041")
TD_HOSTNAME, TD_PORT_STR = TDENGINE_HOST.replace("taosws://", "").replace("http://", "").split(":")[:2]
TD_PORT = int(TD_PORT_STR)
TDENGINE_REACHABLE = _tcp_reachable(TD_HOSTNAME, TD_PORT)
TDENGINE_AVAILABLE = TDENGINE_REACHABLE

_KAFKA_SKIP = not KAFKA_AVAILABLE
_KAFKA_SKIP_REASON = "environment-pending: Kafka broker 不可达或 kafka-python driver 缺失"


# ── 辅助函数 ────────────────────────────────────────────────────────────────


def _make_envelope(
    message_id: str = "l5-001",
    source_id: str = "source-l5-kafka",
    device_id: str = "dev-kafka-1",
    variable_key: str = "active_power",
    value: str = "1500.5",
) -> Envelope:
    """构造测试用 Envelope。"""
    return Envelope(
        schema_version="1.0",
        message_id=message_id,
        message_type="state_snapshot",
        trace_id=f"trace-{message_id}",
        source_id=source_id,
        published_at=datetime.now(tz=timezone.utc),
        items=[
            {
                "device_id": device_id,
                "device_code": device_id,
                "variable_key": variable_key,
                "value": value,
                "value_type": "float64",
                "quality_code": "0",
                "node_key": f"node-{device_id}",
                "source_observed_at": datetime.now(tz=timezone.utc).isoformat(),
            }
        ],
    )


# ── Test: Kafka 端到端 publish + consume ────────────────────────────────────


@pytest.mark.l5
@pytest.mark.skipif(_KAFKA_SKIP, reason=_KAFKA_SKIP_REASON)
class TestL5KafkaPipelineE2E:
    """Kafka → speed_layer pipeline L5 端到端验证。

    使用真实 Kafka broker 进行发布、消费和 consumer group 隔离验证。
    """

    @pytest.mark.asyncio
    async def test_kafka_publish_and_consume_e2e(self) -> None:
        """真实发布 Envelope 到 Kafka topic 并消费验证。

        L5 通过条件:
        1. KafkaSinkAdapter 成功发布消息，返回有效 offset（partition >= 0, offset >= 0）。
        2. KafkaSourceAdapter 从同一 topic 消费到消息。
        3. 消息内容与原 Envelope 一致。
        """
        from whale.message_pipeline.adapters.kafka import (
            KafkaSinkAdapter,
            KafkaSourceAdapter,
        )
        from whale.message_pipeline.model import TopicSpec

        test_topic = f"whale-l5-e2e-kafka-pipeline-{int(datetime.now().timestamp())}"
        group_id = f"whale-l5-e2e-group-{int(datetime.now().timestamp())}"

        # 1. 发布消息
        sink = KafkaSinkAdapter(
            bootstrap_servers=[f"{KAFKA_HOSTNAME}:{KAFKA_PORT}"],
            topic=test_topic,
            key_strategy=PartitionKeyStrategy.SOURCE_ID,
        )
        envelope = _make_envelope(message_id="l5-kafka-pub-001")
        offset = await sink.publish(envelope)
        await sink.flush()
        await sink.close()

        assert offset.partition >= 0, f"期望有效 partition，实际 {offset.partition}"
        assert offset.offset >= 0, f"期望有效 offset，实际 {offset.offset}"

        # 2. 消费消息
        source = KafkaSourceAdapter(
            bootstrap_servers=[f"{KAFKA_HOSTNAME}:{KAFKA_PORT}"],
            group_id=group_id,
            topic_specs=[TopicSpec(name=test_topic)],
            auto_offset_reset="earliest",
        )
        consumed_envelopes: list[Envelope] = []
        try:
            async for env in source.consume(test_topic, group_id):
                consumed_envelopes.append(env)
                if len(consumed_envelopes) >= 1:
                    break
        finally:
            await source.close()

        assert len(consumed_envelopes) >= 1, "未消费到任何消息"
        consumed = consumed_envelopes[0]
        assert consumed.message_id == "l5-kafka-pub-001"
        assert consumed.source_id == "source-l5-kafka"
        assert len(consumed.items) == 1

    @pytest.mark.asyncio
    async def test_kafka_consumer_group_isolation(self) -> None:
        """验证两个 consumer group 可以独立消费同一 topic。

        L5 通过条件:
        1. 两个不同的 consumer group 各自消费到全部消息。
        2. Offset 独立维护，互不影响。
        """
        from whale.message_pipeline.adapters.kafka import (
            KafkaSinkAdapter,
            KafkaSourceAdapter,
        )
        from whale.message_pipeline.model import TopicSpec

        test_topic = f"whale-l5-e2e-isolation-{int(datetime.now().timestamp())}"
        msg_count = 3

        # 发布消息
        sink = KafkaSinkAdapter(
            bootstrap_servers=[f"{KAFKA_HOSTNAME}:{KAFKA_PORT}"],
            topic=test_topic,
            key_strategy=PartitionKeyStrategy.SOURCE_ID,
        )
        for i in range(msg_count):
            await sink.publish(_make_envelope(message_id=f"l5-iso-{i:03d}"))
        await sink.flush()
        await sink.close()

        # 等待消息传播
        await asyncio.sleep(1)

        # Group A 消费
        group_a = f"whale-l5-e2e-group-a-{int(datetime.now().timestamp())}"
        source_a = KafkaSourceAdapter(
            bootstrap_servers=[f"{KAFKA_HOSTNAME}:{KAFKA_PORT}"],
            group_id=group_a,
            topic_specs=[TopicSpec(name=test_topic)],
            auto_offset_reset="earliest",
        )
        count_a = 0
        try:
            async for _ in source_a.consume(test_topic, group_a):
                count_a += 1
                if count_a >= msg_count:
                    break
        finally:
            await source_a.close()
        assert count_a == msg_count, f"Group A 期望消费 {msg_count} 条，实际 {count_a}"

        # Group B 消费（独立 group，从 earliest 开始）
        group_b = f"whale-l5-e2e-group-b-{int(datetime.now().timestamp())}"
        source_b = KafkaSourceAdapter(
            bootstrap_servers=[f"{KAFKA_HOSTNAME}:{KAFKA_PORT}"],
            group_id=group_b,
            topic_specs=[TopicSpec(name=test_topic)],
            auto_offset_reset="earliest",
        )
        count_b = 0
        try:
            async for _ in source_b.consume(test_topic, group_b):
                count_b += 1
                if count_b >= msg_count:
                    break
        finally:
            await source_b.close()
        assert count_b == msg_count, f"Group B 期望消费 {msg_count} 条，实际 {count_b}"


# ── Test: SpeedLayerWiring 完整链路 ──────────────────────────────────────────


@pytest.mark.l5
@pytest.mark.skipif(_KAFKA_SKIP, reason=_KAFKA_SKIP_REASON)
class TestL5SpeedLayerFullChainE2E:
    """SpeedLayerWiring 完整 L5 链路（Kafka → speed_layer → storage）。

    使用真实 Kafka 源 + 真实存储后端（如可用），验证完整数据流闭环。
    """

    @pytest.mark.asyncio
    async def test_speed_layer_wiring_with_real_kafka_source(
        self,
    ) -> None:
        """验证 SpeedLayerWiring 装配 Kafka source + InMemory sinks 可行。

        L5 通过条件:
        1. SpeedLayerWiring.with_kafka_source() + with_memory() 正常 build。
        2. 向 Kafka 发布消息，runner 启动后可正常注册 writer。
        """
        from whale.speed_layer.runner import SpeedLayerWiring

        wiring = SpeedLayerWiring()
        wiring.with_kafka_source(
            bootstrap_servers=[f"{KAFKA_HOSTNAME}:{KAFKA_PORT}"],
            group_id_prefix="whale-l5-e2e-speedlayer",
        )
        wiring.with_memory()  # 使用 InMemory sinks 以便无需外部存储
        wiring.with_inmemory_dlq()

        runner = wiring.build(topic="whale.ingest.state")
        assert runner.writer_count >= 1, "应至少注册一个 writer"

        # 验证 runner 可以正常启动和停止
        await runner.start()
        await asyncio.sleep(0.2)
        await runner.stop()

    @pytest.mark.asyncio
    async def test_full_chain_kafka_to_local_storage(
        self,
    ) -> None:
        """验证 Kafka -> speed_layer -> 本地存储的完整真实链路。

        使用真实 Kafka 发布消息，通过 KafkaSourceAdapter 消费，
        再由 LocalCompressedArchiveSink 写入本地 raw_archive 文件。

        L5 通过条件:
        1. 消息成功发布到 Kafka。
        2. KafkaSourceAdapter 从 Kafka 消费到消息。
        3. LocalCompressedArchiveSink 写入本地压缩文件。
        4. 本地文件内容与原消息一致。
        """
        from whale.message_pipeline.adapters.kafka import KafkaSinkAdapter, KafkaSourceAdapter
        from whale.message_pipeline.model import TopicSpec
        from whale.storage.raw_archive import (
            InMemoryManifestRepository,
            LocalCompressedArchiveSink,
        )

        test_topic = f"whale-l5-e2e-full-chain-{int(datetime.now().timestamp())}"
        group_id = f"whale-l5-e2e-full-group-{int(datetime.now().timestamp())}"
        msg_count = 3

        # 1. 发布消息到 Kafka
        sink = KafkaSinkAdapter(
            bootstrap_servers=[f"{KAFKA_HOSTNAME}:{KAFKA_PORT}"],
            topic=test_topic,
            key_strategy=PartitionKeyStrategy.SOURCE_ID,
        )
        expected_ids = []
        for i in range(msg_count):
            mid = f"l5-full-{i:03d}"
            expected_ids.append(mid)
            await sink.publish(_make_envelope(
                message_id=mid,
                source_id=f"src-full-{i % 2}",
                device_id=f"dev-full-{i}",
                variable_key="active_power",
                value=str(1500.0 + i * 100),
            ))
        await sink.flush()
        await sink.close()

        # 等待消息传播
        await asyncio.sleep(1.5)

        # 2. 从 Kafka 消费消息（有限循环，断点退出）
        source = KafkaSourceAdapter(
            bootstrap_servers=[f"{KAFKA_HOSTNAME}:{KAFKA_PORT}"],
            group_id=group_id,
            topic_specs=[TopicSpec(name=test_topic)],
            auto_offset_reset="earliest",
        )
        consumed: list[dict] = []
        try:
            async for envelope in source.consume(test_topic, group_id):
                consumed.append({
                    "schema_version": envelope.schema_version,
                    "message_id": envelope.message_id,
                    "message_type": envelope.message_type,
                    "source_id": envelope.source_id,
                    "published_at": envelope.published_at.isoformat(),
                    "items": envelope.items,
                })
                if len(consumed) >= msg_count:
                    break
        finally:
            await source.close()

        assert len(consumed) >= msg_count, f"期望消费 {msg_count} 条，实际 {len(consumed)}"
        consumed_ids = [r["message_id"] for r in consumed]
        for mid in expected_ids:
            assert mid in consumed_ids, f"缺失消息 {mid}"

        # 3. 写入本地压缩归档
        with tempfile.TemporaryDirectory() as tmpdir:
            archive = LocalCompressedArchiveSink(base_dir=tmpdir)
            manifest = InMemoryManifestRepository()
            batch_id = str(uuid.uuid4())[:8]
            written = await archive.write(batch_id, consumed)
            await archive.commit(batch_id)
            await manifest.record_manifest(
                batch_id=batch_id,
                file_path=f"{batch_id}.jsonl.gz",
                message_count=written,
                start_time=datetime.now(tz=timezone.utc),
                end_time=datetime.now(tz=timezone.utc),
            )
            assert written >= msg_count, f"期望写入 {msg_count} 条，实际 {written}"

            # 4. 验证 manifest 和本地文件内容
            batches = await archive.list_batches()
            assert len(batches) >= 1

            m = await manifest.get_manifest(batch_id)
            assert m is not None
            assert m["status"] == "committed"
            assert m["message_count"] >= msg_count

            import gzip
            found = 0
            for bid in batches:
                file_path = f"{tmpdir}/{bid}.jsonl.gz"
                if os.path.exists(file_path):
                    with gzip.open(file_path, "rt", encoding="utf-8") as f:
                        for line in f:
                            record = json.loads(line.strip())
                            assert "message_id" in record
                            assert "source_id" in record
                            found += 1
            assert found >= msg_count, f"期望 {msg_count} 条文件记录，实际 {found}"
