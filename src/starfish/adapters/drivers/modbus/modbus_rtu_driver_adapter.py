"""Modbus RTU DriverPort adapter。"""

from __future__ import annotations

from starfish.adapters.drivers.backend_ports import DelegatingDriverAdapter, DriverBackend


class ModbusRtuDriverAdapter(DelegatingDriverAdapter):
    """Modbus RTU driver adapter，PTY 生命周期位于 infrastructure。"""

    def __init__(self, backend: DriverBackend) -> None:
        """接收已创建的 Modbus RTU backend。"""
        super().__init__(backend)


__all__ = ["ModbusRtuDriverAdapter"]
