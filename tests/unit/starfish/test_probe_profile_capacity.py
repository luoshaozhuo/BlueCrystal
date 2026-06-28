"""Starfish runtime 诊断工具测试。

验证：
1. probe_facade 最小可用性探测（start/health/load_points/read）。
2. profile_facade read 采样统计（count/min/max/avg）。
3. capacity_scan 轻量容量扫描（endpoint_count/point_count/read_count）。
4. 边界：空 plan、stub mode、不支持协议、未启动 facade。

测试阶段：开发期验证 (P1)。
使用的替身：HttpRestDriverAdapter (real)、ModbusTcpDriverAdapter (real)、
  MqttDriverAdapter (mqtt-lightweight)、ServerSimulatorDriverAdapter (stub)。
外部依赖：无（纯 Python 标准库）。
不能证明：生产级性能结论、生产容量规划、多并发压力。
NOT_RUN 条件：无。
"""

from __future__ import annotations

from starfish.domain.server_config import (
    StarfishServerConfig,
    StarfishEndpointConfig,
    StarfishPointConfig,
)
from starfish.adapters.drivers.simulator.server_simulator_driver_adapter import ServerSimulatorDriverAdapter
from starfish.adapters.drivers.protocol.http.http_rest_driver_adapter import HttpRestDriverAdapter
from starfish.adapters.drivers.modbus.modbus_tcp_driver_adapter import ModbusTcpDriverAdapter
from starfish.adapters.drivers.protocol.mqtt.mqtt_driver_adapter import MqttDriverAdapter
from starfish.adapters.drivers.iec.iec101_driver_adapter import Iec101DriverAdapter
from starfish.adapters.drivers.modbus.modbus_rtu_driver_adapter import ModbusRtuDriverAdapter
from starfish.adapters.drivers.ads.ads_driver_adapter import AdsDriverAdapter
from starfish.adapters.drivers.iec.goose_driver_adapter import GooseDriverAdapter
from starfish.adapters.drivers.iec.sv_driver_adapter import SvDriverAdapter
from starfish.container import (
    create_ads_driver_adapter,
    create_goose_driver_adapter,
    create_http_rest_driver_adapter,
    create_iec101_driver_adapter,
    create_modbus_rtu_driver_adapter,
    create_modbus_tcp_driver_adapter,
    create_mqtt_driver_adapter,
    create_server_simulator_driver_adapter,
    create_sv_driver_adapter,
)
from whale.ingest.diagnostics.probe import ProbeResult, probe_facade
from whale.ingest.diagnostics.profile import ProfileResult, profile_facade
from whale.ingest.diagnostics.capacity import CapacityResult, capacity_scan


# ── 共享 helpers ────────────────────────────────────────────────────────────────


def _make_minimal_plan(
    scenario_id: str = "tools_test",
    initial_values: dict | None = None,
    protocol_name: str = "OPC_UA",
) -> StarfishServerConfig:
    """构造最小测试用 StarfishServerConfig。

    Args:
        scenario_id: 场景标识。
        initial_values: 初始值 dict。
        protocol_name: 协议名。

    Returns:
        测试用 StarfishServerConfig。
    """
    if initial_values is None:
        initial_values = {"point_0": 0.0, "point_1": 1.0}

    return StarfishServerConfig(
        schema_version="1.0.0",
        scenario_id=scenario_id,
        synthetic=True,
        server_name=f"{scenario_id}_server",
        endpoints=[
            StarfishEndpointConfig(
                endpoint_id=f"{scenario_id}_ep",
                protocol=protocol_name,
                host="127.0.0.1",
                port=0,
            )
        ],
        points=[
            StarfishPointConfig(
                point_id="point_0",
                point_name="Point 0",
                node_key="/points/0",
                value_type="Float",
                access_mode="RO",
            ),
            StarfishPointConfig(
                point_id="point_1",
                point_name="Point 1",
                node_key="/points/1",
                value_type="Float",
                access_mode="RO",
            ),
        ],
        capabilities=["READ"],
        initial_values=initial_values,
    )


# ── probe 测试 ──────────────────────────────────────────────────────────────────


class TestProbeFacade:
    """probe_facade 最小探测测试。"""

    def test_probe_stub_facade_pass(self) -> None:
        """stub facade 探针应返回 PASS。"""
        plan = _make_minimal_plan("probe_stub")
        facade = create_server_simulator_driver_adapter()
        result = probe_facade(facade, plan=plan, endpoint_id="stub_ep")
        assert result.status == "PASS"
        assert result.protocol == ""
        assert result.endpoint_id == "stub_ep"
        assert "read" in result.details
        assert result.details["read"]["point_count"] == 2

    def test_probe_stub_facade_without_plan(self) -> None:
        """无 plan 时探针跳过 load_points，仍应 PASS。"""
        facade = create_server_simulator_driver_adapter()
        result = probe_facade(facade, endpoint_id="no_plan_ep")
        assert result.status == "PASS"
        assert "load_points" not in result.details

    def test_probe_http_rest_facade_pass(self) -> None:
        """HTTP REST real facade 探针应返回 PASS。"""
        plan = _make_minimal_plan(
            "probe_http",
            protocol_name="HTTP_REST",
        )
        facade = create_http_rest_driver_adapter(port=0)
        result = probe_facade(facade, plan=plan, endpoint_id="http_ep")
        assert result.status == "PASS"
        assert result.mode == "real"
        assert result.protocol == "HTTP_REST"
        assert "health" in result.details
        assert result.details["health"]["running"] is True
        assert "read" in result.details

        # cleanup
        facade.stop()

    def test_probe_modbus_facade_pass(self) -> None:
        """Modbus TCP real facade 探针应返回 PASS。"""
        plan = _make_minimal_plan(
            "probe_modbus",
            protocol_name="MODBUS_TCP",
            initial_values={"a": 100, "b": 200},
        )
        facade = create_modbus_tcp_driver_adapter(port=0)
        result = probe_facade(facade, plan=plan, endpoint_id="modbus_ep")
        assert result.status == "PASS"
        assert result.mode == "real"
        assert result.protocol == "MODBUS_TCP"

        facade.stop()

    def test_probe_mqtt_facade_pass(self) -> None:
        """MQTT lightweight facade 探针应返回 PASS。"""
        plan = _make_minimal_plan(
            "probe_mqtt",
            protocol_name="MQTT",
        )
        facade = create_mqtt_driver_adapter(port=0)
        result = probe_facade(facade, plan=plan, endpoint_id="mqtt_ep")
        assert result.status == "PASS"
        assert result.mode == "mqtt-lightweight"
        assert result.protocol == "MQTT"

        facade.stop()

    def test_probe_with_specific_point_ids(self) -> None:
        """指定 read_point_ids 时只探测这些点。"""
        plan = _make_minimal_plan("probe_specific")
        facade = create_server_simulator_driver_adapter()
        result = probe_facade(
            facade, plan=plan,
            read_point_ids=["point_0"],
            endpoint_id="specific_ep",
        )
        assert result.status == "PASS"
        assert result.details["read"]["point_count"] == 1
        assert result.details["read"]["sample"] == {"point_0": 0.0}

    def test_probe_skip_start(self) -> None:
        """skip_start=True 时跳过 start 步骤。"""
        plan = _make_minimal_plan("probe_skip_start")
        facade = create_http_rest_driver_adapter(port=0)
        facade.start()

        result = probe_facade(facade, plan=plan, skip_start=True)
        assert result.status == "PASS"

        facade.stop()

    def test_probe_iec101_facade_pass(self) -> None:
        """IEC101 facade 探针应返回 PASS
        （mode 可能为 codec-enhanced/codec-enhanced-plus/codec-skeleton/
        environment-pending/codebase-pending）。"""
        plan = _make_minimal_plan("probe_iec101", protocol_name="IEC101")
        facade = create_iec101_driver_adapter()
        result = probe_facade(facade, plan=plan, endpoint_id="iec101_ep")
        assert result.status == "PASS"
        assert result.mode in (
            "codec-enhanced",
            "codec-enhanced-plus",
            "codec-skeleton",
            "environment-pending",
            "codebase-pending",
        )
        assert result.protocol == "IEC101"

    def test_probe_modbus_rtu_facade_pass(self) -> None:
        """Modbus RTU facade 探针应返回 PASS
        （mode 可能为 rtu-lightweight 或 codebase-pending）。"""
        plan = _make_minimal_plan("probe_modbus_rtu", protocol_name="MODBUS_RTU")
        # 根据 PTY 可用性选择模式
        from starfish.infrastructure.drivers.backend_factory import probe_modbus_rtu_binary
        pty_ok, _ = probe_modbus_rtu_binary()
        mode = "rtu-lightweight" if pty_ok else "codebase-pending"
        facade = create_modbus_rtu_driver_adapter(mode=mode)
        result = probe_facade(facade, plan=plan, endpoint_id="modbus_rtu_ep")
        assert result.status == "PASS"
        assert result.mode in ("rtu-lightweight", "codebase-pending")
        assert result.protocol == "MODBUS_RTU"

        if mode == "rtu-lightweight":
            facade.stop()

    def test_probe_ads_facade_pass(self) -> None:
        """Beckhoff ADS codebase-pending facade 探针应返回 PASS。"""
        plan = _make_minimal_plan("probe_ads", protocol_name="BECKHOFF_ADS")
        facade = create_ads_driver_adapter()
        result = probe_facade(facade, plan=plan, endpoint_id="ads_ep")
        assert result.status == "PASS"
        assert result.mode == "codebase-pending"
        assert result.protocol == "BECKHOFF_ADS"

    def test_probe_goose_facade_pass(self) -> None:
        """GOOSE environment-pending facade 探针应返回 PASS。"""
        plan = _make_minimal_plan("probe_goose", protocol_name="GOOSE")
        facade = create_goose_driver_adapter()
        result = probe_facade(facade, plan=plan, endpoint_id="goose_ep")
        assert result.status == "PASS"
        assert result.mode == "environment-pending"
        assert result.protocol == "GOOSE"

    def test_probe_sv_facade_pass(self) -> None:
        """SV environment-pending facade 探针应返回 PASS。"""
        plan = _make_minimal_plan("probe_sv", protocol_name="SV")
        facade = create_sv_driver_adapter()
        result = probe_facade(facade, plan=plan, endpoint_id="sv_ep")
        assert result.status == "PASS"
        assert result.mode == "environment-pending"
        assert result.protocol == "SV"

    def test_probe_result_dataclass_defaults(self) -> None:
        """ProbeResult 默认值检查。"""
        r = ProbeResult()
        assert r.status == "NOT_RUN"
        assert r.protocol == ""
        assert r.mode == ""
        assert r.scenario_id == ""
        assert r.endpoint_id == ""
        assert r.reason == ""
        assert r.details == {}


# ── profile 测试 ────────────────────────────────────────────────────────────────


class TestProfileFacade:
    """profile_facade read 采样测试。"""

    def test_profile_stub_facade(self) -> None:
        """stub facade 的 profile 应返回有效统计。"""
        plan = _make_minimal_plan("profile_stub")
        facade = create_server_simulator_driver_adapter()
        facade.load_points(plan)

        result = profile_facade(facade, iterations=50, endpoint_id="stub_ep")
        assert result.status == "PASS"
        assert result.iterations == 50
        assert len(result.samples) == 50
        assert result.duration_ms >= 0
        assert result.stats["count"] == 50
        assert result.stats["min"] >= 0
        assert result.stats["max"] >= result.stats["min"]
        assert result.stats["avg"] >= result.stats["min"]
        assert result.stats["avg"] <= result.stats["max"]

    def test_profile_http_rest_facade(self) -> None:
        """HTTP REST real facade 的 profile 应正常工作。"""
        plan = _make_minimal_plan(
            "profile_http",
            protocol_name="HTTP_REST",
        )
        facade = create_http_rest_driver_adapter(port=0)
        facade.load_points(plan)
        facade.start()

        try:
            result = profile_facade(
                facade, iterations=20,
                endpoint_id="http_ep",
                scenario_id=plan.scenario_id,
            )
            assert result.status == "PASS"
            assert result.iterations == 20
            assert len(result.samples) == 20
            assert result.protocol == "HTTP_REST"
            assert result.mode == "real"
            assert result.scenario_id == "profile_http"
            assert result.stats["count"] == 20
        finally:
            facade.stop()

    def test_profile_with_specific_point_ids(self) -> None:
        """指定 point_ids 时 profile 只读取这些点。"""
        plan = _make_minimal_plan("profile_specific")
        facade = create_server_simulator_driver_adapter()
        facade.load_points(plan)

        result = profile_facade(
            facade, iterations=10,
            point_ids=["point_0"],
        )
        assert result.status == "PASS"
        assert result.iterations == 10
        assert len(result.samples) == 10

    def test_profile_zero_iterations_fails(self) -> None:
        """iterations < 1 时应返回 FAIL。"""
        facade = create_server_simulator_driver_adapter()
        result = profile_facade(facade, iterations=0)
        assert result.status == "FAIL"
        assert "iterations" in result.reason

    def test_profile_iec101_facade(self) -> None:
        """IEC101 facade 的 profile 应 PASS
        （mode 可能为 codec-enhanced/codec-enhanced-plus/codec-skeleton/
        environment-pending/codebase-pending）。"""
        plan = _make_minimal_plan("profile_iec101", protocol_name="IEC101")
        facade = create_iec101_driver_adapter()
        facade.load_points(plan)
        result = profile_facade(facade, iterations=30, endpoint_id="iec101_ep")
        assert result.status == "PASS"
        assert result.iterations == 30
        assert result.mode in (
            "codec-enhanced",
            "codec-enhanced-plus",
            "codec-skeleton",
            "environment-pending",
            "codebase-pending",
        )
        assert result.protocol == "IEC101"

    def test_capacity_iec101_not_run(self) -> None:
        """Round 17 验证：IEC101 codec-only 模式下 capacity_scan 仍为 NOT_RUN。

        IEC101 不在 _CAPACITY_SUPPORTED 中，capacity_scan 必须返回
        NOT_RUN + reason（"协议 'IEC101' 不在容量扫描支持列表中"）。
        不得因 codec-enhanced-plus 模式升级而误判为 PASS。
        """
        plan = _make_minimal_plan(
            "capacity_iec101_codec_plus", protocol_name="IEC101",
        )
        facade = create_iec101_driver_adapter()
        facade.load_points(plan)
        result = capacity_scan(facade, endpoint_id="iec101_capacity")
        assert result.status == "NOT_RUN", (
            f"IEC101 codec-enhanced-plus capacity 应为 NOT_RUN，实际 "
            f"{result.status}: {result.reason}"
        )
        assert result.protocol == "IEC101"
        assert "不在容量扫描支持列表中" in result.reason

    def test_probe_iec101_health_includes_codec_plus_diagnosis(self) -> None:
        """Round 17 验证：probe_facade 走 IEC101 codec-enhanced-plus 时，
        health() 必须显式包含 codec_enhanced_plus_ready 诊断字段。
        """
        plan = _make_minimal_plan(
            "probe_iec101_codec_plus_health", protocol_name="IEC101",
        )
        facade = create_iec101_driver_adapter()
        result = probe_facade(facade, plan=plan, endpoint_id="iec101_probe")
        assert result.status == "PASS"
        assert result.mode == "codec-enhanced-plus"
        # health() detail 中应含 codec_enhanced_plus_ready
        assert "health" in result.details
        health = result.details["health"]
        assert "diagnosis" in health
        diag = health["diagnosis"]
        assert diag.get("codec_enhanced_plus_ready") is True
        # reason 应明确为 codec-enhanced-plus 文案
        assert "codec-enhanced-plus" in health["reason"]
        assert "supports_server=false" in health["reason"]
        assert "supports_serial_runtime=false" in health["reason"]

    def test_profile_goose_facade(self) -> None:
        """GOOSE environment-pending facade 的 profile 应 PASS。"""
        plan = _make_minimal_plan("profile_goose", protocol_name="GOOSE")
        facade = create_goose_driver_adapter()
        facade.load_points(plan)
        result = profile_facade(facade, iterations=20, endpoint_id="goose_ep")
        assert result.status == "PASS"
        assert result.mode == "environment-pending"
        assert result.protocol == "GOOSE"

    def test_profile_sv_facade(self) -> None:
        """SV environment-pending facade 的 profile 应 PASS。"""
        plan = _make_minimal_plan("profile_sv", protocol_name="SV")
        facade = create_sv_driver_adapter()
        facade.load_points(plan)
        result = profile_facade(facade, iterations=20, endpoint_id="sv_ep")
        assert result.status == "PASS"
        assert result.mode == "environment-pending"
        assert result.protocol == "SV"

    def test_profile_result_dataclass_defaults(self) -> None:
        """ProfileResult 默认值检查。"""
        r = ProfileResult()
        assert r.status == "NOT_RUN"
        assert r.iterations == 0
        assert r.duration_ms == 0.0
        assert r.stats == {}
        assert r.samples == []


# ── capacity 测试 ────────────────────────────────────────────────────────────────


class TestCapacityScan:
    """capacity_scan 轻量容量扫描测试。"""

    def test_capacity_http_rest_pass(self) -> None:
        """HTTP REST facade 容量扫描应 PASS。

        注意: _make_minimal_plan 始终创建 2 个 StarfishPointConfig 条目，
        因此 health().point_count 固定为 2，与 initial_values 条目数无关。
        max_tested_points 反映 read() 返回的实际点位数（来自 initial_values）。
        """
        plan = _make_minimal_plan(
            "capacity_http",
            protocol_name="HTTP_REST",
            initial_values={f"p{i}": i for i in range(10)},
        )
        facade = create_http_rest_driver_adapter(port=0)
        facade.load_points(plan)
        facade.start()

        try:
            result = capacity_scan(
                facade, read_count=5,
                endpoint_id="http_ep",
                scenario_id=plan.scenario_id,
            )
            assert result.status == "PASS"
            assert result.protocol == "HTTP_REST"
            assert result.mode == "real"
            # read() 返回 load_points 后的内存值 (10 项 initial_values)
            assert result.max_tested_points == 10
            assert result.read_count == 5
            # health().point_count 来自 len(plan.points) = 2 (两个 StarfishPointConfig)
            assert result.point_count == 2
        finally:
            facade.stop()

    def test_capacity_modbus_pass(self) -> None:
        """Modbus TCP facade 容量扫描应 PASS。"""
        plan = _make_minimal_plan(
            "capacity_modbus",
            protocol_name="MODBUS_TCP",
            initial_values={"a": 1, "b": 2, "c": 3},
        )
        facade = create_modbus_tcp_driver_adapter(port=0)
        facade.load_points(plan)
        facade.start()

        try:
            result = capacity_scan(facade, read_count=3, endpoint_id="modbus_ep")
            assert result.status == "PASS"
            assert result.protocol == "MODBUS_TCP"
            assert result.mode == "real"
            assert result.max_tested_points == 3
        finally:
            facade.stop()

    def test_capacity_mqtt_pass(self) -> None:
        """MQTT lightweight facade 容量扫描应 PASS。"""
        plan = _make_minimal_plan(
            "capacity_mqtt",
            protocol_name="MQTT",
            initial_values={"x": 10, "y": 20},
        )
        facade = create_mqtt_driver_adapter(port=0)
        facade.load_points(plan)
        facade.start()

        try:
            result = capacity_scan(facade, read_count=3, endpoint_id="mqtt_ep")
            assert result.status == "PASS"
            assert result.protocol == "MQTT"
            assert result.mode == "mqtt-lightweight"
            assert result.max_tested_points == 2
        finally:
            facade.stop()

    def test_capacity_pending_protocols_not_run(self) -> None:
        """codebase-pending 和 environment-pending 协议应返回 NOT_RUN。

        IEC101/ADS/GOOSE/SV 不在 _CAPACITY_SUPPORTED 中，
        容量扫描应报告 NOT_RUN。MODBUS_RTU 现在在 _CAPACITY_SUPPORTED 中。
        """
        facades = [
            ("IEC101", create_iec101_driver_adapter()),
            ("BECKHOFF_ADS", create_ads_driver_adapter()),
            ("GOOSE", create_goose_driver_adapter()),
            ("SV", create_sv_driver_adapter()),
        ]
        plan = _make_minimal_plan("capacity_pending")
        for name, facade in facades:
            facade.load_points(plan)
            result = capacity_scan(facade, endpoint_id=f"{name}_ep")
            assert result.status == "NOT_RUN", (
                f"{name} capacity 应为 NOT_RUN, 实际 {result.status}"
            )
            assert "不在容量扫描支持列表中" in result.reason, (
                f"{name} reason 应说明不在支持列表中: {result.reason}"
            )

    def test_capacity_modbus_rtu_supported(self) -> None:
        """MODBUS_RTU 现在在 _CAPACITY_SUPPORTED 中，容量扫描应执行。"""
        plan = _make_minimal_plan(
            "capacity_modbus_rtu",
            protocol_name="MODBUS_RTU",
            initial_values={"a": 1, "b": 2},
        )
        from starfish.infrastructure.drivers.backend_factory import probe_modbus_rtu_binary
        pty_ok, _ = probe_modbus_rtu_binary()
        mode = "rtu-lightweight" if pty_ok else "codebase-pending"
        facade = create_modbus_rtu_driver_adapter(mode=mode)
        facade.load_points(plan)

        result = capacity_scan(facade, endpoint_id="modbus_rtu_cap")
        if pty_ok:
            # rtu-lightweight: 在支持列表中
            assert result.status == "PASS", (
                f"rtu-lightweight MODBUS_RTU capacity 应为 PASS，"
                f"实际 {result.status}: {result.reason}"
            )
        else:
            # codebase-pending mode 也在支持列表中
            assert result.status == "PASS", (
                f"MODBUS_RTU capacity 应为 PASS，"
                f"实际 {result.status}: {result.reason}"
            )

        if mode == "rtu-lightweight":
            facade.stop()

    def test_capacity_unsupported_protocol_not_run(self) -> None:
        """不支持协议（stub/OPC_UA）应返回 NOT_RUN。

        ServerSimulatorDriverAdapter 无 protocol 属性，capacity_scan 中
        result.protocol 为空字符串，不在支持列表中 -> NOT_RUN。
        """
        plan = _make_minimal_plan("capacity_stub", protocol_name="OPC_UA")
        facade = create_server_simulator_driver_adapter()
        facade.load_points(plan)

        result = capacity_scan(facade, endpoint_id="stub_ep")
        assert result.status == "NOT_RUN"
        assert result.protocol == ""
        assert "不在容量扫描支持列表中" in result.reason

    def test_capacity_zero_points(self) -> None:
        """空 initial_values 时 max_tested_points 应为 0。

        point_count 来自 len(plan.points) = 2（fixture 固定值），
        与 initial_values 条目数无关。
        """
        plan = _make_minimal_plan(
            "capacity_empty",
            protocol_name="HTTP_REST",
            initial_values={},
        )
        facade = create_http_rest_driver_adapter(port=0)
        facade.load_points(plan)
        facade.start()

        try:
            result = capacity_scan(facade, read_count=3)
            assert result.status == "PASS"
            assert result.max_tested_points == 0
            # point_count 来自 len(plan.points) = 2
            assert result.point_count == 2
        finally:
            facade.stop()

    def test_capacity_result_dataclass_defaults(self) -> None:
        """CapacityResult 默认值检查。"""
        r = CapacityResult()
        assert r.status == "NOT_RUN"
        assert r.endpoint_count == 0
        assert r.point_count == 0
        assert r.max_tested_points == 0
        assert r.read_count == 0


# ── 集成测试：probe + profile + capacity 组合 ───────────────────────────────────


class TestToolsIntegration:
    """probe / profile / capacity 组合使用测试。"""

    def test_probe_then_profile_then_capacity_on_http_rest(self) -> None:
        """对同一 HTTP REST facade 依次执行 probe/profile/capacity。"""
        plan = _make_minimal_plan(
            "tools_int_http",
            protocol_name="HTTP_REST",
            initial_values={f"p{i}": float(i) for i in range(5)},
        )
        facade = create_http_rest_driver_adapter(port=0)
        facade.load_points(plan)

        # 1. probe
        probe_result = probe_facade(
            facade, plan=plan, endpoint_id="int_ep",
        )
        assert probe_result.status == "PASS"

        # 2. profile (facade 已通过 probe start)
        profile_result = profile_facade(
            facade, iterations=20, endpoint_id="int_ep",
        )
        assert profile_result.status == "PASS"
        assert profile_result.iterations == 20

        # 3. capacity
        cap_result = capacity_scan(
            facade, read_count=5, endpoint_id="int_ep",
        )
        assert cap_result.status == "PASS"
        assert cap_result.max_tested_points == 5

        facade.stop()

    def test_probe_then_profile_on_mqtt(self) -> None:
        """对 MQTT lightweight facade 依次执行 probe/profile。"""
        plan = _make_minimal_plan(
            "tools_int_mqtt",
            protocol_name="MQTT",
        )
        facade = create_mqtt_driver_adapter(port=0)
        facade.load_points(plan)

        probe_result = probe_facade(facade, plan=plan, endpoint_id="mqtt_int")
        assert probe_result.status == "PASS"
        assert probe_result.mode == "mqtt-lightweight"

        profile_result = profile_facade(facade, iterations=10)
        assert profile_result.status == "PASS"

        facade.stop()


# ── Round 20 IEC101 codec capabilities 增量测试 ───────────────────────────────


class TestIec101Round20Capabilities:
    """Round 20：IEC101 facade capabilities 增量不影响 probe/profile/capacity 行为。"""

    def test_probe_iec101_round20_still_pass(self) -> None:
        """Round 20：IEC101 probe 仍 PASS（codec-only 模式下 NOT_RUN/CODEC_ONLY 不影响 probe）。"""
        from starfish.adapters.drivers.iec.iec101_driver_adapter import Iec101DriverAdapter
        plan = _make_minimal_plan("probe_iec101_round20", protocol_name="IEC101")
        facade = create_iec101_driver_adapter()
        result = probe_facade(facade, plan=plan, endpoint_id="iec101_ep_r20")
        assert result.status == "PASS"
        assert result.protocol == "IEC101"
        # mode 仍为 codec-enhanced-* 或 environment-pending / codebase-pending
        assert result.mode in (
            "codec-enhanced",
            "codec-enhanced-plus",
            "codec-skeleton",
            "environment-pending",
            "codebase-pending",
        )

    def test_profile_iec101_round20_still_pass(self) -> None:
        """Round 20：IEC101 profile 仍 PASS。"""
        from starfish.adapters.drivers.iec.iec101_driver_adapter import Iec101DriverAdapter
        plan = _make_minimal_plan("profile_iec101_round20", protocol_name="IEC101")
        facade = create_iec101_driver_adapter()
        facade.load_points(plan)
        result = profile_facade(facade, iterations=20, endpoint_id="iec101_profile_r20")
        assert result.status == "PASS"
        assert result.protocol == "IEC101"

    def test_capacity_iec101_round20_still_not_run(self) -> None:
        """Round 20：IEC101 capacity 仍 NOT_RUN（codec 增量不升级 capacity）。"""
        from starfish.adapters.drivers.iec.iec101_driver_adapter import Iec101DriverAdapter
        plan = _make_minimal_plan("capacity_iec101_round20", protocol_name="IEC101")
        facade = create_iec101_driver_adapter()
        facade.load_points(plan)
        result = capacity_scan(facade, endpoint_id="iec101_capacity_r20")
        assert result.status == "NOT_RUN"
        assert "不在容量扫描支持列表中" in result.reason

    def test_iec101_health_round20_diagnosis(self) -> None:
        """Round 20：IEC101 health() diagnosis 仍为 codec-enhanced-plus 模式。"""
        from starfish.adapters.drivers.iec.iec101_driver_adapter import Iec101DriverAdapter
        plan = _make_minimal_plan("health_iec101_round20", protocol_name="IEC101")
        facade = create_iec101_driver_adapter()
        result = probe_facade(facade, plan=plan, endpoint_id="iec101_health_r20")
        assert "health" in result.details
        health = result.details["health"]
        diag = health["diagnosis"]
        # codec_enhanced_plus_ready 仍为 True
        assert diag.get("codec_enhanced_plus_ready") is True
        # reason 仍包含 supports_server=false / supports_serial_runtime=false
        assert "supports_server=false" in health["reason"]
        assert "supports_serial_runtime=false" in health["reason"]
