"""Seahorse driver adapter 层。

当前只承载与外部 driver 边界相关的适配契约（``backend_ports.py``
和 factory 占位包），不创建外部 backend 与 socket/SDK 调用。
真实 backend 与 SDK 由 ``seahorse.infrastructure.drivers`` 提供。
"""
