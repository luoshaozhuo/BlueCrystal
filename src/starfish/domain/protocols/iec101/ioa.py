"""IEC 60870-5-101 信息对象地址（IOA）编解码。

IOA 为 3 字节小端序无符号整数（0-16777215），
标识 ASDU 内每个信息对象的地址。

不负责：多 IOA 循环展开、IOA 范围校验。
"""

from __future__ import annotations

import struct

IOA_LENGTH = 3  # IOA 固定 3 字节


def encode_information_object_address(ioa: int) -> bytes:
    """将 IOA 整数值编码为 3 字节小端序字节串。

    范围：0 到 2^24 - 1 (16777215)。

    Args:
        ioa: 信息对象地址整数值。

    Returns:
        3 字节 IOA 字节串（小端序）。

    Raises:
        ValueError: ioa 超出 [0, 16777215] 范围。
    """
    if ioa < 0 or ioa > 16777215:
        raise ValueError(
            f"IOA 值 {ioa} 超出有效范围 [0, 16777215]"
        )
    # struct.pack("<I") 产生 4 字节，截取前 3 字节
    raw = struct.pack("<I", ioa & 0xFFFFFF)
    return raw[:3]


def decode_information_object_address(data: bytes) -> int:
    """从 3 字节数据解码 IOA 整数值。

    Args:
        data: 包含 IOA 的字节串（至少 3 字节，仅读取前 3 字节）。

    Returns:
        解码后的 IOA 整数值。

    Raises:
        ValueError: 数据不足 3 字节。
    """
    if len(data) < IOA_LENGTH:
        raise ValueError(
            f"IOA 解码需要至少 {IOA_LENGTH} 字节，实际只有 {len(data)} 字节"
        )
    # 补 0 到 4 字节再解包
    padded = data[:3] + b"\x00"
    value: int = struct.unpack("<I", padded)[0]
    return value


__all__ = [
    "encode_information_object_address",
    "decode_information_object_address",
    "IOA_LENGTH",
]
