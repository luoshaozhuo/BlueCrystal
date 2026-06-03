""".NET virtual ADS server 生命周期测试。

证据等级：L4 integration（需 dotnet + AdsServer 项目环境满足）；
环境不满足时 L2 contract（仅验证接口契约和环境探测）。
本测试验证 create_virtual_ads_server 的 start/stop/cleanup 契约。
环境不足时标记为 skip/environment-pending，原因具体声明。
"""

from __future__ import annotations

import platform

import pytest

from tools.source_lab.protocols.beckhoff_ads.dotnet_virtual_server import (
    VirtualAdsServerLifecycle,
    VirtualAdsServerStartResult,
    create_virtual_ads_server,
    probe_dotnet_environment,
)


def test_create_virtual_ads_server_returns_lifecycle_instance() -> None:
    """create_virtual_ads_server 应返回 VirtualAdsServerLifecycle 实例。"""

    server = create_virtual_ads_server()
    assert isinstance(server, VirtualAdsServerLifecycle)
    assert not server.started
    assert server.pid == 0
    assert server.start_result is None


def test_virtual_ads_server_has_valid_address_defaults() -> None:
    """VirtualAdsServerLifecycle 默认 AMS Net ID 和端口应符合 Beckhoff 惯例。"""

    server = create_virtual_ads_server()
    assert server.ams_net_id
    assert "." in server.ams_net_id, f"AMS Net ID should be dotted: {server.ams_net_id}"
    assert server.ads_port > 0
    assert server.ads_port <= 65535
    assert server.router_port > 0


@pytest.mark.skipif(
    "missing_components" in str(
        probe_dotnet_environment().missing_components if probe_dotnet_environment().missing_components else ""
    ),
    reason="skip: dotnet environment not ready",
)
def test_dotnet_server_start_returns_structured_result_if_env_ready() -> None:
    """环境满足时，server.start() 应返回 VirtualAdsServerStartResult。"""

    probe = probe_dotnet_environment()
    if not probe.overall_environment_ready:
        pytest.skip(
            f"ADS .NET virtual server environment not ready: "
            f"{'; '.join(probe.missing_components)}"
        )

    server = create_virtual_ads_server()
    try:
        result = server.start()
        assert isinstance(result, VirtualAdsServerStartResult)
        if result.success:
            assert result.ams_net_id
            assert result.ads_port > 0
            assert result.pid > 0
            assert "127.0.0.1" in result.server_address
            assert server.started
            assert server.pid > 0
        else:
            # 失败原因必须具体
            assert result.message, "failure message must be non-empty"
    finally:
        if server.started:
            server.stop()


@pytest.mark.skipif(
    probe_dotnet_environment().overall_environment_ready,
    reason="dotnet environment is ready — skip contract-only test; "
           "use the start/stop integration test instead",
)
def test_dotnet_server_reports_unavailable_when_env_missing() -> None:
    """环境不足时，server.start() 必须返回 success=False 且原因具体。"""

    server = create_virtual_ads_server()
    try:
        result = server.start()
        assert not result.success, (
            "start should fail when environment is not ready"
        )
        assert result.message, (
            "failure message must be non-empty"
        )
        assert not server.started
        assert server.pid == 0
    finally:
        if server.started:
            server.stop()


@pytest.mark.skipif(
    not probe_dotnet_environment().overall_environment_ready,
    reason="ADS .NET virtual server environment not ready",
)
def test_dotnet_server_cleanup_is_reliable() -> None:
    """start 后 stop 必须可靠清理子进程，server 状态回到未启动。

    无论 start 成功与否，stop 后：
    - started 必须为 False；
    - pid 必须为 0；
    - 再次 stop 不能异常。
    """

    server = create_virtual_ads_server()
    server.start()

    # stop 必须可靠
    server.stop()
    assert not server.started, "server should be stopped after stop()"
    assert server.pid == 0, "pid should be 0 after stop()"

    # 重复 stop 不能异常
    server.stop()
    assert not server.started


@pytest.mark.skipif(
    not probe_dotnet_environment().overall_environment_ready,
    reason="ADS .NET virtual server environment not ready",
)
def test_dotnet_server_double_start_is_idempotent() -> None:
    """重复 start 应返回 started 状态而非异常。"""

    server = create_virtual_ads_server()
    try:
        first = server.start()
        if not first.success:
            pytest.skip(f"server failed to start: {first.message}")

        second = server.start()
        assert second.success, "second start on already-running server should succeed"
        assert "already running" in second.message.lower()
    finally:
        server.stop()


@pytest.mark.skipif(
    platform.system() != "Windows",
    reason="Full TwinCAT ADS Router verification requires Windows",
)
def test_dotnet_server_lifecycle_on_windows_has_ads_router_detection() -> None:
    """Windows 上 probe 应包含 ADS Router 和 TwinCAT 检测。"""

    probe = probe_dotnet_environment()
    assert probe.is_windows
    assert isinstance(probe.ads_router_available, bool)
    assert isinstance(probe.twincat_available, bool)
