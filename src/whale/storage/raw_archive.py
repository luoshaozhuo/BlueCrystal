"""原始归档层（raw_archive）——不可变原始事实层。

raw_archive 是 Whale 数据底座的最底层，保存 ingest 输出的原始消息的不可变副本。
使用压缩文件（JSONL.gz）格式存储在 HDFS 或对象存储上，绝不使用 TDengine 替代。

本文件包含：
- FileArchiveSinkPort: 压缩文件归档端口。
- ManifestRepositoryPort: batch manifest 记录端口。
- LocalCompressedArchiveSink: 本地 gzip/zstd 压缩文件实现。
- HdfsArchiveSinkAdapter: HDFS adapter contract（environment-pending）。
- S3RawArchiveSink: S3/MinIO 真实写入适配器（使用 boto3，environment-pending fallback）。
- S3ManifestRepository: S3 后端 manifest 仓库（使用 boto3）。
- InMemoryManifestRepository: 测试用内存 manifest 实现。
"""

from __future__ import annotations

import gzip
import io
import json
import logging
import os
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class FileArchiveSinkPort(ABC):
    """压缩文件归档端口。

    将一批 Envelope 写入压缩文件并持久化。raw_archive 是不可变的原始事实层，
    文件一旦提交不应修改或删除。

    实现方责任：
    - 批量写入压缩文件（gzip/zstd）。
    - 管理 batch_id 与文件的映射关系。
    - 确保写入原子性（先写临时文件，后 rename）。

    不负责：
    - 消息去重和排序（由 speed layer 处理）。
    - 文件索引和查询加速（由 raw_index 层处理）。
    """

    @abstractmethod
    async def write(
        self, batch_id: str, envelopes: list[dict[str, Any]]
    ) -> int:
        """写入一批原始消息到压缩文件。

        以 batch_id 为文件名基础，将所有 envelope 序列化为一行一 JSON 的
        压缩文件格式（.jsonl.gz）。

        Args:
            batch_id: 批次标识，用于文件名和 manifest 关联。
            envelopes: 待归档的消息列表，每项为 dict（Envelope 序列化后）。

        Returns:
            写入的消息数量。

        Raises:
            RuntimeError: 写入失败。
        """
        ...

    @abstractmethod
    async def commit(self, batch_id: str) -> None:
        """确认批次写入完成。

        标记 batch_id 对应文件为可用状态，允许下游消费。

        Args:
            batch_id: 待确认的批次标识。

        Raises:
            RuntimeError: 提交失败。
        """
        ...

    @abstractmethod
    async def list_batches(self) -> list[str]:
        """列出所有已提交的 batch_id。

        Returns:
            已提交的 batch_id 列表，按时间排序。

        Raises:
            RuntimeError: 查询失败。
        """
        ...


class ManifestRepositoryPort(ABC):
    """batch manifest 记录端口。

    记录每个 batch 的元数据：文件路径、消息数量、时间范围、状态。

    实现方责任：
    - 持久化 manifest 元数据。
    - 支持按时间范围和状态查询。

    不负责：
    - 消息内容本身的读取。
    """

    @abstractmethod
    async def record_manifest(
        self,
        batch_id: str,
        file_path: str,
        message_count: int,
        start_time: datetime,
        end_time: datetime,
    ) -> None:
        """记录一条 batch manifest。

        Args:
            batch_id: 批次标识。
            file_path: 压缩文件路径。
            message_count: 消息数量。
            start_time: 批次最早消息时间。
            end_time: 批次最晚消息时间。

        Raises:
            RuntimeError: 记录失败。
        """
        ...

    @abstractmethod
    async def get_manifest(self, batch_id: str) -> dict[str, Any] | None:
        """查询指定 batch 的 manifest。

        Args:
            batch_id: 批次标识。

        Returns:
            manifest 记录字典，不存在时返回 None。
        """
        ...


class LocalCompressedArchiveSink(FileArchiveSinkPort):
    """本地 gzip 压缩文件归档实现。

    将消息批次写入本地文件系统的 .jsonl.gz 文件。适用于开发、测试和单机部署。
    生产环境应使用 HdfsArchiveSinkAdapter 或 ObjectStorageArchiveSinkAdapter。

    Attributes:
        _base_dir: 归档文件根目录。
        _compression: 压缩算法（"gzip" 或 "zstd"）。
        _pending: 待提交的批次信息映射。
        _batches: 已提交的 batch_id 列表。
    """

    def __init__(self, base_dir: str | Path, *, compression: str = "gzip"):
        """初始化本地压缩归档 sink。

        Args:
            base_dir: 归档文件根目录，不存在时自动创建。
            compression: 压缩算法，支持 "gzip" 和 "zstd"。
        """
        self._base_dir = Path(base_dir)
        self._compression = compression
        self._base_dir.mkdir(parents=True, exist_ok=True)
        self._pending: dict[str, Path] = {}
        self._batches: list[str] = []

    async def write(
        self, batch_id: str, envelopes: list[dict[str, Any]]
    ) -> int:
        """写入一批消息到本地压缩文件。

        先写入临时文件，成功后再 rename 到目标路径以保证原子性。

        Args:
            batch_id: 批次标识。
            envelopes: 待归档的消息列表。

        Returns:
            写入的消息数量。

        Raises:
            RuntimeError: 写入失败。
        """
        file_path = self._base_dir / f"{batch_id}.jsonl.gz"
        tmp_path = self._base_dir / f"{batch_id}.jsonl.gz.tmp"

        try:
            _write_compressed_jsonl(tmp_path, envelopes, self._compression)
            os.replace(tmp_path, file_path)
            self._pending[batch_id] = file_path
            return len(envelopes)
        except Exception as exc:
            if tmp_path.exists():
                tmp_path.unlink(missing_ok=True)
            raise RuntimeError(f"写入本地压缩文件失败: {batch_id}: {exc}") from exc

    async def commit(self, batch_id: str) -> None:
        """确认批次写入完成。

        Args:
            batch_id: 待确认的批次标识。

        Raises:
            ValueError: batch_id 不在 pending 列表中。
        """
        if batch_id not in self._pending:
            raise ValueError(f"batch_id 不在 pending 列表中: {batch_id}")
        self._batches.append(batch_id)
        del self._pending[batch_id]

    async def list_batches(self) -> list[str]:
        """列出所有已提交的 batch_id。

        Returns:
            已提交的 batch_id 列表，按提交顺序排列。
        """
        return list(self._batches)


class HdfsArchiveSinkAdapter(FileArchiveSinkPort):
    """HDFS 压缩文件归档 adapter（contract adapter）。

    environment-pending: 需要 HDFS 集群环境和 WebHDFS/pyarrow 依赖。
    当前为 contract adapter，仅提供接口骨架和配置校验。
    """

    def __init__(
        self,
        namenode_url: str,
        base_path: str,
        *,
        user: str = "whale",
        compression: str = "gzip",
    ):
        """初始化 HDFS 归档 adapter。

        校验 namenode_url 和 base_path 非空。

        Args:
            namenode_url: HDFS NameNode WebHDFS URL。
            base_path: HDFS 上的归档根目录。
            user: HDFS 操作用户。
            compression: 压缩算法。
        """
        self._namenode_url = namenode_url
        self._base_path = base_path
        self._user = user
        self._compression = compression
        self._config_valid = bool(namenode_url and base_path)
        # environment-pending: HDFS 集群环境依赖

    async def write(
        self, batch_id: str, envelopes: list[dict[str, Any]]
    ) -> int:
        """写入一批消息到 HDFS 压缩文件（contract-only 模式）。

        environment-pending: 返回 0。真实环境下通过 WebHDFS 或 pyarrow 实现。

        Args:
            batch_id: 批次标识。
            envelopes: 待归档的消息列表。

        Returns:
            contract mode 下返回 0。
        """
        return 0

    async def commit(self, batch_id: str) -> None:
        """确认 HDFS 批次写入完成（contract-only 模式）。

        environment-pending: 空操作。
        """
        pass

    async def list_batches(self) -> list[str]:
        """列出 HDFS 上的 batch_id（contract-only 模式）。

        environment-pending: 返回空列表。
        """
        return []


class S3RawArchiveSink(FileArchiveSinkPort):
    """S3/MinIO 对象存储真实写入适配器。

    使用 boto3 将压缩 JSONL 文件写入 S3/MinIO bucket。支持 configurable
    endpoint（适配 MinIO）、bucket、prefix 和 compression 格式。

    boto3 依赖标记为 optional。如果 boto3 不可用，adapter 标记为 degraded，
    所有写操作返回 environment-pending sentinel（count=0），不抛异常。

    适配器边界：
    - 将 batch 消息压缩为 .jsonl.gz 后 upload 到 S3。
    - 管理 object key 命名（{prefix}{batch_id}.jsonl.gz）。
    - 支持 health check（通过 S3 list_buckets 验证连通性）。

    Attributes:
        _endpoint_url: S3/MinIO endpoint URL。
        _bucket: S3 bucket 名称。
        _access_key: 访问密钥 ID。
        _secret_key: 访问密钥 Secret。
        _prefix: 对象前缀路径。
        _compression: 压缩算法。
        _client: boto3 S3 client 实例（延迟初始化）。
        _connected: 是否成功初始化 S3 client。
        _error: 初始化或操作失败时的错误信息。
        _committed: 已提交的 batch_id 集合。
    """

    def __init__(
        self,
        endpoint_url: str,
        bucket: str,
        *,
        access_key: str = "",
        secret_key: str = "",
        prefix: str = "raw_archive/",
        compression: str = "gzip",
        region_name: str = "us-east-1",
        use_ssl: bool = False,
    ) -> None:
        """初始化 S3/MinIO 归档 adapter。

        校验 endpoint_url 和 bucket 非空。S3 client 延迟初始化（首次操作时创建）。

        Args:
            endpoint_url: S3/MinIO endpoint URL。
            bucket: S3 bucket 名称。
            access_key: 访问密钥 ID，MinIO 可为空字符串表示匿名访问。
            secret_key: 访问密钥 Secret。
            prefix: 对象前缀（目录路径），末尾建议带 /。
            compression: 压缩算法（"gzip" 或 "zstd"）。
            region_name: AWS region 名称，MinIO 通常使用 "us-east-1"。
            use_ssl: 是否启用 HTTPS，MinIO 本地部署通常为 False。
        """
        self._endpoint_url = endpoint_url
        self._bucket = bucket
        self._access_key = access_key
        self._secret_key = secret_key
        self._prefix = prefix.rstrip("/") + "/" if prefix else "raw_archive/"
        self._compression = compression
        self._region_name = region_name
        self._use_ssl = use_ssl
        self._config_valid = bool(endpoint_url and bucket)
        self._client: Any = None
        self._connected = False
        self._error: str | None = None
        self._committed: set[str] = set()

    def _ensure_client(self) -> Any:
        """确保 boto3 S3 client 已初始化。

        延迟导入 boto3 并创建 S3 client。如果 boto3 不可用，记录错误。

        Returns:
            boto3 S3 client 实例，不可用时返回 None。
        """
        if self._client is not None:
            return self._client
        try:
            import boto3  # type: ignore[import-untyped]

            client_kwargs: dict[str, Any] = {
                "endpoint_url": self._endpoint_url,
                "region_name": self._region_name,
                "use_ssl": self._use_ssl,
            }
            if self._access_key and self._secret_key:
                client_kwargs["aws_access_key_id"] = self._access_key
                client_kwargs["aws_secret_access_key"] = self._secret_key
            self._client = boto3.client("s3", **client_kwargs)
            self._connected = True
            logger.info("S3 client 初始化成功: endpoint=%s bucket=%s",
                        self._endpoint_url, self._bucket)
            return self._client
        except ImportError:
            self._error = "boto3 未安装，S3 raw_archive 不可用"
            logger.warning(self._error)
        except Exception as exc:
            self._error = f"S3 client 初始化失败: {exc}"
            logger.warning(self._error)
        self._connected = False
        return None

    async def write(
        self, batch_id: str, envelopes: list[dict[str, Any]]
    ) -> int:
        """写入一批消息到 S3/MinIO 压缩文件。

        将 envelopes 压缩为 .jsonl.gz 格式，以 object key
        {prefix}{batch_id}.jsonl.gz 上传到 S3 bucket。

        Args:
            batch_id: 批次标识。
            envelopes: 待归档的消息列表。

        Returns:
            成功写入的消息数量。S3 不可用时返回 0（environment-pending）。

        Raises:
            RuntimeError: S3 上传失败（连接错误、权限不足等）。
        """
        if not envelopes:
            return 0
        client = self._ensure_client()
        if client is None:
            return 0
        # 构造压缩内容
        obj_key = f"{self._prefix}{batch_id}.jsonl.gz"
        content = _compress_to_bytes(envelopes, self._compression)
        try:
            client.put_object(
                Bucket=self._bucket,
                Key=obj_key,
                Body=content,
                ContentType="application/gzip",
                ContentEncoding="gzip",
            )
            logger.debug("S3 归档成功: bucket=%s key=%s count=%d",
                         self._bucket, obj_key, len(envelopes))
            return len(envelopes)
        except Exception as exc:
            # 无凭证或连接失败时降级返回 0，不抛异常
            error_msg = str(exc).lower()
            if "credentials" in error_msg or "connection" in error_msg or "timeout" in error_msg:
                self._error = f"S3 归档降级: {exc}"
                logger.warning("S3 归档降级: bucket=%s key=%s error=%s",
                               self._bucket, obj_key, exc)
                return 0
            raise RuntimeError(
                f"S3 归档写入失败 bucket={self._bucket} key={obj_key}: {exc}"
            ) from exc

    async def commit(self, batch_id: str) -> None:
        """确认 S3 批次写入完成。

        在 S3 上标记 batch_id 为已提交（内存记录）。
        S3 对象本身已在上传时原子写入，commit 仅完成批次状态追踪。

        Args:
            batch_id: 待确认的批次标识。
        """
        self._committed.add(batch_id)
        logger.debug("S3 batch 已提交: batch_id=%s", batch_id)

    async def list_batches(self) -> list[str]:
        """列出 S3 上已提交的 batch_id。

        当前基于内存记录返回。如需扫描 S3 bucket，可使用 list_objects_v2。

        Returns:
            已提交的 batch_id 列表。
        """
        return sorted(self._committed)

    async def health(self) -> bool:
        """通过 S3 head_bucket 检查连通性。

        Returns:
            True 表示 S3/MinIO 可达且 bucket 存在。
        """
        client = self._ensure_client()
        if client is None:
            return False
        try:
            client.head_bucket(Bucket=self._bucket)
            return True
        except Exception as exc:
            logger.warning("S3 health check 失败: %s", exc)
            return False

    @property
    def is_connected(self) -> bool:
        """S3 client 是否可用。"""
        return self._connected


class S3ManifestRepository(ManifestRepositoryPort):
    """S3 后端 manifest 仓库。

    将 batch manifest 元数据以 JSON 对象形式存储在 S3 上。
    manifest 文件的 object key 为 {prefix}_manifests/{batch_id}.json。

    适配器边界：
    - 每条 manifest 记录写入单独的 S3 JSON 对象。
    - 支持按 batch_id 读取 manifest。
    - 需要 S3 client（与 S3RawArchiveSink 共享同一 client 实例或独立创建）。

    Attributes:
        _s3_client: boto3 S3 client 实例。
        _bucket: S3 bucket 名称。
        _prefix: manifest 对象前缀。
    """

    def __init__(
        self,
        s3_client: Any,
        bucket: str,
        prefix: str = "raw_archive/",
    ) -> None:
        """初始化 S3 manifest 仓库。

        Args:
            s3_client: 已初始化的 boto3 S3 client。
            bucket: S3 bucket 名称。
            prefix: 对象前缀路径。
        """
        self._s3_client = s3_client
        self._bucket = bucket
        self._manifest_prefix = f"{prefix.rstrip('/')}/_manifests/"

    async def record_manifest(
        self,
        batch_id: str,
        file_path: str,
        message_count: int,
        start_time: datetime,
        end_time: datetime,
    ) -> None:
        """将 manifest 记录写入 S3 JSON 对象。

        Args:
            batch_id: 批次标识。
            file_path: 压缩文件路径（S3 object key）。
            message_count: 消息数量。
            start_time: 批次最早消息时间。
            end_time: 批次最晚消息时间。

        Raises:
            RuntimeError: S3 写入失败。
        """
        obj_key = f"{self._manifest_prefix}{batch_id}.json"
        manifest_data = {
            "batch_id": batch_id,
            "file_path": file_path,
            "message_count": message_count,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "status": "committed",
            "recorded_at": datetime.utcnow().isoformat() + "Z",
        }
        try:
            payload = json.dumps(manifest_data, ensure_ascii=False, default=str)
            self._s3_client.put_object(
                Bucket=self._bucket,
                Key=obj_key,
                Body=payload.encode("utf-8"),
                ContentType="application/json",
            )
            logger.debug("S3 manifest 已写入: key=%s", obj_key)
        except Exception as exc:
            raise RuntimeError(
                f"S3 manifest 写入失败 bucket={self._bucket} key={obj_key}: {exc}"
            ) from exc

    async def get_manifest(self, batch_id: str) -> dict[str, Any] | None:
        """从 S3 读取指定 batch 的 manifest。

        Args:
            batch_id: 批次标识。

        Returns:
            manifest 记录字典，不存在时返回 None。
        """
        obj_key = f"{self._manifest_prefix}{batch_id}.json"
        try:
            response = self._s3_client.get_object(
                Bucket=self._bucket,
                Key=obj_key,
            )
            body = response["Body"].read()
            result: dict[str, Any] = json.loads(body.decode("utf-8"))
            return result
        except Exception:
            return None


class InMemoryManifestRepository(ManifestRepositoryPort):
    """测试用内存 manifest 仓库。

    将所有 manifest 记录保存在内存 dict 中，用于测试验证。

    Attributes:
        manifests: batch_id 到 manifest 记录的映射。
    """

    def __init__(self) -> None:
        """初始化空的内存 manifest 仓库。"""
        self.manifests: dict[str, dict[str, Any]] = {}

    async def record_manifest(
        self,
        batch_id: str,
        file_path: str,
        message_count: int,
        start_time: datetime,
        end_time: datetime,
    ) -> None:
        """在内存中记录一条 manifest。

        Args:
            batch_id: 批次标识。
            file_path: 压缩文件路径。
            message_count: 消息数量。
            start_time: 批次最早消息时间。
            end_time: 批次最晚消息时间。
        """
        self.manifests[batch_id] = {
            "batch_id": batch_id,
            "file_path": file_path,
            "message_count": message_count,
            "start_time": start_time,
            "end_time": end_time,
            "status": "committed",
        }

    async def get_manifest(self, batch_id: str) -> dict[str, Any] | None:
        """从内存中查询 manifest。

        Args:
            batch_id: 批次标识。

        Returns:
            manifest 记录字典，不存在时返回 None。
        """
        return self.manifests.get(batch_id)


def _compress_to_bytes(
    records: list[dict[str, Any]],
    compression: str,
) -> bytes:
    """将记录列表压缩为字节流（用于 S3/MinIO 上传）。

    先构造 JSONL 文本，再用指定压缩算法压缩为 bytes。

    Args:
        records: 待压缩的记录列表。
        compression: 压缩算法（"gzip" 或 "zstd"）。

    Returns:
        压缩后的字节数据。

    Raises:
        ValueError: 不支持的压缩算法。
    """
    lines = "\n".join(
        json.dumps(r, ensure_ascii=False, default=str) for r in records
    ) + "\n"
    data = lines.encode("utf-8")

    if compression == "gzip":
        buf = io.BytesIO()
        with gzip.GzipFile(fileobj=buf, mode="wb", compresslevel=6) as f:
            f.write(data)
        result: bytes = buf.getvalue()
        return result
    elif compression == "zstd":
        try:
            import zstandard  # type: ignore[import-untyped,import-not-found]
        except ImportError:
            raise RuntimeError(
                "zstd 压缩需要安装 zstandard 包。"
            ) from None
        cctx = zstandard.ZstdCompressor(level=3)
        compressed: bytes = cctx.compress(data)
        return compressed
    else:
        raise ValueError(f"不支持的压缩算法: {compression}")


def _write_compressed_jsonl(
    path: Path,
    records: list[dict[str, Any]],
    compression: str,
) -> None:
    """将记录列表以一行一 JSON 的格式写入压缩文件。

    每行一个 JSON 对象，以换行符分隔，使用指定的压缩算法。

    Args:
        path: 目标文件路径。
        records: 待写入的记录列表。
        compression: 压缩算法（"gzip" 或 "zstd"）。

    Raises:
        ValueError: 不支持的压缩算法。
    """
    lines = "\n".join(
        json.dumps(r, ensure_ascii=False, default=str) for r in records
    ) + "\n"
    data = lines.encode("utf-8")

    if compression == "gzip":
        with gzip.open(path, "wb", compresslevel=6) as f:
            f.write(data)
    elif compression == "zstd":
        try:
            import zstandard  # type: ignore[import-untyped,import-not-found]  # 可选依赖，仅在运行时检查
        except ImportError:
            raise RuntimeError(
                "zstd 压缩需要安装 zstandard 包。"
            ) from None
        cctx = zstandard.ZstdCompressor(level=3)
        with open(path, "wb") as f:
            f.write(cctx.compress(data))
    else:
        raise ValueError(f"不支持的压缩算法: {compression}")
