"""Protocol server factory adapter。

本 adapter 根据 core `ServerDefinition.protocol` 创建对应协议 worker。目前只
注册 IEC104；其他协议未接入时显式报错，避免 manager 中出现协议分支。
"""

from __future__ import annotations

from starfish.adapters.protocols.iec104.server import Iec104Server
from starfish.core.definitions import ServerDefinition
from starfish.core.ports.protocol_server import StarfishServerPort


class ProtocolServerFactory:
    """根据协议创建 Starfish server worker 的 adapter factory。"""

    def create(self, definition: ServerDefinition) -> StarfishServerPort:
        """创建协议 server worker。

        Args:
            definition: core server definition。

        Returns:
            实现 `StarfishServerPort` 的协议 worker。

        Raises:
            ValueError: 当前协议未注册。
        """
        if definition.protocol == "IEC104":
            return Iec104Server(definition)
        raise ValueError(f"当前 Starfish 只支持 IEC104，收到 protocol={definition.protocol}")


__all__ = ["ProtocolServerFactory"]
