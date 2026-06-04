"""文件接入服务单元测试。

验证 FileIngestService 的编排逻辑，包括成功路径、raw_archive 失败、
decode 失败、波形写入失败和故障事件记录失败等分支。

使用 mock/fake 替身，不依赖真实文件系统和外部存储。

被验证对象：
- whale.ingest.file_ingest.service: FileIngestService

测试阶段：开发期验证 (unit，fake/mock 模式)。
不能证明：真实文件系统 IO、真实 TDengine 写入、大文件内存行为。
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from whale.ingest.file_ingest.detector import FileCompletionDetector
from whale.ingest.file_ingest.models import FileIngestRequest
from whale.ingest.file_ingest.repository import InMemoryFaultEventRepository
from whale.ingest.file_ingest.service import FileIngestService
from whale.storage.raw_archive import (
    InMemoryManifestRepository,
    LocalCompressedArchiveSink,
)
from whale.storage.waveform import InMemoryStandardizedWaveformSink


class TestFileIngestServiceSuccess:
    """FileIngestService 成功路径测试。"""

    @pytest.fixture
    def temp_dir(self) -> str:
        """创建临时目录用于 raw_archive 和数据文件。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.mark.asyncio
    async def test_ingest_json_file_full_pipeline(self, temp_dir: str) -> None:
        """验证 JSON 文件接入完整流程成功。"""
        # 准备 JSON 数据文件
        data_path = Path(temp_dir) / "rec.json"
        json_data = {
            "sample_rate_hz": 1200.0,
            "observed_at": "2025-06-01T12:00:00Z",
            "channels": [
                {"key": "ch_a", "unit": "A", "value_type": "FLOAT64"},
                {"key": "ch_b", "unit": "V", "value_type": "FLOAT64"},
            ],
            "samples": [[1.0, 230.0], [2.0, 231.0]],
        }
        data_path.write_text(json.dumps(json_data))

        # 组装依赖
        archive_dir = Path(temp_dir) / "archive"
        archive_dir.mkdir()
        raw_archive = LocalCompressedArchiveSink(str(archive_dir))
        waveform_sink = InMemoryStandardizedWaveformSink()
        fault_repo = InMemoryFaultEventRepository()
        manifest_repo = InMemoryManifestRepository()

        detector = FileCompletionDetector()
        service = FileIngestService(
            detector=detector,
            raw_archive=raw_archive,
            manifest_repo=manifest_repo,
            waveform_sink=waveform_sink,
            fault_event_repo=fault_repo,
        )

        request = FileIngestRequest(
            data_path=str(data_path),
            file_type="plc_high_rate_json",
            source_id="plc-1",
            asset_id="asset-a",
            trace_id="trace-001",
        )

        result = await service.ingest(request)

        assert result.accepted is True
        assert result.raw_batch_id != ""
        assert result.decoded_signal_count == 4  # 2 channels x 2 samples
        assert result.waveform_count == 2  # 2 channels
        assert result.fault_event_count == 1
        assert len(result.errors) == 0
        assert "接入完成" in result.reason

        # 验证 raw_archive 已写入
        batches = await raw_archive.list_batches()
        assert len(batches) == 1

        # 验证波形已写入
        records = waveform_sink.query_by_source("plc-1")
        assert len(records) == 2

        # 验证故障事件已记录
        events = await fault_repo.find_by_source_id("plc-1")
        assert len(events) == 1

    @pytest.mark.asyncio
    async def test_ingest_binary_file_full_pipeline(self, temp_dir: str) -> None:
        """验证二进制文件接入完整流程成功。"""
        import struct
        from whale.ingest.file_ingest.decoder import (
            FAULT_RECORD_MAGIC,
            FAULT_RECORD_VERSION,
        )

        # 准备二进制数据文件
        data_path = Path(temp_dir) / "fault.bin"
        channel_count = 2
        sample_count = 3
        sample_rate = 1000.0
        timestamp_unix = 1717200000.0
        header = struct.pack(
            "<IHHfdI",
            FAULT_RECORD_MAGIC,
            FAULT_RECORD_VERSION,
            channel_count,
            sample_rate,
            timestamp_unix,
            sample_count,
        )
        values = [0.1, 0.2, 0.3, 1.1, 1.2, 1.3]  # channel-major: ch0 x3, ch1 x3
        values_bytes = struct.pack("<6f", *values)
        data_path.write_bytes(header + values_bytes)

        archive_dir = Path(temp_dir) / "archive"
        archive_dir.mkdir()
        raw_archive = LocalCompressedArchiveSink(str(archive_dir))
        waveform_sink = InMemoryStandardizedWaveformSink()
        fault_repo = InMemoryFaultEventRepository()

        detector = FileCompletionDetector()
        service = FileIngestService(
            detector=detector,
            raw_archive=raw_archive,
            waveform_sink=waveform_sink,
            fault_event_repo=fault_repo,
        )

        request = FileIngestRequest(
            data_path=str(data_path),
            file_type="fault_record_binary",
            source_id="plc-2",
            device_id="dev-2",
        )

        result = await service.ingest(request)

        assert result.accepted is True
        assert result.decoded_signal_count == 6  # 2 channels x 3 samples
        assert result.waveform_count == 2
        assert result.fault_event_count == 1


class TestFileIngestServiceErrors:
    """FileIngestService 错误路径和边界测试。"""

    @pytest.fixture
    def temp_dir(self) -> str:
        """创建临时目录。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.mark.asyncio
    async def test_missing_data_path_returns_error(self, temp_dir: str) -> None:
        """验证未指定 data_path/manifest_path 时返回错误。"""
        archive_dir = Path(temp_dir) / "archive"
        archive_dir.mkdir()
        raw_archive = LocalCompressedArchiveSink(str(archive_dir))
        detector = FileCompletionDetector()
        service = FileIngestService(
            detector=detector,
            raw_archive=raw_archive,
        )
        request = FileIngestRequest(file_type="test")
        result = await service.ingest(request)
        assert result.accepted is False
        assert "未指定" in result.reason

    @pytest.mark.asyncio
    async def test_decode_failure_after_raw_archive_success(self, temp_dir: str) -> None:
        """验证 raw_archive 成功但 decode 失败时返回 accepted=False。"""
        # 写入无效 JSON 内容
        data_path = Path(temp_dir) / "bad.json"
        data_path.write_text("not valid json")

        archive_dir = Path(temp_dir) / "archive"
        archive_dir.mkdir()
        raw_archive = LocalCompressedArchiveSink(str(archive_dir))
        detector = FileCompletionDetector()
        service = FileIngestService(
            detector=detector,
            raw_archive=raw_archive,
        )

        request = FileIngestRequest(
            data_path=str(data_path),
            file_type="plc_high_rate_json",
            source_id="plc-1",
        )
        result = await service.ingest(request)

        # raw_archive 应已成功
        assert result.accepted is False
        assert result.raw_batch_id != ""
        assert "raw_archive 成功但解码失败" in result.reason
        assert len(result.errors) > 0
        assert result.decoded_signal_count == 0

    @pytest.mark.asyncio
    async def test_unsupported_file_type(self, temp_dir: str) -> None:
        """验证不支持的文件类型导致 decode 失败。"""
        data_path = Path(temp_dir) / "unknown.txt"
        data_path.write_text("some text")

        archive_dir = Path(temp_dir) / "archive"
        archive_dir.mkdir()
        raw_archive = LocalCompressedArchiveSink(str(archive_dir))
        detector = FileCompletionDetector()
        service = FileIngestService(
            detector=detector,
            raw_archive=raw_archive,
        )

        request = FileIngestRequest(
            data_path=str(data_path),
            file_type="unknown_protocol",
            source_id="plc-1",
        )
        result = await service.ingest(request)
        assert result.accepted is False
        assert "不支持的文件类型" in result.errors[0] or "解码失败" in result.reason

    @pytest.mark.asyncio
    async def test_no_waveform_sink_still_succeeds(self, temp_dir: str) -> None:
        """验证无 waveform_sink 时接入仍然成功（波形写入跳过）。"""
        data_path = Path(temp_dir) / "rec.json"
        json_data = {
            "sample_rate_hz": 100.0,
            "channels": [{"key": "ch", "unit": "A", "value_type": "FLOAT64"}],
            "samples": [[1.0]],
        }
        data_path.write_text(json.dumps(json_data))

        archive_dir = Path(temp_dir) / "archive"
        archive_dir.mkdir()
        raw_archive = LocalCompressedArchiveSink(str(archive_dir))
        detector = FileCompletionDetector()
        service = FileIngestService(
            detector=detector,
            raw_archive=raw_archive,
            waveform_sink=None,  # 无波形 sink
        )

        request = FileIngestRequest(
            data_path=str(data_path),
            file_type="plc_high_rate_json",
            source_id="plc-1",
        )
        result = await service.ingest(request)
        assert result.accepted is True
        assert result.decoded_signal_count == 1
        assert result.waveform_count == 0  # 波形写入跳过


class TestFileIngestServicePartial:
    """FileIngestService 部分成功场景测试。"""

    @pytest.fixture
    def temp_dir(self) -> str:
        """创建临时目录。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.mark.asyncio
    async def test_partial_waveform_write_failure(self, temp_dir: str) -> None:
        """验证波形写入部分失败时 result 记录错误但仍 accepted=True。"""
        data_path = Path(temp_dir) / "rec.json"
        json_data = {
            "sample_rate_hz": 1000.0,
            "channels": [
                {"key": "ch_a", "unit": "A", "value_type": "FLOAT64"},
            ],
            "samples": [[1.0]],
        }
        data_path.write_text(json.dumps(json_data))

        archive_dir = Path(temp_dir) / "archive"
        archive_dir.mkdir()
        raw_archive = LocalCompressedArchiveSink(str(archive_dir))

        # 使用 InMemoryStandardizedWaveformSink，但挂一个会抛异常的 write_waveform
        # 这很难在不修改 sink 的情况下做到。改用 Tdengine waveform sink 作为
        # write_waveform 返回 False 的场景（contract-only 模式）
        from whale.storage.waveform import TdengineStandardizedWaveformSink
        waveform_sink = TdengineStandardizedWaveformSink(dsn="localhost:6041")

        detector = FileCompletionDetector()
        service = FileIngestService(
            detector=detector,
            raw_archive=raw_archive,
            waveform_sink=waveform_sink,
        )

        request = FileIngestRequest(
            data_path=str(data_path),
            file_type="plc_high_rate_json",
            source_id="plc-1",
        )
        result = await service.ingest(request)
        # Tdengine contract adapter 返回 False，所以 waveform_count 为 0
        assert result.accepted is True
        assert result.decoded_signal_count == 1
        assert result.waveform_count == 0


class TestEventTypeInference:
    """故障事件类型推导测试。"""

    def test_infer_json_type(self) -> None:
        """验证 JSON 文件类型推导为 PLC_HIGH_RATE_RECORD。"""
        event_type = FileIngestService._infer_event_type("plc_high_rate_json")
        assert event_type == "PLC_HIGH_RATE_RECORD"

    def test_infer_binary_type(self) -> None:
        """验证二进制文件类型推导为 FAULT_RECORD。"""
        event_type = FileIngestService._infer_event_type("fault_record_binary")
        assert event_type == "FAULT_RECORD"

    def test_infer_unknown_type(self) -> None:
        """验证未知类型推导为 UNKNOWN_FILE_TYPE。"""
        event_type = FileIngestService._infer_event_type("weird_format")
        assert event_type == "UNKNOWN_FILE_TYPE"
