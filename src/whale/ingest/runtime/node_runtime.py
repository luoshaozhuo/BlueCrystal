"""Node heartbeat models and persistence helpers."""

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
    """One runtime node heartbeat snapshot."""

    node_key: str
    runtime_mode: RuntimeMode
    status: str = "ALIVE"
    hostname: str | None = None
    heartbeat_at: datetime = field(default_factory=lambda: datetime.now(tz=UTC))


class NodeRuntimeRepository:
    """Persist node heartbeat state into the runtime DB."""

    def __init__(
        self,
        session_factory: sessionmaker[Session] | Callable[[], Session],
    ) -> None:
        self._session_factory = session_factory

    def upsert_heartbeat(self, heartbeat: NodeHeartbeat) -> IngestRuntimeNode:
        """Insert or update one node heartbeat row."""

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
        """Return one node row by key."""

        session = self._session_factory()
        try:
            return session.get(IngestRuntimeNode, node_key)
        finally:
            session.close()

    def list_nodes(self) -> list[IngestRuntimeNode]:
        """Return all known runtime nodes."""

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
        """Return nodes that are still considered alive."""

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
