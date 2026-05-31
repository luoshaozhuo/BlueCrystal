"""Operation journal for endpoint-level runtime mutations."""

from __future__ import annotations

from dataclasses import dataclass

from tools.source_lab.access.runtime.endpoint_runtime import utc_now_iso


@dataclass(frozen=True, slots=True)
class OperationJournalEntry:
    """Endpoint 运行时操作日志条目。

    记录每次 registry 操作（ADD/UPDATE/PAUSE/RESUME/STOP/DELETE/RECOVER）的完整上下文，
    包括操作标识、决策结果、配置版本变更和影响范围。
    不可变（frozen），通过 create 工厂方法构造并自动注入时间戳。

    不负责：日志的持久化（由 RuntimeStateStore 负责）。
    """
    operation_id: str
    action: str
    endpoint_id: str
    decision: str
    result: str
    reason_code: str
    before_config_version: int | None
    after_config_version: int | None
    changed_fields: tuple[str, ...]
    affected_endpoints: tuple[str, ...]
    unaffected_endpoints: tuple[str, ...]
    timestamp: str

    def to_dict(self) -> dict[str, object]:
        return {
            "operation_id": self.operation_id,
            "action": self.action,
            "endpoint_id": self.endpoint_id,
            "decision": self.decision,
            "result": self.result,
            "reason_code": self.reason_code,
            "before_config_version": self.before_config_version,
            "after_config_version": self.after_config_version,
            "changed_fields": list(self.changed_fields),
            "affected_endpoints": list(self.affected_endpoints),
            "unaffected_endpoints": list(self.unaffected_endpoints),
            "timestamp": self.timestamp,
        }

    @classmethod
    def create(
        cls,
        *,
        operation_id: str,
        action: str,
        endpoint_id: str,
        decision: str,
        result: str,
        reason_code: str,
        before_config_version: int | None,
        after_config_version: int | None,
        changed_fields: tuple[str, ...],
        affected_endpoints: tuple[str, ...],
        unaffected_endpoints: tuple[str, ...],
    ) -> "OperationJournalEntry":
        return cls(
            operation_id=operation_id,
            action=action,
            endpoint_id=endpoint_id,
            decision=decision,
            result=result,
            reason_code=reason_code,
            before_config_version=before_config_version,
            after_config_version=after_config_version,
            changed_fields=changed_fields,
            affected_endpoints=affected_endpoints,
            unaffected_endpoints=unaffected_endpoints,
            timestamp=utc_now_iso(),
        )

