from threading import Lock
from cachetools import TTLCache
class ErrorTraceDeduplicator:
    def __init__(self,*,ttl_seconds:float,max_entries:int):
        self._cache:TTLCache[str,bool]=TTLCache(maxsize=max_entries,ttl=ttl_seconds); self._lock=Lock()
    def should_trace(self,fingerprint:str)->bool:
        with self._lock:
            if fingerprint in self._cache: return False
            self._cache[fingerprint]=True; return True
