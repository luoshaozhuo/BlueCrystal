"""starfish ServerSimulatorFacade 测试。

验证：
1. start/stop 生命周期。
2. health 可观测状态。
3. load_points 初始化值存储。
4. read 读取 initial_values 和 update_values 后的值。
5. write/subscribe/report 返回 NOT_IMPLEMENTED。
6. update_values 内存更新。
7. capabilities 返回已加载的 plan 能力。

测试阶段：开发期验证 (P1)。
使用的替身：使用 StarfishServerConfig fixture 构造本地数据。
外部依赖：无（纯内存测试）。
不能证明：真实协议 server 启动、网络 I/O。
NOT_RUN 条件：无。
"""

from __future__ import annotations

import pytest

from starfish.domain.server_config import (
    StarfishServerConfig,
    StarfishEndpointConfig,
    StarfishPointConfig,
    UnsupportedOperation,
)
from starfish.drivers.server_simulator_facade import ServerSimulatorFacade


# ── Fixtures ────────────────────────────────────────────────────────────────────


def _make_test_plan(
    scenario_id: str = "facade_test",
    capabilities: list[str] | None = None,
    initial_values: dict | None = None,
) -> StarfishServerConfig:
    """构造一个最小测试用 StarfishServerConfig。

    Args:
        scenario_id: 场景标识。
        capabilities: 能力声明列表，默认 ["READ"]。
        initial_values: 初始值 dict，默认包含两个点位。

    Returns:
        测试用 StarfishServerConfig 实例。
    """
    if capabilities is None:
        capabilities = ["READ"]
    if initial_values is None:
        initial_values = {"pt_001": 100.5, "pt_002": 42}

    return StarfishServerConfig(
        schema_version="1.0.0",
        scenario_id=scenario_id,
        synthetic=True,
        server_name=f"{scenario_id}_server",
        endpoints=[
            StarfishEndpointConfig(
                endpoint_id=f"{scenario_id}_ep",
                protocol="OPC_UA",
                host="127.0.0.1",
                port=4840,
            )
        ],
        points=[
            StarfishPointConfig(
                point_id="pt_001",
                point_name="Point One",
                node_key="ns=2;s=pt_001",
                value_type="Float",
                access_mode="RO",
            ),
            StarfishPointConfig(
                point_id="pt_002",
                point_name="Point Two",
                node_key="ns=2;s=pt_002",
                value_type="Int32",
                access_mode="RO",
            ),
        ],
        capabilities=capabilities,
        initial_values=initial_values,
    )


# ── start/stop 生命周期 ─────────────────────────────────────────────────────────


class TestFacadeLifecycle:
    """start/stop 生命周期测试。"""

    def test_initial_state_is_stopped(self) -> None:
        """新建 facade 应为 stopped 状态。"""
        facade = ServerSimulatorFacade()
        health = facade.health()
        assert health["status"] == "stopped"
        assert health["plan_loaded"] is False

    def test_start_sets_status(self) -> None:
        """start() 应将状态置为 started。"""
        facade = ServerSimulatorFacade()
        facade.start()
        assert facade.health()["status"] == "started"

    def test_stop_sets_status(self) -> None:
        """stop() 应将状态置为 stopped。"""
        facade = ServerSimulatorFacade()
        facade.start()
        facade.stop()
        assert facade.health()["status"] == "stopped"

    def test_start_is_idempotent(self) -> None:
        """重复 start() 应为幂等。"""
        facade = ServerSimulatorFacade()
        facade.start()
        facade.start()
        assert facade.health()["status"] == "started"

    def test_stop_is_idempotent(self) -> None:
        """重复 stop() 应为幂等。"""
        facade = ServerSimulatorFacade()
        facade.start()
        facade.stop()
        facade.stop()
        assert facade.health()["status"] == "stopped"

    def test_started_at_is_recorded(self) -> None:
        """start() 后 started_at 应非空。"""
        facade = ServerSimulatorFacade()
        facade.start()
        assert facade.health()["started_at"] is not None


# ── health ──────────────────────────────────────────────────────────────────────


class TestFacadeHealth:
    """health 可观测状态测试。"""

    def test_health_before_load(self) -> None:
        """未 load_points 时 health 应反映空状态。"""
        facade = ServerSimulatorFacade()
        health = facade.health()
        assert health["plan_loaded"] is False
        assert health["point_count"] == 0
        assert health["endpoint_count"] == 0
        assert health["capabilities"] == []

    def test_health_after_load(self) -> None:
        """load_points 后 health 应反映 plan 信息。"""
        plan = _make_test_plan("health_test")
        facade = ServerSimulatorFacade()
        facade.load_points(plan)

        health = facade.health()
        assert health["plan_loaded"] is True
        assert health["point_count"] == 2
        assert health["endpoint_count"] == 1
        assert health["capabilities"] == ["READ"]
        assert health["synthetic"] is True

    def test_health_includes_capabilities(self) -> None:
        """health 应包含正确的 capabilities。"""
        plan = _make_test_plan("cap_test", capabilities=["READ", "WRITE"])
        facade = ServerSimulatorFacade()
        facade.load_points(plan)

        assert facade.health()["capabilities"] == ["READ", "WRITE"]

    def test_health_synthetic_flag(self) -> None:
        """health 应反映 synthetic 标识。"""
        plan = _make_test_plan("syn_test")
        plan.synthetic = True
        facade = ServerSimulatorFacade()
        facade.load_points(plan)

        assert facade.health()["synthetic"] is True


# ── load_points / read / update_values ──────────────────────────────────────────


class TestFacadeReadUpdate:
    """点位读写操作测试。"""

    def test_load_points_populates_values(self) -> None:
        """load_points 应从 plan.initial_values 填充内存存储。"""
        plan = _make_test_plan("load_test")
        facade = ServerSimulatorFacade()
        facade.load_points(plan)

        values = facade.read()
        assert values == {"pt_001": 100.5, "pt_002": 42}

    def test_read_specific_points(self) -> None:
        """read 指定 point_ids 时应只返回对应值。"""
        plan = _make_test_plan("read_test")
        facade = ServerSimulatorFacade()
        facade.load_points(plan)

        values = facade.read(["pt_001"])
        assert values == {"pt_001": 100.5}

    def test_read_nonexistent_point_returns_none(self) -> None:
        """read 不存在的 point_id 应返回 None。"""
        plan = _make_test_plan("nonexist_test")
        facade = ServerSimulatorFacade()
        facade.load_points(plan)

        values = facade.read(["nonexistent"])
        assert values == {"nonexistent": None}

    def test_read_all_returns_all(self) -> None:
        """不指定 point_ids 时 read 应返回全部点位。"""
        plan = _make_test_plan("all_test")
        facade = ServerSimulatorFacade()
        facade.load_points(plan)

        assert len(facade.read()) == 2

    def test_read_empty_list(self) -> None:
        """空 point_ids 列表应返回空 dict。"""
        plan = _make_test_plan("empty_list")
        facade = ServerSimulatorFacade()
        facade.load_points(plan)

        assert facade.read([]) == {}

    def test_update_values_modifies_storage(self) -> None:
        """update_values 应更新内存中的点位值。"""
        plan = _make_test_plan("update_test")
        facade = ServerSimulatorFacade()
        facade.load_points(plan)

        facade.update_values({"pt_001": 999.9, "pt_new": 0})
        values = facade.read()
        assert values["pt_001"] == 999.9
        assert values["pt_new"] == 0
        # 未更新的应保持不变
        assert values["pt_002"] == 42

    def test_reload_plan_overwrites_values(self) -> None:
        """重新 load_points 应覆盖已有值。"""
        plan1 = _make_test_plan("reload_test", initial_values={"a": 1})
        plan2 = _make_test_plan("reload_test", initial_values={"b": 2})

        facade = ServerSimulatorFacade()
        facade.load_points(plan1)
        assert facade.read() == {"a": 1}

        facade.load_points(plan2)
        assert facade.read() == {"b": 2}


# ── NOT_IMPLEMENTED 语义 ────────────────────────────────────────────────────────


class TestFacadeNotImplemented:
    """NOT_IMPLEMENTED 语义测试。"""

    def test_write_raises_unsupported_operation(self) -> None:
        """write 应抛出 UnsupportedOperation。"""
        facade = ServerSimulatorFacade()
        with pytest.raises(UnsupportedOperation, match="write"):
            facade.write("pt_001", 100)

    def test_subscribe_raises_unsupported_operation(self) -> None:
        """subscribe 应抛出 UnsupportedOperation。"""
        facade = ServerSimulatorFacade()
        with pytest.raises(UnsupportedOperation, match="subscribe"):
            facade.subscribe(["pt_001"])

    def test_report_raises_unsupported_operation(self) -> None:
        """report 应抛出 UnsupportedOperation。"""
        facade = ServerSimulatorFacade()
        with pytest.raises(UnsupportedOperation, match="report"):
            facade.report()

    def test_unsupported_operation_includes_operation_name(self) -> None:
        """UnsupportedOperation 消息应包含操作名。"""
        exc = UnsupportedOperation("write", "test reason")
        assert "NOT_IMPLEMENTED" in str(exc)
        assert "write" in str(exc)
        assert "test reason" in str(exc)

    def test_unsupported_operation_attributes(self) -> None:
        """UnsupportedOperation 应有 operation 和 reason 属性。"""
        exc = UnsupportedOperation("subscribe")
        assert exc.operation == "subscribe"
        assert exc.reason == ""


# ── capabilities ────────────────────────────────────────────────────────────────


class TestFacadeCapabilities:
    """capabilities 方法测试。"""

    def test_capabilities_before_load(self) -> None:
        """未 load_points 时 capabilities 应返回空列表。"""
        facade = ServerSimulatorFacade()
        assert facade.capabilities() == []

    def test_capabilities_after_load(self) -> None:
        """load_points 后 capabilities 应返回 plan 中的列表。"""
        plan = _make_test_plan("cap_test", capabilities=["READ", "SUBSCRIBE"])
        facade = ServerSimulatorFacade()
        facade.load_points(plan)

        assert facade.capabilities() == ["READ", "SUBSCRIBE"]

    def test_capabilities_returns_copy_not_reference(self) -> None:
        """capabilities 返回的是副本而非内部引用。"""
        plan = _make_test_plan("ref_test", capabilities=["READ"])
        facade = ServerSimulatorFacade()
        facade.load_points(plan)

        caps = facade.capabilities()
        caps.append("WRITE")
        # 内部不应被修改
        assert facade.capabilities() == ["READ"]


# ── UnsupportedOperation 模型 ───────────────────────────────────────────────────


class TestUnsupportedOperationModel:
    """UnsupportedOperation 异常模型测试。"""

    def test_is_exception_subclass(self) -> None:
        """应为 Exception 子类。"""
        assert issubclass(UnsupportedOperation, Exception)

    def test_can_be_caught_as_exception(self) -> None:
        """应可被标准 except Exception 捕获。"""
        try:
            raise UnsupportedOperation("test_op")
        except Exception as e:
            assert isinstance(e, UnsupportedOperation)

    def test_with_reason(self) -> None:
        """带 reason 的异常应包含原因。"""
        exc = UnsupportedOperation("write", "该协议不支持写入")
        assert exc.reason == "该协议不支持写入"
        assert "该协议不支持写入" in str(exc)


# ── 完整 smoke 流程 ─────────────────────────────────────────────────────────────


class TestFacadeSmokeFlow:
    """Facade 最小 smoke 流程测试。

    验证 document 中描述的完整 smoke 流程：
    load -> health -> start -> read -> write(not_impl) -> stop
    """

    def test_full_smoke_flow(self) -> None:
        """完整 smoke 流程应无异常。"""
        plan = _make_test_plan("smoke_flow", initial_values={"pt_001": 3.14})

        facade = ServerSimulatorFacade()

        # 1. load_points
        facade.load_points(plan)
        assert facade.health()["plan_loaded"] is True

        # 2. health
        health = facade.health()
        assert health["status"] == "stopped"

        # 3. start
        facade.start()
        assert facade.health()["status"] == "started"

        # 4. read
        values = facade.read()
        assert values["pt_001"] == 3.14

        # 5. write NOT_IMPLEMENTED
        with pytest.raises(UnsupportedOperation):
            facade.write("pt_001", 999)

        # 6. subscribe NOT_IMPLEMENTED
        with pytest.raises(UnsupportedOperation):
            facade.subscribe(["pt_001"])

        # 7. report NOT_IMPLEMENTED
        with pytest.raises(UnsupportedOperation):
            facade.report()

        # 8. update_values + 二次 read
        facade.update_values({"pt_001": 2.718})
        assert facade.read(["pt_001"]) == {"pt_001": 2.718}

        # 9. stop
        facade.stop()
        assert facade.health()["status"] == "stopped"
