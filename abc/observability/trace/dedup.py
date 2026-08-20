"""代表性错误 Trace 的 TTL 去重。"""

from threading import Lock

from cachetools import TTLCache


class ErrorTraceDeduplicator:
    """在给定 TTL 窗口内按错误指纹限制重复 Trace。"""

    def __init__(self, *, ttl_seconds: float, max_entries: int) -> None:
        self._cache: TTLCache[str, bool] = TTLCache(
            maxsize=max_entries,
            ttl=ttl_seconds,
        )
        self._lock = Lock()

    def should_trace(self, fingerprint: str) -> bool:
        """判断错误指纹是否应生成代表性 Trace。"""
        with self._lock:
            if fingerprint in self._cache:
                return False
            self._cache[fingerprint] = True
            return True
