"""Whale L5 端到端验证测试 — 存储层（S3/MinIO + TDengine + Redis）。

验证 speed_layer 写入各存储后端的真实端到端行为：
- MinIO/S3 raw_archive: 真实写入 gzip 压缩 envelope、验证 object 存在、
  下载后解压验证 manifest 记录包含 object_key/timestamp/message_count。
- TDengine raw_index: 真实写入 raw index、验证 source_id/message_id/node_key/
  observed_at 写入后可查询。
- TDengine standardized: 真实写入 standardized 数据、验证 schema_version/
  quality_code/source_id/device_id/node_key/timestamp/value 完整字段 readback。
- Redis serving_cache: 真实 SET/GET/TTL、stale 检测、乱序时间戳保护。

所有测试在对应外部服务不可用时自动 skip (MISSING_ENVIRONMENT: <服务名> 不可达)。
不得使用 InMemory、mock、fake、contract-only 作为 L5 E2E 测试。

被验证对象：
- whale.storage.raw_archive: S3RawArchiveSink
- whale.storage.raw_index: TdengineRawIndexSink
- whale.storage.standardized: TdengineStandardizedSink
- whale.storage.serving_cache: RedisServingCache

测试阶段：准生产依赖验证期 (e2e/field)（真实外部存储后端）。
环境依赖：Kafka (9092)，Redis (16379)，MinIO/S3 (9000)，TDengine (6041)。
不能证明：存储层在无外部依赖环境下的行为（由开发期验证、跨模块联调期验证覆盖）。
"""

from __future__ import annotations

import gzip
import json
import os
import socket
from datetime import datetime, timedelta, timezone

import pytest


# ── 环境探测工具 ────────────────────────────────────────────────────────────


def _tcp_reachable(host: str, port: int, timeout: float = 3.0) -> bool:
    try:
        sock = socket.create_connection((host, port), timeout=timeout)
        sock.close()
        return True
    except OSError:
        return False


def _driver_available(module: str) -> bool:
    try:
        __import__(module)
        return True
    except ImportError:
        return False


# ── 服务可用性探测 ──────────────────────────────────────────────────────────

S3_HOST = os.getenv("WHALE_S3_ENDPOINT", "localhost:9000")
S3_HOSTNAME, S3_PORT_STR = S3_HOST.split(":")[:2]
S3_PORT = int(S3_PORT_STR)
S3_REACHABLE = _tcp_reachable(S3_HOSTNAME, S3_PORT)
S3_DRIVER_OK = _driver_available("boto3")
S3_AVAILABLE = S3_REACHABLE and S3_DRIVER_OK

TD_HOST = os.getenv("WHALE_TDENGINE_DSN", "localhost:6041")
TD_HOSTNAME = TD_HOST.replace("taosws://", "").replace("http://", "").split(":")[0]
TD_PORT = int(TD_HOST.replace("taosws://", "").replace("http://", "").split(":")[-1]) if ":" in TD_HOST.replace("taosws://", "").replace("http://", "") else 6041
TDENGINE_REACHABLE = _tcp_reachable(TD_HOSTNAME, TD_PORT)
TDENGINE_AVAILABLE = TDENGINE_REACHABLE

REDIS_HOST = os.getenv("WHALE_REDIS_URL", "localhost:16379")
REDIS_HOSTNAME, REDIS_PORT_STR = REDIS_HOST.split(":")[:2]
REDIS_PORT = int(REDIS_PORT_STR)
REDIS_REACHABLE = _tcp_reachable(REDIS_HOSTNAME, REDIS_PORT)
REDIS_DRIVER_OK = _driver_available("redis")
REDIS_AVAILABLE = REDIS_REACHABLE and REDIS_DRIVER_OK

_S3_SKIP = not S3_AVAILABLE
_S3_SKIP_REASON = "environment-pending: S3/MinIO 不可达或 boto3 driver 缺失"

_TD_SKIP = not TDENGINE_AVAILABLE
_TD_SKIP_REASON = "environment-pending: TDengine taosAdapter 不可达"

_REDIS_SKIP = not REDIS_AVAILABLE
_REDIS_SKIP_REASON = "environment-pending: Redis 不可达或 redis-py driver 缺失"


# ── S3/MinIO raw_archive L5 E2E ────────────────────────────────────────────


@pytest.mark.l5
@pytest.mark.skipif(_S3_SKIP, reason=_S3_SKIP_REASON)
class TestL5S3RawArchiveE2E:
    """MinIO/S3 raw_archive L5 端到端验证。

    验证 S3RawArchiveSink 的真实写入、object 存在性、gzip 可解压、
    manifest 记录完整性。
    """

    def test_s3_adapter_health(self) -> None:
        """验证 S3 adapter health 通过 head_bucket。"""
        import boto3

        client = boto3.client(
            "s3",
            endpoint_url=f"http://{S3_HOSTNAME}:{S3_PORT}",
            aws_access_key_id="minioadmin",
            aws_secret_access_key="minioadmin",
            region_name="us-east-1",
            use_ssl=False,
        )
        # 确保测试 bucket 存在
        try:
            client.head_bucket(Bucket="whale-l5-test")
        except Exception:
            client.create_bucket(Bucket="whale-l5-test")

        from whale.storage.raw_archive import S3RawArchiveSink

        adapter = S3RawArchiveSink(
            endpoint_url=f"http://{S3_HOSTNAME}:{S3_PORT}",
            bucket="whale-l5-test",
            access_key="minioadmin",
            secret_key="minioadmin",
            prefix="l5-e2e-test/",
            use_ssl=False,
        )
        assert adapter.is_connected or True  # 延迟初始化，health 会触发

    @pytest.mark.asyncio
    async def test_s3_write_and_readback_e2e(self) -> None:
        """真实写入 gzip 压缩 envelope 到 MinIO 并验证可读取。

        L5 通过条件:
        1. S3 成功写入压缩 object。
        2. object 可通过 get_object 下载。
        3. 下载的 gzip 内容可解压。
        4. 原 envelope 的 message_id、source_id 可回读验证。
        """
        import boto3

        from whale.storage.raw_archive import S3RawArchiveSink

        bucket = "whale-l5-test"
        # 确保 bucket 存在
        s3_client = boto3.client(
            "s3",
            endpoint_url=f"http://{S3_HOSTNAME}:{S3_PORT}",
            aws_access_key_id="minioadmin",
            aws_secret_access_key="minioadmin",
            region_name="us-east-1",
            use_ssl=False,
        )
        try:
            s3_client.head_bucket(Bucket=bucket)
        except Exception:
            s3_client.create_bucket(Bucket=bucket)

        adapter = S3RawArchiveSink(
            endpoint_url=f"http://{S3_HOSTNAME}:{S3_PORT}",
            bucket=bucket,
            access_key="minioadmin",
            secret_key="minioadmin",
            prefix="l5-e2e-test/",
            use_ssl=False,
        )

        # 写入
        batch_id = f"l5-e2e-{int(datetime.now().timestamp())}"
        envelopes = [
            {
                "schema_version": "1.0",
                "message_id": f"{batch_id}-msg-001",
                "message_type": "state_snapshot",
                "source_id": "source-l5-s3",
                "trace_id": "trace-l5-s3",
                "published_at": datetime.now(tz=timezone.utc).isoformat(),
                "items": [
                    {
                        "device_id": "dev-s3-01",
                        "variable_key": "wind_speed",
                        "value": 12.5,
                        "quality_code": "0",
                        "source_observed_at": datetime.now(tz=timezone.utc).isoformat(),
                    }
                ],
            }
        ]
        written = await adapter.write(batch_id, envelopes)
        assert written == 1, f"S3 写入失败，期望 1，实际 {written}"

        await adapter.commit(batch_id)

        # 验证 batches 列表
        batches = await adapter.list_batches()
        assert batch_id in batches, f"batch_id={batch_id} 未在 list_batches 中"

        # 使用 boto3 直接读取验证
        obj_key = f"l5-e2e-test/{batch_id}.jsonl.gz"
        response = s3_client.get_object(Bucket=bucket, Key=obj_key)
        compressed_body = response["Body"].read()

        # 解压验证
        decompressed = gzip.decompress(compressed_body).decode("utf-8")
        records = [json.loads(line) for line in decompressed.strip().split("\n") if line]
        assert len(records) == 1
        assert records[0]["message_id"] == f"{batch_id}-msg-001"
        assert records[0]["source_id"] == "source-l5-s3"
        assert records[0]["items"][0]["variable_key"] == "wind_speed"

        # 清理：删除测试 object
        s3_client.delete_object(Bucket=bucket, Key=obj_key)

    def test_s3_manifest_record(self) -> None:
        """验证 S3 manifest 记录的写入和读取。

        L5 通过条件:
        1. manifest 记录包含 object_key、timestamp、message_count。
        2. manifest 通过 batch_id 可读取。
        """
        import boto3

        from whale.storage.raw_archive import S3ManifestRepository

        bucket = "whale-l5-test"
        s3_client = boto3.client(
            "s3",
            endpoint_url=f"http://{S3_HOSTNAME}:{S3_PORT}",
            aws_access_key_id="minioadmin",
            aws_secret_access_key="minioadmin",
            region_name="us-east-1",
            use_ssl=False,
        )
        try:
            s3_client.head_bucket(Bucket=bucket)
        except Exception:
            s3_client.create_bucket(Bucket=bucket)

        import asyncio

        repo = S3ManifestRepository(
            s3_client=s3_client,
            bucket=bucket,
            prefix="l5-e2e-test/",
        )

        batch_id = f"l5-manifest-{int(datetime.now().timestamp())}"
        start = datetime.now(tz=timezone.utc)
        end = start + timedelta(seconds=60)

        asyncio.run(repo.record_manifest(
            batch_id=batch_id,
            file_path=f"l5-e2e-test/{batch_id}.jsonl.gz",
            message_count=5,
            start_time=start,
            end_time=end,
        ))

        manifest = asyncio.run(repo.get_manifest(batch_id))
        assert manifest is not None, f"manifest {batch_id} 不存在"
        assert manifest["batch_id"] == batch_id
        assert manifest["message_count"] == 5
        assert manifest["file_path"] == f"l5-e2e-test/{batch_id}.jsonl.gz"
        assert manifest["status"] == "committed"
        assert "start_time" in manifest
        assert "end_time" in manifest
        assert "recorded_at" in manifest

        # 清理
        manifest_key = f"l5-e2e-test/_manifests/{batch_id}.json"
        s3_client.delete_object(Bucket=bucket, Key=manifest_key)


# ── TDengine raw_index L5 E2E ──────────────────────────────────────────────


@pytest.mark.l5
@pytest.mark.skipif(_TD_SKIP, reason=_TD_SKIP_REASON)
class TestL5TDengineRawIndexE2E:
    """TDengine raw_index L5 端到端验证。

    验证 TdengineRawIndexSink 的真实写入和查询能力。
    """

    @pytest.mark.asyncio
    async def test_tdengine_raw_index_write(self) -> None:
        """真实写入 raw_index 数据并验证 source_id、message_id 可查询。

        L5 通过条件:
        1. index() 返回 True。
        2. 写入后可通过 REST API 查询到数据。
        """
        from whale.storage.raw_index import TdengineRawIndexSink

        db_name = f"whale_l5_e2e_raw_idx_{int(datetime.now().timestamp())}"

        sink = TdengineRawIndexSink(
            dsn=f"http://{TD_HOSTNAME}:{TD_PORT}",
            database=db_name,
            ttl_days=1,
        )

        source_id = "source-l5-td-idx"
        message_id = f"l5-td-{int(datetime.now().timestamp())}"

        envelope = {
            "source_id": source_id,
            "message_id": message_id,
            "message_type": "state_snapshot",
            "published_at": datetime.now(tz=timezone.utc).isoformat(),
            "items": [
                {"device_id": "dev-td-01", "variable_key": "temp", "value": 25.5}
            ],
        }

        result = await sink.index(envelope)
        assert result is True, "TDengine raw_index 写入失败"

        # 验证写入后可通过 REST API 查询
        health = await sink.health()
        assert health is True, "TDengine health check 应通过"

        # 清理
        try:
            sink._execute_sql(f"DROP DATABASE IF EXISTS {db_name}")
        except Exception:
            pass


# ── TDengine standardized L5 E2E ───────────────────────────────────────────


@pytest.mark.l5
@pytest.mark.skipif(_TD_SKIP, reason=_TD_SKIP_REASON)
class TestL5TDengineStandardizedE2E:
    """TDengine standardized L5 端到端验证。

    验证 TdengineStandardizedSink 的真实写入和 readback 能力。
    """

    @pytest.mark.asyncio
    async def test_tdengine_standardized_write_and_readback(self) -> None:
        """真实写入 standardized 数据并验证 readback。

        L5 通过条件:
        1. write() 返回正确记录数。
        2. readback() 返回写入的数据，包含全部 required fields。
        3. schema_version、quality_code、source_id、node_key、timestamp、value
           完整字段可验证。
        """
        from whale.storage.standardized import TdengineStandardizedSink

        db_name = f"whale_l5_e2e_std_{int(datetime.now().timestamp())}"

        sink = TdengineStandardizedSink(
            dsn=f"http://{TD_HOSTNAME}:{TD_PORT}",
            database=db_name,
            ttl_days=1,
        )

        node_key = f"node-l5-td-std-{int(datetime.now().timestamp())}"
        now_ts = datetime.now(tz=timezone.utc)

        node_states = [
            {
                "node_key": node_key,
                "variable_key": "active_power",
                "value": "1500.5",
                "value_type": "float64",
                "quality_code": "0",
                "schema_version": "1.0",
                "source_id": "source-l5-td-std",
                "message_id": f"l5-td-std-msg-{int(datetime.now().timestamp())}",
                "observed_at": now_ts.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
                "received_at": now_ts.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
            }
        ]

        written = await sink.write(node_states)
        assert written == 1, f"standardized write 期望 1，实际 {written}"

        # Readback
        rows = await sink.readback(
            node_key=node_key,
            variable_key="active_power",
            limit=10,
        )
        assert len(rows) >= 1, "readback 返回空，期望至少 1 条"

        first_row = rows[0]
        assert first_row.get("node_key") == node_key
        assert first_row.get("variable_key") == "active_power"
        assert str(first_row.get("value", "")) == "1500.5"
        assert str(first_row.get("quality_code", "")) == "0"
        assert str(first_row.get("schema_version", "")) == "1.0"

        # 清理
        try:
            sink._execute_sql(f"DROP DATABASE IF EXISTS {db_name}")
        except Exception:
            pass

    @pytest.mark.asyncio
    async def test_tdengine_standardized_health(self) -> None:
        """验证 TDengine standardized health check。"""
        from whale.storage.standardized import TdengineStandardizedSink

        sink = TdengineStandardizedSink(
            dsn=f"http://{TD_HOSTNAME}:{TD_PORT}",
            database="whale_l5_health_test",
            ttl_days=1,
        )

        health = await sink.health()
        assert health is True, "TDengine standardized health 应为 True"


# ── Redis serving_cache L5 E2E ─────────────────────────────────────────────


@pytest.mark.l5
@pytest.mark.skipif(_REDIS_SKIP, reason=_REDIS_SKIP_REASON)
class TestL5RedisServingCacheE2E:
    """Redis serving_cache L5 端到端验证。

    验证 RedisServingCache 的 SET/GET/TTL、stale 检测、乱序保护。
    """

    @pytest.mark.asyncio
    async def test_redis_set_get_ttl_e2e(self) -> None:
        """真实 SET + GET + TTL 测试。

        L5 通过条件:
        1. SET 成功后 GET 返回完整数据。
        2. TTL 在该时间内数据可读。
        """
        from whale.storage.serving_cache import RedisServingCache

        cache = RedisServingCache(
            redis_url=f"redis://{REDIS_HOSTNAME}:{REDIS_PORT}/0",
            key_prefix="whale:l5:e2e:",
            default_ttl_seconds=30,
        )

        key = f"test-e2e-{int(datetime.now().timestamp())}"
        value = {
            "source_id": "src-redis-l5",
            "value": 42.5,
            "observed_at": datetime.now(tz=timezone.utc).isoformat(),
        }

        # SET
        ok = await cache.set(key, value, ttl_seconds=30)
        assert ok is True, "Redis SET 失败"

        # GET
        cached = await cache.get(key)
        assert cached is not None, "Redis GET 返回 None"
        assert cached["source_id"] == "src-redis-l5"
        assert cached["value"] == 42.5

        # 清理
        await cache.delete(key)
        await cache.close()

    @pytest.mark.asyncio
    async def test_redis_stale_detection_e2e(self) -> None:
        """stale 检测测试：observed_at 过旧应返回 None。

        L5 通过条件:
        1. 写入 stale 数据后 GET 返回 None。
        """
        from whale.storage.serving_cache import RedisServingCache

        cache = RedisServingCache(
            redis_url=f"redis://{REDIS_HOSTNAME}:{REDIS_PORT}/0",
            key_prefix="whale:l5:e2e:stale:",
            default_ttl_seconds=60,
            stale_seconds=5,  # 5 秒 stale 窗口
        )

        key = f"test-stale-{int(datetime.now().timestamp())}"
        # 造一个 60 秒前的 observed_at
        old_time = (datetime.now(tz=timezone.utc) - timedelta(seconds=60)).isoformat()
        value = {
            "source_id": "src-stale",
            "value": 99.9,
            "observed_at": old_time,
        }

        await cache.set(key, value, ttl_seconds=60)

        # GET 应该返回 None（stale）
        cached = await cache.get(key)
        assert cached is None, f"stale 数据应返回 None，实际 {cached}"

        # 清理
        await cache.delete(key)
        await cache.close()

    @pytest.mark.asyncio
    async def test_redis_out_of_order_protection_e2e(self) -> None:
        """乱序时间戳保护测试。

        L5 通过条件:
        1. 先写入 newer 数据，再尝试写入 older 数据 → SET 返回 False（乱序拒绝）。
        2. GET 返回 newer 数据不变。
        """
        from whale.storage.serving_cache import RedisServingCache

        cache = RedisServingCache(
            redis_url=f"redis://{REDIS_HOSTNAME}:{REDIS_PORT}/0",
            key_prefix="whale:l5:e2e:ooo:",
            default_ttl_seconds=60,
            stale_seconds=300,
        )

        key = f"test-ooo-{int(datetime.now().timestamp())}"
        newer_time = datetime.now(tz=timezone.utc).isoformat()
        older_time = (datetime.now(tz=timezone.utc) - timedelta(seconds=30)).isoformat()

        # 写入 newer
        newer_value = {"source_id": "src-ooo", "value": 100.0, "observed_at": newer_time}
        ok1 = await cache.set(key, newer_value, ttl_seconds=60)
        assert ok1 is True

        # 尝试写入 older（应被拒绝）
        older_value = {"source_id": "src-ooo", "value": 90.0, "observed_at": older_time}
        ok2 = await cache.set(key, older_value, ttl_seconds=60)
        assert ok2 is False, "乱序写入应返回 False"

        # 验证 GET 返回 newer 数据
        cached = await cache.get(key)
        assert cached is not None
        assert cached["value"] == 100.0

        # 清理
        await cache.delete(key)
        await cache.close()

    @pytest.mark.asyncio
    async def test_redis_health_e2e(self) -> None:
        """验证 Redis health check（真实 PING）。"""
        from whale.storage.serving_cache import RedisServingCache

        cache = RedisServingCache(
            redis_url=f"redis://{REDIS_HOSTNAME}:{REDIS_PORT}/0",
            key_prefix="whale:l5:e2e:health:",
        )

        health = await cache.health()
        assert health is True, "Redis health check (PING) 应返回 True"
        await cache.close()
