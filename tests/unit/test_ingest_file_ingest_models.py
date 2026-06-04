"""文件接入 DTO 模型单元测试。

验证 file_ingest.models 中所有 dataclass 的字段定义、默认值和
构造行为。

被验证对象：
- whale.ingest.file_ingest.models: FileIngestManifest, FileStabilityProbeResult,
  FileIngestRequest, FileIngestResult, FaultEventMetadata

测试阶段：开发期验证 (unit，无外部依赖)。
不能证明：与真实文件系统、外部服务的交互行为。
"""

from __future__ import annotations

from whale.ingest.file_ingest.models import (
    FaultEventMetadata,
    FileIngestManifest,
    FileIngestRequest,
    FileIngestResult,
    FileStabilityProbeResult,
)


class TestFileIngestManifest:
    """FileIngestManifest DTO 测试。"""

    def test_default_values(self) -> None:
        """验证默认字段值。"""
        m = FileIngestManifest(
            file_id="f-001",
            file_type="plc_high_rate_json",
            path="/data/rec.json",
        )
        assert m.file_id == "f-001"
        assert m.file_type == "plc_high_rate_json"
        assert m.path == "/data/rec.json"
        assert m.size_bytes == 0
        assert m.checksum == ""
        assert m.checksum_algorithm == "sha256"
        assert m.done_flag_path == ""
        assert isinstance(m.metadata, dict)

    def test_full_construction(self) -> None:
        """验证全字段构造。"""
        m = FileIngestManifest(
            file_id="f-002",
            file_type="fault_record_binary",
            path="/data/fault.bin",
            size_bytes=1024,
            checksum="abcdef1234567890",
            checksum_algorithm="sha256",
            created_at="2025-06-01T12:00:00Z",
            done_flag_path="/data/fault.bin.done",
            metadata={"source": "plc-1"},
        )
        assert m.file_id == "f-002"
        assert m.size_bytes == 1024
        assert m.checksum == "abcdef1234567890"
        assert m.checksum_algorithm == "sha256"
        assert m.created_at == "2025-06-01T12:00:00Z"
        assert m.done_flag_path == "/data/fault.bin.done"
        assert m.metadata["source"] == "plc-1"

    def test_created_at_default_is_iso_format(self) -> None:
        """验证 created_at 默认值为 ISO 格式时间戳。"""
        m = FileIngestManifest(
            file_id="f-003",
            file_type="test",
            path="/tmp/test.dat",
        )
        assert "T" in m.created_at
        assert "Z" in m.created_at or "+" in m.created_at


class TestFileStabilityProbeResult:
    """FileStabilityProbeResult DTO 测试。"""

    def test_default_values(self) -> None:
        """验证默认字段值。"""
        r = FileStabilityProbeResult(path="/data/test.bin")
        assert r.path == "/data/test.bin"
        assert r.stable is False
        assert r.size_bytes == 0
        assert r.observed_count == 0
        assert r.reason == ""

    def test_stable_result(self) -> None:
        """验证稳定状态的探测结果。"""
        r = FileStabilityProbeResult(
            path="/data/test.bin",
            stable=True,
            size_bytes=2048,
            observed_count=3,
            reason="size_stable",
        )
        assert r.stable is True
        assert r.size_bytes == 2048
        assert r.observed_count == 3
        assert r.reason == "size_stable"

    def test_unstable_result(self) -> None:
        """验证不稳定状态的探测结果。"""
        r = FileStabilityProbeResult(
            path="/data/missing.bin",
            stable=False,
            size_bytes=0,
            observed_count=1,
            reason="文件不存在: /data/missing.bin",
        )
        assert r.stable is False
        assert r.reason == "文件不存在: /data/missing.bin"


class TestFileIngestRequest:
    """FileIngestRequest DTO 测试。"""

    def test_default_values(self) -> None:
        """验证默认字段值。"""
        req = FileIngestRequest()
        assert req.manifest_path == ""
        assert req.data_path == ""
        assert req.file_type == ""
        assert req.source_id == ""
        assert req.asset_id == ""
        assert req.device_id == ""
        assert req.trace_id == ""

    def test_with_manifest_path(self) -> None:
        """验证通过 manifest_path 构造。"""
        req = FileIngestRequest(
            manifest_path="/data/rec.json.manifest",
            file_type="plc_high_rate_json",
            source_id="plc-1",
            trace_id="trace-001",
        )
        assert req.manifest_path == "/data/rec.json.manifest"
        assert req.data_path == ""
        assert req.file_type == "plc_high_rate_json"

    def test_with_data_path(self) -> None:
        """验证通过 data_path 直接构造。"""
        req = FileIngestRequest(
            data_path="/data/fault.bin",
            file_type="fault_record_binary",
            source_id="plc-1",
            asset_id="asset-a",
            device_id="dev-a",
        )
        assert req.data_path == "/data/fault.bin"
        assert req.asset_id == "asset-a"
        assert req.device_id == "dev-a"


class TestFileIngestResult:
    """FileIngestResult DTO 测试。"""

    def test_default_values(self) -> None:
        """验证默认字段值。"""
        r = FileIngestResult()
        assert r.accepted is False
        assert r.raw_batch_id == ""
        assert r.decoded_signal_count == 0
        assert r.waveform_count == 0
        assert r.fault_event_count == 0
        assert r.reason == ""
        assert r.errors == []

    def test_success_result(self) -> None:
        """验证成功结果。"""
        r = FileIngestResult(
            accepted=True,
            raw_batch_id="file-abc123",
            decoded_signal_count=100,
            waveform_count=5,
            fault_event_count=1,
            reason="接入完成: 100 signals, 5 waveforms, 1 fault_events",
        )
        assert r.accepted is True
        assert r.decoded_signal_count == 100
        assert r.waveform_count == 5

    def test_add_error(self) -> None:
        """验证 add_error 追加错误信息。"""
        r = FileIngestResult()
        r.add_error("decoder failed")
        r.add_error("waveform write failed")
        assert len(r.errors) == 2
        assert "decoder failed" in r.errors
        assert "waveform write failed" in r.errors

    def test_partial_success_with_errors(self) -> None:
        """验证 partial 状态：accepted 和 errors 可共存。"""
        r = FileIngestResult(
            accepted=True,
            raw_batch_id="file-abc",
            decoded_signal_count=50,
            reason="raw_archive 写入成功 (有部分错误)",
        )
        r.add_error("waveform write failed: timed out")
        assert r.accepted is True
        assert len(r.errors) == 1


class TestFaultEventMetadata:
    """FaultEventMetadata DTO 测试。"""

    def test_minimal_construction(self) -> None:
        """验证最小字段构造。"""
        e = FaultEventMetadata(event_id="flt-001")
        assert e.event_id == "flt-001"
        assert e.source_id == ""
        assert e.event_type == ""
        assert e.severity == "WARNING"
        assert e.channel_count == 0
        assert e.sample_rate_hz == 0.0

    def test_full_construction(self) -> None:
        """验证全字段构造。"""
        e = FaultEventMetadata(
            event_id="flt-002",
            source_id="plc-1",
            asset_id="asset-a",
            device_id="dev-a",
            event_type="TRIP",
            started_at="2025-06-01T12:00:00Z",
            ended_at="2025-06-01T12:00:05Z",
            sample_rate_hz=1200.0,
            channel_count=8,
            raw_batch_id="file-abc123",
            severity="CRITICAL",
            metadata={"fault_code": 101},
        )
        assert e.event_id == "flt-002"
        assert e.event_type == "TRIP"
        assert e.severity == "CRITICAL"
        assert e.channel_count == 8
        assert e.sample_rate_hz == 1200.0
        assert e.raw_batch_id == "file-abc123"
        assert e.metadata["fault_code"] == 101
