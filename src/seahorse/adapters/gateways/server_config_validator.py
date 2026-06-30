"""seahorse ServerConfig 契约校验入口。"""
from __future__ import annotations

from seahorse.adapters.gateways.server_plan_validator import (
    validate_server_config,
    validate_server_config_from_dict,
)

__all__ = [
    "validate_server_config",
    "validate_server_config_from_dict",
]
