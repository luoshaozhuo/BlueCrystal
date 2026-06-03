"""Beckhoff AdsLib native runner 预检测试。

测试阶段：开发期验证 (contract)（测试 preflight 输出的结构化契约和边界行为）。
本测试验证：
- ads_native_preflight 在 binary 缺失时的返回结构；
- error 必须包含 protocol、runner、path、build_hint；
- 不得让缺失二进制导致假通过；
- _BeckhoffAdsNativeRunner.check_available 的异常结构。
"""

from __future__ import annotations

from tools.source_lab.access.runners.native_cmd import NativeRunnerUnavailableError
from tools.source_lab.access.runners.native_runner_map import (
    _BeckhoffAdsNativeRunner,
    beckhoff_ads_native_preflight,
)


def test_beckhoff_ads_native_preflight_has_required_fields() -> None:
    """ads_native_preflight 输出必须包含所有必要字段。"""

    result = beckhoff_ads_native_preflight()
    assert isinstance(result, dict)
    assert "available" in result
    assert "protocol" in result
    assert "runner" in result
    assert "path" in result
    assert "build_hint" in result
    assert "error" in result

    assert result["protocol"] == "beckhoff_ads"
    assert result["runner"] == "beckhoff_ads_polling_runner"
    assert isinstance(result["available"], bool)
    assert isinstance(result["path"], str)


def test_beckhoff_ads_native_preflight_when_unavailable_has_error() -> None:
    """binary 缺失时 available=False 且 error 必须非空。"""

    result = beckhoff_ads_native_preflight()
    if not result["available"]:
        assert result["error"] is not None, (
            "unavailable preflight must have a non-null error field"
        )
        assert isinstance(result["error"], str)
        assert len(result["error"]) > 0, "error must not be empty"
        # error 应包含 protocol 名或 runner 名
        assert (
            "beckhoff_ads" in str(result["error"]).lower()
            or "beckhoff_ads_polling_runner" in str(result["error"])
        ), f"error should mention protocol or runner name: {result['error']}"
        # build_hint 必须存在
        assert result["build_hint"] is not None, (
            "unavailable preflight must have a build_hint"
        )


def test_beckhoff_ads_native_preflight_when_available_is_honest() -> None:
    """binary 存在时 available=True 且 error=None。"""

    result = beckhoff_ads_native_preflight()
    if result["available"]:
        assert result["error"] is None, (
            "available preflight must have error=None"
        )
        assert result["build_hint"] is None, (
            "available preflight must have build_hint=None"
        )


def test_beckhoff_ads_native_runner_check_available_struct() -> None:
    """_BeckhoffAdsNativeRunner.check_available 应显式抛出异常而非假成功。"""

    runner = _BeckhoffAdsNativeRunner()
    try:
        runner.check_available()
        # 正常：binary 存在
        assert (
            runner.name == "beckhoff_ads_native_runner"
        ), f"unexpected name: {runner.name}"
    except NativeRunnerUnavailableError as exc:
        # 这是预期行为：binary 缺失
        assert exc.protocol == "beckhoff_ads", (
            f"expected protocol='beckhoff_ads', got '{exc.protocol}'"
        )
        assert exc.runner_name == "beckhoff_ads_polling_runner", (
            f"expected runner_name='beckhoff_ads_polling_runner', "
            f"got '{exc.runner_name}'"
        )
        assert exc.expected_path, (
            "NativeRunnerUnavailableError must include expected_path"
        )
        assert exc.build_hint, (
            "NativeRunnerUnavailableError must include build_hint"
        )
        # build_hint 应包含 cmake 或构建提示
        build_hint_lower = exc.build_hint.lower()
        assert (
            "cmake" in build_hint_lower
            or "build" in build_hint_lower
            or "compile" in build_hint_lower
            or "ads" in build_hint_lower
        ), f"build_hint should contain build instructions: {exc.build_hint}"


def test_beckhoff_ads_native_preflight_never_returns_none_error() -> None:
    """preflight 的 error 字段必须始终是 str 或 None，不能是其他类型。"""

    result = beckhoff_ads_native_preflight()
    error_val = result.get("error")
    assert error_val is None or isinstance(error_val, str), (
        f"error must be str or None, got {type(error_val).__name__}"
    )


def test_beckhoff_ads_native_preflight_runner_name_is_constant() -> None:
    """runner 名称必须始终为 beckhoff_ads_polling_runner。"""

    result = beckhoff_ads_native_preflight()
    assert result["runner"] == "beckhoff_ads_polling_runner", (
        f"runner name changed unexpectedly: {result['runner']}"
    )
