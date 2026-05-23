"""All-protocol streaming capacity registry tests.

注意：本测试验证的是 source_lab access framework closure（registry → factory → runner 构建）；
不等价于验证每个协议的完整工业协议标准合规性。
PASS 仅表示框架路由正确，不表示协议栈完整实现。
"""

from __future__ import annotations

import pytest

from tools.source_lab.access.runners.registry import build_subscription_runner, supports_access_mode


_STREAMING_PROTOCOLS = (
    "opcua",
    "iec101",
    "iec104",
    "iec61850_report",
    "mqtt",
)


@pytest.mark.parametrize("protocol", _STREAMING_PROTOCOLS)
def test_all_streaming_capacity_protocols_are_supported(protocol: str) -> None:
    """Subscribe capacity path should expose a concrete runner for each protocol."""

    assert supports_access_mode(protocol, "subscribe") is True
    assert build_subscription_runner(protocol).name.endswith("runner")
