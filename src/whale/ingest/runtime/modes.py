"""Runtime mode parsing for ingest nodes and schedulers."""

from __future__ import annotations

from enum import StrEnum


class RuntimeMode(StrEnum):
    """Supported ingest runtime modes."""

    STANDALONE = "standalone"
    ACTIVE_STANDBY = "active_standby"
    DUAL_ACTIVE_PARTITIONED = "dual_active_partitioned"
    CLUSTER = "cluster"

    @classmethod
    def parse(cls, value: str) -> "RuntimeMode":
        """Parse one user/config supplied runtime mode."""

        normalized = value.strip().lower()
        try:
            return cls(normalized)
        except ValueError as exc:
            raise ValueError(f"Unsupported runtime mode: {value!r}") from exc
