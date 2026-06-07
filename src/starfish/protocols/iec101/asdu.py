"""IEC 60870-5-101 ASDU 头部编解码。

本模块提供 ASDUHeader 数据类和 ASDU 头部的编码/解码函数。

ASDU 头部结构（最小 6 字节，无长度域）：
    - TypeId (1 byte): ASDU 类型标识符
    - VSQ (1 byte): 可变结构限定词
        - bit 0-6: 信息对象数量（number of IO, 最大 127）
        - bit 7: SQ (sequence) 标志，0=独立地址，1=顺序地址
    - COT (1 byte): 传输原因
        - bit 0-5: 原因码（CauseOfTransmission 枚举值）
        - bit 6: P/N 标志 (0=肯定，1=否定)
        - bit 7: T 标志 (0=未试验，1=试验)
    - CA (2 bytes, 小端序): 公共地址（Common Address）
      （注：在某些链路层配置中 CA 可能不存在，按 CommonAddressLength 决定）

能力边界（骨架阶段）：
    已实现: ASDUHeader 数据类定义、encode/decode 6 字节标准头部。
    未实现: 长度域编码、非标准 CA 长度、信息对象编解码。

不负责：校验 TypeId/COT/VSQ 合法性（由调用方负责）。
"""

from __future__ import annotations

import struct
from dataclasses import dataclass


ASDU_HEADER_MIN_LENGTH = 5  # TypeId(1) + VSQ(1) + COT(1) + CA(2)


@dataclass
class ASDUHeader:
    """IEC 60870-5-101 ASDU 头部。

    描述 ASDU 的类型、传输原因、公共地址和结构信息。
    信息对象的具体内容不包含在此头部中。

    Attributes:
        type_id: ASDU 类型标识（TypeId 枚举的整数值）。
        vsq: 可变结构限定词（bit 0-6: IO 数量, bit 7: SQ 标志）。
        cot: 传输原因（bit 0-5: 原因码, bit 6: P/N, bit 7: T）。
        ca: 公共地址（实际使用 1 或 2 字节，默认 2 字节小端序）。
        ioa_count: 信息对象数量（从 VSQ bit 0-6 解析出，便于访问）。
        sq: 顺序寻址标志（从 VSQ bit 7 解析出）。
    """

    type_id: int = 0
    vsq: int = 0
    cot: int = 0
    ca: int = 0
    ioa_count: int = 0
    sq: bool = False

    @property
    def pn(self) -> bool:
        """P/N 位：True 表示否定确认。"""
        return bool(self.cot & 0x40)

    @property
    def t(self) -> bool:
        """T 位（试验标志）：True 表示试验报文。"""
        return bool(self.cot & 0x80)

    @property
    def cot_cause(self) -> int:
        """纯原因码（不含 P/N、T 位）。"""
        return self.cot & 0x3F


def encode_asdu_header(header: ASDUHeader) -> bytes:
    """将 ASDUHeader 编码为 6 字节头部。

    编码顺序: TypeId(1) VSQ(1) COT(1) CA(2, little-endian)。

    Args:
        header: 要编码的 ASDUHeader 实例。
            vsq 必须已包含 SQ 位和数量。
            cot 必须已包含 P/N 位和 T 位。

    Returns:
        编码后的 6 字节头部。
    """
    result = bytearray()
    result.append(header.type_id & 0xFF)
    result.append(header.vsq & 0xFF)
    result.append(header.cot & 0xFF)
    result.extend(struct.pack("<H", header.ca & 0xFFFF))
    return bytes(result)


def decode_asdu_header(data: bytes) -> ASDUHeader:
    """从 6 字节数据解码 ASDU 头部。

    解码顺序: TypeId(1) VSQ(1) COT(1) CA(2, little-endian)。

    Args:
        data: 包含 ASDU 头部的字节串（至少 6 字节）。

    Returns:
        解析后的 ASDUHeader 实例。

    Raises:
        ValueError: 数据不足 6 字节。
    """
    if len(data) < ASDU_HEADER_MIN_LENGTH:
        raise ValueError(
            f"ASDU 头部需要至少 {ASDU_HEADER_MIN_LENGTH} 字节，"
            f"实际只有 {len(data)} 字节"
        )

    type_id = data[0]
    vsq = data[1]
    cot = data[2]
    ca = struct.unpack("<H", data[3:5])[0]

    ioa_count = vsq & 0x7F
    sq = bool(vsq & 0x80)

    return ASDUHeader(
        type_id=type_id,
        vsq=vsq,
        cot=cot,
        ca=ca,
        ioa_count=ioa_count,
        sq=sq,
    )


__all__ = ["ASDUHeader", "encode_asdu_header", "decode_asdu_header", "ASDU_HEADER_MIN_LENGTH"]
