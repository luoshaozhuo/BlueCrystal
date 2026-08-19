from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from types import MappingProxyType
from typing import Mapping
class AuditResult(StrEnum): SUCCESS="success"; FAILURE="failure"
@dataclass(frozen=True, slots=True)
class AuditRecord:
    audit_id:str; timestamp:datetime; runtime_id:str|None; node_id:str|None; request_id:str|None; actor:str|None; source:str; operation:str; target_type:str; target_id:str|None; result:AuditResult
    detail:Mapping[str,object]=field(default_factory=lambda:MappingProxyType({})); error_type:str|None=None; error_message:str|None=None
@dataclass(frozen=True, slots=True)
class AuditQuery:
    operation:str|None=None; target_type:str|None=None; target_id:str|None=None; actor:str|None=None; result:AuditResult|None=None; limit:int=100
@dataclass(frozen=True, slots=True)
class AuditSpec:
    operation:str; target_type:str; target_arg:str|None=None; detail_args:tuple[str,...]=()
