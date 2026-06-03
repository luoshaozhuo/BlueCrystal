"""IEC 101 backend 单元测试。

被验证对象：``whale.shared.source.iec101.backends.serial_backend.Iec101SerialBackend``。
证据等级：L1 unit/mock — 使用 mock serial fd 和 termios 模拟串口通信。
不能证明：真实串口设备通信、IEC 101 设备互操作性。

Mock 策略：
- mock os.open 返回虚拟 fd；
- mock termios.tcgetattr/tcsetattr 无操作；
- mock os.write 模拟帧发送；
- mock os.read 模拟帧接收；
- mock select.select 模拟数据可用性。
"""
from __future__ import annotations

import struct
from unittest.mock import patch

import pytest

from whale.shared.source.iec101.backends.serial_backend import (
    Iec101SerialBackend,
    _build_fixed_frame,
    _compute_checksum,
    _parse_frame,
)


class TestIec101Checksum:
    """IEC 101 校验和计算测试。"""

    def test_checksum_simple(self) -> None:
        """简单字节序列的校验和计算。"""
        data = bytes([0x40, 0x01])  # CTRL=0x40, LINK_ADDR=0x01
        cs = _compute_checksum(data)
        assert cs == 0x41

    def test_checksum_empty(self) -> None:
        """空序列校验和为 0。"""
        assert _compute_checksum(b"") == 0


class TestIec101FixedFrame:
    """IEC 101 固定长度帧构造测试。"""

    def test_build_reset_frame(self) -> None:
        """RESET_REMOTE_LINK 帧应正确构造。"""
        frame = _build_fixed_frame(0x00, 0x01)  # RESET_REMOTE_LINK + addr 1
        assert frame[0] == 0x10  # START
        assert frame[1] == 0x00  # CTRL
        assert frame[2] == 0x01  # LINK_ADDR
        assert frame[4] == 0x16  # END

    def test_build_and_parse_roundtrip(self) -> None:
        """构造的固定帧应能被解析。"""
        frame = _build_fixed_frame(0x40, 0x03)
        parsed = _parse_frame(frame)
        assert parsed is not None
        ctrl, link_addr, asdu, frame_type = parsed
        assert ctrl == 0x40
        assert link_addr == 0x03
        assert asdu == b""
        assert frame_type == 0


class TestIec101FrameParse:
    """IEC 101 帧解析测试。"""

    def test_parse_too_short_frame(self) -> None:
        """过短帧返回 None。"""
        assert _parse_frame(bytes([0x10])) is None
        assert _parse_frame(b"") is None

    def test_parse_fixed_frame_bad_checksum(self) -> None:
        """校验和错误的固定帧返回 None。"""
        # 构造固定帧后篡改 checksum
        frame = bytearray(_build_fixed_frame(0x40, 0x01))
        frame[3] ^= 0xFF  # 翻转 checksum
        assert _parse_frame(bytes(frame)) is None

    def test_parse_variable_frame(self) -> None:
        """可变长度帧应正确解析。"""
        # 构造简单的可变长度帧
        asdu_data = bytes([100, 1, 6, 1, 0, 0, 0, 0, 0x14])
        pre_cs = struct.pack(">BB", 0x53, 0x01) + asdu_data
        cs = _compute_checksum(pre_cs)
        length = len(asdu_data)
        frame = (
            bytes([0x68, length, length, 0x68])
            + pre_cs
            + bytes([cs, 0x16])
        )
        parsed = _parse_frame(frame)
        assert parsed is not None
        ctrl, link_addr, asdu, frame_type = parsed
        assert ctrl == 0x53
        assert link_addr == 0x01
        assert len(asdu) == length
        assert frame_type == 1


class TestIec101SerialBackendParams:
    """IEC 101 backend 参数校验测试。"""

    def test_valid_params_accepted(self) -> None:
        """标准 IEC 101 参数应被接受。"""
        backend = Iec101SerialBackend(
            serial_port="/dev/ttyUSB0",
            baudrate=9600,
            parity="E",
            stop_bits=1,
            data_bits=8,
            link_address=1,
            common_address=1,
        )
        assert backend._baudrate == 9600
        assert backend._parity == "E"

    @pytest.mark.asyncio
    async def test_invalid_baudrate_raises(self) -> None:
        """不支持的波特率应抛出 ValueError。"""
        backend = Iec101SerialBackend(
            serial_port="/dev/ttyUSB0", baudrate=99999
        )
        # 参数校验在 connect() 中，在 os.open 之前
        with pytest.raises(ValueError, match="波特率"):
            await backend.connect()


class TestIec101SerialBackendRead:
    """IEC 101 read 方法测试（mock 串口 I/O）。"""

    @pytest.mark.asyncio
    async def test_read_not_connected(self) -> None:
        """未连接时 read 应返回错误结果。"""
        backend = Iec101SerialBackend(serial_port="/dev/ttyUSB0")
        result = await backend.read((100,))
        assert result.ok is False
        assert result.error_reason == "not_connected"

    @pytest.mark.asyncio
    async def test_read_no_response(self) -> None:
        """设备无响应时应返回超时或读取失败。"""
        backend = Iec101SerialBackend(
            serial_port="/dev/ttyUSB0", timeout=0.1
        )
        backend._fd = 10

        with patch("os.write", return_value=5):
            with patch("select.select", return_value=([], [], [])):
                result = await backend.read((100,))

        assert result.ok is False


class TestIec101DataAsduParse:
    """IEC 101 数据 ASDU 解析测试。"""

    def test_parse_m_me_nc_1_asdu(self) -> None:
        """M_ME_NC_1（短浮点测量值）ASDU 应正确解析。"""
        backend = Iec101SerialBackend(serial_port="/dev/ttyUSB0")
        # 构造 M_ME_NC_1 ASDU:
        # [type_id=13(1)][vsq=1(1)][cot=20(1)][common_addr=1(2)]
        # [IOA=100(3)][value=42.5(4)]
        ioa = 100
        value_float = 42.5
        type_byte = struct.pack("<B", 13)  # M_ME_NC_1
        vsq_byte = struct.pack("<B", 1)
        cot_byte = struct.pack("<B", 20)  # interrogated
        ca_bytes = struct.pack("<H", 1)   # common_addr
        # IOA: 3 bytes, little-endian
        ioa_bytes = bytes([ioa & 0xFF, (ioa >> 8) & 0xFF, (ioa >> 16) & 0xFF])
        val_bytes = struct.pack("<f", value_float)
        asdu = type_byte + vsq_byte + cot_byte + ca_bytes + ioa_bytes + val_bytes
        result = backend._parse_data_asdu(asdu)
        assert 100 in result
        type_tag, value_str = result[100]
        assert type_tag == "M_ME_NC_1"
        assert "42.5" in value_str
