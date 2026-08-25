"""验证 SQLite 审计存储在内存数据库中的跨操作持久化契约。"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from observability.audit import AuditQuery, AuditRecord, AuditResult, SQLiteAuditStore


def test_file_database_persists_initialized_schema_and_records(tmp_path: Path) -> None:
    """文件 SQLite store 应支持初始化、写入和查询这一完整最小生命周期。"""
    store = SQLiteAuditStore(tmp_path / "audit.sqlite3")
    record = AuditRecord(
        audit_id="audit-1",
        timestamp=datetime(2026, 8, 24, tzinfo=timezone.utc),
        service_name="observability-test",
        service_instance_id="node-1",
        request_id="request-1",
        actor="operator",
        source="http",
        operation="task.run",
        target_type="task",
        target_id="task-1",
        result=AuditResult.SUCCESS,
        detail={"attempt": 1},
    )

    store.append(record)

    assert store.query(AuditQuery(operation="task.run")) == (record,)
