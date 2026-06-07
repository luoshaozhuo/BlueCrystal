"""IEC 60870-5-101 公共地址（CA）编解码。

CA 为 2 字节小端序无符号整数（0-65535），
在 ASDU 头部中标识控制站或被控站地址。

不负责：CA 零地址（广播）的特殊语义处理。
"""

from __future__ import annotations

import struct

CA_LENGTH = 2  # CA 固定 2 字节（IEC 101 标准默认）


def encode_common_address(ca: int) -> bytes:
    """将 CA 整数值编码为 2 字节小端序字节串。

    范围：0 到 2^16 - 1 (65535)。

    Args:
        ca: 公共地址整数值。

    Returns:
        2 字节 CA 字节串（小端序）。

    Raises:
        ValueError: ca 超出 [0, 65535] 范围。
    """
    if ca < 0 or ca > 65535:
        raise ValueError(
            f"CA 值 {ca} 超出有效范围 [0, 65535]"
        )
    return struct.pack("<H", ca)


def decode_common_address(data: bytes) -> int:
    """从 2 字节数据解码 CA 整数值。

    Args:
        data: 包含 CA 的字节串（至少 2 字节，仅读取前 2 字节）。

    Returns:
        解码后的 CA 整数值。

    Raises:
        ValueError: 数据不足 2 字节。
    """
    if len(data) < CA_LENGTH:
        raise ValueError(
            f"CA 解码需要至少 {CA_LENGTH} 字节，实际只有 {len(data)} 字节"
        )
    value: int = struct.unpack("<H", data[:2])[0]
    return value


__all__ = ["encode_common_address", "decode_common_address", "CA_LENGTH"]
