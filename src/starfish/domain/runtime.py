"""starfish 运行时领域抽象。

本模块定义对 application 层稳定可见的运行时抽象，包括驱动协议和
注册表条目。具体协议实现留在 `starfish.drivers`。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

from starfish.domain.server_plan import StarfishEndpointPlan, StarfishServerPlan


@runtime_checkable
class RuntimeDriver(Protocol):
    """协议运行时驱动统一接口。"""

    def load_points(self, plan: StarfishServerPlan) -> None:
        """加载运行所需的计划数据。"""

    def start(self) -> None:
        """启动驱动。"""

    def stop(self) -> None:
        """停止驱动。"""

    def health(self) -> dict[str, Any]:
        """返回驱动健康状态。"""

    def read(self, point_ids: list[str] | None = None) -> dict[str, Any]:
        """读取点位值。"""

    def write(self, point_id: str, value: Any) -> None:
        """写入单点值。"""

    def capabilities(self) -> list[str]:
        """返回驱动能力声明。"""


@dataclass
class DriverEntry:
    """单个 endpoint 的驱动装配结果。"""

    endpoint: StarfishEndpointPlan
    driver: RuntimeDriver | Any = None
    available: bool = True
    reason: str = ""
    mode: str = "stub"


__all__ = ["RuntimeDriver", "DriverEntry"]
