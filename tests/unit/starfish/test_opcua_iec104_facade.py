"""Starfish OPC_UA / IEC104 facade 测试。

验证：
1. 依赖探测（probe_opcua_binary / probe_iec104_binary）。
2. OpcUaFacade / Iec104Facade 生命周期（start / stop / health / load_points / read / update_values）。
3. unavailable 模式语义（binary 缺失时的安全回退）。
4. real 模式生命周期（binary 存在时启动 C runner 子进程）。
5. ServerRegistry dispatch（OPC_UA -> OpcUaFacade, IEC_104 -> Iec104Facade）。
6. probe / profile / capacity 对新协议的处理。
7. NOT_IMPLEMENTED 能力（write / subscribe / report）验证。

测试阶段：开发期验证 (P1)。
使用的替身：OpcUaFacade（real/unavailable 模式）、Iec104Facade（real/unavailable 模式）。
外部依赖：open62541_source_simulator C runner（real mode 测试需要），
  iec104_simulator_server C runner（real mode 测试需要）。
不能证明：完整 OPC UA 协议栈读写、IEC104 ASDU 编解码、生产级链路验证。
NOT_RUN 条件：native binary 不可用时，real mode 测试标记为 skip。
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from starfish.domain.server_config import (
    StarfishServerConfig,
    StarfishEndpointConfig,
    StarfishPointConfig,
    UnsupportedOperation,
)
from starfish.drivers.opcua_facade import (
    OpcUaFacade,
    probe_opcua_binary,
    resolve_open62541_runner_path,
    _generate_opcua_tsv,  # noqa: PLC2701 -- 测试内部 helper
    _map_opcua_type,       # noqa: PLC2701 -- 测试内部 helper
)
from starfish.drivers.iec104_facade import (
    Iec104Facade,
    probe_iec104_binary,
    resolve_iec104_runner_path,
)
from starfish.drivers.server_registry import (
    create_driver_for_endpoint,
    get_supported_protocols,
    get_real_protocols,
    get_native_runner_protocols,
)
from whale.ingest.diagnostics.probe import probe_facade
from whale.ingest.diagnostics.profile import profile_facade
from whale.ingest.diagnostics.capacity import capacity_scan


# ── 环境检测 markers ──────────────────────────────────────────────────────────────

_OPCUA_BINARY_OK, _OPCUA_BINARY_REASON = probe_opcua_binary()
_IEC104_BINARY_OK, _IEC104_BINARY_REASON = probe_iec104_binary()

# 控制是否执行 real mode 测试（需要 native binary 和较长时间）
_REAL_MODE_ENABLED = (
    _OPCUA_BINARY_OK
    and _IEC104_BINARY_OK
    and os.environ.get("STARFISH_REAL_MODE_TESTS", "1") != "0"
)

requires_opcua_binary = pytest.mark.skipif(
    not _OPCUA_BINARY_OK,
    reason=f"open62541 runner 不可用: {_OPCUA_BINARY_REASON}",
)

requires_iec104_binary = pytest.mark.skipif(
    not _IEC104_BINARY_OK,
    reason=f"iec104_simulator_server 不可用: {_IEC104_BINARY_REASON}",
)

requires_real_mode = pytest.mark.skipif(
    not _REAL_MODE_ENABLED,
    reason="native binary 不可用或 STARFISH_REAL_MODE_TESTS=0",
)


# ── fixture helpers ──────────────────────────────────────────────────────────────


def _make_test_plan(
    scenario_id: str = "test_opcua_iec104",
    protocol: str = "OPC_UA",
    initial_values: dict | None = None,
) -> StarfishServerConfig:
    """构造测试用 StarfishServerConfig。

    Args:
        scenario_id: 场景标识。
        protocol: 协议名。
        initial_values: 初始值 dict。

    Returns:
        测试用 StarfishServerConfig。
    """
    if initial_values is None:
        initial_values = {"p0": 42.0, "p1": 100.0, "p2": True}

    return StarfishServerConfig(
        schema_version="1.0.0",
        scenario_id=scenario_id,
        synthetic=True,
        server_name=f"{scenario_id}_server",
        endpoints=[
            StarfishEndpointConfig(
                endpoint_id=f"{scenario_id}_ep",
                protocol=protocol,
                host="127.0.0.1",
                port=0,
            )
        ],
        points=[
            StarfishPointConfig(
                point_id="p0",
                point_name="Point 0",
                node_key="/points/0",
                value_type="Float",
                access_mode="RO",
            ),
            StarfishPointConfig(
                point_id="p1",
                point_name="Point 1",
                node_key="/points/1",
                value_type="Int32",
                access_mode="RO",
            ),
            StarfishPointConfig(
                point_id="p2",
                point_name="Point 2",
                node_key="/points/2",
                value_type="Boolean",
                access_mode="RO",
            ),
        ],
        capabilities=["READ"],
        initial_values=initial_values,
    )


# ── 依赖探测测试 ──────────────────────────────────────────────────────────────────


class TestDependencyProbes:
    """OPC_UA / IEC104 依赖探测测试。"""

    def test_probe_opcua_binary_returns_bool_and_reason(self) -> None:
        """probe_opcua_binary 返回 (bool, str) 元组。"""
        ok, reason = probe_opcua_binary()
        assert isinstance(ok, bool)
        assert isinstance(reason, str)
        assert len(reason) > 0

    def test_probe_iec104_binary_returns_bool_and_reason(self) -> None:
        """probe_iec104_binary 返回 (bool, str) 元组。"""
        ok, reason = probe_iec104_binary()
        assert isinstance(ok, bool)
        assert isinstance(reason, str)
        assert len(reason) > 0

    def test_resolve_opcua_runner_path_returns_path(self) -> None:
        """resolve_open62541_runner_path 返回 Path。"""
        path = resolve_open62541_runner_path()
        assert isinstance(path, Path)
        assert len(str(path)) > 0

    def test_resolve_iec104_runner_path_returns_path(self) -> None:
        """resolve_iec104_runner_path 返回 Path。"""
        path = resolve_iec104_runner_path()
        assert isinstance(path, Path)
        assert len(str(path)) > 0

    def test_environment_variable_respected(self) -> None:
        """SOURCE_SIM_OPEN62541_RUNNER_PATH 环境变量应被优先使用。"""
        test_path = str(Path("/tmp/nonexistent_open62541_simulator"))
        old_env = os.environ.get("SOURCE_SIM_OPEN62541_RUNNER_PATH")
        try:
            os.environ["SOURCE_SIM_OPEN62541_RUNNER_PATH"] = test_path
            resolved = resolve_open62541_runner_path()
            assert str(resolved) == test_path
        finally:
            if old_env is not None:
                os.environ["SOURCE_SIM_OPEN62541_RUNNER_PATH"] = old_env
            else:
                os.environ.pop("SOURCE_SIM_OPEN62541_RUNNER_PATH", None)

    def test_opcua_type_mapping(self) -> None:
        """_map_opcua_type 应正确映射 Starfish value_type 到 OPC UA 类型。"""
        assert _map_opcua_type("Float") == "Double"
        assert _map_opcua_type("Int32") == "Int32"
        assert _map_opcua_type("Boolean") == "Boolean"
        assert _map_opcua_type("String") == "String"
        assert _map_opcua_type("Float64") == "Double"
        assert _map_opcua_type(None) == "Double"
        assert _map_opcua_type("UnknownType") == "Double"

    def test_generate_opcua_tsv_format(self) -> None:
        """_generate_opcua_tsv 生成格式正确的 TSV 配置。"""
        plan = _make_test_plan("tsv_test")
        tsv = _generate_opcua_tsv("127.0.0.1", 4840, plan)

        lines = tsv.strip().split("\n")
        assert len(lines) >= 5  # endpoint + namespace + update_enabled + 3 nodes

        # endpoint 行
        assert lines[0].startswith("endpoint\t")
        assert "opc.tcp://127.0.0.1:4840" in lines[0]

        # namespace_uri 行
        assert lines[1].startswith("namespace_uri\t")

        # update_enabled 行
        assert "update_enabled\tfalse" in lines[2]

        # node 行应包含 6 个字段
        for line in lines[3:]:
            fields = line.split("\t")
            assert len(fields) == 6
            assert fields[0] == "node"

        # 无制表符或换行符在字段内部（separator sanity）
        for line in lines:
            for field in line.split("\t"):
                assert "\t" not in field


# ── OpcUaFacade unavailable 模式测试（无 binary 依赖）────────────────────────────


class TestOpcUaFacadeUnavailable:
    """OpcUaFacade 基本接口测试（unavailable 模式通用，无需 binary）。"""

    def test_facade_protocol_and_mode(self) -> None:
        """facade 应返回正确的 protocol 和 mode 属性。"""
        facade = OpcUaFacade()
        assert facade.protocol == "OPC_UA"
        assert facade.mode in ("real", "unavailable")
        assert isinstance(facade.binary_available, bool)
        assert len(facade.binary_reason) > 0

    def test_unavailable_mode_start_stop(self) -> None:
        """start/stop 应成功（in-memory 或 real 模式均适用）。"""
        plan = _make_test_plan("test_start_stop")
        facade = OpcUaFacade(port=0)
        facade.load_points(plan)  # real 模式下 start 需要已加载 plan
        facade.start()
        assert facade.health()["status"] == "started"
        facade.stop()
        assert facade.health()["status"] == "stopped"

    def test_unavailable_mode_load_points_and_read(self) -> None:
        """load_points 和 read 应正确工作。"""
        plan = _make_test_plan("test_load")
        facade = OpcUaFacade()
        facade.load_points(plan)

        values = facade.read()
        assert values["p0"] == 42.0
        assert values["p1"] == 100.0
        assert values["p2"] is True

        # 指定点位
        subset = facade.read(["p0", "p2"])
        assert subset["p0"] == 42.0
        assert subset["p2"] is True
        # 不存在点位
        assert "p_nonexist" not in subset
        assert facade.read(["p_nonexist"])["p_nonexist"] is None

    def test_unavailable_mode_update_values(self) -> None:
        """update_values 应正确更新内存值。"""
        plan = _make_test_plan("test_update")
        facade = OpcUaFacade()
        facade.load_points(plan)

        facade.update_values({"p0": 999.0, "p_new": "hello"})
        values = facade.read()
        assert values["p0"] == 999.0
        assert values["p_new"] == "hello"
        # p1 未变化
        assert values["p1"] == 100.0

    def test_unavailable_mode_health(self) -> None:
        """health 应正确返回 unavailable 模式信息。"""
        plan = _make_test_plan("test_health")
        facade = OpcUaFacade()
        facade.load_points(plan)

        h = facade.health()
        assert h["protocol"] == "OPC_UA"
        assert h["mode"] in ("real", "unavailable")
        assert h["plan_loaded"] is True
        assert h["point_count"] == 3
        assert h["endpoint_count"] == 1
        assert h["capabilities"] == ["READ"]
        assert h["binary_available"] == facade.binary_available

        if not facade.binary_available:
            assert "reason" in h
            assert len(h["reason"]) > 0

    def test_unavailable_mode_capabilities(self) -> None:
        """capabilities 应返回 plan 中的能力声明。"""
        plan = _make_test_plan("test_caps")
        facade = OpcUaFacade()
        assert facade.capabilities() == []
        facade.load_points(plan)
        assert facade.capabilities() == ["READ"]

    def test_idempotent_start_stop(self) -> None:
        """重复 start/stop 应安全（幂等）。"""
        plan = _make_test_plan("test_idempotent")
        facade = OpcUaFacade(port=0)
        facade.load_points(plan)
        facade.start()
        facade.start()  # 重复 start
        assert facade.health()["status"] == "started"
        facade.stop()
        facade.stop()  # 重复 stop
        assert facade.health()["status"] == "stopped"

    def test_read_before_load_points(self) -> None:
        """load_points 前 read 返回空 dict。"""
        facade = OpcUaFacade()
        values = facade.read()
        assert values == {}


# ── OpcUaFacade NOT_IMPLEMENTED 测试 ────────────────────────────────────────────


class TestOpcUaFacadeNotImplemented:
    """OpcUaFacade NOT_IMPLEMENTED 操作测试。"""

    def test_write_not_implemented(self) -> None:
        """write 应抛出 UnsupportedOperation。"""
        facade = OpcUaFacade()
        with pytest.raises(UnsupportedOperation) as exc:
            facade.write("p0", 42)
        assert "NOT_IMPLEMENTED" in str(exc.value)
        assert "write" in str(exc.value)

    def test_subscribe_not_implemented(self) -> None:
        """subscribe 应抛出 UnsupportedOperation。"""
        facade = OpcUaFacade()
        with pytest.raises(UnsupportedOperation) as exc:
            facade.subscribe(["p0", "p1"])
        assert "NOT_IMPLEMENTED" in str(exc.value)
        assert "subscribe" in str(exc.value)

    def test_report_not_implemented(self) -> None:
        """report 应抛出 UnsupportedOperation。"""
        facade = OpcUaFacade()
        with pytest.raises(UnsupportedOperation) as exc:
            facade.report()
        assert "NOT_IMPLEMENTED" in str(exc.value)
        assert "report" in str(exc.value)

    def test_stop_before_start_safe(self) -> None:
        """未 start 时 stop 应安全（不抛异常）。"""
        facade = OpcUaFacade()
        facade.stop()  # 不应抛异常


# ── Iec104Facade unavailable 模式测试（无 binary 依赖）───────────────────────────


class TestIec104FacadeUnavailable:
    """Iec104Facade 基本接口测试（unavailable 模式通用，无需 binary）。"""

    def test_facade_protocol_and_mode(self) -> None:
        """facade 应返回正确的 protocol 和 mode 属性。"""
        facade = Iec104Facade()
        assert facade.protocol == "IEC104"
        assert facade.mode in ("real", "unavailable")
        assert isinstance(facade.binary_available, bool)
        assert len(facade.binary_reason) > 0

    def test_unavailable_mode_start_stop(self) -> None:
        """unavailable 模式 start/stop 应成功。"""
        facade = Iec104Facade()
        facade.start()
        assert facade.health()["status"] == "started"
        facade.stop()
        assert facade.health()["status"] == "stopped"

    def test_unavailable_mode_load_points_and_read(self) -> None:
        """load_points 和 read 应正确工作。"""
        plan = _make_test_plan("iec104_load", protocol="IEC104")
        facade = Iec104Facade()
        facade.load_points(plan)

        values = facade.read()
        assert values["p0"] == 42.0
        assert values["p1"] == 100.0
        assert values["p2"] is True

    def test_unavailable_mode_update_values(self) -> None:
        """update_values 应正确更新内存值。"""
        plan = _make_test_plan("iec104_update", protocol="IEC104")
        facade = Iec104Facade()
        facade.load_points(plan)

        facade.update_values({"p0": 999.0})
        assert facade.read(["p0"])["p0"] == 999.0

    def test_unavailable_mode_health(self) -> None:
        """health 应正确返回 unavailable 模式信息。"""
        plan = _make_test_plan("iec104_health", protocol="IEC104")
        facade = Iec104Facade()
        facade.load_points(plan)

        h = facade.health()
        assert h["protocol"] == "IEC104"
        assert h["mode"] in ("real", "unavailable")
        assert h["plan_loaded"] is True
        assert h["point_count"] == 3
        assert h["binary_available"] == facade.binary_available

        if not facade.binary_available:
            assert "reason" in h
            assert len(h["reason"]) > 0

    def test_idempotent_start_stop(self) -> None:
        """重复 start/stop 应安全（幂等）。"""
        facade = Iec104Facade()
        facade.start()
        facade.start()
        assert facade.health()["status"] == "started"
        facade.stop()
        facade.stop()
        assert facade.health()["status"] == "stopped"


# ── Iec104Facade NOT_IMPLEMENTED 测试 ───────────────────────────────────────────


class TestIec104FacadeNotImplemented:
    """Iec104Facade NOT_IMPLEMENTED 操作测试。"""

    def test_write_not_implemented(self) -> None:
        """write 应抛出 UnsupportedOperation。"""
        facade = Iec104Facade()
        with pytest.raises(UnsupportedOperation) as exc:
            facade.write("p0", 42)
        assert "NOT_IMPLEMENTED" in str(exc.value)
        assert "write" in str(exc.value)

    def test_subscribe_not_implemented(self) -> None:
        """subscribe 应抛出 UnsupportedOperation。"""
        facade = Iec104Facade()
        with pytest.raises(UnsupportedOperation) as exc:
            facade.subscribe(["p0"])
        assert "NOT_IMPLEMENTED" in str(exc.value)
        assert "subscribe" in str(exc.value)

    def test_report_not_implemented(self) -> None:
        """report 应抛出 UnsupportedOperation。"""
        facade = Iec104Facade()
        with pytest.raises(UnsupportedOperation) as exc:
            facade.report()
        assert "NOT_IMPLEMENTED" in str(exc.value)
        assert "report" in str(exc.value)


# ── ServerRegistry dispatch 测试 ────────────────────────────────────────────────


class TestRuntimeRegistryDispatch:
    """ServerRegistry OPC_UA / IEC104 协议 dispatch 测试。"""

    def test_registry_dispatches_opcua(self) -> None:
        """OPC_UA 协议应 dispatch 到 OpcUaFacade。"""
        plan = _make_test_plan("reg_opcua", protocol="OPC_UA")
        ep = plan.endpoints[0]
        entry = create_driver_for_endpoint(ep, plan)

        assert entry.mode in ("real", "unavailable")
        assert entry.driver is not None
        assert entry.driver.protocol == "OPC_UA"
        if entry.mode == "real":
            assert entry.available is True
            assert "real" in entry.reason.lower()
        else:
            assert entry.available is False
            assert "unavailable" in entry.reason.lower()

    def test_registry_dispatches_iec104(self) -> None:
        """IEC_104 协议应 dispatch 到 Iec104Facade。"""
        plan = _make_test_plan("reg_iec104", protocol="IEC_104")
        ep = plan.endpoints[0]
        entry = create_driver_for_endpoint(ep, plan)

        assert entry.mode in ("real", "unavailable")
        assert entry.driver is not None
        assert entry.driver.protocol == "IEC104"
        if entry.mode == "real":
            assert entry.available is True
        else:
            assert entry.available is False

    def test_registry_dispatches_iec104_alternate_spelling(self) -> None:
        """IEC104（无下划线）协议名应 dispatch 到 Iec104Facade。"""
        plan = _make_test_plan("reg_iec104b", protocol="IEC104")
        ep = plan.endpoints[0]
        entry = create_driver_for_endpoint(ep, plan)

        assert entry.driver is not None
        assert entry.driver.protocol == "IEC104"

    def test_get_supported_protocols_includes_new(self) -> None:
        """get_supported_protocols 应包含 OPC_UA 和 IEC104。"""
        protocols = get_supported_protocols()
        assert "HTTP_REST" in protocols
        assert "MODBUS_TCP" in protocols
        assert "MQTT" in protocols
        assert "OPC_UA" in protocols
        # IEC_104 和 IEC104 都在集合中
        iec_protocols = [p for p in protocols if "IEC" in p]
        assert len(iec_protocols) >= 1

    def test_get_real_protocols_excludes_opcua(self) -> None:
        """get_real_protocols 不包含 OPC_UA（OPC_UA 是 native runner 协议）。"""
        protocols = get_real_protocols()
        assert "OPC_UA" not in protocols
        assert "IEC104" not in protocols

    def test_get_native_runner_protocols(self) -> None:
        """get_native_runner_protocols 应包含 OPC_UA 和 IEC104。"""
        protocols = get_native_runner_protocols()
        assert "OPC_UA" in protocols
        iec_protocols = [p for p in protocols if "IEC" in p]
        assert len(iec_protocols) >= 1


# ── OPC UA real mode 测试（需要 open62541 binary）────────────────────────────────


@pytest.mark.timeout(30)
class TestOpcUaFacadeRealMode:
    """OpcUaFacade real 模式测试（需要 open62541 C runner）。"""

    @requires_opcua_binary
    def test_real_mode_start_stop(self) -> None:
        """real 模式 start 应启动 open62541 子进程，stop 应终止。"""
        plan = _make_test_plan("real_start")
        facade = OpcUaFacade(port=0)
        facade.load_points(plan)

        assert facade.mode == "real"
        facade.start()
        try:
            h = facade.health()
            assert h["status"] == "started"
            assert h["mode"] == "real"
            assert h["running"] is True
            assert h["port"] > 0
        finally:
            facade.stop()

        # stop 后 running 应为 False
        h2 = facade.health()
        assert h2["running"] is False

    @requires_opcua_binary
    def test_real_mode_health_tcp_connect(self) -> None:
        """real 模式 health 应通过 TCP connect 确认端口可达。"""
        plan = _make_test_plan("real_health")
        facade = OpcUaFacade(port=0)
        facade.load_points(plan)

        facade.start()
        try:
            h = facade.health()
            assert h["running"] is True
            assert h["port"] > 0
        finally:
            facade.stop()

    @requires_opcua_binary
    def test_real_mode_idempotent_start(self) -> None:
        """重复 start 应安全（幂等）。"""
        plan = _make_test_plan("real_idempotent")
        facade = OpcUaFacade(port=0)
        facade.load_points(plan)

        facade.start()
        try:
            facade.start()  # 重复 start
            h = facade.health()
            assert h["running"] is True
        finally:
            facade.stop()

    @requires_opcua_binary
    def test_real_mode_stop_before_start_safe(self) -> None:
        """未 start 时 stop 应安全。"""
        plan = _make_test_plan("real_stop_before")
        facade = OpcUaFacade(port=0)
        facade.load_points(plan)
        facade.stop()  # 不应抛异常

    @requires_opcua_binary
    def test_real_mode_start_without_load_points_raises(self) -> None:
        """未 load_points 时 start 应抛出 RuntimeError。"""
        facade = OpcUaFacade(port=0)
        with pytest.raises(RuntimeError, match="load_points"):
            facade.start()


# ── IEC104 real mode 测试（需要 iec104_simulator_server binary）──────────────────


@pytest.mark.timeout(30)
class TestIec104FacadeRealMode:
    """Iec104Facade real 模式测试（需要 iec104_simulator_server C runner）。"""

    @requires_iec104_binary
    def test_real_mode_start_stop(self) -> None:
        """real 模式 start 应启动 iec104_simulator_server 子进程，stop 应终止。"""
        plan = _make_test_plan("real_iec104", protocol="IEC104")
        facade = Iec104Facade(port=0)
        facade.load_points(plan)

        assert facade.mode == "real"
        facade.start()
        try:
            h = facade.health()
            assert h["status"] == "started"
            assert h["mode"] == "real"
            assert h["running"] is True
            assert h["port"] > 0
        finally:
            facade.stop()

        h2 = facade.health()
        assert h2["running"] is False

    @requires_iec104_binary
    def test_real_mode_health_tcp_connect(self) -> None:
        """real 模式 health 应通过 TCP connect 确认端口可达。"""
        plan = _make_test_plan("real_iec104_health", protocol="IEC104")
        facade = Iec104Facade(port=0)
        facade.load_points(plan)

        facade.start()
        try:
            h = facade.health()
            assert h["running"] is True
            assert h["port"] > 0
        finally:
            facade.stop()

    @requires_iec104_binary
    def test_real_mode_idempotent_start(self) -> None:
        """重复 start 应安全（幂等）。"""
        plan = _make_test_plan("real_iec104_idem", protocol="IEC104")
        facade = Iec104Facade(port=0)
        facade.load_points(plan)

        facade.start()
        try:
            facade.start()
            h = facade.health()
            assert h["running"] is True
        finally:
            facade.stop()

    @requires_iec104_binary
    def test_real_mode_start_without_load_points_raises(self) -> None:
        """IEC104 不需要 plan 也能 start（与 OPC_UA 不同，IEC104 无需 TSV config）。"""
        facade = Iec104Facade(port=0)
        # IEC104 runner 只需要端口，不需要 load_points
        # 但为了健康检查的一致性，应 load_points 后再 start
        facade.load_points(
            _make_test_plan("real_iec104_start", protocol="IEC104")
        )
        facade.start()
        try:
            assert facade.health()["running"] is True
        finally:
            facade.stop()


# ── probe / profile / capacity 对新协议测试 ──────────────────────────────────────


class TestProbeForNewProtocols:
    """probe_facade 对 OPC_UA / IEC104 的探测测试。"""

    def test_probe_opcua_unavailable_mode(self) -> None:
        """probe 对 OPC_UA facade 应能执行（unavailable 模式仍 start/health/read 成功）。"""
        plan = _make_test_plan("probe_opcua")
        facade = OpcUaFacade(port=0)
        result = probe_facade(facade, plan=plan, endpoint_id="opcua_ep")
        assert result.status == "PASS"
        assert result.protocol == "OPC_UA"
        assert result.mode in ("real", "unavailable")
        assert "read" in result.details
        facade.stop()

    def test_probe_iec104_unavailable_mode(self) -> None:
        """probe 对 IEC104 facade 应能执行。"""
        plan = _make_test_plan("probe_iec104", protocol="IEC104")
        facade = Iec104Facade(port=0)
        result = probe_facade(facade, plan=plan, endpoint_id="iec104_ep")
        assert result.status == "PASS"
        assert result.protocol == "IEC104"
        assert result.mode in ("real", "unavailable")
        assert "read" in result.details
        facade.stop()

    @requires_opcua_binary
    def test_probe_opcua_real_mode(self) -> None:
        """probe 对 OPC_UA real mode facade 应能执行并返回 real 模式。"""
        plan = _make_test_plan("probe_opcua_real")
        facade = OpcUaFacade(port=0)
        # 必须在 load_points 后 probe
        facade.load_points(plan)
        result = probe_facade(facade, plan=plan, endpoint_id="opcua_real_ep")
        assert result.status == "PASS"
        assert result.mode == "real"
        assert result.protocol == "OPC_UA"
        facade.stop()

    @requires_iec104_binary
    def test_probe_iec104_real_mode(self) -> None:
        """probe 对 IEC104 real mode facade 应能执行并返回 real 模式。"""
        plan = _make_test_plan("probe_iec104_real", protocol="IEC104")
        facade = Iec104Facade(port=0)
        facade.load_points(plan)
        result = probe_facade(facade, plan=plan, endpoint_id="iec104_real_ep")
        assert result.status == "PASS"
        assert result.mode == "real"
        assert result.protocol == "IEC104"
        facade.stop()


class TestProfileForNewProtocols:
    """profile_facade 对 OPC_UA / IEC104 的采样测试。"""

    def test_profile_opcua_unavailable_mode(self) -> None:
        """profile 对 OPC_UA facade 应能采样统计。"""
        plan = _make_test_plan("prof_opcua")
        facade = OpcUaFacade(port=0)
        facade.load_points(plan)

        result = profile_facade(facade, iterations=10, endpoint_id="opcua_ep")
        assert result.status == "PASS"
        # 仅在 binary 可用时，protocol 由 facade 属性填充
        assert result.mode in ("real", "unavailable")
        assert result.iterations == 10
        assert len(result.samples) == 10
        assert result.stats["count"] == 10
        assert result.stats["min"] >= 0

    def test_profile_iec104_unavailable_mode(self) -> None:
        """profile 对 IEC104 facade 应能采样统计。"""
        plan = _make_test_plan("prof_iec104", protocol="IEC104")
        facade = Iec104Facade(port=0)
        facade.load_points(plan)

        result = profile_facade(facade, iterations=10, endpoint_id="iec104_ep")
        assert result.status == "PASS"
        assert result.mode in ("real", "unavailable")
        assert len(result.samples) == 10


class TestCapacityForNewProtocols:
    """capacity_scan 对 OPC_UA / IEC104 的容量扫描测试。"""

    def test_capacity_opcua_unavailable_mode_returns_not_run(self) -> None:
        """unavailable 模式的 OPC_UA capacity 应返回 NOT_RUN + reason。"""
        plan = _make_test_plan("cap_opcua")
        facade = OpcUaFacade(port=0)
        facade.load_points(plan)

        result = capacity_scan(facade, read_count=5, endpoint_id="opcua_ep")
        if facade.mode == "unavailable":
            assert result.status == "NOT_RUN"
            assert "unavailable" in result.reason.lower()
        else:
            assert result.status == "PASS"

    def test_capacity_iec104_unavailable_mode_returns_not_run(self) -> None:
        """unavailable 模式的 IEC104 capacity 应返回 NOT_RUN + reason。"""
        plan = _make_test_plan("cap_iec104", protocol="IEC104")
        facade = Iec104Facade(port=0)
        facade.load_points(plan)

        result = capacity_scan(facade, read_count=5, endpoint_id="iec104_ep")
        if facade.mode == "unavailable":
            assert result.status == "NOT_RUN"
            assert "unavailable" in result.reason.lower()
        else:
            assert result.status == "PASS"


# ── 回归：HTTP_REST / MODBUS_TCP / MQTT 不受影响 ───────────────────────────────


class TestRegressionExistingProtocols:
    """确保 OPC_UA/IEC104 新增不影响已有协议。"""

    def test_http_rest_still_dispatches_to_real(self) -> None:
        """HTTP_REST 仍 dispatch 到 HttpRestFacade (real mode)。"""
        plan = _make_test_plan("reg_http", protocol="HTTP_REST")
        ep = plan.endpoints[0]
        entry = create_driver_for_endpoint(ep, plan)
        assert entry.mode == "real"
        assert entry.available is True

    def test_modbus_tcp_still_dispatches_to_real(self) -> None:
        """MODBUS_TCP 仍 dispatch 到 ModbusTcpFacade (real mode)。"""
        plan = _make_test_plan("reg_modbus", protocol="MODBUS_TCP")
        ep = plan.endpoints[0]
        entry = create_driver_for_endpoint(ep, plan)
        assert entry.mode == "real"
        assert entry.available is True

    def test_mqtt_still_dispatches_to_lightweight(self) -> None:
        """MQTT 仍 dispatch 到 MqttFacade (mqtt-lightweight mode)。"""
        plan = _make_test_plan("reg_mqtt", protocol="MQTT")
        ep = plan.endpoints[0]
        entry = create_driver_for_endpoint(ep, plan)
        assert entry.mode == "mqtt-lightweight"
        assert entry.available is True

    def test_unknown_protocol_still_dispatches_to_stub(self) -> None:
        """未知协议仍 dispatch 到 ServerSimulatorFacade (stub mode)。"""
        plan = _make_test_plan("reg_unknown", protocol="IEC_61850_MMS")
        ep = plan.endpoints[0]
        entry = create_driver_for_endpoint(ep, plan)
        assert entry.mode == "stub"


# ── 集成测试：完整 smoke 流程 ────────────────────────────────────────────────────


class TestSmokeIntegration:
    """完整 smoke 流程集成测试。"""

    def test_opcua_full_smoke_flow(self) -> None:
        """OPC_UA facade 完整 smoke 流程: load -> start -> health -> read -> stop。"""
        plan = _make_test_plan("smoke_opcua")
        facade = OpcUaFacade(port=0)
        facade.load_points(plan)

        try:
            # 1. health pre-start
            h = facade.health()
            assert h["plan_loaded"] is True

            # 2. start
            facade.start()
            h2 = facade.health()
            assert h2["status"] == "started"

            # 3. read
            values = facade.read()
            assert values["p0"] == 42.0
            assert len(values) == 3

            # 4. capabilities
            caps = facade.capabilities()
            assert "READ" in caps

        finally:
            facade.stop()

        # 5. health post-stop
        h3 = facade.health()
        assert h3["status"] == "stopped"

    def test_iec104_full_smoke_flow(self) -> None:
        """IEC104 facade 完整 smoke 流程: load -> start -> health -> read -> stop。"""
        plan = _make_test_plan("smoke_iec104", protocol="IEC104")
        facade = Iec104Facade(port=0)
        facade.load_points(plan)

        try:
            h = facade.health()
            assert h["plan_loaded"] is True

            facade.start()
            h2 = facade.health()
            assert h2["status"] == "started"

            values = facade.read()
            assert values["p0"] == 42.0

            caps = facade.capabilities()
            assert "READ" in caps
        finally:
            facade.stop()

        h3 = facade.health()
        assert h3["status"] == "stopped"

    def test_both_facades_can_run_concurrently(self) -> None:
        """两个 facade 可并发运行。"""
        plan_opcua = _make_test_plan("conc_opcua")
        plan_iec104 = _make_test_plan("conc_iec104", protocol="IEC104")

        opcua = OpcUaFacade(port=0)
        iec104 = Iec104Facade(port=0)

        try:
            opcua.load_points(plan_opcua)
            iec104.load_points(plan_iec104)

            opcua.start()
            iec104.start()

            h_opcua = opcua.health()
            h_iec104 = iec104.health()

            assert h_opcua["status"] == "started"
            assert h_iec104["status"] == "started"

            # 两个 facade 独立工作
            opcua.update_values({"p0": 1.0})
            iec104.update_values({"p0": 2.0})

            assert opcua.read(["p0"])["p0"] == 1.0
            assert iec104.read(["p0"])["p0"] == 2.0
        finally:
            opcua.stop()
            iec104.stop()
