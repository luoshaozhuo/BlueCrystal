"""IEC 60870-5-101 信息体元素（Information Element）编解码。

本模块实现 IEC 60870-5-101 协议中各信息体类型对应的"信息体元素"层
（Information Element, IE）编解码。每个 IE 描述了单个信息点中除
公共字段（IOA、SIQ、QDS、时标）外的业务值字段。

当前实现：
    - NVA (Normalized Value, 16-bit signed normalized value)
        范围 [-1.0, +1.0 - 1/32768]，对应 IEC 60870-5-101 的
        normalized value（占 2 字节，整数表示 -1.0 ~ +(1-2^-15)）。
    - SVA (Scaled Value, 16-bit signed integer) Round 18 新增
        占 2 字节，整数表示 -32768..+32767。SVA 是工程量级整数
        表示，量程与单位由 device profile / 业务侧解释（与 NVA
        的"归一化至 -1.0..1.0-1/32768"语义完全不同）。
    - ShortFloat (IEEE 754 32-bit float, Round 17 新增)
        占 4 字节，按 IEC 60870-5-101 / -104 协议字节序
        （小端序）编码 IEEE 754 single-precision。
        NaN / Inf 策略：拒绝（编码 / 解码均不允许），
        必须由调用方在传入前/传出后处理边界。

不负责：
- CP56Time2a 等 7 字节时标 IE（详见 time.py）。
- 与 60870-5-104 协议差异（位定义一致）。
- 信息体对象组合（Information Object）层面编解码（见 information_object.py）。
"""

from __future__ import annotations

import math
import numbers
import struct
from dataclasses import dataclass
from typing import Any


# ── 归一化值（Normalized Value, NVA）────────────────────────────────────────────


NVA_LENGTH = 2  # NVA 占 2 字节
NVA_MIN = -1.0
NVA_MAX = (32767.0 / 32768.0)  # +1.0 - 1/32768
NVA_INT16_MIN = -32768
NVA_INT16_MAX = 32767


def encode_normalized_value(value: float) -> bytes:
    """将归一化值（-1.0 ~ +1.0-1/32768）编码为 2 字节小端序整数。

    算法：
        int_value = round(value * 32768)
        截断到 int16 范围 [-32768, +32767]。
    边界：
        -1.0  -> 0x8000 (小端序 b"\x00\x80")
        0.0   -> 0x0000
        +(1 - 1/32768) -> 0x7FFF

    Args:
        value: 归一化浮点值，期望范围 [-1.0, +1.0 - 1/32768]。

    Returns:
        2 字节小端序编码结果。

    Raises:
        ValueError: value 超出 [-1.0, +(1-1/32768)] 范围。
    """
    if value < NVA_MIN or value > NVA_MAX:
        raise ValueError(
            f"归一化值 {value} 超出有效范围 [{NVA_MIN}, {NVA_MAX}]"
        )
    # 使用 round 保证最近舍入；32768 = 2^15
    int_value = int(round(value * 32768.0))
    if int_value < NVA_INT16_MIN:
        int_value = NVA_INT16_MIN
    elif int_value > NVA_INT16_MAX:
        int_value = NVA_INT16_MAX
    return struct.pack("<h", int_value)


def decode_normalized_value(data: bytes) -> float:
    """从 2 字节数据解码归一化值。

    Args:
        data: 包含 NVA 的字节串（至少 2 字节，仅读取前 2 字节）。

    Returns:
        归一化浮点值，范围 [-1.0, +1.0 - 1/32768]。

    Raises:
        ValueError: 数据不足 2 字节。
    """
    if len(data) < NVA_LENGTH:
        raise ValueError(
            f"归一化值解码需要至少 {NVA_LENGTH} 字节，实际只有 {len(data)} 字节"
        )
    int_value: int = struct.unpack("<h", data[:2])[0]
    return int_value / 32768.0


# ── 标度化值（Scaled Value, SVA）── Round 18 新增 ────────────────────────────────
# 16-bit 有符号整数（-32768..+32767），与 NVA 同长度但语义不同。
# SVA 是工程量级整数表示，量程与单位由 device profile / 业务侧解释。
# Round 18 新增：实现 encode / decode / ScaledValue dataclass。
# 字节序：小端序（little-endian）。


SVA_LENGTH = 2
SVA_INT16_MIN = -32768
SVA_INT16_MAX = 32767


def encode_scaled_value(value: int) -> bytes:
    """将标度化整数值（-32768..+32767）编码为 2 字节小端序字节串。

    算法：
        截断到 int16 范围 [-32768, +32767]（若越界则抛 ValueError）。
        小端序（low byte first）打包。

    边界：
        -32768  -> 0x8000（小端序 b"\\x00\\x80"）
        0       -> 0x0000
        +32767  -> 0x7FFF

    Args:
        value: 标度化整数，期望范围 [-32768, +32767]。

    Returns:
        2 字节小端序编码结果。

    Raises:
        ValueError: value 越界或非 int 实例。
    """
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(
            f"encode_scaled_value 期望 int 实例，实际 {type(value).__name__}"
        )
    if value < SVA_INT16_MIN or value > SVA_INT16_MAX:
        raise ValueError(
            f"标度化值 {value} 超出有效范围 "
            f"[{SVA_INT16_MIN}, {SVA_INT16_MAX}]"
        )
    return struct.pack("<h", value)


def decode_scaled_value(data: bytes) -> int:
    """从 2 字节小端序数据解码标度化整数值。

    Args:
        data: 包含 SVA 的字节串（至少 2 字节，仅读取前 2 字节）。

    Returns:
        标度化整数值，范围 [-32768, +32767]。

    Raises:
        ValueError: 数据不足 2 字节。
    """
    if len(data) < SVA_LENGTH:
        raise ValueError(
            f"标度化值解码需要至少 {SVA_LENGTH} 字节，"
            f"实际只有 {len(data)} 字节"
        )
    int_value: int = struct.unpack("<h", data[:SVA_LENGTH])[0]
    return int_value


@dataclass
class ScaledValue:
    """标度化值（SVA）数据类包装。

    范围 [-32768, +32767]，使用 2 字节小端序整数表示。
    SVA 是工程量级整数表示，量程与单位由 device profile / 业务侧解释。
    与 ``NormalizedValue``（NVA，浮点归一化值）语义不同。

    Attributes:
        value: 标度化整数值（-32768..+32767）。
    """

    value: int = 0

    def encode(self) -> bytes:
        """编码为 2 字节小端序字节串。"""
        return encode_scaled_value(self.value)

    @classmethod
    def decode(cls, data: bytes) -> "ScaledValue":
        """从 2 字节数据解码 ScaledValue。"""
        return cls(value=decode_scaled_value(data))


# ── 短浮点（Short Float, IEEE 754 32-bit）────────────────────────────────────────


SHORT_FLOAT_LENGTH = 4

# ShortFloat 有限值边界（IEEE 754 single-precision 极值；超过即 ±Inf）
SHORT_FLOAT_FINITE_MAX = 3.4028234663852886e38
SHORT_FLOAT_FINITE_MIN = -3.4028234663852886e38


def encode_short_float(value: Any) -> bytes:
    """将 IEEE 754 32-bit 浮点编码为 4 字节小端序字节串。

    字节序：little-endian（IEC 60870-5-101 / -104 标准字节序，
    与网络字节序相反；调用方须按协议规定以小端序组帧）。

    Round 20 兼容范围（顺序尝试，**不**引入 numpy 硬依赖）：
        1. 原生 ``float`` 实例：直接走 ``struct.pack("<f", value)``。
        2. ``int`` 实例：通过 ``float(int)`` 转换（``int`` 是
           ``numbers.Integral``，但 round-trip ``int -> float -> struct``
           与原 float 路径语义一致）。
        3. ``numbers.Real`` 抽象基类实例（``Decimal`` /
           ``fractions.Fraction`` 等）：通过 ``float(value)`` 转换。
        4. 任何定义了 ``__float__`` 方法的对象（duck typing）：
           通过 ``float(value)`` 转换。
        5. ``Decimal``：本实现沿用 ``float(decimal_value)``（与
           ``numbers.Real`` 路径相同），不引入 ``decimal.Decimal``
           特化路径以避免精度假设差异。

    NaN / Inf 策略（**不**回退）：
        - 拒绝。``math.isnan(value)`` 或 ``math.isinf(value)`` 时
          抛出 ``ValueError``。原因：IEC 60870-5-101 协议未规定
          ShortFloat 携带 NaN/Inf 的语义，跨厂商实现差异较大；
          本 codec 选择"在边界层拒绝"以保证 roundtrip 一致性。
        - 调用方如需支持 NaN/Inf，应在传入前映射为协议层
          约定的占位值（如 ``float('nan')`` -> ``0.0`` 或
          ``QDS.invalid=True``），由业务侧负责。

    Args:
        value: 待编码的有限数值（``float`` / ``int`` /
            ``numbers.Real`` / 带 ``__float__`` 的对象）。

    Returns:
        4 字节小端序编码结果。

    Raises:
        ValueError: ``value`` 为 NaN / Inf；或既不是 ``float`` /
            ``int`` / ``numbers.Real`` 也不是带 ``__float__`` 的对象；
            或转换后仍非有限浮点。
    """
    fvalue: float
    if isinstance(value, float):
        fvalue = value
    elif isinstance(value, int) and not isinstance(value, bool):
        # bool 走 numbers.Real 路径，避免 True/False 被误编码为 1.0/0.0
        # 后调用方误用
        fvalue = float(value)
    elif isinstance(value, numbers.Real):
        # 覆盖 Decimal / Fraction 等
        fvalue = float(value)
    elif hasattr(value, "__float__"):
        # duck typing：自定义 __float__ 对象（如业务包装类）
        try:
            fvalue = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"encode_short_float 无法把 {type(value).__name__} 实例 "
                f"转换为 float：{exc}"
            ) from exc
    else:
        raise ValueError(
            "encode_short_float 期望 float / int / numbers.Real 或带 "
            f"__float__ 方法的对象，实际 {type(value).__name__}"
        )

    # NaN / Inf 拒绝：协议未规定语义，本实现选择严格边界。
    if math.isnan(fvalue):
        raise ValueError(
            "encode_short_float 拒绝 NaN：IEC 60870-5-101 ShortFloat "
            "未规定 NaN 语义，请调用方自行处理"
        )
    if math.isinf(fvalue):
        raise ValueError(
            "encode_short_float 拒绝 Inf：IEC 60870-5-101 ShortFloat "
            "未规定 Inf 语义，请调用方自行处理"
        )
    return struct.pack("<f", fvalue)


def decode_short_float(data: bytes) -> float:
    """从 4 字节小端序数据解码 IEEE 754 32-bit 浮点。

    字节序：little-endian（与 ``encode_short_float`` 对称）。

    NaN / Inf 策略：
        - 拒绝。解码结果为 NaN / Inf 时抛出 ``ValueError``。
        - 理由：与 ``encode_short_float`` 对称，保证 codec
          严格不向调用方泄漏 NaN/Inf，迫使业务侧在边界层处理。

    Args:
        data: 至少 4 字节；仅读取前 4 字节。

    Returns:
        解码后的有限浮点数。

    Raises:
        ValueError: 数据不足 4 字节，或解码结果为 NaN / Inf。
    """
    if len(data) < SHORT_FLOAT_LENGTH:
        raise ValueError(
            f"ShortFloat 解码需要至少 {SHORT_FLOAT_LENGTH} 字节，"
            f"实际只有 {len(data)} 字节"
        )
    value: float = struct.unpack("<f", data[:SHORT_FLOAT_LENGTH])[0]
    if value != value:  # NaN
        raise ValueError(
            "decode_short_float 拒绝 NaN：IEC 60870-5-101 ShortFloat "
            "未规定 NaN 语义"
        )
    if value == float("inf") or value == float("-inf"):
        raise ValueError(
            "decode_short_float 拒绝 Inf：IEC 60870-5-101 ShortFloat "
            "未规定 Inf 语义"
        )
    return value


@dataclass
class ShortFloat:
    """ShortFloat（IEEE 754 32-bit）数据类包装。

    4 字节小端序编码；NaN / Inf 在编码/解码时被拒绝（详见
    ``encode_short_float`` / ``decode_short_float``）。

    Attributes:
        value: 有限浮点值。
    """

    value: float = 0.0

    def encode(self) -> bytes:
        """编码为 4 字节小端序字节串。"""
        return encode_short_float(self.value)

    @classmethod
    def decode(cls, data: bytes) -> "ShortFloat":
        """从 4 字节数据解码 ShortFloat。"""
        return cls(value=decode_short_float(data))


@dataclass
class NormalizedValue:
    """归一化值（NVA）数据类包装。

    范围 [-1.0, +1.0 - 1/32768]，使用 2 字节小端序整数表示。

    Attributes:
        value: 归一化浮点值。
    """

    value: float = 0.0

    def encode(self) -> bytes:
        """编码为 2 字节小端序字节串。"""
        return encode_normalized_value(self.value)

    @classmethod
    def decode(cls, data: bytes) -> "NormalizedValue":
        """从 2 字节数据解码。"""
        return cls(value=decode_normalized_value(data))


__all__ = [
    "NVA_LENGTH",
    "NVA_MIN",
    "NVA_MAX",
    "SVA_LENGTH",
    "SVA_INT16_MIN",
    "SVA_INT16_MAX",
    "SHORT_FLOAT_LENGTH",
    "SHORT_FLOAT_FINITE_MAX",
    "SHORT_FLOAT_FINITE_MIN",
    "NormalizedValue",
    "ShortFloat",
    "ScaledValue",
    "encode_normalized_value",
    "decode_normalized_value",
    "encode_scaled_value",
    "decode_scaled_value",
    "encode_short_float",
    "decode_short_float",
]
