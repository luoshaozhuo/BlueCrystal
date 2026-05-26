"""ServerSimulatorFacade E2E 验收：capacity / profile 管道。

验证通过 facade 启动 simulator 后，capacity scan 和 profile 管道可运行。
不依赖数据库，直接构造 SimulatedSource 绕过 SimulatorSourceProvider 的
仓库依赖。覆盖多协议参数切换路径，验证 NOT_IMPLEMENTED 正确传播。

边界规则：
- 不重构 facade
- 不新增 protocol
- 不扩大业务范围
- 只验证管道可运行（不验证容量指标精确性）
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import replace
from typing import Iterator

import pytest

from tools.source_lab.access.polling.capacity import scan_source_capacity
from tools.source_lab.access.polling.model import CapacityMode, CapacityScanConfig, CapacityStatus
from tools.source_lab.access.polling.profile import run_polling_profile
from tools.source_lab.access.providers.base import SourceRuntimeSpec
from tools.source_lab.access.subscribe.model import SubscribeScanConfig, SubscribeScanResult
from tools.source_lab.access.subscribe.scan import scan_source_subscriptions
from tools.source_lab.access.subscribe.profile import run_subscribe_profile
from tools.source_lab.fleet import SourceSimulatorFleet
from tools.source_lab.model import SimulatedPoint, SimulatedSource, SourceConnection, UpdateConfig
from tools.source_lab.sources import PortAllocator
from whale.shared.source.access.model import SourceEndpointSpec, SourcePointSpec  # type: ignore[import-untyped]


def _build_runner(protocol: str):
    """Construct capacity runner。

    对于 iec61850_mms，使用 NativeCmdCapacityRunner 直接通过 libiec61850
    进行 MMS 读取（Python 探针不支持 C 模拟器所需的完整 COTP+MMS 握手）。
    其他协议保留 Python lightweight polling runner（GenericPollingCapacityRunner 子类）。
    """
    if protocol == "modbus_tcp":
        from tools.source_lab.access.runners.modbus_tcp_polling import ModbusTcpPollingRunner
        return ModbusTcpPollingRunner()
    if protocol == "iec61850_mms":
        from tools.source_lab.access.runners.registry import build_capacity_runner
        return build_capacity_runner(protocol)
    if protocol == "iec104":
        from tools.source_lab.access.runners.registry import build_capacity_runner
        return build_capacity_runner(protocol)
    if protocol == "opcua":
        from tools.source_lab.access.runners.open62541_serial_polling import OpcUaOpen62541CapacityRunner
        return OpcUaOpen62541CapacityRunner()
    if protocol == "iec101":
        from tools.source_lab.access.runners.registry import build_capacity_runner
        return build_capacity_runner(protocol)
    if protocol == "modbus_rtu":
        from tools.source_lab.access.runners.registry import build_capacity_runner
        return build_capacity_runner(protocol)
    if protocol == "http_rest":
        from tools.source_lab.access.runners.http_rest_polling import HttpRestPollingRunner
        return HttpRestPollingRunner()
    raise ValueError(f"no Python runner for {protocol}")


def _build_subscription_runner(protocol: str):
    """Construct subscription runner for streaming protocols."""
    if protocol == "mqtt":
        from tools.source_lab.access.runners.mqtt_subscription import MqttSubscriptionRunner
        return MqttSubscriptionRunner()
    if protocol in ("opcua", "iec61850_goose", "iec61850_sv"):
        from tools.source_lab.access.runners.registry import build_subscription_runner
        return build_subscription_runner(protocol)
    raise ValueError(f"no subscription runner for {protocol}")


# ── 各协议 smoke 测试点位 ──────────────────────────────────────────────
# 每个协议 3 个点，覆盖 FLOAT64/BOOLEAN/INT32

_E2E_POINTS_BY_PROTOCOL: dict[str, tuple[SimulatedPoint, ...]] = {
    "modbus_tcp": (
        SimulatedPoint(ln_name="holding", do_name="0", unit=None, data_type="FLOAT64", initial_value=0.0),
        SimulatedPoint(ln_name="holding", do_name="1", unit=None, data_type="BOOLEAN", initial_value=False),
        SimulatedPoint(ln_name="holding", do_name="2", unit=None, data_type="INT32", initial_value=0),
    ),
    "iec61850_mms": (
        SimulatedPoint(ln_name="GGIO1", do_name="Ind1.stVal", unit=None, data_type="BOOLEAN", initial_value=False),
        SimulatedPoint(ln_name="GGIO1", do_name="Ind2.stVal", unit=None, data_type="BOOLEAN", initial_value=False),
        SimulatedPoint(ln_name="GGIO1", do_name="AnIn1.mag", unit=None, data_type="INT32", initial_value=0),
    ),
    "iec104": (
        SimulatedPoint(ln_name="WPPD1", do_name="TotW", unit="kW", data_type="FLOAT64", initial_value=0.0),
        SimulatedPoint(ln_name="WPPD1", do_name="DevSt", unit=None, data_type="BOOLEAN", initial_value=False),
        SimulatedPoint(ln_name="WPPD1", do_name="OpCnt", unit=None, data_type="INT32", initial_value=0),
    ),
    "iec101": (
        SimulatedPoint(ln_name="WPPD1", do_name="0", unit="kW", data_type="FLOAT64", initial_value=0.0),
        SimulatedPoint(ln_name="WPPD1", do_name="1", unit=None, data_type="BOOLEAN", initial_value=False),
        SimulatedPoint(ln_name="WPPD1", do_name="2", unit=None, data_type="INT32", initial_value=0),
    ),
    "modbus_rtu": (
        SimulatedPoint(ln_name="holding", do_name="0", unit=None, data_type="FLOAT64", initial_value=0.0),
        SimulatedPoint(ln_name="holding", do_name="1", unit=None, data_type="BOOLEAN", initial_value=False),
        SimulatedPoint(ln_name="holding", do_name="2", unit=None, data_type="INT32", initial_value=0),
    ),
    "opcua": (
        SimulatedPoint(ln_name="WPPD1", do_name="TotW", unit="kW", data_type="FLOAT64", initial_value=12.5),
        SimulatedPoint(ln_name="WPPD1", do_name="DevSt", unit=None, data_type="BOOLEAN", initial_value=True),
        SimulatedPoint(ln_name="WPPD1", do_name="OpCnt", unit=None, data_type="INT32", initial_value=7),
    ),
    "http_rest": (
        SimulatedPoint(ln_name="sensor", do_name="temperature", unit="C", data_type="FLOAT64", initial_value=23.5),
        SimulatedPoint(ln_name="sensor", do_name="enabled", unit=None, data_type="BOOLEAN", initial_value=True),
        SimulatedPoint(ln_name="sensor", do_name="counter", unit=None, data_type="INT32", initial_value=42),
    ),
    "mqtt": (
        SimulatedPoint(ln_name="sensor", do_name="temperature", unit="C", data_type="FLOAT64", initial_value=0.0),
        SimulatedPoint(ln_name="sensor", do_name="enabled", unit=None, data_type="BOOLEAN", initial_value=False),
        SimulatedPoint(ln_name="sensor", do_name="counter", unit=None, data_type="INT32", initial_value=0),
    ),
    "iec61850_goose": (
        SimulatedPoint(ln_name="LLN0", do_name="Events.stVal", unit=None, data_type="INT32", initial_value=0),
    ),
    "iec61850_sv": (
        SimulatedPoint(ln_name="LLN0", do_name="PhVMeas.mag", unit=None, data_type="FLOAT32", initial_value=230.0),
    ),
}

# ── 各协议 SourceConnection 构造参数 ────────────────────────────────────
_E2E_CONNECTION_KWARGS: dict[str, dict[str, object]] = {
    "modbus_tcp": {"namespace_uri": None, "ied_name": "", "ld_name": ""},
    "iec61850_mms": {"namespace_uri": None, "ied_name": "IED61850", "ld_name": "Simulator", "params": {"ied_name": "IED61850", "ld_name": "Simulator", "ln_class": "GGIO1", "do_name": "AnIn1", "da_name": "mag", "fc": "NONE"}},
    "iec104": {"namespace_uri": None, "ied_name": "", "ld_name": ""},
    "iec101": {"namespace_uri": None, "ied_name": "", "ld_name": ""},
    "modbus_rtu": {"namespace_uri": None, "ied_name": "", "ld_name": ""},
    "opcua": {"namespace_uri": "urn:whale:e2e:opcua", "ied_name": "OPCUAIED", "ld_name": "LD0"},
    "http_rest": {"namespace_uri": None, "ied_name": "", "ld_name": ""},
    "mqtt": {"namespace_uri": None, "ied_name": "", "ld_name": ""},
    "iec61850_goose": {"namespace_uri": None, "ied_name": "Simulator", "ld_name": "LLN0", "transport": "ethernet_l2", "params": {"l2_interface": "lo", "app_id": 1000, "publish_interval_ms": 1000}},
    "iec61850_sv": {"namespace_uri": None, "ied_name": "Simulator", "ld_name": "LLN0", "transport": "ethernet_l2", "params": {"l2_interface": "lo", "app_id": 4000, "sample_rate_hz": 1}},
}


def _build_e2e_source(protocol: str, port: int) -> SimulatedSource:
    """构造单协议 SimulatedSource，分配指定端口。"""
    kwargs = dict(
        name=f"{protocol}_e2e",
        host="127.0.0.1",
        port=port,
        transport="tcp",
        protocol=protocol,
    )
    kwargs.update(_E2E_CONNECTION_KWARGS.get(protocol, {}))
    points = _E2E_POINTS_BY_PROTOCOL.get(protocol)
    if points is None:
        raise ValueError(f"unsupported protocol for E2E smoke: {protocol}")
    return SimulatedSource(connection=SourceConnection(**kwargs), points=points)  # type: ignore[arg-type]


# ── _FacadeE2EProvider ──────────────────────────────────────────────────
# 简化的 provider：不依赖数据库，直接使用 SimulatedSource 和 facade fleet。


class _FacadeE2EProvider:
    """不依赖数据库的测试用 provider。

    直接持有 SimulatedSource 模板，在 ``build_sources`` 中分配端口并克隆，
    在 ``started`` 中通过 ``SourceSimulatorFleet(use_facade=True)`` 管理生命周期。
    """

    def __init__(
        self,
        base_source: SimulatedSource,
        *,
        port_allocator: PortAllocator | None = None,
    ) -> None:
        self._base_source = base_source
        self._port_allocator = port_allocator or PortAllocator.from_range(start=41101, end=42000)
        self._active_config: CapacityScanConfig | SubscribeScanConfig | None = None

    def build_sources(
        self,
        config: CapacityScanConfig | SubscribeScanConfig,  # type: ignore[override]
        *,
        server_count: int,
    ) -> tuple[SourceRuntimeSpec, ...]:
        self._active_config = config
        ports = self._port_allocator.allocate_many(server_count)
        from tools.source_lab.sources import build_multi_sources

        sources = build_multi_sources(self._base_source, server_count=server_count, ports=ports)
        return tuple(self._as_runtime_spec(source) for source in sources)

    def _as_runtime_spec(self, source: SimulatedSource) -> SourceRuntimeSpec:
        protocol: str = source.connection.protocol
        endpoint = SourceEndpointSpec(
            name=source.connection.name,
            host=source.connection.host,
            port=source.connection.port,
            protocol=source.connection.protocol,
            transport=source.connection.transport,
            namespace_uri=source.connection.namespace_uri,
            ied_name=source.connection.ied_name,
            ld_name=source.connection.ld_name,
            params=dict(source.connection.params),
        )
        if protocol == "opcua":
            from tools.source_lab.protocols.opcua.address_space import logical_path

            points = tuple(
                SourcePointSpec(
                    address=logical_path(source.connection, point),
                    name=point.key,
                    data_type=point.data_type,
                    ln_name=point.ln_name,
                    do_name=point.do_name,
                    unit=point.unit,
                )
                for point in source.points
            )
        else:
            points = tuple(
                SourcePointSpec(
                    address=point.key,
                    name=point.key,
                    data_type=point.data_type,
                    ln_name=point.ln_name,
                    do_name=point.do_name,
                    unit=point.unit,
                )
                for point in source.points
            )
        return SourceRuntimeSpec(endpoint=endpoint, points=points, runtime_handle=source)

    @contextmanager
    def started(self, sources: tuple[SourceRuntimeSpec, ...]) -> Iterator[None]:
        if self._active_config is None:
            raise RuntimeError("_FacadeE2EProvider: call build_sources before started")
        config = self._active_config

        simulated = tuple(
            item.runtime_handle
            for item in sources
            if isinstance(item.runtime_handle, SimulatedSource)
        )
        if len(simulated) != len(sources):
            raise ValueError("_FacadeE2EProvider: expected SimulatedSource handles")

        update_interval_s = 1.0 / max(1.0, config.source_update_hz)
        update_interval_ms = max(1, round(update_interval_s * 1000.0))
        update_params: dict[str, str | int | float | bool] = {
            "internal_update_enabled": config.source_update_enabled,
            "internal_update_interval_ms": update_interval_ms,
        }
        simulated = tuple(
            replace(
                source,
                connection=replace(
                    source.connection,
                    params={**source.connection.params, **update_params},
                ),
            )
            for source in simulated
        )

        fleet = SourceSimulatorFleet.create(
            sources=simulated,
            update_config=UpdateConfig(
                enabled=config.source_update_enabled,
                interval_seconds=update_interval_s,
                update_count=len(sources[0].points) if sources else None,
            ),
            startup_timeout_seconds=config.fleet_startup_timeout_s,
        )
        with fleet:
            yield


# ── Capacity E2E smoke ──────────────────────────────────────────────────
# 验证：facade 启动 simulator → capacity scan 管道可运行 → 各协议正常


def _smoke_capacity_config(protocol: str) -> CapacityScanConfig:
    return CapacityScanConfig(
        mode=CapacityMode.SIMULATOR,
        protocol=protocol,
        endpoints=(),
        points=(),
        server_count_start=1,
        server_count_step=1,
        server_count_max=1,
        hz_start=1.0,
        hz_step=1.0,
        hz_max=1.0,
        process_count=1,
        level_duration_s=8.0,
        warmup_s=3.0,
        read_timeout_s=5.0,
        source_update_enabled=True,
        source_update_hz=1.0,
        period_max_tolerance_ratio=5.0,
        period_mean_error_ratio=5.0,
        fail_confirm_runs=1,
        accept_flaky_as_pass=True,
        stop_hz_ramp_on_first_fail=False,
        min_expected_point_count=1,
        max_expected_point_count=100,
        fleet_startup_timeout_s=60.0,
        fleet_stop_grace_s=0.2,
        progress_enabled=False,
    )


_CI_POLLING_PROTOCOLS = ("modbus_tcp", "iec61850_mms", "iec104", "opcua", "iec101", "modbus_rtu", "http_rest")
_CI_STREAMING_PROTOCOLS = ("mqtt", "opcua", "iec61850_goose", "iec61850_sv")


def _skip_if_l2_unavailable(protocol: str) -> None:
    if protocol not in ("iec61850_goose", "iec61850_sv"):
        return
    import os
    from pathlib import Path

    executable = (
        "iec61850_goose_subscriber_runner"
        if protocol == "iec61850_goose"
        else "iec61850_sv_subscriber_runner"
    )
    exe = Path(__file__).resolve().parents[2] / "native" / "build" / executable
    if not exe.exists():
        pytest.skip(
            f"dependency_missing: {executable} not compiled. CI: "
            "cmake -S tools/source_lab/native -B tools/source_lab/native/build && "
            f"cmake --build tools/source_lab/native/build --target {executable}"
        )
    if os.geteuid() != 0:
        pytest.skip(
            f"raw_socket_permission_missing: {protocol} requires CAP_NET_RAW/root and "
            "a usable L2 interface. CI: pytest -k 'goose or sv' tools/source_lab/tests/access -q"
        )


@pytest.mark.slow
@pytest.mark.parametrize("protocol", _CI_POLLING_PROTOCOLS)
def test_capacity_e2e_via_facade_fleet(protocol: str) -> None:
    """E2E 验证：facade 启动 simulator 后 capacity scan 管道可运行。

    验证：
    1. facade fleet 正常启动
    2. build_sources → started → scan_source_capacity 完整链路
    3. 管道无协议 if/else 分支
    4. 至少一个协议达到 PASS 或 FLAKY；其余协议至少管道正常运行
    """
    allocator = PortAllocator.from_range(start=41201, end=42000)
    port = allocator.allocate_many(1, host="127.0.0.1")[0]
    source = _build_e2e_source(protocol, port)
    provider = _FacadeE2EProvider(source, port_allocator=allocator)
    config = _smoke_capacity_config(protocol)
    runner = _build_runner(protocol)

    result = scan_source_capacity(config, provider=provider, runner=runner)

    assert len(result.levels) > 0, f"{protocol}: no levels returned from capacity scan"
    top = result.levels[0]

    assert top.final_status in (CapacityStatus.PASS, CapacityStatus.FLAKY), (
        f"{protocol}: capacity E2E expected PASS or FLAKY, "
        f"got {top.final_status}: {top.final_reason}"
    )


# ── Profile E2E smoke ───────────────────────────────────────────────────
# 验证：profile 管道与 capacity 使用相同的 provider/runner 接口


@pytest.mark.slow
@pytest.mark.parametrize("protocol", _CI_POLLING_PROTOCOLS)
def test_profile_e2e_via_facade_fleet(protocol: str) -> None:
    """E2E 验证：facade 启动 simulator 后 polling profile 管道可运行。

    验证：
    1. facade fleet 正常启动
    2. run_polling_profile 完整链路
    3. 结果正常返回
    """
    allocator = PortAllocator.from_range(start=41301, end=42000)
    port = allocator.allocate_many(1, host="127.0.0.1")[0]
    source = _build_e2e_source(protocol, port)
    provider = _FacadeE2EProvider(source, port_allocator=allocator)
    config = _smoke_capacity_config(protocol)
    runner = _build_runner(protocol)

    profile_result = run_polling_profile(config, provider=provider, runner=runner)

    assert profile_result is not None
    result = profile_result.result
    assert len(result.levels) > 0, f"{protocol}: no levels from profile"
    top = result.levels[0]

    assert top.final_status in (CapacityStatus.PASS, CapacityStatus.FLAKY), (
        f"{protocol}: profile E2E expected PASS or FLAKY, "
        f"got {top.final_status}: {top.final_reason}"
    )


# ── Streaming capacity E2E smoke ──────────────────────────────────────────
# 验证：facade 启动 simulator → subscribe capacity scan 管道可运行


def _smoke_subscribe_config(protocol: str) -> SubscribeScanConfig:
    return SubscribeScanConfig(
        mode=CapacityMode.SIMULATOR,
        protocol=protocol,
        server_count_start=1,
        server_count_step=1,
        server_count_max=1,
        process_count=1,
        publishing_interval_ms=1000.0,
        sampling_interval_ms=1000.0,
        nominal_sample_hz=1.0,
        queue_size=1,
        duration_s=8.0,
        read_timeout_s=5.0,
        source_update_enabled=True,
        source_update_hz=1.0,
        fleet_startup_timeout_s=60.0,
        fleet_stop_grace_s=0.2,
        progress_enabled=False,
    )


@pytest.mark.slow
@pytest.mark.parametrize("protocol", _CI_STREAMING_PROTOCOLS)
def test_streaming_capacity_e2e_via_facade_fleet(protocol: str) -> None:
    """E2E 验证：facade 启动 simulator 后 subscribe capacity scan 管道可运行。"""
    _skip_if_l2_unavailable(protocol)
    allocator = PortAllocator.from_range(start=41401, end=42000)
    port = allocator.allocate_many(1, host="127.0.0.1")[0]
    source = _build_e2e_source(protocol, port)
    provider = _FacadeE2EProvider(source, port_allocator=allocator)
    config = _smoke_subscribe_config(protocol)
    runner = _build_subscription_runner(protocol)

    result = scan_source_subscriptions(config, provider=provider, runner=runner)

    assert isinstance(result, SubscribeScanResult), f"{protocol}: expected SubscribeScanResult, got {type(result)}"
    assert len(result.levels) > 0, f"{protocol}: no levels from subscribe capacity"
    top = result.levels[0]
    assert top.final_status in (CapacityStatus.PASS, CapacityStatus.FLAKY), (
        f"{protocol}: subscribe capacity E2E expected PASS or FLAKY, "
        f"got {top.final_status}: {top.final_reason}"
    )


@pytest.mark.slow
@pytest.mark.parametrize("protocol", _CI_STREAMING_PROTOCOLS)
def test_streaming_profile_e2e_via_facade_fleet(protocol: str) -> None:
    """E2E 验证：facade 启动 simulator 后 subscribe profile 管道可运行。"""
    _skip_if_l2_unavailable(protocol)
    allocator = PortAllocator.from_range(start=41501, end=42000)
    port = allocator.allocate_many(1, host="127.0.0.1")[0]
    source = _build_e2e_source(protocol, port)
    provider = _FacadeE2EProvider(source, port_allocator=allocator)
    config = _smoke_subscribe_config(protocol)
    runner = _build_subscription_runner(protocol)

    result = run_subscribe_profile(config, provider=provider, runner=runner)

    assert result is not None, f"{protocol}: profile returned None"
    assert len(result.result.levels) > 0, f"{protocol}: no levels from subscribe profile"
    top = result.result.levels[0]
    assert top.final_status in (CapacityStatus.PASS, CapacityStatus.FLAKY), (
        f"{protocol}: subscribe profile E2E expected PASS or FLAKY, "
        f"got {top.final_status}: {top.final_reason}"
    )


# ── NOT_IMPLEMENTED 验收 ────────────────────────────────────────────────
# 验证：不可用协议/操作返回 NOT_IMPLEMENTED，而不是崩溃


@pytest.mark.parametrize(
    "protocol,method",
    [
        ("iec61850_goose", "read"),
        ("iec61850_goose", "write"),
        ("iec61850_goose", "report"),
        ("iec61850_sv", "read"),
        ("iec61850_sv", "write"),
        ("iec61850_sv", "report"),
    ],
)
@pytest.mark.asyncio
async def test_not_implemented_returns_not_implemented(protocol: str, method: str) -> None:
    """GOOSE/SV 不支持的操作应返回 NOT_IMPLEMENTED。"""
    from tools.source_lab.protocols.registry import create_server_simulator

    facade = create_server_simulator(protocol, source=None)
    func = getattr(facade, method)
    args: list[object] = []
    if method in ("read", "subscribe", "report"):
        args.append([])
    elif method == "write":
        args.append({})
    result = await func(*args)
    assert result.status.name == "NOT_IMPLEMENTED", (
        f"{protocol}.{method} expected NOT_IMPLEMENTED, got {result.status.name}"
    )


def test_not_implemented_factory_creates_placeholder() -> None:
    """GOOSE/SV 能力边界只开放 subscribe/update_values。"""
    from tools.source_lab.protocols.registry import create_server_simulator

    for proto in ("iec61850_goose", "iec61850_sv"):
        facade = create_server_simulator(proto, source=None)
        caps = facade.capabilities
        assert caps.read is False
        assert caps.write is False
        assert caps.subscribe is True
        assert caps.report is False
        assert caps.update_values is True


# ── 协议切换路径验证 ────────────────────────────────────────────────────
# 验证 capacity/profile 主路径无 protocol if/else


def test_capacity_profile_has_no_protocol_if_else() -> None:
    """验证 capacity.py 和 profile.py 主路径无协议分支。

    检查：
    - capacity.py 的 scan_capacity 只按 access_mode 分发
    - profile.py 的 run_field_profile 只按 access_mode 分发
    - 无 protocol 字符串比较
    """
    import inspect
    import ast
    from pathlib import Path

    src_root = Path(__file__).resolve().parents[2] / "access"

    for module_name in ("capacity.py", "profile.py"):
        source = (src_root / module_name).read_text(encoding="utf-8")
        tree = ast.parse(source)

        # 检查 protocol 关键字（不应有协议名称字面量）
        for node in ast.walk(tree):
            if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
                continue
            val = node.value.lower()
            if val in ("opcua", "modbus_tcp", "iec104", "iec61850"):
                raise AssertionError(
                    f"{module_name} contains protocol literal {val!r} "
                    f"at line {node.lineno}"
                )
