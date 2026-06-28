"""IEC 104 native DriverPort adapter。"""

from __future__ import annotations

from starfish.adapters.drivers.backend_ports import DelegatingDriverAdapter, DriverBackend


class Iec104DriverAdapter(DelegatingDriverAdapter):
    """IEC 104 adapter，native runner 子进程由 infrastructure backend 管理。"""

    def __init__(self, backend: DriverBackend) -> None:
        """接收已创建的 IEC104 backend。"""
        super().__init__(backend)


__all__ = ["Iec104DriverAdapter"]
