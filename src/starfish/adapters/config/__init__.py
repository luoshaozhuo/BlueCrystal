"""Starfish config adapter 入口。"""

from __future__ import annotations

from starfish.adapters.config.server_config_loader import (
    ServerConfigJsonLoader,
    load_server_config,
)

__all__ = ["ServerConfigJsonLoader", "load_server_config"]
