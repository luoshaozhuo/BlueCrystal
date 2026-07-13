"""Server factory port。"""

from __future__ import annotations

from typing import Protocol

from starfish.core.definitions import ServerDefinition
from starfish.core.ports.protocol_server import StarfishServerPort


class ServerFactoryPort(Protocol):
    """根据 server definition 创建协议 server worker 的 port。"""

    def create(self, definition: ServerDefinition) -> StarfishServerPort:
        """创建一个可由 manager 管理的 server worker。"""


__all__ = ["ServerFactoryPort"]
