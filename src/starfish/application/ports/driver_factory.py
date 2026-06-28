"""Driver factory port。

application runtime 初始化通过本 port 请求 endpoint 的 driver binding；
具体协议 dispatch、环境探测和 facade 构造属于 adapter 职责。
"""

from __future__ import annotations

from typing import Protocol

from starfish.domain import DriverEntry, StarfishEndpointConfig, StarfishServerMemberConfig


class DriverFactoryPort(Protocol):
    """endpoint driver 装配抽象。"""

    def create_driver_for_endpoint(
        self,
        server: StarfishServerMemberConfig,
        endpoint: StarfishEndpointConfig,
    ) -> DriverEntry:
        """创建单个 endpoint 的 driver entry。

        Args:
            server: endpoint 所属 server member。
            endpoint: 待装配的 endpoint 契约。

        Returns:
            包含 driver、mode 和可用性信息的 DriverEntry。
        """
