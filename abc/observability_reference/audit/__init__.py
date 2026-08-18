"""BlueCrystal Audit capability."""

from ...deploy.observability_reference.audit.context import (
    AuditContext,
    bind_audit_context,
    get_audit_context,
)
from ...deploy.observability_reference.audit.decorators import (
    audit_action,
    get_audit_spec,
)
from ...deploy.observability_reference.audit.fastapi import (
    ActorResolver,
    default_actor_resolver,
    install_fastapi_audit,
)
from .models import (
    AuditQuery,
    AuditRecord,
    AuditResult,
    AuditSpec,
)
from .ports import AuditStore
from .service import (
    AuditPersistenceError,
    AuditService,
)

__all__ = [
    "ActorResolver",
    "AuditContext",
    "AuditPersistenceError",
    "AuditQuery",
    "AuditRecord",
    "AuditResult",
    "AuditService",
    "AuditSpec",
    "AuditStore",
    "audit_action",
    "bind_audit_context",
    "default_actor_resolver",
    "get_audit_context",
    "get_audit_spec",
    "install_fastapi_audit",
]
