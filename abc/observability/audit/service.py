from __future__ import annotations
from collections.abc import Mapping
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Protocol
from uuid import uuid4
from ..shared import get_observation_context
from .models import AuditQuery, AuditRecord, AuditResult
class AuditStore(Protocol):
    def append(self,record:AuditRecord)->None: ...
    def query(self,query:AuditQuery)->tuple[AuditRecord,...]: ...
class AuditService:
    def __init__(self,store:AuditStore): self._store=store
    def success(self,*,operation:str,target_type:str,target_id:str|None,detail:Mapping[str,object]|None=None): return self._write(AuditResult.SUCCESS,operation,target_type,target_id,detail,None)
    def failure(self,*,operation:str,target_type:str,target_id:str|None,exception:BaseException,detail:Mapping[str,object]|None=None): return self._write(AuditResult.FAILURE,operation,target_type,target_id,detail,exception)
    def query(self,query:AuditQuery): return self._store.query(query)
    def _write(self,result,operation,target_type,target_id,detail,exception):
        ctx=get_observation_context(); record=AuditRecord(uuid4().hex,datetime.now(timezone.utc),ctx.runtime_id,ctx.node_id,ctx.request_id,ctx.actor,ctx.source or "unknown",operation,target_type,target_id,result,MappingProxyType(dict(detail or {})),type(exception).__qualname__ if exception else None,str(exception) if exception else None); self._store.append(record); return record
