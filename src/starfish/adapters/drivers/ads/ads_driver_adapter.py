"""Beckhoff ADS DriverPort adapter。"""

from __future__ import annotations

from starfish.adapters.drivers.backend_ports import DelegatingDriverAdapter, DriverBackend


class AdsDriverAdapter(DelegatingDriverAdapter):
    """ADS adapter，runtime/binary/environment 探测由 infrastructure 承担。"""

    def __init__(self, backend: DriverBackend) -> None:
        """接收已创建的 ADS backend。"""
        super().__init__(backend)


__all__ = ["AdsDriverAdapter"]
