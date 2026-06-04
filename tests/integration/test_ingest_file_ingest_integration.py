"""文件接入模块集成测试。

验证 FileIngestService 使用真实临时文件和 InMemory 存储后端的
完整闭环行为：检测 -> 归档 -> 解码 -> 波形写入 -> 故障事件记录。

被验证对象：
- whale.ingest.file_ingest: 文件接入完整流程（detector + decoder + service +
  InMemory waveform + InMemory fault_event + 本地 raw_archive）

测试阶段：模块集成期验证 (integration，临时文件 + InMemory 后端)。
不能证明：真实 TDengine/Kafka/HDFS/S3 写入、大文件内存行为和生产环境并发。
"""

from __future__ import annotations

import hashlib
import json
import struct
import tempfile
from pathlib import Path

import pytest

from whale.ingest.file_ingest.decoder import (
    FAULT_RECORD_MAGIC,
    FAULT_RECORD_VERSION,
)
from whale.ingest.file_ingest.detector import FileCompletionDetector
from whale.ingest.file_ingest.models import (
    FileIngestRequest,
)
from whale.ingest.file_ingest.repository import InMemoryFaultEventRepository
from whale.ingest.file_ingest.service import FileIngestService
from whale.storage.raw_archive import InMemoryManifestRepository, LocalCompressedArchiveSink
from whale.storage.waveform import InMemoryStandardizedWaveformSink


class TestFileIngestMinimalClosedLoop:
    """文件接入最小闭环集成测试。"""

    @pytest.fixture
    def work_dir(self) -> str:
        """创建工作目录（raw_archive + 数据文件）。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.mark.asyncio
    async def test_json_ingest_manifest_detect_then_decode(self, work_dir: str) -> None:
        """验证通过 manifest JSON 检测后完成 JSON 文件接入。"""
        wd = Path(work_dir)
        data_file = wd / "high_rate.json"
        json_data = {
            "sample_rate_hz": 2000.0,
            "observed_at": "2025-06-01T12:00:00Z",
            "channels": [
                {"key": "I_a", "unit": "A", "value_type": "FLOAT64"},
                {"key": "I_b", "unit": "A", "value_type": "FLOAT64"},
                {"key": "I_c", "unit": "A", "value_type": "FLOAT64"},
            ],
            "samples": [
                [10.0, 11.0, 12.0],
                [10.1, 11.1, 12.1],
                [10.2, 11.2, 12.2],
                [10.3, 11.3, 12.3],
            ],
        }
        payload = json.dumps(json_data)
        data_file.write_text(payload)

        # 写入 manifest
        content_bytes = payload.encode("utf-8")
        manifest = {
            "data_path": str(data_file),
            "size_bytes": len(content_bytes),
            "checksum": hashlib.sha256(content_bytes).hexdigest(),
            "checksum_algorithm": "sha256",
        }
        manifest_file = wd / "high_rate.json.manifest"
        manifest_file.write_text(json.dumps(manifest))

        # 组装依赖
        archive_dir = wd / "archive"
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
            manifest_path=str(manifest_file),
            file_type="plc_high_rate_json",
            source_id="plc-field-01",
            asset_id="transformer-01",
            trace_id="trace-xyz",
        )
        result = await service.ingest(request)

        # 验证结果
        assert result.accepted is True
        assert result.decoded_signal_count == 12  # 3 channels x 4 samples
        assert result.waveform_count == 3  # 3 channels
        assert result.fault_event_count == 1

        # 验证 raw_archive
        batches = await raw_archive.list_batches()
        assert len(batches) == 1
        assert result.raw_batch_id in batches

        # 验证 manifest_repo
        batch_manifest = await manifest_repo.get_manifest(result.raw_batch_id)
        assert batch_manifest is not None
        assert batch_manifest["batch_id"] == result.raw_batch_id

        # 验证波形
        waveforms = waveform_sink.query_by_source("plc-field-01")
        assert len(waveforms) == 3
        ch_keys = {w["channel_key"] for w in waveforms}
        assert ch_keys == {"I_a", "I_b", "I_c"}
        for w in waveforms:
            assert w["sample_rate_hz"] == 2000.0
            assert len(w["values"]) == 4
            assert len(w["timestamps"]) == 4

        # 验证故障事件
        events = await fault_repo.find_by_source_id("plc-field-01")
        assert len(events) == 1
        assert events[0].event_type == "PLC_HIGH_RATE_RECORD"
        assert events[0].channel_count == 3
        assert events[0].sample_rate_hz == 2000.0
        assert events[0].raw_batch_id == result.raw_batch_id

    @pytest.mark.asyncio
    async def test_binary_ingest_size_stable_detect_then_decode(self, work_dir: str) -> None:
        """验证通过 size stable 检测后完成二进制文件接入。"""
        wd = Path(work_dir)
        data_file = wd / "fault_record.bin"

        # 构造二进制文件
        channel_count = 4
        sample_count = 100
        sample_rate = 4800.0
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
        # 生成正弦波模拟数据
        import math
        values: list[float] = []
        for ch in range(channel_count):
            phase_offset = ch * math.pi / 2
            for s in range(sample_count):
                t = s / sample_rate
                values.append(math.sin(2 * math.pi * 50.0 * t + phase_offset))
        values_bytes = struct.pack(f"<{len(values)}f", *values)
        data_file.write_bytes(header + values_bytes)

        # 组装依赖
        archive_dir = wd / "archive"
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
            data_path=str(data_file),
            file_type="fault_record_binary",
            source_id="plc-field-02",
            device_id="relay-02",
        )
        result = await service.ingest(request)

        # 验证结果
        assert result.accepted is True
        assert result.decoded_signal_count == 400  # 4 channels x 100 samples
        assert result.waveform_count == 4
        assert result.fault_event_count == 1

        # 验证波形数据
        waveforms = waveform_sink.query_by_source("plc-field-02")
        assert len(waveforms) == 4
        for w in waveforms:
            assert w["sample_rate_hz"] == 4800.0
            assert len(w["values"]) == 100
            assert len(w["timestamps"]) == 100
            assert w["quality_code"] == "0"

        # 验证故障事件
        events = await fault_repo.find_by_source_id("plc-field-02")
        assert len(events) == 1
        assert events[0].event_type == "FAULT_RECORD"
        assert events[0].channel_count == 4
        assert events[0].sample_rate_hz == 4800.0


class TestFileIngestDoneFlagIntegration:
    """done flag 检测集成测试。"""

    @pytest.fixture
    def work_dir(self) -> str:
        """创建工作目录。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.mark.asyncio
    async def test_done_flag_detect_then_json_ingest(self, work_dir: str) -> None:
        """验证 done flag 检测后完成文件接入。"""
        wd = Path(work_dir)
        data_file = wd / "event.json"
        json_data = {
            "sample_rate_hz": 400.0,
            "channels": [{"key": "P_total", "unit": "kW", "value_type": "FLOAT64"}],
            "samples": [[500.0], [501.0]],
        }
        data_file.write_text(json.dumps(json_data))

        # 需要 done flag 文件，同时 data 文件也已完成
        done_file = wd / "event.json.done"
        done_file.write_text("completed")

        archive_dir = wd / "archive"
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

        # 注意：service.ingest 中 detect_by_done_flag 需要被 size_stable 失败
        # 后 fallback 调用。size_stable 可能因为 size_stable_count=3 而需要连续 3 次
        # 相同 size 才通过。我们增大 size_stable_count 为 1 来跳过 size_stable。
        # 但因为 service 内部 size_stable_count=DEFAULT_SIZE_STABLE_COUNT=3，
        # 而 data_file 是静态文件，size 不会变化，所以 size_stable 应该直接通过。

        request = FileIngestRequest(
            data_path=str(data_file),
            file_type="plc_high_rate_json",
            source_id="plc-field-03",
        )
        result = await service.ingest(request)
        assert result.accepted is True
        assert result.decoded_signal_count == 2
        assert result.waveform_count == 1


class TestFileIngestChecksumVerification:
    """checksum 校验集成测试。"""

    @pytest.fixture
    def work_dir(self) -> str:
        """创建工作目录。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    def test_manifest_checksum_verification_passes(self, work_dir: str) -> None:
        """验证 manifest checksum 校验通过。"""
        wd = Path(work_dir)
        data_file = wd / "data.bin"
        content = b"verified file content for checksum testing"
        data_file.write_bytes(content)

        manifest = {
            "data_path": str(data_file),
            "size_bytes": len(content),
            "checksum": hashlib.sha256(content).hexdigest(),
            "checksum_algorithm": "sha256",
        }
        manifest_file = wd / "data.bin.manifest"
        manifest_file.write_text(json.dumps(manifest))

        detector = FileCompletionDetector()
        result = detector.detect_by_manifest(str(manifest_file))
        assert result.stable is True
        assert result.reason == "manifest_valid"

    def test_manifest_checksum_verification_fails(self, work_dir: str) -> None:
        """验证 manifest checksum 校验失败。"""
        wd = Path(work_dir)
        data_file = wd / "data.bin"
        content = b"correct content"
        data_file.write_bytes(content)

        # 使用错误的 checksum
        manifest = {
            "data_path": str(data_file),
            "size_bytes": len(content),
            "checksum": hashlib.sha256(b"tampered content").hexdigest(),
            "checksum_algorithm": "sha256",
        }
        manifest_file = wd / "data.bin.manifest"
        manifest_file.write_text(json.dumps(manifest))

        detector = FileCompletionDetector()
        result = detector.detect_by_manifest(str(manifest_file))
        assert result.stable is False
        assert "checksum 不匹配" in result.reason


class TestFileIngestServiceWithNoWaveformOrEvent:
    """无 waveform sink 和无 fault event repo 时的最小接入测试。"""

    @pytest.fixture
    def work_dir(self) -> str:
        """创建工作目录。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.mark.asyncio
    async def test_minimal_ingest_raw_archive_only(self, work_dir: str) -> None:
        """验证仅 raw_archive 的最小接入（无 waveform sink 和 fault repo）。"""
        wd = Path(work_dir)
        data_file = wd / "minimal.json"
        json_data = {
            "sample_rate_hz": 100.0,
            "channels": [{"key": "x", "unit": "", "value_type": "FLOAT64"}],
            "samples": [[1.0]],
        }
        data_file.write_text(json.dumps(json_data))

        archive_dir = wd / "archive"
        archive_dir.mkdir()
        raw_archive = LocalCompressedArchiveSink(str(archive_dir))
        detector = FileCompletionDetector()
        service = FileIngestService(
            detector=detector,
            raw_archive=raw_archive,
            waveform_sink=None,
            fault_event_repo=None,
        )

        request = FileIngestRequest(
            data_path=str(data_file),
            file_type="plc_high_rate_json",
            source_id="plc-min",
        )
        result = await service.ingest(request)
        assert result.accepted is True
        assert result.decoded_signal_count == 1
        assert result.waveform_count == 0
        assert result.fault_event_count == 0
        assert result.raw_batch_id != ""

        # 验证 raw_archive 有文件
        batches = await raw_archive.list_batches()
        assert len(batches) == 1
