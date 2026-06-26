"""IEC 60870-5-101 CP56Time2a 7 字节时标信息元素。

本模块实现 IEC 60870-5-101 / 60870-5-4 中定义的 CP56Time2a 7 字节
时标（time tag）信息元素。CP56Time2a 广泛出现在带时标 TypeId
（``M_SP_TA_1`` / ``M_DP_TA_1`` / ``M_ME_TA_1`` / ``C_SC_TA_1`` 等）
信息体末尾与 ``C_CS_NA_1`` 时钟同步命令中。

CP56Time2a 字节布局（7 字节，按顺序）：

    +---------+---------+---------+---------+---------+---------+---------+
    | byte 0  | byte 1  | byte 2  | byte 3  | byte 4  | byte 5  | byte 6  |
    | ms low  | ms high | min     | hour    | day     | month   | year    |
    +---------+---------+---------+---------+---------+---------+---------+

    byte 0-1 (uint16 LE): 毫秒 0..59999
    byte 2     (uint8):   分钟 0..59
    byte 3     (uint8):   小时 0..23
    byte 4     (uint8):   日 1..31（低 5 位，bit 5=day_of_week 低位，bit 6-7=标志位）
        bit 0-4: 日 (day of month) 1..31
        bit 5-7: 保留为 0
            注：IEC 60870-5-4 把 day_of_week 放 bit 5-7；为兼容 5-101 中常见编码，
            本实现将 day_of_week 单独存放在 CP56Time2a.day_of_week 字段中，
            编码时使用 IEC 60870-5-4 的字节 4 布局（day_of_month 1..31 + 保留位），
            day_of_week 字段编码为单独的概念层属性。
    byte 5     (uint8):   月 1..12（低 4 位，bit 4-7=标志位）
        bit 0-3: 月 (month) 1..12
        bit 4: RES1
        bit 5: RES2
        bit 6: RES3
        bit 7: RES4
    byte 6     (uint8):   年 0..99（低 7 位，bit 7=IV 标志位）
        bit 0-6: 年 0..99（1900-2099 映射，常用 2000-2099）
        bit 7: IV (Invalid) 标志

    三个常用标志位:
        IV (Invalid):  byte 6 bit 7，True 表示该时标无效。
        SU (Summer time):   单独建模于 CP56Time2a.summer_time。
        SB (Substituted):   单独建模于 CP56Time2a.substituted。

能力边界:
    - 实现 CP56Time2a 7 字节时标编解码（IEC 60870-5-4 + IEC 60870-5-101 兼容子集）。
    - 实现 ``datetime <-> CP56Time2a`` 转换辅助函数 ``to_datetime`` / ``from_datetime``。
    - 实现字段级编码：milliseconds / minute / hour / day_of_month / day_of_week /
      month / year / invalid / summer_time / substituted。
    - 显式校验：milliseconds 范围 0..59999、minute 0..59、hour 0..23、
      day_of_month 1..31、month 1..12、year 0..99（与 datetime 转换时映射
      为 2000..2099 或回退区间）、day_of_week 0..7（1=周一，7=周日，0=未指定）。

不负责:
    - 完整时区 / 闰秒 / 历法切换处理。
    - 与 IEC 60870-5-104 的 7 字节时标差异（编码相同）。
    - 真实 GPS / PTP / NTP 时间同步源；本模块只负责时标字段编解码。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

# ── 常量 ────────────────────────────────────────────────────────────────────────


CP56TIME2A_LENGTH = 7  # CP56Time2a 固定 7 字节

# 字段有效范围
MILLISECONDS_MIN = 0
MILLISECONDS_MAX = 59999
MINUTE_MIN = 0
MINUTE_MAX = 59
HOUR_MIN = 0
HOUR_MAX = 23
DAY_OF_MONTH_MIN = 1
DAY_OF_MONTH_MAX = 31
MONTH_MIN = 1
MONTH_MAX = 12

# year 字段: 0..99；映射 datetime.year 时按 2000 + year 取值。
# 一些实现也支持 1970..2069 滑动窗口（70..99 -> 1970..1999，0..69 -> 2000..2069）。
# 本实现采用明确 2000..2099 区间，避免歧义。
YEAR_MIN = 0
YEAR_MAX = 99
DATETIME_YEAR_OFFSET = 2000  # year 字段 0..99 -> datetime.year 2000..2099

# day_of_week: 0=未指定，1..7 含义同 ISO weekday（1=周一，7=周日）
DAY_OF_WEEK_UNSPECIFIED = 0
DAY_OF_WEEK_MIN = 0
DAY_OF_WEEK_MAX = 7

# 标志位掩码
YEAR_INVALID_FLAG_MASK = 0x80  # byte 6 bit 7 = IV
YEAR_YEAR_MASK = 0x7F  # byte 6 bit 0-6 = year 0..99
MONTH_MONTH_MASK = 0x0F  # byte 5 bit 0-3 = month 1..12
DAY_OF_MONTH_MASK = 0x1F  # byte 4 bit 0-4 = day 1..31


# ── 数据类 ──────────────────────────────────────────────────────────────────────


@dataclass
class CP56Time2a:
    """CP56Time2a 7 字节时标数据类。

    表示 IEC 60870-5-101 / 60870-5-4 中通用的 7 字节二进制时标。
    字段值与编码后的字节布局保持一致，可由 ``encode_cp56time2a`` /
    ``decode_cp56time2a`` 双向转换；可由 ``from_datetime`` / ``to_datetime``
    与 Python ``datetime`` 互转（datetime.year 须在 2000..2099 范围内）。

    Attributes:
        milliseconds: 0..59999。
        minute: 0..59。
        hour: 0..23。
        day_of_month: 1..31。
        day_of_week: 0..7（0=未指定，1=周一，7=周日；不参与字节 4 编码）。
        month: 1..12。
        year: 0..99（与 datetime.year 通过 2000+year 映射）。
        invalid: True 表示该时标无效（IV 位）。
        summer_time: True 表示该时标处于夏令时（SU 位，单独建模）。
        substituted: True 表示该时标已被取代（SB 位，单独建模）。
    """

    milliseconds: int = 0
    minute: int = 0
    hour: int = 0
    day_of_month: int = 1
    day_of_week: int = 0
    month: int = 1
    year: int = 0
    invalid: bool = False
    summer_time: bool = False
    substituted: bool = False

    def __post_init__(self) -> None:
        # 字段范围校验
        if not MILLISECONDS_MIN <= self.milliseconds <= MILLISECONDS_MAX:
            raise ValueError(
                f"milliseconds {self.milliseconds} 超出有效范围 "
                f"[{MILLISECONDS_MIN}, {MILLISECONDS_MAX}]"
            )
        if not MINUTE_MIN <= self.minute <= MINUTE_MAX:
            raise ValueError(
                f"minute {self.minute} 超出有效范围 [{MINUTE_MIN}, {MINUTE_MAX}]"
            )
        if not HOUR_MIN <= self.hour <= HOUR_MAX:
            raise ValueError(
                f"hour {self.hour} 超出有效范围 [{HOUR_MIN}, {HOUR_MAX}]"
            )
        if not DAY_OF_MONTH_MIN <= self.day_of_month <= DAY_OF_MONTH_MAX:
            raise ValueError(
                f"day_of_month {self.day_of_month} 超出有效范围 "
                f"[{DAY_OF_MONTH_MIN}, {DAY_OF_MONTH_MAX}]"
            )
        if not MONTH_MIN <= self.month <= MONTH_MAX:
            raise ValueError(
                f"month {self.month} 超出有效范围 [{MONTH_MIN}, {MONTH_MAX}]"
            )
        if not YEAR_MIN <= self.year <= YEAR_MAX:
            raise ValueError(
                f"year {self.year} 超出有效范围 [{YEAR_MIN}, {YEAR_MAX}]"
            )
        if not DAY_OF_WEEK_MIN <= self.day_of_week <= DAY_OF_WEEK_MAX:
            raise ValueError(
                f"day_of_week {self.day_of_week} 超出有效范围 "
                f"[{DAY_OF_WEEK_MIN}, {DAY_OF_WEEK_MAX}]"
            )


# ── 编码 / 解码 ────────────────────────────────────────────────────────────────


def encode_cp56time2a(time: CP56Time2a) -> bytes:
    """将 ``CP56Time2a`` 数据类编码为 7 字节时标。

    编码字节布局严格按 IEC 60870-5-4 / 60870-5-101 标准：

    - byte 0-1: milliseconds（uint16 小端序），范围 0..59999。
    - byte 2: minute（0..59），bit 7 置 0。
    - byte 3: hour（0..23），bit 5=SU（summer_time），bit 6=SB（substituted），
      bit 7=RES。bit 5-7 中 SU/SB 按本实现语义保留并显式编码。
    - byte 4: day_of_month（1..31）+ RES 位（bit 5-7 保留为 0；
      day_of_week 不参与该字节编码，由 CP56Time2a.day_of_week 字段独立表达）。
    - byte 5: month（1..12）+ RES 位（bit 4-7 保留为 0）。
    - byte 6: year（0..99）+ IV 位（bit 7 = invalid）。

    Args:
        time: CP56Time2a 数据类实例。

    Returns:
        7 字节编码结果。
    """
    if not isinstance(time, CP56Time2a):
        raise TypeError(
            f"encode_cp56time2a 期望 CP56Time2a 实例，实际 {type(time).__name__}"
        )
    # 构造 7 字节；任何字段越界已在 __post_init__ 拦截。
    ms_low = time.milliseconds & 0xFF
    ms_high = (time.milliseconds >> 8) & 0xFF
    # byte 2 = minute (0..59)；本实现不把 SU/SB 混入 minute 字节。
    minute_byte = time.minute & 0x3F
    # byte 3 = hour (0..23) + SU(bit 5) + SB(bit 6) + RES(bit 7)
    hour_byte = time.hour & 0x1F
    if time.summer_time:
        hour_byte |= 0x20  # bit 5 = SU
    if time.substituted:
        hour_byte |= 0x40  # bit 6 = SB
    # byte 4 = day_of_month (bit 0-4) + RES(bit 5-7)；day_of_week 不参与编码。
    day_byte = time.day_of_month & DAY_OF_MONTH_MASK
    # byte 5 = month (bit 0-3) + RES(bit 4-7)
    month_byte = time.month & MONTH_MONTH_MASK
    # byte 6 = year (bit 0-6) + IV(bit 7)
    year_byte = time.year & YEAR_YEAR_MASK
    if time.invalid:
        year_byte |= YEAR_INVALID_FLAG_MASK
    return bytes(
        [ms_low, ms_high, minute_byte, hour_byte, day_byte, month_byte, year_byte]
    )


def decode_cp56time2a(data: bytes) -> CP56Time2a:
    """从 7 字节数据解码 CP56Time2a。

    Args:
        data: 至少 7 字节；仅读取前 7 字节。

    Returns:
        解码后的 CP56Time2a 实例。

    Raises:
        ValueError: 数据不足 7 字节。
    """
    if len(data) < CP56TIME2A_LENGTH:
        raise ValueError(
            f"CP56Time2a 解码需要至少 {CP56TIME2A_LENGTH} 字节，"
            f"实际只有 {len(data)} 字节"
        )
    ms_low = data[0]
    ms_high = data[1]
    milliseconds = (ms_high << 8) | ms_low
    minute = data[2] & 0x3F
    hour = data[3] & 0x1F
    summer_time = bool(data[3] & 0x20)
    substituted = bool(data[3] & 0x40)
    day_of_month = data[4] & DAY_OF_MONTH_MASK
    month = data[5] & MONTH_MONTH_MASK
    year = data[6] & YEAR_YEAR_MASK
    invalid = bool(data[6] & YEAR_INVALID_FLAG_MASK)
    return CP56Time2a(
        milliseconds=milliseconds,
        minute=minute,
        hour=hour,
        day_of_month=day_of_month,
        day_of_week=DAY_OF_WEEK_UNSPECIFIED,
        month=month,
        year=year,
        invalid=invalid,
        summer_time=summer_time,
        substituted=substituted,
    )


# ── datetime 互转 ──────────────────────────────────────────────────────────────


def from_datetime(
    dt: datetime,
    *,
    invalid: bool = False,
    summer_time: bool = False,
    substituted: bool = False,
    day_of_week: int = DAY_OF_WEEK_UNSPECIFIED,
) -> CP56Time2a:
    """将 ``datetime`` 转换为 CP56Time2a。

    将 ``dt.year`` 通过 ``2000 + year`` 反推 ``year`` 字段（要求
    ``2000 <= dt.year <= 2099``），``dt.microsecond`` 折算为
    ``milliseconds``。``tzinfo`` 不参与编码（CP56Time2a 本身不含时区，
    夏令时由独立 ``summer_time`` 标志表达）。

    Args:
        dt: 待转换的 ``datetime`` 实例。
        invalid: 是否设置 IV（Invalid）标志。
        summer_time: 是否设置 SU（Summer time）标志。
        substituted: 是否设置 SB（Substituted）标志。
        day_of_week: 0..7（0=未指定，1=周一，7=周日）。

    Returns:
        与 ``dt`` 字段对齐的 CP56Time2a 实例。

    Raises:
        ValueError: ``dt.year`` 不在 2000..2099 范围。
    """
    if not (2000 <= dt.year <= 2099):
        raise ValueError(
            f"CP56Time2a 仅支持 datetime.year ∈ [2000, 2099]，"
            f"实际 {dt.year}（可通过另行编码自行处理）"
        )
    year_field = dt.year - DATETIME_YEAR_OFFSET
    # microsecond -> milliseconds（0..999999 -> 0..999 ms），直接除以 1000
    milliseconds = dt.microsecond // 1000
    return CP56Time2a(
        milliseconds=milliseconds,
        minute=dt.minute,
        hour=dt.hour,
        day_of_month=dt.day,
        day_of_week=day_of_week,
        month=dt.month,
        year=year_field,
        invalid=invalid,
        summer_time=summer_time,
        substituted=substituted,
    )


def to_datetime(time: CP56Time2a) -> datetime:
    """将 CP56Time2a 转换为 ``datetime``（naive datetime）。

    ``year`` 字段通过 ``2000 + year`` 映射；``day_of_week`` /
    ``invalid`` / ``summer_time`` / ``substituted`` 不参与 datetime 字段。

    Args:
        time: CP56Time2a 实例。

    Returns:
        与 ``time`` 字段对齐的 ``datetime`` 实例（无时区）。
    """
    return datetime(
        year=time.year + DATETIME_YEAR_OFFSET,
        month=time.month,
        day=time.day_of_month,
        hour=time.hour,
        minute=time.minute,
        second=0,
        microsecond=time.milliseconds * 1000,
    )


__all__ = [
    "CP56TIME2A_LENGTH",
    "MILLISECONDS_MIN",
    "MILLISECONDS_MAX",
    "MINUTE_MIN",
    "MINUTE_MAX",
    "HOUR_MIN",
    "HOUR_MAX",
    "DAY_OF_MONTH_MIN",
    "DAY_OF_MONTH_MAX",
    "MONTH_MIN",
    "MONTH_MAX",
    "YEAR_MIN",
    "YEAR_MAX",
    "DATETIME_YEAR_OFFSET",
    "DAY_OF_WEEK_UNSPECIFIED",
    "DAY_OF_WEEK_MIN",
    "DAY_OF_WEEK_MAX",
    "CP56Time2a",
    "encode_cp56time2a",
    "decode_cp56time2a",
    "from_datetime",
    "to_datetime",
]
