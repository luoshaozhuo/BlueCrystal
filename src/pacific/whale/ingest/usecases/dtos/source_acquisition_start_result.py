# src/whale/ingest/usecases/dtos/source_acquisition_start_result.py

"""SourceAcquisitionStartResult DTO — source 采集启动结果。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class AcquisitionSession(Protocol):
    """可关闭的采集会话。"""

    async def close(self) -> None:
        """关闭采集会话。"""


@dataclass(slots=True)
class SourceAcquisitionStartResult:
    """一次 source 采集启动结果。"""

    request_id: str
    task_id: int
    mode: str
    sessions: list[AcquisitionSession]