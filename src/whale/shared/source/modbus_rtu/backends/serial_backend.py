"""Modbus RTU 串行通信 backend。

基于 Python 标准库（os、termios、fcntl、struct）
实现 Modbus RTU 协议的串行通信客户端。
不依赖 pyserial 或任何第三方串口库。

职责边界：
- 实现 Modbus RTU 帧构造（地址、功能码、数据、CRC16）和解析；
- 实现串口打开、参数配置（波特率、校验位、停止位、数据位）、关闭和资源清理；
- 实现 holding register 读取（FC03）；
- 不负责业务数据映射或采集策略编排——由 ingest adapter 处理；
- 不负责持久化或缓存——由上层 state cache 处理。

资源生命周期：
- connect() / disconnect() 管理串口文件描述符；
- 使用 os.open / os.close 管理 fd；
- 超时通过 asyncio.to_thread + select/poll 实现；
- 异常路径必须确保 fd 关闭（finally 块）。

序列参数：
- serial_port: 串口设备路径（如 /dev/ttyS0、/dev/ttyUSB0）；
- baudrate: 波特率（默认 9600）；
- parity: 校验位（'N'=无, 'E'=偶, 'O'=奇，默认 'N'）；
- stop_bits: 停止位（1 或 2，默认 1）；
- data_bits: 数据位（7 或 8，默认 8）；
- unit_id: Modbus 从站地址（默认 1）。

Write 状态：NOT_IMPLEMENTED。当前仅支持 FC03 读取。
"""
from __future__ import annotations

import asyncio
import fcntl
import os
import struct
import termios
from datetime import datetime, timezone

from whale.shared.source.modbus_rtu.backends.base import (
    ModbusRtuPreparedReadPlan,
    RawModbusRtuReadResult,
)

# 串口连接默认超时（秒）
_DEFAULT_SERIAL_TIMEOUT_S: float = 3.0
# 读取单帧的最大等待时间（含设备响应和线路延迟）
_DEFAULT_READ_FRAME_TIMEOUT_S: float = 5.0
# Modbus RTU 帧间最小间隔（3.5 字符时间，以毫秒计）
# 在 9600 baud 下约 3.6 ms，取保守值 5 ms
_INTER_FRAME_DELAY_S: float = 0.005
# Modbus 功能码 FC03（read holding registers）
_FC_READ_HOLDING_REGISTERS: int = 0x03
# Modbus RTU 异常响应功能码偏移
_EXCEPTION_OFFSET: int = 0x80

# 校验位常量 -> termios 标志
_PARITY_FLAGS: dict[str, int] = {
    "N": 0,  # no parity (IGNPAR 已设默认)
    "E": termios.PARENB,  # even parity (enable parity, no odd)
    "O": termios.PARENB | termios.PARODD,  # odd parity
}

# 停止位常量 -> termios 标志
_STOP_BITS_FLAGS: dict[int, int] = {
    1: 0,  # 1 stop bit (default)
    2: termios.CSTOPB,  # 2 stop bits
}

# 数据位常量 -> termios 标志
_DATA_BITS_FLAGS: dict[int, int] = {
    7: termios.CS7,
    8: termios.CS8,
}

# 波特率常量 -> termios 速度常量
_BAUDRATE_MAP: dict[int, int] = {
    0: termios.B0,
    50: termios.B50,
    75: termios.B75,
    110: termios.B110,
    134: termios.B134,
    150: termios.B150,
    200: termios.B200,
    300: termios.B300,
    600: termios.B600,
    1200: termios.B1200,
    1800: termios.B1800,
    2400: termios.B2400,
    4800: termios.B4800,
    9600: termios.B9600,
    19200: termios.B19200,
    38400: termios.B38400,
    57600: termios.B57600,
    115200: termios.B115200,
    230400: termios.B230400,
}

def _build_crc_table() -> list[int]:
    """构建 Modbus CRC16 查找表（256 项）。

    仅在模块加载时调用一次。
    """
    table: list[int] = []
    for i in range(256):
        crc = i
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
        table.append(crc)
    return table


# Modbus RTU CRC16 查找表（预计算，减少运行时开销）
_CRC16_TABLE: tuple[int, ...] = tuple(_build_crc_table())


def _compute_crc16(data: bytes) -> int:
    """计算 Modbus RTU CRC16 校验值。

    使用预计算查找表，返回 16 位无符号整数的 CRC 值。

    Args:
        data: 需要计算 CRC 的字节序列（不含 CRC 字段）。

    Returns:
        16 位 CRC 校验结果（低字节在前，符合 Modbus RTU 帧格式）。
    """
    crc = 0xFFFF
    for byte in data:
        idx = (crc ^ byte) & 0xFF
        crc = ((crc >> 8) ^ _CRC16_TABLE[idx]) & 0xFFFF
    return crc


class ModbusRtuSerialBackend:
    """Modbus RTU 串行通信生产级 backend。

    使用 Python 标准库 os/termios 管理串口，
    通过 asyncio.to_thread 将阻塞 I/O 委托到线程池。

    Args:
        serial_port: 串口设备路径（如 /dev/ttyUSB0）。
        baudrate: 波特率（默认 9600）。
        parity: 校验位 ('N'/'E'/'O'，默认 'N')。
        stop_bits: 停止位（1 或 2，默认 1）。
        data_bits: 数据位（7 或 8，默认 8）。
        unit_id: Modbus 从站地址（默认 1）。
        timeout: 读取帧超时秒数（默认 5.0）。

    Raises:
        ValueError: 串口参数无效。
        OSError: 串口设备不可访问。
    """

    def __init__(
        self,
        serial_port: str,
        baudrate: int = 9600,
        parity: str = "N",
        stop_bits: int = 1,
        data_bits: int = 8,
        unit_id: int = 1,
        timeout: float = _DEFAULT_READ_FRAME_TIMEOUT_S,
    ) -> None:
        self._serial_port = serial_port
        self._baudrate = baudrate
        self._parity = parity.upper()
        self._stop_bits = stop_bits
        self._data_bits = data_bits
        self._unit_id = unit_id
        self._timeout = timeout
        self._fd: int = -1
        self._saved_attrs: list[int | list[bytes | int]] | None = None

    async def connect(self) -> None:
        """打开并配置串口。

        使用 os.open() 以读写模式打开串口设备（非阻塞模式，
        避免 open 时等待 DCD），然后配置 termios 参数
        （波特率、校验位、停止位、数据位），
        通过 fcntl 设置为阻塞模式以简化后续读取。

        Raises:
            OSError: 串口设备打开失败。
            ValueError: 参数无效。
        """
        if self._fd >= 0:
            return  # 已连接

        # 校验参数
        if self._parity not in _PARITY_FLAGS:
            raise ValueError(
                f"无效的校验位参数: {self._parity!r}，"
                f"支持的值: {sorted(_PARITY_FLAGS.keys())}"
            )
        if self._stop_bits not in _STOP_BITS_FLAGS:
            raise ValueError(
                f"无效的停止位参数: {self._stop_bits}，"
                f"支持的值: {sorted(_STOP_BITS_FLAGS.keys())}"
            )
        if self._data_bits not in _DATA_BITS_FLAGS:
            raise ValueError(
                f"无效的数据位参数: {self._data_bits}，"
                f"支持的值: {sorted(_DATA_BITS_FLAGS.keys())}"
            )
        if self._baudrate not in _BAUDRATE_MAP:
            raise ValueError(
                f"不支持的波特率: {self._baudrate}，"
                f"支持的值: {sorted(_BAUDRATE_MAP.keys())}"
            )

        # 在 executor 中执行阻塞的串口操作
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._connect_sync)

    def _connect_sync(self) -> None:
        """同步执行串口打开和配置（在 executor 线程中运行）。"""
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
            # 保存原始属性以便 disconnect 时恢复
            self._saved_attrs = termios.tcgetattr(self._fd)

            # 配置 termios
            attrs = termios.tcgetattr(self._fd)

            # 输入标志：忽略 break、忽略帧错误
            attrs[0] = termios.IGNBRK | termios.IGNPAR

            # 输出标志：无处理
            attrs[1] = 0

            # 控制标志：设置数据位，清除硬件流控
            cflag = _DATA_BITS_FLAGS[self._data_bits]
            cflag |= termios.CREAD | termios.CLOCAL
            attrs[2] = cflag

            # 本地标志：无回显、无规范模式
            attrs[3] = 0

            # ISPEED/OSPEED
            baud_const = _BAUDRATE_MAP[self._baudrate]
            attrs[4] = baud_const  # ISPEED
            attrs[5] = baud_const  # OSPEED

            # 设置校验位
            parity_flag = _PARITY_FLAGS[self._parity]
            attrs[2] |= parity_flag

            # 设置停止位
            stop_flag = _STOP_BITS_FLAGS[self._stop_bits]
            attrs[2] |= stop_flag

            # 最小读取字符数和超时（十分之一秒）
            # VMIN=1, VTIME=10 → 等待至少 1 字节或 1 秒超时
            attrs[6][termios.VMIN] = 1
            attrs[6][termios.VTIME] = 10

            termios.tcsetattr(self._fd, termios.TCSANOW, attrs)

            # 清除阻塞模式（已通过 VMIN/VTIME 控制超时）
            flags = fcntl.fcntl(self._fd, fcntl.F_GETFL)
            fcntl.fcntl(self._fd, fcntl.F_SETFL, flags & ~os.O_NONBLOCK)

        except Exception:
            # 配置失败时关闭 fd
            os.close(self._fd)
            self._fd = -1
            self._saved_attrs = None
            raise

    async def disconnect(self) -> None:
        """关闭串口连接并恢复原始 termios 设置。

        如果在 connect 前调用，无副作用。
        无论正常关闭还是异常路径，都确保 fd 被释放。
        """
        if self._fd < 0:
            return

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._disconnect_sync)

    def _disconnect_sync(self) -> None:
        """同步执行串口关闭（在 executor 线程中运行）。"""
        fd = self._fd
        self._fd = -1
        try:
            # 恢复原始 termios 设置
            if self._saved_attrs is not None:
                try:
                    termios.tcsetattr(fd, termios.TCSANOW, self._saved_attrs)
                except OSError:
                    pass  # fd 可能已失效
                self._saved_attrs = None
            # 排空输出缓冲区
            try:
                termios.tcdrain(fd)
            except OSError:
                pass
            os.close(fd)
        except OSError:
            pass  # 忽略关闭时的异常

    async def __aenter__(self) -> "ModbusRtuSerialBackend":
        await self.connect()
        return self

    async def __aexit__(self, exc_type: object, exc: object, tb: object) -> None:
        await self.disconnect()

    def prepare_read(self, reg_addrs: tuple[int, ...]) -> ModbusRtuPreparedReadPlan:
        """为给定寄存器地址列表准备可复用的读取计划。

        Args:
            reg_addrs: 目标 holding register 地址元组（0-based）。

        Returns:
            预准备读取计划。
        """
        return ModbusRtuPreparedReadPlan(
            reg_addrs=reg_addrs,
            unit_id=self._unit_id,
        )

    async def read_prepared(
        self, plan: ModbusRtuPreparedReadPlan
    ) -> RawModbusRtuReadResult:
        """按预准备计划执行一次 Modbus RTU 批量读取（FC03）。

        构造 Modbus RTU 帧，通过串口发送，
        等待并解析设备响应，检查 CRC 和异常码。

        Args:
            plan: 由 prepare_read 创建的读取计划。

        Returns:
            原始读取结果，包含各寄存器值或错误信息。
        """
        if self._fd < 0:
            return RawModbusRtuReadResult(
                ok=False,
                values=(),
                error_reason="not_connected",
                exception="串口未连接，请先调用 connect()",
            )

        start_addr = plan.reg_addrs[0] if plan.reg_addrs else 0
        reg_count = len(plan.reg_addrs)
        if reg_count < 1 or reg_count > 125:
            return RawModbusRtuReadResult(
                ok=False,
                values=(),
                error_reason="invalid_request",
                exception=f"寄存器数量无效: {reg_count}（1-125 有效）",
            )

        # 构造 Modbus RTU 请求帧
        request_frame = self._build_read_request(
            unit_id=plan.unit_id,
            start_addr=start_addr,
            reg_count=reg_count,
        )

        loop = asyncio.get_running_loop()
        try:
            response_bytes = await asyncio.wait_for(
                loop.run_in_executor(
                    None, self._send_and_receive, request_frame
                ),
                timeout=self._timeout,
            )
        except asyncio.TimeoutError:
            return RawModbusRtuReadResult(
                ok=False,
                values=(),
                error_reason="timeout",
                exception=f"读取超时（{self._timeout}s）",
            )

        if response_bytes is None:
            return RawModbusRtuReadResult(
                ok=False,
                values=(),
                error_reason="no_response",
                exception="设备无响应",
            )

        return self._parse_read_response(
            response_bytes=response_bytes,
            expected_reg_count=reg_count,
        )

    def _build_read_request(
        self,
        unit_id: int,
        start_addr: int,
        reg_count: int,
    ) -> bytes:
        """构造 Modbus RTU FC03 读取请求帧。

        RTU 帧格式: [unit_id][func_code][start_addr_hi][start_addr_lo]
        [reg_count_hi][reg_count_lo][crc_lo][crc_hi]

        Args:
            unit_id: 从站地址（1-247）。
            start_addr: 起始寄存器地址。
            reg_count: 读取寄存器数量。

        Returns:
            完整的 RTU 请求帧字节。
        """
        pdu = struct.pack(
            ">BHH",
            _FC_READ_HOLDING_REGISTERS,
            start_addr & 0xFFFF,
            reg_count & 0xFFFF,
        )
        frame_without_crc = struct.pack(">B", unit_id) + pdu
        crc = _compute_crc16(frame_without_crc)
        return frame_without_crc + struct.pack("<H", crc)

    def _send_and_receive(self, request_frame: bytes) -> bytes | None:
        """通过串口发送请求帧并读取响应。

        在 executor 线程中同步执行。
        发送后等待足够的字节以接收完整的响应帧。

        Args:
            request_frame: 待发送的 RTU 请求帧。

        Returns:
            接收到的原始响应字节，或 None 表示无响应。
        """
        fd = self._fd
        if fd < 0:
            return None

        try:
            # 发送请求帧
            written = os.write(fd, request_frame)
            if written != len(request_frame):
                return None

            # 等待帧间间隔
            # 使用 select 实现阻塞式读取，支持超时
            import select

            # 等待设备响应（首字节）
            ready, _, _ = select.select(
                [fd], [], [], _DEFAULT_SERIAL_TIMEOUT_S
            )
            if not ready:
                return None

            # 读取响应帧
            response = bytearray()
            # 最小响应帧: unit_id(1) + func_code(1) + byte_count(1) + data(2*regs) + crc(2)
            # 先读取首部，再按 byte_count 读取剩余
            header = os.read(fd, 4)  # unit_id + func_code + byte_count + 至少1字节
            if len(header) < 4:
                return None
            response.extend(header)

            _unit_id = header[0]  # 接收的从站地址（用于调试）
            func_code = header[1]
            byte_count = header[2] if func_code < _EXCEPTION_OFFSET else 0

            if byte_count > 0:
                remaining = byte_count + 2 - 1  # -1 因为 header 已有 1 字节数据
                if remaining > 0:
                    # 等待剩余数据
                    ready2, _, _ = select.select(
                        [fd], [], [], _DEFAULT_SERIAL_TIMEOUT_S
                    )
                    if not ready2 and remaining > 0:
                        return bytes(response) if len(response) > 3 else None
                    more = os.read(fd, remaining)
                    response.extend(more)
            else:
                # 异常响应: unit_id(1) + error_code(1) + exception_code(1) + crc(2)
                # header 已有 4 字节（含 crc 高字节刚好），再读 1 字节 crc 低字节
                tail = os.read(fd, 1)
                response.extend(tail)

            return bytes(response)

        except OSError:
            return None

    def _parse_read_response(
        self,
        response_bytes: bytes,
        expected_reg_count: int,
    ) -> RawModbusRtuReadResult:
        """解析 Modbus RTU 读取响应帧。

        验证 CRC、检查异常响应码，提取寄存器数据。

        Args:
            response_bytes: 原始响应字节（含 CRC）。
            expected_reg_count: 期望的寄存器数量。

        Returns:
            解析后的读取结果。
        """
        if len(response_bytes) < 5:
            return RawModbusRtuReadResult(
                ok=False,
                values=(),
                error_reason="protocol_error",
                exception=f"响应帧太短: {len(response_bytes)} 字节",
            )

        # 验证 CRC
        frame_data = response_bytes[:-2]
        received_crc = struct.unpack("<H", response_bytes[-2:])[0]
        expected_crc = _compute_crc16(frame_data)
        if received_crc != expected_crc:
            return RawModbusRtuReadResult(
                ok=False,
                values=(),
                error_reason="crc_error",
                exception=f"CRC 校验失败: 收到 0x{received_crc:04X}，"
                f"期望 0x{expected_crc:04X}",
            )

        func_code = response_bytes[1]

        # 检查异常响应
        if func_code >= _EXCEPTION_OFFSET:
            exception_code = response_bytes[2] if len(response_bytes) > 2 else 0
            exception_msgs = {
                1: "非法功能码",
                2: "非法数据地址",
                3: "非法数据值",
                4: "从站设备故障",
                5: "确认（ACK）",
                6: "从站设备忙",
            }
            msg = exception_msgs.get(exception_code, f"异常码 0x{exception_code:02X}")
            return RawModbusRtuReadResult(
                ok=False,
                values=(),
                error_reason="device_exception",
                exception=f"设备返回异常: {msg}",
            )

        # 正常响应: unit_id(1) + func_code(1) + byte_count(1) + data(N*2) + crc(2)
        byte_count = response_bytes[2]
        expected_data_bytes = expected_reg_count * 2
        if byte_count != expected_data_bytes:
            return RawModbusRtuReadResult(
                ok=False,
                values=(),
                error_reason="protocol_error",
                exception=f"字节计数不匹配: 收到 {byte_count}，"
                f"期望 {expected_data_bytes}（{expected_reg_count} 个寄存器）",
            )

        # 提取寄存器值（每 2 字节一个 uint16，大端序）
        values: list[int] = []
        data_start = 3
        data_end = data_start + byte_count
        if len(response_bytes) < data_end + 2:  # +2 for CRC
            return RawModbusRtuReadResult(
                ok=False,
                values=(),
                error_reason="protocol_error",
                exception="响应数据不完整",
            )

        for i in range(data_start, data_end, 2):
            val = struct.unpack(">H", response_bytes[i : i + 2])[0]
            values.append(val)

        return RawModbusRtuReadResult(
            ok=True,
            values=tuple(values),
            response_timestamp=datetime.now(tz=timezone.utc),
        )
