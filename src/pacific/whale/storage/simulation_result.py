"""仿真结果时序存储端口与适配器。

定义仿真结果时序数据的写入和读取端口，以及内存和 TDengine 后端实现。
仿真时序结果区别于标准化波形，用于表达仿真模型运行输出的时序数据。

本文件包含：
- SimulationResultTimeSeriesSinkPort: 仿真结果时序写入/读取抽象端口。
- InMemorySimulationResultTimeSeriesSink: 测试用内存实现（P1 开发期验证）。
- TdengineSimulationResultTimeSeriesSink: TDengine 真实 adapter（P5 准生产依赖验证期）。

TDengine adapter 通过 REST API 与 taosAdapter 通信，使用 urllib 标准库，
不依赖 taos-py 驱动。TDengine 不可达时 write_result_series() 返回 False、
read_result_series() 返回空列表，不抛异常。

环境变量：
- WHALE_TDENGINE_DSN: TDengine 连接字符串（优先）。
- TAOS_DSN: 备选连接字符串。
- WHALE_TDENGINE_REST_PATH: REST API 路径（默认 /rest/sql），例如 /rest/sqlt。
- 均未设置时默认 localhost:6041。

不负责：
- 仿真引擎调度和执行（由 Dolphin/simulation engine 负责）。
- 结果文件的归档（由 raw_archive 层负责）。
"""

from __future__ import annotations

import json
import logging
import os
import urllib.request
import urllib.error
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


class SimulationResultTimeSeriesSinkPort(ABC):
    """仿真结果时序数据存储端口。

    将仿真运行产生的时间序列数据写入持久化存储，并支持按 result_code
    和通道名称读取。

    实现方责任：
    - 按 result_code 维度高效写入时序数据。
    - 保留 channel_name / unit / value_type 等元数据。
    - 支持按 result_code 和时间范围查询验证。

    不负责：
    - 仿真引擎调度和执行（由 Dolphin/simulation engine 负责）。
    - 结果文件的归档（由 raw_archive 层负责）。
    """

    @abstractmethod
    async def write_result_series(
        self,
        result_code: str,
        channel_name: str,
        timestamps: list[str],
        values: list[float],
        *,
        unit: str = "",
        value_type: str = "FLOAT64",
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        """写入一条仿真结果时序数据。

        Args:
            result_code: 仿真结果编码。
            channel_name: 通道名称（如 generator_speed_rpm）。
            timestamps: 各时间点的 UTC ISO 时间戳列表。
            values: 各时间点的值列表（与 timestamps 对齐）。
            unit: 物理单位。
            value_type: 值类型。
            metadata: 扩展元数据。

        Returns:
            True 表示写入成功。

        Raises:
            RuntimeError: 写入失败时由实现决定是否抛异常。
        """
        ...

    @abstractmethod
    async def read_result_series(
        self,
        result_code: str,
        channel_name: str,
        start_time: str | None = None,
        end_time: str | None = None,
    ) -> list[dict[str, Any]]:
        """读取仿真结果时序数据。

        按 result_code、channel_name 和可选时间范围查询。

        Args:
            result_code: 仿真结果编码。
            channel_name: 通道名称。
            start_time: 查询起始时间（ISO 格式），None 表示不限。
            end_time: 查询结束时间（ISO 格式），None 表示不限。

        Returns:
            符合条件的数据点列表，每项包含 timestamp、value 等字段。
        """
        ...


class InMemorySimulationResultTimeSeriesSink(SimulationResultTimeSeriesSinkPort):
    """测试用内存仿真结果时序存储实现。

    将所有时序记录保存在内存列表中，支持按 result_code / channel_name 查询。

    Attributes:
        _records: 按写入顺序存储的时序数据点列表。
    """

    def __init__(self) -> None:
        """初始化空的内存时序存储。"""
        self._records: list[dict[str, Any]] = []

    async def write_result_series(
        self,
        result_code: str,
        channel_name: str,
        timestamps: list[str],
        values: list[float],
        *,
        unit: str = "",
        value_type: str = "FLOAT64",
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        """将仿真结果时序数据点写入内存。

        每个时间点生成一条独立记录。

        Args:
            result_code: 仿真结果编码。
            channel_name: 通道名称。
            timestamps: 时间戳列表。
            values: 值列表。
            unit: 物理单位。
            value_type: 值类型。
            metadata: 扩展元数据。

        Returns:
            True。
        """
        for ts, val in zip(timestamps, values):
            record: dict[str, Any] = {
                "result_code": result_code,
                "channel_name": channel_name,
                "timestamp": ts,
                "value": val,
                "unit": unit,
                "value_type": value_type,
                "metadata": dict(metadata) if metadata else {},
                "_written_at": datetime.now(tz=timezone.utc).isoformat(),
            }
            self._records.append(record)
        return True

    async def read_result_series(
        self,
        result_code: str,
        channel_name: str,
        start_time: str | None = None,
        end_time: str | None = None,
    ) -> list[dict[str, Any]]:
        """按 result_code、channel_name 和时间范围查询时序数据。

        Args:
            result_code: 仿真结果编码。
            channel_name: 通道名称。
            start_time: 查询起始时间（ISO 格式）。
            end_time: 查询结束时间（ISO 格式）。

        Returns:
            符合条件的数据点列表，按时间戳排序。
        """
        result: list[dict[str, Any]] = [
            r for r in self._records
            if r["result_code"] == result_code and r["channel_name"] == channel_name
        ]
        if start_time is not None:
            result = [r for r in result if r["timestamp"] >= start_time]
        if end_time is not None:
            result = [r for r in result if r["timestamp"] <= end_time]
        return sorted(result, key=lambda r: r["timestamp"])

    def clear(self) -> None:
        """清空所有已存储的时序记录。"""
        self._records.clear()


class TdengineSimulationResultTimeSeriesSink(SimulationResultTimeSeriesSinkPort):
    """TDengine 仿真结果时序存储 adapter（真实 REST API 实现）。

    通过 TDengine REST API（/rest/sql）执行数据库创建、超级表创建、
    子表创建和仿真结果时序数据写入。使用标准库 urllib，不依赖 taos-py 驱动。

    TDengine 不可达时，adapter 降级为 environment-pending 模式：
    - write_result_series() 返回 False 且不抛异常。
    - read_result_series() 返回空列表且不抛异常。

    超级表 schema（super table sim_result）：
    - ts: TIMESTAMP（仿真时间点）
    - result_code: NCHAR(128)
    - metric_key: NCHAR(128)（即 channel_name）
    - value: NCHAR(256)
    - metadata_json: NCHAR(4096)
    - TAG: result_code_tag NCHAR(128)

    DSN 解析优先级：
    1. 显式传入的 dsn 参数。
    2. 环境变量 WHALE_TDENGINE_DSN。
    3. 环境变量 TAOS_DSN。
    4. 默认值 localhost:6041。

    REST API 路径优先级：
    1. 显式传入的 rest_path 参数。
    2. 环境变量 WHALE_TDENGINE_REST_PATH。
    3. 默认值 /rest/sql。

    Attributes:
        _host: TDengine taosAdapter 主机。
        _port: taosAdapter REST 端口。
        _database: 目标数据库名。
        _super_table: 超级表名称。
        _user: TDengine 用户名。
        _password: TDengine 密码。
        _rest_path: REST API 路径（如 /rest/sql 或 /rest/sqlt）。
        _initialized: 是否已完成 DDL 初始化。
        _connected: taosAdapter 是否可达。
        _config_valid: 配置是否通过校验。
    """

    def __init__(
        self,
        dsn: str | None = None,
        database: str = "whale_sim_result",
        *,
        user: str = "root",
        password: str = "taosdata",
        rest_path: str | None = None,
    ) -> None:
        """初始化 TDengine 仿真结果存储 adapter。

        校验 dsn 格式。DSN 优先使用显式参数，其次读取环境变量。
        DDL 初始化延迟到首次写入。

        Args:
            dsn: TDengine 连接字符串（host:port 格式）。None 时从环境变量读取。
            database: 目标数据库名。
            user: TDengine 用户名。
            password: TDengine 密码。
            rest_path: REST API 路径（如 /rest/sql 或 /rest/sqlt）。
                None 时从环境变量 WHALE_TDENGINE_REST_PATH 读取，
                仍为空时默认 /rest/sql。

        Raises:
            不抛异常。无效 DSN 时 _config_valid 为 False，所有操作安全返回。
        """
        from pacific.whale.storage.raw_index import _parse_tdengine_dsn

        actual_dsn = dsn
        if actual_dsn is None:
            actual_dsn = (
                os.getenv("WHALE_TDENGINE_DSN")
                or os.getenv("TAOS_DSN")
                or "localhost:6041"
            )
        actual_rest_path = rest_path
        if actual_rest_path is None:
            actual_rest_path = os.getenv("WHALE_TDENGINE_REST_PATH", "")
        if not actual_rest_path:
            actual_rest_path = "/rest/sql"
        self._database = database
        self._super_table = "sim_result"
        self._user = user
        self._password = password
        self._rest_path = actual_rest_path
        self._initialized = False
        self._connected = False
        self._config_valid = False
        self._error: str | None = None
        try:
            host, port = _parse_tdengine_dsn(str(actual_dsn))
            self._host = host
            self._port = port
            self._config_valid = bool(self._host)
        except (ValueError, AttributeError):
            self._host = ""
            self._port = 6041
            self._error = f"TDengine DSN 解析失败: {actual_dsn}"
            logger.warning(self._error)

    def _build_url(self) -> str:
        """构造 TDengine REST API 基础 URL。

        Returns:
            REST API URL，如 http://localhost:6041/rest/sql。
        """
        return f"http://{self._host}:{self._port}{self._rest_path}"

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

        延迟初始化：首次调用时执行，后续跳过。
        创建数据库（如不存在）和 sim_result 超级表（如不存在）。

        Returns:
            True 表示初始化成功，False 表示 TDengine 不可达。
        """
        if self._initialized:
            return self._connected
        self._initialized = True
        if not self._config_valid:
            self._connected = False
            return False
        try:
            # 创建数据库（KEEP 至少 30 天）
            ttl_sql = f"CREATE DATABASE IF NOT EXISTS {self._database} KEEP 30"
            self._execute_sql(ttl_sql)

            # 创建 sim_result 超级表
            create_stable_sql = (
                f"CREATE STABLE IF NOT EXISTS {self._database}.{self._super_table} "
                f"(ts TIMESTAMP, "
                f"result_code NCHAR(128), "
                f"metric_key NCHAR(128), "
                f"`value` NCHAR(256), "
                f"metadata_json NCHAR(4096)) "
                f"TAGS (result_code_tag NCHAR(128))"
            )
            self._execute_sql(create_stable_sql)
            self._connected = True
            logger.info(
                "TDengine simulation_result 初始化完成: db=%s super_table=%s",
                self._database, self._super_table,
            )
            return True
        except Exception as exc:
            self._error = f"TDengine simulation_result 初始化失败: {exc}"
            self._connected = False
            logger.warning(self._error)
            return False

    async def write_result_series(
        self,
        result_code: str,
        channel_name: str,
        timestamps: list[str],
        values: list[float],
        *,
        unit: str = "",
        value_type: str = "FLOAT64",
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        """将仿真结果时序数据批量写入 TDengine。

        每个时间点生成一条独立记录，使用 TDengine 自动建表语法写入。

        Args:
            result_code: 仿真结果编码。
            channel_name: 通道名称（如 generator_speed_rpm）。
            timestamps: 各时间点的 UTC ISO 时间戳列表。
            values: 各时间点的值列表（与 timestamps 对齐）。
            unit: 物理单位（暂存于 metadata_json）。
            value_type: 值类型（暂存于 metadata_json）。
            metadata: 扩展元数据。

        Returns:
            True 表示写入成功，False 表示 TDengine 不可达或写入失败。
        """
        if not timestamps or not values:
            return False
        if not self._ensure_initialized():
            return False

        from pacific.whale.storage.raw_index import _escape_sql_val, _safe_table_name
        from pacific.whale.storage.waveform import _to_tdengine_ts

        # 合并 unit/value_type 到 metadata
        merged_meta: dict[str, Any] = dict(metadata) if metadata else {}
        if unit:
            merged_meta["unit"] = unit
        if value_type:
            merged_meta["value_type"] = value_type
        metadata_json_str = json.dumps(merged_meta)

        # 子表名按 result_code 生成
        subtable_name = f"sr_{_safe_table_name(result_code)}"

        written = 0
        for ts_str, val in zip(timestamps, values):
            try:
                ts_formatted = _to_tdengine_ts(ts_str)
                sql = (
                    f"INSERT INTO {self._database}.{subtable_name} "
                    f"USING {self._database}.{self._super_table} "
                    f"TAGS ('{_escape_sql_val(result_code)}') "
                    f"VALUES ("
                    f"'{_escape_sql_val(ts_formatted)}', "
                    f"'{_escape_sql_val(result_code)}', "
                    f"'{_escape_sql_val(channel_name)}', "
                    f"'{_escape_sql_val(str(val))}', "
                    f"'{_escape_sql_val(metadata_json_str)}'"
                    f")"
                )
                self._execute_sql(sql)
                written += 1
            except Exception as exc:
                logger.warning(
                    "simulation_result 写入失败 result_code=%s channel=%s: %s",
                    result_code, channel_name, exc,
                )
        return written > 0

    async def read_result_series(
        self,
        result_code: str,
        channel_name: str,
        start_time: str | None = None,
        end_time: str | None = None,
    ) -> list[dict[str, Any]]:
        """从 TDengine 读取仿真结果时序数据。

        按 result_code、channel_name 和可选时间范围查询。

        Args:
            result_code: 仿真结果编码。
            channel_name: 通道名称。
            start_time: 查询起始时间（ISO 格式），None 表示不限。
            end_time: 查询结束时间（ISO 格式），None 表示不限。

        Returns:
            符合条件的数据点列表，按时间戳排序。TDengine 不可达时返回空列表。
        """
        if not self._ensure_initialized():
            return []
        try:
            from pacific.whale.storage.raw_index import _escape_sql_val, _safe_table_name
            from pacific.whale.storage.waveform import _to_tdengine_ts

            subtable_name = f"sr_{_safe_table_name(result_code)}"
            where_clauses = [f"metric_key = '{_escape_sql_val(channel_name)}'"]
            if start_time:
                start_fmt = _to_tdengine_ts(start_time)
                where_clauses.append(f"ts >= '{_escape_sql_val(start_fmt)}'")
            if end_time:
                end_fmt = _to_tdengine_ts(end_time)
                where_clauses.append(f"ts <= '{_escape_sql_val(end_fmt)}'")

            where_sql = " AND ".join(where_clauses)
            sql = (
                f"SELECT * FROM {self._database}.{subtable_name} "
                f"WHERE {where_sql} "
                f"ORDER BY ts ASC LIMIT 10000"
            )
            result = self._execute_sql(sql)
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
            rows: list[dict[str, Any]] = []
            for row in data_rows:
                record: dict[str, Any] = {}
                for i, col_name in enumerate(col_names):
                    record[col_name] = row[i] if i < len(row) else None
                rows.append(record)
            return rows
        except Exception as exc:
            logger.warning(
                "simulation_result readback 失败 result_code=%s: %s", result_code, exc
            )
            return []

    async def health(self) -> bool:
        """通过 TDengine REST API 检查连接健康。

        执行 SELECT 1 验证数据库连接正常。

        Returns:
            True 表示 TDengine 可达。
        """
        try:
            result: dict[str, Any] = self._execute_sql("SELECT 1")
            code: int = int(result.get("code", -1))
            return code == 0
        except Exception:
            return False

    def _check_rest_api_alive(self) -> bool:
        """通过 REST API 探活 TDengine taosAdapter。

        对主路径和备选路径 /rest/sqlt 依次尝试执行 SELECT 1。
        TDengine taosAdapter 的 REST 路径可能配置为 /rest/sql（默认）
        或 /rest/sqlt（部分版本/部署）。

        此方法不修改 self._rest_path，仅探测连通性。

        Returns:
            True 表示 REST API 可用（任一路径成功）。
        """
        original_path = self._rest_path
        paths_to_check: list[str] = [original_path]
        # 如果主路径不是 /rest/sqlt，追加备选路径
        if original_path != "/rest/sqlt":
            paths_to_check.append("/rest/sqlt")
        # 如果主路径不是 /rest/sql，追加默认路径
        if original_path != "/rest/sql":
            paths_to_check.append("/rest/sql")

        for path in paths_to_check:
            try:
                self._rest_path = path
                result = self._execute_sql("SELECT 1")
                code: int = int(result.get("code", -1))
                if code == 0:
                    self._rest_path = original_path  # 恢复
                    return True
            except Exception:
                logger.debug(
                    "REST API 探活失败 path=%s host=%s:%s",
                    path, self._host, self._port,
                )
        self._rest_path = original_path  # 恢复
        return False
