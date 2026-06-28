"""IEC 61850 SV DriverPort adapter。"""

from __future__ import annotations

from starfish.adapters.drivers.backend_ports import DelegatingDriverAdapter, DriverBackend


class SvDriverAdapter(DelegatingDriverAdapter):
    """SV adapter，环境探测与 native runner 路径由 infrastructure 承担。"""

    def __init__(self, backend: DriverBackend) -> None:
        """接收已创建的 SV backend。"""
        super().__init__(backend)


__all__ = ["SvDriverAdapter"]
