"""HTTP REST DriverPort adapter。

adapter 层只暴露 application 需要的 driver 形态；真实 HTTP 服务、
socket 健康探测和线程生命周期由 infrastructure backend 承担。
"""

from __future__ import annotations

from starfish.adapters.drivers.backend_ports import DelegatingDriverAdapter, DriverBackend


class HttpRestDriverAdapter(DelegatingDriverAdapter):
    """HTTP REST driver adapter，委托 infrastructure backend 执行物理 I/O。"""

    def __init__(self, backend: DriverBackend) -> None:
        """接收已创建的 HTTP REST backend。"""
        super().__init__(backend)


__all__ = ["HttpRestDriverAdapter"]
