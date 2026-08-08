"""IEC104 Starfish connection worker。

本 adapter 把 core ``ServerDefinition`` 绑定到 iec104-python backend。名称沿用
``Iec104Server`` 以兼容现有 manager，但可按 view 中的 ``station_role`` 装配
受控站或控制站。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Protocol

from starfish.adapters.protocols.iec104.backend import Iec104Backend
from starfish.core.definitions import ServerDefinition, ServerStatus


class Iec104BackendPort(Protocol):
    """IEC104 worker 依赖的最小 backend 接口。"""

    def load_points(self, definition: ServerDefinition) -> None: ...

    def connect(self) -> None: ...

    def start(self) -> None: ...

    def stop(self) -> None: ...

    def update_point(
        self,
        point: int | str,
        value: Any,
        *,
        transmit_spontaneous: bool = True,
        quality: Any = None,
        recorded_at: datetime | None = None,
    ) -> dict[str, Any]: ...

    def point_state(self, point: int | str) -> dict[str, Any]: ...

    def execute_task(
        self,
        task: int | str,
        *,
        values: dict[int | str, Any] | None = None,
    ) -> dict[str, Any]: ...

    def health(self) -> dict[str, Any]: ...


class Iec104Server:
    """一个 IEC104 connection 对应的 Starfish worker。"""

    def __init__(
        self,
        definition: ServerDefinition,
        *,
        backend: Iec104BackendPort | None = None,
    ) -> None:
        """初始化 IEC104 server worker。

        Args:
            definition: 从 DB view 映射出的 IEC104 connection definition。
            backend: 测试可注入的 backend；未传入时创建 c104 backend。
        """
        if definition.protocol != "IEC104":
            raise ValueError(f"Iec104Server 只能接收 IEC104 definition: {definition.protocol}")
        self._definition = definition
        self._backend = backend or Iec104Backend()
        self._initialized = False
        self._started = False

    @property
    def definition(self) -> ServerDefinition:
        """返回该 worker 持有的 server definition。"""
        return self._definition

    @property
    def backend(self) -> Iec104BackendPort:
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
        if self._started:
            return
        self.init()
        self._backend.start()
        self._started = True

    def stop(self) -> None:
        """停止 IEC104 backend。"""
        try:
            self._backend.stop()
        finally:
            self._started = False

    def update_point(
        self,
        point: int | str,
        value: Any,
        *,
        transmit_spontaneous: bool = True,
        quality: Any = None,
        recorded_at: datetime | None = None,
    ) -> dict[str, Any]:
        """更新受控站数据源值，并可按 view 配置触发自发上送。"""
        self.init()
        return self._backend.update_point(
            point,
            value,
            transmit_spontaneous=transmit_spontaneous,
            quality=quality,
            recorded_at=recorded_at,
        )

    def point_state(self, point: int | str) -> dict[str, Any]:
        """读取 adapter 保存的 Point 值与发送时间状态。"""
        self.init()
        return self._backend.point_state(point)

    def execute_task(
        self,
        task: int | str,
        *,
        values: dict[int | str, Any] | None = None,
    ) -> dict[str, Any]:
        """同步执行 view 定义的主动 IEC104 task。"""
        self.start()
        return self._backend.execute_task(task, values=values)

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
