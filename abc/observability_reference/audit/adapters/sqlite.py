"""SQLite Audit Store."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from threading import RLock
from types import MappingProxyType

from ..models import (
    AuditQuery,
    AuditRecord,
    AuditResult,
)


_SCHEMA = """
CREATE TABLE IF NOT EXISTS audit_record (
    audit_id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    runtime_id TEXT,
    node_id TEXT,
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
);

CREATE INDEX IF NOT EXISTS idx_audit_timestamp
    ON audit_record(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_request_id
    ON audit_record(request_id);
CREATE INDEX IF NOT EXISTS idx_audit_actor
    ON audit_record(actor);
CREATE INDEX IF NOT EXISTS idx_audit_target
    ON audit_record(target_type, target_id);
CREATE INDEX IF NOT EXISTS idx_audit_operation
    ON audit_record(operation);
"""


class SQLiteAuditStore:
    """本地 SQLite 审计持久化 Adapter."""

    def __init__(
        self,
        path: str | Path,
    ) -> None:
        self._path = Path(path)
        self._path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        self._lock = RLock()
        self._connection = sqlite3.connect(
            self._path,
            check_same_thread=False,
        )
        self._connection.row_factory = (
            sqlite3.Row
        )
        self._closed = False

        with self._lock:
            self._connection.execute(
                "PRAGMA journal_mode=WAL"
            )
            self._connection.execute(
                "PRAGMA synchronous=NORMAL"
            )
            self._connection.executescript(
                _SCHEMA
            )
            self._connection.commit()

    @property
    def path(self) -> Path:
        return self._path

    def append(
        self,
        record: AuditRecord,
    ) -> None:
        with self._lock:
            self._ensure_open()
            self._connection.execute(
                """
                INSERT INTO audit_record (
                    audit_id,
                    timestamp,
                    runtime_id,
                    node_id,
                    request_id,
                    actor,
                    source,
                    operation,
                    target_type,
                    target_id,
                    result,
                    detail_json,
                    error_type,
                    error_message
                )
                VALUES (
                    ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?, ?
                )
                """,
                (
                    record.audit_id,
                    record.timestamp.isoformat(),
                    record.runtime_id,
                    record.node_id,
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
                        separators=(",", ":"),
                    ),
                    record.error_type,
                    record.error_message,
                ),
            )
            self._connection.commit()

    def query(
        self,
        query: AuditQuery,
    ) -> tuple[AuditRecord, ...]:
        limit = int(query.limit)

        if limit <= 0 or limit > 1000:
            raise ValueError(
                "audit query limit must be "
                "between 1 and 1000"
            )

        where: list[str] = []
        params: list[object] = []

        if query.start_time is not None:
            where.append("timestamp >= ?")
            params.append(
                query.start_time.isoformat()
            )

        if query.end_time is not None:
            where.append("timestamp <= ?")
            params.append(
                query.end_time.isoformat()
            )

        if query.actor is not None:
            where.append("actor = ?")
            params.append(query.actor)

        if query.source is not None:
            where.append("source = ?")
            params.append(query.source)

        if query.operation is not None:
            where.append("operation = ?")
            params.append(query.operation)

        if query.target_type is not None:
            where.append("target_type = ?")
            params.append(query.target_type)

        if query.target_id is not None:
            where.append("target_id = ?")
            params.append(query.target_id)

        if query.result is not None:
            where.append("result = ?")
            params.append(
                query.result.value
            )

        if query.request_id is not None:
            where.append("request_id = ?")
            params.append(query.request_id)

        sql = "SELECT * FROM audit_record"

        if where:
            sql += (
                " WHERE "
                + " AND ".join(where)
            )

        sql += (
            " ORDER BY timestamp DESC "
            "LIMIT ?"
        )
        params.append(limit)

        with self._lock:
            self._ensure_open()
            rows = self._connection.execute(
                sql,
                params,
            ).fetchall()

        return tuple(
            _record_from_row(row)
            for row in rows
        )

    def flush(self) -> None:
        with self._lock:
            self._ensure_open()
            self._connection.commit()

    def close(self) -> None:
        with self._lock:
            if self._closed:
                return

            self._connection.commit()
            self._connection.close()
            self._closed = True

    def _ensure_open(self) -> None:
        if self._closed:
            raise RuntimeError(
                "SQLiteAuditStore is closed"
            )


def _record_from_row(
    row: sqlite3.Row,
) -> AuditRecord:
    detail = json.loads(
        row["detail_json"]
    )

    return AuditRecord(
        audit_id=row["audit_id"],
        timestamp=datetime.fromisoformat(
            row["timestamp"]
        ),
        runtime_id=row["runtime_id"],
        node_id=row["node_id"],
        request_id=row["request_id"],
        actor=row["actor"],
        source=row["source"],
        operation=row["operation"],
        target_type=row["target_type"],
        target_id=row["target_id"],
        result=AuditResult(
            row["result"]
        ),
        detail=MappingProxyType(detail),
        error_type=row["error_type"],
        error_message=row["error_message"],
    )
