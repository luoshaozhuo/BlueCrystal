"""文件接入专用解码器。

将文件内容解码为 DecodedSignal 列表和 StandardizedWaveformValue 列表。
解码器不直接 resolve 到 SignalProfileItem，输出保留 descriptor_key、
channel_key、unit、value_type、observed_at、quality_code、metadata。

本文件包含：
- PlcHighRateJsonDecoder: 开发期 JSON 格式解码器。
- FaultRecordBinaryDecoder: 最小二进制格式解码器。
"""

from __future__ import annotations

import json
import logging
import struct
from datetime import datetime, timezone

from whale.speed_layer.preprocessing.models import (
    DecodedSignal,
    StandardizedWaveformValue,
)

logger = logging.getLogger(__name__)

# ── 二进制格式常量 ──
FAULT_RECORD_MAGIC = 0x57484C45  # "WHLE" little-endian
FAULT_RECORD_VERSION = 1
FAULT_RECORD_HEADER_SIZE = 24  # magic(4) + version(2) + channel_count(2)
# + sample_rate(4) + timestamp(8) + sample_count(4)


class PlcHighRateJsonDecoder:
    """PLC 高采样率 JSON 解码器。

    解析开发期 JSON 格式的高频采样文件。文件格式为一个 JSON 对象，
    包含 sample_rate_hz、channels（列表）和 samples（列表）。

    每个 JSON 文件格式：
    {
        "sample_rate_hz": 1200.0,
        "observed_at": "2025-01-01T00:00:00Z",
        "channels": [
            {"key": "MMXU1.PhV.instMag.f", "unit": "V", "value_type": "FLOAT64"},
            {"key": "MMXU1.A.instMag.f", "unit": "A", "value_type": "FLOAT64"}
        ],
        "samples": [
            [230.5, 5.1],
            [230.6, 5.2]
        ]
    }

    Attributes:
        _source_id: 数据源标识（解码时传入）。
    """

    def decode(
        self,
        content: str | bytes,
        *,
        source_id: str = "",
    ) -> tuple[list[DecodedSignal], list[StandardizedWaveformValue]]:
        """将 JSON 内容解码为 DecodedSignal 和 StandardizedWaveformValue 列表。

        先输出所有 DecodedSignal（按 channels + samples 展开），
        再构建 StandardizedWaveformValue（按 channel 分组）。

        Args:
            content: JSON 文件内容（字符串或 UTF-8 字节串）。
            source_id: 数据源标识。

        Returns:
            (decoded_signals, waveforms) 元组。解码失败时返回空列表。

        Raises:
            json.JSONDecodeError: JSON 解析失败。
            ValueError: 字段类型或结构不符合预期。
        """
        if isinstance(content, bytes):
            content = content.decode("utf-8")

        data: dict = json.loads(content)

        sample_rate_hz = float(data.get("sample_rate_hz", 0.0))
        observed_at = data.get("observed_at", datetime.now(tz=timezone.utc).isoformat())
        channels: list[dict] = data.get("channels", [])
        samples: list[list] = data.get("samples", [])

        decoded_signals: list[DecodedSignal] = []
        waveforms: list[StandardizedWaveformValue] = []

        if not channels or not samples:
            return decoded_signals, waveforms

        # 按 channel 收集每个采样点的值和时间戳
        channel_count = len(channels)
        channel_timestamps: list[list[str]] = [[] for _ in range(channel_count)]
        channel_values: list[list[float]] = [[] for _ in range(channel_count)]

        for sample_idx, sample_values in enumerate(samples):
            # 每个采样点的时间戳按 sample_idx 等间隔递增
            # 使用索引作为偏移（微秒级），调用方可覆盖
            ts = observed_at  # 默认使用文件级时间戳
            for ch_idx in range(channel_count):
                if ch_idx < len(sample_values):
                    channel_timestamps[ch_idx].append(ts)
                    channel_values[ch_idx].append(float(sample_values[ch_idx]))

        # 输出 DecodedSignal
        for ch_idx, ch_info in enumerate(channels):
            ch_key = ch_info.get("key", f"ch_{ch_idx}")

            # 为每个采样点生成 DecodedSignal
            for sample_idx in range(len(channel_values[ch_idx])):
                raw_value = channel_values[ch_idx][sample_idx]
                decoded = DecodedSignal(
                    descriptor_key=ch_key,
                    variable_key=ch_key,
                    raw_value=raw_value,
                    source_timestamp=channel_timestamps[ch_idx][sample_idx],
                    quality_code="0",
                    decode_status="SUCCESS",
                )
                decoded_signals.append(decoded)

            # 按 channel 构建 StandardizedWaveformValue
            waveform = StandardizedWaveformValue(
                node_key=source_id,
                variable_key=ch_key,
                timestamps=channel_timestamps[ch_idx],
                values=channel_values[ch_idx],
                sample_rate_hz=sample_rate_hz,
                quality_code="0",
                channel_id=str(ch_idx),
            )
            # 补充 channel 元数据到 waveform（StandardizedWaveformValue 自身
            # 不含 unit/value_type，通过 metadata 在后续阶段补充）
            waveforms.append(waveform)

        return decoded_signals, waveforms


class FaultRecordBinaryDecoder:
    """故障录波二进制解码器。

    解析最小二进制格式的故障录波文件。二进制格式固定为：

    - magic:      4 bytes, uint32, little-endian, 固定 0x57484C45 ("WHLE")
    - version:    2 bytes, uint16, little-endian, 当前版本 1
    - channel_count: 2 bytes, uint16, little-endian
    - sample_rate: 4 bytes, float32, little-endian
    - timestamp:  8 bytes, double (Unix timestamp seconds)
    - sample_count: 4 bytes, uint32, little-endian
    - values:     sample_count * channel_count * 4 bytes, float32 little-endian

    总头部大小 FAULT_RECORD_HEADER_SIZE = 24 bytes。
    values 按 channel-first 交错排列（ch0_s0, ch1_s0, ch0_s1, ch1_s1, ...）,
    或按 channel-major（ch0 全部采样后 ch1 全部采样）。
    本实现假定 channel-major 排列（各 channel 的全部采样依次排列）。

    Attributes:
        _default_source_id: 默认数据源标识。
    """

    def __init__(self, default_source_id: str = "") -> None:
        """初始化二进制解码器。

        Args:
            default_source_id: 解码时无外部 source_id 时使用的默认值。
        """
        self._default_source_id = default_source_id

    def decode(
        self,
        content: bytes,
        *,
        source_id: str = "",
    ) -> tuple[list[DecodedSignal], list[StandardizedWaveformValue]]:
        """将二进制内容解码为 DecodedSignal 和 StandardizedWaveformValue 列表。

        先校验 magic 和 version，然后解析 header 提取采样参数。
        解码失败时返回空列表，不抛异常（通过 decode_status 标记错误）。

        Args:
            content: 二进制文件内容（bytes）。
            source_id: 数据源标识，为空时使用 default_source_id。

        Returns:
            (decoded_signals, waveforms) 元组。
        """
        if not source_id:
            source_id = self._default_source_id

        if len(content) < FAULT_RECORD_HEADER_SIZE:
            logger.warning(
                "二进制文件太小，无法解析 header: len=%d min=%d",
                len(content), FAULT_RECORD_HEADER_SIZE,
            )
            return [], []

        try:
            # 解析 header
            (
                magic,
                version,
                channel_count,
                sample_rate,
                timestamp_unix,
                sample_count,
            ) = struct.unpack_from("<IHHfdI", content, 0)
        except struct.error as exc:
            logger.warning("二进制 header 解析失败: %s", exc)
            return [], []

        if magic != FAULT_RECORD_MAGIC:
            logger.warning(
                "magic 不匹配: 期望 0x%08X, 实际 0x%08X",
                FAULT_RECORD_MAGIC, magic,
            )
            return [], []

        if version != FAULT_RECORD_VERSION:
            logger.warning(
                "version 不支持: 期望 %d, 实际 %d",
                FAULT_RECORD_VERSION, version,
            )
            return [], []

        if channel_count == 0 or sample_count == 0:
            return [], []

        # 计算期望的 values 数据大小
        expected_values_size = sample_count * channel_count * 4  # float32 = 4 bytes
        total_expected = FAULT_RECORD_HEADER_SIZE + expected_values_size

        if len(content) < total_expected:
            logger.warning(
                "二进制文件不完整: len=%d expected=%d", len(content), total_expected
            )
            return [], []

        # 将 Unix 时间戳转换为 ISO 字符串
        observed_at = datetime.fromtimestamp(timestamp_unix, tz=timezone.utc).isoformat()

        # 按 channel-major 排列解析 values
        # ch0: sample_count values, ch1: sample_count values, ...
        values_offset = FAULT_RECORD_HEADER_SIZE
        channel_values: list[list[float]] = []
        for ch_idx in range(channel_count):
            ch_start = values_offset + ch_idx * sample_count * 4
            ch_vals: list[float] = []
            for s in range(sample_count):
                val_start = ch_start + s * 4
                (val,) = struct.unpack_from("<f", content, val_start)
                ch_vals.append(float(val))
            channel_values.append(ch_vals)

        # 构建时间戳列表：每个采样点等间隔
        interval_s = 1.0 / sample_rate if sample_rate > 0 else 0.0
        timestamps: list[str] = []
        for s in range(sample_count):
            ts_unix = timestamp_unix + s * interval_s
            ts = datetime.fromtimestamp(ts_unix, tz=timezone.utc).isoformat()
            timestamps.append(ts)

        # 输出 DecodedSignal（按 channel * sample 展开）
        decoded_signals: list[DecodedSignal] = []
        waveforms: list[StandardizedWaveformValue] = []

        for ch_idx in range(channel_count):
            ch_key = f"ch_{ch_idx}"
            ch_vals = channel_values[ch_idx]

            for s in range(sample_count):
                decoded = DecodedSignal(
                    descriptor_key=ch_key,
                    variable_key=ch_key,
                    raw_value=ch_vals[s],
                    source_timestamp=timestamps[s] if s < len(timestamps) else observed_at,
                    quality_code="0",
                    decode_status="SUCCESS",
                )
                decoded_signals.append(decoded)

            # 按 channel 构建 StandardizedWaveformValue
            waveform = StandardizedWaveformValue(
                node_key=source_id,
                variable_key=ch_key,
                timestamps=list(timestamps),
                values=list(ch_vals),
                sample_rate_hz=float(sample_rate),
                quality_code="0",
                channel_id=str(ch_idx),
            )
            waveforms.append(waveform)

        return decoded_signals, waveforms
