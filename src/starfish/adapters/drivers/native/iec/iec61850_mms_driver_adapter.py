"""IEC 61850 MMS native DriverPort adapter。"""

from __future__ import annotations

from starfish.adapters.drivers.backend_ports import DelegatingDriverAdapter, DriverBackend


class Iec61850MmsDriverAdapter(DelegatingDriverAdapter):
    """IEC 61850 MMS adapter，native runner 子进程由 infrastructure backend 管理。"""

    def __init__(self, backend: DriverBackend) -> None:
        """接收已创建的 IEC61850 MMS backend。"""
        super().__init__(backend)


__all__ = ["Iec61850MmsDriverAdapter"]
