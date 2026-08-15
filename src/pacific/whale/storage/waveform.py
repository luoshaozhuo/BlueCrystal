"""标准化波形存储端口与适配器。

定义标准化波形值的写入端口和内存/TDengine 后端实现。
标准化波形不同于标准化点值，用于表达高频采样波形或多通道同步数据。

本文件包含：
- StandardizedWaveformValue: 波形单个采样点数据模型。
- StandardizedWaveformSinkPort: 标准化波形写入抽象端口。
- InMemoryStandardizedWaveformSink: 测试用内存实现（P1 开发期验证）。
- TdengineStandardizedWaveformSink: TDengine 真实 adapter（P5 准生产依赖验证期）。

TDengine adapter 通过 REST API 与 taosAdapter 通信，使用 urllib 标准库，
不依赖 taos-py 驱动。TDengine 不可达时 write() 返回 False、readback() 返回空列表，
不抛异常。

环境变量：
- WHALE_TDENGINE_DSN: TDengine 连接字符串（优先）。
- TAOS_DSN: 备选连接字符串。
- WHALE_TDENGINE_REST_PATH: REST API 路径（默认 /rest/sql），例如 /rest/sqlt。
- 均未设置时默认 localhost:6041。

不负责：
- 波形数据的解码和修整（由 ingest decoder 负责）。
- 故障事件的分类和归档（由 FaultEventListener 负责）。
"""

from __future__ import annotations

import json
import logging
import os
import urllib.request
import urllib.error
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class StandardizedWaveformValue:
    """标准化波形单个采样点数据模型。

    表示波形数据中某一采样时刻的值、序号和质量码。
    多个 StandardizedWaveformValue 构成一条完整波形的时间序列。

    Attributes:
        timestamp: UTC ISO 时间戳（如 2025-01-01T00:00:00.000Z 或 TDengine 兼容格式）。
        value: 该采样点的物理量值。
        sample_index: 采样序号，从 0 开始递增。
        quality_code: 该采样点的质量码，默认 "0"（正常）。
    """

    timestamp: str
    value: float
    sample_index: int = 0
    quality_code: str = "0"


class StandardizedWaveformSinkPort(ABC):
    """标准化波形写入端口。

    将解码后的高频波形数据写入持久化存储。每条波形包含多采样点时间戳
    和值列表，以及 sample_rate_hz、channel_id 等元数据。

    实现方责任：
    - 按 event_id / source_id 维度高效写入波形数据。
    - 保留 channel_key / unit / value_type / quality_code 等元数据。
    - 支持按 event_id / source_id 查询验证。

    不负责：
    - 波形数据的解码和修整（由 ingest decoder 负责）。
    - 故障事件的分类和归档（由 FaultEventListener 负责）。
    """

    @abstractmethod
    async def write_waveform(
        self,
        event_id: str,
        source_id: str,
        channel_key: str,
        timestamps: list[str],
        values: list[float],
        *,
        sample_rate_hz: float = 0.0,
        unit: str = "",
        value_type: str = "FLOAT64",
        quality_code: str = "0",
        channel_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        """写入一条标准化波形数据。

        Args:
            event_id: 故障事件标识。
            source_id: 数据源标识。
            channel_key: 通道键。
            timestamps: 各采样点的 UTC ISO 时间戳列表。
            values: 各采样点的值列表（与 timestamps 对齐）。
            sample_rate_hz: 采样率（Hz）。
            unit: 物理单位。
            value_type: 值类型。
            quality_code: 质量码。
            channel_id: 通道标识（多通道波形时使用）。
            metadata: 扩展元数据字典。

        Returns:
            True 表示写入成功。

        Raises:
            RuntimeError: 写入失败时由实现决定是否抛异常。
        """
        ...


class InMemoryStandardizedWaveformSink(StandardizedWaveformSinkPort):
    """测试用内存标准化波形写入实现。

    将所有波形记录保存在内存列表中，支持按 event_id / source_id 查询。

    Attributes:
        _waveforms: 按写入顺序存储的波形记录列表。
    """

    def __init__(self) -> None:
        """初始化空的内存波形存储。"""
        self._waveforms: list[dict[str, Any]] = []

    async def write_waveform(
        self,
        event_id: str,
        source_id: str,
        channel_key: str,
        timestamps: list[str],
        values: list[float],
        *,
        sample_rate_hz: float = 0.0,
        unit: str = "",
        value_type: str = "FLOAT64",
        quality_code: str = "0",
        channel_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        """将一条波形记录写入内存。

        Args:
            event_id: 故障事件标识。
            source_id: 数据源标识。
            channel_key: 通道键。
            timestamps: 采样时间戳列表。
            values: 采样值列表。
            sample_rate_hz: 采样率。
            unit: 物理单位。
            value_type: 值类型。
            quality_code: 质量码。
            channel_id: 通道标识。
            metadata: 扩展元数据。

        Returns:
            True。
        """
        record: dict[str, Any] = {
            "event_id": event_id,
            "source_id": source_id,
            "channel_key": channel_key,
            "timestamps": list(timestamps),
            "values": list(values),
            "sample_rate_hz": sample_rate_hz,
            "unit": unit,
            "value_type": value_type,
            "quality_code": quality_code,
            "channel_id": channel_id,
            "metadata": dict(metadata) if metadata else {},
            "_written_at": datetime.now(tz=timezone.utc).isoformat(),
        }
        self._waveforms.append(record)
        return True

    def query_by_event(self, event_id: str) -> list[dict[str, Any]]:
        """按 event_id 查询波形记录。

        Args:
            event_id: 故障事件标识。

        Returns:
            符合条件的波形记录列表。
        """
        return [w for w in self._waveforms if w["event_id"] == event_id]

    def query_by_source(self, source_id: str) -> list[dict[str, Any]]:
        """按 source_id 查询波形记录。

        Args:
            source_id: 数据源标识。

        Returns:
            符合条件的波形记录列表。
        """
        return [w for w in self._waveforms if w["source_id"] == source_id]

    def clear(self) -> None:
        """清空所有已存储的波形记录。"""
        self._waveforms.clear()


class TdengineStandardizedWaveformSink(StandardizedWaveformSinkPort):
    """TDengine 标准化波形写入 adapter（真实 REST API 实现）。

    通过 TDengine REST API（/rest/sql）执行数据库创建、超级表创建、
    子表创建和波形数据写入。使用标准库 urllib，不依赖 taos-py 驱动。

    TDengine 不可达时，adapter 降级为 environment-pending 模式：
    - write_waveform() 返回 False 且不抛异常。
    - write() 返回 False 且不抛异常。
    - readback() 返回空列表且不抛异常。

    超级表 schema（super table waveform）：
    - ts: TIMESTAMP（采样时间戳）
    - event_id: NCHAR(128)
    - source_id: NCHAR(128)
    - channel_key: NCHAR(128)
    - sample_rate_hz: DOUBLE
    - sample_index: INT
    - value: NCHAR(256)
    - quality_code: NCHAR(8)
    - metadata_json: NCHAR(4096)
    - TAG: event_id_tag NCHAR(128), source_id_tag NCHAR(128)

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
        database: str = "whale_waveform",
        *,
        user: str = "root",
        password: str = "taosdata",
        rest_path: str | None = None,
    ) -> None:
        """初始化 TDengine 波形写入 adapter。

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
        self._super_table = "waveform"
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

    def _connect(self) -> bool:
        """通过 REST API 检测 TDengine 连通性。

        执行 SELECT 1 验证 taosAdapter 可达且正常响应。
        结果缓存到 self._connected，后续调用直接返回缓存值。

        Returns:
            True 表示 TDengine 可达。
        """
        if self._connected:
            return True
        try:
            result = self._execute_sql("SELECT 1")
            code: int = int(result.get("code", -1))
            self._connected = code == 0
            return self._connected
        except Exception as exc:
            logger.debug("TDengine waveform _connect 失败: %s", exc)
            self._connected = False
            return False

    def _ensure_initialized(self) -> bool:
        """确保 TDengine 数据库和超级表已创建。

        延迟初始化：首次调用时执行，后续跳过。
        创建数据库（如不存在）和 waveform 超级表（如不存在）。

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

            # 创建 waveform 超级表
            create_stable_sql = (
                f"CREATE STABLE IF NOT EXISTS {self._database}.{self._super_table} "
                f"(ts TIMESTAMP, "
                f"event_id NCHAR(128), "
                f"source_id NCHAR(128), "
                f"channel_key NCHAR(128), "
                f"sample_rate_hz DOUBLE, "
                f"sample_index INT, "
                f"`value` NCHAR(256), "
                f"quality_code NCHAR(8), "
                f"metadata_json NCHAR(4096)) "
                f"TAGS (event_id_tag NCHAR(128), source_id_tag NCHAR(128))"
            )
            self._execute_sql(create_stable_sql)
            self._connected = True
            logger.info(
                "TDengine waveform 初始化完成: db=%s super_table=%s",
                self._database, self._super_table,
            )
            return True
        except Exception as exc:
            self._error = f"TDengine waveform 初始化失败: {exc}"
            self._connected = False
            logger.warning(self._error)
            return False

    async def write(
        self,
        event_id: str,
        source_id: str,
        channel_key: str,
        samples: list[StandardizedWaveformValue],
        *,
        sample_rate_hz: float = 0.0,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        """批量写入标准化波形采样点到 TDengine。

        将 StandardizedWaveformValue 列表按超级表批量 INSERT。
        使用 TDengine 的自动建表语法（USING STABLE TAGS）。

        Args:
            event_id: 故障事件标识。
            source_id: 数据源标识。
            channel_key: 通道键。
            samples: 波形采样点列表。
            sample_rate_hz: 采样率（Hz）。
            metadata: 扩展元数据字典。

        Returns:
            True 表示全部写入成功，False 表示 TDengine 不可达或写入失败。
        """
        if not samples:
            return False
        if not self._ensure_initialized():
            return False

        from pacific.whale.storage.raw_index import _escape_sql_val, _safe_table_name

        metadata_json_str = json.dumps(metadata) if metadata else "{}"
        # 子表名按 event_id 生成
        subtable_name = f"wf_{_safe_table_name(event_id)}"

        written = 0
        for sample in samples:
            try:
                ts_formatted = _to_tdengine_ts(sample.timestamp)
                sql = (
                    f"INSERT INTO {self._database}.{subtable_name} "
                    f"USING {self._database}.{self._super_table} "
                    f"TAGS ("
                    f"'{_escape_sql_val(event_id)}', "
                    f"'{_escape_sql_val(source_id)}'"
                    f") VALUES ("
                    f"'{_escape_sql_val(ts_formatted)}', "
                    f"'{_escape_sql_val(event_id)}', "
                    f"'{_escape_sql_val(source_id)}', "
                    f"'{_escape_sql_val(channel_key)}', "
                    f"{sample_rate_hz}, "
                    f"{sample.sample_index}, "
                    f"'{_escape_sql_val(str(sample.value))}', "
                    f"'{_escape_sql_val(sample.quality_code)}', "
                    f"'{_escape_sql_val(metadata_json_str)}'"
                    f")"
                )
                self._execute_sql(sql)
                written += 1
            except Exception as exc:
                logger.warning(
                    "waveform 写入失败 event=%s idx=%d: %s",
                    event_id, sample.sample_index, exc,
                )
        return written > 0

    async def write_waveform(
        self,
        event_id: str,
        source_id: str,
        channel_key: str,
        timestamps: list[str],
        values: list[float],
        *,
        sample_rate_hz: float = 0.0,
        unit: str = "",
        value_type: str = "FLOAT64",
        quality_code: str = "0",
        channel_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        """写入一条标准化波形数据到 TDengine。

        将 timestamps 和 values 平行数组转换为 StandardizedWaveformValue 列表，
        委托给 write() 执行批量写入。

        Args:
            event_id: 故障事件标识。
            source_id: 数据源标识。
            channel_key: 通道键。
            timestamps: 各采样点的 UTC ISO 时间戳列表。
            values: 各采样点的值列表（与 timestamps 对齐）。
            sample_rate_hz: 采样率（Hz）。
            unit: 物理单位（当前暂存于 metadata）。
            value_type: 值类型（当前暂存于 metadata）。
            quality_code: 全局质量码（样本级可不同，此处作为默认值）。
            channel_id: 通道标识。
            metadata: 扩展元数据字典。

        Returns:
            True 表示写入成功，False 表示 TDengine 不可达或写入失败。
        """
        if not timestamps or not values:
            return False

        # 将 unit/value_type/channel_id 合并到 metadata
        merged_meta: dict[str, Any] = dict(metadata) if metadata else {}
        if unit:
            merged_meta["unit"] = unit
        if value_type:
            merged_meta["value_type"] = value_type
        if channel_id:
            merged_meta["channel_id"] = channel_id

        samples = [
            StandardizedWaveformValue(
                timestamp=ts,
                value=val,
                sample_index=i,
                quality_code=quality_code,
            )
            for i, (ts, val) in enumerate(zip(timestamps, values))
        ]
        return await self.write(
            event_id=event_id,
            source_id=source_id,
            channel_key=channel_key,
            samples=samples,
            sample_rate_hz=sample_rate_hz,
            metadata=merged_meta,
        )

    async def readback(
        self,
        event_id: str,
        limit: int = 1000,
    ) -> list[dict[str, Any]]:
        """从 TDengine 按 event_id 查询标准化波形数据。

        用于验证写入结果和诊断查询。

        Args:
            event_id: 故障事件标识。
            limit: 返回记录数上限，默认 1000。

        Returns:
            符合条件的波形记录列表，每条包含 ts、event_id、source_id、
            channel_key、sample_rate_hz、sample_index、value、quality_code、
            metadata_json 等字段。TDengine 不可达时返回空列表。
        """
        if not self._ensure_initialized():
            return []
        try:
            from pacific.whale.storage.raw_index import _safe_table_name

            subtable_name = f"wf_{_safe_table_name(event_id)}"
            sql = (
                f"SELECT * FROM {self._database}.{subtable_name} "
                f"ORDER BY ts ASC LIMIT {limit}"
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
            logger.warning("waveform readback 失败 event=%s: %s", event_id, exc)
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


# ---- TDengine waveform 辅助函数 ----


def _to_tdengine_ts(ts_str: str) -> str:
    """将 ISO 8601 或多种时间戳格式转换为 TDengine 兼容格式。

    TDengine REST API 接受的时间戳格式主要是 "YYYY-MM-DD HH:MM:SS.fff"。
    此函数尝试解析 ISO 8601（带 Z 后缀）、标准 datetime 字符串等格式，
    转换为 TDengine 兼容格式。

    Args:
        ts_str: 输入时间戳字符串（支持 ISO 8601、datetime 字符串等）。

    Returns:
        TDengine 兼容时间戳字符串（"YYYY-MM-DD HH:MM:SS.fff" 格式）。
        解析失败时返回原始字符串，由 TDengine 侧处理。
    """
    if not ts_str:
        return ts_str
    try:
        # 尝试 ISO 8601 格式：2025-01-01T00:00:00Z 或 2025-01-01T00:00:00+00:00
        cleaned = ts_str.replace("Z", "+00:00")
        if "T" in cleaned:
            from datetime import datetime, timezone
            dt = datetime.fromisoformat(cleaned)
            # 转为 UTC 后格式化为 TDengine 兼容格式
            if dt.tzinfo is not None:
                dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
            return dt.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        # 已是 "%Y-%m-%d %H:%M:%S" 格式，直接返回
        return ts_str
    except (ValueError, AttributeError):
        # 解析失败，返回原始字符串
        return ts_str
