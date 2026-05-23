"""All-protocol polling profile registry tests.

注意：本测试验证的是 source_lab access framework closure（registry → factory → runner 构建）；
不等价于验证每个协议的完整工业协议标准合规性。
PASS 仅表示框架路由正确，不表示协议栈完整实现。
"""

from __future__ import annotations

from tools.source_lab.access.runners.registry import build_capacity_runner, supports_access_mode


_POLLING_PROTOCOLS = (
    "opcua",
    "modbus_tcp",
    "modbus_rtu",
    "iec101",
    "iec104",
    "iec61850_mms",
    "http_rest",
)


def test_all_polling_profile_protocols_build_capacity_runner() -> None:
    """Polling profile should be available for all registered polling protocols."""

    for protocol in _POLLING_PROTOCOLS:
        assert supports_access_mode(protocol, "polling") is True
        runner = build_capacity_runner(protocol)
        assert runner.name
