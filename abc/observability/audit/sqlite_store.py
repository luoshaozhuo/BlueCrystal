from __future__ import annotations
import json, sqlite3
from datetime import datetime
from pathlib import Path
from types import MappingProxyType
from .models import AuditQuery, AuditRecord, AuditResult
class SQLiteAuditStore:
    def __init__(self,path:str|Path): self._path=str(path); self._initialize()
    def append(self,r:AuditRecord)->None:
        with sqlite3.connect(self._path) as c:
            c.execute("INSERT INTO audit_record VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(r.audit_id,r.timestamp.isoformat(),r.runtime_id,r.node_id,r.request_id,r.actor,r.source,r.operation,r.target_type,r.target_id,r.result.value,json.dumps(dict(r.detail),ensure_ascii=False,default=repr),r.error_type,r.error_message)); c.commit()
    def query(self,q:AuditQuery)->tuple[AuditRecord,...]:
        clauses=[]; params=[]
        for col,val in (("operation",q.operation),("target_type",q.target_type),("target_id",q.target_id),("actor",q.actor),("result",q.result.value if q.result else None)):
            if val is not None: clauses.append(f"{col}=?"); params.append(val)
        where=" WHERE "+" AND ".join(clauses) if clauses else ""; params.append(max(1,q.limit))
        with sqlite3.connect(self._path) as c: rows=c.execute(f"SELECT * FROM audit_record{where} ORDER BY timestamp DESC LIMIT ?",params).fetchall()
        return tuple(AuditRecord(row[0],datetime.fromisoformat(row[1]),row[2],row[3],row[4],row[5],row[6],row[7],row[8],row[9],AuditResult(row[10]),MappingProxyType(json.loads(row[11])),row[12],row[13]) for row in rows)
    def _initialize(self):
        with sqlite3.connect(self._path) as c:
            c.execute("CREATE TABLE IF NOT EXISTS audit_record (audit_id TEXT PRIMARY KEY,timestamp TEXT NOT NULL,runtime_id TEXT,node_id TEXT,request_id TEXT,actor TEXT,source TEXT NOT NULL,operation TEXT NOT NULL,target_type TEXT NOT NULL,target_id TEXT,result TEXT NOT NULL,detail_json TEXT NOT NULL,error_type TEXT,error_message TEXT)"); c.commit()
