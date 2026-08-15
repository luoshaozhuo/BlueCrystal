"""speed layer 预处理 Pipeline 运行期 DTO 与 dataclass。

定义 Round A 预处理管线中使用的所有数据传输对象（DTO），覆盖从原始载荷
输入到标准层写入和状态视图更新的完整数据流。

本文件包含：
- SignalProfileItemDescriptor: 信号点位运行时描述符。
- DecodedSignal: 解码后的信号。
- ResolvedSignal: 解析后的信号（已映射到描述符）。
- StandardizedPointValue: 标准化点值。
- StandardizedWaveformValue: 标准化波形值（Round A 仅定义模型）。
- StateViewRecord: Redis 状态视图记录。
- PipelineContext: 管线上下文（承载所有阶段的中间结果）。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(slots=True)
class SignalProfileItemDescriptor:
    """信号点位运行时描述符。

    从 SignalProfileItem ORM 中提取的运行时必要字段，用于 pipeline operator
    的选择、解码和标准化。Round A 不修改 SignalProfileItem ORM，仅定义运行时
    映射视图。

    Attributes:
        profile_item_id: 点位方案明细 ID（对应 ORM scada_signal_profile_item）。
        descriptor_key: 描述符唯一键，用于 operator 注册和选择匹配。
        variable_key: 变量标识，用于时序存储和查询。
        relative_path: 相对于 LD 实例的点位路径（如 MMXU1.TotW.mag.f）。
        data_type: 数据类型名称（如 INT32 / FLOAT64 / BOOLEAN / STRING）。
        default_unit: 默认单位（如 kW / m/s / C / %）。
        default_scale: 默认倍率，用于值转换。
        default_offset: 默认偏移量，用于值转换。
        default_precision: 默认小数精度。
        protocol: 应用层协议（如 MODBUS / IEC104 / OPC_UA）。
        vendor: 厂家（如 STANDARD / VendorA / VendorB）。
        byte_length: 二进制解码时使用的字节长度。
        endian: 二进制解码时使用的字节序（BIG_ENDIAN / LITTLE_ENDIAN）。
        payload_type: 载荷类型（JSON / BINARY / SCALAR / PROTOBUF）。
        quality_supported: 该点位是否支持质量位。
        timestamp_supported: 该点位是否支持源端时间戳。
    """

    profile_item_id: int
    """点位方案明细主键。"""
    descriptor_key: str
    """描述符唯一键，按 profile_item_id:relative_path 构造。"""
    variable_key: str
    """变量标识。"""
    relative_path: str
    """相对于 LD 实例的路径。"""
    data_type: str
    """数据类型名称。"""
    default_unit: str | None = None
    """默认单位。"""
    default_scale: float | None = None
    """默认倍率。"""
    default_offset: float | None = None
    """默认偏移量。"""
    default_precision: int | None = None
    """默认小数精度。"""
    protocol: str | None = None
    """应用层协议。"""
    vendor: str | None = None
    """厂家。"""
    byte_length: int | None = None
    """字节长度。"""
    endian: str | None = None
    """字节序（BIG_ENDIAN / LITTLE_ENDIAN）。"""
    payload_type: str = "JSON"
    """载荷类型。"""
    quality_supported: bool = False
    """是否支持质量位。"""
    timestamp_supported: bool = False
    """是否支持源端时间戳。"""


@dataclass(slots=True)
class DecodedSignal:
    """解码后的信号。

    从原始 payload（JSON dict、二进制 bytes、标量值）中提取的结构化数据。
    解码失败时记录 decode_status=DECODE_ERROR 和错误信息，不抛异常。
    Round A 要求高频二进制 payload 必须先 decode 再 resolve。

    Attributes:
        descriptor_key: 目标描述符键，用于后续 resolve 阶段映射。
        variable_key: 变量标识。
        raw_value: 解码后的原始值。
        source_timestamp: 源端时间戳（ISO 格式字符串）。
        quality_code: 源端质量码（如 0/1/3）。
        decode_status: 解码状态（SUCCESS / DECODE_ERROR / MISSING）。
        decode_error: 解码失败时的错误信息。
    """

    descriptor_key: str
    """目标描述符键。"""
    variable_key: str
    """变量标识。"""
    raw_value: Any = None
    """解码后的原始值。"""
    source_timestamp: str | None = None
    """源端时间戳。"""
    quality_code: str | None = None
    """源端质量码。"""
    decode_status: str = "SUCCESS"
    """解码状态。"""
    decode_error: str | None = None
    """解码错误信息。"""


@dataclass(slots=True)
class ResolvedSignal:
    """解析后的信号。

    将 DecodedSignal 通过 descriptor_key / variable_key / relative_path /
    profile_item_id 映射到 SignalProfileItemDescriptor 后的结果。
    未匹配到描述符时标记为 UNRESOLVED。

    Attributes:
        descriptor: 匹配到的点位描述符（None 表示未解析）。
        decoded: 原始解码信号。
        resolve_status: 解析状态（RESOLVED / UNRESOLVED）。
    """

    descriptor: SignalProfileItemDescriptor | None
    """匹配到的点位描述符。"""
    decoded: DecodedSignal
    """原始解码信号。"""
    resolve_status: str = "RESOLVED"
    """解析状态。"""


@dataclass(slots=True)
class StandardizedPointValue:
    """标准化点值。

    经过时间戳标准化、值标准化和质量评估后，准备写入 TDengine 标准化层
    的数据记录。字段对齐 StandardizedTimeSeriesSinkPort.write() 的输入契约。

    Attributes:
        node_key: 节点标识。
        variable_key: 变量标识。
        value: 标准化后的值。
        value_type: 值类型（如 INT32 / FLOAT64 / BOOLEAN / STRING）。
        quality_code: 质量码（0=GOOD, 1=MISSING, 2=DECODE_ERROR, 3=STALE,
            4=OUT_OF_ORDER）。
        observed_at: 标准化后的 UTC ISO 时间戳。
        received_at: 接收时间 UTC ISO 时间戳。
        source_id: 数据源标识。
        message_id: 消息唯一标识。
        schema_version: schema 版本号。
    """

    node_key: str
    """节点标识。"""
    variable_key: str
    """变量标识。"""
    value: Any = None
    """标准化后的值。"""
    value_type: str = ""
    """值类型。"""
    quality_code: str = "0"
    """质量码。"""
    observed_at: str = ""
    """标准化后的时间戳。"""
    received_at: str = ""
    """接收时间。"""
    source_id: str = ""
    """数据源标识。"""
    message_id: str = ""
    """消息唯一标识。"""
    schema_version: str = "1.0"
    """schema 版本号。"""


@dataclass(slots=True)
class StandardizedWaveformValue:
    """标准化波形值。

    Round A 只定义数据模型和轻量内存路径，不做文件 watcher。
    用于表达高频采样波形或多通道同步数据。

    Attributes:
        node_key: 节点标识。
        variable_key: 变量标识。
        timestamps: 各采样点的 UTC ISO 时间戳列表。
        values: 各采样点的值列表（与 timestamps 对齐）。
        sample_rate_hz: 采样率（Hz）。
        quality_code: 质量码。
        channel_id: 通道标识（用于多通道波形）。
    """

    node_key: str
    """节点标识。"""
    variable_key: str
    """变量标识。"""
    timestamps: list[str] = field(default_factory=list)
    """采样时间戳列表。"""
    values: list[float] = field(default_factory=list)
    """采样值列表。"""
    sample_rate_hz: float = 0.0
    """采样率。"""
    quality_code: str = "0"
    """质量码。"""
    channel_id: str | None = None
    """通道标识。"""


@dataclass(slots=True)
class StateViewRecord:
    """Redis 状态视图记录。

    将标准化后的信号值封装为 serving cache 可写入的记录格式。

    Attributes:
        cache_key: 缓存键（如 source_id:device_id:variable_key）。
        value: 缓存值字典，包含 source_id、observed_at、value、quality_code 等。
        ttl_seconds: TTL 秒数。
    """

    cache_key: str
    """缓存键。"""
    value: dict[str, Any] = field(default_factory=dict)
    """缓存值字典。"""
    ttl_seconds: int = 60
    """TTL 秒数。"""


@dataclass
class PipelineContext:
    """预处理管线上下文。

    贯串固定 10 阶段 pipeline 的共享上下文。每个阶段从 context 读取所需
    数据，处理后写回 context。无需继承或派生不同 context。

    context 承载以下信息：
    - 消息元信息：source_id、message_id、message_type、trace_id、schema_version。
    - 载荷信息：original_payload（原始载荷）、payload_type、protocol、vendor。
    - 阶段中间结果：decoded_signals、resolved_signals、standardized_values。
    - 状态标记：quality_code、is_duplicate、is_out_of_order、should_dlq。
    - 派生状态：derived_states（source_alive、communication_state 等）。
    - 错误记录：errors 列表。
    - 阶段元数据：stage_results（每个阶段的执行状态和耗时）。

    Attributes:
        source_id: 数据源标识。
        message_id: 消息唯一标识。
        message_type: 消息业务类型。
        schema_version: schema 版本号。
        trace_id: 分布式追踪 ID。
        published_at: 消息发布时间（ISO 格式字符串）。
        received_at: 消息接收时间（ISO 格式字符串）。
        original_payload: 原始载荷（dict / bytes / scalar）。
        items: 原始载荷中的 items 列表（每条为一个数据项 dict）。
        payload_type: 分类后的载荷类型（JSON / BINARY / SCALAR）。
        protocol: 协议（OPC_UA / MODBUS / IEC104 / 等）。
        vendor: 厂家（STANDARD / VendorA / VendorB / 等）。
        descriptor: 当前处理的点位描述符。
        decoded_signals: 解码后的信号列表。
        resolved_signals: 解析后的信号列表。
        standardized_values: 标准化点值列表。
        quality_code: 全局质量码（聚合级）。
        is_duplicate: 是否为重复消息。
        is_out_of_order: 是否存在乱序数据。
        should_dlq: 是否应写入 DLQ。
        errors: 错误消息列表。
        derived_states: 派生状态字典（如 source_alive、communication_state）。
        stage_results: 每个阶段的执行结果（状态和耗时）。
    """

    # ── 消息元信息 ──
    source_id: str = ""
    """数据源标识。"""
    message_id: str = ""
    """消息唯一标识。"""
    message_type: str = ""
    """消息业务类型。"""
    schema_version: str = "1.0"
    """schema 版本号。"""
    trace_id: str | None = None
    """分布式追踪 ID。"""
    published_at: str | None = None
    """消息发布时间。"""
    received_at: str = field(
        default_factory=lambda: datetime.now(tz=timezone.utc).isoformat(),
    )
    """消息接收时间，默认为当前 UTC 时间。"""

    # ── 载荷信息 ──
    original_payload: Any = None
    """原始载荷（dict / bytes / scalar）。"""
    items: list[dict[str, Any]] = field(default_factory=list)
    """原始载荷中的 items 列表。"""
    payload_type: str | None = None
    """分类后的载荷类型。"""
    protocol: str | None = None
    """协议。"""
    vendor: str | None = None
    """厂家。"""
    descriptor: SignalProfileItemDescriptor | None = None
    """当前点位描述符。"""

    # ── 阶段中间结果 ──
    decoded_signals: list[DecodedSignal] = field(default_factory=list)
    """解码信号列表。"""
    resolved_signals: list[ResolvedSignal] = field(default_factory=list)
    """解析信号列表。"""
    standardized_values: list[StandardizedPointValue] = field(default_factory=list)
    """标准化点值列表。"""

    # ── 状态标记 ──
    quality_code: str | None = None
    """全局质量码。"""
    is_duplicate: bool = False
    """是否为重复消息。"""
    is_out_of_order: bool = False
    """是否检测到乱序。"""
    should_dlq: bool = False
    """是否应写入 DLQ。"""
    errors: list[str] = field(default_factory=list)
    """错误消息列表。"""

    # ── 派生状态 ──
    derived_states: dict[str, Any] = field(default_factory=dict)
    """派生状态字典。"""

    # ── 阶段元数据 ──
    stage_results: dict[str, dict[str, Any]] = field(default_factory=dict)
    """阶段执行结果记录，键为阶段序号名，值为含 status/data 的字典。"""
