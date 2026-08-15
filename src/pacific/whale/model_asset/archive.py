"""仿真归档服务。

将仿真模型文件（源文件、输入文件、结果文件）通过 raw_archive 层的
FileArchiveSinkPort 归档到压缩文件，并记录 manifest 元数据。

本服务复用 storage.raw_archive 的端口：
- FileArchiveSinkPort: 压缩文件归档。
- ManifestRepositoryPort: batch manifest 记录。

不负责：
- 文件内容的解析和校验（由 detector 和 repository 负责）。
- 仿真引擎调度。
"""

from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

from pacific.whale.storage.raw_archive import FileArchiveSinkPort, ManifestRepositoryPort

logger = logging.getLogger(__name__)


class SimulationArchiveService:
    """仿真文件归档服务。

    将仿真相关文件压缩归档并记录 manifest。复用 raw_archive 层的归档端口，
    但为仿真场景提供专用的 batch_id 生成和文件列表跟踪。

    Attributes:
        _archive_sink: 文件归档端口。
        _manifest_repo: manifest 记录端口。
    """

    def __init__(
        self,
        archive_sink: FileArchiveSinkPort,
        manifest_repo: ManifestRepositoryPort,
    ) -> None:
        """初始化仿真归档服务。

        Args:
            archive_sink: 压缩文件归档端口实现。
            manifest_repo: manifest 记录仓库实现。
        """
        self._archive_sink = archive_sink
        self._manifest_repo = manifest_repo

    async def archive_files(
        self,
        batch_id: str,
        files: Sequence[str | Path],
        *,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """将一批仿真文件归档到压缩存储。

        读取每个文件的内容和校验和，构造 envelope 后写入压缩文件。
        使用 batch_id 作为归档批次标识。

        Args:
            batch_id: 归档批次标识。
            files: 待归档的文件路径列表。
            metadata: 附加元数据（如 model_code 等）。

        Returns:
            归档结果字典，包含：
            - batch_id: 批次标识。
            - file_count: 归档文件数。
            - file_uris: 文件 URI 列表。
            - checksums: 文件校验和列表。

        Raises:
            FileNotFoundError: 文件不存在。
            RuntimeError: 归档写入失败。
        """
        if not files:
            logger.warning("归档文件列表为空: batch_id=%s", batch_id)
            return {
                "batch_id": batch_id,
                "file_count": 0,
                "file_uris": [],
                "checksums": [],
            }

        envelopes: list[dict[str, Any]] = []
        file_uris: list[str] = []
        checksums: list[str] = []
        now = datetime.now(tz=timezone.utc)

        for file_path in files:
            p = Path(file_path)
            checksum = self._compute_sha256(p)
            uri = str(p.resolve())

            envelopes.append({
                "file_name": p.name,
                "file_uri": uri,
                "checksum_sha256": checksum,
                "file_size_bytes": p.stat().st_size,
                "archived_at": now.isoformat(),
                "metadata": metadata or {},
            })
            file_uris.append(uri)
            checksums.append(checksum)

        count = await self._archive_sink.write(batch_id, envelopes)
        await self._archive_sink.commit(batch_id)

        await self._manifest_repo.record_manifest(
            batch_id=batch_id,
            file_path=f"sim_archive/{batch_id}.jsonl.gz",
            message_count=count,
            start_time=now,
            end_time=now,
        )

        logger.info("仿真文件归档完成: batch_id=%s count=%d", batch_id, count)
        return {
            "batch_id": batch_id,
            "file_count": count,
            "file_uris": file_uris,
            "checksums": checksums,
        }

    @staticmethod
    def _compute_sha256(file_path: Path) -> str:
        """计算文件 SHA256 校验和。

        分块读取以支持大文件。

        Args:
            file_path: 文件路径。

        Returns:
            十六进制 SHA256 字符串。
        """
        sha = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha.update(chunk)
        return sha.hexdigest()

    @staticmethod
    def generate_batch_id(
        model_code: str,
        timestamp: datetime | None = None,
    ) -> str:
        """生成归档批次 ID。

        格式: sim_{model_code}_{timestamp}。

        Args:
            model_code: 模型编码。
            timestamp: 时间戳，None 时使用当前 UTC 时间。

        Returns:
            批次标识字符串。
        """
        ts = timestamp or datetime.now(tz=timezone.utc)
        ts_str = ts.strftime("%Y%m%dT%H%M%SZ")
        return f"sim_{model_code}_{ts_str}"
