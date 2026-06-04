"""文件接入解码器单元测试。

验证 PlcHighRateJsonDecoder 和 FaultRecordBinaryDecoder 的解码行为，
包括正常解码、边界条件和错误处理。

被验证对象：
- whale.ingest.file_ingest.decoder: PlcHighRateJsonDecoder, FaultRecordBinaryDecoder

测试阶段：开发期验证 (unit，无外部依赖)。
不能证明：超大文件、真实设备二进制格式兼容性。
"""

from __future__ import annotations

import json
import struct

import pytest

from whale.ingest.file_ingest.decoder import (
    FAULT_RECORD_HEADER_SIZE,
    FAULT_RECORD_MAGIC,
    FAULT_RECORD_VERSION,
    FaultRecordBinaryDecoder,
    PlcHighRateJsonDecoder,
)


class TestPlcHighRateJsonDecoder:
    """PlcHighRateJsonDecoder 单元测试。"""

    def _make_json_payload(
        self,
        sample_rate_hz: float = 1200.0,
        channels: list[dict] | None = None,
        samples: list[list] | None = None,
        observed_at: str = "2025-06-01T12:00:00Z",
    ) -> str:
        """构造标准测试 JSON 载荷。"""
        if channels is None:
            channels = [
                {"key": "MMXU1.A.instMag.f", "unit": "A", "value_type": "FLOAT64"},
                {"key": "MMXU1.PhV.instMag.f", "unit": "V", "value_type": "FLOAT64"},
            ]
        if samples is None:
            samples = [[5.1, 230.0], [5.2, 230.1], [5.3, 230.2]]
        return json.dumps({
            "sample_rate_hz": sample_rate_hz,
            "observed_at": observed_at,
            "channels": channels,
            "samples": samples,
        })

    def test_decode_basic(self) -> None:
        """验证基本 JSON 解码为 DecodedSignal 和 Waveform。"""
        payload = self._make_json_payload()
        decoder = PlcHighRateJsonDecoder()
        signals, waveforms = decoder.decode(payload, source_id="plc-1")

        # 2 channels x 3 samples = 6 decoded signals
        assert len(signals) == 6
        # 2 channels = 2 waveforms
        assert len(waveforms) == 2

        # 验证第一个 waveform
        wf0 = waveforms[0]
        assert wf0.variable_key == "MMXU1.A.instMag.f"
        assert wf0.node_key == "plc-1"
        assert wf0.sample_rate_hz == 1200.0
        assert len(wf0.values) == 3
        assert wf0.values == [5.1, 5.2, 5.3]

    def test_decode_bytes_content(self) -> None:
        """验证接受 bytes 类型的 JSON 内容。"""
        payload_str = self._make_json_payload()
        payload_bytes = payload_str.encode("utf-8")
        decoder = PlcHighRateJsonDecoder()
        signals, waveforms = decoder.decode(payload_bytes, source_id="plc-1")
        assert len(signals) == 6
        assert len(waveforms) == 2

    def test_decode_single_channel(self) -> None:
        """验证单通道解码。"""
        payload = self._make_json_payload(
            channels=[{"key": "ch_a", "unit": "kW", "value_type": "FLOAT64"}],
            samples=[[100.0], [101.0], [102.0]],
        )
        decoder = PlcHighRateJsonDecoder()
        signals, waveforms = decoder.decode(payload, source_id="plc-1")
        assert len(signals) == 3
        assert len(waveforms) == 1
        assert waveforms[0].variable_key == "ch_a"
        assert waveforms[0].values == [100.0, 101.0, 102.0]

    def test_decode_empty_channels(self) -> None:
        """验证空 channels 返回空列表。"""
        payload = self._make_json_payload(channels=[], samples=[])
        decoder = PlcHighRateJsonDecoder()
        signals, waveforms = decoder.decode(payload)
        assert len(signals) == 0
        assert len(waveforms) == 0

    def test_decode_descriptor_key_present(self) -> None:
        """验证输出的 DecodedSignal 包含正确的 descriptor_key。"""
        payload = self._make_json_payload(
            channels=[{"key": "my.descriptor.key", "unit": "C", "value_type": "FLOAT64"}],
            samples=[[25.0]],
        )
        decoder = PlcHighRateJsonDecoder()
        signals, _ = decoder.decode(payload, source_id="plc-1")
        assert len(signals) == 1
        assert signals[0].descriptor_key == "my.descriptor.key"
        assert signals[0].variable_key == "my.descriptor.key"
        assert signals[0].raw_value == 25.0

    def test_decode_preserves_quality_code(self) -> None:
        """验证输出 signal 的 quality_code 为默认值 0。"""
        payload = self._make_json_payload(
            channels=[{"key": "ch", "unit": "", "value_type": "FLOAT64"}],
            samples=[[1.0]],
        )
        decoder = PlcHighRateJsonDecoder()
        signals, _ = decoder.decode(payload)
        assert signals[0].quality_code == "0"

    def test_invalid_json(self) -> None:
        """验证无效 JSON 抛出异常（由 json 模块抛出）。"""
        decoder = PlcHighRateJsonDecoder()
        with pytest.raises((json.JSONDecodeError, ValueError, TypeError)):
            decoder.decode("not valid json {{{")

    def test_missing_fields(self) -> None:
        """验证缺少 channels/samples 时返回空列表。"""
        decoder = PlcHighRateJsonDecoder()
        signals, waveforms = decoder.decode('{"sample_rate_hz": 1000}')
        assert len(signals) == 0
        assert len(waveforms) == 0


class TestFaultRecordBinaryDecoder:
    """FaultRecordBinaryDecoder 单元测试。"""

    def _make_binary_payload(
        self,
        channel_count: int = 2,
        sample_count: int = 5,
        sample_rate: float = 1000.0,
        timestamp_unix: float = 1717200000.0,
        magic: int = FAULT_RECORD_MAGIC,
        version: int = FAULT_RECORD_VERSION,
        values: list[float] | None = None,
    ) -> bytes:
        """构造标准测试二进制载荷。

        header: magic(4) + version(2) + channel_count(2) + sample_rate(4)
                + timestamp(8) + sample_count(4) = 24 bytes
        values: channel_count * sample_count * 4 bytes (float32 LE)
        """
        header = struct.pack(
            "<IHHfdI",
            magic,
            version,
            channel_count,
            sample_rate,
            timestamp_unix,
            sample_count,
        )
        total_samples = channel_count * sample_count
        if values is None:
            values = [float(i * 0.1) for i in range(total_samples)]
        values_bytes = struct.pack(f"<{len(values)}f", *values)
        return header + values_bytes

    def test_decode_basic(self) -> None:
        """验证基本二进制解码。"""
        payload = self._make_binary_payload(channel_count=2, sample_count=3)
        decoder = FaultRecordBinaryDecoder(default_source_id="plc-1")
        signals, waveforms = decoder.decode(payload)

        # 2 channels x 3 samples = 6 decoded signals
        assert len(signals) == 6
        # 2 channels = 2 waveforms
        assert len(waveforms) == 2

        # 验证第一个 waveform
        wf0 = waveforms[0]
        assert wf0.variable_key == "ch_0"
        assert wf0.node_key == "plc-1"
        assert wf0.sample_rate_hz == 1000.0
        assert len(wf0.values) == 3

        # 验证第二个 waveform
        wf1 = waveforms[1]
        assert wf1.variable_key == "ch_1"

    def test_decode_with_explicit_source_id(self) -> None:
        """验证显式 source_id 覆盖 default_source_id。"""
        payload = self._make_binary_payload(channel_count=1, sample_count=2)
        decoder = FaultRecordBinaryDecoder(default_source_id="default-src")
        _, waveforms = decoder.decode(payload, source_id="explicit-src")
        assert waveforms[0].node_key == "explicit-src"

    def test_decode_fallback_to_default_source(self) -> None:
        """验证无显式 source_id 时使用 default_source_id。"""
        payload = self._make_binary_payload(channel_count=1, sample_count=2)
        decoder = FaultRecordBinaryDecoder(default_source_id="default-src")
        _, waveforms = decoder.decode(payload)
        assert waveforms[0].node_key == "default-src"

    def test_magic_mismatch(self) -> None:
        """验证 magic 不匹配时返回空列表。"""
        payload = self._make_binary_payload(magic=0xDEADBEEF)
        decoder = FaultRecordBinaryDecoder()
        signals, waveforms = decoder.decode(payload)
        assert len(signals) == 0
        assert len(waveforms) == 0

    def test_version_mismatch(self) -> None:
        """验证 version 不匹配时返回空列表。"""
        payload = self._make_binary_payload(version=99)
        decoder = FaultRecordBinaryDecoder()
        signals, waveforms = decoder.decode(payload)
        assert len(signals) == 0
        assert len(waveforms) == 0

    def test_too_small_content(self) -> None:
        """验证内容小于 header 大小时返回空列表。"""
        payload = b"short"
        decoder = FaultRecordBinaryDecoder()
        signals, waveforms = decoder.decode(payload)
        assert len(signals) == 0

    def test_incomplete_values_data(self) -> None:
        """验证 values 数据不完整时返回空列表。"""
        # 构造 header 后在 values 区截断
        payload = self._make_binary_payload(channel_count=3, sample_count=10)
        truncated = payload[:FAULT_RECORD_HEADER_SIZE + 10]  # 截断 values
        decoder = FaultRecordBinaryDecoder()
        signals, waveforms = decoder.decode(truncated)
        assert len(signals) == 0

    def test_descriptor_key_present(self) -> None:
        """验证输出的 DecodedSignal 包含正确的 descriptor_key。"""
        payload = self._make_binary_payload(channel_count=1, sample_count=1, values=[42.0])
        decoder = FaultRecordBinaryDecoder()
        signals, _ = decoder.decode(payload, source_id="plc-1")
        assert signals[0].descriptor_key == "ch_0"
        assert signals[0].variable_key == "ch_0"
        assert signals[0].raw_value == 42.0

    def test_quality_code_default(self) -> None:
        """验证输出 signal 的 quality_code 为默认值 0。"""
        payload = self._make_binary_payload(channel_count=1, sample_count=1, values=[1.0])
        decoder = FaultRecordBinaryDecoder()
        signals, _ = decoder.decode(payload)
        assert signals[0].quality_code == "0"

    def test_timestamps_are_iso_format(self) -> None:
        """验证 timestamps 是 ISO 格式字符串。"""
        payload = self._make_binary_payload(channel_count=1, sample_count=2)
        decoder = FaultRecordBinaryDecoder()
        _, waveforms = decoder.decode(payload)
        ts = waveforms[0].timestamps
        assert len(ts) == 2
        assert "T" in ts[0]
        assert ts[0] != ts[1]  # 不同采样点的时间戳应不同

    def test_header_constants(self) -> None:
        """验证二进制格式常量定义。"""
        assert FAULT_RECORD_MAGIC == 0x57484C45  # "WHLE"
        assert FAULT_RECORD_VERSION == 1
        assert FAULT_RECORD_HEADER_SIZE == 24
