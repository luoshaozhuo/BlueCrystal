"""审计 sink 适配器。提供审计事件的持久化和转发实现（数据库、HTTP、多路）。"""

from pacific.whale.ingest.adapters.audit.db_audit_sink import DbIngestAuditSink
from pacific.whale.ingest.adapters.audit.http_audit_sink import HttpIngestAuditSink
from pacific.whale.ingest.adapters.audit.multi_audit_sink import AuditSinkEmitError, DualIngestAuditSink

__all__ = ["AuditSinkEmitError", "DbIngestAuditSink", "DualIngestAuditSink", "HttpIngestAuditSink"]
