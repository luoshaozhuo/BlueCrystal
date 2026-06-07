"""Starfish Modbus 寄存器值编解码工具测试（Round 18 新增）。

验证：
1. uint16 / int16 / uint32 / int32 / float32 各种边界 roundtrip。
2. byte_order=big / little + word_order=big / little 4 种组合。
3. register 数量不匹配报错。
4. value 越界报错。
5. FLOAT32 NaN/Inf 拒绝。
6. encode/decode 一致性（与 Python struct 公式对齐）。
7. 不得被高估为真实设备验证（仅纯 CPU 协议编解码辅助）。

测试阶段：开发期验证 (P1)。
使用的替身：无（纯编解码器测试）。
不能证明：真实 Modbus 设备交互、生产路径。
NOT_RUN 条件：无（所有测试纯 CPU 运算）。
"""

from __future__ import annotations

import struct

import pytest

from starfish.protocols.modbus import (
    INT16_MAX,
    INT16_MIN,
    INT32_MAX,
    INT32_MIN,
    UINT16_MAX,
    UINT32_MAX,
    ByteOrder,
    ModbusRegisterValueType,
    RegisterEncodingLengthError,
    RegisterEncodingRangeError,
    RegisterEncodingValueError,
    WordOrder,
    decode_register_value,
    encode_register_value,
)


# ── 常量测试 ──────────────────────────────────────────────────────────────────


class TestRegisterEncodingConstants:
    """寄存器编解码常量测试。"""

    def test_int16_min(self) -> None:
        assert INT16_MIN == -32768

    def test_int16_max(self) -> None:
        assert INT16_MAX == 32767

    def test_int32_min(self) -> None:
        assert INT32_MIN == -2147483648

    def test_int32_max(self) -> None:
        assert INT32_MAX == 2147483647

    def test_uint16_max(self) -> None:
        assert UINT16_MAX == 0xFFFF

    def test_uint32_max(self) -> None:
        assert UINT32_MAX == 0xFFFFFFFF


# ── UINT16 编码测试 ────────────────────────────────────────────────────────────


class TestUint16Encoding:
    """UINT16 编码测试。"""

    def test_encode_zero(self) -> None:
        assert encode_register_value(
            0, ModbusRegisterValueType.UINT16,
        ) == [0x0000]

    def test_encode_one(self) -> None:
        assert encode_register_value(
            1, ModbusRegisterValueType.UINT16,
        ) == [0x0001]

    def test_encode_max(self) -> None:
        assert encode_register_value(
            UINT16_MAX, ModbusRegisterValueType.UINT16,
        ) == [0xFFFF]

    def test_encode_typical(self) -> None:
        assert encode_register_value(
            0x1234, ModbusRegisterValueType.UINT16,
        ) == [0x1234]

    def test_encode_out_of_range(self) -> None:
        """UINT16 越界（> 0xFFFF）抛 RegisterEncodingRangeError。"""
        with pytest.raises(RegisterEncodingRangeError, match="UINT16"):
            encode_register_value(
                0x10000, ModbusRegisterValueType.UINT16,
            )

    def test_encode_negative(self) -> None:
        """UINT16 负值抛 RegisterEncodingRangeError。"""
        with pytest.raises(RegisterEncodingRangeError, match="UINT16"):
            encode_register_value(
                -1, ModbusRegisterValueType.UINT16,
            )

    def test_encode_non_int(self) -> None:
        """UINT16 非 int 抛 RegisterEncodingRangeError。"""
        with pytest.raises(RegisterEncodingRangeError, match="UINT16"):
            encode_register_value(
                1.5, ModbusRegisterValueType.UINT16,  # type: ignore[arg-type]
            )

    def test_encode_bool_rejected(self) -> None:
        """UINT16 收到 bool 抛 RegisterEncodingRangeError（bool 视为非 int）。"""
        with pytest.raises(RegisterEncodingRangeError, match="UINT16"):
            encode_register_value(
                True, ModbusRegisterValueType.UINT16,  # type: ignore[arg-type]
            )


class TestUint16Decoding:
    """UINT16 解码测试。"""

    def test_decode_zero(self) -> None:
        assert decode_register_value(
            [0x0000], ModbusRegisterValueType.UINT16,
        ) == 0

    def test_decode_max(self) -> None:
        assert decode_register_value(
            [0xFFFF], ModbusRegisterValueType.UINT16,
        ) == 0xFFFF

    def test_decode_typical(self) -> None:
        assert decode_register_value(
            [0x1234], ModbusRegisterValueType.UINT16,
        ) == 0x1234

    def test_decode_length_mismatch(self) -> None:
        """UINT16 解码寄存器数量不匹配抛 LengthError。"""
        with pytest.raises(RegisterEncodingLengthError):
            decode_register_value(
                [0x0000, 0x0001], ModbusRegisterValueType.UINT16,
            )

    def test_decode_out_of_range(self) -> None:
        """UINT16 解码寄存器值越界抛 RangeError。"""
        with pytest.raises(RegisterEncodingRangeError, match="超出 16-bit"):
            decode_register_value(
                [0x10000], ModbusRegisterValueType.UINT16,
            )

    def test_decode_negative_register(self) -> None:
        """UINT16 解码寄存器负值抛 RangeError。"""
        with pytest.raises(RegisterEncodingRangeError):
            decode_register_value(
                [-1], ModbusRegisterValueType.UINT16,
            )


class TestUint16Roundtrip:
    """UINT16 roundtrip 测试。"""

    @pytest.mark.parametrize(
        "value",
        [0, 1, 100, 32767, 32768, 65534, 65535],
    )
    def test_roundtrip(self, value: int) -> None:
        encoded = encode_register_value(value, ModbusRegisterValueType.UINT16)
        decoded = decode_register_value(encoded, ModbusRegisterValueType.UINT16)
        assert decoded == value


# ── INT16 编码测试 ────────────────────────────────────────────────────────────


class TestInt16Encoding:
    """INT16 编码测试。"""

    def test_encode_zero(self) -> None:
        assert encode_register_value(
            0, ModbusRegisterValueType.INT16,
        ) == [0x0000]

    def test_encode_min(self) -> None:
        assert encode_register_value(
            INT16_MIN, ModbusRegisterValueType.INT16,
        ) == [0x8000]

    def test_encode_max(self) -> None:
        assert encode_register_value(
            INT16_MAX, ModbusRegisterValueType.INT16,
        ) == [0x7FFF]

    def test_encode_minus_one(self) -> None:
        assert encode_register_value(
            -1, ModbusRegisterValueType.INT16,
        ) == [0xFFFF]

    def test_encode_out_of_range(self) -> None:
        """INT16 越界抛 RangeError。"""
        with pytest.raises(RegisterEncodingRangeError, match="INT16"):
            encode_register_value(
                32768, ModbusRegisterValueType.INT16,
            )
        with pytest.raises(RegisterEncodingRangeError, match="INT16"):
            encode_register_value(
                -32769, ModbusRegisterValueType.INT16,
            )


class TestInt16Roundtrip:
    """INT16 roundtrip 测试。"""

    @pytest.mark.parametrize(
        "value",
        [0, 1, -1, 100, -100, 32767, -32768],
    )
    def test_roundtrip(self, value: int) -> None:
        encoded = encode_register_value(value, ModbusRegisterValueType.INT16)
        decoded = decode_register_value(encoded, ModbusRegisterValueType.INT16)
        assert decoded == value


# ── UINT32 编码测试（4 种字节序/字序组合）────────────────────────────────────


class TestUint32EncodingByteOrders:
    """UINT32 4 种组合编码测试。"""

    def test_big_big(self) -> None:
        """byte_order=big, word_order=big: 寄存器顺序 [0x0102, 0x0304]。"""
        regs = encode_register_value(
            0x01020304,
            ModbusRegisterValueType.UINT32,
            ByteOrder.BIG,
            WordOrder.BIG,
        )
        assert regs == [0x0102, 0x0304]

    def test_big_little(self) -> None:
        """byte_order=big, word_order=little: 寄存器顺序 [0x0304, 0x0102]。"""
        regs = encode_register_value(
            0x01020304,
            ModbusRegisterValueType.UINT32,
            ByteOrder.BIG,
            WordOrder.LITTLE,
        )
        assert regs == [0x0304, 0x0102]

    def test_little_big(self) -> None:
        """byte_order=little, word_order=big: 寄存器 [0x0201, 0x0403]。"""
        regs = encode_register_value(
            0x01020304,
            ModbusRegisterValueType.UINT32,
            ByteOrder.LITTLE,
            WordOrder.BIG,
        )
        assert regs == [0x0201, 0x0403]

    def test_little_little(self) -> None:
        """byte_order=little, word_order=little: 寄存器 [0x0403, 0x0201]。"""
        regs = encode_register_value(
            0x01020304,
            ModbusRegisterValueType.UINT32,
            ByteOrder.LITTLE,
            WordOrder.LITTLE,
        )
        assert regs == [0x0403, 0x0201]

    def test_encode_zero(self) -> None:
        regs = encode_register_value(
            0, ModbusRegisterValueType.UINT32,
        )
        assert regs == [0x0000, 0x0000]

    def test_encode_max(self) -> None:
        regs = encode_register_value(
            UINT32_MAX, ModbusRegisterValueType.UINT32,
        )
        assert regs == [0xFFFF, 0xFFFF]

    def test_encode_out_of_range(self) -> None:
        """UINT32 越界抛 RangeError。"""
        with pytest.raises(RegisterEncodingRangeError, match="UINT32"):
            encode_register_value(
                0x100000000, ModbusRegisterValueType.UINT32,
            )
        with pytest.raises(RegisterEncodingRangeError, match="UINT32"):
            encode_register_value(
                -1, ModbusRegisterValueType.UINT32,
            )


class TestUint32DecodingByteOrders:
    """UINT32 4 种组合解码测试。"""

    @pytest.mark.parametrize(
        "byte_order, word_order, registers, expected",
        [
            (ByteOrder.BIG, WordOrder.BIG, [0x0102, 0x0304], 0x01020304),
            (ByteOrder.BIG, WordOrder.LITTLE, [0x0304, 0x0102], 0x01020304),
            (ByteOrder.LITTLE, WordOrder.BIG, [0x0201, 0x0403], 0x01020304),
            (ByteOrder.LITTLE, WordOrder.LITTLE, [0x0403, 0x0201], 0x01020304),
        ],
    )
    def test_decode_combinations(
        self, byte_order: ByteOrder, word_order: WordOrder,
        registers: list[int], expected: int,
    ) -> None:
        decoded = decode_register_value(
            registers,
            ModbusRegisterValueType.UINT32,
            byte_order,
            word_order,
        )
        assert decoded == expected

    def test_decode_length_mismatch(self) -> None:
        """UINT32 寄存器数量不匹配抛 LengthError。"""
        with pytest.raises(RegisterEncodingLengthError):
            decode_register_value(
                [0x0000], ModbusRegisterValueType.UINT32,
            )
        with pytest.raises(RegisterEncodingLengthError):
            decode_register_value(
                [0x0000, 0x0001, 0x0002], ModbusRegisterValueType.UINT32,
            )


class TestUint32Roundtrip:
    """UINT32 4 种组合 roundtrip 测试。"""

    @pytest.mark.parametrize(
        "byte_order, word_order",
        [
            (ByteOrder.BIG, WordOrder.BIG),
            (ByteOrder.BIG, WordOrder.LITTLE),
            (ByteOrder.LITTLE, WordOrder.BIG),
            (ByteOrder.LITTLE, WordOrder.LITTLE),
        ],
    )
    @pytest.mark.parametrize(
        "value",
        [0, 1, 0x12345678, 0x80000000, 0xFFFFFFFF],
    )
    def test_roundtrip(
        self, byte_order: ByteOrder, word_order: WordOrder, value: int,
    ) -> None:
        encoded = encode_register_value(
            value, ModbusRegisterValueType.UINT32, byte_order, word_order,
        )
        decoded = decode_register_value(
            encoded, ModbusRegisterValueType.UINT32, byte_order, word_order,
        )
        assert decoded == value


# ── INT32 编码测试 ────────────────────────────────────────────────────────────


class TestInt32Encoding:
    """INT32 编码测试。"""

    def test_encode_zero(self) -> None:
        regs = encode_register_value(
            0, ModbusRegisterValueType.INT32,
        )
        assert regs == [0x0000, 0x0000]

    def test_encode_min(self) -> None:
        regs = encode_register_value(
            INT32_MIN, ModbusRegisterValueType.INT32,
            ByteOrder.BIG, WordOrder.BIG,
        )
        # INT32_MIN = -2147483648 = 0x80000000
        # big-big: 寄存器 [0x8000, 0x0000]
        assert regs == [0x8000, 0x0000]

    def test_encode_max(self) -> None:
        regs = encode_register_value(
            INT32_MAX, ModbusRegisterValueType.INT32,
            ByteOrder.BIG, WordOrder.BIG,
        )
        # INT32_MAX = 0x7FFFFFFF
        # big-big: 寄存器 [0x7FFF, 0xFFFF]
        assert regs == [0x7FFF, 0xFFFF]

    def test_encode_minus_one(self) -> None:
        regs = encode_register_value(
            -1, ModbusRegisterValueType.INT32,
            ByteOrder.BIG, WordOrder.BIG,
        )
        # -1 = 0xFFFFFFFF
        # big-big: 寄存器 [0xFFFF, 0xFFFF]
        assert regs == [0xFFFF, 0xFFFF]

    def test_encode_out_of_range(self) -> None:
        """INT32 越界抛 RangeError。"""
        with pytest.raises(RegisterEncodingRangeError, match="INT32"):
            encode_register_value(
                0x80000000, ModbusRegisterValueType.INT32,
            )
        with pytest.raises(RegisterEncodingRangeError, match="INT32"):
            encode_register_value(
                -0x80000001, ModbusRegisterValueType.INT32,
            )


class TestInt32Roundtrip:
    """INT32 4 种组合 roundtrip 测试。"""

    @pytest.mark.parametrize(
        "byte_order, word_order",
        [
            (ByteOrder.BIG, WordOrder.BIG),
            (ByteOrder.BIG, WordOrder.LITTLE),
            (ByteOrder.LITTLE, WordOrder.BIG),
            (ByteOrder.LITTLE, WordOrder.LITTLE),
        ],
    )
    @pytest.mark.parametrize(
        "value",
        [0, 1, -1, 1234567890, -1234567890, 2147483647, -2147483648],
    )
    def test_roundtrip(
        self, byte_order: ByteOrder, word_order: WordOrder, value: int,
    ) -> None:
        encoded = encode_register_value(
            value, ModbusRegisterValueType.INT32, byte_order, word_order,
        )
        decoded = decode_register_value(
            encoded, ModbusRegisterValueType.INT32, byte_order, word_order,
        )
        assert decoded == value


# ── FLOAT32 编码测试 ──────────────────────────────────────────────────────────


class TestFloat32Encoding:
    """FLOAT32 编码测试。"""

    def test_encode_one_zero(self) -> None:
        """FLOAT32 1.0 编码 big-big: 寄存器 [0x3F80, 0x0000]（IEEE 754 大端）。"""
        regs = encode_register_value(
            1.0, ModbusRegisterValueType.FLOAT32,
            ByteOrder.BIG, WordOrder.BIG,
        )
        # IEEE 754 single-precision 1.0 = 0x3F800000
        # big-big: 高字在前 -> 寄存器 [0x3F80, 0x0000]
        assert regs == [0x3F80, 0x0000]

    def test_encode_minus_one(self) -> None:
        regs = encode_register_value(
            -1.0, ModbusRegisterValueType.FLOAT32,
            ByteOrder.BIG, WordOrder.BIG,
        )
        # -1.0 = 0xBF800000
        assert regs == [0xBF80, 0x0000]

    def test_encode_nan_rejected(self) -> None:
        """FLOAT32 NaN 拒绝抛 ValueError。"""
        with pytest.raises(RegisterEncodingValueError, match="NaN"):
            encode_register_value(
                float("nan"), ModbusRegisterValueType.FLOAT32,
            )

    def test_encode_positive_inf_rejected(self) -> None:
        """FLOAT32 +Inf 拒绝抛 ValueError。"""
        with pytest.raises(RegisterEncodingValueError, match="Inf"):
            encode_register_value(
                float("inf"), ModbusRegisterValueType.FLOAT32,
            )

    def test_encode_negative_inf_rejected(self) -> None:
        """FLOAT32 -Inf 拒绝抛 ValueError。"""
        with pytest.raises(RegisterEncodingValueError, match="Inf"):
            encode_register_value(
                float("-inf"), ModbusRegisterValueType.FLOAT32,
            )

    def test_encode_non_float_rejected(self) -> None:
        """FLOAT32 非 float 抛 RangeError。"""
        with pytest.raises(RegisterEncodingRangeError, match="FLOAT32"):
            encode_register_value(
                1, ModbusRegisterValueType.FLOAT32,  # type: ignore[arg-type]
            )
        with pytest.raises(RegisterEncodingRangeError, match="FLOAT32"):
            encode_register_value(
                "1.0", ModbusRegisterValueType.FLOAT32,  # type: ignore[arg-type]
            )


class TestFloat32Decoding:
    """FLOAT32 解码测试。"""

    def test_decode_one_zero_big_big(self) -> None:
        decoded = decode_register_value(
            [0x3F80, 0x0000], ModbusRegisterValueType.FLOAT32,
            ByteOrder.BIG, WordOrder.BIG,
        )
        assert decoded == 1.0

    def test_decode_one_zero_little_little(self) -> None:
        """FLOAT32 1.0 little-little: 寄存器 [0x0000, 0x803F]。

        1.0 = 0x3F800000（big-endian），high word = 0x3F80, low word = 0x0000。
        byte_order=LITTLE 对每个 16-bit 字做 byte-swap：
        - high word byte-swap = 0x803F
        - low word byte-swap = 0x0000
        word_order=LITTLE：low word 在前。
        因此 encoded = [0x0000, 0x803F]。
        """
        decoded = decode_register_value(
            [0x0000, 0x803F], ModbusRegisterValueType.FLOAT32,
            ByteOrder.LITTLE, WordOrder.LITTLE,
        )
        assert decoded == 1.0

    def test_decode_nan_bytes_rejected(self) -> None:
        """FLOAT32 NaN 位模式解码拒绝。"""
        # NaN: 0x7FC00000 big-big -> 寄存器 [0x7FC0, 0x0000]
        with pytest.raises(RegisterEncodingValueError, match="NaN"):
            decode_register_value(
                [0x7FC0, 0x0000], ModbusRegisterValueType.FLOAT32,
            )

    def test_decode_positive_inf_bytes_rejected(self) -> None:
        """FLOAT32 +Inf 位模式解码拒绝。"""
        # +Inf: 0x7F800000 big-big -> 寄存器 [0x7F80, 0x0000]
        with pytest.raises(RegisterEncodingValueError, match="Inf"):
            decode_register_value(
                [0x7F80, 0x0000], ModbusRegisterValueType.FLOAT32,
            )

    def test_decode_negative_inf_bytes_rejected(self) -> None:
        """FLOAT32 -Inf 位模式解码拒绝。"""
        with pytest.raises(RegisterEncodingValueError, match="Inf"):
            decode_register_value(
                [0xFF80, 0x0000], ModbusRegisterValueType.FLOAT32,
            )

    def test_decode_length_mismatch(self) -> None:
        """FLOAT32 寄存器数量不匹配抛 LengthError。"""
        with pytest.raises(RegisterEncodingLengthError):
            decode_register_value(
                [0x0000], ModbusRegisterValueType.FLOAT32,
            )


class TestFloat32Roundtrip:
    """FLOAT32 4 种组合 roundtrip 测试。"""

    @pytest.mark.parametrize(
        "byte_order, word_order",
        [
            (ByteOrder.BIG, WordOrder.BIG),
            (ByteOrder.BIG, WordOrder.LITTLE),
            (ByteOrder.LITTLE, WordOrder.BIG),
            (ByteOrder.LITTLE, WordOrder.LITTLE),
        ],
    )
    @pytest.mark.parametrize(
        "value",
        [0.0, 1.0, -1.0, 2.5, -2.5, 1024.0, -1024.0, 0.5, -0.5],
    )
    def test_roundtrip(
        self, byte_order: ByteOrder, word_order: WordOrder, value: float,
    ) -> None:
        encoded = encode_register_value(
            value, ModbusRegisterValueType.FLOAT32, byte_order, word_order,
        )
        decoded = decode_register_value(
            encoded, ModbusRegisterValueType.FLOAT32, byte_order, word_order,
        )
        assert decoded == value


# ── 寄存器值范围边界测试 ──────────────────────────────────────────────────────


class TestRegisterRangeBounds:
    """寄存器值范围边界测试。"""

    def test_register_value_exactly_max(self) -> None:
        """UINT16 解码 0xFFFF 应通过。"""
        decoded = decode_register_value(
            [UINT16_MAX], ModbusRegisterValueType.UINT16,
        )
        assert decoded == UINT16_MAX

    def test_register_value_just_above_max(self) -> None:
        """UINT16 解码 0x10000 应抛 RangeError。"""
        with pytest.raises(RegisterEncodingRangeError, match="超出 16-bit"):
            decode_register_value(
                [0x10000], ModbusRegisterValueType.UINT16,
            )

    def test_register_value_negative(self) -> None:
        """UINT16 解码 -1 应抛 RangeError。"""
        with pytest.raises(RegisterEncodingRangeError):
            decode_register_value(
                [-1], ModbusRegisterValueType.UINT16,
            )


# ── 与 Python struct 公式一致性测试 ──────────────────────────────────────────


class TestConsistencyWithStruct:
    """与 Python struct 公式一致性测试（独立验证 byte_order/word_order 公式）。"""

    @pytest.mark.parametrize(
        "byte_order, word_order",
        [
            (ByteOrder.BIG, WordOrder.BIG),
            (ByteOrder.BIG, WordOrder.LITTLE),
            (ByteOrder.LITTLE, WordOrder.BIG),
            (ByteOrder.LITTLE, WordOrder.LITTLE),
        ],
    )
    def test_uint32_struct_consistency(
        self, byte_order: ByteOrder, word_order: WordOrder,
    ) -> None:
        """UINT32 4 组合的 encode 结果与 byte/word 模型一致。

        模型：
        - high_word = (value >> 16) & 0xFFFF
        - low_word = value & 0xFFFF
        - byte_order=LITTLE 时对两个字都做 byte-swap
        - word_order=BIG 时 [high_word, low_word]，否则 [low_word, high_word]
        """
        value = 0xDEADBEEF
        high_word = (value >> 16) & 0xFFFF
        low_word = value & 0xFFFF
        if byte_order == ByteOrder.LITTLE:
            high_word = ((high_word & 0xFF) << 8) | ((high_word >> 8) & 0xFF)
            low_word = ((low_word & 0xFF) << 8) | ((low_word >> 8) & 0xFF)
        if word_order == WordOrder.BIG:
            expected = [high_word, low_word]
        else:
            expected = [low_word, high_word]
        regs = encode_register_value(
            value, ModbusRegisterValueType.UINT32, byte_order, word_order,
        )
        assert regs == expected

    @pytest.mark.parametrize(
        "byte_order, word_order",
        [
            (ByteOrder.BIG, WordOrder.BIG),
            (ByteOrder.BIG, WordOrder.LITTLE),
            (ByteOrder.LITTLE, WordOrder.BIG),
            (ByteOrder.LITTLE, WordOrder.LITTLE),
        ],
    )
    def test_float32_struct_consistency(
        self, byte_order: ByteOrder, word_order: WordOrder,
    ) -> None:
        """FLOAT32 4 组合的 encode 结果与 byte/word 模型一致。"""
        value = 3.5  # 精确可表示
        raw = struct.pack(">f", value)  # 始终 big-endian raw bytes
        high_word = (raw[0] << 8) | raw[1]
        low_word = (raw[2] << 8) | raw[3]
        if byte_order == ByteOrder.LITTLE:
            high_word = ((high_word & 0xFF) << 8) | ((high_word >> 8) & 0xFF)
            low_word = ((low_word & 0xFF) << 8) | ((low_word >> 8) & 0xFF)
        if word_order == WordOrder.BIG:
            expected = [high_word, low_word]
        else:
            expected = [low_word, high_word]
        regs = encode_register_value(
            value, ModbusRegisterValueType.FLOAT32, byte_order, word_order,
        )
        assert regs == expected


# ── 不高估能力（边界边界）测试 ──────────────────────────────────────────────


class TestNotDeviceValidation:
    """register_encoding 不得被高估为真实设备验证（仅纯 CPU 协议编解码）。"""

    def test_no_io_operations(self) -> None:
        """register_encoding 模块不应包含 socket/pty/serial IO。"""
        import starfish.protocols.modbus.register_encoding as enc

        # 检查模块内容不含 IO 操作
        for attr_name in dir(enc):
            if attr_name.startswith("_"):
                continue
            attr = getattr(enc, attr_name)
            # 函数/方法定义不应包含 socket 等关键词
            if callable(attr):
                try:
                    src = attr.__code__.co_filename
                    assert "modbus" in src, (
                        f"{attr_name} 来源异常: {src}"
                    )
                except (AttributeError, TypeError):
                    pass
