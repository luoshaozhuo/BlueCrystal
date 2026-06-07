"""IEC 60870-5-101 FT1.2 链路帧编解码。

本模块实现 IEC 60870-5-101 协议附录（FT1.2 Frame Format）的链路层
帧编解码，包括：

- 固定长度帧（Fixed Length Frame）：
    5 字节：start(1) + data(1) + checksum(1) + end(1) + 校验和 padding(0)
    实际：start(0x10) + control(1) + checksum(1) + end(0x16) = 5 字节
    用于链路层控制/确认/请求等短帧。
    数据区固定 1 字节，校验和 = (control + data) & 0xFF 后取补码。

- 可变长度帧（Variable Length Frame）：
    start(1=0x68) + length(1) + length(1) + data(length) + checksum(1) + end(1=0x16)
    最小 5 字节；最大 length=255 时 data=255 字节，总长 6+255=261 字节。
    校验和 = sum(data) & 0xFF 后取补码。

- 帧起始 / 结束字符：
    固定帧: 0x10 / 0x16
    可变帧: 0x68 / 0x16

不负责：
- 完整 balanced/unbalanced 传输模式状态机。
- 真实串口/PTY 收发、字节流解析。
- 物理层（RS-232/RS-485）参数配置。
- 链路层超时、重试、滑动窗口。

实现约束：
- 仅 frame codec，不构成 server。
- checksum 算法：取数据字节之和 mod 256，再取 1 的补码（256 - sum % 256，
  当结果等于 0 时用 0xFF 替代；这是 IEC 60870-5-1 / FT1.2 规范）。
  本实现采用：(sum & 0xFF) 后取 1 的补码（= 0xFF - (sum & 0xFF)）。
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum


# ── 帧字符常量 ──────────────────────────────────────────────────────────────────


START_CHAR_FIXED = 0x10  # 固定长度帧起始字符
END_CHAR = 0x16  # 帧结束字符（固定/可变通用）
START_CHAR_VARIABLE = 0x68  # 可变长度帧起始字符


class LinkControl(IntEnum):
    """FT1.2 链路层控制字段常见取值（仅子集，用于测试与编解码验证）。

    - RESET: 0x40, link reset / FCB/FCV reset request
    - RESET_ACK: 0x20, link reset acknowledge
    - USER_DATA: 0x07, user data (balanced mode, no reply)
    - USER_DATA_REPLY: 0x0B, user data (balanced mode, request reply)
    - USER_DATA_NOREPLY: 0x07, 同 USER_DATA
    - SUPERVISORY: 0x01, supervisory function (e.g. ACK of link layer)
    """

    SUPERVISORY = 0x01
    USER_DATA_NOREPLY = 0x07
    USER_DATA_REPLY = 0x0B
    RESET_ACK = 0x20
    RESET = 0x40


FIXED_FRAME_SIZE = 4  # 固定帧总长 4 字节：0x10 + control(1) + cs(1) + 0x16
VARIABLE_FRAME_HEADER_SIZE = 3  # start(1) + length(1) + length(1) = 3
VARIABLE_FRAME_OVERHEAD = 5  # start(1) + length(2) + checksum(1) + end(1) = 5
VARIABLE_FRAME_MAX_PAYLOAD = 255
VARIABLE_FRAME_MAX_SIZE = VARIABLE_FRAME_OVERHEAD + VARIABLE_FRAME_MAX_PAYLOAD


# ── 校验和算法 ──────────────────────────────────────────────────────────────────


def compute_checksum(data: bytes) -> int:
    """计算 FT1.2 校验和。

    算法：
        sum_bytes = sum(data) & 0xFF
        checksum = (~sum_bytes) & 0xFF  # 取 1 的补码

    边界：当 sum_bytes == 0 时，checksum = 0xFF（保持非 0，避免与 0 混淆）。

    Args:
        data: 要计算校验和的数据字节。

    Returns:
        1 字节校验和（0-255）。
    """
    if not data:
        return 0xFF  # 空数据也返回非零校验
    sum_bytes = sum(data) & 0xFF
    return (~sum_bytes) & 0xFF


def verify_checksum(data: bytes, checksum: int) -> bool:
    """验证 FT1.2 校验和是否匹配。

    Args:
        data: 已计算的字节串。
        checksum: 期望的校验和字节。

    Returns:
        True 表示校验通过，False 表示校验失败。
    """
    return compute_checksum(data) == (checksum & 0xFF)


# ── 固定长度帧编解码 ───────────────────────────────────────────────────────────


@dataclass
class FixedFrame:
    """FT1.2 固定长度帧（5 字节）。

    帧结构：
        0x10 + control(1) + checksum(1) + 0x16
    数据区为 1 字节（control 字段），由链路层解释（reset / ACK / supervisory 等）。

    Attributes:
        control: 控制字段字节（参见 LinkControl 枚举）。
    """

    control: int

    def __post_init__(self) -> None:
        if self.control < 0 or self.control > 0xFF:
            raise ValueError(
                f"控制字段值 {self.control} 超出 [0, 0xFF] 范围"
            )

    def encode(self) -> bytes:
        """编码为 5 字节固定长度帧。"""
        data = bytes([self.control])
        cs = compute_checksum(data)
        return bytes([START_CHAR_FIXED, self.control, cs, END_CHAR])

    @classmethod
    def decode(cls, data: bytes) -> "FixedFrame":
        """从 5 字节数据解码固定长度帧。

        Args:
            data: 5 字节固定帧。

        Returns:
            解析后的 FixedFrame 实例。

        Raises:
            FrameError: 帧格式或校验错误。
        """
        if len(data) != FIXED_FRAME_SIZE:
            raise FrameError(
                f"固定长度帧应为 {FIXED_FRAME_SIZE} 字节，"
                f"实际只有 {len(data)} 字节"
            )
        if data[0] != START_CHAR_FIXED:
            raise FrameError(
                f"固定长度帧起始字符应为 0x{START_CHAR_FIXED:02X}，"
                f"实际为 0x{data[0]:02X}"
            )
        if data[3] != END_CHAR:
            raise FrameError(
                f"固定长度帧结束字符应为 0x{END_CHAR:02X}，"
                f"实际为 0x{data[3]:02X}"
            )
        if not verify_checksum(bytes([data[1]]), data[2]):
            raise FrameError(
                f"固定长度帧校验和错误: control=0x{data[1]:02X}, "
                f"cs=0x{data[2]:02X}"
            )
        return cls(control=data[1])


# ── 可变长度帧编解码 ───────────────────────────────────────────────────────────


@dataclass
class VariableFrame:
    """FT1.2 可变长度帧（5 - 261 字节）。

    帧结构：
        0x68 + length + length + data(length bytes) + checksum + 0x16
    data 字段携带用户数据（链路层 payload，例如 ASDU）。

    Attributes:
        data: 用户数据，长度 1-255 字节。
    """

    data: bytes

    def __post_init__(self) -> None:
        if not isinstance(self.data, (bytes, bytearray)):
            raise FrameError(
                f"VariableFrame.data 类型应为 bytes，实际为 {type(self.data).__name__}"
            )
        if len(self.data) == 0:
            raise FrameError("可变长度帧 data 不能为空（length=0 不被允许）")
        if len(self.data) > VARIABLE_FRAME_MAX_PAYLOAD:
            raise FrameError(
                f"可变长度帧 data 长度 {len(self.data)} 超出最大 "
                f"{VARIABLE_FRAME_MAX_PAYLOAD}"
            )

    def encode(self) -> bytes:
        """编码为可变长度帧。"""
        length = len(self.data)
        cs = compute_checksum(self.data)
        return bytes(
            [START_CHAR_VARIABLE, length, length]
            + list(self.data)
            + [cs, END_CHAR]
        )

    @classmethod
    def decode(cls, data: bytes) -> "VariableFrame":
        """从可变长度字节串解码可变长度帧。

        Args:
            data: 完整可变长度帧字节串。

        Returns:
            解析后的 VariableFrame 实例。

        Raises:
            FrameError: 帧格式或校验错误。
        """
        if len(data) < VARIABLE_FRAME_OVERHEAD:
            raise FrameError(
                f"可变长度帧至少需要 {VARIABLE_FRAME_OVERHEAD} 字节，"
                f"实际只有 {len(data)} 字节"
            )
        if data[0] != START_CHAR_VARIABLE:
            raise FrameError(
                f"可变长度帧起始字符应为 0x{START_CHAR_VARIABLE:02X}，"
                f"实际为 0x{data[0]:02X}"
            )
        if data[-1] != END_CHAR:
            raise FrameError(
                f"可变长度帧结束字符应为 0x{END_CHAR:02X}，"
                f"实际为 0x{data[-1]:02X}"
            )
        length = data[1]
        if data[2] != length:
            raise FrameError(
                f"可变长度帧 length 字段不一致: {data[2]} != {length}"
            )
        expected_size = VARIABLE_FRAME_OVERHEAD + length
        if len(data) != expected_size:
            raise FrameError(
                f"可变长度帧长度字段 {length} 与实际数据 {len(data)} 不匹配，"
                f"期望 {expected_size} 字节"
            )
        user_data = bytes(data[3 : 3 + length])
        if not verify_checksum(user_data, data[3 + length]):
            raise FrameError(
                f"可变长度帧校验和错误: data={user_data.hex()}, "
                f"cs=0x{data[3 + length]:02X}"
            )
        return cls(data=user_data)


# ── 帧解析（自动识别固定/可变帧）────────────────────────────────────────────


class FrameError(ValueError):
    """FT1.2 帧格式错误。"""


@dataclass
class FrameDecodeResult:
    """帧解码结果包装。

    区分成功 / 失败 / 未知类型。

    Attributes:
        ok: True 表示解码成功，False 表示失败或不支持。
        frame: 解码后的帧（FixedFrame / VariableFrame），失败时为 None。
        kind: 帧类型："fixed" / "variable" / "unknown"。
        reason: 解码失败或不支持时的原因。
    """

    ok: bool
    frame: object | None = None
    kind: str = "unknown"
    reason: str = ""


def decode_frame(data: bytes) -> FrameDecodeResult:
    """自动识别固定/可变长度帧并解码。

    Args:
        data: 完整帧字节串。

    Returns:
        FrameDecodeResult 包含解码状态、帧对象、帧类型与失败原因。
    """
    if not data:
        return FrameDecodeResult(
            ok=False,
            kind="unknown",
            reason="空数据",
        )
    start_char = data[0]
    if start_char == START_CHAR_FIXED:
        try:
            frame: FixedFrame | VariableFrame = FixedFrame.decode(data)
        except FrameError as exc:
            return FrameDecodeResult(
                ok=False,
                kind="fixed",
                reason=str(exc),
            )
        return FrameDecodeResult(ok=True, frame=frame, kind="fixed")
    if start_char == START_CHAR_VARIABLE:
        try:
            frame = VariableFrame.decode(data)
        except FrameError as exc:
            return FrameDecodeResult(
                ok=False,
                kind="variable",
                reason=str(exc),
            )
        return FrameDecodeResult(ok=True, frame=frame, kind="variable")
    return FrameDecodeResult(
        ok=False,
        kind="unknown",
        reason=f"无法识别的起始字符 0x{start_char:02X}",
    )


__all__ = [
    "START_CHAR_FIXED",
    "START_CHAR_VARIABLE",
    "END_CHAR",
    "LinkControl",
    "FIXED_FRAME_SIZE",
    "VARIABLE_FRAME_HEADER_SIZE",
    "VARIABLE_FRAME_OVERHEAD",
    "VARIABLE_FRAME_MAX_PAYLOAD",
    "VARIABLE_FRAME_MAX_SIZE",
    "FrameError",
    "FixedFrame",
    "VariableFrame",
    "FrameDecodeResult",
    "compute_checksum",
    "verify_checksum",
    "decode_frame",
]
