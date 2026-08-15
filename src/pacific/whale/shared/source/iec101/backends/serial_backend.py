"""IEC 101 串行通信 backend。

基于 Python 标准库（os、termios、fcntl、struct）
实现 IEC 60870-5-101 协议的串行通信客户端。
不依赖 pyserial 或任何第三方串口库。

职责边界：
- 实现 IEC 101 链路层帧构造（FT1.2 格式）和解析；
- 实现串口打开、参数配置（波特率、校验位、停止位、数据位）、关闭和资源清理；
- 实现 interrogation（C_IC_NA_1 总召唤）流程；
- 实现 spontaneous 数据接收基础框架；
- 不负责业务数据映射或采集策略编排——由 ingest adapter 处理；
- 不负责持久化或缓存——由上层 state cache 处理。

资源生命周期：
- connect() / disconnect() 管理串口文件描述符；
- 使用 os.open / os.close 管理 fd；
- 超时通过 asyncio.to_thread 实现；
- 异常路径必须确保 fd 关闭（finally 块）。

序列参数：
- serial_port: 串口设备路径；
- baudrate: 波特率（默认 9600）；
- parity: 校验位（'E'=偶校验是 IEC101 标准默认值，'N'/'O' 也支持）；
- stop_bits: 停止位（1 或 2，IEC101 通常为 1）；
- data_bits: 数据位（通常为 8）；
- link_address: 链路地址（默认 1）；
- common_address: ASDU 公共地址（默认 1）；
- timeout: 超时秒数。

IEC 101 帧格式（FT1.2）:
- 固定长度帧（5 字节）: [START=0x10][CTRL][LINK_ADDR][CS][END=0x16]
- 可变长度帧: [START=0x68][LENGTH][LENGTH][START=0x68][CTRL][LINK_ADDR]
                  [ASDU...][CS][END=0x16]

Write 状态：NOT_IMPLEMENTED。当前仅支持 interrogation 读取。
"""
from __future__ import annotations

import asyncio
import fcntl
import os
import select
import struct
import termios
from datetime import datetime, timezone

from pacific.whale.shared.source.iec101.backends.base import (
    RawIec101ReadResult,
)

# ── IEC 101 帧常量 ──────────────────────────────────────────────────

# 固定长度帧起始/结束
_FIXED_START: int = 0x10
_FRAME_END: int = 0x16
# 可变长度帧起始
_VARIABLE_START: int = 0x68

# 控制域常量
_CTRL_RESET_REMOTE_LINK: int = 0x00
_CTRL_RESET_LOCAL_LINK: int = 0x40
_CTRL_REQUEST_CLASS1: int = 0x0A
_CTRL_REQUEST_CLASS2: int = 0x0B
_CTRL_ACK: int = 0x20  # AFC=1 bit
_CTRL_FCB_BIT: int = 0x20

# ASDU 类型标识
_ASDU_C_IC_NA_1: int = 100  # 总召唤命令
_ASDU_C_IC_NA_1_TERM: int = 0x64  # 总召唤终止（也映射到类型 100）
_ASDU_M_ME_NC_1: int = 13  # 短浮点测量值
_ASDU_M_ME_NB_1: int = 11  # 归一化测量值
_ASDU_M_ME_TE_1: int = 15  # 带时标测量值
_ASDU_M_SP_NA_1: int = 1  # 单点信息
_ASDU_M_DP_NA_1: int = 3  # 双点信息

# COT（传送原因）
_COT_ACTIVATION: int = 6
_COT_ACTIVATION_CONFIRM: int = 7
_COT_DEACTIVATION: int = 8
_COT_DEACTIVATION_CONFIRM: int = 9
_COT_INTERROGATED: int = 20  # 总召唤响应
_COT_SPONTANEOUS: int = 3

# ASDU 构造常量
_ASDU_TYPE_IDX: int = 0
_ASDU_VSQ_IDX: int = 1  # 可变结构限定词
_ASDU_COT_IDX: int = 2
_ASDU_COMMON_ADDR_IDX: int = 3  # 2 字节
_ASDU_IOA_START: int = 5  # IOA 起始位置（最小 ASDU）

# ── 串口参数 ────────────────────────────────────────────────────────

_DEFAULT_SERIAL_TIMEOUT_S: float = 3.0
_DEFAULT_READ_FRAME_TIMEOUT_S: float = 10.0

# termios 常量映射
_BAUDRATE_MAP: dict[int, int] = {
    0: termios.B0,
    110: termios.B110,
    300: termios.B300,
    600: termios.B600,
    1200: termios.B1200,
    2400: termios.B2400,
    4800: termios.B4800,
    9600: termios.B9600,
    19200: termios.B19200,
    38400: termios.B38400,
    57600: termios.B57600,
    115200: termios.B115200,
    230400: termios.B230400,
}

_PARITY_FLAGS: dict[str, int] = {
    "N": 0,
    "E": termios.PARENB,
    "O": termios.PARENB | termios.PARODD,
}

_STOP_BITS_FLAGS: dict[int, int] = {
    1: 0,
    2: termios.CSTOPB,
}

_DATA_BITS_FLAGS: dict[int, int] = {
    7: termios.CS7,
    8: termios.CS8,
}


def _compute_checksum(data: bytes) -> int:
    """计算 IEC 101 算术和校验（checksum）。

    对字节序列求和后取低 8 位。

    Args:
        data: 需要计算校验和的字节序列。

    Returns:
        8 位校验和（0-255）。
    """
    return sum(data) & 0xFF


def _build_fixed_frame(ctrl: int, link_addr: int) -> bytes:
    """构造 IEC 101 固定长度帧（5 字节）。

    格式: [START=0x10][CTRL][LINK_ADDR][CS][END=0x16]

    Args:
        ctrl: 控制域字节。
        link_addr: 链路地址（0-255 或 0-65535）。

    Returns:
        5 字节固定长度帧。
    """
    frame = struct.pack(">BB", ctrl, link_addr & 0xFF)
    cs = _compute_checksum(frame)
    return bytes([_FIXED_START]) + frame + bytes([cs, _FRAME_END])


def _parse_frame(raw: bytes) -> tuple[int, int, bytes, int] | None:
    """解析 IEC 101 FT1.2 帧。

    返回 (ctrl, link_addr, asdu_bytes, frame_type) 或 None。
    frame_type: 0=固定帧, 1=可变帧。

    Args:
        raw: 原始接收字节（完整帧，含 start/end 标记）。

    Returns:
        (ctrl, link_addr, asdu, frame_type) 元组，解析失败返回 None。
    """
    if len(raw) < 5:
        return None

    if raw[0] == _FIXED_START and raw[-1] == _FRAME_END:
        if len(raw) == 5:
            ctrl = raw[1]
            link_addr = raw[2]
            cs = raw[3]
            expected_cs = _compute_checksum(raw[1:3])
            if cs != expected_cs:
                return None
            return (ctrl, link_addr, b"", 0)

    if raw[0] == _VARIABLE_START and raw[-1] == _FRAME_END:
        if len(raw) < 6:
            return None
        length = raw[1]  # LENGTH（重复两次）
        if length != raw[2] or raw[3] != _VARIABLE_START:
            return None
        ctrl = raw[4]
        link_addr = raw[5]
        # ASDU 起始于索引 6，结束于倒数第 2 个字节（CS），最后是 END
        asdu_end = len(raw) - 2
        if asdu_end > 6:
            asdu = raw[6:asdu_end]
        else:
            asdu = b""
        cs = raw[-2]
        expected_cs = _compute_checksum(raw[4:asdu_end])
        if cs != expected_cs:
            return None
        return (ctrl, link_addr, asdu, 1)

    return None


class Iec101SerialBackend:
    """IEC 101 串行通信生产级 backend。

    使用 Python 标准库 os/termios 管理串口，
    通过 asyncio.to_thread 将阻塞 I/O 委托到线程池。

    实现 interrogation（C_IC_NA_1 总召唤）流程：
    1. 建立链路连接（RESET_REMOTE_LINK + ACK 握手）
    2. 发送 C_IC_NA_1 激活 ASDU
    3. 接收数据 ASDU（M_ME_NC_1 等类型）
    4. 检测 C_IC_NA_1 终止 ASDU

    Args:
        serial_port: 串口设备路径（如 /dev/ttyUSB0）。
        baudrate: 波特率（默认 9600）。
        parity: 校验位（'E' 为 IEC101 标准，默认 'E'）。
        stop_bits: 停止位（默认 1）。
        data_bits: 数据位（默认 8）。
        link_address: 链路地址（默认 1）。
        common_address: ASDU 公共地址（默认 1）。
        timeout: 读取超时秒数（默认 10.0）。
    """

    def __init__(
        self,
        serial_port: str,
        baudrate: int = 9600,
        parity: str = "E",
        stop_bits: int = 1,
        data_bits: int = 8,
        link_address: int = 1,
        common_address: int = 1,
        timeout: float = _DEFAULT_READ_FRAME_TIMEOUT_S,
    ) -> None:
        self._serial_port = serial_port
        self._baudrate = baudrate
        self._parity = parity.upper()
        self._stop_bits = stop_bits
        self._data_bits = data_bits
        self._link_address = link_address
        self._common_address = common_address
        self._timeout = timeout
        self._fd: int = -1
        self._saved_attrs: list[int | list[bytes | int]] | None = None
        self._fcb: bool = False  # FCB 位状态（用于平衡传输）

    async def connect(self) -> None:
        """打开并配置串口。

        使用 os.open() 以读写模式打开串口设备，
        配置 termios 参数（波特率 9600、偶校验、1 停止位、8 数据位为标准 IEC101 参数）。

        Raises:
            OSError: 串口设备打开失败。
            ValueError: 参数无效。
        """
        if self._fd >= 0:
            return

        if self._parity not in _PARITY_FLAGS:
            raise ValueError(f"无效的校验位: {self._parity!r}")
        if self._stop_bits not in _STOP_BITS_FLAGS:
            raise ValueError(f"无效的停止位: {self._stop_bits}")
        if self._data_bits not in _DATA_BITS_FLAGS:
            raise ValueError(f"无效的数据位: {self._data_bits}")
        if self._baudrate not in _BAUDRATE_MAP:
            raise ValueError(f"不支持的波特率: {self._baudrate}")

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._connect_sync)

    def _connect_sync(self) -> None:
        """同步打开和配置串口（在 executor 线程中运行）。"""
        try:
            self._fd = os.open(
                self._serial_port,
                os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK,
            )
        except OSError as exc:
            raise OSError(
                f"无法打开串口 {self._serial_port!r}: {exc}"
            ) from exc

        try:
            self._saved_attrs = termios.tcgetattr(self._fd)

            attrs = termios.tcgetattr(self._fd)
            attrs[0] = termios.IGNBRK | termios.IGNPAR
            attrs[1] = 0
            cflag = _DATA_BITS_FLAGS[self._data_bits]
            cflag |= termios.CREAD | termios.CLOCAL
            attrs[2] = cflag
            attrs[3] = 0

            baud_const = _BAUDRATE_MAP[self._baudrate]
            attrs[4] = baud_const
            attrs[5] = baud_const

            parity_flag = _PARITY_FLAGS[self._parity]
            attrs[2] |= parity_flag

            stop_flag = _STOP_BITS_FLAGS[self._stop_bits]
            attrs[2] |= stop_flag

            attrs[6][termios.VMIN] = 1
            attrs[6][termios.VTIME] = 10

            termios.tcsetattr(self._fd, termios.TCSANOW, attrs)

            flags = fcntl.fcntl(self._fd, fcntl.F_GETFL)
            fcntl.fcntl(self._fd, fcntl.F_SETFL, flags & ~os.O_NONBLOCK)

        except Exception:
            os.close(self._fd)
            self._fd = -1
            self._saved_attrs = None
            raise

    async def disconnect(self) -> None:
        """关闭串口连接并恢复原始 termios 设置。"""
        if self._fd < 0:
            return
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._disconnect_sync)

    def _disconnect_sync(self) -> None:
        """同步关闭串口（在 executor 线程中运行）。"""
        fd = self._fd
        self._fd = -1
        try:
            if self._saved_attrs is not None:
                try:
                    termios.tcsetattr(fd, termios.TCSANOW, self._saved_attrs)
                except OSError:
                    pass
                self._saved_attrs = None
            try:
                termios.tcdrain(fd)
            except OSError:
                pass
            os.close(fd)
        except OSError:
            pass

    async def __aenter__(self) -> "Iec101SerialBackend":
        await self.connect()
        return self

    async def __aexit__(self, exc_type: object, exc: object, tb: object) -> None:
        await self.disconnect()

    async def read(self, ioa_list: tuple[int, ...]) -> RawIec101ReadResult:
        """执行一次 IEC 101 interrogation（总召唤）读取。

        流程：
        1. 发送 RESET_REMOTE_LINK 初始化链路
        2. 发送 C_IC_NA_1 激活命令
        3. 接收数据 ASDU
        4. 等待 C_IC_NA_1 终止 ASDU

        Args:
            ioa_list: 目标信息对象地址列表。

        Returns:
            原始读取结果，包含 IOA -> (type_tag, value) 映射。
        """
        if self._fd < 0:
            return RawIec101ReadResult(
                ok=False,
                values={},
                error_reason="not_connected",
                exception="串口未连接，请先调用 connect()",
            )

        loop = asyncio.get_running_loop()
        try:
            result = await asyncio.wait_for(
                loop.run_in_executor(None, self._interrogation_sync, ioa_list),
                timeout=self._timeout,
            )
            return result
        except asyncio.TimeoutError:
            return RawIec101ReadResult(
                ok=False,
                values={},
                error_reason="timeout",
                exception=f"总召唤超时（{self._timeout}s）",
            )

    def _interrogation_sync(
        self, ioa_list: tuple[int, ...]
    ) -> RawIec101ReadResult:
        """同步执行 interrogation 流程（在 executor 线程中运行）。"""
        fd = self._fd
        if fd < 0:
            return RawIec101ReadResult(
                ok=False, values={},
                error_reason="not_connected", exception="fd 无效",
            )

        # Phase 1: 链路重置
        reset_frame = _build_fixed_frame(
            _CTRL_RESET_REMOTE_LINK, self._link_address
        )
        try:
            written = os.write(fd, reset_frame)
            if written != len(reset_frame):
                return RawIec101ReadResult(
                    ok=False, values={},
                    error_reason="write_failed",
                    exception="链路重置帧发送失败",
                )
        except OSError as exc:
            return RawIec101ReadResult(
                ok=False, values={},
                error_reason="write_failed",
                exception=f"串口写入失败: {exc}",
            )

        # 等待 ACK
        ack_raw = self._read_frame_sync(fd, timeout=3.0)
        if ack_raw is None:
            # ACK 未收到不是致命错误，继续 interrogation
            pass

        # Phase 2: 发送 C_IC_NA_1 激活 ASDU
        # 构造 interrogation 命令 ASDU
        asdu = bytes([
            _ASDU_C_IC_NA_1,       # type_id
            1,                       # VSQ (1 个信息对象)
            _COT_ACTIVATION,         # COT: 激活
            self._common_address & 0xFF,        # common_addr lo
            (self._common_address >> 8) & 0xFF,  # common_addr hi
            0, 0, 0,                 # IOA = 0 (总召唤)
            0x14,                     # QOI = 20 (总召唤全局)
        ])
        interrogation_frame = self._build_variable_frame(
            ctrl=_CTRL_REQUEST_CLASS1 | (_CTRL_FCB_BIT if self._fcb else 0),
            link_addr=self._link_address,
            asdu=asdu,
        )
        self._fcb = not self._fcb

        try:
            written = os.write(fd, interrogation_frame)
            if written != len(interrogation_frame):
                return RawIec101ReadResult(
                    ok=False, values={},
                    error_reason="write_failed",
                    exception="总召唤激活帧发送失败",
                )
        except OSError as exc:
            return RawIec101ReadResult(
                ok=False, values={},
                error_reason="write_failed",
                exception=f"串口写入失败: {exc}",
            )

        # Phase 3: 接收数据 ASDU
        collected: dict[int, tuple[str, str]] = {}
        terminated = False
        max_frames = 500  # 安全上限

        for _ in range(max_frames):
            raw_frame = self._read_frame_sync(fd, timeout=self._timeout)
            if raw_frame is None:
                break

            parsed = _parse_frame(raw_frame)
            if parsed is None:
                continue

            ctrl, link_addr, asdu_data, frame_type = parsed

            # 忽略链路层 ACK 帧
            if frame_type == 0:
                if ctrl & _CTRL_ACK:
                    continue

            if frame_type == 1 and len(asdu_data) >= 6:
                type_id = asdu_data[_ASDU_TYPE_IDX]
                cot = asdu_data[_ASDU_COT_IDX]

                # 检查 C_IC_NA_1 终止
                if type_id == _ASDU_C_IC_NA_1 and cot in (
                    _COT_DEACTIVATION, 10,  # 10 = termination of interrogation
                ):
                    terminated = True
                    # 发送确认
                    ack = _build_fixed_frame(
                        _CTRL_ACK, link_addr
                    )
                    try:
                        os.write(fd, ack)
                    except OSError:
                        pass
                    break

                # 解析数据 ASDU
                if type_id in (
                    _ASDU_M_ME_NC_1,
                    _ASDU_M_ME_NB_1,
                    _ASDU_M_ME_TE_1,
                    _ASDU_M_SP_NA_1,
                    _ASDU_M_DP_NA_1,
                ) and cot in (
                    _COT_INTERROGATED,
                    _COT_SPONTANEOUS,
                ):
                    parsed_values = self._parse_data_asdu(asdu_data)
                    for ioa, (type_tag, val) in parsed_values.items():
                        if ioa in ioa_list or not ioa_list:
                            collected[ioa] = (type_tag, val)

        if not collected and not terminated:
            return RawIec101ReadResult(
                ok=False,
                values={},
                error_reason="read_failed",
                exception="未接收到总召唤数据",
            )

        return RawIec101ReadResult(
            ok=True,
            values=collected,
            response_timestamp=datetime.now(tz=timezone.utc),
        )

    def _read_frame_sync(
        self, fd: int, timeout: float
    ) -> bytes | None:
        """同步读取一个完整的 IEC 101 帧。

        支持固定长度帧（5 字节）和可变长度帧。

        Args:
            fd: 串口文件描述符。
            timeout: 读取超时秒数。

        Returns:
            完整帧字节，超时或错误返回 None。
        """
        try:
            # 等待首字节
            ready, _, _ = select.select([fd], [], [], timeout)
            if not ready:
                return None

            start_byte = os.read(fd, 1)
            if len(start_byte) < 1:
                return None

            frame = bytearray()
            frame.extend(start_byte)

            if start_byte[0] == _FIXED_START:
                # 固定长度帧：读取剩余 4 字节
                ready2, _, _ = select.select([fd], [], [], timeout)
                if not ready2:
                    return None
                rest = os.read(fd, 4)
                if len(rest) < 4:
                    return None
                frame.extend(rest)
                return bytes(frame)

            elif start_byte[0] == _VARIABLE_START:
                # 可变长度帧：读取长度字节
                ready2, _, _ = select.select([fd], [], [], timeout)
                if not ready2:
                    return None
                length_byte = os.read(fd, 1)
                if len(length_byte) < 1:
                    return None
                frame.extend(length_byte)

                # 重复 length
                ready3, _, _ = select.select([fd], [], [], timeout)
                if not ready3:
                    return None
                length2 = os.read(fd, 1)
                if len(length2) < 1:
                    return None
                frame.extend(length2)

                # 第二个 start
                ready4, _, _ = select.select([fd], [], [], timeout)
                if not ready4:
                    return None
                start2 = os.read(fd, 1)
                if len(start2) < 1:
                    return None
                frame.extend(start2)

                # 剩余字节: ctrl(1) + link_addr(1) + asdu(length) + cs(1) + end(1)
                remaining = 1 + 1 + length_byte[0] + 1 + 1
                ready5, _, _ = select.select([fd], [], [], timeout)
                if not ready5:
                    return None
                rest = os.read(fd, remaining)
                if len(rest) < remaining:
                    return None
                frame.extend(rest)
                return bytes(frame)

            else:
                return None

        except OSError:
            return None

    def _build_variable_frame(
        self, ctrl: int, link_addr: int, asdu: bytes
    ) -> bytes:
        """构造 IEC 101 可变长度帧。

        格式: [START=0x68][L][L][START=0x68][CTRL][LINK_ADDR][ASDU][CS][END=0x16]

        Args:
            ctrl: 控制域字节。
            link_addr: 链路地址。
            asdu: ASDU 数据。

        Returns:
            完整可变长度帧字节。
        """
        length = len(asdu) & 0xFF
        pre_cs = struct.pack(">BB", ctrl, link_addr & 0xFF) + asdu
        cs = _compute_checksum(pre_cs)
        return (
            bytes([_VARIABLE_START, length, length, _VARIABLE_START])
            + pre_cs
            + bytes([cs, _FRAME_END])
        )

    def _parse_data_asdu(
        self, asdu: bytes
    ) -> dict[int, tuple[str, str]]:
        """解析数据 ASDU 并返回 IOA -> (type_tag, value_str) 映射。

        ASDU 最小格式:
        [type_id(1)][vsq(1)][cot(1)][common_addr(2)][IOA(3)][value(N)]

        Args:
            asdu: ASDU 字节（不含链路层头部和 CS/END）。

        Returns:
            IOA 到 (类型标签, 值字符串) 的映射。
        """
        if len(asdu) < 6:
            return {}

        type_id = asdu[_ASDU_TYPE_IDX]
        vsq = asdu[_ASDU_VSQ_IDX]
        num_objects = vsq & 0x7F  # 低 7 位
        if num_objects == 0:
            num_objects = 1

        # common_addr 在索引 3-4
        # IOA 从索引 5 开始，每个 3 字节
        result: dict[int, tuple[str, str]] = {}

        type_tags: dict[int, str] = {
            _ASDU_M_SP_NA_1: "M_SP_NA_1",
            _ASDU_M_DP_NA_1: "M_DP_NA_1",
            _ASDU_M_ME_NB_1: "M_ME_NB_1",
            _ASDU_M_ME_NC_1: "M_ME_NC_1",
            _ASDU_M_ME_TE_1: "M_ME_TE_1",
        }

        offset = _ASDU_IOA_START  # = 5
        for obj_idx in range(min(num_objects, 200)):
            if offset + 3 > len(asdu):
                break

            ioa = (
                asdu[offset]
                | (asdu[offset + 1] << 8)
                | (asdu[offset + 2] << 16)
            )
            offset += 3

            # 按类型解析值
            if type_id == _ASDU_M_ME_NC_1:
                # 短浮点: 4 字节 IEEE 754 float
                if offset + 4 <= len(asdu):
                    try:
                        raw_val = asdu[offset : offset + 4]
                        val_float = struct.unpack("<f", raw_val)[0]
                        val_str = f"{val_float:.3f}"
                    except struct.error:
                        val_str = "0.000"
                    offset += 4
                else:
                    val_str = "0"
            elif type_id == _ASDU_M_ME_NB_1:
                # 归一化测量值: 2 字节
                if offset + 2 <= len(asdu):
                    raw_val = struct.unpack("<h", asdu[offset : offset + 2])[0]
                    val_str = str(raw_val)
                    offset += 2
                else:
                    val_str = "0"
            elif type_id == _ASDU_M_ME_TE_1:
                # 带时标测量值: 4 字节 float + 3 字节时标（简化解析）
                if offset + 4 <= len(asdu):
                    try:
                        raw_val = asdu[offset : offset + 4]
                        val_float = struct.unpack("<f", raw_val)[0]
                        val_str = f"{val_float:.3f}"
                    except struct.error:
                        val_str = "0.000"
                    offset += 7  # 4 (float) + 3 (CP24Time2a)
                else:
                    val_str = "0"
            elif type_id == _ASDU_M_SP_NA_1:
                # 单点信息: 1 字节（含 SIQ 质量位）
                if offset < len(asdu):
                    siq = asdu[offset]
                    val_str = "1" if (siq & 0x01) else "0"
                    offset += 1
                else:
                    val_str = "0"
            elif type_id == _ASDU_M_DP_NA_1:
                # 双点信息: 1 字节
                if offset < len(asdu):
                    diq = asdu[offset]
                    val_str = str(diq & 0x03)  # 00=中间, 01=分, 10=合
                    offset += 1
                else:
                    val_str = "0"
            else:
                # 未知类型，跳过
                val_str = "0"
                break

            type_tag = type_tags.get(type_id, f"TYPE_{type_id}")
            result[ioa] = (type_tag, val_str)

        return result
