"""All-protocol streaming profile registry tests.

注意：本测试验证的是 source_lab access framework closure（registry → factory → runner 构建）；
不等价于验证每个协议的完整工业协议标准合规性。
PASS 仅表示框架路由正确，不表示协议栈完整实现。
"""

from __future__ import annotations

from tools.source_lab.access.runners.registry import build_subscription_runner, supports_access_mode


_STREAMING_PROTOCOLS = (
    "opcua",
    "iec101",
    "iec104",
    "iec61850_report",
    "mqtt",
)


def test_all_streaming_profile_protocols_build_subscription_runner() -> None:
    """Subscribe profile should be available for all registered streaming protocols."""

    for protocol in _STREAMING_PROTOCOLS:
        assert supports_access_mode(protocol, "subscribe") is True
        runner = build_subscription_runner(protocol)
        assert runner.name
