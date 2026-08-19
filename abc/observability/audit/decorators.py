from __future__ import annotations
from collections.abc import Callable
from typing import Any, TypeVar, cast
from .models import AuditSpec
F=TypeVar("F",bound=Callable[...,Any]); _ATTR="__bluecrystal_audit_spec__"
def audit_action(*,operation:str,target_type:str,target_arg:str|None=None,detail_args:tuple[str,...]=()):
    spec=AuditSpec(operation.strip(),target_type.strip(),target_arg,detail_args)
    if not spec.operation or not spec.target_type: raise ValueError("operation and target_type must not be empty")
    def decorator(func:F)->F: setattr(func,_ATTR,spec); return func
    return decorator
def get_audit_spec(func:Callable[...,Any])->AuditSpec|None:
    value=getattr(func,_ATTR,None); return None if value is None else cast(AuditSpec,value)
