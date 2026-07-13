"""Protocol server worker port。"""

from __future__ import annotations

from typing import Protocol

from starfish.core.definitions import ServerDefinition, ServerStatus


class StarfishServerPort(Protocol):
    """core manager 可管理的 simulator server worker 契约。"""

    @property
    def definition(self) -> ServerDefinition:
        """返回该 worker 持有的 server definition。"""

    def init(self) -> None:
        """初始化 server 内部资源；重复调用应安全。"""

    def start(self) -> None:
        """启动 server；重复调用应安全。"""

    def stop(self) -> None:
        """停止 server 并释放运行资源；重复调用应安全。"""

    def status(self) -> ServerStatus:
        """返回 server 当前运行状态。"""


__all__ = ["StarfishServerPort"]
