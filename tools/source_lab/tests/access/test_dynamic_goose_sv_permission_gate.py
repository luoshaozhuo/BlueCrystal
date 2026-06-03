"""GOOSE/SV dynamic endpoint 权限门禁测试。

验证 L2 权限检查（CAP_NET_RAW、interface 可用性）的准入逻辑。
测试阶段：开发期验证 (contract)。
"""
from __future__ import annotations

from tools.source_lab.tests.access.test_dynamic_goose_sv_streaming_endpoint_adjustment import (
    _l2_runtime_status,
)


def test_goose_sv_permission_gate_reports_raw_socket_permission_missing_without_false_pass() -> None:
    for protocol in ("iec61850_goose", "iec61850_sv"):
        allowed, reason = _l2_runtime_status(protocol)
        if allowed:
            assert reason is None
            continue
        assert reason is not None
        assert "raw_socket_permission_missing" in reason or "dependency_missing" in reason


def test_goose_sv_dynamic_gate_does_not_count_skip_as_pass() -> None:
    statuses = [_l2_runtime_status(protocol) for protocol in ("iec61850_goose", "iec61850_sv")]
    for allowed, reason in statuses:
        if allowed:
            assert reason is None
        else:
            assert reason is not None
            assert "PASSED_TRUE_EVENT_SAMPLE" not in reason
