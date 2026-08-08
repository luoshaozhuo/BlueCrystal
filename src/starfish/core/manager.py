"""Starfish core server manager。

`StarfishServerManager` 是 Supervisor/Worker 模型中的 supervisor。它只管理
实现 `StarfishServerPort` 的 server worker 生命周期，不知道 DB view、
IEC104 native runner 或 CLI 参数。
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from starfish.core.definitions import ServerDefinition
from starfish.core.ports.protocol_server import StarfishServerPort
from starfish.core.ports.server_factory import ServerFactoryPort


class StarfishServerManager:
    """管理多个 Starfish server worker 的 core supervisor。"""

    def __init__(self, servers: Iterable[StarfishServerPort]) -> None:
        """初始化 manager。

        Args:
            servers: 已由 adapter/factory 创建好的 server worker。

        Raises:
            ValueError: 出现重复 connection_id。
        """
        self._servers: dict[int, StarfishServerPort] = {}
        self._initialized = False
        for server in servers:
            connection_id = server.definition.connection_id
            if connection_id in self._servers:
                raise ValueError(f"重复 connection_id: {connection_id}")
            self._servers[connection_id] = server

    @classmethod
    def from_definitions(
        cls,
        definitions: Iterable[ServerDefinition],
        server_factory: ServerFactoryPort,
    ) -> "StarfishServerManager":
        """根据 definition 和 factory 创建 manager。

        Args:
            definitions: 已由 loader 映射完成的纯 server definition。
            server_factory: 实现协议 worker 创建逻辑的 factory port。

        Returns:
            已持有 server workers、尚未启动的 manager。
        """
        return cls(server_factory.create(definition) for definition in definitions)

    @property
    def servers(self) -> dict[int, StarfishServerPort]:
        """返回 connection_id 到 server worker 的只读快照。"""
        return dict(self._servers)

    @property
    def server_count(self) -> int:
        """返回当前 manager 持有的 server 数量。"""
        return len(self._servers)

    def init(self) -> None:
        """初始化全部 server；重复调用安全。"""
        if self._initialized:
            return
        for server in self._servers.values():
            server.init()
        self._initialized = True

    def start(self) -> None:
        """初始化并启动全部 server。

        如果某个 server 启动失败，已启动 server 会被停止，异常继续向上抛出，
        由 CLI/API 边界转换为用户可见错误。
        """
        self.init()
        started: list[StarfishServerPort] = []
        try:
            for server in self._servers.values():
                server.start()
                started.append(server)
        except Exception:
            for server in reversed(started):
                server.stop()
            raise

    def stop(self) -> None:
        """停止全部 server；重复调用安全。"""
        for server in reversed(list(self._servers.values())):
            server.stop()

    def status(self) -> dict[str, Any]:
        """返回全部 server 的运行状态摘要。"""
        return {
            "server_count": self.server_count,
            "servers": self._server_statuses(),
        }

    def _server_statuses(
        self,
        connection_id: int | None = None,
    ) -> dict[int, dict[str, Any]]:
        """返回一个或全部 server 的状态快照。

        Args:
            connection_id: 指定时只返回单个 server 状态。

        Returns:
            `connection_id -> status dict`。

        Raises:
            KeyError: 指定 connection_id 不存在。
        """
        if connection_id is not None:
            server = self._servers[int(connection_id)]
            return {int(connection_id): _status_dict(server)}
        return {
            connection_id: _status_dict(server) for connection_id, server in self._servers.items()
        }

    def health(self, connection_id: int | None = None) -> dict[str, Any]:
        """返回一个或全部 server 的健康状态摘要。"""
        return {
            "server_count": self.server_count,
            "servers": self._server_statuses(connection_id=connection_id),
        }

    def describe(self) -> dict[str, Any]:
        """返回 manager 装配摘要，不触发 server 启动。"""
        return {
            "server_count": len(self._servers),
            "servers": [
                {
                    "connection_id": definition.connection_id,
                    "name": definition.name,
                    "protocol": definition.protocol,
                    "bind_host": definition.bind_host,
                    "bind_port": definition.bind_port,
                    "point_count": len(definition.point_items),
                    "task_count": len(definition.tasks),
                    "capabilities": list(definition.capabilities),
                }
                for definition in (server.definition for server in self._servers.values())
            ],
        }


def _status_dict(server: StarfishServerPort) -> dict[str, Any]:
    """把 ServerStatus dataclass 转成 API/CLI 稳定 dict。"""
    snapshot = server.status()
    result = {
        "connection_id": snapshot.connection_id,
        "protocol": snapshot.protocol,
        "status": snapshot.status,
        "mode": snapshot.mode,
        "running": snapshot.running,
        "point_count": snapshot.point_count,
        "reason": snapshot.reason,
    }
    result.update(snapshot.detail)
    return result


__all__ = ["StarfishServerManager"]
