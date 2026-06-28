"""OPC UA native DriverPort adapter。"""

from __future__ import annotations

from starfish.adapters.drivers.backend_ports import DelegatingDriverAdapter, DriverBackend


class OpcUaDriverAdapter(DelegatingDriverAdapter):
    """OPC UA adapter，native runner 子进程由 infrastructure backend 管理。"""

    def __init__(self, backend: DriverBackend) -> None:
        """接收已创建的 OPC UA backend。"""
        super().__init__(backend)


__all__ = ["OpcUaDriverAdapter"]
