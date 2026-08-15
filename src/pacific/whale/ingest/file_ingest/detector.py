"""文件落地完成检测器。

检测文件是否已完成写入并可用于接入。支持三种检测策略：
- manifest 检测：读取 JSON manifest，校验 data_path、size_bytes、checksum。
- size stable 检测：连续 N 次 stat 文件大小一致才判定稳定。
- done flag 检测：检查 `.done` 文件是否存在。

本文件包含：
- FileCompletionDetector: 文件落地完成检测器。
- SizeProbeProvider: 文件大小探测可注入接口（测试用）。
- OSStatSizeProbe: 操作系统 stat 大小探测实现。
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
from typing import Any, Protocol

from pacific.whale.ingest.file_ingest.models import (
    FileIngestManifest,
    FileStabilityProbeResult,
)

logger = logging.getLogger(__name__)

# ── 默认稳定探测次数：连续 N 次 stat 结果一致才判定稳定 ──
DEFAULT_SIZE_STABLE_COUNT = 3


class SizeProbeProvider(Protocol):
    """文件大小探测注入接口。

    测试中可注入 mock provider 以消除 sleep 依赖和真实文件系统访问。
    """

    def stat_size(self, path: str) -> int:
        """获取指定路径文件的大小（字节）。

        Args:
            path: 文件路径。

        Returns:
            文件大小（字节），文件不存在时返回 -1。
        """
        ...

    def probe_count(self) -> int:
        """返回当前探测调用次数。

        Returns:
            已调用 stat_size 的次数。
        """
        ...


class OSStatSizeProbe:
    """基于操作系统 stat 的文件大小探测实现。

    直接调用 os.stat 获取文件大小。适用于生产环境和集成测试。
    """

    def __init__(self) -> None:
        """初始化操作系统 stat 探测。"""
        self._count = 0

    def stat_size(self, path: str) -> int:
        """通过 os.stat 获取文件大小。

        Args:
            path: 文件路径。

        Returns:
            文件大小（字节），文件不存在时返回 -1。
        """
        self._count += 1
        try:
            return os.stat(path).st_size
        except FileNotFoundError:
            return -1

    def probe_count(self) -> int:
        """返回当前探测次数。

        Returns:
            已调用 stat_size 的次数。
        """
        return self._count


class FileCompletionDetector:
    """文件落地完成检测器。

    通过 manifest 校验、大小稳定性检测和 done flag 检测，判断文件
    是否已完成写入并可安全接入。

    检测失败时返回结构化的 FileStabilityProbeResult 和 reason，
    不抛不可控异常。

    Attributes:
        _size_probe: 文件大小探测实现（可注入测试替身）。
        _size_stable_count: 连续大小一致次数阈值。
    """

    def __init__(
        self,
        size_probe: SizeProbeProvider | None = None,
        *,
        size_stable_count: int = DEFAULT_SIZE_STABLE_COUNT,
    ) -> None:
        """初始化文件落地完成检测器。

        Args:
            size_probe: 文件大小探测实现，默认使用 OSStatSizeProbe。
            size_stable_count: 连续大小一致次数阈值。
        """
        self._size_probe: SizeProbeProvider = size_probe or OSStatSizeProbe()
        self._size_stable_count = size_stable_count

    def detect_by_manifest(self, manifest_path: str) -> FileStabilityProbeResult:
        """通过 JSON manifest 检测文件落地完成。

        读取 manifest JSON，提取 data_path、size_bytes、checksum 字段，
        然后校验实际文件是否满足 manifest 声明。

        严重错误（JSON 解析失败、文件不存在）通过 reason 返回，不抛异常。

        Args:
            manifest_path: manifest JSON 文件路径。

        Returns:
            FileStabilityProbeResult，包含 stable 状态和 reason。
        """
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest_data: dict[str, Any] = json.load(f)
        except FileNotFoundError:
            return FileStabilityProbeResult(
                path=manifest_path,
                stable=False,
                reason=f"manifest 文件不存在: {manifest_path}",
            )
        except json.JSONDecodeError as exc:
            return FileStabilityProbeResult(
                path=manifest_path,
                stable=False,
                reason=f"manifest JSON 解析失败: {exc}",
            )

        data_path = manifest_data.get("data_path", "")
        if not data_path:
            return FileStabilityProbeResult(
                path=manifest_path,
                stable=False,
                reason="manifest 中缺少 data_path 字段",
            )

        expected_size = manifest_data.get("size_bytes", -1)
        expected_checksum = manifest_data.get("checksum", "")
        checksum_algorithm = manifest_data.get("checksum_algorithm", "sha256")

        # 校验 data_path 文件是否存在
        actual_size = self._size_probe.stat_size(data_path)
        if actual_size < 0:
            return FileStabilityProbeResult(
                path=data_path,
                stable=False,
                size_bytes=0,
                reason=f"data_path 指向的文件不存在: {data_path}",
            )

        # 校验文件大小
        if expected_size >= 0 and actual_size != expected_size:
            return FileStabilityProbeResult(
                path=data_path,
                stable=False,
                size_bytes=actual_size,
                reason=f"文件大小不匹配: 期望 {expected_size} 字节, 实际 {actual_size} 字节",
            )

        # 校验 checksum
        if expected_checksum:
            actual_checksum = self._compute_checksum(data_path, checksum_algorithm)
            if actual_checksum != expected_checksum:
                return FileStabilityProbeResult(
                    path=data_path,
                    stable=False,
                    size_bytes=actual_size,
                    reason=f"checksum 不匹配: 期望 {expected_checksum[:16]}..., 实际 {actual_checksum[:16]}...",
                )

        return FileStabilityProbeResult(
            path=data_path,
            stable=True,
            size_bytes=actual_size,
            reason="manifest_valid",
        )

    def detect_by_size_stable(self, data_path: str) -> FileStabilityProbeResult:
        """通过连续多次 stat 检测文件大小稳定性。

        连续 N 次（默认 3 次）stat 文件大小一致才能判定文件写入已完成。
        此方法不包含 sleep/wait 逻辑；调用方负责在多次调用间控制间隔。

        测试中可注入 SizeProbeProvider 消除真实文件系统依赖。

        Args:
            data_path: 待检测的数据文件路径。

        Returns:
            FileStabilityProbeResult，包含 stable 状态和 reason。
        """
        previous_size: int | None = None
        stable_count = 0
        observed_count = 0

        for _ in range(self._size_stable_count):
            current_size = self._size_probe.stat_size(data_path)
            observed_count += 1
            if current_size < 0:
                return FileStabilityProbeResult(
                    path=data_path,
                    stable=False,
                    size_bytes=0,
                    observed_count=observed_count,
                    reason=f"文件不存在: {data_path}",
                )
            if previous_size is not None and current_size == previous_size:
                stable_count += 1
            else:
                stable_count = 1
            previous_size = current_size

        all_stable = stable_count >= self._size_stable_count
        return FileStabilityProbeResult(
            path=data_path,
            stable=all_stable,
            size_bytes=previous_size or 0,
            observed_count=observed_count,
            reason="size_stable" if all_stable else f"size_unstable: stable_count={stable_count}",
        )

    def detect_by_done_flag(self, data_path: str) -> FileStabilityProbeResult:
        """通过 `.done` 标记文件检测文件落地完成。

        检查与 data_path 同目录下的同名 `.done` 文件是否存在。
        例如 data_path 为 `/data/rec.bin`，则检查 `/data/rec.bin.done`。

        此策略依赖上游写入方在写入完毕后创建 `.done` 文件。
        单独使用此策略无法验证文件完整性，建议与 checksum 校验组合使用。

        Args:
            data_path: 数据文件路径。

        Returns:
            FileStabilityProbeResult，包含 stable 状态和 reason。
        """
        done_path = data_path + ".done"
        if os.path.exists(done_path):
            actual_size = self._size_probe.stat_size(data_path)
            return FileStabilityProbeResult(
                path=data_path,
                stable=True,
                size_bytes=actual_size if actual_size >= 0 else 0,
                reason="done_flag_present",
            )
        return FileStabilityProbeResult(
            path=data_path,
            stable=False,
            size_bytes=0,
            reason=f"done_flag 文件不存在: {done_path}",
        )

    def build_manifest_from_file(self, data_path: str, file_type: str) -> FileIngestManifest | None:
        """从数据文件路径构建 manifest。

        读取文件计算 size_bytes 和 sha256 校验和，生成 FileIngestManifest。
        文件不存在时返回 None。

        Args:
            data_path: 数据文件路径。
            file_type: 文件类型。

        Returns:
            FileIngestManifest 实例，文件不存在或读取失败时返回 None。
        """
        try:
            actual_size = self._size_probe.stat_size(data_path)
            if actual_size < 0:
                return None
            checksum = self._compute_checksum(data_path, "sha256")
            file_id = os.path.basename(data_path)
            return FileIngestManifest(
                file_id=file_id,
                file_type=file_type,
                path=data_path,
                size_bytes=actual_size,
                checksum=checksum,
                checksum_algorithm="sha256",
                done_flag_path=data_path + ".done",
            )
        except Exception as exc:
            logger.warning("构建 manifest 失败 path=%s: %s", data_path, exc)
            return None

    @staticmethod
    def _compute_checksum(path: str, algorithm: str = "sha256") -> str:
        """计算文件的校验和。

        Args:
            path: 文件路径。
            algorithm: 校验和算法（当前仅支持 sha256）。

        Returns:
            十六进制校验和字符串。

        Raises:
            ValueError: 不支持的算法。
        """
        if algorithm != "sha256":
            raise ValueError(f"不支持的校验和算法: {algorithm}")
        hasher = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
