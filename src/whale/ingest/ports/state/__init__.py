"""端口接口定义。

定义调用方契约和实现方责任，相关功能。
"""

from whale.ingest.ports.state.source_state_cache_port import (
    SourceStateCacheError,
    SourceStateCachePort,
    SourceStateCacheWriteError,
)
from whale.ingest.ports.state.source_state_snapshot_reader_port import (
    SourceStateSnapshotReaderPort,
)

__all__ = [
    "SourceStateCacheError",
    "SourceStateCachePort",
    "SourceStateSnapshotReaderPort",
    "SourceStateCacheWriteError",
]
