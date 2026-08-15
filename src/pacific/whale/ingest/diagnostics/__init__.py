"""Ingest 侧 runtime 诊断工具。

这些工具消费具备 `start/health/read` 等统一接口的 runtime driver，
用于最小可用性探测、轻量采样和容量扫描。

边界说明：
- 这是 ingest 侧的诊断/验证辅助，不属于 starfish runtime 核心。
- 这里只依赖 duck-typed driver 接口，不直接 import `starfish`。
- 不把 probe/profile/capacity 的局部结果高估为生产级验收。
"""

from pacific.whale.ingest.diagnostics.capacity import CapacityResult, capacity_scan
from pacific.whale.ingest.diagnostics.probe import ProbeResult, probe_facade
from pacific.whale.ingest.diagnostics.profile import ProfileResult, profile_facade

__all__ = [
    "CapacityResult",
    "ProfileResult",
    "ProbeResult",
    "capacity_scan",
    "probe_facade",
    "profile_facade",
]
