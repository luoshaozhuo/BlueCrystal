"""审计日志适配器。

实现 AuditSinkPort，将结构化审计事件持久化或转发。
外部依赖：数据库（SQLAlchemy）/ HTTP 客户端。
失败处理：失败不传播到调用方，记录 error 后继续。
"""

from __future__ import annotations

from collections.abc import Callable

from sqlalchemy.orm import Session, sessionmaker

from whale.ingest.domain.audit_event import IngestAuditEvent
from whale.ingest.ports.audit import IngestAuditSinkPort
from whale.shared.persistence.orm import IngestAuditEventOrm


class DbIngestAuditSink(IngestAuditSinkPort):
    """将结构化审计事件持久化到运行时数据库。"""

    def __init__(self, session_factory: sessionmaker[Session] | Callable[[], Session]) -> None:
        """初始化 DbIngestAuditSink 实例。"""
        self._session_factory = session_factory

    def emit(self, event: IngestAuditEvent) -> None:
        """初始化数据库审计 sink。Args: session_factory: 数据库会话工厂。"""
        """发送一条事件到对应 sink。"""
        payload = event.sanitized_payload()
        session = self._session_factory()
        try:
            row = IngestAuditEventOrm(
                request_id=payload["request_id"],
                actor=payload["actor"],
                action=payload["action"],
                resource_type=payload["resource_type"],
                resource_id=payload["resource_id"],
                decision=payload["decision"],
                result=payload["result"],
                reason_code=payload["reason_code"],
                http_status=payload["http_status"],
                trace_id=payload["trace_id"],
                client_ip=payload["client_ip"],
                node_id=payload["node_id"],
                before_version=payload["before_version"],
                after_version=payload["after_version"],
                changed_fields_json=list(payload["changed_fields"]),
                attributes_json=dict(payload["attributes"]),
                event_timestamp=payload["timestamp"],
            )
            session.add(row)
            session.commit()
        finally:
            session.close()
