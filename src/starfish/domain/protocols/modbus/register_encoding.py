"""Modbus 寄存器值编解码工具（Round 18 新增）。

本模块提供 Modbus TCP / Modbus RTU 共享的寄存器值编解码工具。
按 value_type（uint16/int16/uint32/int32/float32）、byte_order
（big/little）和 word_order（big/little）支持任意组合。

边界与策略：

- uint16：0..0xFFFF。
- int16：-32768..32767。
- uint32：0..0xFFFFFFFF。
- int32：-2147483648..2147483647。
- float32：IEEE 754 32-bit，**严格拒绝** NaN/Inf
  （理由：与 IEC101 ShortFloat 一致；业务侧应在边界层处理）。
- register 数量不匹配：抛 ``RegisterEncodingLengthError``。
- value 越界：抛 ``RegisterEncodingRangeError``。
- NaN/Inf：抛 ``RegisterEncodingValueError``。

本模块**不**负责：
- 真实 Modbus TCP / Modbus RTU 设备 IO（由 facade 负责）。
- 多从站 ID、异常码完整矩阵、Modbus 协议帧级业务逻辑。
- 与真实设备交互（仅纯 CPU 运算的协议编解码辅助）。
"""

from __future__ import annotations

import struct
from enum import Enum
from typing import Final


# ── 类型与异常 ──────────────────────────────────────────────────────────────────


class ByteOrder(str, Enum):
    """字节序（byte order）。

    - ``BIG``：大端序（big-endian，MSB 在前）。
    - ``LITTLE``：小端序（little-endian，LSB 在前）。
    """

    BIG = "big"
    LITTLE = "little"


class WordOrder(str, Enum):
    """字序（word order，32-bit 值的 16-bit 字顺序）。

    仅当 value_type 占 2 个 16-bit 寄存器（uint32/int32/float32）
    时才有意义。``BIG`` 表示高字（value 的高 16-bit）在前，
    ``LITTLE`` 表示低字（value 的低 16-bit）在前。

    - ``BIG``（高字在前）：Modicon / standard Modbus 约定。
    - ``LITTLE``（低字在前）：Daniel / Enron 约定。
    """

    BIG = "big"
    LITTLE = "little"


class ModbusRegisterValueType(str, Enum):
    """Modbus 寄存器值类型枚举。

    - ``UINT16``：无符号 16-bit（1 个 Modbus 寄存器）。
    - ``INT16``：有符号 16-bit（1 个 Modbus 寄存器）。
    - ``UINT32``：无符号 32-bit（2 个 Modbus 寄存器）。
    - ``INT32``：有符号 32-bit（2 个 Modbus 寄存器）。
    - ``FLOAT32``：IEEE 754 32-bit 浮点（2 个 Modbus 寄存器）。
    """

    UINT16 = "uint16"
    INT16 = "int16"
    UINT32 = "uint32"
    INT32 = "int32"
    FLOAT32 = "float32"


class RegisterEncodingError(ValueError):
    """Modbus 寄存器编解码错误基类。"""


class RegisterEncodingRangeError(RegisterEncodingError):
    """值越界（如 uint16 收到负数、int16 收到 > 32767 等）。"""


class RegisterEncodingLengthError(RegisterEncodingError):
    """寄存器数量不匹配（如 uint32 编码时传入 1 个寄存器）。"""


class RegisterEncodingValueError(RegisterEncodingError):
    """IEEE 754 NaN/Inf 等不允许的值。"""


# ── 常量 ────────────────────────────────────────────────────────────────────────


INT16_MIN: Final[int] = -32768
INT16_MAX: Final[int] = 32767
UINT16_MIN: Final[int] = 0
UINT16_MAX: Final[int] = 0xFFFF
INT32_MIN: Final[int] = -2147483648
INT32_MAX: Final[int] = 2147483647
UINT32_MIN: Final[int] = 0
UINT32_MAX: Final[int] = 0xFFFFFFFF


# ── 内部工具 ────────────────────────────────────────────────────────────────────


def _value_type_register_count(value_type: ModbusRegisterValueType) -> int:
    """返回 value_type 占用的 16-bit Modbus 寄存器数。"""
    if value_type in (ModbusRegisterValueType.UINT16, ModbusRegisterValueType.INT16):
        return 1
    if value_type in (
        ModbusRegisterValueType.UINT32,
        ModbusRegisterValueType.INT32,
        ModbusRegisterValueType.FLOAT32,
    ):
        return 2
    raise RegisterEncodingError(f"未知 value_type: {value_type}")


def _validate_uint16(value: int) -> None:
    if not isinstance(value, int) or isinstance(value, bool):
        raise RegisterEncodingRangeError(
            f"UINT16 期望 int 实例，实际 {type(value).__name__}"
        )
    if value < UINT16_MIN or value > UINT16_MAX:
        raise RegisterEncodingRangeError(
            f"UINT16 值 {value} 超出范围 [{UINT16_MIN}, {UINT16_MAX}]"
        )


def _validate_int16(value: int) -> None:
    if not isinstance(value, int) or isinstance(value, bool):
        raise RegisterEncodingRangeError(
            f"INT16 期望 int 实例，实际 {type(value).__name__}"
        )
    if value < INT16_MIN or value > INT16_MAX:
        raise RegisterEncodingRangeError(
            f"INT16 值 {value} 超出范围 [{INT16_MIN}, {INT16_MAX}]"
        )


def _validate_uint32(value: int) -> None:
    if not isinstance(value, int) or isinstance(value, bool):
        raise RegisterEncodingRangeError(
            f"UINT32 期望 int 实例，实际 {type(value).__name__}"
        )
    if value < UINT32_MIN or value > UINT32_MAX:
        raise RegisterEncodingRangeError(
            f"UINT32 值 {value} 超出范围 [{UINT32_MIN}, {UINT32_MAX}]"
        )


def _validate_int32(value: int) -> None:
    if not isinstance(value, int) or isinstance(value, bool):
        raise RegisterEncodingRangeError(
            f"INT32 期望 int 实例，实际 {type(value).__name__}"
        )
    if value < INT32_MIN or value > INT32_MAX:
        raise RegisterEncodingRangeError(
            f"INT32 值 {value} 超出范围 [{INT32_MIN}, {INT32_MAX}]"
        )


def _validate_float32(value: float) -> None:
    if not isinstance(value, float):
        raise RegisterEncodingRangeError(
            f"FLOAT32 期望 float 实例，实际 {type(value).__name__}"
        )
    if value != value:  # NaN
        raise RegisterEncodingValueError(
            "FLOAT32 拒绝 NaN：Modbus register encoding 不接受 NaN，"
            "请调用方在边界层处理"
        )
    if value == float("inf") or value == float("-inf"):
        raise RegisterEncodingValueError(
            "FLOAT32 拒绝 Inf：Modbus register encoding 不接受 Inf，"
            "请调用方在边界层处理"
        )


# ── 公共 API ──────────────────────────────────────────────────────────────────


def encode_register_value(
    value: int | float,
    value_type: ModbusRegisterValueType,
    byte_order: ByteOrder = ByteOrder.BIG,
    word_order: WordOrder = WordOrder.BIG,
) -> list[int]:
    """将值编码为 16-bit 寄存器列表（Modbus 寄存器值）。

    Args:
        value: 待编码值（int 或 float；类型必须与 ``value_type`` 兼容）。
        value_type: 寄存器值类型。
        byte_order: 字节序（big / little）。
        word_order: 字序（big / little）。仅 32-bit 类型有效；
            对 16-bit 类型（uint16/int16）此参数被忽略。

    Returns:
        ``list[int]``：每个元素范围 [0, 0xFFFF] 的 16-bit 寄存器值。
        列表长度：UINT16/INT16 = 1；UINT32/INT32/FLOAT32 = 2。

    Raises:
        RegisterEncodingRangeError: 值越界或类型不匹配。
        RegisterEncodingValueError: FLOAT32 收到 NaN/Inf。
        RegisterEncodingError: 未知 value_type。

    Examples:
        >>> encode_register_value(0x1234, ModbusRegisterValueType.UINT16)
        [0x1234]
        >>> encode_register_value(
        ...     0x01020304,
        ...     ModbusRegisterValueType.UINT32,
        ...     ByteOrder.BIG,
        ...     WordOrder.BIG,
        ... )
        [0x0102, 0x0304]
        >>> encode_register_value(
        ...     0x01020304,
        ...     ModbusRegisterValueType.UINT32,
        ...     ByteOrder.LITTLE,
        ...     WordOrder.LITTLE,
        ... )
        [0x0403, 0x0201]
    """
    if value_type == ModbusRegisterValueType.UINT16:
        int_value = _coerce_to_int(value, "UINT16")
        _validate_range(int_value, "UINT16", UINT16_MIN, UINT16_MAX)
        return [int_value & 0xFFFF]
    if value_type == ModbusRegisterValueType.INT16:
        int_value = _coerce_to_int(value, "INT16")
        _validate_range(int_value, "INT16", INT16_MIN, INT16_MAX)
        # int16 -> uint16 (two's complement)
        u = int_value & 0xFFFF
        return [u]
    if value_type == ModbusRegisterValueType.UINT32:
        int_value = _coerce_to_int(value, "UINT32")
        _validate_range(int_value, "UINT32", UINT32_MIN, UINT32_MAX)
        return _encode_32bit_int(
            int_value, signed=False,
            byte_order=byte_order, word_order=word_order,
        )
    if value_type == ModbusRegisterValueType.INT32:
        int_value = _coerce_to_int(value, "INT32")
        _validate_range(int_value, "INT32", INT32_MIN, INT32_MAX)
        return _encode_32bit_int(
            int_value, signed=True,
            byte_order=byte_order, word_order=word_order,
        )
    if value_type == ModbusRegisterValueType.FLOAT32:
        if not isinstance(value, float):
            raise RegisterEncodingRangeError(
                f"FLOAT32 期望 float 实例，实际 {type(value).__name__}"
            )
        _validate_float32(value)
        return _encode_float32(value, byte_order=byte_order, word_order=word_order)
    raise RegisterEncodingError(f"未知 value_type: {value_type}")


def decode_register_value(
    registers: list[int],
    value_type: ModbusRegisterValueType,
    byte_order: ByteOrder = ByteOrder.BIG,
    word_order: WordOrder = WordOrder.BIG,
) -> int | float:
    """从 16-bit 寄存器列表解码为值（int 或 float）。

    Args:
        registers: 16-bit 寄存器列表；元素范围 [0, 0xFFFF]。
        value_type: 寄存器值类型。
        byte_order: 字节序（big / little）。
        word_order: 字序（big / little）。仅 32-bit 类型有效；
            对 16-bit 类型此参数被忽略。

    Returns:
        - int：当 ``value_type`` 为 UINT16/INT16/UINT32/INT32。
        - float：当 ``value_type`` 为 FLOAT32。

    Raises:
        RegisterEncodingLengthError: 寄存器数量与 value_type 不匹配。
        RegisterEncodingValueError: FLOAT32 解码为 NaN/Inf。
        RegisterEncodingError: 未知 value_type。

    Examples:
        >>> decode_register_value([0x1234], ModbusRegisterValueType.UINT16)
        4660
        >>> decode_register_value(
        ...     [0x0102, 0x0304],
        ...     ModbusRegisterValueType.UINT32,
        ...     ByteOrder.BIG,
        ...     WordOrder.BIG,
        ... )
        16909060
    """
    expected = _value_type_register_count(value_type)
    if len(registers) != expected:
        raise RegisterEncodingLengthError(
            f"{value_type.value} 需要 {expected} 个寄存器，"
            f"实际 {len(registers)} 个"
        )
    for idx, reg in enumerate(registers):
        if not isinstance(reg, int) or isinstance(reg, bool):
            raise RegisterEncodingRangeError(
                f"registers[{idx}] 期望 int，实际 {type(reg).__name__}"
            )
        if reg < 0 or reg > 0xFFFF:
            raise RegisterEncodingRangeError(
                f"registers[{idx}] = {reg} 超出 16-bit 范围 [0, 0xFFFF]"
            )

    if value_type == ModbusRegisterValueType.UINT16:
        return int(registers[0])
    if value_type == ModbusRegisterValueType.INT16:
        # two's complement
        return int(_to_signed(registers[0], 16))
    if value_type == ModbusRegisterValueType.UINT32:
        return int(_decode_32bit_int(
            registers, signed=False,
            byte_order=byte_order, word_order=word_order,
        ))
    if value_type == ModbusRegisterValueType.INT32:
        return int(_decode_32bit_int(
            registers, signed=True,
            byte_order=byte_order, word_order=word_order,
        ))
    if value_type == ModbusRegisterValueType.FLOAT32:
        return float(_decode_float32(
            registers, byte_order=byte_order, word_order=word_order,
        ))
    raise RegisterEncodingError(f"未知 value_type: {value_type}")


def _coerce_to_int(value: int | float, label: str) -> int:
    """将 value 强转为 int（拒绝 bool 和 float 非整型值）。"""
    if isinstance(value, bool):
        raise RegisterEncodingRangeError(
            f"{label} 拒绝 bool（避免 True/False 隐式 1/0 混淆）"
        )
    if not isinstance(value, int):
        raise RegisterEncodingRangeError(
            f"{label} 期望 int 实例，实际 {type(value).__name__}"
        )
    return value


def _validate_range(value: int, label: str, min_v: int, max_v: int) -> None:
    """检查 value 是否在 [min_v, max_v] 范围内。"""
    if value < min_v or value > max_v:
        raise RegisterEncodingRangeError(
            f"{label} 值 {value} 超出范围 [{min_v}, {max_v}]"
        )


# ── 32-bit / float32 字节序与字序组合 ──────────────────────────────────────────


def _byte_swap_16(v: int) -> int:
    """16-bit 寄存器值的字节序反转。"""
    return ((v & 0xFF) << 8) | ((v >> 8) & 0xFF)


def _encode_32bit_int(
    value: int,
    signed: bool,
    byte_order: ByteOrder,
    word_order: WordOrder,
) -> list[int]:
    """32-bit 整数编码。

    模型：byte_order 描述 16-bit 寄存器内部的字节序（big=MSB 在高字节，
    little=MSB 在低字节，**即对 16-bit 整数做 byte-swap**）；
    word_order 描述两个 16-bit 字（高字 / 低字）的输出顺序。

    4 组合（以 value=0x01020304 为例）：
    - big-big: [0x0102, 0x0304]（高字在前，big-endian 字内字节序）
    - big-little: [0x0304, 0x0102]（低字在前，big-endian）
    - little-big: [0x0201, 0x0403]（高字在前，字内 byte-swap）
    - little-little: [0x0403, 0x0201]（低字在前，字内 byte-swap）
    """
    del signed  # 仅用 struct 公式验证；编码实现不依赖 signed
    high_word = (value >> 16) & 0xFFFF
    low_word = value & 0xFFFF
    if byte_order == ByteOrder.LITTLE:
        high_word = _byte_swap_16(high_word)
        low_word = _byte_swap_16(low_word)
    if word_order == WordOrder.BIG:
        return [high_word, low_word]
    return [low_word, high_word]


def _decode_32bit_int(
    registers: list[int],
    signed: bool,
    byte_order: ByteOrder,
    word_order: WordOrder,
) -> int:
    """32-bit 整数解码（编码的逆操作）。"""
    reg0, reg1 = registers[0], registers[1]
    if word_order == WordOrder.BIG:
        high_word = reg0
        low_word = reg1
    else:
        high_word = reg1
        low_word = reg0
    if byte_order == ByteOrder.LITTLE:
        high_word = _byte_swap_16(high_word)
        low_word = _byte_swap_16(low_word)
    if signed:
        # 两个有符号 16-bit 拼成有符号 32-bit
        high_signed = _to_signed(high_word, 16)
        return (high_signed << 16) | low_word
    return (high_word << 16) | low_word


def _encode_float32(
    value: float,
    byte_order: ByteOrder,
    word_order: WordOrder,
) -> list[int]:
    """IEEE 754 32-bit float 编码（与 _encode_32bit_int 同样的 byte/word 模型）。"""
    raw = struct.pack(">I", 0)  # placeholder
    # 用 struct 直接获取 4 字节大端序列
    raw = struct.pack(">f", value)
    high_word = (raw[0] << 8) | raw[1]
    low_word = (raw[2] << 8) | raw[3]
    if byte_order == ByteOrder.LITTLE:
        high_word = _byte_swap_16(high_word)
        low_word = _byte_swap_16(low_word)
    if word_order == WordOrder.BIG:
        return [high_word, low_word]
    return [low_word, high_word]


def _decode_float32(
    registers: list[int],
    byte_order: ByteOrder,
    word_order: WordOrder,
) -> float:
    """IEEE 754 32-bit float 解码（拒绝 NaN/Inf）。"""
    reg0, reg1 = registers[0], registers[1]
    if word_order == WordOrder.BIG:
        high_word = reg0
        low_word = reg1
    else:
        high_word = reg1
        low_word = reg0
    if byte_order == ByteOrder.LITTLE:
        high_word = _byte_swap_16(high_word)
        low_word = _byte_swap_16(low_word)
    raw = bytes(
        [
            (high_word >> 8) & 0xFF,
            high_word & 0xFF,
            (low_word >> 8) & 0xFF,
            low_word & 0xFF,
        ]
    )
    value: float = struct.unpack(">f", raw)[0]
    if value != value:
        raise RegisterEncodingValueError(
            "FLOAT32 解码为 NaN：Modbus register encoding 拒绝 NaN"
        )
    if value == float("inf") or value == float("-inf"):
        raise RegisterEncodingValueError(
            "FLOAT32 解码为 Inf：Modbus register encoding 拒绝 Inf"
        )
    return value


def _to_signed(value: int, bits: int) -> int:
    """将有符号 16-bit / 32-bit 整数从无符号表示转为有符号。"""
    sign_bit = 1 << (bits - 1)
    if value & sign_bit:
        return value - (1 << bits)
    return value


__all__ = [
    # 类型与异常
    "ByteOrder",
    "WordOrder",
    "ModbusRegisterValueType",
    "RegisterEncodingError",
    "RegisterEncodingLengthError",
    "RegisterEncodingRangeError",
    "RegisterEncodingValueError",
    # 常量
    "INT16_MIN",
    "INT16_MAX",
    "INT32_MIN",
    "INT32_MAX",
    "UINT16_MAX",
    "UINT32_MAX",
    # 入口
    "encode_register_value",
    "decode_register_value",
]
