"""All-protocol probe capability matrix tests.

注意：本测试验证的是 source_lab access framework closure（registry → probe mode 映射）；
不等价于验证每个协议的完整工业协议标准合规性。
PASS 仅表示框架路由正确，不表示协议栈完整实现。
"""

from __future__ import annotations

from tools.source_lab.access.runners.registry import (
    list_supported_protocols,
    probe_mode_for_protocol,
)


def test_all_protocols_have_probe_mode_or_explicit_support() -> None:
    """Each registered protocol should map to a concrete probe mode."""

    modes = {protocol: probe_mode_for_protocol(protocol) for protocol in list_supported_protocols()}
    assert modes == {
        "opcua": "polling",
        "modbus_tcp": "polling",
        "modbus_rtu": "polling",
        "iec101": "polling",
        "iec104": "polling",
        "iec61850_mms": "polling",
        "iec61850_report": "streaming",
        "mqtt": "streaming",
        "http_rest": "polling",
    }
