"""Beckhoff ADS client runner / preflight 测试。

验证 AdsLib native runner 的预检行为：binary 缺失时返回明确的 protocol、
runner、path 和 build_hint；不得让缺失导致假通过。
"""

from __future__ import annotations

from unittest.mock import patch

from tools.source_lab.access.runners.native_cmd import NativeRunnerUnavailableError
from tools.source_lab.access.runners.native_runner_map import (
    _BeckhoffAdsNativeRunner,
    beckhoff_ads_native_preflight,
)
from tools.source_lab.access.runners.registry import build_capacity_runner, describe_protocol_runtime_readiness


def test_beckhoff_ads_native_preflight_reports_runner_and_build_hint() -> None:
    """AdsLib runner 缺失时必须返回明确 unavailable/build hint。"""

    runner = _BeckhoffAdsNativeRunner()
    with patch("tools.source_lab.access.runners.native_cmd._find_executable", return_value=None):
        try:
            runner.check_available()
        except NativeRunnerUnavailableError as exc:
            assert exc.protocol == "beckhoff_ads"
            assert exc.runner_name == "beckhoff_ads_polling_runner"
            assert "cmake" in str(exc).lower() or "build" in str(exc).lower()
        else:  # pragma: no cover - should not happen
            raise AssertionError("expected NativeRunnerUnavailableError")


def test_beckhoff_ads_capacity_runner_falls_back_to_python_with_explicit_error() -> None:
    """build_capacity_runner 应回退到 Python runner，并保留 native 检测错误。"""

    with patch("tools.source_lab.access.runners.native_cmd._find_executable", return_value=None):
        info = build_capacity_runner("beckhoff_ads")
    assert info.runner.name == "beckhoff_ads_polling_runner"
    assert info.actual_implementation_level == "python_lightweight_runner"
    assert info.actual_runtime_availability == "degraded_python_fallback"
    assert info.native_check_error is not None
    assert "beckhoff_ads_polling_runner" in info.native_check_error


def test_beckhoff_ads_streaming_readiness_is_explicitly_unavailable() -> None:
    """ADS_NOTIFICATION 未完成时 runtime readiness 不能伪装 available。"""

    readiness = describe_protocol_runtime_readiness("beckhoff_ads", "streaming")
    assert readiness.actual_runtime_availability == "unavailable"
    assert readiness.fallback_reason is not None
    assert "notification" in readiness.fallback_reason.lower()


def test_beckhoff_ads_native_preflight_integration() -> None:
    """集成测试：native_runner_map.beckhoff_ads_native_preflight 输出应结构化。"""

    result = beckhoff_ads_native_preflight()
    assert isinstance(result, dict)
    assert "available" in result
    assert result["protocol"] == "beckhoff_ads"
    assert result["runner"] == "beckhoff_ads_polling_runner"
    assert isinstance(result["path"], str)
    assert result["path"]  # 不为空
    if not result["available"]:
        assert result["error"] is not None, (
            "unavailable preflight must have non-null error"
        )
        assert result["build_hint"] is not None, (
            "unavailable preflight must have non-null build_hint"
        )
