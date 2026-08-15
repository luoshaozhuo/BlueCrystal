"""原始时序索引层（raw_index）——TDengine 快速查询入口。

raw_index 层接收 speed layer 写入后的原始消息，建立按 source_id、device_id、
时间戳的快速查询索引。使用 TDengine 作为后端，但绝不替代 raw_archive 的长期
原始事实层存储。

本文件包含：
- RawIndexSinkPort: 原始时序索引写入端口。
- TdengineRawIndexSink: TDengine 索引 adapter（通过 REST API 实现）。
- MemoryRawIndexSink: 测试用内存索引实现。
"""

from __future__ import annotations

import json
import logging
import urllib.request
import urllib.error
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


class RawIndexSinkPort(ABC):
    """原始时序索引写入端口。

    将 Envelope 及其解析后的 node states 索引到快速查询存储中。raw_index
    是 raw_archive 的索引加速层，不保存完整消息内容，仅保存查询所需的
    索引字段：source_id、device_id、timestamp、质量码等。

    实现方责任：
    - 按时间序列高效写入索引数据。
    - 支持 source_id/device_id/timestamp 组合查询。
    - 自动过期旧数据（按 TTL 配置）。

    不负责：
    - 消息内容的完整存储（由 raw_archive 负责）。
    - 数据清洗和标准化（由 standardized 层负责）。
    """

    @abstractmethod
    async def index(self, envelope: dict[str, Any]) -> bool:
        """将一条 envelope 索引写入 raw_index。

        从 envelope 中提取 source_id、device_id、station_id、timestamp 等
        关键字段写入索引存储。

        Args:
            envelope: 消息信封的序列化字典。

        Returns:
            True 表示写入成功，False 表示重复或跳过。

        Raises:
            RuntimeError: 写入失败。
        """
        ...


class TdengineRawIndexSink(RawIndexSinkPort):
    """TDengine raw_index 写入适配器（通过 REST API 实现）。

    使用 TDengine REST API（/rest/sql）执行数据库创建、超级表创建、
    子表创建和时序数据写入。不依赖 taospy 驱动，仅使用标准库 urllib。

    在 TDengine 不可达时，adapter 降级为 environment-pending 模式，
    所有写操作返回 False 且不抛异常。

    适配器边界：
    - 通过 HTTP REST API 与 TDengine taosAdapter 通信。
    - 管理数据库和表的 DDL 初始化（CREATE DATABASE / STABLE / TABLE）。
    - 将 Envelope 的关键字段写入 raw_index 超级表。

    表结构（超级表 raw_index）：
    - ts: TIMESTAMP（主时间戳）
    - source_id: NCHAR(128)
    - message_id: NCHAR(64)
    - message_type: NCHAR(32)
    - published_at: TIMESTAMP
    - item_count: INT
    - indexed_at: TIMESTAMP
    - TAG: source_id_tag, device_id

    Attributes:
        _host: TDengine taosAdapter 主机。
        _port: taosAdapter REST 端口。
        _database: 目标数据库名。
        _super_table: 超级表名称。
        _ttl_days: 数据自动过期天数。
        _user: TDengine 用户名。
        _password: TDengine 密码。
        _initialized: 是否已完成 DDL 初始化。
        _connected: taosAdapter 是否可达。
        _error: 初始化或操作失败时的错误信息。
    """

    def __init__(
        self,
        dsn: str,
        database: str = "whale_raw_index",
        *,
        ttl_days: int = 90,
        user: str = "root",
        password: str = "taosdata",
    ) -> None:
        """初始化 TDengine raw_index adapter。

        解析 dsn 获取 host:port。DDL 初始化在首次 index 调用时延迟执行。

        Args:
            dsn: TDengine 连接字符串，支持格式：
                - taosws://host:port (WebSocket)
                - http://host:port (REST)
                - host:port (默认 HTTP)
            database: 目标数据库名。
            ttl_days: 数据自动过期天数，0 表示不过期。
            user: TDengine 用户名。
            password: TDengine 密码。

        Raises:
            ValueError: dsn 格式无效。
        """
        host, port = _parse_tdengine_dsn(dsn)
        self._host = host
        self._port = port
        self._database = database
        self._super_table = "raw_index"
        self._ttl_days = ttl_days
        self._user = user
        self._password = password
        self._initialized = False
        self._connected = False
        self._error: str | None = None
        self._config_valid = bool(dsn and database)

    def _build_url(self) -> str:
        """构造 TDengine REST API 基础 URL。

        Returns:
            REST API URL，如 http://localhost:6041/rest/sql。
        """
        return f"http://{self._host}:{self._port}/rest/sql"

    def _execute_sql(self, sql: str) -> dict[str, Any]:
        """通过 REST API 执行一条 SQL。

        使用 HTTP Basic Auth 发送 POST 请求到 /rest/sql。

        Args:
            sql: 待执行的 SQL 语句。

        Returns:
            TDengine REST API 返回的 JSON 响应。

        Raises:
            RuntimeError: HTTP 请求失败或 TDengine 返回错误。
        """
        url = self._build_url()
        data = sql.encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "text/plain"},
            method="POST",
        )
        # HTTP Basic Auth
        import base64
        auth_bytes = base64.b64encode(
            f"{self._user}:{self._password}".encode("utf-8")
        )
        req.add_header("Authorization", f"Basic {auth_bytes.decode('ascii')}")

        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                body = resp.read().decode("utf-8")
                result: dict[str, Any] = json.loads(body)
                # TDengine REST API 总是返回 HTTP 200，错误码在 JSON code 字段中
                code = result.get("code", -1)
                if code != 0:
                    desc = result.get("desc", "unknown error")
                    raise RuntimeError(
                        f"TDengine 执行失败 (code={code}): {desc} "
                        f"sql={sql[:100]}..."
                    )
                return result
        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"TDengine REST API 错误 (HTTP {exc.code}): sql={sql[:100]}... "
                f"body={error_body[:200]}"
            ) from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(
                f"TDengine 连接失败: {self._host}:{self._port} - {exc}"
            ) from exc

    def _ensure_initialized(self) -> bool:
        """确保 TDengine 数据库和超级表已创建。

        延迟初始化：首次 index 调用时执行，后续跳过。
        创建数据库（如不存在）和超级表（如不存在）。

        Returns:
            True 表示初始化成功，False 表示 TDengine 不可达。
        """
        if self._initialized:
            return self._connected
        self._initialized = True
        try:
            # 创建数据库（KEEP 至少 30 天，满足 TDengine 最小要求）
            keep_days = max(self._ttl_days, 30) if self._ttl_days > 0 else 30
            ttl_sql = f"CREATE DATABASE IF NOT EXISTS {self._database} KEEP {keep_days}"
            self._execute_sql(ttl_sql)

            # 创建超级表
            create_stable_sql = (
                f"CREATE STABLE IF NOT EXISTS {self._database}.{self._super_table} "
                f"(ts TIMESTAMP, "
                f"source_id NCHAR(128), "
                f"message_id NCHAR(64), "
                f"message_type NCHAR(32), "
                f"published_at TIMESTAMP, "
                f"item_count INT, "
                f"indexed_at TIMESTAMP) "
                f"TAGS (source_id_tag NCHAR(128), device_id NCHAR(128))"
            )
            self._execute_sql(create_stable_sql)
            self._connected = True
            logger.info(
                "TDengine raw_index 初始化完成: db=%s super_table=%s",
                self._database, self._super_table,
            )
            return True
        except Exception as exc:
            self._error = f"TDengine raw_index 初始化失败: {exc}"
            self._connected = False
            logger.warning(self._error)
            return False

    async def index(self, envelope: dict[str, Any]) -> bool:
        """将原始消息索引写入 TDengine。

        从 envelope 中提取关键字段，构造 INSERT 语句写入 raw_index 超级表。
        使用 TDengine 的自动建表语法（USING STABLE TAGS）。

        Args:
            envelope: 消息信封的序列化字典。

        Returns:
            True 表示写入成功，False 表示 TDengine 不可达或写入失败。
        """
        if not self._ensure_initialized():
            return False

        source_id = str(envelope.get("source_id", ""))
        message_id = str(envelope.get("message_id", ""))
        message_type = str(envelope.get("message_type", ""))
        published_at = str(envelope.get("published_at", ""))
        item_count = len(envelope.get("items", []))
        indexed_at = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

        # 提取 device_id
        device_id = ""
        items = envelope.get("items", [])
        if items and isinstance(items, list):
            first = items[0]
            if isinstance(first, dict):
                device_id = str(first.get("device_id", first.get("device_code", "")))

        # 子表名：按 source_id 生成
        subtable_name = f"ri_{_safe_table_name(source_id)}"

        # 自动建表 + INSERT
        try:
            sql = (
                f"INSERT INTO {self._database}.{subtable_name} "
                f"USING {self._database}.{self._super_table} "
                f"TAGS ('{_escape_sql_val(source_id)}', '{_escape_sql_val(device_id)}') "
                f"VALUES ("
                f"'{_escape_sql_val(published_at)}', "
                f"'{_escape_sql_val(source_id)}', "
                f"'{_escape_sql_val(message_id)}', "
                f"'{_escape_sql_val(message_type)}', "
                f"'{_escape_sql_val(published_at)}', "
                f"{item_count}, "
                f"'{indexed_at}'"
                f")"
            )
            self._execute_sql(sql)
            logger.debug("raw_index 写入成功: source=%s msg=%s", source_id, message_id)
            return True
        except Exception as exc:
            logger.warning("raw_index 写入失败 source=%s: %s", source_id, exc)
            return False

    async def health(self) -> bool:
        """通过 TDengine REST API 检查连接健康。

        执行 SELECT 1 验证数据库连接正常。

        Returns:
            True 表示 TDengine 可达且数据库存在。
        """
        try:
            result: dict[str, Any] = self._execute_sql("SELECT 1")
            code: int = int(result.get("code", -1))
            return code == 0
        except Exception:
            return False


class MemoryRawIndexSink(RawIndexSinkPort):
    """测试用内存 raw_index 实现。

    将所有索引记录保存在内存列表中，支持按 source_id 和 device_id 查询。

    Attributes:
        records: 按写入顺序存储的索引记录列表。
    """

    def __init__(self) -> None:
        """初始化空的内存索引存储。"""
        self.records: list[dict[str, Any]] = []

    async def index(self, envelope: dict[str, Any]) -> bool:
        """将 envelope 写入内存索引。

        提取关键字段构造索引记录并追加到 records 列表。

        Args:
            envelope: 消息信封的序列化字典。

        Returns:
            始终返回 True（内存写入不计重复）。
        """
        record = {
            "source_id": envelope.get("source_id"),
            "message_id": envelope.get("message_id"),
            "message_type": envelope.get("message_type"),
            "published_at": envelope.get("published_at"),
            "item_count": len(envelope.get("items", [])),
            "indexed_at": datetime.now(tz=timezone.utc).isoformat(),
        }
        self.records.append(record)
        return True

    def query_by_source(
        self,
        source_id: str,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> list[dict[str, Any]]:
        """按 source_id 和时间范围查询索引记录。

        测试辅助方法，用于验证写入内容。

        Args:
            source_id: 数据源标识。
            start_time: 时间范围起点（含）。
            end_time: 时间范围终点（含）。

        Returns:
            符合条件的索引记录列表。
        """
        result = [r for r in self.records if r.get("source_id") == source_id]
        if start_time:
            result = [
                r for r in result
                if r.get("published_at", "") >= start_time.isoformat()
            ]
        if end_time:
            result = [
                r for r in result
                if r.get("published_at", "") <= end_time.isoformat()
            ]
        return result


# ---- TDengine 辅助函数 ----

def _parse_tdengine_dsn(dsn: str) -> tuple[str, int]:
    """解析 TDengine DSN 连接字符串，提取 host 和 port。

    支持格式：
    - taosws://host:port → (host, port)
    - http://host:port → (host, port)
    - host:port → (host, port)

    Args:
        dsn: TDengine 连接字符串。

    Returns:
        (host, port) 元组。

    Raises:
        ValueError: dsn 格式无效或端口无法解析。
    """
    cleaned = dsn
    for prefix in ("taosws://", "http://", "https://"):
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix):]
            break
    parts = cleaned.rsplit(":", 1)
    if len(parts) == 2:
        host = parts[0]
        try:
            port = int(parts[1])
        except ValueError:
            raise ValueError(f"TDengine DSN 端口无效: {dsn}")
    else:
        host = parts[0]
        port = 6041
    if not host:
        raise ValueError(f"TDengine DSN host 为空: {dsn}")
    return host, port


def _safe_table_name(name: str) -> str:
    """将 source_id 转换为安全的 TDengine 子表名。

    TDengine 表名不允许特殊字符，将非法字符替换为下划线。

    Args:
        name: 原始名称（如 source_id）。

    Returns:
        安全的表名字符串。
    """
    import re
    return re.sub(r"[^a-zA-Z0-9_]", "_", name).strip("_") or "default_table"


def _escape_sql_val(val: str) -> str:
    """转义 SQL 字符串值中的单引号。

    用于 SQL INSERT 语句中字符串值的转义，防止 SQL 注入风险。
    注意：此函数仅做简单转义，生产环境应使用参数化查询。

    Args:
        val: 待转义的字符串值。

    Returns:
        转义后的安全字符串。
    """
    return val.replace("'", "''").replace("\\", "\\\\")
