"""starfish 工具层 —— probe / profile / capacity。

提供对 facade 和 ServerPlan 的轻量诊断能力：
- probe:  最小启动-健康-读取探测，输出 PASS/FAIL/NOT_RUN + reason。
- profile: 对 read 执行 N 次采样，输出耗时统计（count/min/max/avg）。
- capacity: 对 endpoint_count / point_count / read_count 做轻量扫描。

所有工具输出必须包含 protocol、mode、scenario_id 或 endpoint_id，
不替代生产级性能测试或容量规划。

安全边界：
- 不得 import seahorse / whale.ingest / whale.shared.source。
- 不依赖外部二进制。
- 仅基于 Python 标准库。
"""

from __future__ import annotations

from starfish.tools.probe import ProbeResult, probe_facade
from starfish.tools.profile import ProfileResult, profile_facade
from starfish.tools.capacity import CapacityResult, capacity_scan

__all__ = [
    "ProbeResult",
    "probe_facade",
    "ProfileResult",
    "profile_facade",
    "CapacityResult",
    "capacity_scan",
]
