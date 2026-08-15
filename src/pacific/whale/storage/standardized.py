"""标准时序层（standardized）——TDengine 清洗后数据存储。

standardized 层接收 speed layer 清洗、标准化、质量处理后的时序数据，
使用 TDengine 作为后端存储，支撑后续 warehouse/mart 层的聚合和分析。

本文件包含：
- StandardizedTimeSeriesSinkPort: 标准时序写入端口。
- TdengineStandardizedSink: TDengine 标准层 adapter（通过 REST API 实现）。
- MemoryStandardizedSink: 测试用内存标准层实现。
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


class StandardizedTimeSeriesSinkPort(ABC):
    """标准时序数据写入端口。

    将经过清洗、标准化和质量处理的时序数据写入持久化存储。每条数据包含
    schema_version 和质量码，支持时间基准对齐。

    实现方责任：
    - 按 node/variable 维度高效写入时序数据。
    - 维护 schema_version 和血缘追踪。
    - 支持质量码过滤和查询。

    不负责：
    - 原始消息的保存（由 raw_archive 负责）。
    - 数据清洗逻辑本身（由 speed layer 负责）。
    """

    @abstractmethod
    async def write(self, node_states: list[dict[str, Any]]) -> int:
        """写入一批标准化 node state 数据。

        每条 node state 包含：node_key、variable_key、value、quality_code、
        schema_version、observed_at、received_at。

        Args:
            node_states: 标准化后的节点状态列表。

        Returns:
            成功写入的记录数。

        Raises:
            RuntimeError: 写入失败。
        """
        ...


class TdengineStandardizedSink(StandardizedTimeSeriesSinkPort):
    """TDengine 标准化层写入适配器（通过 REST API 实现）。

    使用 TDengine REST API 将经过清洗和标准化的时序数据写入 TDengine。
    字段包含 schema_version、quality_code、source_id、device_id、node_key、
    timestamp 和 value。支持 write、readback 和 health check。

    在 TDengine 不可达时，adapter 降级为 environment-pending 模式，
    所有写操作返回 0 且不抛异常。

    适配器边界：
    - 通过 HTTP REST API 与 TDengine taosAdapter 通信。
    - 管理数据库和超级表的 DDL 初始化。
    - 批量写入标准化 node state 数据。

    表结构（超级表 standardized）：
    - ts: TIMESTAMP（主时间戳，使用 observed_at）
    - node_key: NCHAR(128)
    - variable_key: NCHAR(128)
    - value: NCHAR(256)
    - value_type: NCHAR(32)
    - quality_code: NCHAR(8)
    - schema_version: NCHAR(16)
    - source_id: NCHAR(128)
    - message_id: NCHAR(64)
    - observed_at: TIMESTAMP
    - received_at: TIMESTAMP
    - TAG: node_key_tag, variable_key_tag, source_id_tag

    Attributes:
        _host: TDengine taosAdapter 主机。
        _port: taosAdapter REST 端口。
        _database: 目标数据库名。
        _super_table: 超级表名称。
        _ttl_days: 数据保留天数。
        _user: TDengine 用户名。
        _password: TDengine 密码。
        _initialized: 是否已完成 DDL 初始化。
        _connected: taosAdapter 是否可达。
        _error: 初始化或操作失败时的错误信息。
    """

    def __init__(
        self,
        dsn: str,
        database: str = "whale_standardized",
        *,
        ttl_days: int = 365,
        user: str = "root",
        password: str = "taosdata",
    ) -> None:
        """初始化 TDengine standardized adapter。

        解析 dsn 获取 host:port。DDL 初始化在首次 write 时延迟执行。

        Args:
            dsn: TDengine 连接字符串。
            database: 目标数据库名。
            ttl_days: 数据保留天数，标准层默认保留更久。
            user: TDengine 用户名。
            password: TDengine 密码。

        Raises:
            ValueError: dsn 格式无效。
        """
        from pacific.whale.storage.raw_index import _parse_tdengine_dsn

        host, port = _parse_tdengine_dsn(dsn)
        self._host = host
        self._port = port
        self._database = database
        self._super_table = "standardized"
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
            REST API URL。
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
        import base64

        url = self._build_url()
        data = sql.encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "text/plain"},
            method="POST",
        )
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
                f"node_key NCHAR(128), "
                f"variable_key NCHAR(128), "
                f"`value` NCHAR(256), "
                f"value_type NCHAR(32), "
                f"quality_code NCHAR(8), "
                f"schema_version NCHAR(16), "
                f"source_id NCHAR(128), "
                f"message_id NCHAR(64), "
                f"observed_at TIMESTAMP, "
                f"received_at TIMESTAMP) "
                f"TAGS (node_key_tag NCHAR(128), variable_key_tag NCHAR(128), "
                f"source_id_tag NCHAR(128))"
            )
            self._execute_sql(create_stable_sql)
            self._connected = True
            logger.info(
                "TDengine standardized 初始化完成: db=%s super_table=%s",
                self._database, self._super_table,
            )
            return True
        except Exception as exc:
            self._error = f"TDengine standardized 初始化失败: {exc}"
            self._connected = False
            logger.warning(self._error)
            return False

    async def write(self, node_states: list[dict[str, Any]]) -> int:
        """将标准化 node state 批量写入 TDengine。

        对每条 state 构造 INSERT ... USING STABLE TAGS 语句，
        写入标准化超级表。TDengine 不可达时返回 0。

        Args:
            node_states: 标准化后的节点状态列表，每条包含：
                node_key, variable_key, value, quality_code, schema_version,
                source_id, observed_at, received_at。

        Returns:
            成功写入的记录数。
        """
        if not node_states:
            return 0
        if not self._ensure_initialized():
            return 0

        from pacific.whale.storage.raw_index import _escape_sql_val, _safe_table_name

        written = 0
        for state in node_states:
            try:
                node_key = str(state.get("node_key", ""))
                variable_key = str(state.get("variable_key", ""))
                value = str(state.get("value", ""))
                value_type = str(state.get("value_type", ""))
                quality_code = str(state.get("quality_code", "0"))
                schema_version = str(state.get("schema_version", "1.0"))
                source_id = str(state.get("source_id", ""))
                message_id = str(state.get("message_id", ""))
                observed_at = str(state.get("observed_at", ""))
                received_at = str(state.get("received_at", ""))

                # 子表名：按 node_key 生成
                subtable_name = f"std_{_safe_table_name(node_key)}"

                sql = (
                    f"INSERT INTO {self._database}.{subtable_name} "
                    f"USING {self._database}.{self._super_table} "
                    f"TAGS ("
                    f"'{_escape_sql_val(node_key)}', "
                    f"'{_escape_sql_val(variable_key)}', "
                    f"'{_escape_sql_val(source_id)}'"
                    f") VALUES ("
                    f"'{_escape_sql_val(observed_at)}', "
                    f"'{_escape_sql_val(node_key)}', "
                    f"'{_escape_sql_val(variable_key)}', "
                    f"'{_escape_sql_val(value)}', "
                    f"'{_escape_sql_val(value_type)}', "
                    f"'{_escape_sql_val(quality_code)}', "
                    f"'{_escape_sql_val(schema_version)}', "
                    f"'{_escape_sql_val(source_id)}', "
                    f"'{_escape_sql_val(message_id)}', "
                    f"'{_escape_sql_val(observed_at)}', "
                    f"'{_escape_sql_val(received_at)}'"
                    f")"
                )
                self._execute_sql(sql)
                written += 1
            except Exception as exc:
                logger.warning(
                    "standardized 写入失败 node=%s var=%s: %s",
                    state.get("node_key"), state.get("variable_key"), exc,
                )
        return written

    async def readback(
        self,
        node_key: str,
        variable_key: str | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """从 TDengine 读取标准层数据。

        用于验证写入结果和诊断查询。

        Args:
            node_key: 节点标识。
            variable_key: 变量标识，None 表示不按变量过滤。
            limit: 返回记录数上限。

        Returns:
            符合条件的标准化记录列表。
        """
        if not self._ensure_initialized():
            return []
        try:
            from pacific.whale.storage.raw_index import _safe_table_name

            subtable_name = f"std_{_safe_table_name(node_key)}"
            sql = (
                f"SELECT * FROM {self._database}.{subtable_name} "
                f"ORDER BY ts DESC LIMIT {limit}"
            )
            result = self._execute_sql(sql)
            # 解析 TDengine REST API 返回的 column_meta + data 格式
            # V3 API: column_meta 是 [["name","type",length], ...] 格式
            data_rows = result.get("data", [])
            col_meta = result.get("column_meta", [])
            col_names: list[str] = []
            for col in col_meta:
                if isinstance(col, list):
                    col_names.append(str(col[0]) if col else f"col_{len(col_names)}")
                elif isinstance(col, dict):
                    col_names.append(str(col.get("name", f"col_{len(col_names)}")))
                else:
                    col_names.append(f"col_{len(col_names)}")
            rows = []
            for row in data_rows:
                record: dict[str, Any] = {}
                for i, col_name in enumerate(col_names):
                    record[col_name] = row[i] if i < len(row) else None
                if variable_key is None or record.get("variable_key") == variable_key:
                    rows.append(record)
            return rows
        except Exception as exc:
            logger.warning("standardized readback 失败 node=%s: %s", node_key, exc)
            return []

    async def health(self) -> bool:
        """通过 TDengine REST API 检查连接健康。

        Returns:
            True 表示 TDengine 可达。
        """
        try:
            result: dict[str, Any] = self._execute_sql("SELECT 1")
            code: int = int(result.get("code", -1))
            return code == 0
        except Exception:
            return False


class MemoryStandardizedSink(StandardizedTimeSeriesSinkPort):
    """测试用内存标准层实现。

    将所有标准化 node state 记录保存在内存列表中，支持按 node_key 和
    variable_key 查询。

    Attributes:
        states: 按写入顺序存储的标准化状态记录列表。
    """

    def __init__(self) -> None:
        """初始化空的内存标准层存储。"""
        self.states: list[dict[str, Any]] = []

    async def write(self, node_states: list[dict[str, Any]]) -> int:
        """将一批标准化 node state 写入内存。

        每条 state 追加到 states 列表并记录写入时间。

        Args:
            node_states: 标准化后的节点状态列表。

        Returns:
            写入的记录数。
        """
        written = 0
        for state in node_states:
            record = dict(state)
            record["_written_at"] = datetime.now(tz=timezone.utc).isoformat()
            self.states.append(record)
            written += 1
        return written

    def query_by_node(
        self,
        node_key: str,
        variable_key: str | None = None,
    ) -> list[dict[str, Any]]:
        """按 node_key 和 variable_key 查询标准化状态。

        测试辅助方法。

        Args:
            node_key: 节点标识。
            variable_key: 变量标识，None 表示按 node 全量查询。

        Returns:
            符合条件的标准化状态记录列表。
        """
        result = [s for s in self.states if s.get("node_key") == node_key]
        if variable_key:
            result = [s for s in result if s.get("variable_key") == variable_key]
        return result
