"""starfish 运行时注册表。

提供根据 ServerPlan 端点协议创建对应 facade 的最小工厂。
支持四种模式：
- real:              已实现的协议专用真实 facade（HTTP_REST、MODBUS_TCP）。
- mqtt-lightweight:   MQTT 轻量级端点（TCP JSON 行协议，非完整 MQTT broker）。
- stub:              未实现协议的 in-memory stub fallback。
- unavailable:       已知但不可用的协议。

安全边界：
- 不得 import seahorse。
- 不得 import whale.ingest / whale.shared.source。
- 不得调用 Whale shared_source production client。
"""

from __future__ import annotations

from starfish.registry.runtime_registry import (
    RuntimeRegistry,
    FacadeEntry,
    create_facade_for_endpoint,
    create_facades,
    get_supported_protocols,
    get_real_protocols,
    get_lightweight_protocols,
)

__all__ = [
    "RuntimeRegistry",
    "FacadeEntry",
    "create_facade_for_endpoint",
    "create_facades",
    "get_supported_protocols",
    "get_real_protocols",
    "get_lightweight_protocols",
]
