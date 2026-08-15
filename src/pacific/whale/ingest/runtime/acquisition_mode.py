"""采集模式定义。

定义支持的采集模式（polling/subscription/report 等）。
"""

from __future__ import annotations

from enum import StrEnum


class AcquisitionMode(StrEnum):
    """支持的采集模式枚举。定义 polling、subscription 等采集方式的常量和元数据。"""

    ONCE = "ONCE"
    POLLING = "POLLING"
    SUBSCRIPTION = "SUBSCRIPTION"
