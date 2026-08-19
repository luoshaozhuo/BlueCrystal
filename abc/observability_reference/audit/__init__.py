"""BlueCrystal Reference Audit capability."""

from .decorators import audit_action, get_audit_spec
from .fastapi import install_fastapi_audit
from .instrumentation import AuditInstrumentationHooks
from .models import AuditQuery, AuditRecord, AuditResult, AuditSpec
from .ports import AuditStore
from .service import AuditPersistenceError, AuditService

__all__ = [
    "AuditInstrumentationHooks",
    "AuditPersistenceError",
    "AuditQuery",
    "AuditRecord",
    "AuditResult",
    "AuditService",
    "AuditSpec",
    "AuditStore",
    "audit_action",
    "get_audit_spec",
    "install_fastapi_audit",
]
