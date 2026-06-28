"""IEC 60870-5-101 信息对象（Information Object）编解码。

本模块实现各 TypeId 对应的"信息对象"层（Information Object, IO）
编解码。每个信息对象代表一个信息点的全部内容（不含 IOA，由 ASDU 层
单独管理；除 SQ=0 情况下 IOA 紧接在头部之后的情况）。

当前实现的 TypeId（监视方向）：

- M_SP_NA_1 (TypeId=1)：
    单点信息，不带时标。
    信息体结构 = SIQ(1 byte)。
    不带时标，因此 object body 长度 = 1 字节。

- M_DP_NA_1 (TypeId=3)：
    双点信息，不带时标。
    信息体结构 = DPI(2 bits) + RES(2 bits) 共 1 字节。
    DPI (Double-point Information) 取值：
        0 = 中间态 / 不确定 (Indeterminate or intermediate state)
        1 = 确定断开 (Determined OFF)
        2 = 确定接通 (Determined ON)
        3 = 不确定 (Indeterminate)
    编码约定：DPI 占低 2 位，bit 2-7 保留为 0。

- M_ME_NA_1 (TypeId=9)：
    测量值归一化（normalized），不带时标。
    信息体结构 = NVA(2 bytes, 16-bit signed) + QDS(1 byte)。
    不带时标，因此 object body 长度 = 3 字节。

- M_ME_NB_1 (TypeId=11)：
    测量值标度化（scaled），不带时标。
    信息体结构 = SVA(2 bytes, 16-bit signed int) + QDS(1 byte)。
    object body 长度 = 3 字节。已支持 information object
    实现（按 lib60870 语义对齐）。

- M_ME_NC_1 (TypeId=13)：
    短浮点测量值（ShortFloat），不带时标。
    信息体结构 = ShortFloat(4 bytes, IEEE 754 LE) + QDS(1 byte)。
    object body 长度 = 5 字节。已支持 information object
    实现。

当前实现的 TypeId（控制方向）：

- C_SC_NA_1 (TypeId=45)：
    单命令（Single Command），不带时标。
    信息体结构 = SCS(1 bit) + S/E(1 bit) + QU(5 bits) + 保留(1 bit)
    共 1 字节。
    SCS (Single Command State) 取值：
        0 = OFF (Latch off)
        1 = ON  (Latch on)
    S/E (Select/Execute) 取值：
        0 = execute (执行)
        1 = select  (选择)
    QU (Qualifier of Command) 5 bits，包含：
        QL 0..3 (Qualifier of command, 短/长脉冲/持续输出等)
        persistent 标志（常用约定）
        保留位。
    本实现保留位级编码能力（旧 roundtrip），同时引入结构化
    ``SingleCommandQualifier`` dataclass（结构化升级，进一步显式化
    select_execute / qualifier / ql_value /
    persistent / pulse 子字段映射），编码时仍按位级写入，结构化
    字段与位级 1:1 对应：
        bit 0 = select_execute
        bit 1-2 = ql_value (0..3)
        bit 3 = persistent 标志
        bit 4-5 = reserved
    旧的 ``qualifier`` 字段（位级）保留为底层字节值，便于
    旧 roundtrip 测试继续通过。S/E 位（bit 1）由
    ``C_SC_NA_1_Object.select_execute`` 单独维护，与 QU 字段正交。

当前实现的 TypeId（带时标）：

- M_SP_TA_1 (TypeId=2)：
    单点信息，带 CP56Time2a 时标。
    信息体结构 = SIQ(1 byte) + CP56Time2a(7 bytes)。
    object body 长度 = 8 字节。

- M_DP_TA_1 (TypeId=4)：
    双点信息，带 CP56Time2a 时标。
    信息体结构 = DPI(1 byte) + CP56Time2a(7 bytes)。
    object body 长度 = 8 字节。

- M_ME_TA_1 (TypeId=10)：
    归一化测量值，带 CP56Time2a 时标。
    信息体结构 = NVA(2 bytes) + QDS(1 byte) + CP56Time2a(7 bytes)。
    object body 长度 = 10 字节。

- M_ME_TB_1 (TypeId=12，已支持)：
    标度化测量值，带 CP56Time2a 时标。
    信息体结构 = SVA(2 bytes, 16-bit signed int) + QDS(1 byte)
    + CP56Time2a(7 bytes)。
    object body 长度 = 10 字节。
    语义：SVA 是 16-bit 有符号整数（-32768..+32767），由业务侧
    解释量程与单位（与 NVA 的"归一化至 -1.0..1.0-1/32768"语义
    完全不同；SVA 是工程量级整数表示，由 device profile 决定
    量程映射）。

- M_ME_TC_1 (TypeId=14，已支持)：
    短浮点测量值，带 CP56Time2a 时标。
    信息体结构 = ShortFloat(4 bytes, IEEE 754 LE) + QDS(1 byte)
    + CP56Time2a(7 bytes)。
    object body 长度 = 12 字节。
    语义：ShortFloat 携带 IEEE 754 single-precision 浮点（4 字节，
    little-endian），编码/解码时拒绝 NaN/Inf（详见
    ``information_elements.encode_short_float``）。

不负责：
- SQ=1 模式下首 IOA + 自增序列的协议行为（由 asdu 列表层处理）。
- M_DP_NA_1 的全部 QUALIFIER 子语义；M_DP_NA_1 仍仅位级。
- C_SE_TA_1 / C_SE_TB_1 / C_SE_TC_1 等控制方向带时标命令
  （已支持；与不带时标 C_SE_NA_1/C_SE_NB_1/C_SE_NC_1
  同语义但末尾追加 CP56Time2a 7 字节时标；object body 长度
  12 / 12 / 14 字节；仍仅 command codec，
  **不**等效真实写能力）。
"""

from __future__ import annotations

import struct
from dataclasses import dataclass, field
from enum import Enum

from starfish.domain.protocols.iec101.quality import QDS, SIQ, decode_qds, decode_siq, encode_qds, encode_siq
from starfish.domain.protocols.iec101.information_elements import (
    decode_normalized_value,
    decode_scaled_value,
    decode_short_float,
    encode_normalized_value,
    encode_scaled_value,
    encode_short_float,
)
from starfish.domain.protocols.iec101.time import (
    CP56TIME2A_LENGTH,
    CP56Time2a,
    decode_cp56time2a,
    encode_cp56time2a,
)


# ── M_SP_NA_1: Single-point information (without time tag) ────────────────────


M_SP_NA_1_OBJECT_SIZE = 1  # 仅 SIQ 1 字节


@dataclass
class M_SP_NA_1_Object:
    """M_SP_NA_1 信息对象（单点信息，不带时标）。

    Attributes:
        siq: 单点信息质量描述符（含 value 与质量标志）。
    """

    siq: SIQ

    def encode(self) -> bytes:
        """编码为 1 字节信息体（不含 IOA）。

        Returns:
            1 字节编码结果。
        """
        return encode_siq(self.siq)

    @classmethod
    def decode(cls, data: bytes) -> "M_SP_NA_1_Object":
        """从 1 字节数据解码 M_SP_NA_1 信息体。

        Args:
            data: 至少 1 字节。

        Returns:
            解析后的 M_SP_NA_1_Object 实例。

        Raises:
            ValueError: 数据不足 1 字节。
        """
        return cls(siq=decode_siq(data[:M_SP_NA_1_OBJECT_SIZE]))


# ── M_DP_NA_1: Double-point information (without time tag) ─────────────────────


M_DP_NA_1_OBJECT_SIZE = 1  # 仅 DPI 1 字节


class DoublePointValue:
    """双点信息（DPI）状态枚举语义。

    实际编码仅使用 2 位（0-3），但作为 dataclass 字段时使用
    明确的整数值（0-3）以避免歧义。
    """

    INTERMEDIATE = 0  # 中间态 / 不确定
    OFF = 1  # 确定断开
    ON = 2  # 确定接通
    INDETERMINATE = 3  # 不确定


@dataclass
class M_DP_NA_1_Object:
    """M_DP_NA_1 信息对象（双点信息，不带时标）。

    Attributes:
        dpi: 双点信息状态（0-3，参见 DoublePointValue）。
        reserved_high_bits: DPI 高 6 位（保留），默认为 0。
    """

    dpi: int = 0
    reserved_high_bits: int = 0

    def __post_init__(self) -> None:
        if self.dpi < 0 or self.dpi > 3:
            raise ValueError(
                f"DPI 值 {self.dpi} 超出有效范围 [0, 3]"
            )
        if self.reserved_high_bits < 0 or self.reserved_high_bits > 0x3F:
            raise ValueError(
                f"reserved_high_bits {self.reserved_high_bits} 超出范围 [0, 0x3F]"
            )

    def encode(self) -> bytes:
        """编码为 1 字节信息体（DPI 在低 2 位，高 6 位为 reserved）。"""
        return bytes([(self.reserved_high_bits << 2) | (self.dpi & 0x03)])

    @classmethod
    def decode(cls, data: bytes) -> "M_DP_NA_1_Object":
        """从 1 字节数据解码 M_DP_NA_1 信息体。

        Args:
            data: 至少 1 字节。

        Returns:
            解析后的 M_DP_NA_1_Object 实例。

        Raises:
            ValueError: 数据不足 1 字节。
        """
        if len(data) < M_DP_NA_1_OBJECT_SIZE:
            raise ValueError(
                f"M_DP_NA_1 解码需要至少 {M_DP_NA_1_OBJECT_SIZE} 字节，"
                f"实际只有 {len(data)} 字节"
            )
        byte = data[0]
        return cls(dpi=byte & 0x03, reserved_high_bits=(byte >> 2) & 0x3F)


# ── M_ME_NA_1: Measured value, normalized (without time tag) ──────────────────


M_ME_NA_1_OBJECT_SIZE = 3  # NVA(2) + QDS(1) = 3 字节


@dataclass
class M_ME_NA_1_Object:
    """M_ME_NA_1 信息对象（归一化测量值，不带时标）。

    Attributes:
        nva: 归一化浮点值（-1.0 ~ +(1-1/32768)）。
        qds: 测量值质量描述符。
    """

    nva: float
    qds: QDS

    def encode(self) -> bytes:
        """编码为 3 字节信息体：NVA(2) + QDS(1)。"""
        result = bytearray()
        result.extend(encode_normalized_value(self.nva))
        result.extend(encode_qds(self.qds))
        return bytes(result)

    @classmethod
    def decode(cls, data: bytes) -> "M_ME_NA_1_Object":
        """从 3 字节数据解码 M_ME_NA_1 信息体。

        Args:
            data: 至少 3 字节。

        Returns:
            解析后的 M_ME_NA_1_Object 实例。

        Raises:
            ValueError: 数据不足 3 字节。
        """
        if len(data) < M_ME_NA_1_OBJECT_SIZE:
            raise ValueError(
                f"M_ME_NA_1 解码需要至少 {M_ME_NA_1_OBJECT_SIZE} 字节，"
                f"实际只有 {len(data)} 字节"
            )
        nva = decode_normalized_value(data[:2])
        qds = decode_qds(data[2:3])
        return cls(nva=nva, qds=qds)


# ── M_ME_NB_1: Measured value, scaled (without time tag) ──────────────────────
# 已支持：与 M_ME_TB_1 同语义但不带时标，对应 TypeId=11。
# SVA 是 16-bit 有符号整数（-32768..+32767）；量程与单位由
# device profile / 业务侧解释（与 NVA 的"归一化至 -1.0..1.0-1/32768"
# 语义完全不同；SVA 是工程量级整数表示）。编码：小端序 int16。


M_ME_NB_1_OBJECT_SIZE = 3  # SVA(2) + QDS(1) = 3 字节


@dataclass
class M_ME_NB_1_Object:
    """M_ME_NB_1 信息对象（标度化测量值，不带时标，已支持）。

    信息体结构 = SVA(2 bytes, 16-bit signed int) + QDS(1 byte)，
    object body = 3 字节。

    Attributes:
        sva: 标度化整数值（-32768..+32767）。
        qds: 测量值质量描述符。
    """

    sva: int = 0
    qds: QDS = field(default=None)  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.qds is None:
            self.qds = QDS()
        if not -32768 <= self.sva <= 32767:
            raise ValueError(
                f"M_ME_NB_1 sva 值 {self.sva} 超出 int16 范围 "
                f"[-32768, 32767]"
            )
        if not isinstance(self.qds, QDS):
            raise TypeError(
                f"qds 字段必须为 QDS 实例，实际 {type(self.qds).__name__}"
            )

    def encode(self) -> bytes:
        """编码为 3 字节信息体：SVA(2) + QDS(1)。"""
        result = bytearray()
        result.extend(encode_scaled_value(self.sva))
        result.extend(encode_qds(self.qds))
        return bytes(result)

    @classmethod
    def decode(cls, data: bytes) -> "M_ME_NB_1_Object":
        """从 3 字节数据解码 M_ME_NB_1 信息体。

        Args:
            data: 至少 3 字节。

        Returns:
            解析后的 M_ME_NB_1_Object 实例。

        Raises:
            ValueError: 数据不足 3 字节。
        """
        if len(data) < M_ME_NB_1_OBJECT_SIZE:
            raise ValueError(
                f"M_ME_NB_1 解码需要至少 {M_ME_NB_1_OBJECT_SIZE} 字节，"
                f"实际只有 {len(data)} 字节"
            )
        sva = decode_scaled_value(data[:2])
        qds = decode_qds(data[2:3])
        return cls(sva=sva, qds=qds)


# ── M_ME_NC_1: Measured value, short float (without time tag) ──────────────────
# 已支持：与 M_ME_TC_1 同语义但不带时标，对应 TypeId=13。
# ShortFloat 携带 IEEE 754 single-precision 浮点（4 字节 LE）；
# 编码/解码时拒绝 NaN/Inf（详见 information_elements.encode_short_float）。
# 业务方如需支持 NaN/Inf，应在边界层映射为 QDS.invalid=True 等协议层
# 约定的占位状态。


M_ME_NC_1_OBJECT_SIZE = 5  # ShortFloat(4) + QDS(1) = 5 字节


@dataclass
class M_ME_NC_1_Object:
    """M_ME_NC_1 信息对象（短浮点测量值，不带时标，已支持）。

    信息体结构 = ShortFloat(4 bytes, IEEE 754 LE) + QDS(1 byte)，
    object body = 5 字节。

    Attributes:
        sva: ShortFloat 浮点值（NaN/Inf 拒绝）。
        qds: 测量值质量描述符。
    """

    sva: float = 0.0
    qds: QDS = field(default=None)  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.qds is None:
            self.qds = QDS()
        if not isinstance(self.sva, float):
            raise TypeError(
                f"M_ME_NC_1 sva 字段必须为 float，实际 {type(self.sva).__name__}"
            )
        if not isinstance(self.qds, QDS):
            raise TypeError(
                f"qds 字段必须为 QDS 实例，实际 {type(self.qds).__name__}"
            )

    def encode(self) -> bytes:
        """编码为 5 字节信息体：ShortFloat(4) + QDS(1)。"""
        result = bytearray()
        result.extend(encode_short_float(self.sva))
        result.extend(encode_qds(self.qds))
        return bytes(result)

    @classmethod
    def decode(cls, data: bytes) -> "M_ME_NC_1_Object":
        """从 5 字节数据解码 M_ME_NC_1 信息体。

        Args:
            data: 至少 5 字节。

        Returns:
            解析后的 M_ME_NC_1_Object 实例。

        Raises:
            ValueError: 数据不足 5 字节。
        """
        if len(data) < M_ME_NC_1_OBJECT_SIZE:
            raise ValueError(
                f"M_ME_NC_1 解码需要至少 {M_ME_NC_1_OBJECT_SIZE} 字节，"
                f"实际只有 {len(data)} 字节"
            )
        sva = decode_short_float(data[:4])
        qds = decode_qds(data[4:5])
        return cls(sva=sva, qds=qds)


# ── C_SC_NA_1: Single command (without time tag) ─────────────────────────────


C_SC_NA_1_OBJECT_SIZE = 1  # SCS(1 bit) + S/E(1 bit) + QU(5 bits) + 保留(1 bit) = 1 字节


class CommandPulse(str, Enum):
    """C_SC_NA_1 命令脉冲/输出类型枚举。

    常见 IEC 60870-5-101 限定词语义映射：

    - ``NO_QUALIFIER`` = ql_value=0，无额外限定词（默认）。
    - ``SHORT_PULSE`` = ql_value=1，短脉冲持续。
    - ``LONG_PULSE`` = ql_value=2，长脉冲持续。
    - ``PERSISTENT`` = ql_value=3，持续输出（与 ``persistent=True`` 等价）。

    业务层按枚举直接操作；底层 ``to_byte()`` 仍按位级编码。
    """

    NO_QUALIFIER = "no_qualifier"
    SHORT_PULSE = "short_pulse"
    LONG_PULSE = "long_pulse"
    PERSISTENT = "persistent"


_COMMAND_PULSE_TO_QL: dict[CommandPulse, int] = {
    CommandPulse.NO_QUALIFIER: 0,
    CommandPulse.SHORT_PULSE: 1,
    CommandPulse.LONG_PULSE: 2,
    CommandPulse.PERSISTENT: 3,
}

_QL_TO_COMMAND_PULSE: dict[int, CommandPulse] = {
    0: CommandPulse.NO_QUALIFIER,
    1: CommandPulse.SHORT_PULSE,
    2: CommandPulse.LONG_PULSE,
    3: CommandPulse.PERSISTENT,
}


_UNSET = object()


@dataclass
class SingleCommandQualifier:
    """C_SC_NA_1 QU 字段结构化语义（已支持，扩展）。

    把过去 6 位位级 ``qualifier`` 升级为结构化字段，便于业务层按
    协议语义理解与操作。**注意**：S/E 位（byte bit 1）在协议中独立于
    QU 字段（byte bits 2-7），本类只建模 QU 字段（不含 S/E）。
    S/E 由 ``C_SC_NA_1_Object.select_execute`` 单独维护。

    结构化字段与位级 ``C_SC_NA_1_Object.qualifier``（QU 字段）严格
    1:1 对应：

        bit 0 = RESERVED（保留为 0，与协议 6-bit QU 起始位对齐）
        bit 1-2 = ql_value (Qualifier of command, 0..3)
        bit 3 = persistent (持久脉冲标志，常用约定)
        bit 4-5 = reserved (写入 0)

    含义:
        - ql_value: 限定词值 0..3，常见映射：
            0 = 无额外限定词（默认）。
            1 = short pulse duration (短脉冲持续)。
            2 = long pulse duration (长脉冲持续)。
            3 = persistent output (持续输出)。
        - persistent: True 表示持续输出（常与 ql_value=3 等价，
          保留独立字段以便业务层按布尔语义直接操作）。
        - pulse: 命令脉冲/输出类型枚举，与
          ``ql_value`` / ``persistent`` 双向同步。
        - select_execute: S/E 位镜像。仅作
          便利视图；权威源仍是 ``C_SC_NA_1_Object.select_execute``。
        - qualifier: 6 位命令限定词位级字段镜像。
          编码权威源；``sync_from_qualifier()`` 会从此回写到
          ``ql_value`` 等结构化字段。
        - ql: 限定词 0..3 的别名（已支持，与 ``ql_value``
          同步；保留以兼容 IEC 文档中的 ql 命名）。

    Attributes:
        ql_value: 限定词 0..3。
        persistent: True 表示持续输出。
        pulse: 命令脉冲/输出类型枚举。
        select_execute: S/E 位镜像（0=execute, 1=select）。
        qualifier: 6 位命令限定词位级字段镜像。
        ql: 限定词 0..3 的别名。
    """

    ql_value: int = 0
    persistent: bool = False
    pulse: CommandPulse = CommandPulse.NO_QUALIFIER
    select_execute: int = 0
    qualifier: int = 0
    ql: int = 0

    def __post_init__(self) -> None:
        if not isinstance(self.persistent, bool):
            raise ValueError(
                f"persistent 必须为 bool，实际 {type(self.persistent).__name__}"
            )
        if not 0 <= self.ql_value <= 3:
            raise ValueError(
                f"ql_value {self.ql_value} 超出范围 [0, 3]"
            )
        if self.select_execute not in (0, 1):
            raise ValueError(
                f"select_execute {self.select_execute} 必须为 0 或 1"
            )
        if not 0 <= self.qualifier <= 0x3F:
            raise ValueError(
                f"qualifier {self.qualifier} 超出范围 [0, 0x3F]"
            )
        if not 0 <= self.ql <= 3:
            raise ValueError(
                f"ql {self.ql} 超出范围 [0, 3]"
            )
        if not isinstance(self.pulse, CommandPulse):
            raise ValueError(
                f"pulse 必须为 CommandPulse 实例，实际 "
                f"{type(self.pulse).__name__}"
            )
        # 既有一致性策略：分层权威源 + 严格冲突检测
        # 优先级（高 -> 低）：qualifier > ql_value / ql > pulse
        # 1. ``qualifier`` 是位级字段权威源；若 ``qualifier`` 与
        #    ``ql_value + persistent`` 位布局不一致，先以 qualifier
        #    反推 ql_value / persistent（兼容 ``sync_from_qualifier``
        #    与 ``from_byte`` 入口）。
        # 2. ``ql_value`` 是协议语义权威源；``ql`` 同步 ``ql_value``。
        # 3. ``pulse`` 是 ``ql_value`` 的语义视图；不一致时同步。
        # 4. ``qualifier`` 最终按 ``ql_value + persistent`` 位布局重新计算。
        expected_ql_from_qualifier = (self.qualifier >> 1) & 0x03
        expected_persistent_from_qualifier = bool(
            (self.qualifier >> 3) & 0x01
        )
        # 检测"是否显式传了 ql_value"：通过比较 ql_value 与 qualifier 推导值
        # 若 ql_value 显式传且与 qualifier 推导值不一致，保留 ql_value
        # （业务层显式传 ql_value 表示语义优先）。
        # 若 ql_value 仍为默认 0 且 qualifier 推导值非 0，以 qualifier 为准。
        if self.ql_value == 0 and expected_ql_from_qualifier != 0:
            # ql_value 未显式覆盖（仍为默认 0），按 qualifier 同步
            self.ql_value = expected_ql_from_qualifier
        # persistent 类似
        if not self.persistent and expected_persistent_from_qualifier:
            self.persistent = expected_persistent_from_qualifier
        if self.ql != self.ql_value:
            self.ql = self.ql_value
        if _COMMAND_PULSE_TO_QL[self.pulse] != self.ql_value:
            self.pulse = _QL_TO_COMMAND_PULSE[self.ql_value]
        # 重新计算 qualifier（按 ql_value + persistent 的位布局）
        expected_qualifier = (
            (self.ql_value & 0x03) << 1
            | (int(self.persistent) & 0x01) << 3
        )
        if self.qualifier != expected_qualifier:
            self.qualifier = expected_qualifier

    def to_byte(self) -> int:
        """编码为 6 位 QU 字段值（不含 SCS、S/E 位）。

        编码按位级字段权威（``ql_value`` / ``persistent``）。
        """
        byte = (self.ql_value & 0x03) << 1
        byte |= (int(self.persistent) & 0x01) << 3
        # bit 0/4-5 保留为 0
        return byte & 0x3F

    @classmethod
    def from_byte(cls, value: int) -> "SingleCommandQualifier":
        """从 6 位 QU 字段值解码。

        Args:
            value: 0..0x3F 范围内的位级值。

        Returns:
            解码后的 ``SingleCommandQualifier`` 实例。
        """
        if value < 0 or value > 0x3F:
            raise ValueError(
                f"SingleCommandQualifier.from_byte 期望 0..0x3F，实际 {value}"
            )
        ql = (value >> 1) & 0x03
        persistent = bool((value >> 3) & 0x01)
        # 直接以 derived 字段构造（绕开 auto-sync 覆写）
        return cls.__direct(
            ql_value=ql,
            persistent=persistent,
            pulse=_QL_TO_COMMAND_PULSE[ql],
            qualifier=value,
            ql=ql,
        )

    @classmethod
    def __direct(
        cls,
        *,
        ql_value: int,
        persistent: bool,
        pulse: CommandPulse,
        qualifier: int,
        ql: int,
        select_execute: int = 0,
    ) -> "SingleCommandQualifier":
        """内部 direct 构造：跳过 auto-sync 覆写（仅 ``from_byte`` 内部使用）。

        Python dataclass 的 ``__init__`` + ``__post_init__`` 无法绕过
        校验，因此用 ``object.__new__`` + 直接字段赋值构造。
        """
        obj = cls.__new__(cls)
        obj.ql_value = ql_value
        obj.persistent = persistent
        obj.pulse = pulse
        obj.select_execute = select_execute
        obj.qualifier = qualifier
        obj.ql = ql
        return obj

    def sync_from_qualifier(self) -> None:
        """从 ``qualifier`` 位级字段同步到结构化字段（``ql_value`` /
        ``persistent`` / ``pulse`` / ``ql``）。

        用于调用方仅修改 ``qualifier`` 后希望结构化字段与之一致
        的场景。S/E 位（``select_execute``）不由本方法维护。
        """
        ql = (self.qualifier >> 1) & 0x03
        self.ql_value = ql
        self.ql = ql
        self.persistent = bool((self.qualifier >> 3) & 0x01)
        self.pulse = _QL_TO_COMMAND_PULSE[ql]


@dataclass
class C_SC_NA_1_Object:
    """C_SC_NA_1 信息对象（单命令，不带时标）。

    结构化升级：保留位级 ``qualifier``（旧 roundtrip 兼容），
    同时新增结构化 ``qu_bit`` 字段（``SingleCommandQualifier``）。
    编码权威源策略：
        - ``scs`` / ``select_execute`` / ``qualifier``（位级字段）始终是
          编码与解码的权威源；``__post_init__`` 阶段以位级字段
          （``select_execute`` + ``qualifier``）重建 ``qu_bit``，确保
          旧 roundtrip 测试继续通过。
        - ``qu_bit`` 是结构化的便利视图；调用方可通过 ``qu_bit`` 直接
          操作 ql_value / persistent 等语义字段；修改 ``qu_bit`` 后
          也可通过 ``sync_qu_bit()`` 显式回写到 ``qualifier`` 位级字段。

    Attributes:
        scs: 单命令状态（0=OFF, 1=ON）。
        select_execute: 0=execute 执行，1=select 选择。
        qualifier: 6 位命令限定词（QU 字段），默认为 0。
        qu_bit: 结构化 QU 字段，类型 ``SingleCommandQualifier``。
    """

    scs: int = 0
    select_execute: int = 0
    qualifier: int = 0
    qu_bit: SingleCommandQualifier = field(default=None)  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.scs not in (0, 1):
            raise ValueError(f"SCS 值 {self.scs} 必须为 0 或 1")
        if self.select_execute not in (0, 1):
            raise ValueError(
                f"select_execute 值 {self.select_execute} 必须为 0 或 1"
            )
        if self.qualifier < 0 or self.qualifier > 0x3F:
            raise ValueError(
                f"qualifier {self.qualifier} 超出范围 [0, 0x3F]"
            )
        if self.qu_bit is None:
            # 旧用法：未提供 qu_bit 时按位级字段（qualifier）构造
            # qu_bit 结构化视图，确保旧 roundtrip 与 qu_bit 一致。
            # 注意：S/E 位（select_execute）不参与 QU 字段。
            self.qu_bit = SingleCommandQualifier(
                ql_value=(self.qualifier >> 1) & 0x03,
                persistent=bool((self.qualifier >> 3) & 0x01),
                select_execute=self.select_execute,
                qualifier=self.qualifier,
            )
        # 显式提供 qu_bit 时，把 S/E 位镜像同步到 qu_bit.select_execute
        # （仅便利视图，权威源仍是 self.select_execute）。
        else:
            self.qu_bit.select_execute = self.select_execute

    def sync_qu_bit(self) -> None:
        """显式将结构化 ``qu_bit`` 回写到 ``qualifier`` 位级字段。

        用于调用方仅通过 ``qu_bit`` 修改语义、然后希望底层字节与
        结构化字段一致的场景。编码始终以位级 ``qualifier`` 为准，
        所以本函数必须在 encode 前调用。
        注意：S/E 位（``self.select_execute``）不由 ``qu_bit`` 维护。
        """
        if self.qu_bit is None:
            return
        self.qualifier = self.qu_bit.to_byte()

    def encode(self) -> bytes:
        """编码为 1 字节信息体：bit 0=SCS, bit 1=S/E, bit 2-7=QU。"""
        byte = (self.scs & 0x01) | ((self.select_execute & 0x01) << 1)
        byte |= (self.qualifier & 0x3F) << 2
        return bytes([byte & 0xFF])

    @classmethod
    def decode(cls, data: bytes) -> "C_SC_NA_1_Object":
        """从 1 字节数据解码 C_SC_NA_1 信息体。"""
        if len(data) < C_SC_NA_1_OBJECT_SIZE:
            raise ValueError(
                f"C_SC_NA_1 解码需要至少 {C_SC_NA_1_OBJECT_SIZE} 字节，"
                f"实际只有 {len(data)} 字节"
            )
        byte = data[0]
        scs = byte & 0x01
        select_execute = (byte >> 1) & 0x01
        qualifier = (byte >> 2) & 0x3F
        qu_bit = SingleCommandQualifier.from_byte(qualifier)
        # 同步 S/E 位镜像到 qu_bit
        qu_bit.select_execute = select_execute
        return cls(
            scs=scs,
            select_execute=select_execute,
            qualifier=qualifier,
            qu_bit=qu_bit,
        )


# ── C_SE_NA_1 / C_SE_NB_1 / C_SE_NC_1: Set-point command ──────────────────────
# 已支持：三个不带时标设定值命令。
# 注意：本模块**不实现真实写命令发送**；Iec101Facade 仍保持
# supports_server=false / supports_write_runtime=false（避免
# command codec 被误解为真实写能力）。命令编解码器是 IEC 101
# 控制方向的标准 TypeId，编码权威源 / 字节布局与 lib60870 对齐。


# ── SetPointQualifier（QOS）—— 设定值命令限定词 ────────────────────────────────


class SetPointQualifier(str, Enum):
    """C_SE_* 设定值命令限定词枚举。

    对应 IEC 60870-5-101 §7.2.6.6 / §7.2.6.7 / §7.2.6.8 QOS
    字段定义（ql 0..3，2 bits）：

    - ``NOT_PERMITTED`` = ql=0，未使用 / 保留。
    - ``SHORT_PULSE`` = ql=1，短脉冲持续。
    - ``LONG_PULSE`` = ql=2，长脉冲持续。
    - ``PERSISTENT_OUTPUT`` = ql=3，持续输出。

    业务层按枚举直接操作；底层 ``to_byte()`` 仍按位级编码。
    """

    NOT_PERMITTED = "not_permitted"
    SHORT_PULSE = "short_pulse"
    LONG_PULSE = "long_pulse"
    PERSISTENT_OUTPUT = "persistent_output"


_SET_POINT_QL_TO_QUALIFIER: dict[int, SetPointQualifier] = {
    0: SetPointQualifier.NOT_PERMITTED,
    1: SetPointQualifier.SHORT_PULSE,
    2: SetPointQualifier.LONG_PULSE,
    3: SetPointQualifier.PERSISTENT_OUTPUT,
}

_SET_POINT_QUALIFIER_TO_QL: dict[SetPointQualifier, int] = {
    SetPointQualifier.NOT_PERMITTED: 0,
    SetPointQualifier.SHORT_PULSE: 1,
    SetPointQualifier.LONG_PULSE: 2,
    SetPointQualifier.PERSISTENT_OUTPUT: 3,
}


@dataclass
class SetPointCommandQualifier:
    """C_SE_* QOS 字段结构化语义。

    把 6 位位级 QOS 升级为结构化字段，便于业务层按协议语义理解与
    操作。S/E 位（byte bit 1）在协议中独立于 QOS 字段（byte bits
    2-7），本类只建模 QOS 字段（不含 S/E）。S/E 由对应的
    ``C_SE_*_Object.select_execute`` 单独维护。

    结构化字段与位级 QOS 严格 1:1 对应（与 C_SC_NA_1 的
    SingleCommandQualifier 布局类似）：

        bit 0 = RESERVED（保留为 0）
        bit 1-2 = ql (0..3)
        bit 3-5 = reserved (写入 0)

    Attributes:
        ql: 限定词 0..3。
        qualifier: 设定值命令限定词枚举。
        select_execute: S/E 位镜像（0=execute, 1=select）。
        qos: 6 位 QOS 字段位级镜像。
    """

    ql: int = 0
    qualifier: SetPointQualifier = SetPointQualifier.NOT_PERMITTED
    select_execute: int = 0
    qos: int = 0

    def __post_init__(self) -> None:
        if not 0 <= self.ql <= 3:
            raise ValueError(
                f"ql {self.ql} 超出范围 [0, 3]"
            )
        if self.select_execute not in (0, 1):
            raise ValueError(
                f"select_execute {self.select_execute} 必须为 0 或 1"
            )
        if not 0 <= self.qos <= 0x3F:
            raise ValueError(
                f"qos {self.qos} 超出范围 [0, 0x3F]"
            )
        if not isinstance(self.qualifier, SetPointQualifier):
            raise TypeError(
                f"qualifier 必须为 SetPointQualifier 实例，实际 "
                f"{type(self.qualifier).__name__}"
            )
        # 双向同步：qualifier <-> ql（ql 为权威源）
        if _SET_POINT_QUALIFIER_TO_QL[self.qualifier] != self.ql:
            self.qualifier = _SET_POINT_QL_TO_QUALIFIER[self.ql]
        # 重新计算 qos（按 ql 位布局）
        expected_qos = (self.ql & 0x03) << 1
        if self.qos != expected_qos:
            self.qos = expected_qos

    def to_byte(self) -> int:
        """编码为 6 位 QOS 字段值（不含 S/E 位）。"""
        byte = (self.ql & 0x03) << 1
        # bit 0/3-5 保留为 0
        return byte & 0x3F

    @classmethod
    def from_byte(cls, value: int) -> "SetPointCommandQualifier":
        """从 6 位 QOS 字段值解码。

        Args:
            value: 0..0x3F 范围内的位级值。

        Returns:
            解码后的 ``SetPointCommandQualifier`` 实例。
        """
        if value < 0 or value > 0x3F:
            raise ValueError(
                f"SetPointCommandQualifier.from_byte 期望 0..0x3F，"
                f"实际 {value}"
            )
        ql = (value >> 1) & 0x03
        obj = cls.__new__(cls)
        obj.ql = ql
        obj.qualifier = _SET_POINT_QL_TO_QUALIFIER[ql]
        obj.select_execute = 0
        obj.qos = value
        return obj


# ── C_SE_NA_1: Set-point command, normalized (without time tag) ───────────────


C_SE_NA_1_OBJECT_SIZE = 5  # NVA(2) + QOS(1) + S/E(2 bits) = 5 字节
# 字节布局：
#   byte 0-1: NVA（16-bit signed normalized value，little-endian）
#   byte 2:   QOS 字段（ql 2 bits + reserved；与 C_SC_NA_1 QU 类似）
#   byte 3:   S/E（1 bit）+ 0..6 bits reserved（按 lib60870 字节布局）
#   byte 4:   reserved（按 lib60870 字节布局）


@dataclass
class C_SE_NA_1_Object:
    """C_SE_NA_1 信息对象（归一化设定值命令，不带时标，已支持）。

    字节布局（5 字节）：

    - byte 0-1: NVA（16-bit signed normalized value，little-endian）
    - byte 2:   QOS 字段（ql 2 bits + reserved 6 bits）
    - byte 3:   S/E 位（bit 0 = select_execute，bit 1-7 reserved）
    - byte 4:   reserved（0x00）

    Attributes:
        nva: 归一化浮点值（-1.0 ~ +(1-1/32768)）。
        qos: 设定值命令限定词结构化字段。
        select_execute: 0=execute 执行，1=select 选择。
    """

    nva: float = 0.0
    qos: SetPointCommandQualifier = field(default=None)  # type: ignore[assignment]
    select_execute: int = 0

    def __post_init__(self) -> None:
        if self.qos is None:
            self.qos = SetPointCommandQualifier()
        if self.select_execute not in (0, 1):
            raise ValueError(
                f"select_execute {self.select_execute} 必须为 0 或 1"
            )
        if not -1.0 <= self.nva <= 32767.0 / 32768.0:
            raise ValueError(
                f"C_SE_NA_1 nva 值 {self.nva} 超出归一化范围 "
                f"[-1.0, +(1-1/32768)]"
            )
        if not isinstance(self.qos, SetPointCommandQualifier):
            raise TypeError(
                f"qos 字段必须为 SetPointCommandQualifier 实例，"
                f"实际 {type(self.qos).__name__}"
            )
        # 同步 S/E 镜像到 qos.select_execute（仅便利视图）
        self.qos.select_execute = self.select_execute

    def sync_qos(self) -> None:
        """显式将结构化 qos ql 字段回写到底层编码（无操作，保留接口）。"""
        # 当前实现：ql 已是 NVA 字节布局权威源，qos.to_byte() 在
        # encode 时调用；保留此方法以备后续引入更多 QOS 子字段。
        return None

    def encode(self) -> bytes:
        """编码为 5 字节信息体：NVA(2) + QOS(1) + S/E+reserved(2)。"""
        result = bytearray()
        result.extend(encode_normalized_value(self.nva))
        result.append(self.qos.to_byte() & 0xFF)
        result.append(self.select_execute & 0x01)  # S/E 位 + reserved 0
        result.append(0x00)  # reserved
        return bytes(result)

    @classmethod
    def decode(cls, data: bytes) -> "C_SE_NA_1_Object":
        """从 5 字节数据解码 C_SE_NA_1 信息体。

        Args:
            data: 至少 5 字节。

        Returns:
            解析后的 C_SE_NA_1_Object 实例。

        Raises:
            ValueError: 数据不足 5 字节。
        """
        if len(data) < C_SE_NA_1_OBJECT_SIZE:
            raise ValueError(
                f"C_SE_NA_1 解码需要至少 {C_SE_NA_1_OBJECT_SIZE} 字节，"
                f"实际只有 {len(data)} 字节"
            )
        nva = decode_normalized_value(data[:2])
        qos = SetPointCommandQualifier.from_byte(data[2])
        select_execute = data[3] & 0x01
        qos.select_execute = select_execute
        return cls(nva=nva, qos=qos, select_execute=select_execute)


# ── C_SE_NB_1: Set-point command, scaled (without time tag) ───────────────────


C_SE_NB_1_OBJECT_SIZE = 5  # SVA(2) + QOS(1) + S/E+reserved(2) = 5 字节


@dataclass
class C_SE_NB_1_Object:
    """C_SE_NB_1 信息对象（标度化设定值命令，不带时标，已支持）。

    字节布局（5 字节）：

    - byte 0-1: SVA（16-bit signed scaled value，little-endian）
    - byte 2:   QOS 字段（ql 2 bits + reserved 6 bits）
    - byte 3:   S/E 位（bit 0 = select_execute，bit 1-7 reserved）
    - byte 4:   reserved（0x00）

    Attributes:
        sva: 标度化整数值（-32768..+32767）。
        qos: 设定值命令限定词结构化字段。
        select_execute: 0=execute 执行，1=select 选择。
    """

    sva: int = 0
    qos: SetPointCommandQualifier = field(default=None)  # type: ignore[assignment]
    select_execute: int = 0

    def __post_init__(self) -> None:
        if self.qos is None:
            self.qos = SetPointCommandQualifier()
        if self.select_execute not in (0, 1):
            raise ValueError(
                f"select_execute {self.select_execute} 必须为 0 或 1"
            )
        if not -32768 <= self.sva <= 32767:
            raise ValueError(
                f"C_SE_NB_1 sva 值 {self.sva} 超出 int16 范围 "
                f"[-32768, 32767]"
            )
        if not isinstance(self.qos, SetPointCommandQualifier):
            raise TypeError(
                f"qos 字段必须为 SetPointCommandQualifier 实例，"
                f"实际 {type(self.qos).__name__}"
            )
        # 同步 S/E 镜像到 qos.select_execute
        self.qos.select_execute = self.select_execute

    def sync_qos(self) -> None:
        """显式将结构化 qos ql 字段回写到底层编码（无操作，保留接口）。"""
        return None

    def encode(self) -> bytes:
        """编码为 5 字节信息体：SVA(2) + QOS(1) + S/E+reserved(2)。"""
        result = bytearray()
        result.extend(encode_scaled_value(self.sva))
        result.append(self.qos.to_byte() & 0xFF)
        result.append(self.select_execute & 0x01)  # S/E 位 + reserved 0
        result.append(0x00)  # reserved
        return bytes(result)

    @classmethod
    def decode(cls, data: bytes) -> "C_SE_NB_1_Object":
        """从 5 字节数据解码 C_SE_NB_1 信息体。

        Args:
            data: 至少 5 字节。

        Returns:
            解析后的 C_SE_NB_1_Object 实例。

        Raises:
            ValueError: 数据不足 5 字节。
        """
        if len(data) < C_SE_NB_1_OBJECT_SIZE:
            raise ValueError(
                f"C_SE_NB_1 解码需要至少 {C_SE_NB_1_OBJECT_SIZE} 字节，"
                f"实际只有 {len(data)} 字节"
            )
        sva = decode_scaled_value(data[:2])
        qos = SetPointCommandQualifier.from_byte(data[2])
        select_execute = data[3] & 0x01
        qos.select_execute = select_execute
        return cls(sva=sva, qos=qos, select_execute=select_execute)


# ── C_SE_NC_1: Set-point command, short float (without time tag) ──────────────


C_SE_NC_1_OBJECT_SIZE = 7  # ShortFloat(4) + QOS(1) + S/E+reserved(2) = 7 字节


@dataclass
class C_SE_NC_1_Object:
    """C_SE_NC_1 信息对象（短浮点设定值命令，不带时标，已支持）。

    字节布局（7 字节）：

    - byte 0-3: ShortFloat（IEEE 754 32-bit，little-endian）
    - byte 4:   QOS 字段（ql 2 bits + reserved 6 bits）
    - byte 5:   S/E 位（bit 0 = select_execute，bit 1-7 reserved）
    - byte 6:   reserved（0x00）

    Attributes:
        sva: ShortFloat 浮点值（NaN/Inf 拒绝）。
        qos: 设定值命令限定词结构化字段。
        select_execute: 0=execute 执行，1=select 选择。
    """

    sva: float = 0.0
    qos: SetPointCommandQualifier = field(default=None)  # type: ignore[assignment]
    select_execute: int = 0

    def __post_init__(self) -> None:
        if self.qos is None:
            self.qos = SetPointCommandQualifier()
        if self.select_execute not in (0, 1):
            raise ValueError(
                f"select_execute {self.select_execute} 必须为 0 或 1"
            )
        if not isinstance(self.sva, float):
            raise TypeError(
                f"C_SE_NC_1 sva 字段必须为 float，实际 "
                f"{type(self.sva).__name__}"
            )
        if not isinstance(self.qos, SetPointCommandQualifier):
            raise TypeError(
                f"qos 字段必须为 SetPointCommandQualifier 实例，"
                f"实际 {type(self.qos).__name__}"
            )
        # 同步 S/E 镜像到 qos.select_execute
        self.qos.select_execute = self.select_execute

    def sync_qos(self) -> None:
        """显式将结构化 qos ql 字段回写到底层编码（无操作，保留接口）。"""
        return None

    def encode(self) -> bytes:
        """编码为 7 字节信息体：ShortFloat(4) + QOS(1) + S/E+reserved(2)。"""
        result = bytearray()
        result.extend(encode_short_float(self.sva))
        result.append(self.qos.to_byte() & 0xFF)
        result.append(self.select_execute & 0x01)  # S/E 位 + reserved 0
        result.append(0x00)  # reserved
        return bytes(result)

    @classmethod
    def decode(cls, data: bytes) -> "C_SE_NC_1_Object":
        """从 7 字节数据解码 C_SE_NC_1 信息体。

        Args:
            data: 至少 7 字节。

        Returns:
            解析后的 C_SE_NC_1_Object 实例。

        Raises:
            ValueError: 数据不足 7 字节。
        """
        if len(data) < C_SE_NC_1_OBJECT_SIZE:
            raise ValueError(
                f"C_SE_NC_1 解码需要至少 {C_SE_NC_1_OBJECT_SIZE} 字节，"
                f"实际只有 {len(data)} 字节"
            )
        sva = decode_short_float(data[:4])
        qos = SetPointCommandQualifier.from_byte(data[4])
        select_execute = data[5] & 0x01
        qos.select_execute = select_execute
        return cls(sva=sva, qos=qos, select_execute=select_execute)


# ── C_SE_TA_1 / C_SE_TB_1 / C_SE_TC_1: Set-point command with CP56Time2a ──────
# 已支持：三个带时标设定值命令。
# 字节布局（与 IEC 60870-5-101 §7.2.6.9/10/11 对齐）：
#   C_SE_TA_1: NVA(2) + QOS(1) + S/E(1) + reserved(1) + CP56Time2a(7) = 12 字节
#   C_SE_TB_1: SVA(2) + QOS(1) + S/E(1) + reserved(1) + CP56Time2a(7) = 12 字节
#   C_SE_TC_1: ShortFloat(4) + QOS(1) + S/E(1) + reserved(1)
#              + CP56Time2a(7) = 14 字节
# 注意：本模块**不实现真实写命令发送**；C_SE_TA_1/TB_1/TC_1 仅是命令
# codec，Iec101Facade 仍保持 supports_server=false /
# supports_serial_runtime=false / supports_write_runtime=false（避免
# command codec 被误解为真实写能力）。


# ── C_SE_TA_1: Set-point command, normalized, with CP56Time2a ────────────────


C_SE_TA_1_OBJECT_SIZE = 12  # NVA(2) + QOS(1) + S/E(1) + reserved(1) + CP56Time2a(7) = 12 字节


@dataclass
class C_SE_TA_1_Object:
    """C_SE_TA_1 信息对象（归一化设定值命令，带 CP56Time2a 时标，已支持）。

    字节布局（12 字节）：

    - byte 0-1:  NVA（16-bit signed normalized value，little-endian）
    - byte 2:    QOS 字段（ql 2 bits + reserved 6 bits）
    - byte 3:    S/E 位（bit 0 = select_execute，bit 1-7 reserved）
    - byte 4:    reserved（0x00）
    - byte 5-11: CP56Time2a 7 字节时标

    Attributes:
        nva: 归一化浮点值（-1.0 ~ +(1-1/32768)）。
        qos: 设定值命令限定词结构化字段。
        select_execute: 0=execute 执行，1=select 选择。
        time: CP56Time2a 时标。
    """

    nva: float = 0.0
    qos: SetPointCommandQualifier = field(default=None)  # type: ignore[assignment]
    select_execute: int = 0
    time: CP56Time2a = field(default=None)  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.qos is None:
            self.qos = SetPointCommandQualifier()
        if self.time is None:
            self.time = CP56Time2a()
        if self.select_execute not in (0, 1):
            raise ValueError(
                f"select_execute {self.select_execute} 必须为 0 或 1"
            )
        if not -1.0 <= self.nva <= 32767.0 / 32768.0:
            raise ValueError(
                f"C_SE_TA_1 nva 值 {self.nva} 超出归一化范围 "
                f"[-1.0, +(1-1/32768)]"
            )
        if not isinstance(self.qos, SetPointCommandQualifier):
            raise TypeError(
                f"qos 字段必须为 SetPointCommandQualifier 实例，"
                f"实际 {type(self.qos).__name__}"
            )
        if not isinstance(self.time, CP56Time2a):
            raise TypeError(
                f"time 字段必须为 CP56Time2a 实例，实际 {type(self.time).__name__}"
            )
        # 同步 S/E 镜像到 qos.select_execute（仅便利视图）
        self.qos.select_execute = self.select_execute

    def sync_qos(self) -> None:
        """显式将结构化 qos ql 字段回写到底层编码（无操作，保留接口）。"""
        return None

    def encode(self) -> bytes:
        """编码为 12 字节信息体：NVA(2) + QOS(1) + S/E(1) + reserved(1)
        + CP56Time2a(7)。"""
        result = bytearray()
        result.extend(encode_normalized_value(self.nva))
        result.append(self.qos.to_byte() & 0xFF)
        result.append(self.select_execute & 0x01)
        result.append(0x00)  # reserved
        result.extend(encode_cp56time2a(self.time))
        return bytes(result)

    @classmethod
    def decode(cls, data: bytes) -> "C_SE_TA_1_Object":
        """从 12 字节数据解码 C_SE_TA_1 信息体。

        Args:
            data: 至少 12 字节。

        Returns:
            解析后的 C_SE_TA_1_Object 实例。

        Raises:
            ValueError: 数据不足 12 字节。
        """
        if len(data) < C_SE_TA_1_OBJECT_SIZE:
            raise ValueError(
                f"C_SE_TA_1 解码需要至少 {C_SE_TA_1_OBJECT_SIZE} 字节，"
                f"实际只有 {len(data)} 字节"
            )
        nva = decode_normalized_value(data[:2])
        qos = SetPointCommandQualifier.from_byte(data[2])
        select_execute = data[3] & 0x01
        qos.select_execute = select_execute
        time_tag = decode_cp56time2a(data[5 : 5 + CP56TIME2A_LENGTH])
        return cls(
            nva=nva, qos=qos, select_execute=select_execute, time=time_tag,
        )


# ── C_SE_TB_1: Set-point command, scaled, with CP56Time2a ────────────────────


C_SE_TB_1_OBJECT_SIZE = 12  # SVA(2) + QOS(1) + S/E(1) + reserved(1) + CP56Time2a(7) = 12 字节


@dataclass
class C_SE_TB_1_Object:
    """C_SE_TB_1 信息对象（标度化设定值命令，带 CP56Time2a 时标，已支持）。

    字节布局（12 字节）：

    - byte 0-1:  SVA（16-bit signed scaled value，little-endian）
    - byte 2:    QOS 字段（ql 2 bits + reserved 6 bits）
    - byte 3:    S/E 位（bit 0 = select_execute，bit 1-7 reserved）
    - byte 4:    reserved（0x00）
    - byte 5-11: CP56Time2a 7 字节时标

    Attributes:
        sva: 标度化整数值（-32768..+32767）。
        qos: 设定值命令限定词结构化字段。
        select_execute: 0=execute 执行，1=select 选择。
        time: CP56Time2a 时标。
    """

    sva: int = 0
    qos: SetPointCommandQualifier = field(default=None)  # type: ignore[assignment]
    select_execute: int = 0
    time: CP56Time2a = field(default=None)  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.qos is None:
            self.qos = SetPointCommandQualifier()
        if self.time is None:
            self.time = CP56Time2a()
        if self.select_execute not in (0, 1):
            raise ValueError(
                f"select_execute {self.select_execute} 必须为 0 或 1"
            )
        if not -32768 <= self.sva <= 32767:
            raise ValueError(
                f"C_SE_TB_1 sva 值 {self.sva} 超出 int16 范围 "
                f"[-32768, 32767]"
            )
        if not isinstance(self.qos, SetPointCommandQualifier):
            raise TypeError(
                f"qos 字段必须为 SetPointCommandQualifier 实例，"
                f"实际 {type(self.qos).__name__}"
            )
        if not isinstance(self.time, CP56Time2a):
            raise TypeError(
                f"time 字段必须为 CP56Time2a 实例，实际 {type(self.time).__name__}"
            )
        # 同步 S/E 镜像到 qos.select_execute
        self.qos.select_execute = self.select_execute

    def sync_qos(self) -> None:
        """显式将结构化 qos ql 字段回写到底层编码（无操作，保留接口）。"""
        return None

    def encode(self) -> bytes:
        """编码为 12 字节信息体：SVA(2) + QOS(1) + S/E(1) + reserved(1)
        + CP56Time2a(7)。"""
        result = bytearray()
        result.extend(encode_scaled_value(self.sva))
        result.append(self.qos.to_byte() & 0xFF)
        result.append(self.select_execute & 0x01)
        result.append(0x00)  # reserved
        result.extend(encode_cp56time2a(self.time))
        return bytes(result)

    @classmethod
    def decode(cls, data: bytes) -> "C_SE_TB_1_Object":
        """从 12 字节数据解码 C_SE_TB_1 信息体。

        Args:
            data: 至少 12 字节。

        Returns:
            解析后的 C_SE_TB_1_Object 实例。

        Raises:
            ValueError: 数据不足 12 字节。
        """
        if len(data) < C_SE_TB_1_OBJECT_SIZE:
            raise ValueError(
                f"C_SE_TB_1 解码需要至少 {C_SE_TB_1_OBJECT_SIZE} 字节，"
                f"实际只有 {len(data)} 字节"
            )
        sva = decode_scaled_value(data[:2])
        qos = SetPointCommandQualifier.from_byte(data[2])
        select_execute = data[3] & 0x01
        qos.select_execute = select_execute
        time_tag = decode_cp56time2a(data[5 : 5 + CP56TIME2A_LENGTH])
        return cls(
            sva=sva, qos=qos, select_execute=select_execute, time=time_tag,
        )


# ── C_SE_TC_1: Set-point command, short float, with CP56Time2a ───────────────


C_SE_TC_1_OBJECT_SIZE = 14  # ShortFloat(4) + QOS(1) + S/E(1) + reserved(1) + CP56Time2a(7) = 14 字节


@dataclass
class C_SE_TC_1_Object:
    """C_SE_TC_1 信息对象（短浮点设定值命令，带 CP56Time2a 时标，已支持）。

    字节布局（14 字节）：

    - byte 0-3:  ShortFloat（IEEE 754 32-bit，little-endian）
    - byte 4:    QOS 字段（ql 2 bits + reserved 6 bits）
    - byte 5:    S/E 位（bit 0 = select_execute，bit 1-7 reserved）
    - byte 6:    reserved（0x00）
    - byte 7-13: CP56Time2a 7 字节时标

    Attributes:
        sva: ShortFloat 浮点值（NaN/Inf 拒绝）。
        qos: 设定值命令限定词结构化字段。
        select_execute: 0=execute 执行，1=select 选择。
        time: CP56Time2a 时标。
    """

    sva: float = 0.0
    qos: SetPointCommandQualifier = field(default=None)  # type: ignore[assignment]
    select_execute: int = 0
    time: CP56Time2a = field(default=None)  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.qos is None:
            self.qos = SetPointCommandQualifier()
        if self.time is None:
            self.time = CP56Time2a()
        if self.select_execute not in (0, 1):
            raise ValueError(
                f"select_execute {self.select_execute} 必须为 0 或 1"
            )
        if not isinstance(self.sva, float):
            raise TypeError(
                f"C_SE_TC_1 sva 字段必须为 float，实际 "
                f"{type(self.sva).__name__}"
            )
        if not isinstance(self.qos, SetPointCommandQualifier):
            raise TypeError(
                f"qos 字段必须为 SetPointCommandQualifier 实例，"
                f"实际 {type(self.qos).__name__}"
            )
        if not isinstance(self.time, CP56Time2a):
            raise TypeError(
                f"time 字段必须为 CP56Time2a 实例，实际 {type(self.time).__name__}"
            )
        # 同步 S/E 镜像到 qos.select_execute
        self.qos.select_execute = self.select_execute

    def sync_qos(self) -> None:
        """显式将结构化 qos ql 字段回写到底层编码（无操作，保留接口）。"""
        return None

    def encode(self) -> bytes:
        """编码为 14 字节信息体：ShortFloat(4) + QOS(1) + S/E(1)
        + reserved(1) + CP56Time2a(7)。"""
        result = bytearray()
        result.extend(encode_short_float(self.sva))
        result.append(self.qos.to_byte() & 0xFF)
        result.append(self.select_execute & 0x01)
        result.append(0x00)  # reserved
        result.extend(encode_cp56time2a(self.time))
        return bytes(result)

    @classmethod
    def decode(cls, data: bytes) -> "C_SE_TC_1_Object":
        """从 14 字节数据解码 C_SE_TC_1 信息体。

        Args:
            data: 至少 14 字节。

        Returns:
            解析后的 C_SE_TC_1_Object 实例。

        Raises:
            ValueError: 数据不足 14 字节。
        """
        if len(data) < C_SE_TC_1_OBJECT_SIZE:
            raise ValueError(
                f"C_SE_TC_1 解码需要至少 {C_SE_TC_1_OBJECT_SIZE} 字节，"
                f"实际只有 {len(data)} 字节"
            )
        sva = decode_short_float(data[:4])
        qos = SetPointCommandQualifier.from_byte(data[4])
        select_execute = data[5] & 0x01
        qos.select_execute = select_execute
        time_tag = decode_cp56time2a(data[7 : 7 + CP56TIME2A_LENGTH])
        return cls(
            sva=sva, qos=qos, select_execute=select_execute, time=time_tag,
        )


# ── M_SP_TA_1: Single-point information with time tag (CP56Time2a) ───────────


M_SP_TA_1_OBJECT_SIZE = 8  # SIQ(1) + CP56Time2a(7) = 8 字节


@dataclass
class M_SP_TA_1_Object:
    """M_SP_TA_1 信息对象（单点信息，带 CP56Time2a 时标）。

    信息体结构 = SIQ(1 byte) + CP56Time2a(7 bytes)，object body = 8 字节。

    Attributes:
        siq: 单点信息质量描述符。
        time: CP56Time2a 时标。
    """

    siq: SIQ
    time: CP56Time2a

    def encode(self) -> bytes:
        """编码为 8 字节信息体：SIQ(1) + CP56Time2a(7)。"""
        result = bytearray()
        result.extend(encode_siq(self.siq))
        result.extend(encode_cp56time2a(self.time))
        return bytes(result)

    @classmethod
    def decode(cls, data: bytes) -> "M_SP_TA_1_Object":
        """从 8 字节数据解码 M_SP_TA_1 信息体。

        Args:
            data: 至少 8 字节。

        Returns:
            解析后的 M_SP_TA_1_Object 实例。

        Raises:
            ValueError: 数据不足 8 字节。
        """
        if len(data) < M_SP_TA_1_OBJECT_SIZE:
            raise ValueError(
                f"M_SP_TA_1 解码需要至少 {M_SP_TA_1_OBJECT_SIZE} 字节，"
                f"实际只有 {len(data)} 字节"
            )
        siq = decode_siq(data[:1])
        time_tag = decode_cp56time2a(data[1 : 1 + CP56TIME2A_LENGTH])
        return cls(siq=siq, time=time_tag)


# ── M_DP_TA_1: Double-point information with time tag (CP56Time2a) ───────────


M_DP_TA_1_OBJECT_SIZE = 8  # DPI(1) + CP56Time2a(7) = 8 字节


@dataclass
class M_DP_TA_1_Object:
    """M_DP_TA_1 信息对象（双点信息，带 CP56Time2a 时标）。

    信息体结构 = DPI(1 byte) + CP56Time2a(7 bytes)，object body = 8 字节。

    Attributes:
        dpi: 双点信息状态（0-3，参见 DoublePointValue）。
        time: CP56Time2a 时标。
        reserved_high_bits: DPI 高 6 位（保留），默认为 0。
    """

    dpi: int = 0
    time: CP56Time2a = field(default=None)  # type: ignore[assignment]
    reserved_high_bits: int = 0

    def __post_init__(self) -> None:
        if self.time is None:
            self.time = CP56Time2a()
        if self.dpi < 0 or self.dpi > 3:
            raise ValueError(
                f"DPI 值 {self.dpi} 超出有效范围 [0, 3]"
            )
        if self.reserved_high_bits < 0 or self.reserved_high_bits > 0x3F:
            raise ValueError(
                f"reserved_high_bits {self.reserved_high_bits} 超出范围 [0, 0x3F]"
            )
        if not isinstance(self.time, CP56Time2a):
            raise TypeError(
                f"time 字段必须为 CP56Time2a 实例，实际 {type(self.time).__name__}"
            )

    def encode(self) -> bytes:
        """编码为 8 字节信息体：DPI(1) + CP56Time2a(7)。"""
        dpi_byte = (self.reserved_high_bits << 2) | (self.dpi & 0x03)
        result = bytearray([dpi_byte & 0xFF])
        result.extend(encode_cp56time2a(self.time))
        return bytes(result)

    @classmethod
    def decode(cls, data: bytes) -> "M_DP_TA_1_Object":
        """从 8 字节数据解码 M_DP_TA_1 信息体。"""
        if len(data) < M_DP_TA_1_OBJECT_SIZE:
            raise ValueError(
                f"M_DP_TA_1 解码需要至少 {M_DP_TA_1_OBJECT_SIZE} 字节，"
                f"实际只有 {len(data)} 字节"
            )
        byte = data[0]
        dpi = byte & 0x03
        reserved = (byte >> 2) & 0x3F
        time_tag = decode_cp56time2a(data[1 : 1 + CP56TIME2A_LENGTH])
        return cls(dpi=dpi, time=time_tag, reserved_high_bits=reserved)


# ── M_ME_TA_1: Measured value, normalized, with time tag (CP56Time2a) ─────────


M_ME_TA_1_OBJECT_SIZE = 10  # NVA(2) + QDS(1) + CP56Time2a(7) = 10 字节


@dataclass
class M_ME_TA_1_Object:
    """M_ME_TA_1 信息对象（归一化测量值，带 CP56Time2a 时标）。

    信息体结构 = NVA(2 bytes) + QDS(1 byte) + CP56Time2a(7 bytes)，
    object body = 10 字节。

    Attributes:
        nva: 归一化浮点值（-1.0 ~ +(1-1/32768)）。
        qds: 测量值质量描述符。
        time: CP56Time2a 时标。
    """

    nva: float = 0.0
    qds: QDS = field(default=None)  # type: ignore[assignment]
    time: CP56Time2a = field(default=None)  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.qds is None:
            self.qds = QDS()
        if self.time is None:
            self.time = CP56Time2a()
        if not isinstance(self.qds, QDS):
            raise TypeError(
                f"qds 字段必须为 QDS 实例，实际 {type(self.qds).__name__}"
            )
        if not isinstance(self.time, CP56Time2a):
            raise TypeError(
                f"time 字段必须为 CP56Time2a 实例，实际 {type(self.time).__name__}"
            )

    def encode(self) -> bytes:
        """编码为 10 字节信息体：NVA(2) + QDS(1) + CP56Time2a(7)。"""
        result = bytearray()
        result.extend(encode_normalized_value(self.nva))
        result.extend(encode_qds(self.qds))
        result.extend(encode_cp56time2a(self.time))
        return bytes(result)

    @classmethod
    def decode(cls, data: bytes) -> "M_ME_TA_1_Object":
        """从 10 字节数据解码 M_ME_TA_1 信息体。"""
        if len(data) < M_ME_TA_1_OBJECT_SIZE:
            raise ValueError(
                f"M_ME_TA_1 解码需要至少 {M_ME_TA_1_OBJECT_SIZE} 字节，"
                f"实际只有 {len(data)} 字节"
            )
        nva = decode_normalized_value(data[:2])
        qds = decode_qds(data[2:3])
        time_tag = decode_cp56time2a(data[3 : 3 + CP56TIME2A_LENGTH])
        return cls(nva=nva, qds=qds, time=time_tag)


# ── M_ME_TB_1: Measured value, scaled, with time tag (CP56Time2a) ──────────────


M_ME_TB_1_OBJECT_SIZE = 10  # SVA(2) + QDS(1) + CP56Time2a(7) = 10 字节


@dataclass
class M_ME_TB_1_Object:
    """M_ME_TB_1 信息对象（标度化测量值，带 CP56Time2a 时标）。

    信息体结构 = SVA(2 bytes, 16-bit signed int) + QDS(1 byte)
    + CP56Time2a(7 bytes)，object body = 10 字节。

    语义说明：SVA 是 16-bit 有符号整数（-32768..+32767），
    不带量纲语义；量程与单位由 device profile / 业务侧解释。
    编码：小端序 int16。

    Attributes:
        sva: 标度化整数值（-32768..+32767）。
        qds: 测量值质量描述符。
        time: CP56Time2a 时标。
    """

    sva: int = 0
    qds: QDS = field(default=None)  # type: ignore[assignment]
    time: CP56Time2a = field(default=None)  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.qds is None:
            self.qds = QDS()
        if self.time is None:
            self.time = CP56Time2a()
        if not -32768 <= self.sva <= 32767:
            raise ValueError(
                f"M_ME_TB_1 sva 值 {self.sva} 超出 int16 范围 [-32768, 32767]"
            )
        if not isinstance(self.qds, QDS):
            raise TypeError(
                f"qds 字段必须为 QDS 实例，实际 {type(self.qds).__name__}"
            )
        if not isinstance(self.time, CP56Time2a):
            raise TypeError(
                f"time 字段必须为 CP56Time2a 实例，实际 {type(self.time).__name__}"
            )

    def encode(self) -> bytes:
        """编码为 10 字节信息体：SVA(2) + QDS(1) + CP56Time2a(7)。"""
        result = bytearray()
        result.extend(struct.pack("<h", self.sva))
        result.extend(encode_qds(self.qds))
        result.extend(encode_cp56time2a(self.time))
        return bytes(result)

    @classmethod
    def decode(cls, data: bytes) -> "M_ME_TB_1_Object":
        """从 10 字节数据解码 M_ME_TB_1 信息体。"""
        if len(data) < M_ME_TB_1_OBJECT_SIZE:
            raise ValueError(
                f"M_ME_TB_1 解码需要至少 {M_ME_TB_1_OBJECT_SIZE} 字节，"
                f"实际只有 {len(data)} 字节"
            )
        (sva,) = struct.unpack("<h", data[:2])
        qds = decode_qds(data[2:3])
        time_tag = decode_cp56time2a(data[3 : 3 + CP56TIME2A_LENGTH])
        return cls(sva=sva, qds=qds, time=time_tag)


# ── M_ME_TC_1: Measured value, short float, with time tag (CP56Time2a) ────────


M_ME_TC_1_OBJECT_SIZE = 12  # ShortFloat(4) + QDS(1) + CP56Time2a(7) = 12 字节


@dataclass
class M_ME_TC_1_Object:
    """M_ME_TC_1 信息对象（短浮点测量值，带 CP56Time2a 时标）。

    信息体结构 = ShortFloat(4 bytes, IEEE 754 LE) + QDS(1 byte)
    + CP56Time2a(7 bytes)，object body = 12 字节。

    语义说明：ShortFloat 携带 IEEE 754 single-precision 浮点；
    编码/解码时拒绝 NaN/Inf（详见
    ``information_elements.encode_short_float`` /
    ``decode_short_float``）。业务方如需支持 NaN/Inf，应在边界
    层映射为 QDS.invalid=True 等协议层约定的占位状态。

    Attributes:
        sva: ShortFloat 浮点值（NaN/Inf 拒绝）。
        qds: 测量值质量描述符。
        time: CP56Time2a 时标。
    """

    sva: float = 0.0
    qds: QDS = field(default=None)  # type: ignore[assignment]
    time: CP56Time2a = field(default=None)  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.qds is None:
            self.qds = QDS()
        if self.time is None:
            self.time = CP56Time2a()
        if not isinstance(self.sva, float):
            raise TypeError(
                f"M_ME_TC_1 sva 字段必须为 float，实际 {type(self.sva).__name__}"
            )
        if not isinstance(self.qds, QDS):
            raise TypeError(
                f"qds 字段必须为 QDS 实例，实际 {type(self.qds).__name__}"
            )
        if not isinstance(self.time, CP56Time2a):
            raise TypeError(
                f"time 字段必须为 CP56Time2a 实例，实际 {type(self.time).__name__}"
            )

    def encode(self) -> bytes:
        """编码为 12 字节信息体：ShortFloat(4) + QDS(1) + CP56Time2a(7)。"""
        result = bytearray()
        result.extend(encode_short_float(self.sva))
        result.extend(encode_qds(self.qds))
        result.extend(encode_cp56time2a(self.time))
        return bytes(result)

    @classmethod
    def decode(cls, data: bytes) -> "M_ME_TC_1_Object":
        """从 12 字节数据解码 M_ME_TC_1 信息体。"""
        if len(data) < M_ME_TC_1_OBJECT_SIZE:
            raise ValueError(
                f"M_ME_TC_1 解码需要至少 {M_ME_TC_1_OBJECT_SIZE} 字节，"
                f"实际只有 {len(data)} 字节"
            )
        sva = decode_short_float(data[:4])
        qds = decode_qds(data[4:5])
        time_tag = decode_cp56time2a(data[5 : 5 + CP56TIME2A_LENGTH])
        return cls(sva=sva, qds=qds, time=time_tag)


__all__ = [
    "M_SP_NA_1_OBJECT_SIZE",
    "M_DP_NA_1_OBJECT_SIZE",
    "M_ME_NA_1_OBJECT_SIZE",
    "M_ME_NB_1_OBJECT_SIZE",
    "M_ME_NC_1_OBJECT_SIZE",
    "C_SC_NA_1_OBJECT_SIZE",
    "C_SE_NA_1_OBJECT_SIZE",
    "C_SE_NB_1_OBJECT_SIZE",
    "C_SE_NC_1_OBJECT_SIZE",
    "C_SE_TA_1_OBJECT_SIZE",
    "C_SE_TB_1_OBJECT_SIZE",
    "C_SE_TC_1_OBJECT_SIZE",
    "M_SP_TA_1_OBJECT_SIZE",
    "M_DP_TA_1_OBJECT_SIZE",
    "M_ME_TA_1_OBJECT_SIZE",
    "M_ME_TB_1_OBJECT_SIZE",
    "M_ME_TC_1_OBJECT_SIZE",
    "CommandPulse",
    "DoublePointValue",
    "SetPointQualifier",
    "SingleCommandQualifier",
    "SetPointCommandQualifier",
    "M_SP_NA_1_Object",
    "M_DP_NA_1_Object",
    "M_ME_NA_1_Object",
    "M_ME_NB_1_Object",
    "M_ME_NC_1_Object",
    "C_SC_NA_1_Object",
    "C_SE_NA_1_Object",
    "C_SE_NB_1_Object",
    "C_SE_NC_1_Object",
    "C_SE_TA_1_Object",
    "C_SE_TB_1_Object",
    "C_SE_TC_1_Object",
    "M_SP_TA_1_Object",
    "M_DP_TA_1_Object",
    "M_ME_TA_1_Object",
    "M_ME_TB_1_Object",
    "M_ME_TC_1_Object",
]
