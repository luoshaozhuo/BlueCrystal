"""Protocol server factory adapter。

本 adapter 接收单 connection 配置 DataFrame，并在 IEC104/ADS worker 边界创建
runtime definition。协议分支保持在 composition 外围，manager 不感知实现细节。
"""

from __future__ import annotations

import pandas as pd

from starfish.adapters.protocols.ads.server import AdsServer
from starfish.adapters.protocols.iec104.server import Iec104Server
from starfish.core.ports.protocol_server import StarfishServerPort
from starfish.core.definitions import ServerDefinition


class ProtocolServerFactory:
    """根据协议创建 Starfish server worker 的 adapter factory。"""

    @classmethod
    def create(cls, definition: ServerDefinition) -> StarfishServerPort:
        """创建协议 server worker。

        Args:
            configuration: 单 connection、一行一个 point 的公共配置帧。

        Returns:
            实现 `StarfishServerPort` 的协议 worker。

        Raises:
            ValueError: 当前协议未注册。
        """
        protocol = definition.conn['protocol']
        if protocol == "IEC104":
            return Iec104Server(definition)
        elif protocol == "ADS":
            return AdsServer(definition)
        raise ValueError(f"Starfish 未注册 protocol={protocol}")


__all__ = ["ProtocolServerFactory"]
