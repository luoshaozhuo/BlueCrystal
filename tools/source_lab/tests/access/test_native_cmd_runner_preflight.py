"""NativeCmdCapacityRunner 预检单元测试。

验证：
1. 二进制存在 → check_available() 通过
2. 二进制缺失 → NativeRunnerUnavailableError
3. 错误消息包含 protocol/runner_name/expected_path/build_hint
4. 真实 runner（modbus_tcp/iec61850_mms）预检正常通过
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from tools.source_lab.access.runners.native_cmd import (
    NativeCmdCapacityRunner,
    NativeRunnerUnavailableError,
    _find_executable,
)


class _TestNativeRunner(NativeCmdCapacityRunner):
    """Minimal runner subclass for preflight testing."""
    name = "test_native_runner"
    executable_name = "non_existent_binary_xyz"


class _RealNativeRunner(NativeCmdCapacityRunner):
    """Runner with a known real binary for positive testing."""
    name = "modbus_tcp_native_runner"
    executable_name = "modbus_tcp_polling_runner"


def test_preflight_missing_binary_raises_error() -> None:
    """二进制缺失时 check_available() 抛出 NativeRunnerUnavailableError。"""
    runner = _TestNativeRunner()
    with patch(
        "tools.source_lab.access.runners.native_cmd._find_executable",
        return_value=None,
    ):
        with pytest.raises(NativeRunnerUnavailableError) as excinfo:
            runner.check_available()

    assert runner.executable_name in str(excinfo.value)
    assert "not found" in str(excinfo.value).lower()
    assert excinfo.value.runner_name == "non_existent_binary_xyz"
    assert excinfo.value.expected_path != ""


def test_preflight_error_contains_build_hint() -> None:
    """错误消息包含编译提示。"""
    runner = _TestNativeRunner()
    with patch(
        "tools.source_lab.access.runners.native_cmd._find_executable",
        return_value=None,
    ):
        with pytest.raises(NativeRunnerUnavailableError) as excinfo:
            runner.check_available()

    msg = str(excinfo.value)
    assert "cmake" in msg or "build" in msg


def test_preflight_available_passes() -> None:
    """二进制存在且可执行时 check_available() 不抛出异常。"""
    # 使用真实的 find_executable 路径（应当能找到编译产物）
    exe = _find_executable("modbus_tcp_polling_runner")
    if exe is None:
        pytest.skip("modbus_tcp_polling_runner not compiled in this environment")

    runner = _RealNativeRunner()
    # 不应抛异常
    runner.check_available()


def test_preflight_available_exe_check() -> None:
    """使用 mock 验证二进制存在时可执行检查通过。"""
    runner = _TestNativeRunner()
    # 使用 /bin/true 作为模拟二进制
    with patch(
        "tools.source_lab.access.runners.native_cmd._find_executable",
        return_value=Path("/bin/true"),
    ):
        # 不应抛异常
        runner.check_available()


def test_preflight_iec61850_mms_available() -> None:
    """iec61850_mms 原生 runner 可执行文件应当已编译。"""
    from tools.source_lab.access.runners.native_runner_map import _Iec61850MmsNativeRunner

    exe = _find_executable("iec61850_mms_client_runner")
    if exe is None:
        pytest.skip("iec61850_mms_client_runner not compiled in this environment")

    runner = _Iec61850MmsNativeRunner()
    runner.check_available()


def test_build_capacity_runner_native_uses_preflight() -> None:
    """build_capacity_runner 对原生 runner 执行预检。"""
    from tools.source_lab.access.runners.registry import build_capacity_runner

    # iec61850_mms: 应当返回原生 runner（不是 Python fallback）
    runner = build_capacity_runner("iec61850_mms")
    from tools.source_lab.access.runners.native_cmd import NativeCmdCapacityRunner
    assert isinstance(runner, NativeCmdCapacityRunner)


def test_build_capacity_runner_fallback_on_missing() -> None:
    """原生二进制缺失时 build_capacity_runner 回退到 Python lightweight runner。"""
    from tools.source_lab.access.runners.registry import build_capacity_runner

    # mock 让所有 _find_executable 返回 None → 原生 runner 预检失败 → fallback
    with patch(
        "tools.source_lab.access.runners.native_cmd._find_executable",
        return_value=None,
    ):
        # iec61850_mms 有 Python fallback (Iec61850MmsPollingRunner)
        runner = build_capacity_runner("iec61850_mms")
        from tools.source_lab.access.runners.native_cmd import NativeCmdCapacityRunner
        assert not isinstance(runner, NativeCmdCapacityRunner)
