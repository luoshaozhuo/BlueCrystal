"""starfish ServerPlan JSON 加载器。

提供从 Seahorse handoff JSON 文件加载并校验 ServerPlan 的能力。
仅依赖 JSON/dict/schema，不 import seahorse Python 模块。

安全边界：
- 不得 import seahorse。
- 不得 import whale.ingest / whale.shared.source。
- 文件 I/O 仅读取。
"""

from __future__ import annotations

from starfish.loader.server_plan_loader import load_server_plan

__all__ = ["load_server_plan"]
