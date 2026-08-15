"""Server factory port。"""

from __future__ import annotations

from typing import Protocol

import pandas as pd

from pacific.starfish.core.ports.protocol_server import StarfishServerPort
from pacific.starfish.core.definitions import ServerDefinition


class ServerFactoryPort(Protocol):
    """根据单 connection 配置帧创建协议 server worker 的 port。"""

    def create(self, definition: ServerDefinition) -> StarfishServerPort:
        """在协议原生边界创建一个可由 manager 管理的 server worker。"""


__all__ = ["ServerFactoryPort"]
