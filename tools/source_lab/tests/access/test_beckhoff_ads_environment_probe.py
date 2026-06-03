"""Beckhoff ADS 环境探测测试。

证据等级：L2 contract + environment-pending（当环境不满足时 skip）。
本测试验证 probe_dotnet_environment 的结构化输出正确性。
当环境不满足时，明确声明缺失组件，不制造假通过。
"""

from __future__ import annotations

import platform

import pytest

from tools.source_lab.protocols.beckhoff_ads.dotnet_virtual_server import (
    DotnetEnvironmentProbeResult,
    describe_ads_environment_requirements,
    probe_dotnet_environment,
)


@pytest.mark.skipif(
    platform.system() != "Windows",
    reason="Beckhoff TwinCAT/ADS Router requires Windows for full environment; "
           "Linux can only validate dotnet + project file presence",
)
def test_beckhoff_ads_environment_probe_on_windows() -> None:
    """Windows 上应返回完整的环境探测结果（含 TwinCAT/ADS Router 检测）。"""

    result = probe_dotnet_environment()
    assert isinstance(result, DotnetEnvironmentProbeResult)
    assert result.platform_os == "Windows"


def test_beckhoff_ads_environment_probe_structure() -> None:
    """环境探测输出结构必须包含所有必要字段且类型正确。"""

    result = probe_dotnet_environment()
    assert isinstance(result, DotnetEnvironmentProbeResult)
    assert isinstance(result.dotnet_available, bool)
    assert isinstance(result.dotnet_version, str)
    assert isinstance(result.platform_os, str)
    assert isinstance(result.is_windows, bool)
    assert isinstance(result.ads_server_project_found, bool)
    assert isinstance(result.overall_environment_ready, bool)
    assert isinstance(result.missing_components, tuple)
    assert isinstance(result.probe_errors, tuple)

    # overall_environment_ready 不可为 True 当 missing_components 非空时
    if result.missing_components:
        assert not result.overall_environment_ready, (
            f"overall_environment_ready=True but missing components: "
            f"{result.missing_components}"
        )


def test_describe_ads_environment_requirements_structure() -> None:
    """describe_ads_environment_requirements 应返回结构化环境要求。"""

    requirements = describe_ads_environment_requirements()
    assert isinstance(requirements, dict)
    assert "dotnet" in requirements
    assert "twincat" in requirements
    assert "ads_router" in requirements
    assert "ads_server_project" in requirements
    assert requirements["dotnet"]["required"] is True
    assert requirements["ads_server_project"]["required"] is True


def test_environment_probe_reports_missing_components_honestly() -> None:
    """环境不足时必须将缺失组件列在 missing_components 中。"""

    result = probe_dotnet_environment()

    # 检查 dotnet 可用时 version 不为空
    if result.dotnet_available:
        assert result.dotnet_version, (
            "dotnet is available but version is empty"
        )

    # 非 Windows 时必须列出 twincat_runtime 缺失
    if not result.is_windows:
        assert "twincat_runtime" in result.missing_components, (
            "non-Windows platform should report twincat_runtime as missing"
        )


@pytest.mark.skipif(
    probe_dotnet_environment().overall_environment_ready is False,
    reason="ADS .NET virtual server environment not ready: "
           + (
               "; ".join(probe_dotnet_environment().missing_components)
               if probe_dotnet_environment().missing_components
               else "unknown"
           ),
)
def test_beckhoff_ads_environment_is_ready_for_full_test() -> None:
    """当环境满足时，确认 overall_environment_ready=True。"""

    result = probe_dotnet_environment()
    assert result.overall_environment_ready is True
    assert result.dotnet_available is True
    assert result.ads_server_project_found is True
