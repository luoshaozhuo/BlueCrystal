"""native interactive control 边界测试。

验证 native runner 交互式控制接口的安全边界和权限隔离。
测试阶段：开发期验证 (contract)。
"""
from __future__ import annotations

from tools.source_lab.access.runtime import NATIVE_INTERACTIVE_CONTROL_CAPABILITIES


def test_dynamic_native_interactive_control_boundary() -> None:
    for protocol in ("opcua", "iec61850_report", "iec61850_goose", "iec61850_sv", "mqtt"):
        metadata = NATIVE_INTERACTIVE_CONTROL_CAPABILITIES[protocol]
        assert metadata["mode"] == "replacement_only"
        assert metadata["interactive_control"] is False
        assert isinstance(metadata["reason"], str) and metadata["reason"]


def test_replacement_only_runner_is_not_marked_interactive() -> None:
    replacement_only = [
        protocol
        for protocol, metadata in NATIVE_INTERACTIVE_CONTROL_CAPABILITIES.items()
        if metadata["mode"] == "replacement_only"
    ]
    assert replacement_only
    assert all(
        NATIVE_INTERACTIVE_CONTROL_CAPABILITIES[protocol]["interactive_control"] is False
        for protocol in replacement_only
    )
