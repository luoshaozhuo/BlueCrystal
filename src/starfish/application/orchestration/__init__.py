"""Starfish application orchestration 入口。

orchestration 分组保存配置到 manager/runtime graph 的装配编排，不承载
driver I/O 执行逻辑，也不实现协议或 native 细节。
"""

from __future__ import annotations

from starfish.application.orchestration.registry import (
    RuntimeRegistry,
    ServerRegistry,
    create_server_registry,
)
from starfish.application.orchestration.service import (
    BuiltManager,
    LoadedConfig,
    ServerManagerBuildError,
    StarfishServerManagerService,
)

__all__ = [
    "BuiltManager",
    "LoadedConfig",
    "RuntimeRegistry",
    "ServerManagerBuildError",
    "ServerRegistry",
    "StarfishServerManagerService",
    "create_server_registry",
]
