"""节点运行时管理。

管理 ingest 节点的生命周期、心跳和状态上报。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Callable

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from whale.shared.persistence.orm import IngestRuntimeNode

from whale.ingest.runtime.modes import RuntimeMode


@dataclass(slots=True)
class NodeHeartbeat:
    """单个运行时节点心跳快照。"""

    node_key: str
    runtime_mode: RuntimeMode
    status: str = "ALIVE"
    hostname: str | None = None
    heartbeat_at: datetime = field(default_factory=lambda: datetime.now(tz=UTC))


class NodeRuntimeRepository:
    """持久化节点心跳状态到运行时数据库。"""

    def __init__(
        self,
        session_factory: sessionmaker[Session] | Callable[[], Session],
    ) -> None:
        """初始化节点运行时仓库。Args: session_factory: 数据库会话工厂。"""
        self._session_factory = session_factory

    def upsert_heartbeat(self, heartbeat: NodeHeartbeat) -> IngestRuntimeNode:
        """插入或更新一条节点心跳记录。"""

        session = self._session_factory()
        try:
            row = session.get(IngestRuntimeNode, heartbeat.node_key)
            if row is None:
                row = IngestRuntimeNode(
                    node_key=heartbeat.node_key,
                    runtime_mode=heartbeat.runtime_mode.value,
                    status=heartbeat.status,
                    hostname=heartbeat.hostname,
                    heartbeat_at=heartbeat.heartbeat_at,
                    last_seen_at=heartbeat.heartbeat_at,
                )
                session.add(row)
            else:
                row.runtime_mode = heartbeat.runtime_mode.value
                row.status = heartbeat.status
                row.hostname = heartbeat.hostname
                row.heartbeat_at = heartbeat.heartbeat_at
                row.last_seen_at = heartbeat.heartbeat_at
            session.commit()
            session.refresh(row)
            return row
        finally:
            session.close()

    def get(self, node_key: str) -> IngestRuntimeNode | None:
        """按键返回单行节点记录。"""

        session = self._session_factory()
        try:
            return session.get(IngestRuntimeNode, node_key)
        finally:
            session.close()

    def list_nodes(self) -> list[IngestRuntimeNode]:
        """返回所有已知的运行时节点。"""

        session = self._session_factory()
        try:
            return list(
                session.scalars(
                    select(IngestRuntimeNode).order_by(IngestRuntimeNode.node_key)
                )
            )
        finally:
            session.close()

    def list_alive_nodes(
        self,
        *,
        now: datetime,
        heartbeat_timeout_seconds: int,
    ) -> list[IngestRuntimeNode]:
        """返回仍视为存活的节点列表。"""

        threshold = now.timestamp() - heartbeat_timeout_seconds
        alive: list[IngestRuntimeNode] = []
        for row in self.list_nodes():
            last_seen = row.last_seen_at
            last_seen_utc = (
                last_seen.replace(tzinfo=UTC)
                if last_seen.tzinfo is None
                else last_seen.astimezone(UTC)
            )
            if last_seen_utc.timestamp() >= threshold and row.status == "ALIVE":
                alive.append(row)
        return alive
