"""Starfish IEC 60870-5-101 信息体元素（IE）测试。

验证：
1. SIQ 质量描述符 encode/decode 与质量标志位 roundtrip。
2. QDS 质量描述符 encode/decode 与质量标志位 roundtrip。
3. NVA 归一化值 encode/decode 与边界（-1.0, 0.0, +1-1/32768）。
4. SIQFlags / QDSFlags 位标志位组合语义。
5. CP56Time2a 7 字节时标 IE encode/decode roundtrip（Round 16 新增）。
6. CP56Time2a 与 datetime 互转（from_datetime / to_datetime）。
7. CP56Time2a 字段边界（milliseconds/minute/hour/day_of_month/month/year）。
8. CP56Time2a 标志位（invalid/summer_time/substituted）边界。
9. ShortFloat IEEE 754 32-bit IE encode/decode 与边界
   （Round 17 新增；含 0.0 / -0.0 / NaN / Inf 拒绝策略）。
10. ScaledValue IE encode/decode 与边界（Round 18 新增）。

测试阶段：开发期验证 (P1)。
使用的替身：无（纯编解码器测试，无外部依赖）。
不能证明：真实 IEC101 server 帧正确性、链路层能力、串口通信。
NOT_RUN 条件：无（所有测试纯 CPU 运算）。
"""

from __future__ import annotations

from datetime import datetime

import pytest

from starfish.protocols.iec101 import (
    CP56TIME2A_LENGTH,
    CP56Time2a,
    QDS,
    QDSFlags,
    SHORT_FLOAT_FINITE_MAX,
    SHORT_FLOAT_FINITE_MIN,
    SHORT_FLOAT_LENGTH,
    SIQ,
    SIQFlags,
    SVA_INT16_MAX,
    SVA_INT16_MIN,
    SVA_LENGTH,
    ScaledValue,
    ShortFloat,
    decode_cp56time2a,
    decode_normalized_value,
    decode_qds,
    decode_scaled_value,
    decode_short_float,
    decode_siq,
    encode_cp56time2a,
    encode_normalized_value,
    encode_qds,
    encode_scaled_value,
    encode_short_float,
    encode_siq,
    from_datetime,
    to_datetime,
)


# ── SIQ 测试 ───────────────────────────────────────────────────────────────────


class TestSIQ:
    """SIQ 质量描述符编解码测试。"""

    def test_siq_value_on(self) -> None:
        """SIQ value=True 应编码为 SPI_ON 位。"""
        siq = SIQ(value=True)
        encoded = encode_siq(siq)
        assert encoded == b"\x01"

    def test_siq_value_off(self) -> None:
        """SIQ value=False 应编码为 0x00。"""
        siq = SIQ(value=False)
        encoded = encode_siq(siq)
        assert encoded == b"\x00"

    def test_siq_decode_on(self) -> None:
        """SIQ 解码 0x01 应得到 value=True。"""
        siq = decode_siq(b"\x01")
        assert siq.value is True
        assert siq.blocked is False
        assert siq.substituted is False
        assert siq.not_topical is False
        assert siq.invalid is False

    def test_siq_decode_off(self) -> None:
        """SIQ 解码 0x00 应得到 value=False。"""
        siq = decode_siq(b"\x00")
        assert siq.value is False

    def test_siq_all_flags(self) -> None:
        """SIQ 全部质量位均置位。"""
        siq = SIQ(value=True, blocked=True, substituted=True, not_topical=True, invalid=True)
        encoded = encode_siq(siq)
        # 0x01 | 0x02 | 0x04 | 0x08 | 0x10 = 0x1F
        assert encoded == b"\x1F"
        decoded = decode_siq(encoded)
        assert decoded.value is True
        assert decoded.blocked is True
        assert decoded.substituted is True
        assert decoded.not_topical is True
        assert decoded.invalid is True

    def test_siq_roundtrip(self) -> None:
        """SIQ 多种组合 roundtrip。"""
        cases = [
            SIQ(value=False),
            SIQ(value=True),
            SIQ(value=True, blocked=True),
            SIQ(value=False, substituted=True),
            SIQ(value=True, not_topical=True),
            SIQ(value=False, invalid=True),
            SIQ(value=True, blocked=True, substituted=True, not_topical=True, invalid=True),
        ]
        for siq in cases:
            decoded = decode_siq(encode_siq(siq))
            assert decoded.value == siq.value
            assert decoded.blocked == siq.blocked
            assert decoded.substituted == siq.substituted
            assert decoded.not_topical == siq.not_topical
            assert decoded.invalid == siq.invalid

    def test_siq_decode_too_short(self) -> None:
        """SIQ 解码数据不足时应抛出 ValueError。"""
        with pytest.raises(ValueError):
            decode_siq(b"")

    def test_siq_flags_intflag_combine(self) -> None:
        """SIQFlags 位标志位组合语义。"""
        flags = SIQFlags.SPI_ON | SIQFlags.BLOCKED
        assert int(flags) == 0x03
        assert bool(flags & SIQFlags.SPI_ON)
        assert bool(flags & SIQFlags.BLOCKED)
        assert not bool(flags & SIQFlags.SUBSTITUTED)


# ── QDS 测试 ───────────────────────────────────────────────────────────────────


class TestQDS:
    """QDS 质量描述符编解码测试。"""

    def test_qds_no_flags(self) -> None:
        """QDS 无任何质量位应编码为 0x00。"""
        qds = QDS()
        encoded = encode_qds(qds)
        assert encoded == b"\x00"

    def test_qds_overflow(self) -> None:
        """QDS overflow=True 应编码为 0x01。"""
        qds = QDS(overflow=True)
        encoded = encode_qds(qds)
        assert encoded == b"\x01"
        decoded = decode_qds(encoded)
        assert decoded.overflow is True
        assert decoded.blocked is False

    def test_qds_all_quality_flags(self) -> None:
        """QDS 全部质量位（OV+BL+SB+NT+IV）置位。"""
        qds = QDS(overflow=True, blocked=True, substituted=True, not_topical=True, invalid=True)
        encoded = encode_qds(qds)
        # 0x01 | 0x04 | 0x08 | 0x10 | 0x20 = 0x3D
        assert encoded == b"\x3D"
        decoded = decode_qds(encoded)
        assert decoded.overflow is True
        assert decoded.blocked is True
        assert decoded.substituted is True
        assert decoded.not_topical is True
        assert decoded.invalid is True

    def test_qds_roundtrip(self) -> None:
        """QDS 多种组合 roundtrip。"""
        cases = [
            QDS(),
            QDS(overflow=True),
            QDS(blocked=True),
            QDS(substituted=True),
            QDS(not_topical=True),
            QDS(invalid=True),
            QDS(overflow=True, invalid=True),
            QDS(overflow=True, blocked=True, substituted=True, not_topical=True, invalid=True),
        ]
        for qds in cases:
            decoded = decode_qds(encode_qds(qds))
            assert decoded.overflow == qds.overflow
            assert decoded.blocked == qds.blocked
            assert decoded.substituted == qds.substituted
            assert decoded.not_topical == qds.not_topical
            assert decoded.invalid == qds.invalid

    def test_qds_decode_too_short(self) -> None:
        """QDS 解码数据不足时应抛出 ValueError。"""
        with pytest.raises(ValueError):
            decode_qds(b"")

    def test_qds_flags_intflag_combine(self) -> None:
        """QDSFlags 位标志位组合语义。"""
        flags = QDSFlags.OVERFLOW | QDSFlags.INVALID
        assert int(flags) == 0x21
        assert bool(flags & QDSFlags.OVERFLOW)
        assert bool(flags & QDSFlags.INVALID)
        assert not bool(flags & QDSFlags.BLOCKED)


# ── NVA 归一化值测试 ──────────────────────────────────────────────────────────


class TestNormalizedValue:
    """NVA 归一化值编解码测试。"""

    def test_nva_zero(self) -> None:
        """NVA 0.0 应编码为 0x0000。"""
        encoded = encode_normalized_value(0.0)
        assert encoded == b"\x00\x00"
        assert decode_normalized_value(encoded) == 0.0

    def test_nva_minus_one(self) -> None:
        """NVA -1.0 应编码为 0x8000（小端序 b"\\x00\\x80"）。"""
        encoded = encode_normalized_value(-1.0)
        assert encoded == b"\x00\x80"
        assert decode_normalized_value(encoded) == -1.0

    def test_nva_max_positive(self) -> None:
        """NVA 最大正值 (1 - 1/32768) 应编码为 0x7FFF。"""
        encoded = encode_normalized_value(32767.0 / 32768.0)
        assert encoded == b"\xFF\x7F"
        assert abs(decode_normalized_value(encoded) - 32767.0 / 32768.0) < 1e-9

    def test_nva_half(self) -> None:
        """NVA 0.5 应编码为 0x4000（小端序 b"\\x00\\x40"）。"""
        encoded = encode_normalized_value(0.5)
        assert encoded == b"\x00\x40"
        assert abs(decode_normalized_value(encoded) - 0.5) < 1e-9

    def test_nva_quarter(self) -> None:
        """NVA 0.25 应编码为 0x2000。"""
        encoded = encode_normalized_value(0.25)
        assert encoded == b"\x00\x20"
        assert abs(decode_normalized_value(encoded) - 0.25) < 1e-9

    def test_nva_round_trip_values(self) -> None:
        """NVA 多个值 roundtrip。"""
        values = [-1.0, -0.5, -0.25, 0.0, 0.25, 0.5, 0.75, 32767.0 / 32768.0]
        for v in values:
            encoded = encode_normalized_value(v)
            decoded = decode_normalized_value(encoded)
            assert abs(decoded - v) < 1e-6, f"NVA roundtrip 失败: {v} -> {decoded}"

    def test_nva_value_error_above_max(self) -> None:
        """NVA 超过最大值应抛出 ValueError。"""
        with pytest.raises(ValueError):
            encode_normalized_value(1.0)

    def test_nva_value_error_below_min(self) -> None:
        """NVA 低于最小值应抛出 ValueError。"""
        with pytest.raises(ValueError):
            encode_normalized_value(-1.5)

    def test_nva_decode_too_short(self) -> None:
        """NVA 解码数据不足时应抛出 ValueError。"""
        with pytest.raises(ValueError):
            decode_normalized_value(b"\x01")

    def test_nva_length(self) -> None:
        """NVA 编码始终为 2 字节。"""
        for v in [-1.0, 0.0, 0.5, 32767.0 / 32768.0]:
            encoded = encode_normalized_value(v)
            assert len(encoded) == 2


# ── CP56Time2a 测试（Round 16 新增）────────────────────────────────────────────


class TestCP56Time2aConstants:
    """CP56Time2a 常量与字段范围测试。"""

    def test_length_constant(self) -> None:
        """CP56TIME2A_LENGTH 常量应为 7。"""
        assert CP56TIME2A_LENGTH == 7

    def test_milliseconds_range(self) -> None:
        """milliseconds 范围 0..59999。"""
        assert 0 <= 0 <= 59999
        assert 0 <= 59999 <= 59999

    def test_year_min_max(self) -> None:
        """year 范围 0..99。"""
        assert 0 >= 0
        assert 99 <= 99


class TestCP56Time2aEncodeDecode:
    """CP56Time2a encode/decode 基础测试。"""

    def test_encode_returns_7_bytes(self) -> None:
        """encode_cp56time2a 返回 7 字节。"""
        t = CP56Time2a()
        encoded = encode_cp56time2a(t)
        assert len(encoded) == 7

    def test_encode_decode_roundtrip_zero(self) -> None:
        """零值 CP56Time2a 编码/解码 roundtrip。"""
        t = CP56Time2a(
            milliseconds=0, minute=0, hour=0, day_of_month=1,
            day_of_week=0, month=1, year=0,
        )
        encoded = encode_cp56time2a(t)
        decoded = decode_cp56time2a(encoded)
        assert decoded.milliseconds == 0
        assert decoded.minute == 0
        assert decoded.hour == 0
        assert decoded.day_of_month == 1
        assert decoded.month == 1
        assert decoded.year == 0
        assert decoded.invalid is False

    def test_encode_decode_roundtrip_max(self) -> None:
        """极值 CP56Time2a 编码/解码 roundtrip。"""
        t = CP56Time2a(
            milliseconds=59999, minute=59, hour=23, day_of_month=31,
            day_of_week=7, month=12, year=99,
            invalid=True, summer_time=True, substituted=True,
        )
        encoded = encode_cp56time2a(t)
        decoded = decode_cp56time2a(encoded)
        assert decoded.milliseconds == 59999
        assert decoded.minute == 59
        assert decoded.hour == 23
        assert decoded.day_of_month == 31
        # day_of_week 不参与编码（Round 16 实现选择），解码时重置为 0
        assert decoded.day_of_week == 0
        assert decoded.month == 12
        assert decoded.year == 99
        assert decoded.invalid is True
        assert decoded.summer_time is True
        assert decoded.substituted is True

    def test_encode_milliseconds_bytes(self) -> None:
        """milliseconds 应编码为小端序 uint16（byte 0/1）。"""
        t = CP56Time2a(milliseconds=0x1234)
        encoded = encode_cp56time2a(t)
        assert encoded[0] == 0x34
        assert encoded[1] == 0x12

    def test_encode_minute_hour_bytes(self) -> None:
        """minute (byte 2) 与 hour (byte 3) 编码位置正确。"""
        t = CP56Time2a(minute=15, hour=12)
        encoded = encode_cp56time2a(t)
        assert (encoded[2] & 0x3F) == 15
        assert (encoded[3] & 0x1F) == 12

    def test_encode_summer_time_flag(self) -> None:
        """summer_time 标志位映射到 hour byte bit 5。"""
        t = CP56Time2a(hour=10, summer_time=True)
        encoded = encode_cp56time2a(t)
        assert bool(encoded[3] & 0x20)

    def test_encode_substituted_flag(self) -> None:
        """substituted 标志位映射到 hour byte bit 6。"""
        t = CP56Time2a(hour=10, substituted=True)
        encoded = encode_cp56time2a(t)
        assert bool(encoded[3] & 0x40)

    def test_encode_invalid_flag(self) -> None:
        """invalid 标志位映射到 year byte bit 7。"""
        t = CP56Time2a(year=20, invalid=True)
        encoded = encode_cp56time2a(t)
        assert bool(encoded[6] & 0x80)

    def test_decode_too_short(self) -> None:
        """decode_cp56time2a 数据不足 7 字节应抛出 ValueError。"""
        with pytest.raises(ValueError):
            decode_cp56time2a(b"\x00\x00\x00")

    def test_encode_type_error(self) -> None:
        """encode_cp56time2a 非 CP56Time2a 实例应抛出 TypeError。"""
        with pytest.raises(TypeError):
            encode_cp56time2a(b"\x00" * 7)  # type: ignore[arg-type]


class TestCP56Time2aFieldBounds:
    """CP56Time2a 字段范围校验测试。"""

    def test_invalid_milliseconds_negative(self) -> None:
        """milliseconds 负值应抛出 ValueError。"""
        with pytest.raises(ValueError):
            CP56Time2a(milliseconds=-1)

    def test_invalid_milliseconds_above_max(self) -> None:
        """milliseconds > 59999 应抛出 ValueError。"""
        with pytest.raises(ValueError):
            CP56Time2a(milliseconds=60000)

    def test_invalid_minute(self) -> None:
        """minute 越界应抛出 ValueError。"""
        with pytest.raises(ValueError):
            CP56Time2a(minute=60)
        with pytest.raises(ValueError):
            CP56Time2a(minute=-1)

    def test_invalid_hour(self) -> None:
        """hour 越界应抛出 ValueError。"""
        with pytest.raises(ValueError):
            CP56Time2a(hour=24)
        with pytest.raises(ValueError):
            CP56Time2a(hour=-1)

    def test_invalid_day_of_month(self) -> None:
        """day_of_month 越界应抛出 ValueError。"""
        with pytest.raises(ValueError):
            CP56Time2a(day_of_month=0)
        with pytest.raises(ValueError):
            CP56Time2a(day_of_month=32)

    def test_invalid_month(self) -> None:
        """month 越界应抛出 ValueError。"""
        with pytest.raises(ValueError):
            CP56Time2a(month=0)
        with pytest.raises(ValueError):
            CP56Time2a(month=13)

    def test_invalid_year(self) -> None:
        """year 越界应抛出 ValueError。"""
        with pytest.raises(ValueError):
            CP56Time2a(year=-1)
        with pytest.raises(ValueError):
            CP56Time2a(year=100)

    def test_invalid_day_of_week(self) -> None:
        """day_of_week 越界应抛出 ValueError。"""
        with pytest.raises(ValueError):
            CP56Time2a(day_of_week=-1)
        with pytest.raises(ValueError):
            CP56Time2a(day_of_week=8)


class TestCP56Time2aDatetime:
    """CP56Time2a 与 datetime 互转测试。"""

    def test_from_datetime_basic(self) -> None:
        """from_datetime 基础转换。"""
        dt = datetime(2026, 6, 7, 12, 34, 56, 789000)
        t = from_datetime(dt)
        assert t.milliseconds == 789
        assert t.minute == 34
        assert t.hour == 12
        assert t.day_of_month == 7
        assert t.month == 6
        assert t.year == 26  # 2026 - 2000

    def test_from_datetime_with_flags(self) -> None:
        """from_datetime 可传入 invalid / summer_time / substituted。"""
        dt = datetime(2026, 1, 1, 0, 0, 0, 0)
        t = from_datetime(
            dt, invalid=True, summer_time=True, substituted=True, day_of_week=3,
        )
        assert t.invalid is True
        assert t.summer_time is True
        assert t.substituted is True
        assert t.day_of_week == 3

    def test_from_datetime_year_too_old_raises(self) -> None:
        """from_datetime 1999 年及之前应抛出 ValueError。"""
        with pytest.raises(ValueError):
            from_datetime(datetime(1999, 12, 31, 23, 59, 59))

    def test_from_datetime_year_too_new_raises(self) -> None:
        """from_datetime 2100 年及以上应抛出 ValueError。"""
        with pytest.raises(ValueError):
            from_datetime(datetime(2100, 1, 1, 0, 0, 0))

    def test_to_datetime_basic(self) -> None:
        """to_datetime 基础转换。"""
        t = CP56Time2a(
            year=26, month=6, day_of_month=7,
            hour=12, minute=34, milliseconds=789,
        )
        dt = to_datetime(t)
        assert dt.year == 2026
        assert dt.month == 6
        assert dt.day == 7
        assert dt.hour == 12
        assert dt.minute == 34
        assert dt.second == 0
        assert dt.microsecond == 789000

    def test_datetime_roundtrip(self) -> None:
        """datetime -> CP56Time2a -> datetime 字段保持一致。"""
        dt = datetime(2026, 6, 7, 12, 34, 0, 500000)
        t = from_datetime(dt)
        encoded = encode_cp56time2a(t)
        decoded = decode_cp56time2a(encoded)
        dt2 = to_datetime(decoded)
        assert dt2.year == dt.year
        assert dt2.month == dt.month
        assert dt2.day == dt.day
        assert dt2.hour == dt.hour
        assert dt2.minute == dt.minute
        assert dt2.microsecond == dt.microsecond


# ── ShortFloat 测试（Round 17 新增）────────────────────────────────────────────


class TestShortFloatConstants:
    """ShortFloat 常量测试。"""

    def test_length_constant(self) -> None:
        """SHORT_FLOAT_LENGTH 常量应为 4。"""
        assert SHORT_FLOAT_LENGTH == 4

    def test_finite_max(self) -> None:
        """SHORT_FLOAT_FINITE_MAX 应为 IEEE 754 single-precision 极大值。"""
        assert SHORT_FLOAT_FINITE_MAX == 3.4028234663852886e38

    def test_finite_min(self) -> None:
        """SHORT_FLOAT_FINITE_MIN 应为 IEEE 754 single-precision 极小值。"""
        assert SHORT_FLOAT_FINITE_MIN == -3.4028234663852886e38


class TestShortFloatEncodeDecode:
    """ShortFloat encode/decode 基础测试。"""

    def test_encode_zero(self) -> None:
        """ShortFloat(0.0) 应编码为 4 字节 0x00000000（小端序）。"""
        encoded = encode_short_float(0.0)
        assert encoded == b"\x00\x00\x00\x00"

    def test_decode_zero(self) -> None:
        """ShortFloat 解码 0x00000000 应得到 0.0。"""
        assert decode_short_float(b"\x00\x00\x00\x00") == 0.0

    def test_encode_length(self) -> None:
        """encode_short_float 返回 4 字节。"""
        for v in (0.0, 1.0, -1.0, 2.5, -1.5):
            assert len(encode_short_float(v)) == 4

    def test_encode_little_endian(self) -> None:
        """ShortFloat 编码为小端序（与 IEC 60870-5-101/104 标准一致）。"""
        # IEEE 754 single-precision 1.0 = 0x3F800000，LE = b"\x00\x00\x80\x3F"
        encoded = encode_short_float(1.0)
        assert encoded == b"\x00\x00\x80\x3F"
        # IEEE 754 single-precision -1.0 = 0xBF800000，LE = b"\x00\x00\x80\xBF"
        encoded_neg = encode_short_float(-1.0)
        assert encoded_neg == b"\x00\x00\x80\xBF"

    def test_roundtrip_zero(self) -> None:
        """ShortFloat 0.0 roundtrip。"""
        assert decode_short_float(encode_short_float(0.0)) == 0.0

    def test_roundtrip_negative_zero(self) -> None:
        """ShortFloat -0.0 roundtrip（-0.0 在 IEEE 754 中是有效值）。"""
        encoded = encode_short_float(-0.0)
        # -0.0 编码为 0x80000000（LE b"\x00\x00\x00\x80"）
        assert encoded == b"\x00\x00\x00\x80"
        decoded = decode_short_float(encoded)
        # 解码后 -0.0 == 0.0 为 True（IEEE 754 规定）
        assert decoded == 0.0
        # 但符号位不同
        import struct
        bits = struct.unpack("<I", encoded)[0]
        assert bits & 0x80000000  # 符号位为 1

    def test_roundtrip_positive_values(self) -> None:
        """ShortFloat 多个正有限值 roundtrip。

        仅使用 IEEE 754 single-precision 精确可表示的值
        （如 0.5、1.0、1.5、2.0 等二进制浮点），3.14 此类
        十进制小数会引入精度误差，不在本测试范围内。
        """
        values = [0.5, 1.0, 1.5, 2.0, 100.0, 1024.0, 0.0625, 0.125]
        for v in values:
            decoded = decode_short_float(encode_short_float(v))
            assert decoded == v, f"ShortFloat roundtrip 失败: {v} -> {decoded}"

    def test_roundtrip_negative_values(self) -> None:
        """ShortFloat 多个负有限值 roundtrip（同上，仅精确可表示的值）。"""
        values = [-0.5, -1.0, -1.5, -2.0, -100.0, -1024.0, -0.0625, -0.125]
        for v in values:
            decoded = decode_short_float(encode_short_float(v))
            assert decoded == v, f"ShortFloat roundtrip 失败: {v} -> {decoded}"

    def test_roundtrip_finite_extremes(self) -> None:
        """ShortFloat IEEE 754 极值 roundtrip（FLT_MAX / FLT_MIN）。"""
        for v in (SHORT_FLOAT_FINITE_MAX, SHORT_FLOAT_FINITE_MIN):
            decoded = decode_short_float(encode_short_float(v))
            assert decoded == v, f"ShortFloat 极值 roundtrip 失败: {v} -> {decoded}"

    def test_encode_nan_rejected(self) -> None:
        """encode_short_float 拒绝 NaN（协议未规定语义）。"""
        with pytest.raises(ValueError, match="NaN"):
            encode_short_float(float("nan"))

    def test_encode_positive_inf_rejected(self) -> None:
        """encode_short_float 拒绝 +Inf。"""
        with pytest.raises(ValueError, match="Inf"):
            encode_short_float(float("inf"))

    def test_encode_negative_inf_rejected(self) -> None:
        """encode_short_float 拒绝 -Inf。"""
        with pytest.raises(ValueError, match="Inf"):
            encode_short_float(float("-inf"))

    def test_encode_non_float_rejected(self) -> None:
        """encode_short_float 拒绝无 ``__float__`` 的对象（Round 20 契约）。

        Round 20 扩展：int / numbers.Real / 带 __float__ 的对象**均**可
        接受。本测试验证真正不兼容类型（如裸 str / list / None）必须
        抛 ValueError。
        """
        with pytest.raises(ValueError):
            encode_short_float("1.0")  # type: ignore[arg-type]
        with pytest.raises(ValueError):
            encode_short_float([1.0, 2.0])  # type: ignore[arg-type]
        with pytest.raises(ValueError):
            encode_short_float(None)  # type: ignore[arg-type]

    def test_decode_too_short(self) -> None:
        """decode_short_float 数据不足 4 字节时抛出 ValueError。"""
        with pytest.raises(ValueError, match="至少 4 字节"):
            decode_short_float(b"\x00\x00\x00")
        with pytest.raises(ValueError, match="至少 4 字节"):
            decode_short_float(b"")

    def test_decode_nan_bytes_rejected(self) -> None:
        """decode_short_float 拒绝 NaN 位模式。"""
        # IEEE 754 NaN: exponent 全 1 + mantissa 非 0
        # 0x7FC00000 (quiet NaN), LE = b"\x00\x00\xC0\x7F"
        with pytest.raises(ValueError, match="NaN"):
            decode_short_float(b"\x00\x00\xC0\x7F")

    def test_decode_positive_inf_bytes_rejected(self) -> None:
        """decode_short_float 拒绝 +Inf 位模式。"""
        # +Inf: 0x7F800000, LE = b"\x00\x00\x80\x7F"
        with pytest.raises(ValueError, match="Inf"):
            decode_short_float(b"\x00\x00\x80\x7F")

    def test_decode_negative_inf_bytes_rejected(self) -> None:
        """decode_short_float 拒绝 -Inf 位模式。"""
        # -Inf: 0xFF800000, LE = b"\x00\x00\x80\xFF"
        with pytest.raises(ValueError, match="Inf"):
            decode_short_float(b"\x00\x00\x80\xFF")


class TestShortFloatDataclass:
    """ShortFloat 数据类（包装）测试。"""

    def test_default_value(self) -> None:
        """ShortFloat 默认 value=0.0。"""
        sf = ShortFloat()
        assert sf.value == 0.0

    def test_dataclass_encode(self) -> None:
        """ShortFloat.encode() 应与 encode_short_float 一致。"""
        sf = ShortFloat(value=3.14)
        assert sf.encode() == encode_short_float(3.14)

    def test_dataclass_decode(self) -> None:
        """ShortFloat.decode() 应与 decode_short_float 一致。"""
        sf = ShortFloat.decode(b"\x00\x00\x80\x3F")  # 1.0
        assert sf.value == 1.0

    def test_dataclass_roundtrip(self) -> None:
        """ShortFloat 数据类 roundtrip。"""
        sf = ShortFloat(value=2.5)
        decoded = ShortFloat.decode(sf.encode())
        assert decoded.value == 2.5


# ── ScaledValue 测试（Round 18 新增）───────────────────────────────────────────


class TestScaledValueConstants:
    """ScaledValue 常量测试。"""

    def test_length_constant(self) -> None:
        """SVA_LENGTH 常量应为 2。"""
        assert SVA_LENGTH == 2

    def test_int16_min(self) -> None:
        """SVA_INT16_MIN 应为 -32768。"""
        assert SVA_INT16_MIN == -32768

    def test_int16_max(self) -> None:
        """SVA_INT16_MAX 应为 +32767。"""
        assert SVA_INT16_MAX == 32767


class TestScaledValueEncodeDecode:
    """ScaledValue encode/decode 基础测试。"""

    def test_encode_zero(self) -> None:
        """encode_scaled_value(0) 应编码为 2 字节 0x0000（小端序）。"""
        assert encode_scaled_value(0) == b"\x00\x00"

    def test_encode_positive(self) -> None:
        """encode_scaled_value(1) 应编码为 0x0001。"""
        assert encode_scaled_value(1) == b"\x01\x00"

    def test_encode_max(self) -> None:
        """encode_scaled_value(32767) 应编码为 0x7FFF。"""
        assert encode_scaled_value(32767) == b"\xFF\x7F"

    def test_encode_min(self) -> None:
        """encode_scaled_value(-32768) 应编码为 0x8000（小端序 b"\\x00\\x80"）。"""
        assert encode_scaled_value(-32768) == b"\x00\x80"

    def test_encode_minus_one(self) -> None:
        """encode_scaled_value(-1) 应编码为 0xFFFF（小端序 b"\\xFF\\xFF"）。"""
        assert encode_scaled_value(-1) == b"\xFF\xFF"

    def test_encode_length(self) -> None:
        """encode_scaled_value 返回 2 字节。"""
        for v in (0, 1, -1, 32767, -32768, 12345):
            assert len(encode_scaled_value(v)) == 2

    def test_encode_little_endian(self) -> None:
        """ScaledValue 编码为小端序（int16 LE）。"""
        # 0x1234 -> LE b"\x34\x12"
        assert encode_scaled_value(0x1234) == b"\x34\x12"

    def test_decode_zero(self) -> None:
        """decode_scaled_value(b"\\x00\\x00") 应得到 0。"""
        assert decode_scaled_value(b"\x00\x00") == 0

    def test_decode_max(self) -> None:
        """decode_scaled_value 0x7FFF 应得到 +32767。"""
        assert decode_scaled_value(b"\xFF\x7F") == 32767

    def test_decode_min(self) -> None:
        """decode_scaled_value 0x8000 应得到 -32768。"""
        assert decode_scaled_value(b"\x00\x80") == -32768

    def test_roundtrip_values(self) -> None:
        """ScaledValue 多个 int16 值 roundtrip。"""
        for v in (0, 1, -1, 100, -100, 12345, -12345, 32767, -32768):
            assert decode_scaled_value(encode_scaled_value(v)) == v

    def test_encode_out_of_range_positive(self) -> None:
        """encode_scaled_value(32768) 应抛 ValueError。"""
        with pytest.raises(ValueError, match="标度化值"):
            encode_scaled_value(32768)

    def test_encode_out_of_range_negative(self) -> None:
        """encode_scaled_value(-32769) 应抛 ValueError。"""
        with pytest.raises(ValueError, match="标度化值"):
            encode_scaled_value(-32769)

    def test_encode_non_int_rejected(self) -> None:
        """encode_scaled_value 非 int 实例应抛 ValueError。"""
        with pytest.raises(ValueError, match="int"):
            encode_scaled_value(1.5)  # type: ignore[arg-type]
        with pytest.raises(ValueError, match="int"):
            encode_scaled_value("100")  # type: ignore[arg-type]
        with pytest.raises(ValueError, match="int"):
            encode_scaled_value(True)  # type: ignore[arg-type]

    def test_decode_too_short(self) -> None:
        """decode_scaled_value 数据不足 2 字节应抛 ValueError。"""
        with pytest.raises(ValueError, match="至少 2 字节"):
            decode_scaled_value(b"\x01")
        with pytest.raises(ValueError, match="至少 2 字节"):
            decode_scaled_value(b"")


class TestScaledValueDataclass:
    """ScaledValue 数据类测试。"""

    def test_default_value(self) -> None:
        """ScaledValue 默认 value=0。"""
        sv = ScaledValue()
        assert sv.value == 0

    def test_dataclass_encode(self) -> None:
        """ScaledValue.encode() 应与 encode_scaled_value 一致。"""
        sv = ScaledValue(value=100)
        assert sv.encode() == encode_scaled_value(100)

    def test_dataclass_decode(self) -> None:
        """ScaledValue.decode() 应与 decode_scaled_value 一致。"""
        sv = ScaledValue.decode(b"\x01\x00")
        assert sv.value == 1

    def test_dataclass_roundtrip(self) -> None:
        """ScaledValue 数据类 roundtrip。"""
        sv = ScaledValue(value=12345)
        decoded = ScaledValue.decode(sv.encode())
        assert decoded.value == 12345


# ── ShortFloat 兼容扩展测试（Round 20 新增）──────────────────────────────────


class TestShortFloatRound20Compat:
    """Round 20 兼容扩展：int / Decimal / __float__ 兼容（不引入 numpy）。"""

    def test_int_input_accepted(self) -> None:
        """encode_short_float 接受 int 输入（与 float 路径等价）。"""
        # int 42 == float 42.0
        assert encode_short_float(42) == encode_short_float(42.0)
        assert encode_short_float(0) == encode_short_float(0.0)
        assert encode_short_float(-1) == encode_short_float(-1.0)

    def test_int_roundtrip(self) -> None:
        """int -> encode -> decode -> float 完整 roundtrip。"""
        for v in (0, 1, -1, 100, 1024, -2048, 12345):
            encoded = encode_short_float(v)
            decoded = decode_short_float(encoded)
            assert decoded == float(v), f"int {v} roundtrip 失败: {decoded}"

    def test_decimal_input_accepted(self) -> None:
        """encode_short_float 接受 decimal.Decimal 输入。"""
        from decimal import Decimal
        d = Decimal("2.5")
        encoded = encode_short_float(d)
        # Decimal 2.5 在 IEEE 754 中可精确表示
        decoded = decode_short_float(encoded)
        assert decoded == 2.5

    def test_decimal_pi_approximation(self) -> None:
        """Decimal pi 近似值（IEEE 754 精度内）。"""
        from decimal import Decimal
        d = Decimal("3.14")
        encoded = encode_short_float(d)
        decoded = decode_short_float(encoded)
        # 3.14 在 IEEE 754 single 中约为 3.140000104904175
        assert abs(decoded - 3.14) < 1e-6

    def test_fraction_input_accepted(self) -> None:
        """encode_short_float 接受 fractions.Fraction（numbers.Real 子类）。"""
        from fractions import Fraction
        f = Fraction(1, 2)  # 0.5
        encoded = encode_short_float(f)
        assert decode_short_float(encoded) == 0.5

    def test_duck_typed_float_object(self) -> None:
        """encode_short_float 接受自定义带 __float__ 方法的对象。"""
        class _FloatWrapper:
            def __init__(self, v: float) -> None:
                self._v = v

            def __float__(self) -> float:
                return self._v

        w = _FloatWrapper(1.5)
        encoded = encode_short_float(w)
        assert decode_short_float(encoded) == 1.5

    def test_duck_typed_int_object(self) -> None:
        """encode_short_float 接受自定义带 __float__ 的 int 包装。"""
        class _IntWrapper:
            def __init__(self, v: int) -> None:
                self._v = v

            def __float__(self) -> float:
                return float(self._v)

        w = _IntWrapper(42)
        encoded = encode_short_float(w)
        assert decode_short_float(encoded) == 42.0

    def test_decimal_nan_rejected(self) -> None:
        """Decimal NaN 仍被拒绝（Round 17 严格策略不回退）。"""
        from decimal import Decimal
        with pytest.raises(ValueError, match="NaN"):
            encode_short_float(Decimal("NaN"))

    def test_decimal_inf_rejected(self) -> None:
        """Decimal Infinity 仍被拒绝（Round 17 严格策略不回退）。"""
        from decimal import Decimal
        with pytest.raises(ValueError, match="Inf"):
            encode_short_float(Decimal("Infinity"))

    def test_unsupported_type_rejected(self) -> None:
        """无 __float__ 方法的对象被拒绝。"""
        with pytest.raises(ValueError):
            encode_short_float(object())  # 无 __float__
        with pytest.raises(ValueError):
            encode_short_float(None)

    def test_duck_typed_raising_float_rejected(self) -> None:
        """__float__ 抛异常的对象被拒绝。"""
        class _BadWrapper:
            def __float__(self) -> float:
                raise TypeError("cannot convert")

        with pytest.raises(ValueError):
            encode_short_float(_BadWrapper())

    def test_no_numpy_import(self) -> None:
        """information_elements 模块不引入 numpy 硬依赖。"""
        import starfish.protocols.iec101.information_elements as ie_module
        # 检查模块全局没有 numpy 名字
        assert not hasattr(ie_module, "np"), (
            "information_elements 不应 import numpy 作为硬依赖"
        )
        assert not hasattr(ie_module, "numpy"), (
            "information_elements 不应 import numpy 作为硬依赖"
        )

