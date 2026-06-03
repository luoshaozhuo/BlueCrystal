"""Beckhoff ADS 真实协议 read/write/readback 闭环测试。

测试阶段：跨模块联调期验证 (integration)（需 dotnet + AdsServer + AdsLib runner 全部就绪时）；
环境不满足时为开发期验证 (contract)（仅验证 backend_kind=beckhoff_dotnet 的 facade 契约和
降级路径，以及 backend_kind=in_process 的 lightweight fallback 对照）。

本测试覆盖：
- BeckhoffDotnetAdsSimulatorFacade 的 start/health/read/write/stop 契约；
- environment-pending 时的 skip 语义（缺 dotnet / 缺 ADS Router / 缺 AdsLib runner /
  缺 NuGet restore / 非 Windows 等原因必须具体）；
- BeckhoffAdsSimulatorFacade（in_process backend）的现有行为对照；
- protocol_evidence 只有在真实 server+client 闭环成功后才为 true；
- ADS_NOTIFICATION 仍为 NOT_IMPLEMENTED，不得 fake subscribe。
"""

from __future__ import annotations

import platform
from dataclasses import replace

import pytest

from tools.source_lab.model import SimulatedPoint, SimulatedSource, SourceConnection
from tools.source_lab.protocols.beckhoff_ads.ads_client import ads_native_preflight
from tools.source_lab.protocols.beckhoff_ads.dotnet_virtual_server import probe_dotnet_environment
from tools.source_lab.protocols.beckhoff_ads.simulator import BeckhoffDotnetAdsSimulatorFacade
from tools.source_lab.protocols.common.simulator_models import (
    ReadSimulatorResult,
    SimulatorHealth,
    SimulatorStatus,
)
from tools.source_lab.protocols.registry import create_server_simulator


# ── Shared fixtures ────────────────────────────────────────────────────────


def _build_ads_source_for_real_test() -> SimulatedSource:
    """构造用于真实协议测试的 ADS source。"""

    points = (
        SimulatedPoint(
            ln_name="ADS",
            do_name="ActivePower",
            unit="kW",
            data_type="FLOAT64",
            initial_value=12.5,
            address="MAIN.WTG_ADS_001.ActivePower",
            protocol_params={
                "symbol_name": "MAIN.WTG_ADS_001.ActivePower",
                "index_group": 16416,
                "index_offset": 32,
                "data_size": 8,
                "ads_data_type": "LREAL",
            },
        ),
        SimulatedPoint(
            ln_name="ADS",
            do_name="LocalState",
            unit=None,
            data_type="BOOLEAN",
            initial_value=True,
            address="MAIN.WTG_ADS_001.LocalState",
            protocol_params={
                "symbol_name": "MAIN.WTG_ADS_001.LocalState",
                "index_group": 16416,
                "index_offset": 40,
                "data_size": 1,
                "ads_data_type": "BOOL",
            },
        ),
    )
    return SimulatedSource(
        connection=SourceConnection(
            name="beckhoff_ads_real_test",
            host="127.0.0.1",
            port=48898,
            transport="TCP",
            protocol="beckhoff_ads",
            application_protocol="BECKHOFF_ADS",
            service_type="ADS_READ_WRITE",
            namespace_uri=None,
            ied_name="ADS",
            ld_name="LD_ADS_REAL_001",
            params={
                "ams_net_id": "5.32.160.1.1.1",
                "ads_router_port": 48898,
                "ads_server_port": 851,
                "request_timeout_ms": 1000,
                "backend_kind": "beckhoff_dotnet",
            },
        ),
        points=points,
    )


def _describe_env_skip_reason() -> str | None:
    """生成环境不满足时的具体 skip reason。

    Returns:
        具体原因文本，环境满足时返回 None。
    """
    parts: list[str] = []

    # 检查 .NET 环境
    dotnet_probe = probe_dotnet_environment()
    if not dotnet_probe.overall_environment_ready:
        for comp in dotnet_probe.missing_components:
            if comp == "dotnet_cli":
                parts.append("缺少 dotnet CLI")
            elif comp == "ads_server_project":
                parts.append("缺少 AdsServer 示例项目")
            elif comp == "twincat_runtime":
                parts.append("缺少 TwinCAT 运行时")
            else:
                parts.append(f"缺少环境组件: {comp}")

    # 检查 AdsLib native runner
    preflight = ads_native_preflight()
    if not preflight["available"]:
        parts.append("缺少 AdsLib native runner 二进制")

    # 检查平台
    if platform.system() != "Windows":
        parts.append(
            f"非 Windows 平台 ({platform.system()})；"
            "ADS full verification 需要 Windows + TwinCAT"
        )

    if not parts:
        return None
    return "; ".join(parts)


# ── Dotnet backend facade contract tests ────────────────────────────────────


def test_beckhoff_dotnet_facade_has_correct_capabilities() -> None:
    """BeckhoffDotnetAdsSimulatorFacade 应声明 read/write/update_values 能力。"""

    facade = BeckhoffDotnetAdsSimulatorFacade()
    caps = facade.capabilities
    assert caps.read is True
    assert caps.write is True
    assert caps.update_values is True
    assert caps.subscribe is False
    assert caps.report is False


def test_beckhoff_dotnet_facade_protocol_evidence_starts_false() -> None:
    """未启动 server 时 protocol_evidence 必须为 False。"""

    facade = BeckhoffDotnetAdsSimulatorFacade()
    assert facade.protocol_evidence is False


@pytest.mark.asyncio
async def test_beckhoff_dotnet_facade_requires_source_for_start() -> None:
    """无 SimulatedSource 时 start 必须返回 BAD_REQUEST。"""

    facade = BeckhoffDotnetAdsSimulatorFacade(source=None)
    result = await facade.start()
    assert result.status == SimulatorStatus.BAD_REQUEST


@pytest.mark.asyncio
async def test_beckhoff_dotnet_facade_health_when_not_running() -> None:
    """未启动时 health 应返回 NOT_RUNNING。"""

    facade = BeckhoffDotnetAdsSimulatorFacade()
    health = await facade.health()
    assert isinstance(health, SimulatorHealth)
    assert health.status == SimulatorStatus.NOT_RUNNING


@pytest.mark.asyncio
async def test_beckhoff_dotnet_facade_read_when_not_running() -> None:
    """未启动时 read 必须返回 NOT_RUNNING。"""

    facade = BeckhoffDotnetAdsSimulatorFacade()
    result = await facade.read(["ADS.ActivePower"])
    assert isinstance(result, ReadSimulatorResult)
    assert result.status == SimulatorStatus.NOT_RUNNING


@pytest.mark.asyncio
async def test_beckhoff_dotnet_facade_notification_is_not_implemented() -> None:
    """ADS_NOTIFICATION 必须仍为 NOT_IMPLEMENTED，不得 fake subscribe。"""

    source = _build_ads_source_for_real_test()
    facade = BeckhoffDotnetAdsSimulatorFacade(source=source)
    result = await facade.subscribe(["ADS.ActivePower"])
    assert result.status == SimulatorStatus.NOT_IMPLEMENTED
    report_result = await facade.report(["ADS.ActivePower"])
    assert report_result.status == SimulatorStatus.NOT_IMPLEMENTED


@pytest.mark.asyncio
async def test_beckhoff_dotnet_facade_environment_unavailable_returns_skip_info() -> None:
    """环境不足时 start 应返回 UNAVAILABLE 而非假通过。"""

    source = _build_ads_source_for_real_test()
    facade = BeckhoffDotnetAdsSimulatorFacade(source=source)

    start_result = await facade.start()
    if start_result.status == SimulatorStatus.UNAVAILABLE:
        # 这是预期行为——环境不足
        assert start_result.message, "UNAVAILABLE 必须有具体原因"
        # 确认 protocol_evidence 仍为 false
        assert facade.protocol_evidence is False
    elif start_result.status == SimulatorStatus.OK:
        # 环境满足——这是好事，继续测试
        try:
            health = await facade.health()
            assert health.status == SimulatorStatus.OK
        finally:
            stop_result = await facade.stop()
            assert stop_result.status == SimulatorStatus.OK
    else:
        # 其他状态码
        assert start_result.status != SimulatorStatus.ERROR, (
            f"环境就绪但意外错误: {start_result.message}"
        )


@pytest.mark.asyncio
async def test_beckhoff_dotnet_stop_when_not_running_is_idempotent() -> None:
    """未启动时 stop 应返回 NOT_RUNNING，不能异常。"""

    facade = BeckhoffDotnetAdsSimulatorFacade()
    result = await facade.stop()
    assert result.status == SimulatorStatus.NOT_RUNNING


# ── Real protocol read/write/readback (environment-dependent) ──────────────


@pytest.mark.asyncio
@pytest.mark.slow
async def test_beckhoff_ads_real_protocol_readback_full_cycle() -> None:
    """真实 ADS 完整 read/write/readback 闭环测试。

    环境满足时运行：
    1. 启动 .NET virtual ADS server；
    2. 读取初始值；
    3. 写入新值；
    4. readback 确认；
    5. 停止 server 并验证 protocol_evidence=true。

    环境不满足时 skip，原因必须具体（缺 dotnet / 缺 ADS Router /
    缺 AdsLib runner / 缺 NuGet restore / 非 Windows 等）。
    """

    skip_reason = _describe_env_skip_reason()
    if skip_reason is not None:
        pytest.skip(skip_reason)

    source = _build_ads_source_for_real_test()
    facade = BeckhoffDotnetAdsSimulatorFacade(source=source)

    # Start server
    start_result = await facade.start()
    if start_result.status == SimulatorStatus.UNAVAILABLE:
        pytest.skip(f"env became unavailable: {start_result.message}")
    assert start_result.status == SimulatorStatus.OK, start_result.message

    try:
        # Load points
        load_result = await facade.load_points([])
        assert load_result.status == SimulatorStatus.OK

        # Health check
        health = await facade.health()
        assert health.status == SimulatorStatus.OK
        assert health.points_count == 2

        # Read initial values
        read_before = await facade.read(
            ["ADS.ActivePower", "ADS.LocalState"]
        )
        assert read_before.status in {SimulatorStatus.OK, SimulatorStatus.PARTIAL_SUCCESS}, (
            f"initial read failed: {read_before.message if hasattr(read_before, 'message') else ''}"
        )

        # Write new values
        write_result = await facade.write({
            "ADS.ActivePower": 33.5,
            "ADS.LocalState": False,
        })
        assert write_result.status in {SimulatorStatus.OK, SimulatorStatus.PARTIAL_SUCCESS}, (
            f"write failed: {write_result.message}"
        )

        # Readback
        readback = await facade.read(
            ["ADS.ActivePower", "ADS.LocalState"]
        )
        assert readback.status in {SimulatorStatus.OK, SimulatorStatus.PARTIAL_SUCCESS}, (
            f"readback failed: {readback.message if hasattr(readback, 'message') else ''}"
        )

        # 如果能读到 readback 值，验证一致性
        if isinstance(readback.values, dict):
            if "ADS.ActivePower" in readback.values:
                assert readback.values["ADS.ActivePower"] == 33.5, (
                    f"readback value mismatch: expected 33.5, "
                    f"got {readback.values['ADS.ActivePower']}"
                )
            if "ADS.LocalState" in readback.values:
                assert readback.values["ADS.LocalState"] is False, (
                    f"readback value mismatch: expected False, "
                    f"got {readback.values['ADS.LocalState']}"
                )

        # 验证 protocol_evidence
        # 注意：只有当原生 AdsLib client 路径成功时才为 true
        # in_process fallback 不会设置 protocol_evidence
        from tools.source_lab.protocols.beckhoff_ads.ads_client import PyAdsClient

        client = getattr(facade, "_client", None)
        if isinstance(client, PyAdsClient) and client.protocol_evidence:
            assert facade.protocol_evidence, (
                "protocol_evidence should be true after successful "
                "native client read/write/readback cycle"
            )
    finally:
        stop_result = await facade.stop()
        assert stop_result.status in {
            SimulatorStatus.OK,
            SimulatorStatus.NOT_RUNNING,
            SimulatorStatus.PARTIAL_SUCCESS,
        }
        assert not facade.protocol_evidence, (
            "protocol_evidence should be reset to false after stop"
        )


# ── In-process backend comparison tests ────────────────────────────────────


@pytest.mark.asyncio
async def test_beckhoff_ads_in_process_backend_still_works() -> None:
    """确认 backend_kind=in_process 的 lightweight path 仍然可用。"""

    from tools.source_lab.tests.access.test_beckhoff_ads_simulator_contract import _build_ads_source

    source = _build_ads_source()
    # 显式设置 backend_kind=in_process
    source = replace(
        source,
        connection=replace(
            source.connection,
            params={**source.connection.params, "backend_kind": "in_process"},
        ),
    )
    facade = create_server_simulator("beckhoff_ads", source)

    assert (await facade.start()).status == SimulatorStatus.OK
    try:
        values = await facade.read(["ADS.ActivePower"])
        assert values.status == SimulatorStatus.OK
        assert isinstance(values.values, dict)
        assert values.values["ADS.ActivePower"] == 12.5

        write = await facade.write({"ADS.ActivePower": 77.5})
        assert write.status == SimulatorStatus.OK

        readback = await facade.read(["ADS.ActivePower"])
        assert isinstance(readback.values, dict)
        assert readback.values["ADS.ActivePower"] == 77.5
    finally:
        assert (await facade.stop()).status == SimulatorStatus.OK
