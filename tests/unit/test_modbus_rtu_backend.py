"""Modbus RTU backend 单元测试。

被验证对象：``whale.shared.source.modbus_rtu.backends.serial_backend.ModbusRtuSerialBackend``。
测试阶段：开发期验证 (unit/mock) — 使用 mock serial fd 和 termios 模拟串口通信。
不能证明：真实串口设备通信、电气特性、线路噪声。

Mock 策略：
- mock os.open 返回虚拟 fd；
- mock termios.tcgetattr/tcsetattr 无操作；
- mock os.read/os.write 模拟 Modbus RTU 帧交换；
- mock select.select 模拟数据可用性。
"""
from __future__ import annotations

import struct
from unittest.mock import patch

import pytest

from whale.shared.source.modbus_rtu.backends.base import (
    ModbusRtuPreparedReadPlan,
)
from whale.shared.source.modbus_rtu.backends.serial_backend import (
    ModbusRtuSerialBackend,
    _compute_crc16,
)


def _make_modbus_rtu_read_response(
    unit_id: int, start_addr: int, values: list[int]
) -> bytes:
    """构造一个合法的 Modbus RTU FC03 读取响应帧。

    构造响应帧数据部分（不含 CRC），
    使用 _compute_crc16 计算并添加正确的 CRC。
    """
    byte_count = len(values) * 2
    header = struct.pack(">BBB", unit_id, 0x03, byte_count)
    data = b"".join(struct.pack(">H", v) for v in values)
    frame_without_crc = header + data
    crc = _compute_crc16(frame_without_crc)
    return frame_without_crc + struct.pack("<H", crc)


def _make_modbus_rtu_exception_response(
    unit_id: int, exception_code: int
) -> bytes:
    """构造 Modbus RTU 异常响应帧。

    使用 _compute_crc16 计算并添加正确的 CRC。
    """
    frame_without_crc = struct.pack(">BBB", unit_id, 0x83, exception_code)
    crc = _compute_crc16(frame_without_crc)
    return frame_without_crc + struct.pack("<H", crc)


class TestModbusRtuCrc16:
    """CRC16 校验计算单元测试。"""

    def test_crc16_known_values(self) -> None:
        """验证已知 Modbus RTU 帧的 CRC16 计算结果。"""
        # FC03 读取请求帧: [0x01][0x03][0x00][0x01][0x00][0x01]
        # 标准 Modbus CRC-16 (polynomial 0xA001 reversed, init 0xFFFF)
        frame = bytes([0x01, 0x03, 0x00, 0x01, 0x00, 0x01])
        crc = _compute_crc16(frame)
        # 参考 bit-by-bit 实现验证: CRC=0xCAD5
        # RTU 帧中存储为 LE: [0xD5, 0xCA]
        assert crc == 0xCAD5

    def test_crc16_empty_returns_ffff(self) -> None:
        """空数据的 CRC16 初始值为 0xFFFF。"""
        crc = _compute_crc16(b"")
        assert crc == 0xFFFF


class TestModbusRtuSerialBackendParams:
    """Modbus RTU backend 参数校验测试。"""

    def test_valid_params_accepted(self) -> None:
        """有效参数应被接受。"""
        backend = ModbusRtuSerialBackend(
            serial_port="/dev/ttyUSB0",
            baudrate=9600,
            parity="N",
            stop_bits=1,
            data_bits=8,
            unit_id=1,
        )
        assert backend._baudrate == 9600
        assert backend._parity == "N"

    @pytest.mark.asyncio
    async def test_invalid_parity_raises(self) -> None:
        """无效校验位应在 connect 时抛出 ValueError。"""
        backend = ModbusRtuSerialBackend(
            serial_port="/dev/ttyUSB0", parity="X"
        )
        # 参数校验在 connect() 中，在 os.open 之前
        with pytest.raises(ValueError, match="校验位"):
            await backend.connect()

    @pytest.mark.asyncio
    async def test_invalid_baudrate_raises(self) -> None:
        """不支持的波特率应抛出 ValueError。"""
        backend = ModbusRtuSerialBackend(
            serial_port="/dev/ttyUSB0", baudrate=99999
        )
        with pytest.raises(ValueError, match="波特率"):
            await backend.connect()


class TestModbusRtuSerialBackendPrepareRead:
    """prepare_read 方法单元测试。"""

    def test_prepare_read_returns_plan(self) -> None:
        """prepare_read 应返回包含地址和 unit_id 的计划。"""
        backend = ModbusRtuSerialBackend(
            serial_port="/dev/ttyUSB0", unit_id=3
        )
        plan = backend.prepare_read((100, 101, 102))
        assert plan.reg_addrs == (100, 101, 102)
        assert plan.unit_id == 3


class TestModbusRtuSerialBackendReadPrepared:
    """read_prepared 方法单元测试（mock 串口 I/O）。"""

    @pytest.mark.asyncio
    async def test_read_prepared_success(self) -> None:
        """模拟正常 Modbus RTU 读取流程，验证返回值和时间戳。

        使用 side_effect 模拟 os.read 的分段返回：
        第一次返回响应头 4 字节，第二次返回剩余数据。
        """
        response = _make_modbus_rtu_read_response(1, 100, [0x1234, 0x5678])
        # 响应帧: [unit_id][0x03][byte_count=4][data0_hi][data0_lo]
        #          [data1_hi][data1_lo][crc_lo][crc_hi] = 9 字节
        header_part = response[:4]  # 前 4 字节
        rest_part = response[4:]    # 剩余 5 字节

        backend = ModbusRtuSerialBackend(
            serial_port="/dev/ttyUSB0", unit_id=1
        )
        backend._fd = 10  # mock fd
        plan = ModbusRtuPreparedReadPlan(reg_addrs=(100, 101), unit_id=1)

        with patch("os.write", return_value=8):
            with patch("select.select", return_value=([10], [], [])):
                with patch("os.read", side_effect=[header_part, rest_part]):
                    result = await backend.read_prepared(plan)

        assert result.ok is True
        assert len(result.values) == 2
        assert result.values[0] == 0x1234
        assert result.values[1] == 0x5678
        assert result.response_timestamp is not None

    @pytest.mark.asyncio
    async def test_read_prepared_not_connected(self) -> None:
        """未连接时 read_prepared 应返回错误结果。"""
        backend = ModbusRtuSerialBackend(serial_port="/dev/ttyUSB0")
        plan = ModbusRtuPreparedReadPlan(reg_addrs=(100,), unit_id=1)
        result = await backend.read_prepared(plan)
        assert result.ok is False
        assert result.error_reason == "not_connected"

    @pytest.mark.asyncio
    async def test_read_prepared_timeout(self) -> None:
        """读取超时应返回 no_response 或 timeout 错误。

        当 select 超时时，_send_and_receive 返回 None，
        read_prepared 将其转换为 no_response 错误。
        """
        backend = ModbusRtuSerialBackend(
            serial_port="/dev/ttyUSB0", unit_id=1, timeout=0.1
        )
        backend._fd = 10
        plan = ModbusRtuPreparedReadPlan(reg_addrs=(100,), unit_id=1)

        with patch("os.write", return_value=8):
            with patch("select.select", return_value=([], [], [])):
                result = await backend.read_prepared(plan)

        assert result.ok is False
        assert result.error_reason == "no_response"

    @pytest.mark.asyncio
    async def test_read_prepared_exception_response(self) -> None:
        """设备返回异常响应时应报告 device_exception。

        异常响应格式: [unit_id][0x83][exception_code][crc_lo][crc_hi] = 5 字节
        使用 side_effect 模拟分帧读取。
        """
        response = _make_modbus_rtu_exception_response(1, 2)
        header_part = response[:4]   # unit_id + error_func + exc_code + first crc byte
        tail_part = response[4:]     # last crc byte

        backend = ModbusRtuSerialBackend(
            serial_port="/dev/ttyUSB0", unit_id=1
        )
        backend._fd = 10
        plan = ModbusRtuPreparedReadPlan(reg_addrs=(100,), unit_id=1)

        with patch("os.write", return_value=8):
            with patch("select.select", return_value=([10], [], [])):
                with patch("os.read", side_effect=[header_part, tail_part]):
                    result = await backend.read_prepared(plan)

        assert result.ok is False
        assert result.error_reason == "device_exception"

    @pytest.mark.asyncio
    async def test_read_prepared_crc_error(self) -> None:
        """CRC 校验失败应报告 crc_error。"""
        response = _make_modbus_rtu_read_response(1, 100, [0x1234])
        # 篡改 CRC 最后一字节
        corrupted = bytearray(response)
        corrupted[-1] ^= 0xFF
        corrupted_bytes = bytes(corrupted)
        header_part = corrupted_bytes[:4]
        rest_part = corrupted_bytes[4:]

        backend = ModbusRtuSerialBackend(
            serial_port="/dev/ttyUSB0", unit_id=1
        )
        backend._fd = 10
        plan = ModbusRtuPreparedReadPlan(reg_addrs=(100,), unit_id=1)

        with patch("os.write", return_value=8):
            with patch("select.select", return_value=([10], [], [])):
                with patch("os.read", side_effect=[header_part, rest_part]):
                    result = await backend.read_prepared(plan)

        assert result.ok is False
        assert result.error_reason == "crc_error"
