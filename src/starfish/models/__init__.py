"""starfish 最小数据模型。

本包镜像 Seahorse ServerPlan JSON 契约，不 import seahorse Python 类型。
所有模型为纯 @dataclass，可用于 JSON 反序列化后的内存操作。

安全边界：
- 不得 import seahorse。
- 不得 import whale.ingest。
- 不得 import whale.shared.source。
"""

from __future__ import annotations

from starfish.models.plan import (
    StarfishServerPlan,
    StarfishEndpointPlan,
    StarfishPointPlan,
    LoadResult,
    ValidationResult,
    UnsupportedOperation,
)

__all__ = [
    "StarfishServerPlan",
    "StarfishEndpointPlan",
    "StarfishPointPlan",
    "LoadResult",
    "ValidationResult",
    "UnsupportedOperation",
]
