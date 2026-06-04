"""文件落地完成检测器单元测试。

验证 FileCompletionDetector 的三种检测策略和 checksum 校验逻辑。
size_stable 检测通过可注入 MockSizeProbe 消除真实文件系统和 sleep 依赖。

被验证对象：
- whale.ingest.file_ingest.detector: FileCompletionDetector,
  OSStatSizeProbe, SizeProbeProvider

测试阶段：开发期验证 (unit，部分使用临时文件)。
不能证明：真实文件系统 inotify、生产环境并发写入检测。
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


from whale.ingest.file_ingest.detector import (
    FileCompletionDetector,
)


class MockSizeProbe:
    """可注入的 Mock 文件大小探测。

    通过预设返回值控制 stat_size 的结果，用于测试 size_stable 检测
    而无需 sleep 或真实文件系统。支持按 probe 顺序返回不同值。
    """

    def __init__(self, sizes: list[int] | None = None) -> None:
        """初始化 Mock 探测。

        Args:
            sizes: 每次 stat 返回的 size 列表，-1 表示文件不存在。
        """
        self._sizes = list(sizes) if sizes else []
        self._count = 0
        self._default = -1

    def stat_size(self, path: str) -> int:
        """返回预设的大小值。

        Args:
            path: 文件路径（不影响返回值）。

        Returns:
            预设的 size 值。
        """
        self._count += 1
        if self._count <= len(self._sizes):
            return self._sizes[self._count - 1]
        # 超出预设后返回最后一个值（模拟持续稳定的场景）
        if self._sizes:
            return self._sizes[-1]
        return self._default

    def probe_count(self) -> int:
        """返回当前探测次数。"""
        return self._count


class TestFileCompletionDetectorSizeStable:
    """size_stable 检测策略测试。"""

    def test_stable_after_consecutive_same_sizes(self) -> None:
        """验证连续 N 次相同大小后判定稳定。"""
        # 三次相同值 100 -> stable
        probe = MockSizeProbe(sizes=[100, 100, 100])
        detector = FileCompletionDetector(size_probe=probe, size_stable_count=3)
        result = detector.detect_by_size_stable("/fake/path.bin")
        assert result.stable is True
        assert result.size_bytes == 100
        assert result.observed_count == 3
        assert result.reason == "size_stable"

    def test_unstable_when_size_changes(self) -> None:
        """验证大小变化时判定不稳定。"""
        probe = MockSizeProbe(sizes=[100, 150, 150])
        detector = FileCompletionDetector(size_probe=probe, size_stable_count=3)
        result = detector.detect_by_size_stable("/fake/path.bin")
        assert result.stable is False
        assert result.observed_count == 3
        assert "unstable" in result.reason.lower()

    def test_file_not_found(self) -> None:
        """验证文件不存在时返回 unstable。"""
        probe = MockSizeProbe(sizes=[-1, -1, -1])
        detector = FileCompletionDetector(size_probe=probe, size_stable_count=3)
        result = detector.detect_by_size_stable("/fake/missing.bin")
        assert result.stable is False
        assert "不存在" in result.reason

    def test_stable_with_custom_count(self) -> None:
        """验证自定义稳定次数（5 次）。"""
        probe = MockSizeProbe(sizes=[200, 200, 200, 200, 200])
        detector = FileCompletionDetector(size_probe=probe, size_stable_count=5)
        result = detector.detect_by_size_stable("/fake/path.bin")
        assert result.stable is True
        assert result.observed_count == 5

    def test_stable_count_1_immediate_stable(self) -> None:
        """验证 size_stable_count=1 时首次即判定稳定。"""
        probe = MockSizeProbe(sizes=[42])
        detector = FileCompletionDetector(size_probe=probe, size_stable_count=1)
        result = detector.detect_by_size_stable("/fake/path.bin")
        assert result.stable is True
        assert result.observed_count == 1


class TestFileCompletionDetectorManifest:
    """manifest 检测策略测试（使用临时文件）。"""

    def test_valid_manifest(self, tmp_path: Path) -> None:
        """验证完整有效的 manifest 检测。"""
        data_file = tmp_path / "data.bin"
        data_content = b"hello world test data for checksum\n" * 10
        data_file.write_bytes(data_content)
        expected_checksum = hashlib.sha256(data_content).hexdigest()
        expected_size = len(data_content)

        manifest = {
            "data_path": str(data_file),
            "size_bytes": expected_size,
            "checksum": expected_checksum,
            "checksum_algorithm": "sha256",
        }
        manifest_file = tmp_path / "data.bin.manifest"
        manifest_file.write_text(json.dumps(manifest))

        detector = FileCompletionDetector()
        result = detector.detect_by_manifest(str(manifest_file))
        assert result.stable is True
        assert result.size_bytes == expected_size
        assert result.reason == "manifest_valid"

    def test_manifest_file_not_found(self) -> None:
        """验证 manifest 文件不存在时返回 unstable。"""
        detector = FileCompletionDetector()
        result = detector.detect_by_manifest("/nonexistent/manifest.json")
        assert result.stable is False
        assert "不存在" in result.reason

    def test_manifest_invalid_json(self, tmp_path: Path) -> None:
        """验证 JSON 解析失败时返回 unstable。"""
        manifest_file = tmp_path / "bad.manifest"
        manifest_file.write_text("not json {{{")
        detector = FileCompletionDetector()
        result = detector.detect_by_manifest(str(manifest_file))
        assert result.stable is False
        assert "json" in result.reason.lower() or "解析" in result.reason

    def test_manifest_missing_data_path(self, tmp_path: Path) -> None:
        """验证 manifest 缺少 data_path 时返回 unstable。"""
        manifest_file = tmp_path / "empty.manifest"
        manifest_file.write_text(json.dumps({"size_bytes": 100, "checksum": "abc"}))
        detector = FileCompletionDetector()
        result = detector.detect_by_manifest(str(manifest_file))
        assert result.stable is False
        assert "data_path" in result.reason

    def test_data_file_not_found(self, tmp_path: Path) -> None:
        """验证 manifest 引用的 data_path 文件不存在。"""
        manifest = {"data_path": str(tmp_path / "missing.bin"), "size_bytes": 100}
        manifest_file = tmp_path / "broken.manifest"
        manifest_file.write_text(json.dumps(manifest))
        detector = FileCompletionDetector()
        result = detector.detect_by_manifest(str(manifest_file))
        assert result.stable is False
        assert "不存在" in result.reason

    def test_size_mismatch(self, tmp_path: Path) -> None:
        """验证文件大小不匹配。"""
        data_file = tmp_path / "data.bin"
        data_file.write_bytes(b"hello")
        manifest = {
            "data_path": str(data_file),
            "size_bytes": 9999,
            "checksum": "abc",
        }
        manifest_file = tmp_path / "data.manifest"
        manifest_file.write_text(json.dumps(manifest))
        detector = FileCompletionDetector()
        result = detector.detect_by_manifest(str(manifest_file))
        assert result.stable is False
        assert "大小不匹配" in result.reason

    def test_checksum_mismatch(self, tmp_path: Path) -> None:
        """验证 checksum 不匹配。"""
        data_file = tmp_path / "data.bin"
        data_file.write_bytes(b"correct data")
        correct_size = len(b"correct data")
        manifest = {
            "data_path": str(data_file),
            "size_bytes": correct_size,
            "checksum": hashlib.sha256(b"wrong data").hexdigest(),
        }
        manifest_file = tmp_path / "data.manifest"
        manifest_file.write_text(json.dumps(manifest))
        detector = FileCompletionDetector()
        result = detector.detect_by_manifest(str(manifest_file))
        assert result.stable is False
        assert "checksum 不匹配" in result.reason


class TestFileCompletionDetectorDoneFlag:
    """done flag 检测策略测试（使用临时文件）。"""

    def test_done_flag_present(self, tmp_path: Path) -> None:
        """验证 .done 文件存在时判定完成。"""
        data_file = tmp_path / "rec.bin"
        data_file.write_bytes(b"some data content here")
        done_file = tmp_path / "rec.bin.done"
        done_file.write_text("done")
        detector = FileCompletionDetector()
        result = detector.detect_by_done_flag(str(data_file))
        assert result.stable is True
        assert result.reason == "done_flag_present"
        assert result.size_bytes > 0

    def test_done_flag_missing(self, tmp_path: Path) -> None:
        """验证 .done 文件不存在时判定未完成。"""
        data_file = tmp_path / "rec.bin"
        data_file.write_bytes(b"data")
        detector = FileCompletionDetector()
        result = detector.detect_by_done_flag(str(data_file))
        assert result.stable is False
        assert "done_flag" in result.reason

    def test_done_flag_one_file_not_the_other(self, tmp_path: Path) -> None:
        """验证只有特定文件的 .done 生效。"""
        file_a = tmp_path / "a.bin"
        file_b = tmp_path / "b.bin"
        file_a.write_bytes(b"a")
        file_b.write_bytes(b"b")
        (tmp_path / "a.bin.done").write_text("done")

        detector = FileCompletionDetector()
        result_a = detector.detect_by_done_flag(str(file_a))
        result_b = detector.detect_by_done_flag(str(file_b))
        assert result_a.stable is True
        assert result_b.stable is False


class TestBuildManifestFromFile:
    """build_manifest_from_file 测试。"""

    def test_build_from_existing_file(self, tmp_path: Path) -> None:
        """验证从文件构建 manifest。"""
        data_file = tmp_path / "test.bin"
        content = b"test file content for manifest building"
        data_file.write_bytes(content)
        expected_checksum = hashlib.sha256(content).hexdigest()

        detector = FileCompletionDetector()
        manifest = detector.build_manifest_from_file(str(data_file), "test_type")
        assert manifest is not None
        assert manifest.file_id == "test.bin"
        assert manifest.file_type == "test_type"
        assert manifest.path == str(data_file)
        assert manifest.size_bytes == len(content)
        assert manifest.checksum == expected_checksum
        assert manifest.checksum_algorithm == "sha256"
        assert manifest.done_flag_path == str(data_file) + ".done"

    def test_build_from_missing_file(self) -> None:
        """验证文件不存在时返回 None。"""
        detector = FileCompletionDetector()
        manifest = detector.build_manifest_from_file("/nonexistent/file.bin", "test")
        assert manifest is None


class TestOSStatSizeProbe:
    """OSStatSizeProbe 测试。"""

    def test_stat_size_returns_correct_size(self, tmp_path: Path) -> None:
        """验证 OSStatSizeProbe 正确返回文件大小。"""
        data_file = tmp_path / "real.bin"
        content = b"real file content" * 42
        data_file.write_bytes(content)
        from whale.ingest.file_ingest.detector import OSStatSizeProbe
        p = OSStatSizeProbe()
        size = p.stat_size(str(data_file))
        assert size == len(content)

    def test_stat_size_file_missing(self) -> None:
        """验证文件不存在时返回 -1。"""
        from whale.ingest.file_ingest.detector import OSStatSizeProbe
        p = OSStatSizeProbe()
        size = p.stat_size("/nonexistent/for/sure/file.bin")
        assert size == -1
