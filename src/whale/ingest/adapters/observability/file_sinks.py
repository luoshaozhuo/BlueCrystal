"""Lightweight JSONL sinks for ingest metrics and audit."""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from whale.ingest.domain.audit_event import IngestAuditEvent
from whale.ingest.ports.audit import IngestAuditSinkPort
from whale.ingest.ports.command.source_command_audit_port import (
    SourceCommandAuditEvent,
    SourceCommandAuditPort,
)
from whale.ingest.ports.metrics import IngestMetricEvent, IngestMetricsPort


def _serialize(payload: dict[str, object]) -> str:
    normalized: dict[str, object] = {}
    for key, value in payload.items():
        if isinstance(value, datetime):
            normalized[key] = value.isoformat()
        else:
            normalized[key] = value
    return json.dumps(normalized, ensure_ascii=False, separators=(",", ":"))


class JsonlIngestMetricsSink(IngestMetricsPort):
    """Persist ingest metric events as one JSONL line per event."""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def emit(self, event: IngestMetricEvent) -> None:
        self._append(asdict(event))

    def _append(self, payload: dict[str, object]) -> None:
        with self._path.open("a", encoding="utf-8") as fh:
            fh.write(_serialize(payload))
            fh.write("\n")


class JsonlSourceCommandAuditSink(SourceCommandAuditPort):
    """Persist source command audit events as one JSONL line per event."""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def emit(self, event: SourceCommandAuditEvent) -> None:
        self._append(asdict(event))

    def _append(self, payload: dict[str, object]) -> None:
        with self._path.open("a", encoding="utf-8") as fh:
            fh.write(_serialize(payload))
            fh.write("\n")


class JsonlIngestAuditSink(IngestAuditSinkPort):
    """Persist ingest audit events as JSONL lines."""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def emit(self, event: IngestAuditEvent) -> None:
        self._append(event.sanitized_payload())

    def _append(self, payload: dict[str, object]) -> None:
        with self._path.open("a", encoding="utf-8") as fh:
            fh.write(_serialize(payload))
            fh.write("\n")
