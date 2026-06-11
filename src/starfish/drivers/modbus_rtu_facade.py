"""Starfish Modbus RTU 协议 PTY 轻量级 server facade。

本模块提供 Modbus RTU 协议的轻量级 PTY server 生命周期实现。
使用 Python 标准库 pty 创建 PTY pair，在 daemon 线程中从 master 端
读取 RTU 帧并响应以下功能码：

    FC01 Read Coils (位读取，最大 2000 线圈)
    FC02 Read Discrete Inputs (位读取，同 FC01 格式)
    FC03 Read Holding Registers (保持寄存器读取)
    FC04 Read Input Registers (输入寄存器读取)
    FC05 Write Single Coil (0xFF00=ON, 0x0000=OFF)
    FC06 Write Single Register (单寄存器写入)
    FC15 Write Multiple Coils (多位写入，位打包)
    FC16 Write Multiple Registers (多寄存器写入)

与 ModbusTcpFacade 的差异（链路层）：
    - TCP 版本：使用 MBAP 头部（7 字节），无 CRC。
    - RTU 版本：无 MBAP 头部，帧尾使用 CRC-16-IBM 校验。

帧格式：
    请求帧：[slave_id(1)][func_code(1)][data(N)][crc(2)]
    响应帧：同上格式

数据区模型（每个数据区有独立的地址空间，从 0 开始）：
    - coils:         bool 列表，位编址，FC01/FC05/FC15 可读写
    - discrete_inputs: bool 列表，位编址，FC02 只读
    - holding_registers: 16-bit int 列表，FC03/FC06/FC16 可读写
    - input_registers:   16-bit int 列表，FC04 只读

PTY 帧边界策略：
    RTU 规范要求帧间 3.5 字符间隔作为帧边界。但 PTY 是本地模拟，
    无真实串口时序。使用 time.sleep(0.05) 作为帧间分隔符，
    确保单次 read 能获取完整帧。这不代表真实串口时序。

能力边界：
    已实现: start() / stop() / health() / load_points() / read() / write()
    未实现: subscribe() / report()

Round 19 扩展（register_encoding 工具接入）：
    接入 ``starfish.protocols.modbus.register_encoding`` 工具子包，
    提供 ``encode_register_value`` / ``decode_register_value`` 公共
    API（在 facade 上以 ``encode_register_value`` /
    ``decode_register_value`` 形式暴露），支持 5 value_type × 4 byte/
    word 组合。FC01/FC02/FC03/FC04/FC05/FC06/FC15/FC16 等真实
    Modbus 帧行为**不**受影响（register_encoding 仅作为 CPU 辅助层，
    不修改 PTY 串口模拟器的基础协议帧读写）。capabilities 新增
    supports_register_encoding + supported_register_value_types +
    supported_byte_orders + supported_word_orders +
    supports_typed_register_helpers 字段。**不**声明真实现场 RS-232/
    RS-485 串口设备验证。

运行模式：
    - rtu-lightweight: PTY 可用时的轻量级 Modbus RTU server
      （不等同真实串口现场，仅用于本地验证）
    - codebase-pending: PTY 不可用时的 in-memory stub

安全边界：
    - 不得 import seahorse / whale.ingest / whale.shared.source。
    - 不连接生产数据库。
    - 所有数据标注 synthetic。
    - PTY 不等同真实串口现场，标注 "不等同真实串口现场"。
"""

from __future__ import annotations

import os
import pty
import struct
import threading
import time
from datetime import datetime, timezone
from typing import Any

from starfish.domain import StarfishServerPlan, StarfishPointPlan, UnsupportedOperation


def _crc16(data: bytes) -> int:
    """Modbus RTU 标准 CRC-16-IBM 计算。

    多项式：0xA001（0x8005 的反转）。
    初始值：0xFFFF。
    无最终异或。

    Args:
        data: 待计算 CRC 的字节串。

    Returns:
        16-bit CRC 值（低位在前格式，即 Modbus RTU 帧中使用的格式）。
    """
    crc = 0xFFFF
    for b in data:
        crc ^= b
        for _ in range(8):
            if crc & 0x0001:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return crc & 0xFFFF


def _build_rtu_frame(slave_id: int, pdu: bytes) -> bytes:
    """构造包含 CRC 校验的完整 Modbus RTU 帧。

    帧结构：[slave_id(1)][pdu(N)][crc(2)]

    Args:
        slave_id: 从站地址 (1-247)。
        pdu: 协议数据单元（功能码 + 数据）。

    Returns:
        完整 RTU 帧字节串。
    """
    header = struct.pack(">B", slave_id)
    payload = header + pdu
    crc = _crc16(payload)
    # CRC 在帧中为低位在前
    return payload + struct.pack("<H", crc)


def _parse_rtu_frame(data: bytes) -> tuple[int, int, bytes] | None:
    """解析 Modbus RTU 帧，提取 slave_id、功能码和 PDU 数据。

    帧结构：[slave_id(1)][func_code(1)][pdu_data(N)][crc(2)]
    最小帧长：4 字节（slave + func + crc）。

    Args:
        data: 原始 RTU 帧字节串（含 CRC）。

    Returns:
        (slave_id, function_code, pdu_data) 元组，或 None（帧无效或 CRC 失败）。
    """
    if len(data) < 4:
        return None
    slave_id = data[0]
    function_code = data[1]

    # 提取 CRC（最后 2 字节，低位在前）
    received_crc = struct.unpack("<H", data[-2:])[0]
    computed_crc = _crc16(data[:-2])

    if received_crc != computed_crc:
        return None

    # pdu_data 不包含 slave_id 和 crc，但包含 function_code
    # 注意：RTU PDU = function_code + remaining data（不含 slave_id 和 CRC）
    # 这里 pdu_data 从 function_code 开始
    pdu = data[1:-2]  # [func_code][pdu_data]

    return (slave_id, function_code, pdu[1:])  # pdu[1:] 是 func_code 后的数据


def _pack_bits(bits: list[int]) -> bytes:
    """将位列表打包为 Modbus 位字节串（每字节 LSB 先）。

    用于 FC01/FC02 响应的线圈/离散输入状态编码。

    Args:
        bits: 位值列表（0 或 1）。

    Returns:
        位打包后的字节串。
    """
    byte_count = (len(bits) + 7) // 8
    result = bytearray(byte_count)
    for i, bit in enumerate(bits):
        if bit:
            result[i // 8] |= (1 << (i % 8))
    return bytes(result)


def _unpack_bits(data: bytes, count: int) -> list[bool]:
    """从 Modbus 位打包字节串解包为布尔列表。

    用于 FC15 请求的线圈数据解析（每字节 LSB 先）。

    Args:
        data: 位打包的字节串。
        count: 有效位数。

    Returns:
        布尔值列表，长度为 count。
    """
    result: list[bool] = []
    for i in range(count):
        byte_idx = i // 8
        bit_idx = i % 8
        if byte_idx < len(data):
            result.append(bool(data[byte_idx] & (1 << bit_idx)))
        else:
            result.append(False)
    return result


def probe_modbus_rtu_binary() -> tuple[bool, str]:
    """探测 Modbus RTU PTY 轻量级实现可用性。

    探测步骤：
        1. 检查 pty 模块是否可用。
        2. 尝试创建 PTY pair 验证 PTY 创建能力。

    Returns:
        (True, reason) 当 PTY 可用时。
        (False, reason) 当 PTY 不可用时。
    """
    """探测 Modbus RTU PTY 轻量级实现可用性。

    探测步骤：
        1. 检查 pty 模块是否可用。
        2. 尝试创建 PTY pair 验证 PTY 创建能力。

    Returns:
        (True, reason) 当 PTY 可用时。
        (False, reason) 当 PTY 不可用时。
    """
    try:
        import pty as _pty
        # 尝试创建 PTY pair 验证 pty 是否真正可用
        master_fd, slave_fd = _pty.openpty()
        os.close(master_fd)
        os.close(slave_fd)
        return (
            True,
            "MODBUS_RTU PTY lightweight mode 可用 "
            "(local PTY simulation, 不等同真实串口)。"
            "注：PTY 不等同真实串口现场，"
            "无真实 RS-232/RS-485 电气特性和时序。",
        )
    except (ImportError, OSError, AttributeError) as exc:
        return (
            False,
            f"MODBUS_RTU 当前不可用: PTY 创建失败 ({exc})。状态：codebase-pending",
        )


class ModbusRtuFacade:
    """Modbus RTU 协议轻量级 PTY server facade。

    使用 pty.openpty() 创建 PTY pair，在 daemon 线程中从 master 端
    读取 RTU 帧并响应 FC01-FC06、FC15、FC16。

    支持的功能码：
        FC01 Read Coils, FC02 Read Discrete Inputs,
        FC03 Read Holding Registers, FC04 Read Input Registers,
        FC05 Write Single Coil, FC06 Write Single Register,
        FC15 Write Multiple Coils, FC16 Write Multiple Registers。

    PTY 不等同真实串口：
        - 无 RS-232/RS-485 电平、波特率、奇偶校验、停止位等物理层特性。
        - 帧间 3.5 字符间隔通过 time.sleep(0.05) 模拟，无真实串口时序。
        - 仅用于本地功能验证，不能替代真实串口现场测试。

    数据区映射策略：
        通过 StarfishPointPlan.variable_key 字段判定点位所属数据区：
        - "coils" / "coil" -> coils 区
        - "discrete_inputs" / "discrete" -> discrete_inputs 区
        - "input_registers" / "input_reg" -> input_registers 区
        - 默认 -> holding_registers 区（与 Round 13 兼容）
        每个数据区内按 point_id 字典序排序分配从 0 开始的地址。

    不负责：真实串口配置、浮点/32-bit 寄存器编解码、多从站 ID 支持、
    广播地址（0x00）处理。

    Attributes:
        _plan: 已加载的 StarfishServerPlan。
        _mode: 运行模式 ("rtu-lightweight" 或 "codebase-pending")。
        _started: 是否已调用 start()。
        _values: 内存点位值存储 (point_id -> value)，holding 区。
        _started_at: start() 调用时间。
        _reg_map: point_id -> holding register_address 映射。
        _reg_rev: holding register_address -> point_id 反向映射。
        _point_area: point_id -> 数据区名 映射。
        _coil_addr / _di_addr / _ir_addr: 各数据区 point_id -> 区内地址。
        _coil_states: 线圈状态存储 (point_id -> bool)。
        _di_states: 离散输入状态存储 (point_id -> bool)。
        _slave_id: RTU 从站地址（默认 1）。
        _master_fd: PTY master 端文件描述符。
        _slave_name: PTY slave 端路径（如 /dev/pts/N）。
        _thread: RTU 帧读取 daemon 线程。
        _stop_event: 停止信号。
        _lock: 线程安全锁（_values / _coil_states / _di_states 读写保护）。
    """

    def __init__(
        self,
        slave_id: int = 1,
        mode: str = "rtu-lightweight",
    ) -> None:
        self._plan: StarfishServerPlan | None = None
        self._mode: str = mode
        self._started: bool = False
        self._values: dict[str, Any] = {}
        self._started_at: datetime | None = None
        self._slave_id: int = slave_id

        # 寄存器地址映射（holding registers 区，兼容 Round 13）
        self._reg_map: dict[str, int] = {}
        self._reg_rev: dict[int, str] = {}

        # 数据区分类（point_id -> area_name）
        # area_name: "coils" / "discrete_inputs" / "holding_registers" /
        #             "input_registers"
        self._point_area: dict[str, str] = {}

        # 各数据区的 point_id -> 区内地址 映射
        self._coil_addr: dict[str, int] = {}
        self._coil_addr_rev: dict[int, str] = {}
        self._di_addr: dict[str, int] = {}
        self._di_addr_rev: dict[int, str] = {}
        self._ir_addr: dict[str, int] = {}
        self._ir_addr_rev: dict[int, str] = {}

        # 线圈和离散输入的值存储（bool）
        self._coil_states: dict[str, bool] = {}
        self._di_states: dict[str, bool] = {}

        # PTY 资源
        self._master_fd: int | None = None
        self._slave_fd: int | None = None
        self._slave_name: str = ""
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()

        # 线程安全锁（_values / _coil_states / _di_states 读写保护）
        self._lock = threading.Lock()

    # ── 属性 ──────────────────────────────────────────────────────────────────

    @property
    def protocol(self) -> str:
        """返回归一化协议名。"""
        return "MODBUS_RTU"

    @property
    def mode(self) -> str:
        """返回运行模式。

        - "rtu-lightweight": PTY 可用时的轻量级 Modbus RTU server。
        - "codebase-pending": PTY 不可用时的 in-memory stub。
        """
        return self._mode

    @property
    def slave_path(self) -> str:
        """返回 slave PTY 路径（如 /dev/pts/N），供客户端连接。

        仅在已启动且 PTY 创建成功后有值。
        """
        return self._slave_name

    # ── 生命周期 ──────────────────────────────────────────────────────────────

    def start(self) -> None:
        """启动 Modbus RTU PTY server。

        使用 pty.openpty() 创建 master/slave PTY pair，
        在 daemon 线程中从 master 端读取 RTU 帧并响应。

        重复调用安全（幂等）。
        codebase-pending 模式仅设置内存状态不启动 PTY。

        Raises:
            OSError: PTY pair 创建失败。
        """
        if self._started:
            return

        if self._mode == "codebase-pending":
            self._started = True
            self._started_at = datetime.now(timezone.utc)
            return

        master_fd, slave_fd = pty.openpty()
        slave_name = os.ttyname(slave_fd)

        # 设置 master_fd 为非阻塞，避免 os.read() 永久阻塞 daemon 线程
        import fcntl
        flags = fcntl.fcntl(master_fd, fcntl.F_GETFL)
        fcntl.fcntl(master_fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

        self._master_fd = master_fd
        self._slave_name = slave_name
        # slave_fd 保留打开状态，使 slave PTY 设备持续存在。
        # 客户端应打开 slave_name 路径来连接。
        # 注意：slave_fd 在 stop() 时关闭。
        self._slave_fd = slave_fd
        self._stop_event.clear()

        thread = threading.Thread(target=self._read_loop, daemon=True)
        thread.start()
        self._thread = thread
        self._started = True
        self._started_at = datetime.now(timezone.utc)

    def stop(self) -> None:
        """停止 Modbus RTU PTY server。

        设置停止信号，关闭 PTY fd（master 和 slave），等待线程结束。
        不删除已加载的 plan 和 values。
        重复调用安全（幂等）。
        """
        if not self._started:
            return

        self._stop_event.set()

        # 关闭 master fd
        if self._master_fd is not None:
            try:
                os.close(self._master_fd)
            except OSError:
                pass
            self._master_fd = None

        # 关闭 slave fd
        if self._slave_fd is not None:
            try:
                os.close(self._slave_fd)
            except OSError:
                pass
            self._slave_fd = None

        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None

        self._slave_name = ""
        self._started = False

    # ── 可观测性 ──────────────────────────────────────────────────────────────

    def health(self) -> dict[str, Any]:
        """返回当前 facade 的可观测健康状态。

        检查 PTY fd 是否有效。codebase-pending 模式始终报告 running=False。
        包含各数据区点位统计。

        Returns:
            包含 health 信息的 dict。
        """
        pty_ok = False
        if self._master_fd is not None and self._started:
            try:
                os.fstat(self._master_fd)
                pty_ok = True
            except OSError:
                pass

        result: dict[str, Any] = {
            "status": "started" if self._started else "stopped",
            "plan_loaded": self._plan is not None,
            "point_count": len(self._plan.points) if self._plan else 0,
            "endpoint_count": len(self._plan.endpoints) if self._plan else 0,
            "capabilities": list(self._plan.capabilities) if self._plan else [],
            "started_at": self._started_at.isoformat() if self._started_at else None,
            "synthetic": self._plan.synthetic if self._plan else True,
            "protocol": self.protocol,
            "mode": self._mode,
            "running": pty_ok if self._mode == "rtu-lightweight" else False,
            "function_codes": [
                "FC01", "FC02", "FC03", "FC04", "FC05", "FC06",
                "FC15", "FC16",
            ],
            "data_areas": {
                "coils": len(self._coil_states),
                "discrete_inputs": len(self._di_states),
                "holding_registers": len(self._reg_map),
                "input_registers": len(self._ir_addr),
            },
        }
        if self._slave_name:
            result["slave_path"] = self._slave_name
        if self._mode == "rtu-lightweight":
            result["note"] = (
                "PTY 不等同真实串口现场，"
                "无真实 RS-232/RS-485 电气特性和时序"
            )
        return result

    # ── 数据操作 ──────────────────────────────────────────────────────────────

    def load_points(self, plan: StarfishServerPlan) -> None:
        """从 StarfishServerPlan 加载点位定义和初始值。

        按 variable_key 判定各点位所属数据区，
        在每个数据区内按 point_id 字典序排序分配从 0 开始的地址。

        Args:
            plan: 已加载并校验的 StarfishServerPlan。
        """
        self._plan = plan
        with self._lock:
            self._values = dict(plan.initial_values)
            # 初始化线圈和离散输入存储（从初始值中提取布尔值）
            self._coil_states.clear()
            self._di_states.clear()
        self._build_register_map(plan)
        # 从 initial_values 初始化线圈和离散输入
        for pid, val in plan.initial_values.items():
            area = self._point_area.get(pid, "holding_registers")
            if area == "coils":
                self._coil_states[pid] = bool(val)
            elif area == "discrete_inputs":
                self._di_states[pid] = bool(val)

    def _classify_point_area(self, point: StarfishPointPlan) -> str:
        """根据 StarfishPointPlan 的 variable_key 判定点位所属数据区。

        映射规则（大小写不敏感）：
            - variable_key 含 "coils" / "coil" -> coils
            - variable_key 含 "discrete_inputs" / "discrete" -> discrete_inputs
            - variable_key 含 "input_registers" / "input_reg" -> input_registers
            - 其他（含空字符串） -> holding_registers（默认，兼容 Round 13）

        Args:
            point: StarfishPointPlan 实例。

        Returns:
            数据区名字符串。
        """
        vk = (point.variable_key or "").lower()
        if "coil" in vk:
            return "coils"
        if "discrete" in vk:
            return "discrete_inputs"
        if "input_reg" in vk:
            return "input_registers"
        return "holding_registers"

    def _build_register_map(self, plan: StarfishServerPlan) -> None:
        """构建全数据区 point_id <-> address 双向映射。

        对每个数据区的点按 point_id 字典序排序，索引即为区内地址。
        此映射在 load_points 时确定，确保重复加载结果一致。

        数据区映射策略：
            - coils: 可读写，FC01/FC05/FC15
            - discrete_inputs: 只读，FC02
            - holding_registers: 可读写，FC03/FC06/FC16
            - input_registers: 只读，FC04
        """
        # 分类点位（从 plan.points 获取元数据）
        point_area: dict[str, str] = {}
        for pt in plan.points:
            point_area[pt.point_id] = self._classify_point_area(pt)
        self._point_area = point_area

        # 兼容处理：initial_values 中可能包含 plan.points 之外的点位 ID
        # （如测试中单独指定 initial_values 而未更新 points 列表）。
        # 此类点位默认归属于 holding_registers 区。
        for pid in plan.initial_values:
            if pid not in point_area:
                point_area[pid] = "holding_registers"

        # 按数据区分组排序
        area_points: dict[str, list[str]] = {
            "coils": [], "discrete_inputs": [],
            "holding_registers": [], "input_registers": [],
        }
        for pid, area in point_area.items():
            if area in area_points:
                area_points[area].append(pid)

        # 构建各区映射
        for area_key, addr_map_attr, rev_map_attr in [
            ("coils", "_coil_addr", "_coil_addr_rev"),
            ("discrete_inputs", "_di_addr", "_di_addr_rev"),
            ("holding_registers", "_reg_map", "_reg_rev"),
            ("input_registers", "_ir_addr", "_ir_addr_rev"),
        ]:
            pids = sorted(area_points[area_key])
            addr_map: dict[str, int] = {}
            rev_map: dict[int, str] = {}
            for i, pid in enumerate(pids):
                addr_map[pid] = i
                rev_map[i] = pid
            setattr(self, addr_map_attr, addr_map)
            setattr(self, rev_map_attr, rev_map)

    def read(self, point_ids: list[str] | None = None) -> dict[str, Any]:
        """从内存读取当前点位值。

        线程安全：使用内部锁保护 _values dict。

        Args:
            point_ids: 要读取的点位 ID 列表，None 表示全部。

        Returns:
            point_id -> 当前值 的 dict。不存在的点位置为 None。
        """
        with self._lock:
            if point_ids is None:
                return dict(self._values)
            return {pid: self._values.get(pid) for pid in point_ids}

    def write(self, point_id: str, value: Any) -> None:
        """写入单个点位值到内存存储（等同于 FC06 写入效果）。

        rtu-lightweight 模式：直接更新内部 _values 存储。
        codebase-pending 模式：抛出 UnsupportedOperation。

        Args:
            point_id: 目标点位 ID。
            value: 要写入的值。

        Raises:
            KeyError: point_id 不在已加载的点位集合中。
            UnsupportedOperation: codebase-pending 模式下未实现。
        """
        if self._mode == "codebase-pending":
            raise UnsupportedOperation(
                "write",
                "ModbusRtuFacade.write 尚未实现（codebase-pending 模式），"
                "待 Modbus RTU PTY 链路可用后实现",
            )

        with self._lock:
            if point_id not in self._values:
                raise KeyError(
                    f"点位 '{point_id}' 未在已加载的 initial_values 中找到。"
                    f"可用点位: {sorted(self._values.keys())}"
                )
            self._values[point_id] = value

    def update_values(self, values: dict[str, Any]) -> None:
        """批量更新点位值到内存存储。

        线程安全。与 write 共享同一 _values 存储。
        同时同步更新关联数据区（coils / discrete_inputs）的值。

        Args:
            values: point_id -> 新值 的 dict。
        """
        with self._lock:
            self._values.update(values)
            for pid, val in values.items():
                area = self._point_area.get(pid, "holding_registers")
                if area == "coils":
                    self._coil_states[pid] = bool(val)
                elif area == "discrete_inputs":
                    self._di_states[pid] = bool(val)

    def capabilities(self) -> list[str]:
        """返回当前 facade 的能力声明列表。

        当 plan 已加载时返回 plan 声明的能力 + MODBUS_RTU 功能码列表。
        未加载 plan 时返回空列表（兼容 Round 13 行为）。

        Returns:
            能力声明字符串列表，未加载时返回空列表。
        """
        if self._plan is None:
            return []
        caps: list[str] = list(self._plan.capabilities)
        caps.extend([
            "MODBUS_RTU_FC01", "MODBUS_RTU_FC02", "MODBUS_RTU_FC03",
            "MODBUS_RTU_FC04", "MODBUS_RTU_FC05", "MODBUS_RTU_FC06",
            "MODBUS_RTU_FC15", "MODBUS_RTU_FC16",
        ])
        return caps

    # ── Register encoding 工具接入（Round 19 新增）────────────────────────────

    def encode_register_value(
        self,
        value: int | float,
        value_type: Any,
        byte_order: Any = None,
        word_order: Any = None,
    ) -> list[int]:
        """将值编码为 16-bit 寄存器列表（Modbus 寄存器值）。

        接入 ``starfish.protocols.modbus.register_encoding.encode_register_value``
        工具。本 facade 不修改 FC01/FC02/FC03/FC04/FC05/FC06/FC15/FC16
        等真实 Modbus RTU 帧行为，仅在 CPU 层提供 32-bit / float32
        register encoding 辅助。**不**接入真实 RS-232/RS-485 串口
        现场验证。

        Args:
            value: 待编码值（int 或 float）。
            value_type: ``ModbusRegisterValueType`` 枚举。
            byte_order: ``ByteOrder`` 枚举（默认 big-endian）。
            word_order: ``WordOrder`` 枚举（默认 big-endian）。

        Returns:
            ``list[int]``：16-bit 寄存器值列表。

        Raises:
            见 ``register_encoding.encode_register_value``。
        """
        from starfish.protocols.modbus.register_encoding import (
            ByteOrder as _ByteOrder,
            WordOrder as _WordOrder,
            encode_register_value as _encode,
        )
        if byte_order is None:
            byte_order = _ByteOrder.BIG
        if word_order is None:
            word_order = _WordOrder.BIG
        return _encode(
            value=value,
            value_type=value_type,
            byte_order=byte_order,
            word_order=word_order,
        )

    def decode_register_value(
        self,
        registers: list[int],
        value_type: Any,
        byte_order: Any = None,
        word_order: Any = None,
    ) -> int | float:
        """从 16-bit 寄存器列表解码为值（int 或 float）。

        接入 ``starfish.protocols.modbus.register_encoding.decode_register_value``
        工具。

        Args:
            registers: 16-bit 寄存器值列表。
            value_type: ``ModbusRegisterValueType`` 枚举。
            byte_order: ``ByteOrder`` 枚举（默认 big-endian）。
            word_order: ``WordOrder`` 枚举（默认 big-endian）。

        Returns:
            - int：当 ``value_type`` 为 UINT16/INT16/UINT32/INT32。
            - float：当 ``value_type`` 为 FLOAT32。

        Raises:
            见 ``register_encoding.decode_register_value``。
        """
        from starfish.protocols.modbus.register_encoding import (
            ByteOrder as _ByteOrder,
            WordOrder as _WordOrder,
            decode_register_value as _decode,
        )
        if byte_order is None:
            byte_order = _ByteOrder.BIG
        if word_order is None:
            word_order = _WordOrder.BIG
        return _decode(
            registers=registers,
            value_type=value_type,
            byte_order=byte_order,
            word_order=word_order,
        )

    def register_encoding_capabilities(self) -> list[str]:
        """返回 register_encoding 工具的能力声明（Round 19 新增）。

        包含 supports_register_encoding / supported_register_value_types /
        supported_byte_orders / supported_word_orders / supports_typed_
        register_helpers 字段。**不**声明真实现场 RS-232/RS-485 串口
        设备验证。

        Returns:
            register_encoding 能力声明字符串列表。
        """
        from starfish.protocols.modbus.register_encoding import (
            ByteOrder, ModbusRegisterValueType, WordOrder,
        )
        value_types = ",".join(vt.value for vt in ModbusRegisterValueType)
        byte_orders = ",".join(bo.value for bo in ByteOrder)
        word_orders = ",".join(wo.value for wo in WordOrder)
        return [
            "supports_register_encoding=true",
            f"supported_register_value_types={value_types}",
            f"supported_byte_orders={byte_orders}",
            f"supported_word_orders={word_orders}",
            "supports_typed_register_helpers=true",
            "supports_register_encoding_runtime=false",
        ]

    # ── NOT_IMPLEMENTED 操作 ──────────────────────────────────────────────────

    def subscribe(self, point_ids: list[str]) -> None:
        """订阅点位数据变更通知 —— 当前未实现。

        Modbus RTU 协议本身不支持服务端主动推送通知。

        Args:
            point_ids: 要订阅的点位 ID 列表。

        Raises:
            UnsupportedOperation: 订阅操作尚未实现。
        """
        raise UnsupportedOperation(
            "subscribe",
            "ModbusRtuFacade.subscribe 尚未实现，"
            "Modbus RTU 协议不支持服务端主动推送，需通过轮询替代",
        )

    def report(self) -> dict[str, Any]:
        """上报当前门面状态摘要 —— 当前未实现。

        Raises:
            UnsupportedOperation: report 操作尚未实现。
        """
        raise UnsupportedOperation(
            "report",
            "ModbusRtuFacade.report 尚未实现，"
            "待后续轮次实现结构化 telemetry report",
        )

    # ── PTY RTU 帧处理（内部）─────────────────────────────────────────────────

    def _read_loop(self) -> None:
        """PTY master 端读取循环。

        在 daemon 线程中运行。持续从 master_fd 读取 RTU 帧字节，
        对完整帧解析并生成响应，通过 master_fd 写回。

        因为 PTY 是双向的，对 master 写入的数据会出现在 slave 端。
        对 slave 写入的数据会出现在 master 端。
        """
        assert self._master_fd is not None
        buf = b""

        while not self._stop_event.is_set():
            try:
                data = os.read(self._master_fd, 4096)
                if not data:
                    break  # PTY 已关闭
            except BlockingIOError:
                # 非阻塞模式下暂无数据，稍作休眠后重试
                time.sleep(0.01)
                if self._stop_event.is_set():
                    return
                continue
            except OSError:
                if self._stop_event.is_set():
                    return
                continue

            buf += data

            # RTU 帧处理：尝试从缓冲区中提取完整帧
            # 最小帧长：slave(1) + func(1) + crc(2) = 4 字节
            while len(buf) >= 4:
                # 尝试解析以 buf[0] 为 slave_id 的帧
                # 先通过 CRC 探测帧边界
                parsed = self._try_extract_frame(buf)
                if parsed is None:
                    # 如果无法提取完整帧，等待更多数据
                    # 但若缓冲区过长仍无法匹配，丢弃首字节
                    if len(buf) > 512:
                        buf = buf[1:]
                    else:
                        break
                else:
                    frame, response = parsed
                    if response:
                        try:
                            os.write(self._master_fd, response)
                        except OSError:
                            return
                    buf = buf[len(frame):]

    def _try_extract_frame(self, data: bytes) -> tuple[bytes, bytes] | None:
        """尝试从字节串中提取一个完整 RTU 帧并生成响应。

        对可能的帧长度（最小 4 字节）逐一尝试 CRC 验证，
        找到第一个 CRC 验证通过的帧。

        Args:
            data: 缓冲区字节串。

        Returns:
            (consumed_bytes, response_bytes) 元组，或 None（无法提取）。
            response_bytes 可为空（无响应或异常帧不回复）。
        """
        # RTU 帧最小 4 字节，最大 256 字节
        max_len = min(len(data), 256)
        for frame_len in range(4, max_len + 1):
            test_frame = data[:frame_len]
            if len(test_frame) < 4:
                continue
            received_crc = struct.unpack("<H", test_frame[-2:])[0]
            computed_crc = _crc16(test_frame[:-2])
            if received_crc == computed_crc:
                # 有效帧，解析并生成响应
                response = self._handle_rtu_request(test_frame)
                return (test_frame, response)
        return None

    def _handle_rtu_request(self, frame: bytes) -> bytes:
        """处理完整 RTU 请求帧并生成响应。

        解析 slave_id、功能码，分发到对应处理器。

        支持功能码: FC01-FC06, FC15, FC16。

        Args:
            frame: 完整 RTU 请求帧。

        Returns:
            RTU 响应帧字节串，异常或无效请求返回空 bytes（静默忽略）。
        """
        if len(frame) < 4:
            return b""

        slave_id = frame[0]
        function_code = frame[1]
        pdu_data = frame[2:-2]  # 功能码后的数据，不含 slave_id 和 CRC

        handlers = {
            0x01: self._handle_rtu_fc01,
            0x02: self._handle_rtu_fc02,
            0x03: self._handle_rtu_fc03,
            0x04: self._handle_rtu_fc04,
            0x05: self._handle_rtu_fc05,
            0x06: self._handle_rtu_fc06,
            0x0F: self._handle_rtu_fc15,
            0x10: self._handle_rtu_fc16,
        }

        handler = handlers.get(function_code)
        if handler is not None:
            return handler(slave_id, pdu_data)
        # 不支持的功能码：返回异常响应
        return self._build_rtu_exception(slave_id, function_code, 0x01)

    def _handle_rtu_fc03(self, slave_id: int, pdu_data: bytes) -> bytes:
        """处理 RTU FC03（Read Holding Registers）请求。

        请求 PDU：[start_addr(2)][quantity(2)]
        响应 PDU：[fc03(1)][byte_count(1)][reg_values(N)]

        Args:
            slave_id: 从站地址。
            pdu_data: PDU 数据（功能码后的 4 字节）。

        Returns:
            RTU 响应帧。
        """
        if len(pdu_data) < 4:
            return self._build_rtu_exception(slave_id, 0x03, 0x02)

        start_addr = struct.unpack(">H", pdu_data[0:2])[0]
        quantity = struct.unpack(">H", pdu_data[2:4])[0]

        if quantity < 1 or quantity > 125:
            return self._build_rtu_exception(slave_id, 0x03, 0x03)

        # 从内存读取寄存器值
        registers: list[int] = []
        with self._lock:
            for offset in range(quantity):
                reg_addr = start_addr + offset
                point_id = self._reg_rev.get(reg_addr)
                if point_id is not None and point_id in self._values:
                    v = self._values[point_id]
                    if isinstance(v, bool):
                        reg = 1 if v else 0
                    elif isinstance(v, (int, float)):
                        reg = int(v) & 0xFFFF
                    else:
                        reg = 0
                else:
                    reg = 0
                registers.append(reg)

        # 构造 FC03 响应 PDU：功能码 + 字节数 + 寄存器值
        byte_count = len(registers) * 2
        pdu = struct.pack(">BB", 0x03, byte_count)
        for reg in registers:
            pdu += struct.pack(">H", reg)

        return _build_rtu_frame(slave_id, pdu)

    def _handle_rtu_fc06(self, slave_id: int, pdu_data: bytes) -> bytes:
        """处理 RTU FC06（Write Single Register）请求。

        请求 PDU：[reg_addr(2)][reg_value(2)]
        响应 PDU：回显请求（[fc06(1)][reg_addr(2)][reg_value(2)]）

        Args:
            slave_id: 从站地址。
            pdu_data: PDU 数据（功能码后的 4 字节）。

        Returns:
            RTU 响应帧（回显请求）。
        """
        if len(pdu_data) < 4:
            return self._build_rtu_exception(slave_id, 0x06, 0x02)

        reg_addr = struct.unpack(">H", pdu_data[0:2])[0]
        reg_value = struct.unpack(">H", pdu_data[2:4])[0]

        # 更新内部存储
        with self._lock:
            point_id = self._reg_rev.get(reg_addr)
            if point_id is not None:
                self._values[point_id] = reg_value

        # FC06 响应 = 回显请求（PDU = func_code + addr + value）
        pdu = struct.pack(">BHH", 0x06, reg_addr, reg_value)
        return _build_rtu_frame(slave_id, pdu)

    def _handle_rtu_fc01(self, slave_id: int, pdu_data: bytes) -> bytes:
        """处理 RTU FC01（Read Coils）请求。

        请求 PDU：[start_addr(2)][quantity(2)]
        响应 PDU：[fc01(1)][byte_count(1)][coil_status(N)]，位打包，LSB 优先。

        Args:
            slave_id: 从站地址。
            pdu_data: PDU 数据（4 字节：起始地址 + 数量）。

        Returns:
            RTU 响应帧。
        """
        if len(pdu_data) < 4:
            return self._build_rtu_exception(slave_id, 0x01, 0x02)

        start_addr = struct.unpack(">H", pdu_data[0:2])[0]
        quantity = struct.unpack(">H", pdu_data[2:4])[0]

        if quantity < 1 or quantity > 2000:
            return self._build_rtu_exception(slave_id, 0x01, 0x03)

        # 越界检查：请求的最后一个线圈地址应在已定义线圈范围内
        with self._lock:
            max_addr = len(self._coil_addr_rev) - 1
        if start_addr + quantity - 1 > max_addr and max_addr >= 0:
            return self._build_rtu_exception(slave_id, 0x01, 0x02)

        # 读取线圈状态
        coil_bits: list[int] = []
        with self._lock:
            for offset in range(quantity):
                addr = start_addr + offset
                pid = self._coil_addr_rev.get(addr)
                if pid is not None:
                    coil_bits.append(1 if self._coil_states.get(pid, False) else 0)
                else:
                    coil_bits.append(0)

        # 位打包
        packed = _pack_bits(coil_bits)
        pdu = struct.pack(">BB", 0x01, len(packed)) + packed
        return _build_rtu_frame(slave_id, pdu)

    def _handle_rtu_fc02(self, slave_id: int, pdu_data: bytes) -> bytes:
        """处理 RTU FC02（Read Discrete Inputs）请求。

        与 FC01 格式相同，但读取离散输入区（只读）。
        请求 PDU：[start_addr(2)][quantity(2)]

        Args:
            slave_id: 从站地址。
            pdu_data: PDU 数据（4 字节：起始地址 + 数量）。

        Returns:
            RTU 响应帧。
        """
        if len(pdu_data) < 4:
            return self._build_rtu_exception(slave_id, 0x02, 0x02)

        start_addr = struct.unpack(">H", pdu_data[0:2])[0]
        quantity = struct.unpack(">H", pdu_data[2:4])[0]

        if quantity < 1 or quantity > 2000:
            return self._build_rtu_exception(slave_id, 0x02, 0x03)

        with self._lock:
            max_addr = len(self._di_addr_rev) - 1
        if start_addr + quantity - 1 > max_addr and max_addr >= 0:
            return self._build_rtu_exception(slave_id, 0x02, 0x02)

        # 读取离散输入状态
        di_bits: list[int] = []
        with self._lock:
            for offset in range(quantity):
                addr = start_addr + offset
                pid = self._di_addr_rev.get(addr)
                if pid is not None:
                    di_bits.append(1 if self._di_states.get(pid, False) else 0)
                else:
                    di_bits.append(0)

        packed = _pack_bits(di_bits)
        pdu = struct.pack(">BB", 0x02, len(packed)) + packed
        return _build_rtu_frame(slave_id, pdu)

    def _handle_rtu_fc04(self, slave_id: int, pdu_data: bytes) -> bytes:
        """处理 RTU FC04（Read Input Registers）请求。

        与 FC03 格式相同，但读取输入寄存器区（只读）。
        请求 PDU：[start_addr(2)][quantity(2)]

        Args:
            slave_id: 从站地址。
            pdu_data: PDU 数据（4 字节：起始地址 + 数量）。

        Returns:
            RTU 响应帧。
        """
        if len(pdu_data) < 4:
            return self._build_rtu_exception(slave_id, 0x04, 0x02)

        start_addr = struct.unpack(">H", pdu_data[0:2])[0]
        quantity = struct.unpack(">H", pdu_data[2:4])[0]

        if quantity < 1 or quantity > 125:
            return self._build_rtu_exception(slave_id, 0x04, 0x03)

        registers: list[int] = []
        with self._lock:
            for offset in range(quantity):
                addr = start_addr + offset
                pid = self._ir_addr_rev.get(addr)
                if pid is not None and pid in self._values:
                    v = self._values[pid]
                    if isinstance(v, bool):
                        reg = 1 if v else 0
                    elif isinstance(v, (int, float)):
                        reg = int(v) & 0xFFFF
                    else:
                        reg = 0
                else:
                    reg = 0
                registers.append(reg)

        byte_count = len(registers) * 2
        pdu = struct.pack(">BB", 0x04, byte_count)
        for reg in registers:
            pdu += struct.pack(">H", reg)

        return _build_rtu_frame(slave_id, pdu)

    def _handle_rtu_fc05(self, slave_id: int, pdu_data: bytes) -> bytes:
        """处理 RTU FC05（Write Single Coil）请求。

        请求 PDU：[coil_addr(2)][coil_value(2)]
        coil_value: 0xFF00 = ON, 0x0000 = OFF。
        响应 PDU：回显请求。

        Args:
            slave_id: 从站地址。
            pdu_data: PDU 数据（4 字节：地址 + 值）。

        Returns:
            RTU 响应帧（回显）。
        """
        if len(pdu_data) < 4:
            return self._build_rtu_exception(slave_id, 0x05, 0x02)

        coil_addr = struct.unpack(">H", pdu_data[0:2])[0]
        coil_value = struct.unpack(">H", pdu_data[2:4])[0]

        if coil_value not in (0x0000, 0xFF00):
            return self._build_rtu_exception(slave_id, 0x05, 0x03)

        with self._lock:
            pid = self._coil_addr_rev.get(coil_addr)
            if pid is not None:
                self._coil_states[pid] = (coil_value == 0xFF00)
            else:
                return self._build_rtu_exception(slave_id, 0x05, 0x02)

        # FC05 响应 = 回显请求
        pdu = struct.pack(">BHH", 0x05, coil_addr, coil_value)
        return _build_rtu_frame(slave_id, pdu)

    def _handle_rtu_fc15(self, slave_id: int, pdu_data: bytes) -> bytes:
        """处理 RTU FC15（Write Multiple Coils）请求。

        请求 PDU：[start_addr(2)][quantity(2)][byte_count(1)][coil_data(N)]
        响应 PDU：[start_addr(2)][quantity(2)]（echo 起始地址和数量）。

        Args:
            slave_id: 从站地址。
            pdu_data: PDU 数据。

        Returns:
            RTU 响应帧。
        """
        if len(pdu_data) < 5:
            return self._build_rtu_exception(slave_id, 0x0F, 0x02)

        start_addr = struct.unpack(">H", pdu_data[0:2])[0]
        quantity = struct.unpack(">H", pdu_data[2:4])[0]
        byte_count = pdu_data[4]

        if quantity < 1 or quantity > 1968:
            return self._build_rtu_exception(slave_id, 0x0F, 0x03)

        expected_bytes = (quantity + 7) // 8
        if byte_count != expected_bytes:
            return self._build_rtu_exception(slave_id, 0x0F, 0x03)

        if len(pdu_data) < 5 + byte_count:
            return self._build_rtu_exception(slave_id, 0x0F, 0x02)

        coil_data = pdu_data[5:5 + byte_count]
        bits = _unpack_bits(coil_data, quantity)

        with self._lock:
            max_addr = len(self._coil_addr_rev) - 1
        if start_addr + quantity - 1 > max_addr and max_addr >= 0:
            return self._build_rtu_exception(slave_id, 0x0F, 0x02)

        with self._lock:
            for offset, bit_val in enumerate(bits):
                addr = start_addr + offset
                pid = self._coil_addr_rev.get(addr)
                if pid is not None:
                    self._coil_states[pid] = bit_val

        # FC15 响应 = echo start_addr + quantity
        pdu = struct.pack(">BHH", 0x0F, start_addr, quantity)
        return _build_rtu_frame(slave_id, pdu)

    def _handle_rtu_fc16(self, slave_id: int, pdu_data: bytes) -> bytes:
        """处理 RTU FC16（Write Multiple Registers）请求。

        请求 PDU：[start_addr(2)][quantity(2)][byte_count(1)][reg_values(N)]
        响应 PDU：[start_addr(2)][quantity(2)]（echo 起始地址和数量）。

        Args:
            slave_id: 从站地址。
            pdu_data: PDU 数据。

        Returns:
            RTU 响应帧。
        """
        if len(pdu_data) < 5:
            return self._build_rtu_exception(slave_id, 0x10, 0x02)

        start_addr = struct.unpack(">H", pdu_data[0:2])[0]
        quantity = struct.unpack(">H", pdu_data[2:4])[0]
        byte_count = pdu_data[4]

        if quantity < 1 or quantity > 123:
            return self._build_rtu_exception(slave_id, 0x10, 0x03)

        if byte_count != quantity * 2:
            return self._build_rtu_exception(slave_id, 0x10, 0x03)

        if len(pdu_data) < 5 + byte_count:
            return self._build_rtu_exception(slave_id, 0x10, 0x02)

        reg_data = pdu_data[5:5 + byte_count]

        with self._lock:
            for offset in range(quantity):
                addr = start_addr + offset
                pid = self._reg_rev.get(addr)
                if pid is not None:
                    reg_value = struct.unpack(
                        ">H", reg_data[offset * 2: offset * 2 + 2]
                    )[0]
                    self._values[pid] = reg_value

        # FC16 响应 = echo start_addr + quantity
        pdu = struct.pack(">BHH", 0x10, start_addr, quantity)
        return _build_rtu_frame(slave_id, pdu)

    def _build_rtu_exception(
        self, slave_id: int, function_code: int, exception_code: int,
    ) -> bytes:
        """构造 Modbus RTU 异常响应帧。

        异常响应 PDU：[function_code | 0x80][exception_code]

        Args:
            slave_id: 从站地址。
            function_code: 原始功能码。
            exception_code: 异常码（1=illegal function, 2=illegal data address,
                3=illegal data value）。

        Returns:
            RTU 异常响应帧。
        """
        pdu = struct.pack(">BB", function_code | 0x80, exception_code)
        return _build_rtu_frame(slave_id, pdu)


__all__ = [
    "ModbusRtuFacade",
    "probe_modbus_rtu_binary",
    "_crc16",
    "_build_rtu_frame",
    "_pack_bits",
    "_unpack_bits",
]
