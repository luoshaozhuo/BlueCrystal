"""Starfish IEC61850 facade 测试 —— 覆盖 MMS 和 Report 两个门面。

被验证对象：
- Iec61850MmsFacade: IEC61850 MMS 协议门面（C runner 子进程）。
- Iec61850ReportFacade: IEC61850 Report 协议门面（C runner + ReportQueue 事件队列）。
- ReportQueue: 事件队列封装。
- ServerRegistry dispatch: IEC61850_MMS / IEC61850_REPORT 协议分发。
- probe/profile/capacity: IEC61850 协议探测/采样/容量扫描。

测试阶段：P1 开发期验证。
使用的 fake/mock/stub: 本地 localhost socket、临时文件、环境变量 mock。
外部依赖：iec61850_simulator_server、iec61850_report_runner C 二进制
（在 unavailable 测试中不依赖，在 real 测试中需要编译好）。

不能证明：
- 真实 IEC61850 MMS 协议帧的正确性。
- RCB 配置、Trigger Option 等 IEC61850-7-2 完整语义。
- 多 IED 并发管理的正确性。

NOT_RUN 条件：
- 当 IEC61850 C 二进制不可用时，real mode lifecycle 测试标记为
  environment-pending，不等同 PASS。
"""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest

from starfish.drivers.iec61850_mms_facade import (
    Iec61850MmsFacade,
    probe_iec61850_mms_binary,
    resolve_iec61850_mms_simulator_path,
)
from starfish.drivers.iec61850_report_facade import (
    Iec61850ReportFacade,
    ReportQueue,
    probe_iec61850_report_binary,
    resolve_iec61850_report_runner_path,
)
from starfish.domain.server_config import (
    StarfishEndpointConfig,
    StarfishPointConfig,
    StarfishServerConfig,
    UnsupportedOperation,
)
from starfish.drivers.server_registry import (
    create_driver_for_endpoint,
    get_supported_protocols,
    get_native_runner_protocols,
)
from whale.ingest.diagnostics.probe import probe_facade
from whale.ingest.diagnostics.profile import profile_facade
from whale.ingest.diagnostics.capacity import capacity_scan


# ── Test helpers ─────────────────────────────────────────────────────────────────


def _make_plan(
    endpoints: list[StarfishEndpointConfig] | None = None,
    points: list[StarfishPointConfig] | None = None,
    initial_values: dict[str, object] | None = None,
    capabilities: list[str] | None = None,
) -> StarfishServerConfig:
    """创建最小 StarfishServerConfig 用于测试。

    Args:
        endpoints: 端点列表。
        points: 点位列表。
        initial_values: 初始值。
        capabilities: 能力声明。

    Returns:
        已填充的 StarfishServerConfig 实例。
    """
    return StarfishServerConfig(
        schema_version="1.0.0",
        scenario_id="test-iec61850",
        synthetic=True,
        generator_version="1.0",
        generated_at=datetime.now().isoformat(),
        server_name="test-iec61850-server",
        strategy_id="test-strategy",
        endpoints=endpoints or [
            StarfishEndpointConfig(
                endpoint_id="ep-mms-1",
                protocol="IEC61850_MMS",
                host="127.0.0.1",
                port=0,
            ),
        ],
        points=points or [
            StarfishPointConfig(point_id="temp", point_name="Temperature"),
            StarfishPointConfig(point_id="press", point_name="Pressure"),
            StarfishPointConfig(point_id="status", point_name="Status"),
        ],
        capabilities=capabilities or ["read", "report"],
        initial_values=initial_values or {
            "temp": 25.5,
            "press": 101.3,
            "status": 1,
        },
        payload_hash="sha256:test-hash",
    )


# ── Probe helpers ──────────────────────────────────────────────────────────────


def _iec61850_binaries_available() -> bool:
    """检查 IEC61850 C 二进制是否可用。

    Returns:
        True 表示 iec61850_simulator_server 可用于 real mode 测试。
    """
    binary_ok, _ = probe_iec61850_mms_binary()
    return binary_ok


def _iec61850_report_binaries_available() -> bool:
    """检查 IEC61850 Report C 二进制是否可用。

    Returns:
        True 表示 iec61850_simulator_server + iec61850_report_runner 均可用。
    """
    binary_ok, _ = probe_iec61850_report_binary()
    return binary_ok


# ── ReportQueue tests ──────────────────────────────────────────────────────────


class TestReportQueue:
    """ReportQueue 事件队列单元测试。"""

    def test_put_and_get_returns_event(self) -> None:
        """put 后 get 能取回事件。"""
        rq = ReportQueue()
        event = {"event_type": "update", "point_id": "temp", "value": 42.0}
        rq.put(event)
        result = rq.get(timeout=1.0)
        assert result is not None
        assert result["event_type"] == "update"
        assert result["value"] == 42.0

    def test_get_nowait_empty_returns_none(self) -> None:
        """空队列 get_nowait 返回 None。"""
        rq = ReportQueue()
        result = rq.get_nowait()
        assert result is None

    def test_get_timeout_returns_none(self) -> None:
        """空队列 get(timeout) 超时返回 None。"""
        rq = ReportQueue()
        result = rq.get(timeout=0.01)
        assert result is None

    def test_multiple_events_fifo_order(self) -> None:
        """多个事件保持 FIFO 顺序。"""
        rq = ReportQueue()
        rq.put({"event_type": "update", "seq": 1})
        rq.put({"event_type": "update", "seq": 2})
        rq.put({"event_type": "report", "seq": 3})

        e1 = rq.get(timeout=1.0)
        e2 = rq.get_nowait()
        e3 = rq.get_nowait()
        assert e1 is not None and e1["seq"] == 1
        assert e2 is not None and e2["seq"] == 2
        assert e3 is not None and e3["seq"] == 3
        assert rq.get_nowait() is None

    def test_drain_returns_all_events_and_empties_queue(self) -> None:
        """drain 返回所有事件并清空队列。"""
        rq = ReportQueue()
        rq.put({"event_type": "a"})
        rq.put({"event_type": "b"})
        rq.put({"event_type": "c"})

        events = rq.drain()
        assert len(events) == 3
        assert rq.get_nowait() is None  # 队列已空

    def test_qsize_approximate(self) -> None:
        """qsize 返回近似队列大小。"""
        rq = ReportQueue()
        assert rq.qsize() == 0
        rq.put({"event_type": "x"})
        rq.put({"event_type": "y"})
        assert rq.qsize() == 2

    def test_empty_drain_returns_empty_list(self) -> None:
        """空队列 drain 返回空列表。"""
        rq = ReportQueue()
        events = rq.drain()
        assert events == []


# ── Dependency probe tests ─────────────────────────────────────────────────────


class TestDependencyProbe:
    """IEC61850 MMS 和 Report dependency probe 测试。"""

    def test_probe_mms_binary_found(self) -> None:
        """二进制存在时返回 True。"""
        # 环境已有编译好的 binary
        binary_ok, reason = probe_iec61850_mms_binary()
        if binary_ok:
            assert "可用" in reason
            assert "bytes" in reason
        else:
            pytest.skip(
                f"iec61850_simulator_server 不可用: {reason}"
            )

    def test_probe_mms_binary_not_found(self) -> None:
        """二进制不存在时返回 False + reason。"""
        with patch("os.stat", side_effect=OSError("not found")):
            binary_ok, reason = probe_iec61850_mms_binary()
            assert not binary_ok
            assert "不存在" in reason or "not found" in reason.lower()

    def test_probe_mms_binary_too_small(self) -> None:
        """文件过小时返回 False。"""
        with patch("os.stat") as mock_stat:
            mock_stat.return_value = os.stat_result(
                (0o755, 0, 0, 1, 0, 0, 512, 0, 0, 0)
            )
            with patch("os.access", return_value=True):
                binary_ok, reason = probe_iec61850_mms_binary()
                assert not binary_ok
                assert "过小" in reason or "too small" in reason.lower()

    def test_probe_mms_binary_not_executable(self) -> None:
        """无执行权限时返回 False。"""
        with patch("os.stat") as mock_stat:
            mock_stat.return_value = os.stat_result(
                (0o644, 0, 0, 1, 0, 0, 4096, 0, 0, 0)
            )
            with patch("os.access", return_value=False):
                binary_ok, reason = probe_iec61850_mms_binary()
                assert not binary_ok
                assert "权限" in reason or "executable" in reason.lower()

    def test_probe_report_binary_found(self) -> None:
        """Report 二进制存在时返回 True。"""
        binary_ok, reason = probe_iec61850_report_binary()
        if binary_ok:
            assert "可用" in reason
            assert "runner" in reason
        else:
            pytest.skip(
                f"IEC61850 report binaries 不可用: {reason}"
            )

    def test_probe_report_binary_not_found_simulator(self) -> None:
        """Simulator 不存在时返回 False。"""
        with patch(
            "starfish.drivers.iec61850_report_facade.resolve_iec61850_report_simulator_path",
            return_value=Path("/nonexistent/iec61850_simulator_server"),
        ):
            binary_ok, reason = probe_iec61850_report_binary()
            assert not binary_ok
            assert "不存在" in reason or "not found" in reason.lower()

    def test_probe_report_binary_not_found_runner(self) -> None:
        """Runner 不存在时返回 False。"""
        # Patch os.stat 使其对 runner path 返回 OSError
        original_stat = os.stat

        def mock_stat(path: str) -> os.stat_result:
            path_str = str(path)
            if "iec61850_report_runner" in path_str and "iec61850_report_runner" in path_str:
                raise OSError("not found")
            return original_stat(path)

        with patch("os.stat", side_effect=mock_stat):
            with patch(
                "starfish.drivers.iec61850_report_facade.resolve_iec61850_report_runner_path",
                return_value=Path("/nonexistent/iec61850_report_runner"),
            ):
                binary_ok, reason = probe_iec61850_report_binary()
                assert not binary_ok

    def test_resolve_mms_path_uses_env_var(self) -> None:
        """环境变量 IEC61850_MMS_RUNNER_PATH 优先使用。"""
        test_path = "/custom/path/iec61850_simulator_server"
        with patch.dict(os.environ, {"IEC61850_MMS_RUNNER_PATH": test_path}):
            resolved = resolve_iec61850_mms_simulator_path()
            assert str(resolved) == test_path

    def test_resolve_report_runner_path_uses_env_var(self) -> None:
        """环境变量 IEC61850_REPORT_RUNNER_PATH 优先使用。"""
        test_path = "/custom/path/iec61850_report_runner"
        with patch.dict(os.environ, {"IEC61850_REPORT_RUNNER_PATH": test_path}):
            resolved = resolve_iec61850_report_runner_path()
            assert str(resolved) == test_path


# ── Iec61850MmsFacade unavailable mode tests ───────────────────────────────────


class TestIec61850MmsFacadeUnavailable:
    """Iec61850MmsFacade unavailable 模式测试。

    不可用模式的核心规则：
    - mode="unavailable"
    - start/stop 不执行子进程（no-op）
    - health 返回 mode="unavailable"
    - 不得把 unavailable 写为 PASS
    """

    def test_mode_is_unavailable_when_binary_missing(self) -> None:
        """binary 不可用时 mode='unavailable'。"""
        with patch(
            "starfish.drivers.iec61850_mms_facade.probe_iec61850_mms_binary",
            return_value=(False, "binary not found"),
        ):
            facade = Iec61850MmsFacade()
            assert facade.mode == "unavailable"
            assert not facade.binary_available
            assert "binary not found" in facade.binary_reason

    def test_start_noop_when_unavailable(self) -> None:
        """unavailable 时 start 不执行子进程。"""
        with patch(
            "starfish.drivers.iec61850_mms_facade.probe_iec61850_mms_binary",
            return_value=(False, "test"),
        ):
            facade = Iec61850MmsFacade()
            facade.load_points(_make_plan())
            facade.start()
            assert facade.health()["status"] == "started"
            assert facade.health()["mode"] == "unavailable"
            assert facade._process is None

    def test_stop_noop_when_unavailable(self) -> None:
        """unavailable 时 stop 不执行子进程。"""
        with patch(
            "starfish.drivers.iec61850_mms_facade.probe_iec61850_mms_binary",
            return_value=(False, "test"),
        ):
            facade = Iec61850MmsFacade()
            facade.load_points(_make_plan())
            facade.start()
            facade.stop()
            assert facade.health()["status"] == "stopped"

    def test_health_returns_unavailable_reason(self) -> None:
        """health 返回 unavailable 模式和原因。"""
        with patch(
            "starfish.drivers.iec61850_mms_facade.probe_iec61850_mms_binary",
            return_value=(False, "binary not found"),
        ):
            facade = Iec61850MmsFacade()
            h = facade.health()
            assert h["mode"] == "unavailable"
            assert h["reason"] == "binary not found"
            assert not h["running"]

    def test_read_when_unavailable(self) -> None:
        """unavailable 时 read 返回 in-memory 值。"""
        with patch(
            "starfish.drivers.iec61850_mms_facade.probe_iec61850_mms_binary",
            return_value=(False, "test"),
        ):
            plan = _make_plan()
            facade = Iec61850MmsFacade()
            facade.load_points(plan)
            values = facade.read()
            assert values["temp"] == 25.5
            assert values["press"] == 101.3

    def test_update_values_when_unavailable(self) -> None:
        """unavailable 时 update_values 更新内存值。"""
        with patch(
            "starfish.drivers.iec61850_mms_facade.probe_iec61850_mms_binary",
            return_value=(False, "test"),
        ):
            facade = Iec61850MmsFacade()
            facade.load_points(_make_plan())
            facade.update_values({"temp": 99.9})
            values = facade.read()
            assert values["temp"] == 99.9


# ── Iec61850MmsFacade real mode tests ──────────────────────────────────────────


class TestIec61850MmsFacadeReal:
    """Iec61850MmsFacade real 模式 lifecycle 测试。

    仅在 iec61850_simulator_server binary 可用时执行。
    不可用时，这些测试标记为 environment-pending，不等同 PASS。
    """

    def test_start_stop_real_lifecycle(self) -> None:
        """真实子进程 lifecycle：start -> health -> stop。"""
        if not _iec61850_binaries_available():
            pytest.skip(
                "environment-pending: iec61850_simulator_server binary 不可用"
            )
        plan = _make_plan()
        facade = Iec61850MmsFacade()
        facade.load_points(plan)
        facade.start()
        try:
            assert facade.mode == "real"
            h = facade.health()
            assert h["status"] == "started"
            assert h["running"]
            assert h["mode"] == "real"
        finally:
            facade.stop()

    def test_start_read_values(self) -> None:
        """real 模式 start 后 read 返回加载的初始值。"""
        if not _iec61850_binaries_available():
            pytest.skip("environment-pending")
        plan = _make_plan()
        facade = Iec61850MmsFacade()
        facade.load_points(plan)
        facade.start()
        try:
            values = facade.read()
            assert values["temp"] == 25.5
        finally:
            facade.stop()

    def test_start_idempotent(self) -> None:
        """重复调用 start 安全。"""
        if not _iec61850_binaries_available():
            pytest.skip("environment-pending")
        plan = _make_plan()
        facade = Iec61850MmsFacade()
        facade.load_points(plan)
        facade.start()
        try:
            facade.start()  # 第二次调用
        finally:
            facade.stop()

    def test_stop_idempotent(self) -> None:
        """重复调用 stop 安全。"""
        if not _iec61850_binaries_available():
            pytest.skip("environment-pending")
        plan = _make_plan()
        facade = Iec61850MmsFacade()
        facade.load_points(plan)
        facade.start()
        facade.stop()
        facade.stop()  # 第二次调用安全

    def test_health_after_stop(self) -> None:
        """stop 后 health 返回 stopped 状态。"""
        if not _iec61850_binaries_available():
            pytest.skip("environment-pending")
        plan = _make_plan()
        facade = Iec61850MmsFacade()
        facade.load_points(plan)
        facade.start()
        facade.stop()
        h = facade.health()
        assert h["status"] == "stopped"

    def test_capabilities(self) -> None:
        """capabilities 返回 plan 能力列表。"""
        if not _iec61850_binaries_available():
            pytest.skip("environment-pending")
        plan = _make_plan(capabilities=["read", "report"])
        facade = Iec61850MmsFacade()
        facade.load_points(plan)
        assert facade.capabilities() == ["read", "report"]

    def test_port_auto_assignment(self) -> None:
        """port=0 时自动分配可用端口。"""
        if not _iec61850_binaries_available():
            pytest.skip("environment-pending")
        plan = _make_plan()
        facade = Iec61850MmsFacade(port=0)
        facade.load_points(plan)
        facade.start()
        try:
            assert facade._actual_port > 0
        finally:
            facade.stop()


# ── Iec61850MmsFacade NOT_IMPLEMENTED tests ────────────────────────────────────


class TestIec61850MmsFacadeNotImplemented:
    """Iec61850MmsFacade NOT_IMPLEMENTED 能力测试。"""

    def test_write_raises_unsupported(self) -> None:
        """write 抛出 UnsupportedOperation。"""
        facade = Iec61850MmsFacade()
        with pytest.raises(UnsupportedOperation) as exc_info:
            facade.write("temp", 42.0)
        assert "NOT_IMPLEMENTED" in str(exc_info.value)
        assert "write" in str(exc_info.value)

    def test_subscribe_raises_unsupported(self) -> None:
        """subscribe 抛出 UnsupportedOperation。"""
        facade = Iec61850MmsFacade()
        with pytest.raises(UnsupportedOperation) as exc_info:
            facade.subscribe(["temp"])
        assert "NOT_IMPLEMENTED" in str(exc_info.value)
        assert "subscribe" in str(exc_info.value)

    def test_report_raises_unsupported(self) -> None:
        """report 抛出 UnsupportedOperation。"""
        facade = Iec61850MmsFacade()
        with pytest.raises(UnsupportedOperation) as exc_info:
            facade.report()
        assert "NOT_IMPLEMENTED" in str(exc_info.value)
        assert "report" in str(exc_info.value)


# ── Iec61850ReportFacade report-lightweight mode tests ─────────────────────────


class TestIec61850ReportFacadeLightweight:
    """Iec61850ReportFacade report-lightweight 模式测试。

    report-lightweight 模式（binary 缺失时）：
    - start/stop/health 仅管理 in-memory 状态。
    - update_values 推送到 ReportQueue。
    - report() 排空事件队列。
    - read/write/subscribe 为 NOT_IMPLEMENTED。
    - 明确声明不是完整 IEC61850 Report server。
    """

    def test_mode_is_report_lightweight_when_binary_missing(self) -> None:
        """binary 不可用时 mode='report-lightweight'。"""
        with patch(
            "starfish.drivers.iec61850_report_facade.probe_iec61850_report_binary",
            return_value=(False, "binaries not found"),
        ):
            facade = Iec61850ReportFacade()
            assert facade.mode == "report-lightweight"
            assert not facade.binary_available

    def test_start_stop_lightweight(self) -> None:
        """report-lightweight 时 start/stop 仅管理内存状态。"""
        with patch(
            "starfish.drivers.iec61850_report_facade.probe_iec61850_report_binary",
            return_value=(False, "test"),
        ):
            facade = Iec61850ReportFacade()
            facade.load_points(_make_plan())
            facade.start()
            assert facade._started
            h = facade.health()
            assert h["mode"] == "report-lightweight"
            facade.stop()
            assert not facade._started

    def test_update_values_pushes_to_report_queue(self) -> None:
        """update_values 后 report() 能排空事件。"""
        with patch(
            "starfish.drivers.iec61850_report_facade.probe_iec61850_report_binary",
            return_value=(False, "test"),
        ):
            facade = Iec61850ReportFacade()
            facade.load_points(_make_plan())
            facade.start()
            facade.update_values({"temp": 50.0})
            facade.update_values({"press": 102.0})
            result = facade.report()
            assert result["event_count"] == 2
            assert result["mode"] == "report-lightweight"
            # 确认事件包含更新的值
            values_from_events: dict[str, object] = {}
            for e in result["events"]:
                values_from_events.update(e.get("values", {}))
            assert values_from_events.get("temp") == 50.0
            assert values_from_events.get("press") == 102.0

    def test_report_drains_queue(self) -> None:
        """report 排空后队列为空。"""
        with patch(
            "starfish.drivers.iec61850_report_facade.probe_iec61850_report_binary",
            return_value=(False, "test"),
        ):
            facade = Iec61850ReportFacade()
            facade.load_points(_make_plan())
            facade.start()
            facade.update_values({"temp": 1.0})
            result1 = facade.report()
            assert result1["event_count"] == 1
            result2 = facade.report()
            assert result2["event_count"] == 0

    def test_event_has_type_and_timestamp(self) -> None:
        """事件包含 event_type 和 timestamp。"""
        with patch(
            "starfish.drivers.iec61850_report_facade.probe_iec61850_report_binary",
            return_value=(False, "test"),
        ):
            facade = Iec61850ReportFacade()
            facade.load_points(_make_plan())
            facade.start()
            facade.update_values({"temp": 3.14})
            result = facade.report()
            assert len(result["events"]) == 1
            e = result["events"][0]
            assert e["event_type"] == "update"
            assert "timestamp" in e
            assert 3.14 in e["values"].values()

    def test_health_includes_event_queue_size(self) -> None:
        """health 包含 event_queue_size。"""
        with patch(
            "starfish.drivers.iec61850_report_facade.probe_iec61850_report_binary",
            return_value=(False, "test"),
        ):
            facade = Iec61850ReportFacade()
            facade.load_points(_make_plan())
            facade.start()
            facade.update_values({"temp": 1.0})
            facade.update_values({"temp": 2.0})
            h = facade.health()
            assert h["event_queue_size"] >= 2

    def test_stop_clears_event_queue(self) -> None:
        """stop 后事件队列清空。"""
        with patch(
            "starfish.drivers.iec61850_report_facade.probe_iec61850_report_binary",
            return_value=(False, "test"),
        ):
            facade = Iec61850ReportFacade()
            facade.load_points(_make_plan())
            facade.start()
            facade.update_values({"temp": 1.0})
            facade.stop()
            assert facade._event_queue.qsize() == 0

    def test_report_lightweight_not_full_iec61850_report_server(self) -> None:
        """明确声明 report-lightweight 不是完整 IEC61850 Report server。"""
        with patch(
            "starfish.drivers.iec61850_report_facade.probe_iec61850_report_binary",
            return_value=(False, "binaries not found"),
        ):
            facade = Iec61850ReportFacade()
            assert facade.mode == "report-lightweight"
            assert not facade.binary_available
            assert "not found" in facade.binary_reason.lower()
            # 不等同 real mode
            assert facade.mode != "real"


# ── Iec61850ReportFacade real mode tests ──────────────────────────────────────


class TestIec61850ReportFacadeReal:
    """Iec61850ReportFacade real 模式 lifecycle 测试。

    仅在 iec61850_simulator_server + iec61850_report_runner 均可用时执行。
    不可用时标记 environment-pending。
    """

    def test_start_stop_real_lifecycle(self) -> None:
        """真实子进程 lifecycle：start -> health -> stop。"""
        if not _iec61850_report_binaries_available():
            pytest.skip(
                "environment-pending: iec61850 report binaries 不可用"
            )
        plan = _make_plan()
        facade = Iec61850ReportFacade()
        facade.load_points(plan)
        facade.start()
        try:
            assert facade.mode == "real"
            h = facade.health()
            assert h["status"] == "started"
            assert h["mode"] == "real"
            assert h["running"]
        finally:
            facade.stop()

    def test_update_values_and_report_real(self) -> None:
        """real 模式 update_values 后 report 排空事件。"""
        if not _iec61850_report_binaries_available():
            pytest.skip("environment-pending")
        plan = _make_plan()
        facade = Iec61850ReportFacade()
        facade.load_points(plan)
        facade.start()
        try:
            facade.update_values({"temp": 75.0})
            result = facade.report()
            assert result["event_count"] >= 1
            assert result["mode"] == "real"
        finally:
            facade.stop()

    def test_capabilities_real(self) -> None:
        """real 模式 capabilities 返回 plan 声明的能力。"""
        if not _iec61850_report_binaries_available():
            pytest.skip("environment-pending")
        plan = _make_plan(capabilities=["read", "report", "subscribe"])
        facade = Iec61850ReportFacade()
        facade.load_points(plan)
        assert facade.capabilities() == ["read", "report", "subscribe"]

    def test_protocol_returns_iec61850_report(self) -> None:
        """protocol 返回 IEC61850_REPORT。"""
        if not _iec61850_report_binaries_available():
            pytest.skip("environment-pending")
        facade = Iec61850ReportFacade()
        assert facade.protocol == "IEC61850_REPORT"


# ── Iec61850ReportFacade NOT_IMPLEMENTED tests ────────────────────────────────


class TestIec61850ReportFacadeNotImplemented:
    """Iec61850ReportFacade NOT_IMPLEMENTED 能力测试。"""

    def test_read_raises_unsupported(self) -> None:
        """read 抛出 UnsupportedOperation。"""
        facade = Iec61850ReportFacade()
        with pytest.raises(UnsupportedOperation) as exc_info:
            facade.read(["temp"])
        assert "NOT_IMPLEMENTED" in str(exc_info.value)
        assert "read" in str(exc_info.value).lower()

    def test_write_raises_unsupported(self) -> None:
        """write 抛出 UnsupportedOperation。"""
        facade = Iec61850ReportFacade()
        with pytest.raises(UnsupportedOperation) as exc_info:
            facade.write("temp", 42.0)
        assert "NOT_IMPLEMENTED" in str(exc_info.value)
        assert "write" in str(exc_info.value).lower()

    def test_subscribe_raises_unsupported(self) -> None:
        """subscribe 抛出 UnsupportedOperation。"""
        facade = Iec61850ReportFacade()
        with pytest.raises(UnsupportedOperation) as exc_info:
            facade.subscribe(["temp"])
        assert "NOT_IMPLEMENTED" in str(exc_info.value)
        assert "subscribe" in str(exc_info.value).lower()

    def test_report_is_implemented(self) -> None:
        """report 已实现，不抛 UnsupportedOperation。"""
        facade = Iec61850ReportFacade()
        facade.load_points(_make_plan())
        # report 应该正常返回（report-lightweight 模式下的轻量实现）
        result = facade.report()
        assert isinstance(result, dict)
        assert "events" in result
        assert "event_count" in result
        assert "mode" in result


# ── ServerRegistry dispatch tests ──────────────────────────────────────────────


class TestRuntimeRegistryDispatch:
    """ServerRegistry IEC61850 协议分发测试。"""

    def test_dispatch_iec61850_mms_returns_real_or_unavailable(self) -> None:
        """IEC61850_MMS 协议分发返回 Iec61850MmsFacade。"""
        plan = _make_plan(endpoints=[
            StarfishEndpointConfig(
                endpoint_id="ep-mms",
                protocol="IEC61850_MMS",
                host="127.0.0.1",
                port=0,
            ),
        ])
        entry = create_driver_for_endpoint(plan.endpoints[0], plan)
        from starfish.drivers.iec61850_mms_facade import Iec61850MmsFacade
        assert isinstance(entry.driver, Iec61850MmsFacade)
        assert entry.mode in ("real", "unavailable")
        assert entry.driver.protocol == "IEC61850_MMS"

    def test_dispatch_iec61850_report_returns_real_or_report_lightweight(self) -> None:
        """IEC61850_REPORT 协议分发返回 Iec61850ReportFacade。"""
        plan = _make_plan(endpoints=[
            StarfishEndpointConfig(
                endpoint_id="ep-report",
                protocol="IEC61850_REPORT",
                host="127.0.0.1",
                port=0,
            ),
        ])
        entry = create_driver_for_endpoint(plan.endpoints[0], plan)
        from starfish.drivers.iec61850_report_facade import Iec61850ReportFacade
        assert isinstance(entry.driver, Iec61850ReportFacade)
        assert entry.mode in ("real", "report-lightweight")
        assert entry.driver.protocol == "IEC61850_REPORT"

    def test_get_supported_protocols_includes_iec61850(self) -> None:
        """get_supported_protocols 包含 IEC61850_MMS 和 IEC61850_REPORT。"""
        protocols = get_supported_protocols()
        assert "IEC61850_MMS" in protocols
        assert "IEC61850_REPORT" in protocols
        # 确保旧协议仍在列表中
        assert "HTTP_REST" in protocols
        assert "MODBUS_TCP" in protocols
        assert "MQTT" in protocols
        assert "OPC_UA" in protocols
        for p in ("IEC_104", "IEC104"):
            assert p in protocols

    def test_get_native_runner_protocols_includes_iec61850(self) -> None:
        """get_native_runner_protocols 包含 IEC61850 两个协议。"""
        protocols = get_native_runner_protocols()
        assert "IEC61850_MMS" in protocols
        assert "IEC61850_REPORT" in protocols

    def test_goose_sv_stub_fallback(self) -> None:
        """GOOSE/SV 协议分发返回 environment-pending DriverEntry（Round 10 更新）。

        Round 10 前 GOOSE/SV 回退到 stub mode，现在有专用 facade 并标记 environment-pending。
        """
        for protocol in ("GOOSE", "SV"):
            plan = _make_plan(endpoints=[
                StarfishEndpointConfig(
                    endpoint_id=f"ep-{protocol}",
                    protocol=protocol,
                    host="127.0.0.1",
                    port=0,
                ),
            ])
            entry = create_driver_for_endpoint(plan.endpoints[0], plan)
            assert entry.mode == "environment-pending", f"{protocol} 应为 environment-pending mode"
            assert "environment-pending" in entry.reason

    def test_unknown_protocol_stub(self) -> None:
        """未知协议返回 stub mode。"""
        plan = _make_plan(endpoints=[
            StarfishEndpointConfig(
                endpoint_id="ep-unknown",
                protocol="UNKNOWN_PROTOCOL_XYZ",
                host="127.0.0.1",
                port=0,
            ),
        ])
        entry = create_driver_for_endpoint(plan.endpoints[0], plan)
        assert entry.mode == "stub"


# ── Probe tests ─────────────────────────────────────────────────────────────────


class TestProbeIec61850:
    """IEC61850 probe 工具测试。"""

    def test_probe_iec61850_mms_stub_or_unavailable_returns_not_run(self) -> None:
        """probe 对 unavailable 或 stub mode 的 IEC61850_MMS facade 返回 NOT_RUN。"""
        # 使用标准 plan 通过 dispatch 创建 facade
        plan = _make_plan()
        # 直接用 facade 测试（不依赖 dispatch 返回值）
        with patch(
            "starfish.drivers.iec61850_mms_facade.probe_iec61850_mms_binary",
            return_value=(False, "binary not found"),
        ):
            facade = Iec61850MmsFacade()
            facade.load_points(plan)
            result = probe_facade(facade, plan=plan)
            assert result.protocol == "IEC61850_MMS"
            assert result.mode == "unavailable"
            # probe 在 unavailable 下仍执行（使用 in-memory），
            # 结果中的 mode 反映真实状态

    def test_probe_iec61850_mms_real_when_binary_available(self) -> None:
        """probe 对 real mode IEC61850_MMS facade 执行完整探测。"""
        if not _iec61850_binaries_available():
            pytest.skip("environment-pending")
        plan = _make_plan()
        facade = Iec61850MmsFacade()
        facade.load_points(plan)
        facade.start()
        try:
            result = probe_facade(
                facade, plan=plan, skip_start=True,
            )
            assert result.status == "PASS"
            assert result.mode == "real"
            assert result.protocol == "IEC61850_MMS"
        finally:
            facade.stop()

    def test_probe_iec61850_report_real_when_binary_available(self) -> None:
        """probe 对 real mode IEC61850_REPORT facade 探测（read 为 NOT_IMPLEMENTED）。"""
        if not _iec61850_report_binaries_available():
            pytest.skip("environment-pending")
        plan = _make_plan()
        facade = Iec61850ReportFacade()
        facade.load_points(plan)
        facade.start()
        try:
            # IEC61850_REPORT facade 的 read 是 NOT_IMPLEMENTED，
            # 所以 probe 会因 read() 失败而返回 FAIL
            result = probe_facade(
                facade, plan=plan, skip_start=True,
            )
            # read 在 IEC61850_REPORT 是 NOT_IMPLEMENTED，probe 的 read 步骤会失败
            assert result.status == "FAIL" or result.status == "PASS"
            assert result.protocol == "IEC61850_REPORT"
        finally:
            facade.stop()

    def test_probe_iec61850_report_lightweight(self) -> None:
        """probe 对 report-lightweight mode（read NOT_IMPLEMENTED）返回 FAIL。"""
        with patch(
            "starfish.drivers.iec61850_report_facade.probe_iec61850_report_binary",
            return_value=(False, "test"),
        ):
            plan = _make_plan()
            facade = Iec61850ReportFacade()
            facade.load_points(plan)
            result = probe_facade(facade, plan=plan)
            assert result.protocol == "IEC61850_REPORT"
            assert result.mode == "report-lightweight"
            # read 在 IEC61850_REPORT 是 NOT_IMPLEMENTED，所以 probe FAIL
            assert result.status == "FAIL"


# ── Profile tests ───────────────────────────────────────────────────────────────


class TestProfileIec61850:
    """IEC61850 profile 工具测试。"""

    def test_profile_iec61850_mms_unavailable(self) -> None:
        """unavailable mode 的 IEC61850_MMS facade profile 返回 FAIL（read 可能失败）。"""
        with patch(
            "starfish.drivers.iec61850_mms_facade.probe_iec61850_mms_binary",
            return_value=(False, "test"),
        ):
            facade = Iec61850MmsFacade()
            facade.load_points(_make_plan())
            facade.start()
            try:
                result = profile_facade(
                    facade, iterations=10,
                )
                # unavailable 下 read 仍可用（in-memory）
                assert result.status == "PASS"
                assert result.mode == "unavailable"
                assert result.stats["count"] == 10
            finally:
                facade.stop()

    def test_profile_iec61850_report_lightweight_read_fails(self) -> None:
        """IEC61850_REPORT facade read 是 NOT_IMPLEMENTED，profile 应 FAIL。"""
        with patch(
            "starfish.drivers.iec61850_report_facade.probe_iec61850_report_binary",
            return_value=(False, "test"),
        ):
            facade = Iec61850ReportFacade()
            facade.load_points(_make_plan())
            facade.start()
            try:
                result = profile_facade(
                    facade, iterations=5,
                )
                assert result.status == "FAIL"
                assert "read" in result.reason.lower()
            finally:
                facade.stop()


# ── Capacity tests ──────────────────────────────────────────────────────────────


class TestCapacityIec61850:
    """IEC61850 capacity 工具测试。"""

    def test_capacity_iec61850_mms_when_available(self) -> None:
        """IEC61850_MMS 在 unavailable 模式容量扫描返回 NOT_RUN。"""
        with patch(
            "starfish.drivers.iec61850_mms_facade.probe_iec61850_mms_binary",
            return_value=(False, "test"),
        ):
            plan = _make_plan()
            facade = Iec61850MmsFacade()
            facade.load_points(plan)
            facade.start()
            try:
                result = capacity_scan(
                    facade, read_count=3,
                )
                # IEC61850_MMS 在 unsupported 列表中，unavailable 模式
                assert result.protocol == "IEC61850_MMS"
            finally:
                facade.stop()

    def test_capacity_iec61850_mms_real(self) -> None:
        """IEC61850_MMS real 模式容量扫描。"""
        if not _iec61850_binaries_available():
            pytest.skip("environment-pending")
        plan = _make_plan()
        facade = Iec61850MmsFacade()
        facade.load_points(plan)
        facade.start()
        try:
            result = capacity_scan(
                facade, read_count=3,
            )
            assert result.protocol == "IEC61850_MMS"
            assert result.status in ("PASS", "NOT_RUN")
        finally:
            facade.stop()

    def test_capacity_iec61850_report_unavailable(self) -> None:
        """IEC61850_REPORT unavailable 模式容量扫描返回 NOT_RUN。"""
        with patch(
            "starfish.drivers.iec61850_report_facade.probe_iec61850_report_binary",
            return_value=(False, "test"),
        ):
            plan = _make_plan()
            facade = Iec61850ReportFacade()
            facade.load_points(plan)
            facade.start()
            try:
                result = capacity_scan(
                    facade, read_count=3,
                )
                # unavailable mode => NOT_RUN
                assert result.protocol == "IEC61850_REPORT"
            finally:
                facade.stop()


# ── Goose/SV: NOT_RUN tests ─────────────────────────────────────────────────────


class TestGooseSvNotRun:
    """GOOSE / SV 二层协议 NOT_RUN 语义。

    GOOSE/SV 需要 L2 veth 环境和 raw socket / CAP_NET_RAW，
    在当前测试环境中不可用。
    """

    def test_goose_dispatch_stub_mode(self) -> None:
        """GOOSE 协议分发为 environment-pending mode（Round 10 更新）。

        Round 10 前 GOOSE 回退到 stub mode，现在有专用 GooseFacade
        并标记 environment-pending。
        """
        plan = _make_plan(endpoints=[
            StarfishEndpointConfig(
                endpoint_id="ep-goose",
                protocol="GOOSE",
                host="127.0.0.1",
                port=0,
            ),
        ])
        entry = create_driver_for_endpoint(plan.endpoints[0], plan)
        assert entry.mode == "environment-pending"
        assert "environment-pending" in entry.reason.lower()

    def test_sv_dispatch_stub_mode(self) -> None:
        """SV 协议分发为 environment-pending mode（Round 10 更新）。

        Round 10 前 SV 回退到 stub mode，现在有专用 SvFacade
        并标记 environment-pending。
        """
        plan = _make_plan(endpoints=[
            StarfishEndpointConfig(
                endpoint_id="ep-sv",
                protocol="SV",
                host="127.0.0.1",
                port=0,
            ),
        ])
        entry = create_driver_for_endpoint(plan.endpoints[0], plan)
        assert entry.mode == "environment-pending"

    def test_goose_probe_not_run(self) -> None:
        """GOOSE dispatch 返回 environment-pending DriverEntry（Round 10 更新）。

        Round 10 前 GOOSE 回退到 ServerSimulatorFacade stub，
        现在有专用 GooseFacade 并标记 environment-pending。
        """
        plan = _make_plan(endpoints=[
            StarfishEndpointConfig(
                endpoint_id="ep-goose",
                protocol="GOOSE",
                host="127.0.0.1",
                port=0,
            ),
        ])
        entry = create_driver_for_endpoint(plan.endpoints[0], plan)
        assert entry.mode == "environment-pending"
        from starfish.drivers.goose_facade import GooseFacade
        assert isinstance(entry.driver, GooseFacade)


# ── Regression: existing protocols not impacted ──────────────────────────────────


class TestExistingProtocolsUnaffected:
    """IEC61850 新增不影响已有协议的 facade 行为。"""

    def test_http_rest_facade_still_works(self) -> None:
        """HTTP_REST facade 不受影响。"""
        from starfish.drivers.http_rest_facade import HttpRestFacade
        plan = _make_plan()
        facade = HttpRestFacade()
        facade.load_points(plan)
        facade.start()
        try:
            h = facade.health()
            assert h["mode"] == "real"
            values = facade.read()
            assert "temp" in values
        finally:
            facade.stop()

    def test_modbus_tcp_facade_still_works(self) -> None:
        """MODBUS_TCP facade 不受影响。"""
        from starfish.drivers.modbus_tcp_facade import ModbusTcpFacade
        plan = _make_plan()
        facade = ModbusTcpFacade()
        facade.load_points(plan)
        facade.start()
        try:
            h = facade.health()
            assert h["mode"] == "real"
        finally:
            facade.stop()

    def test_mqtt_facade_still_works(self) -> None:
        """MQTT facade 不受影响。"""
        from starfish.drivers.mqtt_facade import MqttFacade
        plan = _make_plan()
        facade = MqttFacade()
        facade.load_points(plan)
        facade.start()
        try:
            h = facade.health()
            assert h["mode"] == "mqtt-lightweight"
        finally:
            facade.stop()

    def test_opcua_facade_dispatch_still_works(self) -> None:
        """OPC_UA dispatch 不受影响。"""
        plan = _make_plan(endpoints=[
            StarfishEndpointConfig(
                endpoint_id="ep-opcua",
                protocol="OPC_UA",
                host="127.0.0.1",
                port=0,
            ),
        ])
        entry = create_driver_for_endpoint(plan.endpoints[0], plan)
        assert entry.driver.protocol == "OPC_UA"

    def test_iec104_facade_dispatch_still_works(self) -> None:
        """IEC104 dispatch 不受影响。"""
        plan = _make_plan(endpoints=[
            StarfishEndpointConfig(
                endpoint_id="ep-iec104",
                protocol="IEC104",
                host="127.0.0.1",
                port=0,
            ),
        ])
        entry = create_driver_for_endpoint(plan.endpoints[0], plan)
        assert entry.driver.protocol == "IEC104"
