"""DTO for state snapshot publish requests."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class StateSnapshotPublishRequest:
    """Request to publish one full state snapshot from cache to message queue.

    Fields:
        trace_id: Correlation trace id for observability.
        station_id: Optional filter — only publish sources matching this station.
        source_id: Optional filter — only publish the given source_id.
        ld_name: Optional filter — only publish the given ld_name.
        dry_run: When true, read snapshot but do not publish.
        max_items_per_message: Split snapshot into multiple messages when
            item count exceeds this threshold. 0 means no splitting.
    """

    trace_id: str | None = None
    station_id: str | None = None
    source_id: str | None = None
    ld_name: str | None = None
    dry_run: bool = False
    max_items_per_message: int = 0
    attributes: dict[str, str] = field(default_factory=dict)
