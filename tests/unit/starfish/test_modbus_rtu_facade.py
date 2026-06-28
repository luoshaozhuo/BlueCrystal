"""Starfish Modbus RTU PTY 轻量级 facade 测试。

验证：
1. CRC16 计算正确性（已知向量验证）。
2. RTU 帧 encode/decode 测试。
3. FC03 Read Holding Registers 请求/响应。
4. FC06 Write Single Register 请求/响应。
5. PTY start/stop/health/read 生命周期测试。
6. 异常帧处理测试（非法功能码、CRC 错误）。
7. codebase-pending 模式 fallback 测试。

测试阶段：开发期验证 (P1)。
使用的替身：pty.openpty() 创建 PTY pair（不等同真实串口）。
外部依赖：无（Python 标准库 pty）。
不能证明：真实 RS-232/RS-485 串口电气特性、波特率、奇偶校验、停止位。
NOT_RUN 条件：PTY 不可用时跳过 rtu-lightweight 模式测试。
"""

from __future__ import annotations

import fcntl
import os
import struct
import termios
import time

import pytest

from starfish.container import (
    create_ads_driver_adapter,
    create_default_backend_factory,
    create_default_driver_factory,
    create_goose_driver_adapter,
    create_http_rest_driver_adapter,
    create_iec101_driver_adapter,
    create_iec104_driver_adapter,
    create_iec61850_mms_driver_adapter,
    create_iec61850_report_driver_adapter,
    create_modbus_rtu_driver_adapter,
    create_modbus_tcp_driver_adapter,
    create_mqtt_driver_adapter,
    create_opcua_driver_adapter,
    create_server_simulator_driver_adapter,
    create_sv_driver_adapter,
)

from starfish.domain.server_config import (
    StarfishServerConfig,
    StarfishEndpointConfig,
    StarfishPointConfig,
    UnsupportedOperation,
)
from starfish.adapters.drivers.modbus.modbus_rtu_driver_adapter import (
    ModbusRtuDriverAdapter,
)
from starfish.infrastructure.drivers.modbus.modbus_rtu_pty_backend import (
    probe_modbus_rtu_binary,
    _crc16,
    _build_rtu_frame,
    _pack_bits,
    _unpack_bits,
)
from starfish.domain.protocols.modbus.register_encoding import (
    ByteOrder,
    ModbusRegisterValueType,
    WordOrder,
)


# ── fixtures ────────────────────────────────────────────────────────────────────


def _make_plan(
    scenario_id: str = "modbus_rtu_test",
    initial_values: dict | None = None,
) -> StarfishServerConfig:
    """构造最小测试用 StarfishServerConfig。

    Args:
        scenario_id: 场景标识。
        initial_values: 初始值 dict，None 时使用默认值。

    Returns:
        包含 2 个点位的 StarfishServerConfig。
    """
    if initial_values is None:
        initial_values = {"point_a": 1.0, "point_b": 2.0}

    return StarfishServerConfig(
        schema_version="1.0.0",
        scenario_id=scenario_id,
        synthetic=True,
        server_name=f"{scenario_id}_server",
        endpoints=[
            StarfishEndpointConfig(
                endpoint_id=f"{scenario_id}_ep",
                protocol="MODBUS_RTU",
                host="127.0.0.1",
                port=0,
            )
        ],
        points=[
            StarfishPointConfig(
                point_id="point_a",
                point_name="Point A",
                node_key="/points/a",
                value_type="Float",
                access_mode="RO",
            ),
            StarfishPointConfig(
                point_id="point_b",
                point_name="Point B",
                node_key="/points/b",
                value_type="Float",
                access_mode="RW",
            ),
        ],
        capabilities=["READ"],
        initial_values=initial_values,
    )


# ── CRC16 测试 ──────────────────────────────────────────────────────────────────


class TestCrc16:
    """CRC-16-IBM 计算正确性测试。"""

    def test_crc16_known_vector_1(self) -> None:
        """标准已知向量：\\x01\\x03\\x00\\x00\\x00\\x01 → CRC 值 0x0A84
        （在帧中按小端序打包为 84 0A，CRC 计算函数返回 16-bit 值）。
        """
        data = b"\x01\x03\x00\x00\x00\x01"
        crc = _crc16(data)
        assert crc == 0x0A84, f"CRC16 应为 0x0A84，实际 0x{crc:04X}"

    def test_crc16_known_vector_2(self) -> None:
        """读取响应帧 CRC 验证。
        FC03 响应：slave=01, func=03, byte_count=02, values=0000。
        """
        data = b"\x01\x03\x02\x00\x00"
        crc = _crc16(data)
        assert crc == 0x44B8, f"CRC16 应为 0x44B8，实际 0x{crc:04X}"

    def test_crc16_empty(self) -> None:
        """空数据 CRC 应为 0xFFFF（初始值不经任何处理即为最终值）。"""
        crc = _crc16(b"")
        assert crc == 0xFFFF

    def test_crc16_single_byte(self) -> None:
        """单字节 CRC 应为确定值。"""
        crc = _crc16(b"\x00")
        # 0x00 ^ 0xFFFF = 0xFFFF, 经过 8 次移位和多项式异或后得到
        assert crc == 0x40BF, f"CRC16(\\x00) 应为 0x40BF，实际 0x{crc:04X}"

    def test_crc16_all_zeros(self) -> None:
        """全零帧 CRC 一致性。"""
        data = b"\x00" * 10
        crc1 = _crc16(data)
        crc2 = _crc16(data)
        assert crc1 == crc2


# ── RTU 帧编解码测试 ────────────────────────────────────────────────────────────


class TestRtuFrameCodec:
    """RTU 帧 encode / decode 测试。"""

    def test_build_rtu_frame_basic(self) -> None:
        """构造基本 RTU 帧并验证格式。"""
        pdu = b"\x03\x00\x00\x00\x01"  # FC03 read holding registers
        frame = _build_rtu_frame(0x01, pdu)
        # frame = [slave][pdu][crc_low][crc_high]
        assert len(frame) == 1 + len(pdu) + 2  # slave + pdu + crc
        assert frame[0] == 0x01  # slave_id
        assert frame[1:1 + len(pdu)] == pdu
        # 验证 CRC
        crc = struct.unpack("<H", frame[-2:])[0]
        computed = _crc16(frame[:-2])
        assert crc == computed

    def test_build_rtu_frame_known_crc(self) -> None:
        """构造已知 CRC 期望值的 RTU 帧。"""
        # FC03 读取 1 个寄存器从地址 0: slave=01, func=03, start=0000, qty=0001
        # CRC 值 = 0x0A84，以小端序打包为 84 0A
        pdu = b"\x03\x00\x00\x00\x01"
        frame = _build_rtu_frame(0x01, pdu)
        # 帧应为：01 03 00 00 00 01 84 0A
        expected = b"\x01\x03\x00\x00\x00\x01\x84\x0A"
        assert frame == expected, (
            f"RTU 帧不匹配: {frame.hex()} != {expected.hex()}"
        )

    def test_rtu_frame_crc_self_consistent(self) -> None:
        """RTU 帧 CRC 自一致性验证。"""
        pdu = b"\x03\x00\x00\x00\x02"  # FC03 read 2 registers
        frame = _build_rtu_frame(0x01, pdu)
        crc = struct.unpack("<H", frame[-2:])[0]
        computed = _crc16(frame[:-2])
        assert crc == computed

    def test_rtu_frame_different_slave_id(self) -> None:
        """不同 slave_id 的帧应有不同 CRC。"""
        pdu = b"\x03\x00\x00\x00\x01"
        frame1 = _build_rtu_frame(0x01, pdu)
        frame2 = _build_rtu_frame(0x02, pdu)
        assert frame1 != frame2
        # 但 CRC 不同
        assert frame1[-2:] != frame2[-2:]


# ── codebase-pending 模式测试 ────────────────────────────────────────────────────


class TestModbusRtuCodebasePending:
    """codebase-pending 模式下的 facade 行为测试。"""

    def test_construction_codebase_pending(self) -> None:
        """构造 codebase-pending facade 应返回正确 mode。"""
        facade = create_modbus_rtu_driver_adapter(mode="codebase-pending")
        assert facade.protocol == "MODBUS_RTU"
        assert facade.mode == "codebase-pending"

    def test_start_stop_codebase_pending(self) -> None:
        """codebase-pending 模式 start/stop 生命周期。"""
        facade = create_modbus_rtu_driver_adapter(mode="codebase-pending")
        facade.start()
        h = facade.health()
        assert h["status"] == "started"
        assert h["mode"] == "codebase-pending"
        assert h["running"] is False

        facade.stop()
        assert facade.health()["status"] == "stopped"

    def test_load_points_and_read_codebase_pending(self) -> None:
        """codebase-pending 模式 load_points / read。"""
        plan = _make_plan("rtu_cp")
        facade = create_modbus_rtu_driver_adapter(mode="codebase-pending")
        facade.load_points(plan)
        values = facade.read()
        assert values["point_a"] == 1.0
        assert values["point_b"] == 2.0

    def test_update_values_codebase_pending(self) -> None:
        """codebase-pending 模式 update_values。"""
        plan = _make_plan("rtu_cp_update")
        facade = create_modbus_rtu_driver_adapter(mode="codebase-pending")
        facade.load_points(plan)
        facade.update_values({"point_a": 99.9})
        assert facade.read(["point_a"]) == {"point_a": 99.9}

    def test_not_implemented_codebase_pending(self) -> None:
        """codebase-pending 模式 NOT_IMPLEMENTED 操作。"""
        plan = _make_plan("rtu_cp_notimpl")
        facade = create_modbus_rtu_driver_adapter(mode="codebase-pending")
        facade.load_points(plan)

        with pytest.raises(UnsupportedOperation, match="write"):
            facade.write("point_a", 100)

        with pytest.raises(UnsupportedOperation, match="subscribe"):
            facade.subscribe(["point_a"])

        with pytest.raises(UnsupportedOperation, match="report"):
            facade.report()

    def test_capabilities_codebase_pending(self) -> None:
        """codebase-pending 模式 capabilities。"""
        plan = _make_plan("rtu_cp_caps")
        facade = create_modbus_rtu_driver_adapter(mode="codebase-pending")
        assert facade.capabilities() == []
        facade.load_points(plan)
        # Round 14: capabilities() 现在包含 plan 声明能力 + MODBUS_RTU 功能码
        caps = facade.capabilities()
        assert "READ" in caps
        assert "MODBUS_RTU_FC03" in caps
        assert "MODBUS_RTU_FC06" in caps


# ── probe 测试 ──────────────────────────────────────────────────────────────────


class TestProbeModbusRtu:
    """probe_modbus_rtu_binary 测试。"""

    def test_probe_returns_boolean_and_reason(self) -> None:
        """probe 应返回 (bool, str)。"""
        ok, reason = probe_modbus_rtu_binary()
        assert isinstance(ok, bool)
        assert isinstance(reason, str)
        assert len(reason) > 0

    def test_probe_reason_contains_modbus_rtu(self) -> None:
        """probe reason 应包含 MODBUS_RTU。"""
        _, reason = probe_modbus_rtu_binary()
        assert "MODBUS_RTU" in reason

    def test_probe_pty_available_is_expected(self) -> None:
        """在 WSL2 环境中 PTY 应可用。"""
        ok, reason = probe_modbus_rtu_binary()
        if ok:
            assert "PTY" in reason
            assert "不等同真实串口" in reason
        else:
            assert "codebase-pending" in reason


# ── rtu-lightweight 模式测试 ─────────────────────────────────────────────────────


@pytest.fixture
def rtu_facade() -> ModbusRtuDriverAdapter:
    """创建 rtu-lightweight 模式的 facade 实例。"""
    return create_modbus_rtu_driver_adapter(mode="rtu-lightweight")


class TestModbusRtuLightweight:
    """rtu-lightweight 模式下的 PTY 生命周期和操作测试。"""

    def test_construction(self, rtu_facade: ModbusRtuDriverAdapter) -> None:
        """新建 facade 应为未启动状态，mode 为 rtu-lightweight。"""
        assert rtu_facade.protocol == "MODBUS_RTU"
        assert rtu_facade.mode == "rtu-lightweight"

    def test_initial_health(self, rtu_facade: ModbusRtuDriverAdapter) -> None:
        """停止状态 health 应反映正确元信息。"""
        h = rtu_facade.health()
        assert h["status"] == "stopped"
        assert h["mode"] == "rtu-lightweight"
        assert h["protocol"] == "MODBUS_RTU"
        assert h["running"] is False
        assert "不等同真实串口" in h.get("note", "")

    def test_start_stop_lifecycle(self, rtu_facade: ModbusRtuDriverAdapter) -> None:
        """PTY start/stop 基本生命周期。"""
        rtu_facade.start()
        h = rtu_facade.health()
        assert h["status"] == "started"
        # PTY 应报告 running
        assert h["running"] is True

        # slave_path 应不为空
        assert rtu_facade.slave_path != ""
        assert rtu_facade.slave_path.startswith("/dev/")

        rtu_facade.stop()
        assert rtu_facade.health()["status"] == "stopped"
        # 停止后 slave_path 应为空
        assert rtu_facade.slave_path == ""

    def test_start_idempotent(self, rtu_facade: ModbusRtuDriverAdapter) -> None:
        """重复 start 为幂等。"""
        rtu_facade.start()
        path1 = rtu_facade.slave_path
        rtu_facade.start()
        path2 = rtu_facade.slave_path
        assert path1 == path2
        rtu_facade.stop()

    def test_stop_idempotent(self, rtu_facade: ModbusRtuDriverAdapter) -> None:
        """重复 stop 为幂等。"""
        rtu_facade.start()
        rtu_facade.stop()
        rtu_facade.stop()
        assert rtu_facade.health()["status"] == "stopped"

    def test_load_points_and_read(self, rtu_facade: ModbusRtuDriverAdapter) -> None:
        """load_points 后 read 返回 initial_values。"""
        plan = _make_plan("rtu_lw_load")
        rtu_facade.load_points(plan)
        values = rtu_facade.read()
        assert values["point_a"] == 1.0
        assert values["point_b"] == 2.0

    def test_read_specific_points(self, rtu_facade: ModbusRtuDriverAdapter) -> None:
        """指定 point_ids 时应只返回对应值。"""
        plan = _make_plan("rtu_lw_specific")
        rtu_facade.load_points(plan)
        values = rtu_facade.read(["point_a"])
        assert values == {"point_a": 1.0}

    def test_read_nonexistent_point(self, rtu_facade: ModbusRtuDriverAdapter) -> None:
        """不存在 point_id 应返回 None。"""
        plan = _make_plan("rtu_lw_nonexist")
        rtu_facade.load_points(plan)
        values = rtu_facade.read(["nonexistent"])
        assert values == {"nonexistent": None}

    def test_write_success(self, rtu_facade: ModbusRtuDriverAdapter) -> None:
        """write 应更新内存值。"""
        plan = _make_plan("rtu_lw_write")
        rtu_facade.load_points(plan)
        rtu_facade.write("point_a", 42.0)
        assert rtu_facade.read(["point_a"]) == {"point_a": 42.0}

    def test_write_nonexistent_point(self, rtu_facade: ModbusRtuDriverAdapter) -> None:
        """write 不存在点位应抛出 KeyError。"""
        plan = _make_plan("rtu_lw_write_err")
        rtu_facade.load_points(plan)
        with pytest.raises(KeyError):
            rtu_facade.write("nonexistent", 100)

    def test_update_values(self, rtu_facade: ModbusRtuDriverAdapter) -> None:
        """update_values 应批量更新内存值。"""
        plan = _make_plan("rtu_lw_update")
        rtu_facade.load_points(plan)
        rtu_facade.update_values({"point_a": 99.9, "new_point": 0})
        values = rtu_facade.read()
        assert values["point_a"] == 99.9
        assert values["new_point"] == 0

    def test_capabilities(self, rtu_facade: ModbusRtuDriverAdapter) -> None:
        """capabilities 应返回 plan 中的声明 + MODBUS_RTU 功能码。"""
        plan = _make_plan("rtu_lw_caps")
        rtu_facade.load_points(plan)
        caps = rtu_facade.capabilities()
        assert "READ" in caps
        assert "MODBUS_RTU_FC03" in caps
        assert "MODBUS_RTU_FC06" in caps

    def test_capabilities_no_plan(self, rtu_facade: ModbusRtuDriverAdapter) -> None:
        """未加载 plan 时 capabilities 返回空列表。"""
        assert rtu_facade.capabilities() == []

    def test_subscribe_raises_unsupported(self, rtu_facade: ModbusRtuDriverAdapter) -> None:
        """subscribe 应抛出 UnsupportedOperation。"""
        plan = _make_plan("rtu_lw_sub")
        rtu_facade.load_points(plan)
        with pytest.raises(UnsupportedOperation, match="subscribe"):
            rtu_facade.subscribe(["point_a"])

    def test_report_raises_unsupported(self, rtu_facade: ModbusRtuDriverAdapter) -> None:
        """report 应抛出 UnsupportedOperation。"""
        plan = _make_plan("rtu_lw_report")
        rtu_facade.load_points(plan)
        with pytest.raises(UnsupportedOperation, match="report"):
            rtu_facade.report()

    def test_health_after_load_points(self, rtu_facade: ModbusRtuDriverAdapter) -> None:
        """load_points 后 health 应反映 plan 信息。"""
        plan = _make_plan("rtu_lw_health")
        rtu_facade.load_points(plan)
        h = rtu_facade.health()
        assert h["plan_loaded"] is True
        assert h["point_count"] == 2
        assert h["endpoint_count"] == 1
        assert h["synthetic"] is True

    def test_health_with_slave_path(self, rtu_facade: ModbusRtuDriverAdapter) -> None:
        """启动后 health 应包含 slave_path。"""
        plan = _make_plan("rtu_lw_slave")
        rtu_facade.load_points(plan)
        rtu_facade.start()
        try:
            h = rtu_facade.health()
            assert "slave_path" in h
            assert h["slave_path"].startswith("/dev/")
        finally:
            rtu_facade.stop()

    def test_slave_path_before_start(self, rtu_facade: ModbusRtuDriverAdapter) -> None:
        """未启动时 slave_path 应为空。"""
        assert rtu_facade.slave_path == ""


# ── 寄存器映射测试 ──────────────────────────────────────────────────────────────


class TestRegisterMapping:
    """point_id -> 寄存器地址映射测试（与 ModbusTcpDriverAdapter 一致）。"""

    def test_sorted_register_mapping(self) -> None:
        """point_id 按字典序排序后分配从 0 开始的寄存器地址。"""
        plan = _make_plan(
            "rtu_map",
            initial_values={"c_zone": 1, "a_zone": 2, "b_zone": 3},
        )
        facade = create_modbus_rtu_driver_adapter(mode="rtu-lightweight")
        facade.load_points(plan)

        # 字典序：a_zone, b_zone, c_zone → 寄存器 0, 1, 2
        values = facade.read()
        sorted_ids = sorted(values.keys())
        assert sorted_ids == ["a_zone", "b_zone", "c_zone"]

        # 验证通过 read 可以读取全部
        assert facade.read() == {"a_zone": 2, "b_zone": 3, "c_zone": 1}

        facade.stop()

    def test_register_map_stable_on_reload(self) -> None:
        """重复 load_points 后寄存器映射应保持稳定。"""
        plan = _make_plan("rtu_reload")
        facade = create_modbus_rtu_driver_adapter(mode="rtu-lightweight")
        facade.load_points(plan)
        map1 = dict(facade._reg_map)
        facade.load_points(plan)
        map2 = dict(facade._reg_map)
        assert map1 == map2

        facade.stop()


# ── PTY 读写辅助 ─────────────────────────────────────────────────────────────


def _setup_raw_pty(slave_fd: int) -> None:
    """设置 slave PTY 为 raw 模式，禁用行缓冲和回显。

    在 raw 模式下，数据直接通过 PTY 传递，不做任何终端处理。
    这对于二进制协议（Modbus RTU）至关重要。

    Args:
        slave_fd: PTY slave 端文件描述符。
    """
    attrs = termios.tcgetattr(slave_fd)
    # 禁用回显、规范模式、信号处理
    attrs[3] = attrs[3] & ~(
        termios.ECHO | termios.ICANON | termios.ISIG
    )
    # 禁用 CR→NL 映射、输入奇偶校验等
    attrs[0] = 0  # iflag
    attrs[1] = 0  # oflag
    attrs[2] = attrs[2] & ~(termios.CSIZE) | termios.CS8  # 8-bit
    attrs[4] = termios.B9600  # ispeed (dummy)
    attrs[5] = termios.B9600  # ospeed (dummy)
    termios.tcsetattr(slave_fd, termios.TCSANOW, attrs)


def _pty_read(slave_fd: int, timeout: float = 1.0) -> bytes:
    """从 PTY slave fd 非阻塞读取，带超时。

    设置 slave fd 为非阻塞模式，轮询读取直到超时或获得数据。
    读取后将 fd 恢复为阻塞模式。

    Args:
        slave_fd: PTY slave 端文件描述符。
        timeout: 最大等待时间（秒）。

    Returns:
        读取到的字节串，超时返回空 bytes。
    """
    # 设为非阻塞
    flags = fcntl.fcntl(slave_fd, fcntl.F_GETFL)
    fcntl.fcntl(slave_fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

    deadline = time.monotonic() + timeout
    response = b""
    while time.monotonic() < deadline:
        try:
            chunk = os.read(slave_fd, 4096)
            if chunk:
                response += chunk
                if len(response) >= 5:
                    # 有足够数据，尝试解析完整帧
                    break
        except BlockingIOError:
            time.sleep(0.01)
            continue

    # 恢复阻塞模式
    fcntl.fcntl(slave_fd, fcntl.F_SETFL, flags)
    return response


# ── FC03/FC06 PTY 通信测试 ──────────────────────────────────────────────────────


class TestModbusRtuPtyCommunication:
    """通过 PTY slave 端与 facade 通信测试 FC03/FC06 功能。"""

    def test_fc03_read_holding_registers_via_pty(self) -> None:
        """通过 PTY slave 发送 FC03 请求并验证响应。"""
        plan = _make_plan(
            "rtu_fc03_pty",
            initial_values={"point_a": 100, "point_b": 200},
        )
        facade = create_modbus_rtu_driver_adapter(mode="rtu-lightweight")
        facade.load_points(plan)
        facade.start()

        try:
            # 打开 slave PTY 端
            slave_name = facade.slave_path
            assert slave_name != ""

            slave_fd = os.open(slave_name, os.O_RDWR | os.O_NOCTTY)
            _setup_raw_pty(slave_fd)

            # 构造 FC03 请求：读取 2 个寄存器从地址 0
            # slave=01, func=03, start=0000, qty=0002
            pdu = struct.pack(">BHH", 0x03, 0x0000, 0x0002)
            request = _build_rtu_frame(0x01, pdu)

            os.write(slave_fd, request)

            # 非阻塞读取响应
            response = _pty_read(slave_fd)
            os.close(slave_fd)

            # 验证响应：应包含 2 个寄存器值
            assert len(response) >= 9, (
                f"FC03 响应帧长度不足: {len(response)} bytes, {response.hex()}"
            )
            assert response[0] == 0x01  # slave_id 回显
            assert response[1] == 0x03  # FC03

            # 验证 CRC
            crc = struct.unpack("<H", response[-2:])[0]
            computed_crc = _crc16(response[:-2])
            assert crc == computed_crc, "响应帧 CRC 校验失败"

        finally:
            facade.stop()

    def test_fc06_write_single_register_via_pty(self) -> None:
        """通过 PTY slave 发送 FC06 请求并验证响应（回显）。"""
        plan = _make_plan(
            "rtu_fc06_pty",
            initial_values={"point_a": 50, "point_b": 75},
        )
        facade = create_modbus_rtu_driver_adapter(mode="rtu-lightweight")
        facade.load_points(plan)
        facade.start()

        try:
            slave_name = facade.slave_path
            slave_fd = os.open(slave_name, os.O_RDWR | os.O_NOCTTY)
            _setup_raw_pty(slave_fd)

            # 构造 FC06 请求：写入寄存器 1（point_b），值=999
            pdu = struct.pack(">BHH", 0x06, 0x0001, 999)
            request = _build_rtu_frame(0x01, pdu)

            os.write(slave_fd, request)
            response = _pty_read(slave_fd)
            os.close(slave_fd)

            # FC06 响应应回显请求
            assert len(response) >= 8, (
                f"FC06 响应帧长度不足: {len(response)} bytes"
            )
            assert response[1] == 0x06  # FC06

            # 验证内部值已更新
            val = facade.read(["point_b"])
            assert val["point_b"] == 999, f"FC06 后 point_b 应为 999，实际 {val['point_b']}"

        finally:
            facade.stop()

    def test_fc03_out_of_range_returns_zero(self) -> None:
        """FC03 请求超出映射范围的寄存器应返回 0。"""
        plan = _make_plan(
            "rtu_fc03_range",
            initial_values={"point_a": 100},
        )
        facade = create_modbus_rtu_driver_adapter(mode="rtu-lightweight")
        facade.load_points(plan)
        facade.start()

        try:
            slave_name = facade.slave_path
            slave_fd = os.open(slave_name, os.O_RDWR | os.O_NOCTTY)
            _setup_raw_pty(slave_fd)

            # 读取地址 5 开始的 1 个寄存器（超出范围）
            pdu = struct.pack(">BHH", 0x03, 0x0005, 0x0001)
            request = _build_rtu_frame(0x01, pdu)

            os.write(slave_fd, request)
            response = _pty_read(slave_fd)
            os.close(slave_fd)

            # 应返回 0（寄存器不存在）
            assert len(response) >= 7, (
                f"FC03 越界响应长度不足: {len(response)} bytes"
            )
            assert response[1] == 0x03  # FC03
            byte_count = response[2]
            assert byte_count == 2  # 1 个寄存器 = 2 字节
            # 值应为 0
            reg_value = struct.unpack(">H", response[3:5])[0]
            assert reg_value == 0

        finally:
            facade.stop()

    def test_illegal_function_code_returns_exception(self) -> None:
        """非法功能码应返回异常响应。"""
        plan = _make_plan("rtu_exception")
        facade = create_modbus_rtu_driver_adapter(mode="rtu-lightweight")
        facade.load_points(plan)
        facade.start()

        try:
            slave_name = facade.slave_path
            slave_fd = os.open(slave_name, os.O_RDWR | os.O_NOCTTY)
            _setup_raw_pty(slave_fd)

            # 发送非法功能码 0x08（Diagnostics - 不支持）
            pdu = b"\x08\x00\x00\x00\x01"
            request = _build_rtu_frame(0x01, pdu)

            os.write(slave_fd, request)
            response = _pty_read(slave_fd)
            os.close(slave_fd)

            # 异常响应：功能码 | 0x80
            assert len(response) >= 5, (
                f"异常响应长度不足: {len(response)} bytes"
            )
            assert response[1] == 0x88  # 0x08 | 0x80
            assert response[2] == 0x01  # illegal function

            # CRC 校验
            crc = struct.unpack("<H", response[-2:])[0]
            computed_crc = _crc16(response[:-2])
            assert crc == computed_crc

        finally:
            facade.stop()

    def test_crc_error_frame_ignored(self) -> None:
        """CRC 错误的帧应被静默忽略。"""
        plan = _make_plan("rtu_crc_bad")
        facade = create_modbus_rtu_driver_adapter(mode="rtu-lightweight")
        facade.load_points(plan)
        facade.start()

        try:
            slave_name = facade.slave_path
            slave_fd = os.open(slave_name, os.O_RDWR | os.O_NOCTTY)
            _setup_raw_pty(slave_fd)

            # 构造 FC03 请求但修改 CRC 为错误值
            pdu = struct.pack(">BHH", 0x03, 0x0000, 0x0001)
            # 不通过 _build_rtu_frame，手动构造错误 CRC 帧
            raw = struct.pack(">B", 0x01) + pdu + struct.pack("<H", 0xDEAD)
            os.write(slave_fd, raw)

            # 尝试读取，不应有响应（CRC 错误被忽略）
            response = _pty_read(slave_fd, timeout=0.3)

            os.close(slave_fd)
            # CRC 错误的帧不产生响应
            assert response == b"", (
                f"CRC 错误帧应被忽略，但收到了响应: {response.hex()}"
            )

        finally:
            facade.stop()


# ── 边界测试 ────────────────────────────────────────────────────────────────────


class TestModbusRtuEdgeCases:
    """Modbus RTU facade 边界条件测试。"""

    def test_start_without_load_points(self) -> None:
        """未 load_points 时 start 应成功执行。"""
        facade = create_modbus_rtu_driver_adapter(mode="rtu-lightweight")
        facade.start()
        try:
            h = facade.health()
            assert h["status"] == "started"
            assert h["plan_loaded"] is False
            assert h["point_count"] == 0
        finally:
            facade.stop()

    def test_read_without_plan(self) -> None:
        """未 load_points 时 read 应返回空 dict。"""
        facade = create_modbus_rtu_driver_adapter(mode="rtu-lightweight")
        values = facade.read()
        assert values == {}

    def test_capabilities_without_plan(self) -> None:
        """未 load_points 时 capabilities 返回空列表。"""
        facade = create_modbus_rtu_driver_adapter(mode="rtu-lightweight")
        assert facade.capabilities() == []

    def test_bool_value_handling(self) -> None:
        """布尔值应转为 1/0 用于寄存器响应。"""
        plan = _make_plan("rtu_bool", initial_values={"flag": True})
        facade = create_modbus_rtu_driver_adapter(mode="rtu-lightweight")
        facade.load_points(plan)
        facade.start()

        try:
            slave_name = facade.slave_path
            slave_fd = os.open(slave_name, os.O_RDWR | os.O_NOCTTY)
            _setup_raw_pty(slave_fd)

            pdu = struct.pack(">BHH", 0x03, 0x0000, 0x0001)
            request = _build_rtu_frame(0x01, pdu)
            os.write(slave_fd, request)

            response = _pty_read(slave_fd)
            os.close(slave_fd)

            assert len(response) >= 7, (
                f"布尔值 FC03 响应长度不足: {len(response)} bytes"
            )
            reg_value = struct.unpack(">H", response[3:5])[0]
            assert reg_value == 1  # True → 1

        finally:
            facade.stop()


# ── 位打包/解包测试 ────────────────────────────────────────────────────────────


class TestBitPacking:
    """_pack_bits / _unpack_bits 位打包工具函数测试。"""

    def test_pack_single_byte_all_zeros(self) -> None:
        """8 位全 0 应打包为 1 字节 0x00。"""
        result = _pack_bits([0] * 8)
        assert result == b"\x00"

    def test_pack_single_byte_all_ones(self) -> None:
        """8 位全 1 应打包为 1 字节 0xFF。"""
        result = _pack_bits([1] * 8)
        assert result == b"\xFF"

    def test_pack_bit_zero_on(self) -> None:
        """第 0 位（LSB）为 1 应产生 0x01。"""
        bits = [1, 0, 0, 0, 0, 0, 0, 0]
        result = _pack_bits(bits)
        assert result == b"\x01"

    def test_pack_bit_seven_on(self) -> None:
        """第 7 位（MSB）为 1 应产生 0x80。"""
        bits = [0, 0, 0, 0, 0, 0, 0, 1]
        result = _pack_bits(bits)
        assert result == b"\x80"

    def test_pack_multiple_bytes(self) -> None:
        """跨字节打包：9 位产生 2 字节。"""
        bits = [1] * 9
        result = _pack_bits(bits)
        assert len(result) == 2
        assert result[0] == 0xFF  # 前 8 位
        assert result[1] == 0x01  # 第 9 位

    def test_unpack_roundtrip(self) -> None:
        """打包后解包应与原始位列表一致。"""
        original = [1, 0, 1, 0, 1, 1, 0, 1]
        packed = _pack_bits(original)
        unpacked = _unpack_bits(packed, len(original))
        assert unpacked == [bool(b) for b in original]

    def test_unpack_partial_count(self) -> None:
        """解包时仅读取 count 个有效位。"""
        packed = b"\xFF"  # 8 位全 1
        result = _unpack_bits(packed, 3)
        assert result == [True, True, True]


# ── FC01 Read Coils 测试 ────────────────────────────────────────────────────────


def _make_plan_with_coils() -> StarfishServerConfig:
    """构造包含线圈点位和保持寄存器的测试用 StarfishServerConfig。

    Returns:
        包含 2 个线圈点 + 1 个保持寄存器点的 ServerPlan。
    """
    return StarfishServerConfig(
        schema_version="1.0.0",
        scenario_id="modbus_rtu_coils",
        synthetic=True,
        server_name="modbus_rtu_coils_server",
        endpoints=[
            StarfishEndpointConfig(
                endpoint_id="modbus_rtu_coils_ep",
                protocol="MODBUS_RTU",
                host="127.0.0.1",
                port=0,
            )
        ],
        points=[
            StarfishPointConfig(
                point_id="coil_0",
                point_name="Coil 0",
                node_key="/coils/0",
                variable_key="coils",
                value_type="Bool",
                access_mode="RW",
            ),
            StarfishPointConfig(
                point_id="coil_1",
                point_name="Coil 1",
                node_key="/coils/1",
                variable_key="coils",
                value_type="Bool",
                access_mode="RW",
            ),
            StarfishPointConfig(
                point_id="reg_a",
                point_name="Register A",
                node_key="/reg/a",
                variable_key="",
                value_type="Float",
                access_mode="RW",
            ),
        ],
        capabilities=["READ"],
        initial_values={"coil_0": True, "coil_1": False, "reg_a": 42},
    )


def _make_plan_with_discrete_inputs() -> StarfishServerConfig:
    """构造包含离散输入点位的测试用 StarfishServerConfig。

    Returns:
        包含 2 个离散输入点的 ServerPlan。
    """
    return StarfishServerConfig(
        schema_version="1.0.0",
        scenario_id="modbus_rtu_di",
        synthetic=True,
        server_name="modbus_rtu_di_server",
        endpoints=[
            StarfishEndpointConfig(
                endpoint_id="modbus_rtu_di_ep",
                protocol="MODBUS_RTU",
                host="127.0.0.1",
                port=0,
            )
        ],
        points=[
            StarfishPointConfig(
                point_id="di_0",
                point_name="DI 0",
                node_key="/di/0",
                variable_key="discrete_inputs",
                value_type="Bool",
                access_mode="RO",
            ),
            StarfishPointConfig(
                point_id="di_1",
                point_name="DI 1",
                node_key="/di/1",
                variable_key="discrete_inputs",
                value_type="Bool",
                access_mode="RO",
            ),
        ],
        capabilities=["READ"],
        initial_values={"di_0": True, "di_1": False},
    )


def _make_plan_with_input_registers() -> StarfishServerConfig:
    """构造包含输入寄存器点位的测试用 StarfishServerConfig。

    Returns:
        包含 2 个输入寄存器点的 ServerPlan。
    """
    return StarfishServerConfig(
        schema_version="1.0.0",
        scenario_id="modbus_rtu_ir",
        synthetic=True,
        server_name="modbus_rtu_ir_server",
        endpoints=[
            StarfishEndpointConfig(
                endpoint_id="modbus_rtu_ir_ep",
                protocol="MODBUS_RTU",
                host="127.0.0.1",
                port=0,
            )
        ],
        points=[
            StarfishPointConfig(
                point_id="ir_0",
                point_name="Input Reg 0",
                node_key="/ir/0",
                variable_key="input_registers",
                value_type="Int32",
                access_mode="RO",
            ),
            StarfishPointConfig(
                point_id="ir_1",
                point_name="Input Reg 1",
                node_key="/ir/1",
                variable_key="input_registers",
                value_type="Int32",
                access_mode="RO",
            ),
        ],
        capabilities=["READ"],
        initial_values={"ir_0": 100, "ir_1": 200},
    )


class TestModbusRtuFc01Coils:
    """FC01 Read Coils PTY 通信测试。"""

    def test_fc01_read_coils_via_pty(self) -> None:
        """通过 PTY slave 发送 FC01 请求并验证线圈状态响应。"""
        plan = _make_plan_with_coils()
        facade = create_modbus_rtu_driver_adapter(mode="rtu-lightweight")
        facade.load_points(plan)
        facade.start()

        try:
            slave_name = facade.slave_path
            slave_fd = os.open(slave_name, os.O_RDWR | os.O_NOCTTY)
            _setup_raw_pty(slave_fd)

            # FC01 请求：读取 2 个线圈从地址 0
            pdu = struct.pack(">BHH", 0x01, 0x0000, 0x0002)
            request = _build_rtu_frame(0x01, pdu)
            os.write(slave_fd, request)

            response = _pty_read(slave_fd)
            os.close(slave_fd)

            assert len(response) >= 5, (
                f"FC01 响应帧长度不足: {len(response)} bytes"
            )
            assert response[0] == 0x01  # slave_id
            assert response[1] == 0x01  # FC01
            byte_count = response[2]
            assert byte_count == 1  # 2 个线圈 = 1 字节
            # coil_0=True (bit0=1), coil_1=False (bit1=0) -> 0x01
            assert response[3] & 0x01 == 1  # coil_0 = ON
            assert response[3] & 0x02 == 0  # coil_1 = OFF

            # 验证 CRC
            crc = struct.unpack("<H", response[-2:])[0]
            computed_crc = _crc16(response[:-2])
            assert crc == computed_crc

        finally:
            facade.stop()

    def test_fc01_illegal_data_address(self) -> None:
        """FC01 请求超出范围的线圈地址应返回异常 0x02。"""
        plan = _make_plan_with_coils()
        facade = create_modbus_rtu_driver_adapter(mode="rtu-lightweight")
        facade.load_points(plan)
        facade.start()

        try:
            slave_name = facade.slave_path
            slave_fd = os.open(slave_name, os.O_RDWR | os.O_NOCTTY)
            _setup_raw_pty(slave_fd)

            pdu = struct.pack(">BHH", 0x01, 0x000A, 0x0004)
            request = _build_rtu_frame(0x01, pdu)
            os.write(slave_fd, request)

            response = _pty_read(slave_fd)
            os.close(slave_fd)

            assert len(response) >= 5
            assert response[1] == 0x81  # FC01 | 0x80
            assert response[2] == 0x02  # illegal data address

        finally:
            facade.stop()

    def test_fc01_illegal_data_value(self) -> None:
        """FC01 请求数量超出范围应返回异常 0x03。"""
        plan = _make_plan_with_coils()
        facade = create_modbus_rtu_driver_adapter(mode="rtu-lightweight")
        facade.load_points(plan)
        facade.start()

        try:
            slave_name = facade.slave_path
            slave_fd = os.open(slave_name, os.O_RDWR | os.O_NOCTTY)
            _setup_raw_pty(slave_fd)

            # 请求 2001 个线圈（超出 2000 上限）
            pdu = struct.pack(">BHH", 0x01, 0x0000, 0x07D1)
            request = _build_rtu_frame(0x01, pdu)
            os.write(slave_fd, request)

            response = _pty_read(slave_fd)
            os.close(slave_fd)

            assert len(response) >= 5
            assert response[1] == 0x81  # FC01 | 0x80
            assert response[2] == 0x03  # illegal data value

        finally:
            facade.stop()


# ── FC02 Read Discrete Inputs 测试 ───────────────────────────────────────────────


class TestModbusRtuFc02DiscreteInputs:
    """FC02 Read Discrete Inputs PTY 通信测试。"""

    def test_fc02_read_discrete_inputs_via_pty(self) -> None:
        """通过 PTY slave 发送 FC02 请求并验证离散输入状态响应。"""
        plan = _make_plan_with_discrete_inputs()
        facade = create_modbus_rtu_driver_adapter(mode="rtu-lightweight")
        facade.load_points(plan)
        facade.start()

        try:
            slave_name = facade.slave_path
            slave_fd = os.open(slave_name, os.O_RDWR | os.O_NOCTTY)
            _setup_raw_pty(slave_fd)

            # FC02 请求：读取 2 个离散输入从地址 0
            pdu = struct.pack(">BHH", 0x02, 0x0000, 0x0002)
            request = _build_rtu_frame(0x01, pdu)
            os.write(slave_fd, request)

            response = _pty_read(slave_fd)
            os.close(slave_fd)

            assert len(response) >= 5
            assert response[0] == 0x01
            assert response[1] == 0x02  # FC02
            assert response[2] == 1     # 1 byte
            # di_0=True (bit0=1), di_1=False (bit1=0) -> 0x01
            assert response[3] & 0x01 == 1
            assert response[3] & 0x02 == 0

        finally:
            facade.stop()

    def test_fc02_illegal_data_address(self) -> None:
        """FC02 请求超出范围的离散输入地址应返回异常 0x02。"""
        plan = _make_plan_with_discrete_inputs()
        facade = create_modbus_rtu_driver_adapter(mode="rtu-lightweight")
        facade.load_points(plan)
        facade.start()

        try:
            slave_name = facade.slave_path
            slave_fd = os.open(slave_name, os.O_RDWR | os.O_NOCTTY)
            _setup_raw_pty(slave_fd)

            pdu = struct.pack(">BHH", 0x02, 0x0010, 0x0004)
            request = _build_rtu_frame(0x01, pdu)
            os.write(slave_fd, request)

            response = _pty_read(slave_fd)
            os.close(slave_fd)

            assert len(response) >= 5
            assert response[1] == 0x82  # FC02 | 0x80
            assert response[2] == 0x02  # illegal data address

        finally:
            facade.stop()


# ── FC04 Read Input Registers 测试 ───────────────────────────────────────────────


class TestModbusRtuFc04InputRegisters:
    """FC04 Read Input Registers PTY 通信测试。"""

    def test_fc04_read_input_registers_via_pty(self) -> None:
        """通过 PTY slave 发送 FC04 请求并验证输入寄存器响应。"""
        plan = _make_plan_with_input_registers()
        facade = create_modbus_rtu_driver_adapter(mode="rtu-lightweight")
        facade.load_points(plan)
        facade.start()

        try:
            slave_name = facade.slave_path
            slave_fd = os.open(slave_name, os.O_RDWR | os.O_NOCTTY)
            _setup_raw_pty(slave_fd)

            # FC04 请求：读取 2 个输入寄存器从地址 0
            pdu = struct.pack(">BHH", 0x04, 0x0000, 0x0002)
            request = _build_rtu_frame(0x01, pdu)
            os.write(slave_fd, request)

            response = _pty_read(slave_fd)
            os.close(slave_fd)

            assert len(response) >= 9
            assert response[0] == 0x01
            assert response[1] == 0x04  # FC04
            assert response[2] == 4     # 2 registers * 2 bytes
            # ir_0=100, ir_1=200
            val0 = struct.unpack(">H", response[3:5])[0]
            val1 = struct.unpack(">H", response[5:7])[0]
            assert val0 == 100
            assert val1 == 200

        finally:
            facade.stop()

    def test_fc04_illegal_data_value(self) -> None:
        """FC04 请求数量超出范围应返回异常 0x03。"""
        plan = _make_plan_with_input_registers()
        facade = create_modbus_rtu_driver_adapter(mode="rtu-lightweight")
        facade.load_points(plan)
        facade.start()

        try:
            slave_name = facade.slave_path
            slave_fd = os.open(slave_name, os.O_RDWR | os.O_NOCTTY)
            _setup_raw_pty(slave_fd)

            # 请求 126 个寄存器（超出 125 上限）
            pdu = struct.pack(">BHH", 0x04, 0x0000, 0x007E)
            request = _build_rtu_frame(0x01, pdu)
            os.write(slave_fd, request)

            response = _pty_read(slave_fd)
            os.close(slave_fd)

            assert len(response) >= 5
            assert response[1] == 0x84  # FC04 | 0x80
            assert response[2] == 0x03  # illegal data value

        finally:
            facade.stop()


# ── FC05 Write Single Coil 测试 ──────────────────────────────────────────────────


class TestModbusRtuFc05WriteSingleCoil:
    """FC05 Write Single Coil PTY 通信测试。"""

    def test_fc05_write_coil_on_via_pty(self) -> None:
        """通过 PTY slave 发送 FC05 ON 请求并验证响应（回显）+ 读回。"""
        plan = _make_plan_with_coils()
        facade = create_modbus_rtu_driver_adapter(mode="rtu-lightweight")
        facade.load_points(plan)
        facade.start()

        try:
            slave_name = facade.slave_path
            slave_fd = os.open(slave_name, os.O_RDWR | os.O_NOCTTY)
            _setup_raw_pty(slave_fd)

            # FC05 写入线圈 0 = ON (0xFF00)
            pdu = struct.pack(">BHH", 0x05, 0x0000, 0xFF00)
            request = _build_rtu_frame(0x01, pdu)
            os.write(slave_fd, request)

            response = _pty_read(slave_fd)
            os.close(slave_fd)

            assert len(response) >= 8
            assert response[1] == 0x05  # FC05 回显
            # 验证回显值
            echo_addr = struct.unpack(">H", response[2:4])[0]
            echo_val = struct.unpack(">H", response[4:6])[0]
            assert echo_addr == 0x0000
            assert echo_val == 0xFF00

        finally:
            facade.stop()

    def test_fc05_write_coil_off_via_pty(self) -> None:
        """通过 PTY slave 发送 FC05 OFF 请求并验证响应（回显）。"""
        plan = _make_plan_with_coils()
        facade = create_modbus_rtu_driver_adapter(mode="rtu-lightweight")
        facade.load_points(plan)
        facade.start()

        try:
            slave_name = facade.slave_path
            slave_fd = os.open(slave_name, os.O_RDWR | os.O_NOCTTY)
            _setup_raw_pty(slave_fd)

            # FC05 写入线圈 0 = OFF (0x0000)
            pdu = struct.pack(">BHH", 0x05, 0x0000, 0x0000)
            request = _build_rtu_frame(0x01, pdu)
            os.write(slave_fd, request)

            response = _pty_read(slave_fd)
            os.close(slave_fd)

            assert len(response) >= 8
            assert response[1] == 0x05  # FC05 回显
            echo_val = struct.unpack(">H", response[4:6])[0]
            assert echo_val == 0x0000  # OFF

        finally:
            facade.stop()

    def test_fc05_illegal_data_value(self) -> None:
        """FC05 写入非法线圈值（非 0x0000/0xFF00）应返回异常 0x03。"""
        plan = _make_plan_with_coils()
        facade = create_modbus_rtu_driver_adapter(mode="rtu-lightweight")
        facade.load_points(plan)
        facade.start()

        try:
            slave_name = facade.slave_path
            slave_fd = os.open(slave_name, os.O_RDWR | os.O_NOCTTY)
            _setup_raw_pty(slave_fd)

            # 非法值 0x1234
            pdu = struct.pack(">BHH", 0x05, 0x0000, 0x1234)
            request = _build_rtu_frame(0x01, pdu)
            os.write(slave_fd, request)

            response = _pty_read(slave_fd)
            os.close(slave_fd)

            assert len(response) >= 5
            assert response[1] == 0x85  # FC05 | 0x80
            assert response[2] == 0x03  # illegal data value

        finally:
            facade.stop()

    def test_fc05_write_then_read_back(self) -> None:
        """FC05 写入后通过 FC01 读回验证一致性。"""
        plan = _make_plan_with_coils()
        facade = create_modbus_rtu_driver_adapter(mode="rtu-lightweight")
        facade.load_points(plan)
        facade.start()

        try:
            slave_name = facade.slave_path
            slave_fd = os.open(slave_name, os.O_RDWR | os.O_NOCTTY)
            _setup_raw_pty(slave_fd)

            # Step 1: FC05 写入 coil_1 = ON
            pdu_w = struct.pack(">BHH", 0x05, 0x0001, 0xFF00)
            os.write(slave_fd, _build_rtu_frame(0x01, pdu_w))
            _pty_read(slave_fd)  # 读取 FC05 响应

            # 短暂等待确保帧被处理
            time.sleep(0.05)

            # Step 2: FC01 读回
            pdu_r = struct.pack(">BHH", 0x01, 0x0000, 0x0002)
            os.write(slave_fd, _build_rtu_frame(0x01, pdu_r))
            response = _pty_read(slave_fd)

            os.close(slave_fd)

            assert len(response) >= 5
            assert response[1] == 0x01  # FC01
            # coil_0 初始为 True, coil_1 写入为 True -> 0x03
            assert response[3] & 0x01 == 1  # coil_0 still ON
            assert response[3] & 0x02 == 2  # coil_1 now ON

        finally:
            facade.stop()


# ── FC15 Write Multiple Coils 测试 ───────────────────────────────────────────────


class TestModbusRtuFc15WriteMultipleCoils:
    """FC15 Write Multiple Coils PTY 通信测试。"""

    def test_fc15_write_multiple_coils_via_pty(self) -> None:
        """通过 PTY slave 发送 FC15 请求并验证响应。"""
        plan = _make_plan_with_coils()
        facade = create_modbus_rtu_driver_adapter(mode="rtu-lightweight")
        facade.load_points(plan)
        facade.start()

        try:
            slave_name = facade.slave_path
            slave_fd = os.open(slave_name, os.O_RDWR | os.O_NOCTTY)
            _setup_raw_pty(slave_fd)

            # FC15 写入 2 个线圈：bit0=OFF, bit1=ON
            pdu = (
                struct.pack(">BHH", 0x0F, 0x0000, 0x0002)
                + b"\x01"  # byte_count
                + b"\x02"  # coil_data: bit0=0, bit1=1
            )
            request = _build_rtu_frame(0x01, pdu)
            os.write(slave_fd, request)

            response = _pty_read(slave_fd)
            os.close(slave_fd)

            assert len(response) >= 8
            assert response[1] == 0x0F  # FC15
            # 响应 = echo start_addr + quantity
            resp_addr = struct.unpack(">H", response[2:4])[0]
            resp_qty = struct.unpack(">H", response[4:6])[0]
            assert resp_addr == 0x0000
            assert resp_qty == 0x0002

        finally:
            facade.stop()

    def test_fc15_write_then_read_back(self) -> None:
        """FC15 写入后通过 FC01 读回验证一致性。"""
        plan = _make_plan_with_coils()
        facade = create_modbus_rtu_driver_adapter(mode="rtu-lightweight")
        facade.load_points(plan)
        facade.start()

        try:
            slave_name = facade.slave_path
            slave_fd = os.open(slave_name, os.O_RDWR | os.O_NOCTTY)
            _setup_raw_pty(slave_fd)

            # Step 1: FC15 写入两个线圈均为 ON
            pdu_w = (
                struct.pack(">BHH", 0x0F, 0x0000, 0x0002)
                + b"\x01"  # byte_count
                + b"\x03"  # 两个 bit 均为 1
            )
            os.write(slave_fd, _build_rtu_frame(0x01, pdu_w))
            _pty_read(slave_fd)

            time.sleep(0.05)

            # Step 2: FC01 读回验证
            pdu_r = struct.pack(">BHH", 0x01, 0x0000, 0x0002)
            os.write(slave_fd, _build_rtu_frame(0x01, pdu_r))
            response = _pty_read(slave_fd)

            os.close(slave_fd)

            assert len(response) >= 5
            assert response[1] == 0x01
            # 两个线圈都应为 ON
            assert response[3] == 0x03  # bit0=1, bit1=1

        finally:
            facade.stop()

    def test_fc15_byte_count_mismatch(self) -> None:
        """FC15 byte_count 与数量不匹配应返回异常 0x03。"""
        plan = _make_plan_with_coils()
        facade = create_modbus_rtu_driver_adapter(mode="rtu-lightweight")
        facade.load_points(plan)
        facade.start()

        try:
            slave_name = facade.slave_path
            slave_fd = os.open(slave_name, os.O_RDWR | os.O_NOCTTY)
            _setup_raw_pty(slave_fd)

            # 请求 9 个线圈，byte_count=1（应为 2）
            pdu = (
                struct.pack(">BHH", 0x0F, 0x0000, 0x0009)
                + b"\x01"  # byte_count=1 (应为 2)
                + b"\x00"
            )
            request = _build_rtu_frame(0x01, pdu)
            os.write(slave_fd, request)

            response = _pty_read(slave_fd)
            os.close(slave_fd)

            assert len(response) >= 5
            assert response[1] == 0x8F  # FC15 | 0x80
            assert response[2] == 0x03  # illegal data value

        finally:
            facade.stop()


# ── FC16 Write Multiple Registers 测试 ───────────────────────────────────────────


class TestModbusRtuFc16WriteMultipleRegisters:
    """FC16 Write Multiple Registers PTY 通信测试。"""

    def test_fc16_write_multiple_registers_via_pty(self) -> None:
        """通过 PTY slave 发送 FC16 请求并验证响应。"""
        plan = _make_plan("rtu_fc16")
        facade = create_modbus_rtu_driver_adapter(mode="rtu-lightweight")
        facade.load_points(plan)
        facade.start()

        try:
            slave_name = facade.slave_path
            slave_fd = os.open(slave_name, os.O_RDWR | os.O_NOCTTY)
            _setup_raw_pty(slave_fd)

            # FC16 写入 2 个寄存器：addr 0=100, addr 1=200
            pdu = (
                struct.pack(">BHH", 0x10, 0x0000, 0x0002)
                + b"\x04"  # byte_count = 2 * 2 = 4
                + struct.pack(">HH", 100, 200)
            )
            request = _build_rtu_frame(0x01, pdu)
            os.write(slave_fd, request)

            response = _pty_read(slave_fd)
            os.close(slave_fd)

            assert len(response) >= 8
            assert response[1] == 0x10  # FC16
            resp_addr = struct.unpack(">H", response[2:4])[0]
            resp_qty = struct.unpack(">H", response[4:6])[0]
            assert resp_addr == 0x0000
            assert resp_qty == 0x0002

        finally:
            facade.stop()

    def test_fc16_write_then_read_back(self) -> None:
        """FC16 写入后通过 FC03 读回验证一致性。"""
        plan = _make_plan("rtu_fc16_readback")
        facade = create_modbus_rtu_driver_adapter(mode="rtu-lightweight")
        facade.load_points(plan)
        facade.start()

        try:
            slave_name = facade.slave_path
            slave_fd = os.open(slave_name, os.O_RDWR | os.O_NOCTTY)
            _setup_raw_pty(slave_fd)

            # Step 1: FC16 写入值
            pdu_w = (
                struct.pack(">BHH", 0x10, 0x0000, 0x0002)
                + b"\x04"
                + struct.pack(">HH", 777, 888)
            )
            os.write(slave_fd, _build_rtu_frame(0x01, pdu_w))
            _pty_read(slave_fd)

            time.sleep(0.05)

            # Step 2: FC03 读回
            pdu_r = struct.pack(">BHH", 0x03, 0x0000, 0x0002)
            os.write(slave_fd, _build_rtu_frame(0x01, pdu_r))
            response = _pty_read(slave_fd)

            os.close(slave_fd)

            assert len(response) >= 9
            assert response[1] == 0x03
            val0 = struct.unpack(">H", response[3:5])[0]
            val1 = struct.unpack(">H", response[5:7])[0]
            assert val0 == 777
            assert val1 == 888

        finally:
            facade.stop()

    def test_fc16_byte_count_mismatch(self) -> None:
        """FC16 byte_count 与数量不匹配应返回异常 0x03。"""
        plan = _make_plan("rtu_fc16_bcm")
        facade = create_modbus_rtu_driver_adapter(mode="rtu-lightweight")
        facade.load_points(plan)
        facade.start()

        try:
            slave_name = facade.slave_path
            slave_fd = os.open(slave_name, os.O_RDWR | os.O_NOCTTY)
            _setup_raw_pty(slave_fd)

            # 请求 2 个寄存器但 byte_count=2（应为 4）
            pdu = (
                struct.pack(">BHH", 0x10, 0x0000, 0x0002)
                + b"\x02"  # byte_count=2 (应为 4)
                + struct.pack(">H", 100)  # 仅 1 个寄存器值
            )
            request = _build_rtu_frame(0x01, pdu)
            os.write(slave_fd, request)

            response = _pty_read(slave_fd)
            os.close(slave_fd)

            assert len(response) >= 5
            assert response[1] == 0x90  # FC16 | 0x80
            assert response[2] == 0x03  # illegal data value

        finally:
            facade.stop()


# ── 数据区模型测试 ───────────────────────────────────────────────────────────────


class TestDataAreaModel:
    """数据区分类和映射测试。"""

    def test_health_reports_data_areas(self) -> None:
        """health() 应包含各数据区统计。"""
        plan = _make_plan_with_coils()
        facade = create_modbus_rtu_driver_adapter(mode="rtu-lightweight")
        facade.load_points(plan)
        h = facade.health()
        assert "data_areas" in h
        areas = h["data_areas"]
        assert areas["coils"] == 2
        assert areas["holding_registers"] == 1
        assert areas["discrete_inputs"] == 0
        assert areas["input_registers"] == 0

    def test_function_codes_in_health(self) -> None:
        """health() 应列出支持的功能码。"""
        plan = _make_plan_with_coils()
        facade = create_modbus_rtu_driver_adapter(mode="rtu-lightweight")
        facade.load_points(plan)
        h = facade.health()
        assert "function_codes" in h
        fcs = h["function_codes"]
        assert "FC01" in fcs
        assert "FC03" in fcs
        assert "FC06" in fcs
        assert "FC15" in fcs
        assert "FC16" in fcs

    def test_capabilities_include_fc_codes(self) -> None:
        """capabilities() 应包含 MODBUS_RTU 功能码声明。"""
        plan = _make_plan_with_coils()
        facade = create_modbus_rtu_driver_adapter(mode="rtu-lightweight")
        facade.load_points(plan)
        caps = facade.capabilities()
        assert "MODBUS_RTU_FC01" in caps
        assert "MODBUS_RTU_FC03" in caps
        assert "MODBUS_RTU_FC05" in caps
        assert "MODBUS_RTU_FC15" in caps
        assert "MODBUS_RTU_FC16" in caps

    def test_point_area_classification(self) -> None:
        """通过 variable_key 正确分类点位到数据区。"""
        plan = _make_plan_with_coils()
        facade = create_modbus_rtu_driver_adapter(mode="rtu-lightweight")
        facade.load_points(plan)
        assert facade._point_area.get("coil_0") == "coils"
        assert facade._point_area.get("coil_1") == "coils"
        assert facade._point_area.get("reg_a") == "holding_registers"

    def test_update_values_syncs_coil_state(self) -> None:
        """update_values 应同步更新线圈存储。"""
        plan = _make_plan_with_coils()
        facade = create_modbus_rtu_driver_adapter(mode="rtu-lightweight")
        facade.load_points(plan)
        # 初始状态 coil_0=True
        assert facade._coil_states.get("coil_0") is True
        # 更新
        facade.update_values({"coil_0": False})
        assert facade._coil_states.get("coil_0") is False


# ── Round 19 register_encoding 工具接入测试 ─────────────────────────────────


class TestModbusRtuRegisterEncodingIntegration:
    """ModbusRtuDriverAdapter 接入 register_encoding 工具的测试（Round 19 新增）。

    验证 facade 的 encode_register_value / decode_register_value 方法
    **真实调用** starfish.domain.protocols.modbus.register_encoding 工具，
    而非仅修改 capabilities 文案。
    """

    def test_encode_register_value_uint16_calls_tool(self) -> None:
        """encode_register_value(UINT16) 应真实调用 register_encoding 工具。"""
        facade = create_modbus_rtu_driver_adapter()
        # 真实调用 register_encoding 工具
        regs = facade.encode_register_value(
            0x1234,
            ModbusRegisterValueType.UINT16,
        )
        assert regs == [0x1234]

    def test_encode_register_value_uint32_little_little(self) -> None:
        """encode_register_value(UINT32, little, little) 应按工具规则编码。"""
        facade = create_modbus_rtu_driver_adapter()
        regs = facade.encode_register_value(
            0x01020304,
            ModbusRegisterValueType.UINT32,
            ByteOrder.LITTLE,
            WordOrder.LITTLE,
        )
        # 验证仅检查与工具一致性（不对硬编码值负责）
        from starfish.domain.protocols.modbus.register_encoding import encode_register_value
        expected = encode_register_value(
            0x01020304,
            ModbusRegisterValueType.UINT32,
            ByteOrder.LITTLE,
            WordOrder.LITTLE,
        )
        assert regs == expected

    def test_encode_register_value_float32(self) -> None:
        """encode_register_value(FLOAT32) 应能往返。"""
        facade = create_modbus_rtu_driver_adapter()
        regs = facade.encode_register_value(
            2.5,
            ModbusRegisterValueType.FLOAT32,
            ByteOrder.BIG,
            WordOrder.BIG,
        )
        assert len(regs) == 2
        val = facade.decode_register_value(
            regs,
            ModbusRegisterValueType.FLOAT32,
            ByteOrder.BIG,
            WordOrder.BIG,
        )
        assert val == 2.5

    def test_decode_register_value_consistency(self) -> None:
        """encode + decode 应真实回得原值。"""
        facade = create_modbus_rtu_driver_adapter()
        for value in [0, 1, 100, 32767, -32768]:
            regs = facade.encode_register_value(
                value,
                ModbusRegisterValueType.INT16,
            )
            decoded = facade.decode_register_value(
                regs,
                ModbusRegisterValueType.INT16,
            )
            assert decoded == value

    def test_encode_register_value_rejects_nan(self) -> None:
        """encode_register_value(FLOAT32, NaN) 应抛 ValueError。"""
        from starfish.domain.protocols.modbus.register_encoding import (
            RegisterEncodingValueError,
        )
        facade = create_modbus_rtu_driver_adapter()
        with pytest.raises(RegisterEncodingValueError):
            facade.encode_register_value(
                float("nan"),
                ModbusRegisterValueType.FLOAT32,
            )

    def test_register_encoding_capabilities_contains_required(self) -> None:
        """register_encoding_capabilities() 应包含 5 value_type + 2 byte_order + 2 word_order。"""
        facade = create_modbus_rtu_driver_adapter()
        caps = facade.register_encoding_capabilities()
        assert "supports_register_encoding=true" in caps
        assert "supports_typed_register_helpers=true" in caps
        # 5 value_type
        vt_line = [c for c in caps if c.startswith("supported_register_value_types=")][0]
        vt_count = len(vt_line.split("=")[1].split(","))
        assert vt_count == 5
        assert "uint16" in vt_line
        assert "int16" in vt_line
        assert "uint32" in vt_line
        assert "int32" in vt_line
        assert "float32" in vt_line
        # 2 byte_order
        bo_line = [c for c in caps if c.startswith("supported_byte_orders=")][0]
        assert "big" in bo_line
        assert "little" in bo_line
        # 2 word_order
        wo_line = [c for c in caps if c.startswith("supported_word_orders=")][0]
        assert "big" in wo_line
        assert "little" in wo_line
        # 不应声明真实现场设备验证
        assert "supports_register_encoding_runtime=false" in caps

    def test_register_encoding_does_not_modify_existing_facade_behavior(self) -> None:
        """register_encoding 接入不应修改 FC03/FC06 等基础帧行为。"""
        facade = create_modbus_rtu_driver_adapter()
        # 加载 plan 后 capabilities() 才会带 FC 列表（既有行为）
        plan = _make_plan()
        facade.load_points(plan)
        # 既有 capabilities() 不应改变（无 register_encoding 干扰）
        caps = facade.capabilities()
        # 既有 FC 列表不变
        assert "MODBUS_RTU_FC01" in caps
        assert "MODBUS_RTU_FC03" in caps
        assert "MODBUS_RTU_FC06" in caps
        assert "MODBUS_RTU_FC16" in caps
        # register_encoding 是独立方法
        reg_caps = facade.register_encoding_capabilities()
        assert "supports_register_encoding=true" in reg_caps
