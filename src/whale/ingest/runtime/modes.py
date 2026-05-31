"""运行模式定义。

定义 ingest 运行时的操作模式。
"""

from __future__ import annotations

from enum import StrEnum


class RuntimeMode(StrEnum):
    """支持的 ingest 运行时模式。"""

    STANDALONE = "standalone"
    ACTIVE_STANDBY = "active_standby"
    DUAL_ACTIVE_PARTITIONED = "dual_active_partitioned"
    CLUSTER = "cluster"

    @classmethod
    def parse(cls, value: str) -> "RuntimeMode":
        """解析用户/配置提供的运行时模式。"""

        normalized = value.strip().lower()
        try:
            return cls(normalized)
        except ValueError as exc:
            raise ValueError(f"Unsupported runtime mode: {value!r}") from exc
