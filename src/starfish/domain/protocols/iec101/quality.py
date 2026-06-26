"""IEC 60870-5-101 信息体质量描述符（Quality Descriptor）编解码。

本模块定义 IEC 60870-5-101 协议中使用的两类质量描述符：

- SIQ (Single-point Information Quality descriptor)：
    单点信息质量描述符，1 字节长度，附在 M_SP_NA_1 / M_SP_TA_1 等
    单点信息体之后，描述该信息点的当前质量。
- QDS (Quality Descriptor for Measured Values)：
    测量值质量描述符，1 字节长度，附在 M_ME_NA_1 / M_ME_NB_1 / M_ME_NC_1
    等测量值信息体之后，描述该测量值的质量。

两类描述符均使用 IntFlag 风格的位标志位组合表达多维质量状态。

不负责：
- 时标信息（CP56Time2a 等）的质量位处理。
- 信息体本身的语义解析。
- 与 IEC 60870-5-104 的语义差异（位定义基本一致，编码相同）。
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntFlag


class SIQFlags(IntFlag):
    """单点信息质量描述符（SIQ）的位标志。

    位布局（低 7 位为质量位，bit 7 保留为 0）：

    - bit 0 (0x01) - SPI: Single-Point Information
        0 = 断开 (OFF)，1 = 接通 (ON)。
    - bit 1 (0x02) - BL: Blocked / 被闭锁
    - bit 2 (0x04) - SB: Substituted / 被取代
    - bit 3 (0x08) - NT: Not Topical / 非最新
    - bit 4 (0x10) - IV: Invalid / 无效
    - bit 5 (0x20) - RES1: 保留
    - bit 6 (0x40) - RES2: 保留
    - bit 7 (0x80) - RES3: 保留
    """

    SPI_OFF = 0x00
    SPI_ON = 0x01
    BLOCKED = 0x02
    SUBSTITUTED = 0x04
    NOT_TOPICAL = 0x08
    INVALID = 0x10
    RES1 = 0x20
    RES2 = 0x40
    RES3 = 0x80


class QDSFlags(IntFlag):
    """测量值质量描述符（QDS）的位标志。

    位布局（bit 0-7 全部为质量位）：

    - bit 0 (0x01) - OV: Overflow / 溢出
    - bit 1 (0x02) - RES1: 保留
    - bit 2 (0x04) - BL: Blocked / 被闭锁
    - bit 3 (0x08) - SB: Substituted / 被取代
    - bit 4 (0x10) - NT: Not Topical / 非最新
    - bit 5 (0x20) - IV: Invalid / 无效
    - bit 6 (0x40) - RES2: 保留
    - bit 7 (0x80) - RES3: 保留
    """

    OVERFLOW = 0x01
    RES1 = 0x02
    BLOCKED = 0x04
    SUBSTITUTED = 0x08
    NOT_TOPICAL = 0x10
    INVALID = 0x20
    RES2 = 0x40
    RES3 = 0x80


SIQ_LENGTH = 1  # SIQ 固定 1 字节
QDS_LENGTH = 1  # QDS 固定 1 字节


@dataclass
class SIQ:
    """单点信息质量描述符（SIQ）数据类。

    携带单点信息（boolean-like）的当前质量状态。
    在 M_SP_NA_1 / M_SP_TA_1 信息体中紧接在值字段之后。

    Attributes:
        value: 布尔状态，True=ON（接通），False=OFF（断开）。
        blocked: True 表示该信息点被闭锁。
        substituted: True 表示该信息点的值已被手动替代。
        not_topical: True 表示该信息点非最新（采集失败/未刷新）。
        invalid: True 表示该信息点无效。
    """

    value: bool = False
    blocked: bool = False
    substituted: bool = False
    not_topical: bool = False
    invalid: bool = False

    def to_flags(self) -> int:
        """将 SIQ 数据类编码为 SIQFlags 位标志位整数。

        Returns:
            1 字节 SIQ 位标志位整数（0-255）。
        """
        flags = SIQFlags.SPI_ON if self.value else SIQFlags.SPI_OFF
        if self.blocked:
            flags |= SIQFlags.BLOCKED
        if self.substituted:
            flags |= SIQFlags.SUBSTITUTED
        if self.not_topical:
            flags |= SIQFlags.NOT_TOPICAL
        if self.invalid:
            flags |= SIQFlags.INVALID
        return int(flags) & 0xFF

    @classmethod
    def from_flags(cls, flags: int) -> "SIQ":
        """从 SIQFlags 位标志位整数解码 SIQ 数据类。

        Args:
            flags: 1 字节 SIQ 位标志位整数（0-255）。

        Returns:
            解析后的 SIQ 数据类。
        """
        return cls(
            value=bool(flags & SIQFlags.SPI_ON),
            blocked=bool(flags & SIQFlags.BLOCKED),
            substituted=bool(flags & SIQFlags.SUBSTITUTED),
            not_topical=bool(flags & SIQFlags.NOT_TOPICAL),
            invalid=bool(flags & SIQFlags.INVALID),
        )


@dataclass
class QDS:
    """测量值质量描述符（QDS）数据类。

    携带测量值（normalized/scaled/float）的当前质量状态。
    在 M_ME_NA_1 / M_ME_NB_1 / M_ME_NC_1 等信息体中紧接在值字段之后。

    Attributes:
        overflow: True 表示测量值超出量程上限/下限。
        blocked: True 表示该信息点被闭锁。
        substituted: True 表示该信息点的值已被手动替代。
        not_topical: True 表示该信息点非最新（采集失败/未刷新）。
        invalid: True 表示该信息点无效。
    """

    overflow: bool = False
    blocked: bool = False
    substituted: bool = False
    not_topical: bool = False
    invalid: bool = False

    def to_flags(self) -> int:
        """将 QDS 数据类编码为 QDSFlags 位标志位整数。

        Returns:
            1 字节 QDS 位标志位整数（0-255）。
        """
        flags = QDSFlags(0)
        if self.overflow:
            flags |= QDSFlags.OVERFLOW
        if self.blocked:
            flags |= QDSFlags.BLOCKED
        if self.substituted:
            flags |= QDSFlags.SUBSTITUTED
        if self.not_topical:
            flags |= QDSFlags.NOT_TOPICAL
        if self.invalid:
            flags |= QDSFlags.INVALID
        return int(flags) & 0xFF

    @classmethod
    def from_flags(cls, flags: int) -> "QDS":
        """从 QDSFlags 位标志位整数解码 QDS 数据类。

        Args:
            flags: 1 字节 QDS 位标志位整数（0-255）。

        Returns:
            解析后的 QDS 数据类。
        """
        return cls(
            overflow=bool(flags & QDSFlags.OVERFLOW),
            blocked=bool(flags & QDSFlags.BLOCKED),
            substituted=bool(flags & QDSFlags.SUBSTITUTED),
            not_topical=bool(flags & QDSFlags.NOT_TOPICAL),
            invalid=bool(flags & QDSFlags.INVALID),
        )


def encode_siq(siq: SIQ) -> bytes:
    """将 SIQ 数据类编码为 1 字节。

    Args:
        siq: SIQ 数据类实例。

    Returns:
        1 字节 SIQ 编码结果。
    """
    return bytes([siq.to_flags() & 0xFF])


def decode_siq(data: bytes) -> SIQ:
    """从 1 字节数据解码 SIQ 数据类。

    Args:
        data: 包含 SIQ 的字节串（至少 1 字节，仅读取第 1 字节）。

    Returns:
        解析后的 SIQ 数据类。

    Raises:
        ValueError: 数据不足 1 字节。
    """
    if len(data) < SIQ_LENGTH:
        raise ValueError(
            f"SIQ 解码需要至少 {SIQ_LENGTH} 字节，实际只有 {len(data)} 字节"
        )
    return SIQ.from_flags(data[0])


def encode_qds(qds: QDS) -> bytes:
    """将 QDS 数据类编码为 1 字节。

    Args:
        qds: QDS 数据类实例。

    Returns:
        1 字节 QDS 编码结果。
    """
    return bytes([qds.to_flags() & 0xFF])


def decode_qds(data: bytes) -> QDS:
    """从 1 字节数据解码 QDS 数据类。

    Args:
        data: 包含 QDS 的字节串（至少 1 字节，仅读取第 1 字节）。

    Returns:
        解析后的 QDS 数据类。

    Raises:
        ValueError: 数据不足 1 字节。
    """
    if len(data) < QDS_LENGTH:
        raise ValueError(
            f"QDS 解码需要至少 {QDS_LENGTH} 字节，实际只有 {len(data)} 字节"
        )
    return QDS.from_flags(data[0])


__all__ = [
    "SIQFlags",
    "QDSFlags",
    "SIQ",
    "QDS",
    "SIQ_LENGTH",
    "QDS_LENGTH",
    "encode_siq",
    "decode_siq",
    "encode_qds",
    "decode_qds",
]
