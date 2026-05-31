"""可观测性适配器。

实现指标/日志/追踪等可观测性 sink。
"""

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
    """将 ingest 指标事件按每条一行 JSONL 持久化。"""

    def __init__(self, path: str | Path) -> None:
        """初始化 JsonlIngestMetricsSink 实例。"""
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def emit(self, event: IngestMetricEvent) -> None:
        """初始化 JSONL 指标 sink。Args: file_path: 输出文件路径。"""
        """发送一条事件到对应 sink。"""
        self._append(asdict(event))

    def _append(self, payload: dict[str, object]) -> None:
        with self._path.open("a", encoding="utf-8") as fh:
            fh.write(_serialize(payload))
            fh.write("\n")


class JsonlSourceCommandAuditSink(SourceCommandAuditPort):
    """将源命令审计事件按每条一行 JSONL 持久化。"""

    def __init__(self, path: str | Path) -> None:
        """初始化 JsonlSourceCommandAuditSink 实例。"""
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def emit(self, event: SourceCommandAuditEvent) -> None:
        """初始化 JSONL 命令审计 sink。Args: file_path: 输出文件路径。"""
        """发送事件到目标 sink。"""
        self._append(asdict(event))

    def _append(self, payload: dict[str, object]) -> None:
        with self._path.open("a", encoding="utf-8") as fh:
            fh.write(_serialize(payload))
            fh.write("\n")


class JsonlIngestAuditSink(IngestAuditSinkPort):
    """将 ingest 审计事件按 JSONL 行持久化。"""

    def __init__(self, path: str | Path) -> None:
        """初始化 JsonlIngestAuditSink 实例。"""
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def emit(self, event: IngestAuditEvent) -> None:
        """初始化 JSONL 审计 sink。Args: file_path: 输出文件路径。"""
        """发送事件到目标 sink。"""
        self._append(event.sanitized_payload())

    def _append(self, payload: dict[str, object]) -> None:
        with self._path.open("a", encoding="utf-8") as fh:
            fh.write(_serialize(payload))
            fh.write("\n")
