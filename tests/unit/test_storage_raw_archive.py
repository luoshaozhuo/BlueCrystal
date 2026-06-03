"""storage raw_archive 层单元测试。

验证 LocalCompressedArchiveSink 的写入/提交/查询行为和
InMemoryManifestRepository 的 manifest 记录/查询功能。

被验证对象：
- whale.storage.raw_archive: LocalCompressedArchiveSink, InMemoryManifestRepository,
  HdfsArchiveSinkAdapter, ObjectStorageArchiveSinkAdapter

证据等级：L1 unit/mock（纯内存+本地文件测试）。
不能证明：HDFS/S3 真实存储的写入和查询行为。
"""

from __future__ import annotations

import gzip
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest

from whale.storage.raw_archive import (
    FileArchiveSinkPort,
    HdfsArchiveSinkAdapter,
    InMemoryManifestRepository,
    LocalCompressedArchiveSink,
    ManifestRepositoryPort,
    S3ManifestRepository,
    S3RawArchiveSink,
)


class TestLocalCompressedArchiveSink:
    """LocalCompressedArchiveSink 单元测试。"""

    @pytest.fixture
    def temp_dir(self) -> str:
        """创建临时目录用于归档测试。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.mark.asyncio
    async def test_write_and_commit(self, temp_dir: str) -> None:
        """验证写入一批消息并可提交。"""
        sink = LocalCompressedArchiveSink(temp_dir, compression="gzip")
        batch_id = "batch-001"
        envelopes = [
            {"message_id": "msg-1", "value": "hello"},
            {"message_id": "msg-2", "value": "world"},
        ]

        written = await sink.write(batch_id, envelopes)
        assert written == 2

        await sink.commit(batch_id)
        batches = await sink.list_batches()
        assert "batch-001" in batches

    @pytest.mark.asyncio
    async def test_file_is_valid_gzip_jsonl(self, temp_dir: str) -> None:
        """验证写入的文件是合法的 gzip JSONL 格式。"""
        sink = LocalCompressedArchiveSink(temp_dir, compression="gzip")
        batch_id = "batch-001"
        envelopes = [{"msg": "hello"}, {"msg": "world"}]

        await sink.write(batch_id, envelopes)
        await sink.commit(batch_id)

        file_path = Path(temp_dir) / f"{batch_id}.jsonl.gz"
        assert file_path.exists()

        with gzip.open(file_path, "rt", encoding="utf-8") as f:
            lines = f.readlines()
        assert len(lines) == 2
        data = [json.loads(line) for line in lines]
        assert data[0]["msg"] == "hello"

    @pytest.mark.asyncio
    async def test_commit_non_existent_batch_raises(self, temp_dir: str) -> None:
        """验证提交不存在的 batch_id 抛出异常。"""
        sink = LocalCompressedArchiveSink(temp_dir)
        with pytest.raises(ValueError):
            await sink.commit("nonexistent-batch")

    @pytest.mark.asyncio
    async def test_empty_batch(self, temp_dir: str) -> None:
        """验证写入空批次可正常运行。"""
        sink = LocalCompressedArchiveSink(temp_dir)
        written = await sink.write("empty-batch", [])
        assert written == 0


class TestHdfsArchiveSinkAdapter:
    """HdfsArchiveSinkAdapter contract adapter 测试。"""

    def test_is_file_archive_sink_port(self) -> None:
        """验证 HdfsArchiveSinkAdapter 实现 FileArchiveSinkPort。"""
        adapter = HdfsArchiveSinkAdapter(
            namenode_url="http://namenode:9870",
            base_path="/whale/raw_archive",
        )
        assert isinstance(adapter, FileArchiveSinkPort)

    @pytest.mark.asyncio
    async def test_write_returns_zero_in_contract_mode(self) -> None:
        """验证 contract mode 下 write 返回 0。"""
        adapter = HdfsArchiveSinkAdapter(
            namenode_url="http://namenode:9870",
            base_path="/whale/raw_archive",
        )
        result = await adapter.write("batch-001", [{"msg": "test"}])
        assert result == 0

    @pytest.mark.asyncio
    async def test_list_batches_returns_empty(self) -> None:
        """验证 contract mode 下 list_batches 返回空列表。"""
        adapter = HdfsArchiveSinkAdapter(
            namenode_url="http://namenode:9870",
            base_path="/whale/raw_archive",
        )
        batches = await adapter.list_batches()
        assert batches == []


class TestS3RawArchiveSink:
    """S3RawArchiveSink 单元测试（contract/degraded mode）。"""

    def test_is_file_archive_sink_port(self) -> None:
        """验证 S3RawArchiveSink 实现 FileArchiveSinkPort。"""
        adapter = S3RawArchiveSink(
            endpoint_url="http://minio:9000",
            bucket="whale-raw",
        )
        assert isinstance(adapter, FileArchiveSinkPort)

    @pytest.mark.asyncio
    async def test_write_returns_zero_in_degraded_mode(self) -> None:
        """验证 boto3 不可用时 write 返回 0（degraded mode）。"""
        adapter = S3RawArchiveSink(
            endpoint_url="http://minio:9000",
            bucket="whale-raw",
        )
        result = await adapter.write("batch-001", [{"msg": "test"}])
        # boto3 不可用时返回 0（environment-pending）
        assert result == 0

    def test_config_valid_with_endpoint_and_bucket(self) -> None:
        """验证有效配置下 _config_valid 为 True。"""
        adapter = S3RawArchiveSink(
            endpoint_url="http://minio:9000",
            bucket="whale-raw",
        )
        assert adapter._config_valid is True

    @pytest.mark.asyncio
    async def test_health_returns_false_without_boto3(self) -> None:
        """验证无 boto3 时 health 返回 False。"""
        adapter = S3RawArchiveSink(
            endpoint_url="http://minio:9000",
            bucket="whale-raw",
        )
        assert await adapter.health() is False

    @pytest.mark.asyncio
    async def test_commit_and_list_batches(self) -> None:
        """验证 commit 和 list_batches 正常（degraded mode）。"""
        adapter = S3RawArchiveSink(
            endpoint_url="http://minio:9000",
            bucket="whale-raw",
        )
        await adapter.commit("batch-001")
        await adapter.commit("batch-002")
        batches = await adapter.list_batches()
        assert "batch-001" in batches
        assert "batch-002" in batches

    def test_is_connected_false_without_boto3(self) -> None:
        """验证无 boto3 时 is_connected 为 False。"""
        adapter = S3RawArchiveSink(
            endpoint_url="http://minio:9000",
            bucket="whale-raw",
        )
        # _ensure_client 未被调用时 _connected 为 False
        assert adapter.is_connected is False


class TestS3ManifestRepository:
    """S3ManifestRepository contract 测试。"""

    def test_is_manifest_repository_port(self) -> None:
        """验证 S3ManifestRepository 实现 ManifestRepositoryPort。"""
        from unittest.mock import MagicMock

        mock_client = MagicMock()
        repo = S3ManifestRepository(
            s3_client=mock_client,
            bucket="whale-raw",
            prefix="raw_archive/",
        )
        assert isinstance(repo, ManifestRepositoryPort)


class TestInMemoryManifestRepository:
    """InMemoryManifestRepository 单元测试。"""

    def test_is_manifest_repository_port(self) -> None:
        """验证 InMemoryManifestRepository 实现 ManifestRepositoryPort。"""
        repo = InMemoryManifestRepository()
        assert isinstance(repo, ManifestRepositoryPort)

    @pytest.mark.asyncio
    async def test_record_and_get_manifest(self) -> None:
        """验证记录和查询 manifest 可正常工作。"""
        repo = InMemoryManifestRepository()
        start = datetime(2026, 6, 1, tzinfo=timezone.utc)
        end = datetime(2026, 6, 2, tzinfo=timezone.utc)

        await repo.record_manifest(
            batch_id="batch-001",
            file_path="/data/batch-001.jsonl.gz",
            message_count=100,
            start_time=start,
            end_time=end,
        )

        manifest = await repo.get_manifest("batch-001")
        assert manifest is not None
        assert manifest["batch_id"] == "batch-001"
        assert manifest["message_count"] == 100

    @pytest.mark.asyncio
    async def test_get_nonexistent_manifest_returns_none(self) -> None:
        """验证查询不存在的 manifest 返回 None。"""
        repo = InMemoryManifestRepository()
        result = await repo.get_manifest("nonexistent")
        assert result is None
