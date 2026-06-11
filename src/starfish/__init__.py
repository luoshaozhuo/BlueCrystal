"""starfish 对外包入口。

starfish 是多协议 simulator/runtime 核心。
它读取 Seahorse 导出的 `starfish_server_plan.json`，
装配协议驱动，并对外暴露统一的 `StarfishRuntime`。

当前正式分层只有：
- `api`
- `application`
- `domain`
- `drivers`
- `native`
- `protocols`

明确不再放在 `starfish` 内部的能力：
- `probe`
- `profile`
- `capacity`

上述诊断工具已迁移到 `whale.ingest.diagnostics`，因为它们属于
“消费 runtime 的外部工具”，而不是 runtime 核心职责。

硬边界：
- 不得 import `seahorse`
- 不得 import `whale.ingest`
- 不得 import `whale.shared.source`
- 所有运行数据均为 `synthetic`
"""

from __future__ import annotations

from starfish.api import StarfishRuntime, StarfishRuntimeApi, create_default_runtime_api

__all__ = ["StarfishRuntime", "StarfishRuntimeApi", "create_default_runtime_api"]
