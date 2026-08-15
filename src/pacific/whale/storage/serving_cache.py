"""业务侧近实时 serving cache 层。

serving cache 提供低延迟的实时数据查询服务，支撑近实时监视和业务查询。
speed layer 实时更新 serving cache，保证数据的新鲜度和乱序保护。

本文件包含：
- ServingCachePort: serving cache 读写端口。
- InMemoryServingCache: 测试用内存实现。
- RedisServingCache: 真实 Redis 适配器，使用 redis-py 实现 KV 缓存。
"""

from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from typing import Any

logger = logging.getLogger(__name__)


class ServingCachePort(ABC):
    """业务侧 serving cache 读写端口。

    支撑近实时监视和业务查询的低延迟 KV cache。speed layer 实时更新，
    支持 TTL、stale 检测和乱序保护。

    实现方责任：
    - 按业务 key 高效读写。
    - 管理 TTL 和 stale 语义。
    - 支持按 source/device/node 维度更新。

    不负责：
    - 长期历史数据查询（由 warehouse/mart 负责）。
    """

    @abstractmethod
    async def get(self, key: str) -> dict[str, Any] | None:
        """按 key 读取缓存值。

        Args:
            key: 缓存键。

        Returns:
            缓存值，不存在或已过期返回 None。
        """
        ...

    @abstractmethod
    async def set(
        self,
        key: str,
        value: dict[str, Any],
        ttl_seconds: int | None = None,
    ) -> bool:
        """设置缓存值。

        如果 key 已存在，检查 timestamp 做乱序保护：仅当新值的 observed_at
        不早于已有值时更新。

        Args:
            key: 缓存键。
            value: 缓存值字典。
            ttl_seconds: TTL 秒数，None 表示使用默认值。

        Returns:
            True 表示写入成功，False 表示被乱序保护拒绝。
        """
        ...

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """删除缓存条目。

        Args:
            key: 缓存键。

        Returns:
            True 表示删除成功。
        """
        ...

    @abstractmethod
    async def health(self) -> bool:
        """检查缓存后端健康状态。

        Returns:
            True 表示健康可用。
        """
        ...


class InMemoryServingCache(ServingCachePort):
    """测试用内存 serving cache 实现。

    所有缓存条目保存在内存 dict 中，支持 TTL 过期和乱序保护。

    Attributes:
        _store: key 到缓存条目（含 value、expires_at）的映射。
        _default_ttl: 默认 TTL 秒数。
    """

    def __init__(self, default_ttl_seconds: int = 60) -> None:
        """初始化内存 serving cache。

        Args:
            default_ttl_seconds: 默认 TTL（秒）。
        """
        self._store: dict[str, dict[str, Any]] = {}
        """缓存存储：key -> {value, expires_at}。"""
        self._default_ttl = default_ttl_seconds
        """默认 TTL 秒数。"""

    async def get(self, key: str) -> dict[str, Any] | None:
        """从内存缓存读取值，自动清除过期条目。

        Args:
            key: 缓存键。

        Returns:
            缓存值，不存在或已过期返回 None。
        """
        entry = self._store.get(key)
        if entry is None:
            return None
        expires_at = entry.get("_expires_at")
        if expires_at:
            try:
                exp = datetime.fromisoformat(str(expires_at))
                if datetime.now(tz=timezone.utc) >= exp:
                    del self._store[key]
                    return None
            except (ValueError, TypeError):
                pass
        return dict(entry.get("value", {}))

    async def set(
        self,
        key: str,
        value: dict[str, Any],
        ttl_seconds: int | None = None,
    ) -> bool:
        """设置缓存值，含乱序保护。

        检查新值的 observed_at 是否不早于已有值的 observed_at，
        如果是更旧的数据则拒绝写入。

        Args:
            key: 缓存键。
            value: 缓存值字典。
            ttl_seconds: TTL 秒数。

        Returns:
            True 表示写入或覆盖成功，False 表示乱序拒绝。
        """
        # 乱序保护：只有更新的 observed_at 才覆盖
        existing = self._store.get(key)
        if existing:
            existing_obs = existing.get("value", {}).get("observed_at")
            new_obs = value.get("observed_at")
            if existing_obs and new_obs:
                try:
                    exist_ts = datetime.fromisoformat(str(existing_obs))
                    new_ts = datetime.fromisoformat(str(new_obs))
                    if new_ts < exist_ts:
                        return False
                except (ValueError, TypeError):
                    pass

        ttl = ttl_seconds if ttl_seconds is not None else self._default_ttl
        expires_at = datetime.now(tz=timezone.utc) + timedelta(seconds=ttl)
        self._store[key] = {
            "value": dict(value),
            "_expires_at": expires_at.isoformat(),
        }
        return True

    async def delete(self, key: str) -> bool:
        """删除缓存条目。

        Args:
            key: 缓存键。

        Returns:
            True 表示删除成功（key 不存在也返回 True）。
        """
        self._store.pop(key, None)
        return True

    async def health(self) -> bool:
        """内存缓存始终健康。

        Returns:
            始终返回 True。
        """
        return True

    def size(self) -> int:
        """返回当前缓存条目数。

        测试辅助方法。

        Returns:
            未过期的缓存条目数量。
        """
        return len(self._store)


class RedisServingCache(ServingCachePort):
    """真实 Redis serving cache 适配器。

    使用 redis-py 实现 KV 缓存，支持 TTL、stale 检测和乱序时间戳保护。
    缓存值序列化为 JSON 存储，键使用可配置前缀隔离不同环境。

    适配器边界：
    - 封装 redis-py 的 SET/GET/DEL 操作。
    - 在 SET 时内嵌乱序保护逻辑（通过 Lua 脚本或两次调用）。
    - 不负责业务语义校验和缓存预热。

    Attributes:
        _client: redis-py async client 实例。
        _key_prefix: 缓存键前缀，用于环境隔离。
        _default_ttl: 默认 TTL 秒数。
        _stale_seconds: stale 判定阈值，observed_at 早于此阈值时认为 stale。
        _connected: 是否成功连接 Redis。
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        *,
        key_prefix: str = "whale:cache:",
        default_ttl_seconds: int = 60,
        stale_seconds: int = 300,
    ) -> None:
        """初始化 Redis serving cache 适配器。

        校验 redis_url 非空，延迟创建 Redis 连接（首次操作时连接）。

        Args:
            redis_url: Redis 连接 URL，格式为 redis://host:port/db。
            key_prefix: 缓存键前缀，所有 key 前加此前缀实现命名空间隔离。
            default_ttl_seconds: 默认 TTL（秒），无显式 TTL 时使用。
            stale_seconds: stale 判定阈值（秒），observed_at 早于当前时间
                超过此值时认为数据已过期。

        Raises:
            ValueError: redis_url 为空或格式无效。
        """
        if not redis_url:
            raise ValueError("redis_url 不能为空")
        self._redis_url = redis_url
        self._key_prefix = key_prefix
        self._default_ttl = default_ttl_seconds
        self._stale_seconds = stale_seconds
        self._client: Any = None
        self._connected = False
        self._error: str | None = None

    def _ensure_client(self) -> Any:
        """确保 Redis client 已初始化。

        延迟导入 redis 模块并创建异步 client。如果 redis 模块不可用或连接失败，
        记录错误并返回 None。

        Returns:
            redis async client 实例，不可用时返回 None。
        """
        if self._client is not None:
            return self._client
        try:
            import redis.asyncio as aioredis  # type: ignore[import-untyped]

            self._client = aioredis.from_url(
                self._redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
            )
            self._connected = True
            logger.info("Redis serving cache 连接成功: %s", self._redis_url)
            return self._client
        except ImportError:
            self._error = "redis-py 未安装，Redis serving cache 不可用"
            logger.warning(self._error)
        except Exception as exc:
            self._error = f"Redis 连接失败: {exc}"
            logger.warning(self._error)
        self._connected = False
        return None

    def _full_key(self, key: str) -> str:
        """构造带前缀的完整 Redis 键。

        Args:
            key: 业务缓存键。

        Returns:
            加前缀后的完整 Redis 键。
        """
        return f"{self._key_prefix}{key}"

    async def get(self, key: str) -> dict[str, Any] | None:
        """从 Redis 读取缓存值，含 stale 检测。

        如果缓存值的 observed_at 早于当前时间超过 stale_seconds，
        视为 stale 数据，返回 None 标记无效。

        Args:
            key: 缓存键。

        Returns:
            缓存值字典，不存在、已过期或 stale 时返回 None。
        """
        client = self._ensure_client()
        if client is None:
            return None
        try:
            full_key = self._full_key(key)
            raw = await client.get(full_key)
            if raw is None:
                return None
            value: dict[str, Any] = json.loads(raw)
            # stale 检测：observed_at 过旧视为无效
            observed_at = value.get("observed_at")
            if observed_at:
                try:
                    obs = datetime.fromisoformat(str(observed_at))
                    cutoff = datetime.now(tz=timezone.utc) - timedelta(
                        seconds=self._stale_seconds
                    )
                    if obs < cutoff:
                        logger.debug("缓存 key=%s 已 stale: observed_at=%s", key, observed_at)
                        return None
                except (ValueError, TypeError):
                    pass
            return value
        except (json.JSONDecodeError, TypeError) as exc:
            logger.warning("Redis 缓存值反序列化失败 key=%s: %s", key, exc)
            return None
        except Exception as exc:
            logger.error("Redis GET 失败 key=%s: %s", key, exc)
            return None

    async def set(
        self,
        key: str,
        value: dict[str, Any],
        ttl_seconds: int | None = None,
    ) -> bool:
        """设置 Redis 缓存值，含乱序时间戳保护。

        先 GET 已有值比较 observed_at，仅当新值不早于已有值时 SET。
        使用 SETEX 命令同时设置值和 TTL。

        Args:
            key: 缓存键。
            value: 缓存值字典，应包含 observed_at 字段用于乱序保护。
            ttl_seconds: TTL 秒数，None 使用默认值。

        Returns:
            True 表示写入成功，False 表示被乱序保护拒绝或写入失败。
        """
        client = self._ensure_client()
        if client is None:
            return False
        try:
            full_key = self._full_key(key)
            # 乱序保护：检查已有值的 observed_at
            existing_raw = await client.get(full_key)
            if existing_raw is not None:
                try:
                    existing: dict[str, Any] = json.loads(existing_raw)
                    existing_obs = existing.get("observed_at")
                    new_obs = value.get("observed_at")
                    if existing_obs and new_obs:
                        exist_ts = datetime.fromisoformat(str(existing_obs))
                        new_ts = datetime.fromisoformat(str(new_obs))
                        if new_ts < exist_ts:
                            logger.debug(
                                "乱序保护拒绝 key=%s: new_obs=%s < exist_obs=%s",
                                key, new_obs, existing_obs,
                            )
                            return False
                except (json.JSONDecodeError, ValueError, TypeError):
                    # 已有值解析失败时，允许覆盖
                    pass

            ttl = ttl_seconds if ttl_seconds is not None else self._default_ttl
            payload = json.dumps(value, ensure_ascii=False, default=str)
            await client.setex(full_key, ttl, payload)
            return True
        except Exception as exc:
            logger.error("Redis SET 失败 key=%s: %s", key, exc)
            return False

    async def delete(self, key: str) -> bool:
        """从 Redis 删除缓存条目。

        Args:
            key: 缓存键。

        Returns:
            True 表示删除成功（含 key 不存在的情况）。
        """
        client = self._ensure_client()
        if client is None:
            return False
        try:
            full_key = self._full_key(key)
            await client.delete(full_key)
            return True
        except Exception as exc:
            logger.error("Redis DEL 失败 key=%s: %s", key, exc)
            return False

    async def health(self) -> bool:
        """通过 PING 命令检查 Redis 连接健康。

        Returns:
            True 表示 Redis 可达并 PONG 响应正常。
        """
        client = self._ensure_client()
        if client is None:
            return False
        try:
            result = await client.ping()
            return result is True
        except Exception as exc:
            logger.warning("Redis health check 失败: %s", exc)
            return False

    async def close(self) -> None:
        """关闭 Redis 连接。

        安全关闭 client 连接，释放连接池资源。
        """
        if self._client is not None:
            try:
                await self._client.aclose()
            except Exception as exc:
                logger.warning("Redis 连接关闭失败: %s", exc)
            finally:
                self._client = None
                self._connected = False
