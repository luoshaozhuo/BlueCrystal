"""IEC 101 DriverPort adapter。"""

from __future__ import annotations

from starfish.adapters.drivers.backend_ports import DelegatingDriverAdapter, DriverBackend


class Iec101DriverAdapter(DelegatingDriverAdapter):
    """IEC 101 adapter，codec/probe/backend 细节由 infrastructure 承担。"""

    def __init__(self, backend: DriverBackend) -> None:
        """接收已创建的 IEC101 backend。"""
        super().__init__(backend)


__all__ = ["Iec101DriverAdapter"]
