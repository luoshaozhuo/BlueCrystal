"""Starfish application ports。

ports 定义 application 层依赖的抽象边界，具体文件 I/O、协议 driver
创建和 runtime 实现均由 adapters 或 infrastructure 提供。
"""

from __future__ import annotations

from starfish.application.ports.config_loader import ConfigLoaderPort
from starfish.application.ports.driver_factory import DriverFactoryPort
from starfish.application.ports.driver_port import DriverPort
from starfish.application.ports.registry import RegistryPort

__all__ = ["ConfigLoaderPort", "DriverFactoryPort", "DriverPort", "RegistryPort"]
