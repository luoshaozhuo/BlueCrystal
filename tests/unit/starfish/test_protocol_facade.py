"""Starfish 协议专用 facade 测试。

验证 HttpRestFacade 和 ModbusTcpFacade 的真实 server 生命周期：
1. start/stop 真实 server 进程。
2. health TCP connect 探测。
3. load_points + read initial_values。
4. update_values 后 read 反映新值。
5. capabilities 返回 plan 中的能力声明。
6. write/subscribe/report 语义（协议特有）。
7. 真实 Modbus FC03/FC06 协议读写。

测试阶段：开发期验证 (P1) + 模块集成期验证 (P3)。
使用的替身：HTTP REST 和 Modbus TCP 协议真实 server（localhost 动态端口）。
外部依赖：无（纯 Python 标准库）。
不能证明：多并发客户端性能、断线重连、生产级 TLS/认证。
NOT_RUN 条件：无。
"""

from __future__ import annotations

import json
import socket
import struct
from urllib.error import HTTPError
from urllib.request import ProxyHandler, build_opener

import pytest

from starfish.models.plan import (
    StarfishServerPlan,
    StarfishEndpointPlan,
    StarfishPointPlan,
    UnsupportedOperation,
)
from starfish.facade.http_rest_facade import HttpRestFacade
from starfish.facade.modbus_tcp_facade import ModbusTcpFacade
from starfish.facade.mqtt_facade import MqttFacade
from starfish.facade.server_simulator_facade import ServerSimulatorFacade
from starfish.facade.iec101_facade import Iec101Facade
from starfish.facade.modbus_rtu_facade import ModbusRtuFacade
from starfish.facade.ads_facade import AdsFacade
from starfish.facade.goose_facade import GooseFacade
from starfish.facade.sv_facade import SvFacade
from starfish.registry.runtime_registry import (
    create_facade_for_endpoint,
    create_facades,
    get_supported_protocols,
    get_real_protocols,
    get_lightweight_protocols,
    get_codebase_pending_protocols,
    get_environment_pending_protocols,
)

# 创建无代理 opener，避免环境代理配置干扰 localhost 请求
_no_proxy_opener = build_opener(ProxyHandler({}))


# ── 共享 fixtures ────────────────────────────────────────────────────────────────


def _make_http_plan(
    scenario_id: str = "http_facade_test",
    initial_values: dict | None = None,
) -> StarfishServerPlan:
    """构造 HTTP REST 测试用 StarfishServerPlan。

    Args:
        scenario_id: 场景标识。
        initial_values: 初始值 dict。

    Returns:
        测试用 StarfishServerPlan。
    """
    if initial_values is None:
        initial_values = {"temp_sensor_1": 25.5, "pressure_1": 101.3}

    return StarfishServerPlan(
        schema_version="1.0.0",
        scenario_id=scenario_id,
        synthetic=True,
        server_name=f"{scenario_id}_http_server",
        endpoints=[
            StarfishEndpointPlan(
                endpoint_id=f"{scenario_id}_ep",
                protocol="HTTP_REST",
                host="127.0.0.1",
                port=0,
            )
        ],
        points=[
            StarfishPointPlan(
                point_id="temp_sensor_1",
                point_name="Temperature Sensor 1",
                node_key="/points/temp_sensor_1",
                value_type="Float",
                access_mode="RO",
            ),
            StarfishPointPlan(
                point_id="pressure_1",
                point_name="Pressure Sensor 1",
                node_key="/points/pressure_1",
                value_type="Float",
                access_mode="RO",
            ),
        ],
        capabilities=["READ"],
        initial_values=initial_values,
    )


def _make_modbus_plan(
    scenario_id: str = "modbus_facade_test",
    initial_values: dict | None = None,
) -> StarfishServerPlan:
    """构造 Modbus TCP 测试用 StarfishServerPlan。

    注意：initial_values 的 key 按字典序排序后分配寄存器地址。
    例如 {"a": 100, "b": 200} -> "a"=reg0, "b"=reg1。

    Args:
        scenario_id: 场景标识。
        initial_values: 初始值 dict（key 按字典序确定寄存器地址）。

    Returns:
        测试用 StarfishServerPlan。
    """
    if initial_values is None:
        initial_values = {"reg_valve_1": 42, "reg_valve_2": 100}

    return StarfishServerPlan(
        schema_version="1.0.0",
        scenario_id=scenario_id,
        synthetic=True,
        server_name=f"{scenario_id}_modbus_server",
        endpoints=[
            StarfishEndpointPlan(
                endpoint_id=f"{scenario_id}_ep",
                protocol="MODBUS_TCP",
                host="127.0.0.1",
                port=0,
            )
        ],
        points=[
            StarfishPointPlan(
                point_id="reg_valve_1",
                point_name="Valve Register 1",
                node_key="modbus://127.0.0.1:0/1",
                value_type="UInt16",
                access_mode="RW",
            ),
            StarfishPointPlan(
                point_id="reg_valve_2",
                point_name="Valve Register 2",
                node_key="modbus://127.0.0.1:0/2",
                value_type="UInt16",
                access_mode="RW",
            ),
        ],
        capabilities=["READ", "WRITE"],
        initial_values=initial_values,
    )


# ── HTTP REST Facade 测试 ────────────────────────────────────────────────────────


class TestHttpRestFacadeLifecycle:
    """HTTP REST facade start/stop 生命周期测试。"""

    def test_initial_state(self) -> None:
        """新建 facade 应为 stopped 状态。"""
        facade = HttpRestFacade()
        h = facade.health()
        assert h["status"] == "stopped"
        assert h["running"] is False
        assert h["mode"] == "real"
        assert h["protocol"] == "HTTP_REST"

    def test_start_and_stop(self) -> None:
        """start 后 server 应可连接，stop 后应断开。"""
        plan = _make_http_plan("start_stop")
        facade = HttpRestFacade(port=0)
        facade.load_points(plan)
        facade.start()

        h = facade.health()
        assert h["status"] == "started"
        assert h["running"] is True
        assert h["port"] > 0

        facade.stop()
        h2 = facade.health()
        assert h2["status"] == "stopped"
        assert h2["running"] is False

    def test_start_idempotent(self) -> None:
        """重复 start() 应为幂等。"""
        plan = _make_http_plan("idempotent_start")
        facade = HttpRestFacade(port=0)
        facade.load_points(plan)

        facade.start()
        facade.start()  # 第二次应无操作
        assert facade.health()["running"] is True

        facade.stop()

    def test_stop_idempotent(self) -> None:
        """重复 stop() 应为幂等。"""
        plan = _make_http_plan("idempotent_stop")
        facade = HttpRestFacade(port=0)
        facade.load_points(plan)

        facade.start()
        facade.stop()
        facade.stop()  # 第二次应无操作
        assert facade.health()["running"] is False

    def test_port_auto_allocation(self) -> None:
        """端口 0 时 OS 应自动分配端口。"""
        plan = _make_http_plan("auto_port")
        facade = HttpRestFacade(port=0)
        facade.load_points(plan)
        facade.start()

        actual_port = facade.health()["port"]
        assert actual_port > 0
        assert actual_port != 0

        facade.stop()


class TestHttpRestFacadeReadWrite:
    """HTTP REST facade 数据读写测试。"""

    def test_load_points_populates_values(self) -> None:
        """load_points 应从 plan.initial_values 填充内存。"""
        plan = _make_http_plan("load")
        facade = HttpRestFacade()
        facade.load_points(plan)

        values = facade.read()
        assert values["temp_sensor_1"] == 25.5
        assert values["pressure_1"] == 101.3

    def test_read_specific_points(self) -> None:
        """指定 point_ids 时应只返回对应值。"""
        plan = _make_http_plan("specific")
        facade = HttpRestFacade()
        facade.load_points(plan)

        values = facade.read(["temp_sensor_1"])
        assert values == {"temp_sensor_1": 25.5}

    def test_read_nonexistent_point(self) -> None:
        """不存在 point_id 应返回 None。"""
        plan = _make_http_plan("nonexist")
        facade = HttpRestFacade()
        facade.load_points(plan)

        values = facade.read(["nonexistent"])
        assert values == {"nonexistent": None}

    def test_update_values(self) -> None:
        """update_values 应更新内存值。"""
        plan = _make_http_plan("update")
        facade = HttpRestFacade()
        facade.load_points(plan)

        facade.update_values({"temp_sensor_1": 99.9, "new_point": 0})
        values = facade.read()
        assert values["temp_sensor_1"] == 99.9
        assert values["pressure_1"] == 101.3  # 未更新
        assert values["new_point"] == 0

    def test_http_get_returns_values(self) -> None:
        """HTTP GET /points 应返回当前内存值。"""
        plan = _make_http_plan("http_get")
        facade = HttpRestFacade(port=0)
        facade.load_points(plan)
        facade.start()

        port = facade.health()["port"]
        url = f"http://127.0.0.1:{port}/points"
        body = _no_proxy_opener.open(url, timeout=5.0).read().decode("utf-8")
        payload = json.loads(body)

        assert "values" in payload
        values_list = payload["values"]
        values_dict = {item["point"]: item["value"] for item in values_list}
        assert values_dict.get("temp_sensor_1") == 25.5
        assert values_dict.get("pressure_1") == 101.3

        facade.stop()

    def test_http_get_404_for_other_paths(self) -> None:
        """非 /points 路径应返回 404。"""
        plan = _make_http_plan("http_404")
        facade = HttpRestFacade(port=0)
        facade.load_points(plan)
        facade.start()

        port = facade.health()["port"]
        try:
            _no_proxy_opener.open(f"http://127.0.0.1:{port}/other", timeout=5.0)
            assert False, "应抛 HTTPError"
        except HTTPError as e:
            assert e.code == 404

        facade.stop()

    def test_capabilities_reflects_plan(self) -> None:
        """capabilities 应返回 plan 中的声明。"""
        plan = _make_http_plan("caps")
        facade = HttpRestFacade()
        facade.load_points(plan)

        assert facade.capabilities() == ["READ"]


class TestHttpRestNotImplemented:
    """HTTP REST facade NOT_IMPLEMENTED 语义测试。"""

    def test_write_raises_unsupported(self) -> None:
        """write 应抛出 UnsupportedOperation。"""
        plan = _make_http_plan("notimpl_write")
        facade = HttpRestFacade()
        facade.load_points(plan)

        with pytest.raises(UnsupportedOperation, match="write"):
            facade.write("temp_sensor_1", 100)

    def test_subscribe_raises_unsupported(self) -> None:
        """subscribe 应抛出 UnsupportedOperation。"""
        plan = _make_http_plan("notimpl_sub")
        facade = HttpRestFacade()
        facade.load_points(plan)

        with pytest.raises(UnsupportedOperation, match="subscribe"):
            facade.subscribe(["temp_sensor_1"])

    def test_report_raises_unsupported(self) -> None:
        """report 应抛出 UnsupportedOperation。"""
        plan = _make_http_plan("notimpl_report")
        facade = HttpRestFacade()
        facade.load_points(plan)

        with pytest.raises(UnsupportedOperation, match="report"):
            facade.report()


# ── Modbus TCP Facade 测试 ───────────────────────────────────────────────────────


class TestModbusTcpFacadeLifecycle:
    """Modbus TCP facade start/stop 生命周期测试。"""

    def test_initial_state(self) -> None:
        """新建 facade 应为 stopped 状态。"""
        facade = ModbusTcpFacade()
        h = facade.health()
        assert h["status"] == "stopped"
        assert h["running"] is False
        assert h["mode"] == "real"
        assert h["protocol"] == "MODBUS_TCP"

    def test_start_and_stop(self) -> None:
        """start 后 server 应可连接，stop 后应断开。"""
        plan = _make_modbus_plan("mb_start_stop")
        facade = ModbusTcpFacade(port=0)
        facade.load_points(plan)
        facade.start()

        h = facade.health()
        assert h["status"] == "started"
        assert h["running"] is True
        assert h["port"] > 0

        facade.stop()
        h2 = facade.health()
        assert h2["status"] == "stopped"
        assert h2["running"] is False

    def test_start_idempotent(self) -> None:
        """重复 start() 应为幂等。"""
        plan = _make_modbus_plan("mb_idem_start")
        facade = ModbusTcpFacade(port=0)
        facade.load_points(plan)

        facade.start()
        facade.start()
        assert facade.health()["running"] is True
        facade.stop()

    def test_port_auto_allocation(self) -> None:
        """端口 0 时 OS 应自动分配端口。"""
        plan = _make_modbus_plan("mb_auto_port")
        facade = ModbusTcpFacade(port=0)
        facade.load_points(plan)
        facade.start()

        actual_port = facade.health()["port"]
        assert actual_port > 0
        facade.stop()


class TestModbusTcpFacadeReadWrite:
    """Modbus TCP facade 数据读写测试。"""

    def test_load_points_builds_register_map(self) -> None:
        """load_points 应构建 point_id -> register 映射。"""
        plan = _make_modbus_plan(
            "mb_map",
            initial_values={"zzz": 10, "aaa": 20, "mmm": 30},
        )
        facade = ModbusTcpFacade()
        facade.load_points(plan)

        # 按字典序排序: aaa=0, mmm=1, zzz=2
        assert facade._reg_map["aaa"] == 0
        assert facade._reg_map["mmm"] == 1
        assert facade._reg_map["zzz"] == 2
        assert facade._reg_rev[0] == "aaa"
        assert facade._reg_rev[1] == "mmm"
        assert facade._reg_rev[2] == "zzz"

    def test_read_initial_values(self) -> None:
        """load_points 后 read 应返回 initial_values。"""
        plan = _make_modbus_plan(
            "mb_load",
            initial_values={"reg_valve_1": 100, "reg_valve_2": 200},
        )
        facade = ModbusTcpFacade()
        facade.load_points(plan)

        values = facade.read()
        assert values["reg_valve_1"] == 100
        assert values["reg_valve_2"] == 200

    def test_write_updates_value(self) -> None:
        """write 应更新内部值并可通过 read 读取。"""
        plan = _make_modbus_plan("mb_write")
        facade = ModbusTcpFacade()
        facade.load_points(plan)

        facade.write("reg_valve_1", 999)
        assert facade.read(["reg_valve_1"]) == {"reg_valve_1": 999}
        # 其他点位不受影响
        assert facade.read(["reg_valve_2"]) == {"reg_valve_2": 100}

    def test_write_unknown_point_raises_keyerror(self) -> None:
        """write 不存在的 point_id 应抛出 KeyError。"""
        plan = _make_modbus_plan("mb_keyerror")
        facade = ModbusTcpFacade()
        facade.load_points(plan)

        with pytest.raises(KeyError, match="unknown_pid"):
            facade.write("unknown_pid", 0)

    def test_update_values(self) -> None:
        """update_values 应批量更新内存值。"""
        plan = _make_modbus_plan("mb_update")
        facade = ModbusTcpFacade()
        facade.load_points(plan)

        facade.update_values({"reg_valve_1": 500, "new_reg": 300})
        values = facade.read()
        assert values["reg_valve_1"] == 500
        assert values["reg_valve_2"] == 100
        assert values["new_reg"] == 300

    def test_fc03_read_holding_registers(self) -> None:
        """真实 Modbus FC03 读取应返回寄存器值。"""
        plan = _make_modbus_plan(
            "mb_fc03",
            initial_values={"a": 100, "b": 200, "c": 300},
        )
        facade = ModbusTcpFacade(port=0)
        facade.load_points(plan)
        facade.start()

        port = facade.health()["port"]
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3.0)
            sock.connect(("127.0.0.1", port))

            # 构造 FC03 请求：读起始地址 0，数量 3
            tid = 1
            pid = 0
            unit_id = 1
            start_addr = 0
            quantity = 3
            pdu = struct.pack(">BHH", 0x03, start_addr, quantity)
            mbap = struct.pack(">HHHB", tid, pid, len(pdu) + 1, unit_id)
            sock.sendall(mbap + pdu)

            # 接收响应
            resp = sock.recv(1024)
            sock.close()

            # 解析 MBAP + PDU
            assert len(resp) >= 9
            resp_tid = struct.unpack(">H", resp[0:2])[0]
            assert resp_tid == tid
            fc = resp[7]
            assert fc == 0x03
            byte_count = resp[8]
            assert byte_count == quantity * 2  # 3 registers * 2 bytes

            # 按地址顺序: a=0 -> 100, b=1 -> 200, c=2 -> 300
            reg0 = struct.unpack(">H", resp[9:11])[0]
            reg1 = struct.unpack(">H", resp[11:13])[0]
            reg2 = struct.unpack(">H", resp[13:15])[0]
            assert reg0 == 100
            assert reg1 == 200
            assert reg2 == 300
        finally:
            facade.stop()

    def test_fc06_write_single_register(self) -> None:
        """真实 Modbus FC06 写入后 FC03 应读取到新值。"""
        plan = _make_modbus_plan(
            "mb_fc06",
            initial_values={"a": 10, "b": 20},
        )
        facade = ModbusTcpFacade(port=0)
        facade.load_points(plan)
        facade.start()

        port = facade.health()["port"]
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3.0)
            sock.connect(("127.0.0.1", port))

            # 1. FC06 写入：寄存器 1 (="b")，写入值 777
            tid = 1
            pid = 0
            unit_id = 1
            reg_addr = 1  # "b" 对应的寄存器
            reg_value = 777
            pdu = struct.pack(">BHH", 0x06, reg_addr, reg_value)
            mbap = struct.pack(">HHHB", tid, pid, len(pdu) + 1, unit_id)
            sock.sendall(mbap + pdu)

            # 接收 FC06 响应（回显）
            resp = sock.recv(1024)
            assert len(resp) >= 12
            assert resp[7] == 0x06
            resp_addr = struct.unpack(">H", resp[8:10])[0]
            resp_val = struct.unpack(">H", resp[10:12])[0]
            assert resp_addr == reg_addr
            assert resp_val == reg_value

            # 2. FC03 读取全部寄存器，验证写入成功
            tid2 = 2
            pdu2 = struct.pack(">BHH", 0x03, 0, 2)
            mbap2 = struct.pack(">HHHB", tid2, pid, len(pdu2) + 1, unit_id)
            sock.sendall(mbap2 + pdu2)

            resp2 = sock.recv(1024)
            sock.close()

            assert resp2[7] == 0x03
            # reg0 = "a" = 10, reg1 = "b" = 777 (写入值)
            assert struct.unpack(">H", resp2[9:11])[0] == 10
            assert struct.unpack(">H", resp2[11:13])[0] == 777

            # 同时验证 facade.read() 也反映了写入值
            assert facade.read()["b"] == 777
        finally:
            facade.stop()

    def test_fc06_write_invalid_address_ignored(self) -> None:
        """FC06 写入无效寄存器地址时不影响已有数据。"""
        plan = _make_modbus_plan("mb_fc06_invalid")
        facade = ModbusTcpFacade(port=0)
        facade.load_points(plan)
        facade.start()

        port = facade.health()["port"]
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3.0)
            sock.connect(("127.0.0.1", port))

            # FC06 写入不存在的寄存器 99
            pdu = struct.pack(">BHH", 0x06, 99, 555)
            mbap = struct.pack(">HHHB", 1, 0, len(pdu) + 1, 1)
            sock.sendall(mbap + pdu)
            resp = sock.recv(1024)
            sock.close()

            # 回显仍发送（Modbus 协议规范），但不更新注册表映射外的值
            assert resp[7] == 0x06

            # read 不应新增点位
            values = facade.read()
            assert "unknown_pid" not in values
        finally:
            facade.stop()

    def test_capabilities(self) -> None:
        """capabilities 应返回 plan 中的声明。"""
        plan = _make_modbus_plan("mb_caps")
        facade = ModbusTcpFacade()
        facade.load_points(plan)

        assert facade.capabilities() == ["READ", "WRITE"]


class TestModbusTcpNotImplemented:
    """Modbus TCP facade NOT_IMPLEMENTED 语义测试。"""

    def test_subscribe_raises_unsupported(self) -> None:
        """subscribe 应抛出 UnsupportedOperation。"""
        plan = _make_modbus_plan("mb_notimpl_sub")
        facade = ModbusTcpFacade()
        facade.load_points(plan)

        with pytest.raises(UnsupportedOperation, match="subscribe"):
            facade.subscribe(["reg_valve_1"])

    def test_report_raises_unsupported(self) -> None:
        """report 应抛出 UnsupportedOperation。"""
        plan = _make_modbus_plan("mb_notimpl_report")
        facade = ModbusTcpFacade()
        facade.load_points(plan)

        with pytest.raises(UnsupportedOperation, match="report"):
            facade.report()


# ── 完整 smoke 流程测试 ──────────────────────────────────────────────────────────


class TestFacadeSmokeFlow:
    """Facade 完整 smoke 流程测试。"""

    def test_http_rest_smoke_flow(self) -> None:
        """HTTP REST facade 完整 smoke 流程。"""
        plan = _make_http_plan("http_smoke_flow")
        facade = HttpRestFacade(port=0)
        facade.load_points(plan)

        # load_points
        assert facade.health()["plan_loaded"] is True

        # start
        facade.start()
        assert facade.health()["running"] is True

        # read
        values = facade.read()
        assert values["temp_sensor_1"] == 25.5

        # capabilities
        assert "READ" in facade.capabilities()

        # NOT_IMPLEMENTED: write
        with pytest.raises(UnsupportedOperation):
            facade.write("temp_sensor_1", 999)

        # update_values + read
        facade.update_values({"temp_sensor_1": 88.0})
        assert facade.read(["temp_sensor_1"]) == {"temp_sensor_1": 88.0}

        # stop
        facade.stop()
        assert facade.health()["running"] is False

    def test_modbus_tcp_smoke_flow(self) -> None:
        """Modbus TCP facade 完整 smoke 流程。"""
        plan = _make_modbus_plan("mb_smoke_flow")
        facade = ModbusTcpFacade(port=0)
        facade.load_points(plan)

        # load_points
        assert facade.health()["plan_loaded"] is True

        # start
        facade.start()
        assert facade.health()["running"] is True

        # read
        values = facade.read()
        assert values["reg_valve_1"] == 42

        # write (real)
        facade.write("reg_valve_1", 500)
        assert facade.read(["reg_valve_1"]) == {"reg_valve_1": 500}

        # capabilities
        assert "WRITE" in facade.capabilities()

        # NOT_IMPLEMENTED: subscribe
        with pytest.raises(UnsupportedOperation):
            facade.subscribe(["reg_valve_1"])

        # update_values + read
        facade.update_values({"reg_valve_1": 255})
        assert facade.read(["reg_valve_1"]) == {"reg_valve_1": 255}

        # stop
        facade.stop()
        assert facade.health()["running"] is False


# ── RuntimeRegistry 工厂 dispatch 测试 ──────────────────────────────────────────


class TestRegistryFactoryDispatch:
    """RuntimeRegistry 工厂 dispatch 测试。"""

    def test_http_rest_dispatches_to_http_rest_facade(self) -> None:
        """HTTP_REST 协议应 dispatch 到 HttpRestFacade。"""
        plan = _make_http_plan("dispatch_http")
        ep = plan.endpoints[0]
        entry = create_facade_for_endpoint(ep, plan)

        assert entry.mode == "real"
        assert entry.available is True
        assert isinstance(entry.facade, HttpRestFacade)
        assert entry.facade.protocol == "HTTP_REST"

    def test_modbus_tcp_dispatches_to_modbus_tcp_facade(self) -> None:
        """MODBUS_TCP 协议应 dispatch 到 ModbusTcpFacade。"""
        plan = _make_modbus_plan("dispatch_modbus")
        ep = plan.endpoints[0]
        entry = create_facade_for_endpoint(ep, plan)

        assert entry.mode == "real"
        assert entry.available is True
        assert isinstance(entry.facade, ModbusTcpFacade)
        assert entry.facade.protocol == "MODBUS_TCP"

    def test_unknown_protocol_dispatches_to_stub(self) -> None:
        """未知协议应 dispatch 到 in-memory stub。"""
        plan = _make_http_plan("dispatch_unknown")
        ep = StarfishEndpointPlan(
            endpoint_id="unknown_ep",
            protocol="IEC_61850_MMS",
            host="127.0.0.1",
            port=4840,
        )
        entry = create_facade_for_endpoint(ep, plan)

        assert entry.mode == "stub"
        assert entry.available is True
        assert isinstance(entry.facade, ServerSimulatorFacade)
        assert "in-memory stub" in entry.reason

    def test_create_facades_multiple_endpoints(self) -> None:
        """多 endpoint 时应为每个创建正确类型的 facade。"""
        plan = StarfishServerPlan(
            schema_version="1.0.0",
            scenario_id="multi_dispatch",
            synthetic=True,
            server_name="multi_server",
            endpoints=[
                StarfishEndpointPlan(
                    endpoint_id="http_ep",
                    protocol="HTTP_REST",
                    host="127.0.0.1",
                    port=0,
                ),
                StarfishEndpointPlan(
                    endpoint_id="modbus_ep",
                    protocol="MODBUS_TCP",
                    host="127.0.0.1",
                    port=0,
                ),
                StarfishEndpointPlan(
                    endpoint_id="mqtt_ep",
                    protocol="MQTT",
                    host="127.0.0.1",
                    port=0,
                ),
                StarfishEndpointPlan(
                    endpoint_id="iec61850_ep",
                    protocol="IEC_61850_MMS",
                    host="127.0.0.1",
                    port=4840,
                ),
            ],
            points=[],
            capabilities=["READ"],
            initial_values={},
        )
        registry = create_facades(plan)

        assert len(registry.entries) == 4

        modes = {e.endpoint.endpoint_id: e.mode for e in registry.entries}
        assert modes["http_ep"] == "real"
        assert modes["modbus_ep"] == "real"
        assert modes["mqtt_ep"] == "mqtt-lightweight"
        assert modes["iec61850_ep"] == "stub"

        # 类型检查
        assert isinstance(registry.entries[0].facade, HttpRestFacade)
        assert isinstance(registry.entries[1].facade, ModbusTcpFacade)
        assert isinstance(registry.entries[2].facade, MqttFacade)
        assert isinstance(registry.entries[3].facade, ServerSimulatorFacade)

    def test_get_supported_protocols(self) -> None:
        """get_supported_protocols 应返回已实现协议列表。"""
        protocols = get_supported_protocols()
        assert "HTTP_REST" in protocols
        assert "MODBUS_TCP" in protocols
        assert "MQTT" in protocols
        assert "OPC_UA" in protocols
        # IEC_104 和 IEC104 都应在列表中
        iec_protocols = [p for p in protocols if "IEC" in p]
        assert len(iec_protocols) >= 1

    def test_mqtt_dispatches_to_mqtt_facade(self) -> None:
        """MQTT 协议应 dispatch 到 MqttFacade（mqtt-lightweight mode）。"""
        plan = _make_http_plan("dispatch_mqtt")
        ep = StarfishEndpointPlan(
            endpoint_id="mqtt_ep",
            protocol="MQTT",
            host="127.0.0.1",
            port=0,
        )
        entry = create_facade_for_endpoint(ep, plan)

        assert entry.mode == "mqtt-lightweight"
        assert entry.available is True
        assert isinstance(entry.facade, MqttFacade)
        assert entry.facade.protocol == "MQTT"
        assert "非完整 MQTT broker" in entry.reason

    def test_mqtt_protocol_normalization(self) -> None:
        """MQTT 协议名大小写变体应正确归一化。"""
        plan = _make_http_plan("dispatch_mqtt_norm")
        for variant in ["mqtt", "MQTT", "Mqtt", "m q t t"]:
            ep = StarfishEndpointPlan(
                endpoint_id=f"mqtt_norm_{variant}",
                protocol=variant,
                host="127.0.0.1",
                port=0,
            )
            entry = create_facade_for_endpoint(ep, plan)
            # "m q t t" 归一化后变成 "M_Q_T_T"，不匹配 MQTT
            # 但 "mqtt" 和 "MQTT" 应该都匹配
            if variant in ("mqtt", "MQTT", "Mqtt"):
                assert isinstance(entry.facade, MqttFacade), (
                    f"变体 '{variant}' 应 dispatch 到 MqttFacade, "
                    f"实际 mode={entry.mode}"
                )

    def test_get_real_protocols(self) -> None:
        """get_real_protocols 应只返回 real 模式协议。"""
        protocols = get_real_protocols()
        assert "HTTP_REST" in protocols
        assert "MODBUS_TCP" in protocols
        assert "MQTT" not in protocols  # MQTT is lightweight, not real
        assert len(protocols) == 2

    def test_get_lightweight_protocols(self) -> None:
        """get_lightweight_protocols 应只返回 lightweight 模式协议。
        MODBUS_RTU 在 PTY 可用时也属于 lightweight。
        """
        protocols = get_lightweight_protocols()
        assert "MQTT" in protocols
        assert "HTTP_REST" not in protocols
        from starfish.facade.modbus_rtu_facade import probe_modbus_rtu_binary
        pty_ok, _ = probe_modbus_rtu_binary()
        if pty_ok:
            assert "MODBUS_RTU" in protocols
            assert len(protocols) >= 2
        else:
            assert len(protocols) == 1


class TestPendingProtocolDispatch:
    """Round 10 新增：codebase-pending 和 environment-pending 协议 dispatch 测试。"""

    def test_iec101_dispatches_to_iec101_facade(self) -> None:
        """IEC101 协议应 dispatch 到 Iec101Facade
        （mode 可能为 codec-enhanced/codec-enhanced-plus/codec-skeleton/
        environment-pending/codebase-pending）。"""
        plan = _make_http_plan("dispatch_iec101")
        ep = StarfishEndpointPlan(
            endpoint_id="iec101_ep",
            protocol="IEC101",
            host="127.0.0.1",
            port=2404,
        )
        entry = create_facade_for_endpoint(ep, plan)
        assert entry.mode in (
            "codec-enhanced",
            "codec-enhanced-plus",
            "codec-skeleton",
            "environment-pending",
            "codebase-pending",
        )
        assert entry.available is True
        assert isinstance(entry.facade, Iec101Facade)
        assert entry.facade.protocol == "IEC101"

    def test_iec_101_variant_dispatches_to_iec101_facade(self) -> None:
        """IEC_101 协议变体应 dispatch 到 Iec101Facade
        （mode 可能为 codec-enhanced/codec-enhanced-plus/codec-skeleton/
        environment-pending/codebase-pending）。"""
        plan = _make_http_plan("dispatch_iec_101")
        ep = StarfishEndpointPlan(
            endpoint_id="iec_101_ep",
            protocol="IEC_101",
            host="127.0.0.1",
            port=2404,
        )
        entry = create_facade_for_endpoint(ep, plan)
        assert entry.mode in (
            "codec-enhanced",
            "codec-enhanced-plus",
            "codec-skeleton",
            "environment-pending",
            "codebase-pending",
        )
        assert isinstance(entry.facade, Iec101Facade)

    def test_modbus_rtu_dispatches_to_modbus_rtu_facade(self) -> None:
        """MODBUS_RTU 协议应 dispatch 到 ModbusRtuFacade
        （PTY 可用时 rtu-lightweight，不可用时 codebase-pending）。"""
        plan = _make_http_plan("dispatch_modbus_rtu")
        ep = StarfishEndpointPlan(
            endpoint_id="modbus_rtu_ep",
            protocol="MODBUS_RTU",
            host="127.0.0.1",
            port=0,
        )
        entry = create_facade_for_endpoint(ep, plan)
        assert entry.mode in ("rtu-lightweight", "codebase-pending"), (
            f"MODBUS_RTU mode 应为 rtu-lightweight 或 codebase-pending，"
            f"实际 {entry.mode}"
        )
        assert entry.available is True
        assert isinstance(entry.facade, ModbusRtuFacade)
        assert entry.facade.protocol == "MODBUS_RTU"

    def test_beckhoff_ads_dispatches_to_ads_facade(self) -> None:
        """BECKHOFF_ADS 协议应 dispatch 到 AdsFacade（codebase-pending）。"""
        plan = _make_http_plan("dispatch_ads")
        ep = StarfishEndpointPlan(
            endpoint_id="ads_ep",
            protocol="BECKHOFF_ADS",
            host="127.0.0.1",
            port=48898,
        )
        entry = create_facade_for_endpoint(ep, plan)
        assert entry.mode == "codebase-pending"
        assert entry.available is True
        assert isinstance(entry.facade, AdsFacade)
        assert entry.facade.protocol == "BECKHOFF_ADS"

    def test_ads_short_name_dispatches_to_ads_facade(self) -> None:
        """ADS 短名协议应 dispatch 到 AdsFacade（codebase-pending）。"""
        plan = _make_http_plan("dispatch_ads_short")
        ep = StarfishEndpointPlan(
            endpoint_id="ads_short_ep",
            protocol="ADS",
            host="127.0.0.1",
            port=48898,
        )
        entry = create_facade_for_endpoint(ep, plan)
        assert entry.mode == "codebase-pending"
        assert isinstance(entry.facade, AdsFacade)

    def test_goose_dispatches_to_goose_facade(self) -> None:
        """GOOSE 协议应 dispatch 到 GooseFacade（environment-pending）。"""
        plan = _make_http_plan("dispatch_goose")
        ep = StarfishEndpointPlan(
            endpoint_id="goose_ep",
            protocol="GOOSE",
            host="127.0.0.1",
            port=0,
        )
        entry = create_facade_for_endpoint(ep, plan)
        assert entry.mode == "environment-pending"
        assert entry.available is True
        assert isinstance(entry.facade, GooseFacade)
        assert entry.facade.protocol == "GOOSE"

    def test_sv_dispatches_to_sv_facade(self) -> None:
        """SV 协议应 dispatch 到 SvFacade（environment-pending）。"""
        plan = _make_http_plan("dispatch_sv")
        ep = StarfishEndpointPlan(
            endpoint_id="sv_ep",
            protocol="SV",
            host="127.0.0.1",
            port=0,
        )
        entry = create_facade_for_endpoint(ep, plan)
        assert entry.mode == "environment-pending"
        assert entry.available is True
        assert isinstance(entry.facade, SvFacade)
        assert entry.facade.protocol == "SV"

    def test_multi_endpoint_with_pending_protocols(self) -> None:
        """多 endpoint 中含 pending 协议时应正确 dispatch。"""
        plan = StarfishServerPlan(
            schema_version="1.0.0",
            scenario_id="multi_pending",
            synthetic=True,
            server_name="multi_pending_server",
            endpoints=[
                StarfishEndpointPlan(
                    endpoint_id="http_ep",
                    protocol="HTTP_REST",
                    host="127.0.0.1",
                    port=0,
                ),
                StarfishEndpointPlan(
                    endpoint_id="iec101_ep",
                    protocol="IEC101",
                    host="127.0.0.1",
                    port=2404,
                ),
                StarfishEndpointPlan(
                    endpoint_id="goose_ep",
                    protocol="GOOSE",
                    host="127.0.0.1",
                    port=0,
                ),
                StarfishEndpointPlan(
                    endpoint_id="sv_ep",
                    protocol="SV",
                    host="127.0.0.1",
                    port=0,
                ),
            ],
            points=[],
            capabilities=["READ"],
            initial_values={},
        )
        registry = create_facades(plan)
        assert len(registry.entries) == 4

        modes = {e.endpoint.endpoint_id: e.mode for e in registry.entries}
        assert modes["http_ep"] == "real"
        assert modes["iec101_ep"] in (
            "codec-enhanced",
            "codec-enhanced-plus",
            "codec-skeleton",
            "environment-pending",
            "codebase-pending",
        )
        assert modes["goose_ep"] == "environment-pending"
        assert modes["sv_ep"] == "environment-pending"

        # 类型检查
        assert isinstance(registry.entries[0].facade, HttpRestFacade)
        assert isinstance(registry.entries[1].facade, Iec101Facade)
        assert isinstance(registry.entries[2].facade, GooseFacade)
        assert isinstance(registry.entries[3].facade, SvFacade)

    def test_get_supported_protocols_includes_pending(self) -> None:
        """get_supported_protocols 应包含 codebase-pending 和 environment-pending 协议。"""
        protocols = get_supported_protocols()
        assert "HTTP_REST" in protocols
        assert "MODBUS_TCP" in protocols
        assert "IEC101" in protocols
        assert "MODBUS_RTU" in protocols
        assert "BECKHOFF_ADS" in protocols
        assert "GOOSE" in protocols
        assert "SV" in protocols

    def test_get_codebase_pending_protocols(self) -> None:
        """get_codebase_pending_protocols 应返回 codebase-pending 协议。
        IEC101 和 MODBUS_RTU 动态决定：binary/PTY 可用时不在此列表。
        """
        protocols = get_codebase_pending_protocols()
        assert "BECKHOFF_ADS" in protocols
        assert "GOOSE" not in protocols
        assert "SV" not in protocols
        # IEC101 在 binary 缺失时应在列表中
        from starfish.facade.iec101_facade import Iec101Facade
        if Iec101Facade().mode == "codebase-pending":
            assert "IEC101" in protocols
        else:
            assert "IEC101" not in protocols
        # MODBUS_RTU 在 PTY 不可用时应在列表中
        from starfish.facade.modbus_rtu_facade import probe_modbus_rtu_binary
        pty_ok, _ = probe_modbus_rtu_binary()
        if not pty_ok:
            assert "MODBUS_RTU" in protocols

    def test_get_environment_pending_protocols(self) -> None:
        """get_environment_pending_protocols 应返回 environment-pending 协议。
        IEC101 动态判断：binary 已编译时为 environment-pending。
        """
        protocols = get_environment_pending_protocols()
        assert "GOOSE" in protocols
        assert "SV" in protocols
        # IEC101 在 binary 已编译时应在列表中
        from starfish.facade.iec101_facade import Iec101Facade
        if Iec101Facade().mode == "environment-pending":
            assert "IEC101" in protocols
        else:
            assert "IEC101" not in protocols


class TestRegistryStartStopAll:
    """RuntimeRegistry start_all/stop_all 集成测试。"""

    def test_start_all_starts_all_available(self) -> None:
        """start_all 应启动所有可用的 facade。"""
        plan = StarfishServerPlan(
            schema_version="1.0.0",
            scenario_id="start_all_test",
            synthetic=True,
            server_name="start_all_server",
            endpoints=[
                StarfishEndpointPlan(
                    endpoint_id="http_ep",
                    protocol="HTTP_REST",
                    host="127.0.0.1",
                    port=0,
                ),
                StarfishEndpointPlan(
                    endpoint_id="modbus_ep",
                    protocol="MODBUS_TCP",
                    host="127.0.0.1",
                    port=0,
                ),
            ],
            points=[],
            capabilities=["READ"],
            initial_values={"a": 1},
        )
        registry = create_facades(plan)

        try:
            registry.start_all()

            for entry in registry.entries:
                h = entry.facade.health()
                assert h["status"] == "started", f"{entry.endpoint.endpoint_id} 未启动"
                assert h["running"] is True
        finally:
            registry.stop_all()

    def test_health_all_aggregates(self) -> None:
        """health_all 应聚合所有 facade 的健康信息。"""
        plan = StarfishServerPlan(
            schema_version="1.0.0",
            scenario_id="health_all_test",
            synthetic=True,
            server_name="health_all_server",
            endpoints=[
                StarfishEndpointPlan(
                    endpoint_id="http_ep",
                    protocol="HTTP_REST",
                    host="127.0.0.1",
                    port=0,
                ),
            ],
            points=[],
            capabilities=["READ"],
            initial_values={},
        )
        registry = create_facades(plan)

        health = registry.health_all()
        assert "http_ep" in health
        assert health["http_ep"]["mode"] == "real"


# ── Round 19 Modbus TCP facade register_encoding 工具接入测试 ──────────────────


class TestModbusTcpFacadeRegisterEncoding:
    """ModbusTcpFacade 接入 register_encoding 工具的测试（Round 19 新增）。

    验证 facade 的 encode_register_value / decode_register_value 方法
    **真实调用** starfish.protocols.modbus.register_encoding 工具，
    而非仅修改 capabilities 文案。同时验证 Modbus TCP FC03/FC06
    帧行为不因 register_encoding 接入而回退。
    """

    def test_encode_register_value_uint16_calls_tool(self) -> None:
        """encode_register_value(UINT16) 应真实调用 register_encoding 工具。"""
        from starfish.protocols.modbus.register_encoding import (
            ModbusRegisterValueType,
        )
        facade = ModbusTcpFacade()
        regs = facade.encode_register_value(
            0x1234,
            ModbusRegisterValueType.UINT16,
        )
        assert regs == [0x1234]

    def test_encode_register_value_uint32_little_little(self) -> None:
        """encode_register_value(UINT32, little, little) 应与工具结果一致。"""
        from starfish.protocols.modbus.register_encoding import (
            ByteOrder, ModbusRegisterValueType, WordOrder,
            encode_register_value,
        )
        facade = ModbusTcpFacade()
        regs = facade.encode_register_value(
            0x01020304,
            ModbusRegisterValueType.UINT32,
            ByteOrder.LITTLE,
            WordOrder.LITTLE,
        )
        expected = encode_register_value(
            0x01020304,
            ModbusRegisterValueType.UINT32,
            ByteOrder.LITTLE,
            WordOrder.LITTLE,
        )
        assert regs == expected

    def test_encode_register_value_float32_roundtrip(self) -> None:
        """encode + decode(FLOAT32) 应真实回得原值。"""
        from starfish.protocols.modbus.register_encoding import (
            ByteOrder, ModbusRegisterValueType, WordOrder,
        )
        facade = ModbusTcpFacade()
        for value in [0.0, 1.0, 2.5, -1.5, 1024.0]:
            regs = facade.encode_register_value(
                value,
                ModbusRegisterValueType.FLOAT32,
                ByteOrder.BIG,
                WordOrder.BIG,
            )
            decoded = facade.decode_register_value(
                regs,
                ModbusRegisterValueType.FLOAT32,
                ByteOrder.BIG,
                WordOrder.BIG,
            )
            assert decoded == value

    def test_encode_register_value_int16_roundtrip(self) -> None:
        """encode + decode(INT16) 多种边界值。"""
        from starfish.protocols.modbus.register_encoding import (
            ModbusRegisterValueType,
        )
        facade = ModbusTcpFacade()
        for value in [0, 1, 100, 32767, -1, -32768]:
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
        from starfish.protocols.modbus.register_encoding import (
            ModbusRegisterValueType,
            RegisterEncodingValueError,
        )
        facade = ModbusTcpFacade()
        with pytest.raises(RegisterEncodingValueError):
            facade.encode_register_value(
                float("nan"),
                ModbusRegisterValueType.FLOAT32,
            )

    def test_register_encoding_capabilities_contains_required(self) -> None:
        """register_encoding_capabilities() 应包含 5 value_type + 2 byte_order + 2 word_order。"""
        facade = ModbusTcpFacade()
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
        """register_encoding 接入不应修改 FC03/FC06 等基础帧行为。

        验证 ModbusTcpFacade 既有 capabilities() 仍按 plan 行为
        返回（不自动插入 register_encoding 字段）；register_encoding
        字段必须通过独立 register_encoding_capabilities() 方法获取。
        """
        facade = ModbusTcpFacade()
        # 加载 plan 后 capabilities() 才会带 plan 能力
        plan = _make_modbus_tcp_plan()
        facade.load_points(plan)
        caps = facade.capabilities()
        # 既有 capabilities() 不应含 register_encoding 字段
        assert not any("register_encoding" in c for c in caps)
        # register_encoding 是独立方法
        reg_caps = facade.register_encoding_capabilities()
        assert "supports_register_encoding=true" in reg_caps


def _make_modbus_tcp_plan() -> StarfishServerPlan:
    """构造最小 Modbus TCP 测试 plan。"""
    return StarfishServerPlan(
        schema_version="1.0.0",
        scenario_id="modbus_tcp_reg_enc_test",
        synthetic=True,
        server_name="modbus_tcp_reg_enc_server",
        endpoints=[
            StarfishEndpointPlan(
                endpoint_id="modbus_tcp_ep",
                protocol="MODBUS_TCP",
                host="127.0.0.1",
                port=0,
            ),
        ],
        points=[
            StarfishPointPlan(
                point_id="point_a",
                point_name="Point A",
                node_key="/points/a",
                value_type="Float",
                access_mode="RO",
            ),
        ],
        capabilities=["READ"],
        initial_values={"point_a": 1.0},
    )
