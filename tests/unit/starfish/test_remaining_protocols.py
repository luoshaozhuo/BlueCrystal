"""Starfish 剩余 5 个协议 facade 测试（Round 10 新增）。

验证 IEC101 / MODBUS_RTU / Beckhoff ADS / GOOSE / SV 五个 pending 协议 facade：
1. 构造、mode、probe 返回 False。
2. NOT_IMPLEMENTED 语义（write/subscribe/report 均抛出 UnsupportedOperation）。
3. 基本生命周期（start/stop/health/load_points/read/update_values/capabilities）。

测试阶段：开发期验证 (P1)。
使用的替身：in-memory stub facade（所有被测 facade 均为 stub/pending 模式）。
外部依赖：无（纯内存操作）。
不能证明：真实协议 server 生命周期、网络连通性、协议帧正确性。
NOT_RUN 条件：无。
"""

from __future__ import annotations

import pytest

from starfish.domain.server_config import StarfishServerConfig, StarfishEndpointConfig, StarfishPointConfig, UnsupportedOperation
from starfish.adapters.drivers.iec.iec101_facade import Iec101Facade, probe_iec101_binary
from starfish.adapters.drivers.modbus.modbus_rtu_facade import ModbusRtuFacade, probe_modbus_rtu_binary
from starfish.adapters.drivers.ads.ads_facade import AdsFacade, probe_ads_binary
from starfish.adapters.drivers.iec.goose_facade import GooseFacade, probe_goose_binary
from starfish.adapters.drivers.iec.sv_facade import SvFacade, probe_sv_binary


# ── 共享 fixtures ────────────────────────────────────────────────────────────────


def _make_minimal_plan(scenario_id: str = "test") -> StarfishServerConfig:
    """构造最小测试用 StarfishServerConfig。

    Args:
        scenario_id: 场景标识。

    Returns:
        包含 2 个浮点点位和 READ 能力的 StarfishServerConfig。
    """
    return StarfishServerConfig(
        schema_version="1.0.0",
        scenario_id=scenario_id,
        synthetic=True,
        server_name=f"{scenario_id}_server",
        endpoints=[
            StarfishEndpointConfig(
                endpoint_id=f"{scenario_id}_ep",
                protocol="STUB",
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
        initial_values={"point_a": 1.0, "point_b": 2.0},
    )


# ── IEC101 Facade 测试 ───────────────────────────────────────────────────────────


class TestIec101Facade:
    """IEC101 facade codebase-pending stub 测试。"""

    def test_construction(self) -> None:
        """新建 facade 应为未启动状态，
        mode 为 codec-enhanced（Round 15 增强编解码器就绪）或
        codec-enhanced-plus（Round 16 时间增强）/codec-skeleton/
        environment-pending/codebase-pending。"""
        facade = Iec101Facade()
        assert facade.protocol == "IEC101"
        assert facade.mode in (
            "codec-enhanced",
            "codec-enhanced-plus",
            "codec-skeleton",
            "environment-pending",
            "codebase-pending",
        )

    def test_initial_health(self) -> None:
        """停止状态 health 应反映正确元信息。"""
        facade = Iec101Facade()
        h = facade.health()
        assert h["status"] == "stopped"
        assert h["mode"] in (
            "codec-enhanced",
            "codec-enhanced-plus",
            "codec-skeleton",
            "environment-pending",
            "codebase-pending",
        )
        assert h["protocol"] == "IEC101"
        assert h["running"] is False

    def test_probe_returns_false(self) -> None:
        """probe_iec101_binary 应始终返回 (False, reason)。"""
        ok, reason = probe_iec101_binary()
        assert ok is False
        assert ("codec-skeleton" in reason or "codebase-pending" in reason
                or "environment-pending" in reason or "codec-enhanced" in reason)
        assert "IEC101" in reason

    def test_start_stop_lifecycle(self) -> None:
        """start/stop 基本生命周期。"""
        facade = Iec101Facade()
        facade.start()
        assert facade.health()["status"] == "started"
        facade.stop()
        assert facade.health()["status"] == "stopped"

    def test_start_idempotent(self) -> None:
        """重复 start 为幂等。"""
        facade = Iec101Facade()
        facade.start()
        facade.start()
        assert facade.health()["status"] == "started"
        facade.stop()

    def test_stop_idempotent(self) -> None:
        """重复 stop 为幂等。"""
        facade = Iec101Facade()
        facade.start()
        facade.stop()
        facade.stop()
        assert facade.health()["status"] == "stopped"

    def test_load_points_and_read(self) -> None:
        """load_points 后 read 返回 initial_values。"""
        plan = _make_minimal_plan("iec101_load")
        facade = Iec101Facade()
        facade.load_points(plan)
        values = facade.read()
        assert values["point_a"] == 1.0
        assert values["point_b"] == 2.0

    def test_read_specific_points(self) -> None:
        """指定 point_ids 时应只返回对应值。"""
        plan = _make_minimal_plan("iec101_specific")
        facade = Iec101Facade()
        facade.load_points(plan)
        values = facade.read(["point_a"])
        assert values == {"point_a": 1.0}

    def test_read_nonexistent_point(self) -> None:
        """不存在 point_id 应返回 None。"""
        plan = _make_minimal_plan("iec101_nonexist")
        facade = Iec101Facade()
        facade.load_points(plan)
        values = facade.read(["nonexistent"])
        assert values == {"nonexistent": None}

    def test_update_values(self) -> None:
        """update_values 应更新内存值。"""
        plan = _make_minimal_plan("iec101_update")
        facade = Iec101Facade()
        facade.load_points(plan)
        facade.update_values({"point_a": 99.9, "new_point": 0})
        values = facade.read()
        assert values["point_a"] == 99.9
        assert values["point_b"] == 2.0
        assert values["new_point"] == 0

    def test_capabilities(self) -> None:
        """capabilities 应返回 plan 中的声明。"""
        plan = _make_minimal_plan("iec101_caps")
        facade = Iec101Facade()
        facade.load_points(plan)
        assert facade.capabilities() == ["READ"]

    def test_capabilities_no_plan(self) -> None:
        """未加载 plan 时 capabilities 返回增强编解码器能力声明（Round 15 新增）。"""
        facade = Iec101Facade()
        caps = facade.capabilities()
        # Round 16：mode 可为 codec-enhanced-plus（CP56Time2a+带时标+link-layer skeleton）
        assert (
            "codec_mode=codec-enhanced" in caps
            or "codec_mode=codec-enhanced-plus" in caps
        )
        assert "supports_ft12_frame_codec=true" in caps
        assert "supports_server=false" in caps
        assert "supports_serial_runtime=false" in caps
        # supported_type_ids 应包含 M_SP_NA_1 / M_DP_NA_1 / M_ME_NA_1 / C_SC_NA_1
        type_ids_line = next(
            (c for c in caps if c.startswith("supported_type_ids=")),
            "",
        )
        for tid in ("M_SP_NA_1", "M_DP_NA_1", "M_ME_NA_1", "C_SC_NA_1"):
            assert tid in type_ids_line

    def test_write_raises_unsupported(self) -> None:
        """write 应抛出 UnsupportedOperation。"""
        plan = _make_minimal_plan("iec101_write")
        facade = Iec101Facade()
        facade.load_points(plan)
        with pytest.raises(UnsupportedOperation, match="write"):
            facade.write("point_a", 100)

    def test_subscribe_raises_unsupported(self) -> None:
        """subscribe 应抛出 UnsupportedOperation。"""
        plan = _make_minimal_plan("iec101_sub")
        facade = Iec101Facade()
        facade.load_points(plan)
        with pytest.raises(UnsupportedOperation, match="subscribe"):
            facade.subscribe(["point_a"])

    def test_report_raises_unsupported(self) -> None:
        """report 应抛出 UnsupportedOperation。"""
        plan = _make_minimal_plan("iec101_report")
        facade = Iec101Facade()
        facade.load_points(plan)
        with pytest.raises(UnsupportedOperation, match="report"):
            facade.report()

    def test_health_after_load_points(self) -> None:
        """load_points 后 health 应反映 plan 信息。"""
        plan = _make_minimal_plan("iec101_health")
        facade = Iec101Facade()
        facade.load_points(plan)
        h = facade.health()
        assert h["plan_loaded"] is True
        assert h["point_count"] == 2
        assert h["endpoint_count"] == 1
        assert h["synthetic"] is True


# ── MODBUS_RTU Facade 测试 ───────────────────────────────────────────────────────


class TestModbusRtuFacade:
    """MODBUS_RTU facade 测试（codebase-pending 或 rtu-lightweight）。"""

    def test_construction(self) -> None:
        """默认构造应为 codebase-pending 模式（显式指定时）。"""
        facade = ModbusRtuFacade(mode="codebase-pending")
        assert facade.protocol == "MODBUS_RTU"
        assert facade.mode == "codebase-pending"

    def test_construction_rtu_lightweight(self) -> None:
        """rtu-lightweight 模式构造。"""
        facade = ModbusRtuFacade(mode="rtu-lightweight")
        assert facade.protocol == "MODBUS_RTU"
        assert facade.mode == "rtu-lightweight"

    def test_probe_returns_bool_and_reason(self) -> None:
        """probe_modbus_rtu_binary 返回 (bool, str)。"""
        ok, reason = probe_modbus_rtu_binary()
        assert isinstance(ok, bool)
        assert isinstance(reason, str)
        assert len(reason) > 0
        assert "MODBUS_RTU" in reason
        if ok:
            assert "PTY" in reason
            assert "不等同真实串口" in reason
        else:
            assert "codebase-pending" in reason

    def test_start_stop_lifecycle_codebase_pending(self) -> None:
        """codebase-pending 模式 start/stop。"""
        facade = ModbusRtuFacade(mode="codebase-pending")
        facade.start()
        assert facade.health()["status"] == "started"
        facade.stop()
        assert facade.health()["status"] == "stopped"

    def test_load_points_and_read_codebase_pending(self) -> None:
        """codebase-pending 模式 load_points/read。"""
        plan = _make_minimal_plan("modbus_rtu_load")
        facade = ModbusRtuFacade(mode="codebase-pending")
        facade.load_points(plan)
        values = facade.read()
        assert values["point_a"] == 1.0
        assert values["point_b"] == 2.0

    def test_update_values_codebase_pending(self) -> None:
        """codebase-pending 模式 update_values。"""
        plan = _make_minimal_plan("modbus_rtu_update")
        facade = ModbusRtuFacade(mode="codebase-pending")
        facade.load_points(plan)
        facade.update_values({"point_b": 500})
        assert facade.read(["point_b"]) == {"point_b": 500}

    def test_write_not_implemented_codebase_pending(self) -> None:
        """codebase-pending 模式 write 应抛出 UnsupportedOperation。"""
        plan = _make_minimal_plan("modbus_rtu_write")
        facade = ModbusRtuFacade(mode="codebase-pending")
        facade.load_points(plan)
        with pytest.raises(UnsupportedOperation, match="write"):
            facade.write("point_a", 100)

    def test_subscribe_raises_unsupported(self) -> None:
        """subscribe（所有模式）应抛出 UnsupportedOperation。"""
        plan = _make_minimal_plan("modbus_rtu_sub")
        facade = ModbusRtuFacade(mode="codebase-pending")
        facade.load_points(plan)
        with pytest.raises(UnsupportedOperation, match="subscribe"):
            facade.subscribe(["point_a"])

    def test_report_raises_unsupported(self) -> None:
        """report（所有模式）应抛出 UnsupportedOperation。"""
        plan = _make_minimal_plan("modbus_rtu_report")
        facade = ModbusRtuFacade(mode="codebase-pending")
        facade.load_points(plan)
        with pytest.raises(UnsupportedOperation, match="report"):
            facade.report()


# ── Beckhoff ADS Facade 测试 ─────────────────────────────────────────────────────


class TestAdsFacade:
    """Beckhoff ADS facade codebase-pending stub 测试。"""

    def test_construction(self) -> None:
        facade = AdsFacade()
        assert facade.protocol == "BECKHOFF_ADS"
        assert facade.mode == "codebase-pending"

    def test_probe_returns_false(self) -> None:
        ok, reason = probe_ads_binary()
        assert ok is False
        assert "codebase-pending" in reason

    def test_start_stop_lifecycle(self) -> None:
        facade = AdsFacade()
        facade.start()
        assert facade.health()["status"] == "started"
        facade.stop()
        assert facade.health()["status"] == "stopped"

    def test_load_points_and_read(self) -> None:
        plan = _make_minimal_plan("ads_load")
        facade = AdsFacade()
        facade.load_points(plan)
        values = facade.read()
        assert values["point_a"] == 1.0

    def test_capabilities(self) -> None:
        plan = _make_minimal_plan("ads_caps")
        facade = AdsFacade()
        facade.load_points(plan)
        assert facade.capabilities() == ["READ"]

    def test_write_raises_unsupported(self) -> None:
        plan = _make_minimal_plan("ads_write")
        facade = AdsFacade()
        facade.load_points(plan)
        with pytest.raises(UnsupportedOperation, match="write"):
            facade.write("point_a", 100)

    def test_subscribe_raises_unsupported(self) -> None:
        plan = _make_minimal_plan("ads_sub")
        facade = AdsFacade()
        facade.load_points(plan)
        with pytest.raises(UnsupportedOperation, match="subscribe"):
            facade.subscribe(["point_a"])

    def test_report_raises_unsupported(self) -> None:
        plan = _make_minimal_plan("ads_report")
        facade = AdsFacade()
        facade.load_points(plan)
        with pytest.raises(UnsupportedOperation, match="report"):
            facade.report()


# ── GOOSE Facade 测试 ────────────────────────────────────────────────────────────


class TestGooseFacade:
    """GOOSE facade environment-pending stub 测试。"""

    def test_construction(self) -> None:
        facade = GooseFacade()
        assert facade.protocol == "GOOSE"
        assert facade.mode == "environment-pending"

    def test_probe_returns_false(self) -> None:
        ok, reason = probe_goose_binary()
        assert ok is False
        assert "environment-pending" in reason
        assert "GOOSE" in reason

    def test_start_stop_lifecycle(self) -> None:
        facade = GooseFacade()
        facade.start()
        assert facade.health()["status"] == "started"
        facade.stop()
        assert facade.health()["status"] == "stopped"

    def test_load_points_and_read(self) -> None:
        plan = _make_minimal_plan("goose_load")
        facade = GooseFacade()
        facade.load_points(plan)
        values = facade.read()
        assert values["point_a"] == 1.0
        assert values["point_b"] == 2.0

    def test_health_mode_is_environment_pending(self) -> None:
        """health 应报告 mode=environment-pending。"""
        plan = _make_minimal_plan("goose_health")
        facade = GooseFacade()
        facade.load_points(plan)
        h = facade.health()
        assert h["mode"] == "environment-pending"
        assert h["protocol"] == "GOOSE"
        assert h["running"] is False

    def test_write_raises_unsupported(self) -> None:
        plan = _make_minimal_plan("goose_write")
        facade = GooseFacade()
        facade.load_points(plan)
        with pytest.raises(UnsupportedOperation):
            facade.write("point_a", 100)

    def test_subscribe_raises_unsupported(self) -> None:
        plan = _make_minimal_plan("goose_sub")
        facade = GooseFacade()
        facade.load_points(plan)
        with pytest.raises(UnsupportedOperation):
            facade.subscribe(["point_a"])

    def test_report_raises_unsupported(self) -> None:
        plan = _make_minimal_plan("goose_report")
        facade = GooseFacade()
        facade.load_points(plan)
        with pytest.raises(UnsupportedOperation):
            facade.report()


# ── SV Facade 测试 ───────────────────────────────────────────────────────────────


class TestSvFacade:
    """SV (Sampled Values) facade environment-pending stub 测试。"""

    def test_construction(self) -> None:
        facade = SvFacade()
        assert facade.protocol == "SV"
        assert facade.mode == "environment-pending"

    def test_probe_returns_false(self) -> None:
        ok, reason = probe_sv_binary()
        assert ok is False
        assert "environment-pending" in reason
        assert "SV" in reason

    def test_start_stop_lifecycle(self) -> None:
        facade = SvFacade()
        facade.start()
        assert facade.health()["status"] == "started"
        facade.stop()
        assert facade.health()["status"] == "stopped"

    def test_load_points_and_read(self) -> None:
        plan = _make_minimal_plan("sv_load")
        facade = SvFacade()
        facade.load_points(plan)
        values = facade.read()
        assert values["point_a"] == 1.0
        assert values["point_b"] == 2.0

    def test_update_values_and_read(self) -> None:
        plan = _make_minimal_plan("sv_update")
        facade = SvFacade()
        facade.load_points(plan)
        facade.update_values({"point_a": -999.0})
        assert facade.read(["point_a"]) == {"point_a": -999.0}

    def test_write_raises_unsupported(self) -> None:
        plan = _make_minimal_plan("sv_write")
        facade = SvFacade()
        facade.load_points(plan)
        with pytest.raises(UnsupportedOperation):
            facade.write("point_a", 100)

    def test_subscribe_raises_unsupported(self) -> None:
        plan = _make_minimal_plan("sv_sub")
        facade = SvFacade()
        facade.load_points(plan)
        with pytest.raises(UnsupportedOperation):
            facade.subscribe(["point_a"])

    def test_report_raises_unsupported(self) -> None:
        plan = _make_minimal_plan("sv_report")
        facade = SvFacade()
        facade.load_points(plan)
        with pytest.raises(UnsupportedOperation):
            facade.report()


# ── 跨协议 mode 一致性测试 ───────────────────────────────────────────────────────


class TestPendingFacadeModeConsistency:
    """验证 pending facade 的 mode 一致性。"""

    def test_codebase_pending_facades_mode(self) -> None:
        """IEC101 的 mode 为 codec-enhanced-plus（Round 16）/codec-enhanced
        （Round 15）/codec-skeleton/environment-pending（binary 已编译）/
        codebase-pending（binary 缺失）。ADS 的 mode 始终为 codebase-pending
        （无 .NET runtime / Python ADS 实现）。MODBUS_RTU 默认 mode 根据
        构造参数而定，不在此处断言固定值。
        """
        assert Iec101Facade().mode in (
            "codec-enhanced",
            "codec-enhanced-plus",
            "codec-skeleton",
            "codebase-pending",
            "environment-pending",
        )
        assert AdsFacade().mode == "codebase-pending"

    def test_modbus_rtu_mode_by_construction(self) -> None:
        """MODBUS_RTU facade 的 mode 由构造参数决定。"""
        assert ModbusRtuFacade(mode="codebase-pending").mode == "codebase-pending"
        assert ModbusRtuFacade(mode="rtu-lightweight").mode == "rtu-lightweight"

    def test_environment_pending_facades_mode(self) -> None:
        """GOOSE、SV 的 mode 均为 environment-pending。"""
        assert GooseFacade().mode == "environment-pending"
        assert SvFacade().mode == "environment-pending"

    def test_probes_return_bool_and_reason(self) -> None:
        """所有 pending facade 的 probe 函数均返回 (bool, str) 且 reason 非空。
        MODBUS_RTU probe 在 PTY 可用时可返回 True。
        """
        probes = [
            ("IEC101", probe_iec101_binary, False),
            ("ADS", probe_ads_binary, False),
            ("GOOSE", probe_goose_binary, False),
            ("SV", probe_sv_binary, False),
        ]
        for name, probe_fn, expect_false in probes:
            ok, reason = probe_fn()
            assert ok is False, f"{name} probe 应返回 False"
            assert isinstance(reason, str), f"{name} reason 应为字符串"
            assert len(reason) > 0, f"{name} reason 不应为空"

        # MODBUS_RTU 探针可能返回 True（PTY 可用时）
        ok, reason = probe_modbus_rtu_binary()
        assert isinstance(ok, bool)
        assert isinstance(reason, str)
        assert len(reason) > 0
        if ok:
            assert "PTY" in reason
            assert "不等同真实串口" in reason

    def test_not_implemented_for_codebase_and_environment_pending(self) -> None:
        """codebase-pending 和 environment-pending 模式的
        write/subscribe/report 均抛出 UnsupportedOperation。
        MODBUS_RTU codebase-pending 模式 write 也 NOT_IMPLEMENTED。
        """
        facades = [
            ("IEC101", Iec101Facade()),
            ("ADS", AdsFacade()),
            ("GOOSE", GooseFacade()),
            ("SV", SvFacade()),
        ]
        plan = _make_minimal_plan("notimpl_test")
        for name, facade in facades:
            facade.load_points(plan)
            with pytest.raises(UnsupportedOperation):
                facade.write("point_a", 0)
            with pytest.raises(UnsupportedOperation):
                facade.subscribe(["point_a"])
            with pytest.raises(UnsupportedOperation):
                facade.report()

        # MODBUS_RTU codebase-pending 模式: write/subscribe/report 均 NOT_IMPLEMENTED
        modbus_cp = ModbusRtuFacade(mode="codebase-pending")
        modbus_cp.load_points(plan)
        with pytest.raises(UnsupportedOperation):
            modbus_cp.write("point_a", 0)
        with pytest.raises(UnsupportedOperation):
            modbus_cp.subscribe(["point_a"])
        with pytest.raises(UnsupportedOperation):
            modbus_cp.report()
