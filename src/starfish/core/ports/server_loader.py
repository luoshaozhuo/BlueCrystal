"""Server definition loader port。"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from starfish.core.definitions import ServerDefinition


class ServerDefinitionLoaderPort(Protocol):
    """从外部来源加载 simulator server definition 的 port。"""

    def load(self, connection_ids: Sequence[int]) -> list[ServerDefinition]:
        """加载指定 connection IDs 对应的 server definitions。"""


__all__ = ["ServerDefinitionLoaderPort"]
