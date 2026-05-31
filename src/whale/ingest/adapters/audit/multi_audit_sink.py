"""可组合的审计 sink 适配器。提供多路审计事件转发和聚合错误处理。"""

from __future__ import annotations

from whale.ingest.domain.audit_event import IngestAuditEvent
from whale.ingest.ports.audit import IngestAuditSinkPort


class AuditSinkEmitError(RuntimeError):
    """聚合审计 sink 的发送失败异常。保留部分写入可见性，记录哪些 sink 成功/失败。"""

    def __init__(self, *, primary_error: Exception | None, secondary_error: Exception | None) -> None:
        """初始化审计发送异常。Args: message: 异常消息。sink_name: 失败的 sink 名称。cause: 原始异常。"""
        self.primary_error = primary_error
        self.secondary_error = secondary_error
        parts: list[str] = []
        if primary_error is not None:
            parts.append(f"primary={type(primary_error).__name__}")
        if secondary_error is not None:
            parts.append(f"secondary={type(secondary_error).__name__}")
        super().__init__("dual_audit_sink_emit_failed:" + ",".join(parts))


class DualIngestAuditSink(IngestAuditSinkPort):
    """将一条审计事件同时发送到两个 sink，支持 DB + JSONL 双写场景。"""

    def __init__(self, primary: IngestAuditSinkPort, secondary: IngestAuditSinkPort) -> None:
        """初始化双路审计 sink。Args: sinks: 审计 sink 列表，emit 时依次转发。"""
        self._primary = primary
        self._secondary = secondary
        self.last_error: AuditSinkEmitError | None = None

    def emit(self, event: IngestAuditEvent) -> None:
        """空操作 emit，不实际发送事件。"""
        primary_error: Exception | None = None
        secondary_error: Exception | None = None
        self.last_error = None

        try:
            self._primary.emit(event)
        except Exception as exc:  # pragma: no cover - exercised by integration path
            primary_error = exc

        try:
            self._secondary.emit(event)
        except Exception as exc:  # pragma: no cover - exercised by integration path
            secondary_error = exc

        if primary_error is None and secondary_error is None:
            return

        self.last_error = AuditSinkEmitError(
            primary_error=primary_error,
            secondary_error=secondary_error,
        )
        if secondary_error is not None:
            raise self.last_error
