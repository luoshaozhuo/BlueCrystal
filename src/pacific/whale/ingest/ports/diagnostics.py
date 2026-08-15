"""IngestRuntimeDiagnosticsPort — 采集运行时诊断端口."""

from __future__ import annotations

from typing import Protocol


class IngestRuntimeDiagnosticsPort(Protocol):
    """对 usecase 屏蔽 ingest_source_health / ingest_runtime_event 两张表的写入细节."""

    def mark_success(
        self,
        task_id: int,
        ld_instance_id: int,
        acquisition_mode: str,
    ) -> None:
        """采集成功后更新 health：清零 consecutive_failure_count，设置 HEALTHY."""

    def record_failure(
        self,
        task_id: int,
        ld_instance_id: int,
        acquisition_mode: str,
        failure_category: str,
        error_code: str | None = None,
        error_message: str | None = None,
    ) -> None:
        """采集失败后写 runtime_event 并更新 health."""

    def record_recovered(
        self,
        task_id: int,
        ld_instance_id: int,
        acquisition_mode: str,
    ) -> None:
        """从失败恢复到成功时写 RECOVERED 事件."""

    def mark_alive(
        self,
        task_id: int,
        ld_instance_id: int,
        acquisition_mode: str,
    ) -> None:
        """更新 last_alive_at，不改变 health_status."""
