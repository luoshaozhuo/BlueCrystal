"""Starfish core server manager。

`StarfishServerManager` 是 Supervisor/Worker 模型中的 supervisor。它持有装配完成
的一行一个 point 配置 DataFrame，并用原生 dict 管理 worker 生命周期；它不知道
DB view、IEC104 native runner 或 CLI 参数。
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from pacific.starfish.core.ports.protocol_server import StarfishServerPort

class StarfishServerManager:
    def __init__(self, servers: Iterable[StarfishServerPort]):
        self.servers = servers

    def start(self) -> None:
        for server in self.servers:
            if server.status().running:
                continue
            try:
                server.init()
                server.start()
            except Exception:
                self.stop()
                raise

    def stop(self) -> None:
        for server in self.servers:
            if not server.status().running:
                continue
            server.stop()

    def status(self) -> dict[str, Any]:
        """返回 manager 状态字典。"""
        return {{
            "connection_id": server.definition.connection_id,
            "protocol": server.definition.protocol,
            "status": server.status(),
            } for server in self.servers}