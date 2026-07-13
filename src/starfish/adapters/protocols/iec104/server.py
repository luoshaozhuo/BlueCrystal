"""IEC104 Starfish server worker。

本 adapter 把 core `ServerDefinition` 绑定到 IEC104 native backend。它实现
`StarfishServerPort` 生命周期，不让 manager 依赖 IEC104 细节。
"""

from __future__ import annotations

from typing import Any

from starfish.core.definitions import ServerDefinition, ServerStatus
from starfish.adapters.protocols.iec104.backend import Iec104NativeBackend


class Iec104Server:
    """一个 IEC104 connection 对应的 simulator server worker。"""

    def __init__(
        self,
        definition: ServerDefinition,
        *,
        backend: Iec104NativeBackend | None = None,
    ) -> None:
        """初始化 IEC104 server worker。

        Args:
            definition: 从 DB view 映射出的 IEC104 server definition。
            backend: 测试可注入的 backend；未传入时创建 native backend。
        """
        if definition.protocol != "IEC104":
            raise ValueError(f"Iec104Server 只能接收 IEC104 definition: {definition.protocol}")
        self._definition = definition
        self._backend = backend or Iec104NativeBackend(
            bind_host=definition.bind_host,
            port=definition.bind_port,
        )
        self._initialized = False

    @property
    def definition(self) -> ServerDefinition:
        """返回该 worker 持有的 server definition。"""
        return self._definition

    @property
    def backend(self) -> Iec104NativeBackend:
        """返回注入的 backend，供测试验证 wiring。"""
        return self._backend

    def init(self) -> None:
        """加载点位并执行 backend 预连接；重复调用安全。"""
        if self._initialized:
            return
        self._backend.load_points(self._definition)
        self._backend.connect()
        self._initialized = True

    def start(self) -> None:
        """启动 IEC104 backend；未 init 时会先 init。"""
        self.init()
        self._backend.start()

    def stop(self) -> None:
        """停止 IEC104 backend。"""
        self._backend.stop()

    def status(self) -> ServerStatus:
        """返回 IEC104 server 当前运行状态。"""
        health = self._backend.health()
        reason = health.get("reason")
        return ServerStatus(
            connection_id=self._definition.connection_id,
            protocol=self._definition.protocol,
            status=str(health.get("status") or "unknown"),
            mode=str(health.get("mode") or "unknown"),
            running=bool(health.get("running")),
            point_count=int(health.get("point_count") or len(self._definition.point_items)),
            reason=str(reason) if reason else None,
            detail=_health_detail(health),
        )


def _health_detail(health: dict[str, Any]) -> dict[str, Any]:
    """过滤核心字段外的 backend health 细节。"""
    excluded = {"status", "mode", "running", "point_count", "reason"}
    return {key: value for key, value in health.items() if key not in excluded}


__all__ = ["Iec104Server"]
