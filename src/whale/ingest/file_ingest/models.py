"""文件接入运行期数据模型与 DTO。

定义文件接入最小闭环中使用到的数据传输对象（DTO），覆盖从文件落地
检测、请求入参到接入结果和故障事件元数据的完整数据流。

本文件包含：
- FileIngestManifest: 文件接入 manifest 记录。
- FileStabilityProbeResult: 文件稳定性探测结果。
- FileIngestRequest: 文件接入请求入参。
- FileIngestResult: 文件接入结果。
- FaultEventMetadata: 故障事件元数据。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(slots=True)
class FileIngestManifest:
    """文件接入 manifest 记录。

    描述一个待接入文件的完整元数据，由文件落地检测阶段产生。
    包含文件标识、路径、大小、校验和、时间戳和完成标记路径。

    Attributes:
        file_id: 文件唯一标识。
        file_type: 文件类型（如 plc_high_rate_json / fault_record_binary）。
        path: 文件绝对路径或相对路径。
        size_bytes: 文件字节数。
        checksum: 文件校验和十六进制字符串。
        checksum_algorithm: 校验和算法（如 sha256）。
        created_at: 文件创建时间（UTC ISO 格式字符串）。
        done_flag_path: 完成的 `.done` 标记文件路径。
        metadata: 扩展元数据字典。
    """

    file_id: str
    """文件唯一标识。"""
    file_type: str
    """文件类型。"""
    path: str
    """文件路径。"""
    size_bytes: int = 0
    """文件字节数。"""
    checksum: str = ""
    """校验和。"""
    checksum_algorithm: str = "sha256"
    """校验和算法。"""
    created_at: str = field(
        default_factory=lambda: datetime.now(tz=timezone.utc).isoformat(),
    )
    """文件创建时间（UTC ISO 格式）。"""
    done_flag_path: str = ""
    """完成标记文件路径（.done 文件）。"""
    metadata: dict[str, Any] = field(default_factory=dict)
    """扩展元数据字典。"""


@dataclass(slots=True)
class FileStabilityProbeResult:
    """文件稳定性探测结果。

    表示对指定路径文件的落地完成状态探测结论。探测方式包括
    manifest 校验、文件大小稳定检查和 done flag 文件检查。

    Attributes:
        path: 被探测的文件路径。
        stable: 文件是否已稳定（落地完成）。
        size_bytes: 最终文件大小（字节）。
        observed_count: 稳定性探测次数。
        reason: 探测结论说明（如 size_stable / done_flag_present / manifest_valid）。
    """

    path: str
    """被探测的文件路径。"""
    stable: bool = False
    """文件是否已稳定。"""
    size_bytes: int = 0
    """最终文件大小（字节）。"""
    observed_count: int = 0
    """探测次数。"""
    reason: str = ""
    """探测结论说明。"""


@dataclass(slots=True)
class FileIngestRequest:
    """文件接入请求入参。

    由调用方传入的接入请求参数，指定待接入文件的路径、类型和
    关联的 source/asset/device 信息及追踪 ID。

    Attributes:
        manifest_path: manifest JSON 文件路径（与 data_path 二选一）。
        data_path: 数据文件直接路径（与 manifest_path 二选一）。
        file_type: 文件类型。
        source_id: 数据源标识。
        asset_id: 资产标识（与 device_id 语义可互换）。
        device_id: 设备标识（与 asset_id 语义可互换）。
        trace_id: 分布式追踪 ID。
    """

    manifest_path: str = ""
    """manifest JSON 文件路径。"""
    data_path: str = ""
    """数据文件直接路径。"""
    file_type: str = ""
    """文件类型。"""
    source_id: str = ""
    """数据源标识。"""
    asset_id: str = ""
    """资产标识。"""
    device_id: str = ""
    """设备标识。"""
    trace_id: str = ""
    """分布式追踪 ID。"""


@dataclass
class FileIngestResult:
    """文件接入结果。

    接入完成后返回的结构化结果，包含接入状态、统计信息和错误列表。

    Attributes:
        accepted: 是否整体成功接入。
        raw_batch_id: raw_archive 批次 ID。
        decoded_signal_count: 解码得到的 DecodedSignal 数量。
        waveform_count: 写入的波形记录数。
        fault_event_count: 记录的故障事件数量。
        reason: 总体结果描述。
        errors: 处理过程中的错误信息列表。
    """

    accepted: bool = False
    """是否整体成功接入。"""
    raw_batch_id: str = ""
    """raw_archive 批次 ID。"""
    decoded_signal_count: int = 0
    """解码得到的信号数量。"""
    waveform_count: int = 0
    """写入的波形记录数。"""
    fault_event_count: int = 0
    """记录的故障事件数量。"""
    reason: str = ""
    """总体结果描述。"""
    errors: list[str] = field(default_factory=list)
    """处理过程中的错误信息列表。"""

    def add_error(self, error_msg: str) -> None:
        """追加一条错误信息。

        Args:
            error_msg: 错误描述文本。
        """
        self.errors.append(error_msg)


@dataclass(slots=True)
class FaultEventMetadata:
    """故障事件元数据。

    描述一次故障事件的完整元信息，包含事件标识、隶属关系、时间范围、
    采样参数、原始批次引用和严重程度。

    Attributes:
        event_id: 故障事件唯一标识。
        source_id: 数据源标识。
        asset_id: 资产标识。
        device_id: 设备标识。
        event_type: 故障事件类型（如 TRIP / OVERLOAD / SHORT_CIRCUIT）。
        started_at: 故障开始时间（UTC ISO 格式）。
        ended_at: 故障结束时间（UTC ISO 格式）。
        sample_rate_hz: 采样率（Hz）。
        channel_count: 通道数量。
        raw_batch_id: 关联的 raw_archive 批次 ID。
        severity: 严重程度（如 CRITICAL / WARNING / INFO）。
        metadata: 扩展元数据字典。
    """

    event_id: str
    """故障事件唯一标识。"""
    source_id: str = ""
    """数据源标识。"""
    asset_id: str = ""
    """资产标识。"""
    device_id: str = ""
    """设备标识。"""
    event_type: str = ""
    """故障事件类型。"""
    started_at: str = ""
    """故障开始时间（UTC ISO 格式）。"""
    ended_at: str = ""
    """故障结束时间（UTC ISO 格式）。"""
    sample_rate_hz: float = 0.0
    """采样率（Hz）。"""
    channel_count: int = 0
    """通道数量。"""
    raw_batch_id: str = ""
    """关联的 raw_archive 批次 ID。"""
    severity: str = "WARNING"
    """严重程度。"""
    metadata: dict[str, Any] = field(default_factory=dict)
    """扩展元数据字典。"""
