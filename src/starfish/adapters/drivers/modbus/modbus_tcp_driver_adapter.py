"""Modbus TCP DriverPort adapter。"""

from __future__ import annotations

from starfish.adapters.drivers.backend_ports import DelegatingDriverAdapter, DriverBackend


class ModbusTcpDriverAdapter(DelegatingDriverAdapter):
    """Modbus TCP driver adapter，真实 socket server 位于 infrastructure。"""

    def __init__(self, backend: DriverBackend) -> None:
        """接收已创建的 Modbus TCP backend。"""
        super().__init__(backend)


__all__ = ["ModbusTcpDriverAdapter"]
