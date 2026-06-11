"""Starfish Modbus TCP 协议真实 server facade。

本模块提供 Modbus TCP 协议的真实 server 生命周期实现。
使用 Python 标准库 socket 启动真实 TCP server，处理 Modbus
FC03（Read Holding Registers）和 FC06（Write Single Register）功能码。

点位到寄存器地址的映射：
    将 plan 中所有 point_id 按字典序排序后，按索引分配寄存器地址。
    第一个 point_id 对应寄存器 0，第二个对应寄存器 1，依此类推。
    此映射在 load_points 时确定，后续 start/stop 不影响映射关系。

Round 19 扩展（register_encoding 工具接入）：
    接入 ``starfish.protocols.modbus.register_encoding`` 工具子包，
    提供 ``encode_register_value`` / ``decode_register_value`` 公共
    API（在 facade 上以 ``encode_register_value`` /
    ``decode_register_value`` 形式暴露），支持 5 value_type × 4 byte/
    word 组合。FC03/FC06/FC16 等真实 Modbus 帧行为**不**受影响
    （register_encoding 仅作为 CPU 辅助层，不修改 socket server 的
    基础协议帧读写）。capabilities 新增 supports_register_encoding
    + supported_register_value_types + supported_byte_orders +
    supported_word_orders + supports_typed_register_helpers 字段。

当前实现状态：
- 已实现: start() / stop() / health() / load_points() / read() /
  write() / update_values() / capabilities() + register_encoding
  工具接入（Round 19）
  （write 为真实 Modbus FC06 写入，内部值更新后可通过 FC03 读取）
- NOT_IMPLEMENTED: subscribe() / report()

协议 server 特征：
- 零外部二进制依赖（纯 Python 标准库）。
- 可在单元测试中通过 localhost 动态端口稳定运行。
- 线程模式：daemon 线程运行 accept 循环，每个客户端连接独立线程处理。

安全边界：
- 不得 import seahorse / whale.ingest / whale.shared.source。
- 不连接生产数据库。
- 所有数据标注 synthetic。
- register_encoding 工具是纯 CPU 辅助层，**不**代表真实 Modbus 设备验证。
"""

from __future__ import annotations

import socket
import struct
import threading
from datetime import datetime, timezone
from typing import Any

from starfish.domain import StarfishServerMemberConfig, UnsupportedOperation


class ModbusTcpFacade:
    """Modbus TCP 协议真实 server facade。

    启动 TCP socket server，监听指定端口，处理 Modbus TCP 客户端请求。
    支持 FC03（读取多个保持寄存器）和 FC06（写入单个寄存器）。
    通过 MBAP 头部 + PDU 结构解析 Modbus TCP 帧。

    点位映射策略：
        由于 StarfishServerMemberConfig 的 StarfishPointConfig 不含寄存器地址字段，
        本 facade 在 load_points 时将 plan.initial_values 的 key 按字典序
        排序，按索引分配连续的寄存器地址（0-based）。此映射是确定性的，
        只要 initial_values 的 key 集合不变，映射关系就稳定。

    不负责：Modbus RTU 串行通信、异常码完整矩阵、
    浮点/32-bit 寄存器编解码、多单元 ID 支持。

    Attributes:
        _plan: 已加载的 StarfishServerMemberConfig。
        _started: 是否已调用 start()。
        _values: 内存点位值存储 (point_id -> value)。
        _started_at: start() 调用时间。
        _reg_map: point_id -> register_address 映射。
        _reg_rev: register_address -> point_id 反向映射。
        _server_socket: 监听 socket。
        _thread: accept 线程。
        _stop_event: 停止信号。
    """

    def __init__(self, bind_host: str = "127.0.0.1", port: int = 0) -> None:
        self._plan: StarfishServerMemberConfig | None = None
        self._started: bool = False
        self._values: dict[str, Any] = {}
        self._started_at: datetime | None = None
        self._bind_host: str = bind_host
        self._port: int = port
        self._actual_port: int = 0

        # 寄存器地址映射
        self._reg_map: dict[str, int] = {}
        self._reg_rev: dict[int, str] = {}

        # socket / 线程
        self._server_socket: socket.socket | None = None
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()

        # 线程安全锁（_values 读写保护）
        self._lock = threading.Lock()

    # ── 生命周期 ──────────────────────────────────────────────────────────────

    def start(self) -> None:
        """启动 Modbus TCP 真实 server。

        绑定 socket 到 bind_host:port，在 daemon 线程中运行 accept 循环。
        每个客户端连接在独立 daemon 线程中处理。

        重复调用安全（幂等）。

        Raises:
            OSError: 端口已被占用。
        """
        if self._started:
            return

        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((self._bind_host, self._port))
        server.listen(64)
        server.settimeout(0.5)  # accept 超时以响应 stop_event

        self._server_socket = server
        self._actual_port = server.getsockname()[1]
        self._stop_event.clear()

        thread = threading.Thread(target=self._serve_loop, daemon=True)
        thread.start()
        self._thread = thread
        self._started = True
        self._started_at = datetime.now(timezone.utc)

    def stop(self) -> None:
        """停止 Modbus TCP server。

        设置停止信号，关闭监听 socket，等待 accept 线程结束。
        不删除已加载的 plan 和 values，以便停止后仍可查询。
        重复调用安全（幂等）。
        """
        if not self._started:
            return

        self._stop_event.set()
        if self._server_socket is not None:
            try:
                self._server_socket.close()
            except OSError:
                pass
            self._server_socket = None

        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None

        self._started = False

    # ── 可观测性 ──────────────────────────────────────────────────────────────

    def health(self) -> dict[str, Any]:
        """返回当前 facade 的可观测健康状态。

        通过 TCP connect 探测 server socket 是否可连接。

        Returns:
            包含 health 信息的 dict。
        """
        port = self._actual_port or self._port
        running = False
        if self._started and port > 0:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1.0)
                try:
                    sock.connect((self._bind_host, port))
                    running = True
                except OSError:
                    pass
                finally:
                    sock.close()
            except Exception:
                pass

        return {
            "status": "started" if self._started else "stopped",
            "plan_loaded": self._plan is not None,
            "point_count": len(self._plan.points) if self._plan else 0,
            "endpoint_count": len(self._plan.endpoints) if self._plan else 0,
            "capabilities": list(self._plan.capabilities) if self._plan else [],
            "started_at": self._started_at.isoformat() if self._started_at else None,
            "synthetic": self._plan.synthetic if self._plan else True,
            "protocol": "MODBUS_TCP",
            "mode": "real",
            "port": port,
            "running": running,
        }

    # ── 数据操作 ──────────────────────────────────────────────────────────────

    def load_points(self, plan: StarfishServerMemberConfig) -> None:
        """从 StarfishServerMemberConfig 加载点位定义和初始值。

        同时构建 point_id -> register_address 映射：
        将 initial_values 的 key 按字典序排序后按索引分配寄存器地址。

        Args:
            plan: 已加载并校验的 StarfishServerMemberConfig。
        """
        self._plan = plan
        with self._lock:
            self._values = dict(plan.initial_values)
        self._build_register_map(plan)

    def _build_register_map(self, plan: StarfishServerMemberConfig) -> None:
        """构建 point_id <-> register_address 双向映射。

        按 initial_values key 字典序排序，索引即为寄存器地址。
        此映射在 load_points 时确定，确保重复加载结果一致。
        """
        sorted_ids = sorted(plan.initial_values.keys())
        reg_map: dict[str, int] = {}
        reg_rev: dict[int, str] = {}
        for i, pid in enumerate(sorted_ids):
            reg_map[pid] = i
            reg_rev[i] = pid
        self._reg_map = reg_map
        self._reg_rev = reg_rev

    def read(self, point_ids: list[str] | None = None) -> dict[str, Any]:
        """读取当前内存中的点位值。

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
        """写入单个点位值 —— 真实实现。

        直接更新内部存储。Modbus 客户端通过 FC06 写入时也会更新同一存储。
        写入后可通过 FC03 读取新值。

        Args:
            point_id: 目标点位 ID。
            value: 要写入的值。

        Raises:
            KeyError: point_id 不在已加载的点位集合中。
        """
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

        Args:
            values: point_id -> 新值 的 dict。
        """
        with self._lock:
            self._values.update(values)

    def capabilities(self) -> list[str]:
        """返回当前已加载 plan 的能力声明列表。

        Returns:
            能力声明字符串列表，未加载时返回空列表。
        """
        if self._plan is None:
            return []
        return list(self._plan.capabilities)

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
        工具。本 facade 不修改 FC03/FC06/FC16 等真实 Modbus 帧行为，仅
        在 CPU 层提供 32-bit / float32 register encoding 辅助。

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
        register_helpers 字段。**不**声明真实现场设备验证。

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

        Modbus 协议本身不支持服务端主动推送通知，
        需依赖外部轮询或上层机制。

        Args:
            point_ids: 要订阅的点位 ID 列表。

        Raises:
            UnsupportedOperation: 订阅操作尚未实现。
        """
        raise UnsupportedOperation(
            "subscribe",
            "ModbusTcpFacade.subscribe 尚未实现，"
            "Modbus 协议不支持服务端主动推送，需通过轮询替代",
        )

    def report(self) -> dict[str, Any]:
        """上报当前门面状态摘要 —— 当前未实现。

        Raises:
            UnsupportedOperation: report 操作尚未实现。
        """
        raise UnsupportedOperation(
            "report",
            "ModbusTcpFacade.report 尚未实现，"
            "待后续轮次实现结构化 telemetry report",
        )

    # ── 协议属性 ──────────────────────────────────────────────────────────────

    @property
    def protocol(self) -> str:
        """返回归一化协议名。"""
        return "MODBUS_TCP"

    @property
    def mode(self) -> str:
        """返回运行模式：real（真实 server）、stub（内存替身）或 unavailable（不可用）。"""
        return "real"

    # ── Modbus TCP 协议处理（内部）────────────────────────────────────────────

    def _serve_loop(self) -> None:
        """主 accept 循环。

        在 daemon 线程中运行，等待客户端连接。
        每个连接在独立 daemon 线程中处理。
        """
        assert self._server_socket is not None
        while not self._stop_event.is_set():
            try:
                client, _addr = self._server_socket.accept()
            except socket.timeout:
                continue
            except OSError:
                if self._stop_event.is_set():
                    return
                continue
            threading.Thread(target=self._handle_client, args=(client,), daemon=True).start()

    def _handle_client(self, client: socket.socket) -> None:
        """处理单个 Modbus TCP 客户端连接。

        循环接收数据，解析 MBAP + PDU，调用功能码处理器。

        Args:
            client: 已接受的客户端 socket。
        """
        with client:
            client.settimeout(0.5)
            while not self._stop_event.is_set():
                try:
                    request = client.recv(4096)
                except socket.timeout:
                    continue
                except OSError:
                    return
                if not request:
                    return
                try:
                    response = self._handle_mbap(request)
                except Exception:
                    response = b""
                if response:
                    try:
                        client.sendall(response)
                    except OSError:
                        return

    def _handle_mbap(self, data: bytes) -> bytes:
        """解析 MBAP 头部并分发到对应功能码处理器。

        MBAP 头部结构（7 字节）：
            Transaction ID (2B) | Protocol ID (2B) | Length (2B) | Unit ID (1B)

        随后紧跟 PDU（Protocol Data Unit）。

        Args:
            data: 完整的 Modbus TCP 帧（MBAP + PDU）。

        Returns:
            响应帧（MBAP + PDU），或空 bytes 表示忽略。
        """
        if len(data) < 8:
            return b""

        tid = struct.unpack(">H", data[0:2])[0]
        pid = struct.unpack(">H", data[2:4])[0]
        _length = struct.unpack(">H", data[4:6])[0]
        unit_id = data[6]
        function_code = data[7]

        pdu_data = data[8:]

        if function_code == 0x03:
            return self._handle_read_holding_registers(tid, pid, unit_id, pdu_data)
        elif function_code == 0x06:
            return self._handle_write_single_register(tid, pid, unit_id, pdu_data)
        else:
            # 不支持的功能码 -> 异常响应 (illegal function)
            return self._build_exception(tid, pid, unit_id, function_code, 0x01)

    def _handle_read_holding_registers(
        self, tid: int, pid: int, unit_id: int, pdu_data: bytes,
    ) -> bytes:
        """处理 FC03（Read Holding Registers）。

        从 pdu_data 中解析起始地址和数量，从内存 _values 中读取对应值。

        Args:
            tid: Transaction ID。
            pid: Protocol ID。
            unit_id: Unit ID。
            pdu_data: PDU 数据（不含功能码）。

        Returns:
            MBAP + PDU 响应帧。
        """
        if len(pdu_data) < 4:
            return self._build_exception(tid, pid, unit_id, 0x03, 0x02)

        start_addr = struct.unpack(">H", pdu_data[0:2])[0]
        quantity = struct.unpack(">H", pdu_data[2:4])[0]

        if quantity < 1 or quantity > 125:
            # 非法数据值
            return self._build_exception(tid, pid, unit_id, 0x03, 0x03)

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

        mbap = struct.pack(">HHHB", tid, pid, len(pdu) + 1, unit_id)
        return mbap + pdu

    def _handle_write_single_register(
        self, tid: int, pid: int, unit_id: int, pdu_data: bytes,
    ) -> bytes:
        """处理 FC06（Write Single Register）。

        从 pdu_data 中解析寄存器地址和写入值，更新内部 _values。

        Args:
            tid: Transaction ID。
            pid: Protocol ID。
            unit_id: Unit ID。
            pdu_data: PDU 数据（不含功能码）。

        Returns:
            MBAP + PDU 响应帧（回显写入内容）。
        """
        if len(pdu_data) < 4:
            return self._build_exception(tid, pid, unit_id, 0x06, 0x02)

        reg_addr = struct.unpack(">H", pdu_data[0:2])[0]
        reg_value = struct.unpack(">H", pdu_data[2:4])[0]

        # 更新内部存储
        with self._lock:
            point_id = self._reg_rev.get(reg_addr)
            if point_id is not None:
                self._values[point_id] = reg_value

        # FC06 响应 = 回显请求
        pdu = struct.pack(">BHH", 0x06, reg_addr, reg_value)
        mbap = struct.pack(">HHHB", tid, pid, len(pdu) + 1, unit_id)
        return mbap + pdu

    @staticmethod
    def _build_exception(
        tid: int, pid: int, unit_id: int, function_code: int, exception_code: int,
    ) -> bytes:
        """构造 Modbus 异常响应帧。

        异常响应 PDU：功能码 | 0x80 + 异常码。

        Args:
            tid: Transaction ID。
            pid: Protocol ID。
            unit_id: Unit ID。
            function_code: 原始功能码。
            exception_code: 异常码（1=illegal function, 2=illegal data address, 3=illegal data value）。

        Returns:
            MBAP + 异常 PDU 响应帧。
        """
        pdu = struct.pack(">BB", function_code | 0x80, exception_code)
        mbap = struct.pack(">HHHB", tid, pid, len(pdu) + 1, unit_id)
        return mbap + pdu


__all__ = ["ModbusTcpFacade"]
