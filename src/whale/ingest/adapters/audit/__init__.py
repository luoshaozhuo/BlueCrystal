"""Audit sink adapters."""

from whale.ingest.adapters.audit.db_audit_sink import DbIngestAuditSink
from whale.ingest.adapters.audit.http_audit_sink import HttpIngestAuditSink
from whale.ingest.adapters.audit.multi_audit_sink import AuditSinkEmitError, DualIngestAuditSink

__all__ = ["AuditSinkEmitError", "DbIngestAuditSink", "DualIngestAuditSink", "HttpIngestAuditSink"]
