"""Seahorse 数据源基础设施。

本包提供内存 DataSource runtime adapter。它只实现本地取值能力，不连接
Starfish、不读取 Whale DB，也不启动真实 scheduler executor。
"""

from seahorse.infrastructure.data_sources.runtime import InMemoryDataSourceRuntime

__all__ = ["InMemoryDataSourceRuntime"]
