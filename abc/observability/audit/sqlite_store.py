"""基于 SQLite 的审计记录存储实现。"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from types import MappingProxyType
from contextlib import closing

from .models import AuditQuery, AuditRecord, AuditResult


class SQLiteAuditStore:
    """将审计记录持久化到本地 SQLite 数据库。"""

    def __init__(self, path: str | Path) -> None:
        """创建 SQLite store，并确保父目录及表结构存在。"""
        resolved = Path(path)
        if resolved != Path(":memory:"):
            resolved.parent.mkdir(parents=True, exist_ok=True)
        self._path = str(resolved)
        self._initialize()

    def append(self, record: AuditRecord) -> None:
        """追加一条审计记录。

        Args:
            record: 待持久化的审计记录。
        """
        values = (
            record.audit_id,
            record.timestamp.isoformat(),
            record.service_name,
            record.service_instance_id,
            record.request_id,
            record.actor,
            record.source,
            record.operation,
            record.target_type,
            record.target_id,
            record.result.value,
            json.dumps(
                dict(record.detail),
                ensure_ascii=False,
                default=repr,
            ),
            record.error_type,
            record.error_message,
        )
        with closing(sqlite3.connect(self._path)) as connection:
            connection.execute(
                "INSERT INTO audit_record VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                values,
            )
            connection.commit()

    def query(self, query: AuditQuery) -> tuple[AuditRecord, ...]:
        """按条件查询审计记录。

        Args:
            query: 查询条件。

        Returns:
            按时间倒序排列的审计记录。
        """
        clauses: list[str] = []
        params: list[object] = []
        filters = (
            ("operation", query.operation),
            ("target_type", query.target_type),
            ("target_id", query.target_id),
            ("actor", query.actor),
            ("result", query.result.value if query.result else None),
        )
        for column, value in filters:
            if value is not None:
                clauses.append(f"{column}=?")
                params.append(value)

        where_clause = " WHERE " + " AND ".join(clauses) if clauses else ""
        params.append(max(1, query.limit))
        statement = (
            f"SELECT * FROM audit_record{where_clause} "
            "ORDER BY timestamp DESC LIMIT ?"
        )

        with closing(sqlite3.connect(self._path)) as connection:
            rows = connection.execute(statement, params).fetchall()

        return tuple(self._row_to_record(row) for row in rows)

    def _initialize(self) -> None:
        with closing(sqlite3.connect(self._path)) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_record (
                    audit_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    service_name TEXT,
                    service_instance_id TEXT,
                    request_id TEXT,
                    actor TEXT,
                    source TEXT NOT NULL,
                    operation TEXT NOT NULL,
                    target_type TEXT NOT NULL,
                    target_id TEXT,
                    result TEXT NOT NULL,
                    detail_json TEXT NOT NULL,
                    error_type TEXT,
                    error_message TEXT
                )
                """
            )
            connection.commit()

    @staticmethod
    def _row_to_record(row: tuple[object, ...]) -> AuditRecord:
        return AuditRecord(
            audit_id=str(row[0]),
            timestamp=datetime.fromisoformat(str(row[1])),
            service_name=None if row[2] is None else str(row[2]),
            service_instance_id=None if row[3] is None else str(row[3]),
            request_id=None if row[4] is None else str(row[4]),
            actor=None if row[5] is None else str(row[5]),
            source=str(row[6]),
            operation=str(row[7]),
            target_type=str(row[8]),
            target_id=None if row[9] is None else str(row[9]),
            result=AuditResult(str(row[10])),
            detail=MappingProxyType(json.loads(str(row[11]))),
            error_type=None if row[12] is None else str(row[12]),
            error_message=None if row[13] is None else str(row[13]),
        )
