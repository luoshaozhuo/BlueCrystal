"""状态缓存适配器。

实现 SourceStateCachePort，管理采集状态的缓存读写。
外部依赖：Redis。
"""

from pacific.whale.ingest.adapters.state.redis_source_state_cache import (
    RedisSourceStateCache,
    RedisSourceStateCacheSettings,
)

__all__ = ["RedisSourceStateCache", "RedisSourceStateCacheSettings"]
