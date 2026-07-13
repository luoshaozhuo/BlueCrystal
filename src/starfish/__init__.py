"""starfish 对外包入口。

Starfish 是 simulator runtime orchestrator。它采用 Hexagonal Architecture：
CLI 作为 inbound adapter，core manager 管理 server workers，DB view 与
IEC104 native backend 作为 outbound adapters。

硬边界：
- 不得 import `seahorse`
- 不得 import `whale.ingest`
- 不得 import `whale.shared.source`
- 当前 Python 主路径只保留 IEC104 simulator
"""

from __future__ import annotations

from starfish.core import StarfishServerManager

__all__ = ["StarfishServerManager"]
