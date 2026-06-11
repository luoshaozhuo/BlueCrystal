"""starfish 对外 API 入口。

本层为 CLI、未来脚本调用或其他高层消费者提供统一入口，
避免外部直接耦合 loader 与 registry 的底层装配细节。
"""

from __future__ import annotations

from starfish.api.runtime_api import (
    StarfishRuntime,
    StarfishRuntimeApi,
    create_default_runtime_api,
)

__all__ = ["StarfishRuntime", "StarfishRuntimeApi", "create_default_runtime_api"]
