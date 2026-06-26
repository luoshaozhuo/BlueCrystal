"""Runtime registry port。

本 port 只描述 application 层构建 RuntimeGraph 的能力边界；配置文件读取、
driver 实例化细节和 native/process 能力均由其他 port 或 adapter 提供。
"""

from __future__ import annotations

from typing import Protocol

from starfish.application.runtime import RuntimeGraph
from starfish.domain import StarfishServerConfig


class RegistryPort(Protocol):
    """RuntimeGraph 构建 port。"""

    def build_runtime_graph(self, config: StarfishServerConfig) -> RuntimeGraph:
        """根据已校验配置构建 RuntimeGraph。

        Args:
            config: 已通过加载与校验的 Starfish server 配置。

        Returns:
            nodes[] -> bindings[] -> driver_instance 结构的运行图。
        """


__all__ = ["RegistryPort"]
