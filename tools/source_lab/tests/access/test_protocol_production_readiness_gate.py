"""Protocol production readiness gate.

本测试验证协议的 production_client_read/write 标记是否满足工程门禁要求。
不允许 skipped 测试 — 所有门禁必须明确通过或失败。

门禁规则（对应 ai_shared/rules/ 中的协议准入策略）：

production_client_read=true 必须满足：
  1. shared/source/{protocol}/ 存在生产 client/backend/reader。
  2. ingest/adapters/source/{protocol}_source_acquisition_adapter.py 存在。
  3. 该协议有 native runner 或真实 Python production client。
  4. 该协议有 capacity 测试通过（通过 build_capacity_runner 验证）。
  5. 测试不得 skipped。
  6. 必须检查 RunnerInfo.actual_implementation_level，不得仅依赖 PROTOCOL_CAPABILITIES
     静态字典判断 native runner 可用性。

production_client_write=true 必须满足：
  1. SourceWritePort adapter 存在（{protocol}_source_write_adapter.py）。
  2. supported_write_operations 非空。
  3. native runner 或 production client 支持真实写入。

Python lightweight runner 不得标记 production_client_write=true。
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from tools.source_lab.access.runners.registry import (
    PROTOCOL_CAPABILITIES,
    RunnerInfo,
    build_capacity_runner,
    describe_protocol_runtime_readiness,
)

# ── Known production-ready protocols ───────────────────────────────────
# These are the protocols that currently have production clients in shared/source.

_KNOWN_PRODUCTION_READ_PROTOCOLS: dict[str, dict[str, str]] = {
    "opcua": {
        "shared_source": "src/whale/shared/source/opcua",
        "read_adapter": "src/whale/ingest/adapters/source/opcua_source_acquisition_adapter.py",
        "write_adapter": "src/whale/ingest/adapters/source/opcua_source_write_adapter.py",
    },
    "modbus_tcp": {
        "shared_source": "src/whale/shared/source/modbus",
        "read_adapter": "src/whale/ingest/adapters/source/modbus_source_acquisition_adapter.py",
        "write_adapter": "src/whale/ingest/adapters/source/modbus_source_write_adapter.py",
    },
    "iec61850_mms": {
        "shared_source": "src/whale/shared/source/iec61850",
        "read_adapter": "src/whale/ingest/adapters/source/iec61850_source_acquisition_adapter.py",
        "write_adapter": "src/whale/ingest/adapters/source/iec61850_source_write_adapter.py",
    },
    "iec61850_report": {
        "shared_source": "src/whale/shared/source/iec61850",
        "read_adapter": "src/whale/ingest/adapters/source/iec61850_report_source_acquisition_adapter.py",
        "write_adapter": "",
    },
}

_REPO_ROOT = Path(__file__).resolve().parents[4]


def _file_exists(relative_path: str) -> bool:
    return _REPO_ROOT.joinpath(relative_path).exists()


# ── Production client read gate ───────────────────────────────────────


@pytest.mark.parametrize("protocol, paths", list(_KNOWN_PRODUCTION_READ_PROTOCOLS.items()))
def test_known_production_protocols_have_shared_source(protocol: str, paths: dict[str, str]) -> None:
    """Known production client 协议必须有 shared/source/{protocol} 目录。"""
    shared_path = paths.get("shared_source", "")
    assert _file_exists(shared_path), (
        f"{protocol}: production client declared but {shared_path} does not exist"
    )


@pytest.mark.parametrize("protocol, paths", list(_KNOWN_PRODUCTION_READ_PROTOCOLS.items()))
def test_known_production_protocols_have_read_adapter(protocol: str, paths: dict[str, str]) -> None:
    """Known production client 协议必须有 read adapter。"""
    adapter_path = paths.get("read_adapter", "")
    assert _file_exists(adapter_path), (
        f"{protocol}: production client declared but {adapter_path} does not exist"
    )


def test_production_read_protocols_have_capacity_runner() -> None:
    """所有已知 production read 协议必须有可构建的 capacity runner。

    验证返回的 RunnerInfo 包含有效的 actual_implementation_level，
    不静默吞异常。
    """
    for protocol in _KNOWN_PRODUCTION_READ_PROTOCOLS:
        cap = PROTOCOL_CAPABILITIES.get(protocol, {})
        if cap.get("polling") is not True:
            continue
        try:
            info = build_capacity_runner(protocol)
            assert info is not None
            # RunnerInfo 必须包含实际实现级别
            assert isinstance(info, RunnerInfo)
            assert info.actual_implementation_level in (
                "real_native_runner", "python_lightweight_runner",
            ), f"{protocol}: unexpected actual_implementation_level={info.actual_implementation_level}"
            # 底层 runner 必须可用
            assert info.runner is not None
        except Exception as exc:
            pytest.fail(f"{protocol}: build_capacity_runner failed: {exc}")


# ── QA-8: native runner 运行时可用性检测 ──────────────────────────────


def test_native_runner_unavailable_detected_via_runner_info() -> None:
    """mock 原生二进制缺失时，build_capacity_runner 返回的 RunnerInfo
    的 actual_implementation_level 不等于 real_native_runner。

    确保 production/readiness gate 不因静态 PROTOCOL_CAPABILITIES 误报。
    """
    with patch(
        "tools.source_lab.access.runners.native_cmd._find_executable",
        return_value=None,
    ):
        # iec61850_mms 在静态注册表中声明为 real_native_runner
        info = build_capacity_runner("iec61850_mms")
        assert isinstance(info, RunnerInfo)
        # 静态声明仍为 real_native_runner
        assert info.declared_implementation_level == "real_native_runner"
        # 但运行时实际级别应为 python_lightweight
        assert info.actual_implementation_level != "real_native_runner", (
            "QA-8: native binary missing but RunnerInfo still claims real_native_runner"
        )
        assert info.fallback_reason is not None
        assert info.is_native_ready is False


def test_native_runner_available_via_runner_info() -> None:
    """原生二进制 mock 可用时，RunnerInfo 必须标记 is_native_ready=True，
    actual_runtime_availability=available_native。

    验证正常路径：native runner 可用时所有 readiness 属性正确。
    """
    mock_exe = MagicMock(spec=Path)
    mock_exe.exists.return_value = True
    with patch(
        "tools.source_lab.access.runners.native_cmd._find_executable",
        return_value=mock_exe,
    ):
        with patch("os.access", return_value=True):
            info = build_capacity_runner("iec61850_mms")
            assert isinstance(info, RunnerInfo)
            assert info.declared_implementation_level == "real_native_runner"
            assert info.actual_implementation_level == "real_native_runner"
            assert info.is_native_ready is True
            assert info.actual_runtime_availability == "available_native"
            assert info.fallback_reason is None
            assert info.native_check_error is None


def test_native_unavailable_has_fallback_fields() -> None:
    """native 不可用时，RunnerInfo 的 actual_runtime_availability 必须为
    degraded_python_fallback，且 native_check_error 和 fallback_reason 不能为空。
    """
    with patch(
        "tools.source_lab.access.runners.native_cmd._find_executable",
        return_value=None,
    ):
        info = build_capacity_runner("iec61850_mms")
        assert isinstance(info, RunnerInfo)
        # 运行时可用性必须显式标记为 degraded
        assert info.actual_runtime_availability == "degraded_python_fallback", (
            f"QA-8: expected 'degraded_python_fallback' but got "
            f"'{info.actual_runtime_availability}'"
        )
        # fallback 原因必须明确
        assert info.fallback_reason is not None, (
            "QA-8: fallback_reason must be set when native is unavailable"
        )
        # native 检测错误必须记录
        assert info.native_check_error is not None, (
            "QA-8: native_check_error must be set when native check fails"
        )
        # actual_runner 必须反映实际使用的 runner
        assert "python_lightweight" not in info.actual_runner.lower(), (
            f"QA-8: actual_runner should not be the fallback's Python name, "
            f"got {info.actual_runner}"
        )


@pytest.mark.parametrize("protocol", ["opcua", "modbus_tcp", "iec104", "iec61850_mms"])
def test_runner_info_fields_for_protocols(protocol: str) -> None:
    """每个协议 mock native 不可用时，RunnerInfo 字段必须完整。"""
    with patch(
        "tools.source_lab.access.runners.native_cmd._find_executable",
        return_value=None,
    ):
        info = build_capacity_runner(protocol)
        assert isinstance(info, RunnerInfo)
        # 必须有 declared/actual/availability 三元组
        assert isinstance(info.declared_implementation_level, str)
        assert isinstance(info.actual_implementation_level, str)
        assert info.actual_runtime_availability in (
            "available_native",
            "degraded_python_fallback",
            "unavailable",
        ), f"{protocol}: unexpected actual_runtime_availability={info.actual_runtime_availability}"
        assert isinstance(info.actual_runner, str)
        assert len(info.actual_runner) > 0
        assert info.fallback_reason is not None


def test_readiness_gate_does_not_treat_degraded_as_ready() -> None:
    """readiness gate 验证：当 RunnerInfo.is_native_ready=False 时，
    不得将协议判定为 real_native_runner ready。

    确保调用方不因 PROTOCOL_CAPABILITIES 静态字典的高估而误判。
    """
    with patch(
        "tools.source_lab.access.runners.native_cmd._find_executable",
        return_value=None,
    ):
        info = build_capacity_runner("iec61850_mms")
        # readiness gate 必须以 is_native_ready 为准
        assert info.is_native_ready is False, (
            "QA-8: readiness gate must not treat a degraded runner as native-ready. "
            "is_native_ready must be False when native binary is absent."
        )
        # 但声明级别仍然不变（向后兼容）
        assert info.declared_implementation_level == "real_native_runner"
        # 运行时可用性标记为 degraded
        assert info.actual_runtime_availability == "degraded_python_fallback"


# ── Production client write gate ──────────────────────────────────────


@pytest.mark.parametrize("protocol, paths", list(_KNOWN_PRODUCTION_READ_PROTOCOLS.items()))
def test_production_write_protocols_have_write_adapter(protocol: str, paths: dict[str, str]) -> None:
    """production_client_write=True 协议必须有 write adapter。"""
    cap = PROTOCOL_CAPABILITIES.get(protocol, {})
    if cap.get("production_client_write") is not True:
        return  # not a write-enabled protocol — skip check, not a failure
    write_adapter = paths.get("write_adapter", "")
    assert _file_exists(write_adapter), (
        f"{protocol}: production_client_write=True but {write_adapter} does not exist"
    )
    supported: tuple[str, ...] = cap.get("supported_write_operations", ())  # type: ignore[assignment]
    assert len(supported) >= 1, (
        f"{protocol}: production_client_write=True but supported_write_operations is empty"
    )


def test_non_production_protocols_must_not_have_write_adapter_in_known() -> None:
    """production_client_write=False 协议不应在已知映射中有 write adapter。"""
    for protocol, paths in _KNOWN_PRODUCTION_READ_PROTOCOLS.items():
        cap = PROTOCOL_CAPABILITIES.get(protocol, {})
        if cap.get("production_client_write") is True:
            continue  # write-enabled, adapter expected
        wa = paths.get("write_adapter", "")
        if wa and _file_exists(wa):
            pytest.fail(
                f"{protocol}: production_client_write=False but {wa} exists. "
                "Either remove the adapter or set production_client_write=True."
            )


def test_python_lightweight_runners_must_not_claim_production_write() -> None:
    """python_lightweight_runner 不得标记 production_client_write=true。"""
    for name, cap in PROTOCOL_CAPABILITIES.items():
        level = cap.get("current_implementation_level", "")
        if level != "python_lightweight_runner":
            continue
        if cap.get("write") is True or cap.get("production_client_write") is True:
            pytest.fail(
                f"{name}: python_lightweight_runner must not claim "
                f"production_client_write=true"
            )


# ── Registry integrity gate ──────────────────────────────────────────


def test_production_client_write_requires_supported_operations() -> None:
    """production_client_write=True → supported_write_operations 必须非空。"""
    for name, cap in PROTOCOL_CAPABILITIES.items():
        if cap.get("production_client_write") is not True:
            continue
        supported: tuple[str, ...] = cap.get("supported_write_operations", ())  # type: ignore[assignment]
        assert len(supported) >= 1, (
            f"{name}: production_client_write=True but supported_write_operations is empty"
        )


def test_all_protocols_have_write_operation_fields() -> None:
    """每个协议条目必须有 supported_write_operations 和 unsupported_write_operations。"""
    for name, cap in PROTOCOL_CAPABILITIES.items():
        assert "supported_write_operations" in cap, f"{name}: missing supported_write_operations"
        assert "unsupported_write_operations" in cap, f"{name}: missing unsupported_write_operations"


@pytest.mark.parametrize(
    ("protocol", "expected_level", "expected_availability"),
    [
        ("iec101", "fake_or_simulated_runner", "degraded_runtime"),
        ("iec104", "fake_or_simulated_runner", "degraded_runtime"),
        ("mqtt", "python_lightweight_runner", "available_runtime"),
    ],
)
def test_subscription_runtime_readiness_reports_actual_non_native_level(
    protocol: str,
    expected_level: str,
    expected_availability: str,
) -> None:
    """subscription readiness 不能只回显静态声明级别。"""
    readiness = describe_protocol_runtime_readiness(protocol, "streaming")
    assert readiness.declared_implementation_level == "real_native_runner" or protocol == "mqtt"
    assert readiness.actual_implementation_level == expected_level
    assert readiness.actual_runtime_availability == expected_availability
    assert readiness.is_native_ready is False


def test_opcua_subscription_native_missing_is_not_runtime_ready() -> None:
    """即使静态 capability 为 native，runner 缺失时 subscription readiness 也不能 PASS。"""
    with patch(
        "tools.source_lab.access.runners.open62541_subscription._resolve_runner_path",
        return_value=Path("/nonexistent/open62541_subscription_runner"),
    ):
        readiness = describe_protocol_runtime_readiness("opcua", "streaming")
    assert readiness.declared_implementation_level == "real_native_runner"
    assert readiness.actual_implementation_level == "unavailable"
    assert readiness.actual_runtime_availability == "unavailable"
    assert readiness.is_native_ready is False


def test_goose_runtime_readiness_keeps_controlled_l2_tags() -> None:
    """GOOSE readiness 输出必须保留受控 L2 环境标签。"""
    with patch(
        "tools.source_lab.access.runners.iec61850_l2_streaming._find_executable",
        return_value=Path("/tmp/iec61850_goose_subscriber_runner"),
    ):
        readiness = describe_protocol_runtime_readiness("iec61850_goose", "streaming")
    assert readiness.actual_implementation_level == "real_native_runner"
    assert readiness.actual_runtime_availability == "available_native"
    assert "controlled_l2_environment" in readiness.runtime_constraint_tags
    assert "cap_net_raw_required" in readiness.runtime_constraint_tags


def test_report_runtime_readiness_requires_endpoint_opt_in_even_with_native_binary() -> None:
    """IEC 61850 Report 不能因 native binary 存在就被当作默认 runtime-ready native。"""
    with patch(
        "tools.source_lab.access.runners.iec61850_report._resolve_runner_path",
        return_value=Path("/tmp/iec61850_report_runner"),
    ):
        readiness = describe_protocol_runtime_readiness("iec61850_report", "streaming")
    assert readiness.declared_implementation_level == "real_native_runner"
    assert readiness.actual_implementation_level == "python_lightweight_runner"
    assert readiness.actual_runtime_availability == "degraded_runtime"
    assert "endpoint_opt_in_required" in readiness.runtime_constraint_tags
