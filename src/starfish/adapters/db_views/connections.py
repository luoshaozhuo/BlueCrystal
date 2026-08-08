"""Whale connection 执行视图的通用索引 loader。

本 adapter 只读取 `vw_connection_object_full` 中的 connection identity 和
protocol，用于全量枚举与协议分派。协议参数、task 和 point item 由对应协议
loader 继续加载。
"""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import bindparam, create_engine, text
from sqlalchemy.engine import Engine

from starfish.adapters.db_views.errors import DbViewLoadError


class ConnectionDbViewLoader:
    """读取 connection IDs 及其 protocol。"""

    def __init__(self, db_url: str | None = None, *, engine: Engine | None = None) -> None:
        if engine is None and not db_url:
            raise DbViewLoadError("缺少 WHALE_DB_URL，无法读取 connection view")
        self._engine = engine or create_engine(str(db_url), future=True)

    def list_connection_ids(self) -> list[int]:
        """按 connection_id 排序返回执行视图中的全部 connection。"""
        with self._engine.connect() as conn:
            rows = conn.execute(text("""
                    SELECT connection_id
                    FROM whale.vw_connection_object_full
                    ORDER BY connection_id
                    """)).mappings()
            return [int(row["connection_id"]) for row in rows]

    def load_protocols(self, connection_ids: Sequence[int]) -> dict[int, str]:
        """返回指定 connection IDs 对应的归一化 protocol。"""
        normalized_ids = list(dict.fromkeys(int(value) for value in connection_ids))
        if not normalized_ids:
            raise DbViewLoadError("connection_ids 不能为空")

        stmt = text("""
            SELECT connection_id, protocol
            FROM whale.vw_connection_object_full
            WHERE connection_id IN :connection_ids
            ORDER BY connection_id
            """).bindparams(bindparam("connection_ids", expanding=True))
        with self._engine.connect() as conn:
            rows = list(conn.execute(stmt, {"connection_ids": normalized_ids}).mappings())

        protocols = {
            int(row["connection_id"]): _normalize_protocol(row.get("protocol")) for row in rows
        }
        missing = sorted(set(normalized_ids) - protocols.keys())
        if missing:
            raise DbViewLoadError(f"未找到 connection_id: {missing}")
        empty_protocol = sorted(
            connection_id for connection_id, protocol in protocols.items() if not protocol
        )
        if empty_protocol:
            raise DbViewLoadError(f"connection protocol 为空: {empty_protocol}")
        return protocols


def _normalize_protocol(value: object) -> str:
    """把 DB protocol code 归一为 registry key。"""
    return str(value or "").strip().upper().replace("-", "_").replace(" ", "_")


__all__ = ["ConnectionDbViewLoader"]
