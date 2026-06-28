"""In-memory simulator DriverPort adapter。"""

from __future__ import annotations

from starfish.adapters.drivers.backend_ports import DelegatingDriverAdapter, DriverBackend


class ServerSimulatorDriverAdapter(DelegatingDriverAdapter):
    """未知协议 fallback adapter，真实 in-memory backend 由组合根注入。"""

    def __init__(self, backend: DriverBackend) -> None:
        """接收已创建的 in-memory simulator backend。"""
        super().__init__(backend)


__all__ = ["ServerSimulatorDriverAdapter"]
