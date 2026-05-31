"""状态快照发布请求 DTO。承载一次发布操作所需的源标识、时间戳等参数。"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class StateSnapshotPublishRequest:
    """请求将一次全量状态快照从缓存发布到消息队列。包含源 ID 和时间范围过滤。"""

    trace_id: str | None = None
    station_id: str | None = None
    source_id: str | None = None
    ld_name: str | None = None
    dry_run: bool = False
    max_items_per_message: int = 0
    attributes: dict[str, str] = field(default_factory=dict)
