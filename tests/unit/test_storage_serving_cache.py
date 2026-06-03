"""storage serving_cache Redis 适配器单元测试。

验证 RedisServingCache 的 upsert/get、TTL、stale 检查、乱序时间戳保护
和序列化行为。使用 fakeredis 或 mock 进行隔离测试。

被验证对象：
- whale.storage.serving_cache: RedisServingCache

证据等级：L1 unit/mock（使用 unittest.mock 隔离 redis 依赖）。
redis-py 是核心依赖，在 CI 环境可用，但此处用 mock 保证纯单元级隔离。
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

import pytest

from whale.storage.serving_cache import (
    InMemoryServingCache,
    RedisServingCache,
    ServingCachePort,
)


class TestRedisServingCache:
    """RedisServingCache 单元测试（使用 mock 隔离 redis-py）。"""

    @pytest.fixture
    def mock_redis_client(self) -> AsyncMock:
        """构造 mock redis async client。"""
        client = AsyncMock()
        client.ping = AsyncMock(return_value=True)
        client.get = AsyncMock(return_value=None)
        client.setex = AsyncMock(return_value=True)
        client.delete = AsyncMock(return_value=True)
        return client

    def test_is_serving_cache_port(self) -> None:
        """验证 RedisServingCache 实现 ServingCachePort。"""
        cache = RedisServingCache(redis_url="redis://localhost:6379/0")
        assert isinstance(cache, ServingCachePort)

    def test_init_with_empty_url_raises(self) -> None:
        """验证空 redis_url 抛出 ValueError。"""
        with pytest.raises(ValueError, match="redis_url 不能为空"):
            RedisServingCache(redis_url="")

    def test_key_prefix_isolation(self) -> None:
        """验证 key_prefix 正确应用于 Redis 键。"""
        cache = RedisServingCache(
            redis_url="redis://localhost:6379/0",
            key_prefix="whale:cache:",
        )
        # 直接测试内部方法
        full_key = cache._full_key("sensor:temp")
        assert full_key == "whale:cache:sensor:temp"

    def test_full_key_without_prefix(self) -> None:
        """验证无前缀时的 key 构造。"""
        cache = RedisServingCache(
            redis_url="redis://localhost:6379/0",
            key_prefix="",
        )
        assert cache._full_key("sensor:temp") == "sensor:temp"

    @pytest.mark.asyncio
    async def test_health_ping_ok(self, mock_redis_client: AsyncMock) -> None:
        """验证 health check 在 PING 成功时返回 True。"""
        cache = RedisServingCache(redis_url="redis://localhost:6379/0")
        cache._client = mock_redis_client
        cache._connected = True

        assert await cache.health() is True
        mock_redis_client.ping.assert_called_once()

    @pytest.mark.asyncio
    async def test_health_ping_fails(self, mock_redis_client: AsyncMock) -> None:
        """验证 health check 在 PING 失败时返回 False。"""
        mock_redis_client.ping.side_effect = Exception("connection refused")
        cache = RedisServingCache(redis_url="redis://localhost:6379/0")
        cache._client = mock_redis_client
        cache._connected = True

        assert await cache.health() is False

    @pytest.mark.asyncio
    async def test_health_no_client(self) -> None:
        """验证无 client 时 health 返回 False。"""
        cache = RedisServingCache(redis_url="redis://localhost:6379/0")
        assert await cache.health() is False

    @pytest.mark.asyncio
    async def test_get_returns_parsed_json(
        self, mock_redis_client: AsyncMock
    ) -> None:
        """验证 get 正确解析 JSON 返回值（observed_at 在 stale 窗口内）。"""
        import json

        recent_time = datetime.now(tz=timezone.utc).isoformat()
        value = {"observed_at": recent_time, "value": 25.5}
        mock_redis_client.get.return_value = json.dumps(value)
        cache = RedisServingCache(redis_url="redis://localhost:6379/0")
        cache._client = mock_redis_client
        cache._connected = True

        result = await cache.get("sensor:temp")
        assert result == value

    @pytest.mark.asyncio
    async def test_get_none_for_missing_key(
        self, mock_redis_client: AsyncMock
    ) -> None:
        """验证 key 不存在时 get 返回 None。"""
        mock_redis_client.get.return_value = None
        cache = RedisServingCache(redis_url="redis://localhost:6379/0")
        cache._client = mock_redis_client
        cache._connected = True

        result = await cache.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_stale_detection(
        self, mock_redis_client: AsyncMock
    ) -> None:
        """验证 stale 检测：observed_at 过旧返回 None。"""
        import json

        old_time = (
            datetime.now(tz=timezone.utc) - timedelta(seconds=600)
        ).isoformat()
        value = {"observed_at": old_time, "value": 25.5}
        mock_redis_client.get.return_value = json.dumps(value)
        cache = RedisServingCache(
            redis_url="redis://localhost:6379/0", stale_seconds=300
        )
        cache._client = mock_redis_client
        cache._connected = True

        result = await cache.get("sensor:old")
        assert result is None  # stale

    @pytest.mark.asyncio
    async def test_set_with_ttl(
        self, mock_redis_client: AsyncMock
    ) -> None:
        """验证 set 使用 SETEX 命令设置值和 TTL。"""
        cache = RedisServingCache(
            redis_url="redis://localhost:6379/0", default_ttl_seconds=60
        )
        cache._client = mock_redis_client
        cache._connected = True

        recent_time = datetime.now(tz=timezone.utc).isoformat()
        value = {"observed_at": recent_time, "value": 30.0}
        result = await cache.set("sensor:temp", value, ttl_seconds=120)
        assert result is True
        mock_redis_client.setex.assert_called_once()
        # 检查 SETEX 调用参数
        call_args = mock_redis_client.setex.call_args
        assert call_args[0][1] == 120  # ttl_seconds

    @pytest.mark.asyncio
    async def test_set_out_of_order_rejection(
        self, mock_redis_client: AsyncMock
    ) -> None:
        """验证乱序保护：新值 observed_at 更早时拒绝写入。"""
        import json

        newer_time = datetime.now(tz=timezone.utc).isoformat()
        older_time = (
            datetime.now(tz=timezone.utc) - timedelta(seconds=10)
        ).isoformat()
        existing = {"observed_at": newer_time, "value": 25.5}
        mock_redis_client.get.return_value = json.dumps(existing)
        cache = RedisServingCache(
            redis_url="redis://localhost:6379/0", default_ttl_seconds=60
        )
        cache._client = mock_redis_client
        cache._connected = True

        # 尝试用更旧的数据覆盖
        new_value = {"observed_at": older_time, "value": 20.0}
        result = await cache.set("sensor:temp", new_value)
        assert result is False
        # SETEX 不应被调用
        mock_redis_client.setex.assert_not_called()

    @pytest.mark.asyncio
    async def test_set_no_existing_value(
        self, mock_redis_client: AsyncMock
    ) -> None:
        """验证 key 不存在时直接写入（无乱序检查）。"""
        mock_redis_client.get.return_value = None
        cache = RedisServingCache(
            redis_url="redis://localhost:6379/0", default_ttl_seconds=60
        )
        cache._client = mock_redis_client
        cache._connected = True

        recent_time = datetime.now(tz=timezone.utc).isoformat()
        value = {"observed_at": recent_time, "value": 40.0}
        result = await cache.set("sensor:new", value)
        assert result is True

    @pytest.mark.asyncio
    async def test_delete_returns_true(
        self, mock_redis_client: AsyncMock
    ) -> None:
        """验证 delete 成功返回 True。"""
        cache = RedisServingCache(redis_url="redis://localhost:6379/0")
        cache._client = mock_redis_client
        cache._connected = True

        result = await cache.delete("sensor:temp")
        assert result is True
        mock_redis_client.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_without_client_returns_false(self) -> None:
        """验证无 Redis client 时 set 返回 False。"""
        cache = RedisServingCache(redis_url="redis://localhost:6379/0")
        # 不初始化 _client
        result = await cache.set("key", {"value": 1})
        assert result is False

    @pytest.mark.asyncio
    async def test_get_without_client_returns_none(self) -> None:
        """验证无 Redis client 时 get 返回 None。"""
        cache = RedisServingCache(redis_url="redis://localhost:6379/0")
        result = await cache.get("key")
        assert result is None


class TestInMemoryServingCacheExtended:
    """InMemoryServingCache 扩展测试（补充 serving cache contract 覆盖）。"""

    @pytest.mark.asyncio
    async def test_health_always_true(self) -> None:
        """验证 InMemoryServingCache 的 health 始终返回 True。"""
        cache = InMemoryServingCache()
        assert await cache.health() is True
