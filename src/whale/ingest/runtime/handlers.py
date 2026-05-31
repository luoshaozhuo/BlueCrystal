"""WorkerRuntime job handlers for ingest.

本模块定义 WorkerRuntime 使用的 JobHandler 实现。
每个 handler 负责将 scheduler job 转换为对应的 use case 调用。

当前状态：
- ``AcquisitionJobHandler`` — 最小生产采集 handler（PENDING 完整验证）。
  通过 asyncio.run() 桥接 async use case 到 sync handler 协议。
  长期应替换为基于共享事件循环的异步调度器。

JobHandler 协议要求：
    ``execute(self, job: IngestRuntimeJob) -> None``
    抛出异常即标记为 job_failed，由 WorkerRuntime._execute_one 的
    except 块统一处理 audit/metrics/lease。
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from whale.ingest.usecases.dtos.source_acquisition_request import (
    AcquisitionExecutionOptions,
    AcquisitionItemData,
    SourceAcquisitionRequest,
)
from whale.ingest.usecases.dtos.source_connection_data import SourceConnectionData
from whale.shared.persistence.orm.ingest_runtime import IngestRuntimeJob

if TYPE_CHECKING:
    from whale.ingest.usecases.source_acquisition_use_case import (
        SourceAcquisitionUseCase,
    )

_logger = logging.getLogger(__name__)


class AcquisitionJobHandler:
    """将 scheduler job 转换为 SourceAcquisitionUseCase 调用的生产 handler。

    从 ``job.config_json`` 读取采集参数，构造 ``SourceAcquisitionRequest``，
    通过 ``asyncio.run()`` 同步桥接到异步 use case。

    局限性（PENDING 完整解决）：
    - 每次调用 ``asyncio.run()`` 创建新事件循环，高频调度时开销较大。
      长期方案：将 WorkerRuntime 迁移到异步事件循环共享。
    - 当前仅支持 config_json 中的 "items" 字段为 list[dict] 格式。
    - 不处理 subscription 模式的长时间运行会话 — subscription session
      的生命周期由 SubscriptionAcquisitionRole 内部管理，handler
      仅负责触发启动。
    - 采集结果的生命周期由 PollingAcquisitionRole/SubscriptionAcquisitionRole
      驱动，handler 不返回采集数据 — 数据写入由 state cache 完成。

    Args:
        use_case: 已装配的 SourceAcquisitionUseCase 实例。
    """

    def __init__(self, use_case: SourceAcquisitionUseCase) -> None:
        """初始化采集任务 handler。Args: use_case: 采集用例实例。"""
        self._use_case = use_case

    def execute(self, job: IngestRuntimeJob) -> None:
        """初始化采集任务 handler。Args: use_case: 采集用例实例。"""
        """执行一次采集 job。

        从 ``job.config_json`` 解析请求参数并调用 use case。
        异常向上传播，由 WorkerRuntime 在 ``_execute_one`` 的 except 块
        统一处理 job_failed 指标和审计事件。

        Raises:
            ValueError: config_json 缺少必要字段或格式错误。
            RuntimeError: use case 执行失败。
        """
        config = job.config_json
        request = self._build_request_from_config(config)
        _logger.info(
            "AcquisitionJobHandler executing job_id=%s task_id=%s protocol=%s",
            job.job_id,
            request.task_id,
            request.execution.protocol,
        )
        # 同步桥接到异步 use case。
        # 长期应替换为共享事件循环或异步调度器。
        try:
            asyncio.run(self._use_case.start(request))
        except Exception:
            _logger.exception(
                "AcquisitionJobHandler failed job_id=%s task_id=%s",
                job.job_id,
                request.task_id,
            )
            raise

    @staticmethod
    def _build_request_from_config(
        config: dict[str, object],
    ) -> SourceAcquisitionRequest:
        """从 job config JSON 构造 SourceAcquisitionRequest。

        支持的 config_json 字段：
            request_id (str): 请求标识。
            task_id (int): 关联的采集任务 ID。
            execution (dict): 执行选项（protocol, transport, acquisition_mode 等）。
            connections (list[dict]): 连接信息列表。
            items (list[dict]): 采集点位列表。

        Raises:
            ValueError: 必要字段缺失或格式错误。
        """
        request_id = _get_str(config, "request_id", job_prefix="unknown")
        task_id = _get_int(config, "task_id", default=1)

        exec_raw = config.get("execution")
        if not isinstance(exec_raw, dict):
            raise ValueError(
                "config_json.execution is required and must be a dict"
            )
        execution = AcquisitionExecutionOptions(
            protocol=_get_str(exec_raw, "protocol"),
            transport=_get_str(exec_raw, "transport"),
            acquisition_mode=_get_str(exec_raw, "acquisition_mode", default="READ"),
            interval_ms=_get_int(exec_raw, "interval_ms", default=5000),
            max_iteration=_get_int_or_none(exec_raw, "max_iteration"),
            request_timeout_ms=_get_int(exec_raw, "request_timeout_ms", default=5000),
            freshness_timeout_ms=_get_int(exec_raw, "freshness_timeout_ms", default=30000),
            alive_timeout_ms=_get_int(exec_raw, "alive_timeout_ms", default=60000),
            client_backend=_get_str_or_none(exec_raw, "client_backend"),
            params=_get_dict(exec_raw, "params"),
        )

        conns_raw = config.get("connections")
        if not isinstance(conns_raw, list):
            raise ValueError(
                "config_json.connections is required and must be a list"
            )
        connections = [_parse_connection(c) for c in conns_raw]

        items_raw = config.get("items")
        if not isinstance(items_raw, list):
            raise ValueError(
                "config_json.items is required and must be a list"
            )
        items = [_parse_item(i) for i in items_raw]

        return SourceAcquisitionRequest(
            request_id=request_id,
            task_id=task_id,
            execution=execution,
            connections=connections,
            items=items,
        )


# ── helpers ──────────────────────────────────────────────────────────────


def _get_str(data: dict[str, object], key: str, *, default: str = "", job_prefix: str = "") -> str:
    value = data.get(key, default)
    if not isinstance(value, str):
        raise ValueError(
            f"config_json.{key} is required and must be a string, got {type(value).__name__}"
        )
    return value


def _get_str_or_none(data: dict[str, object], key: str) -> str | None:
    value = data.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        return None
    return value


def _get_int(data: dict[str, object], key: str, *, default: int = 0) -> int:
    value = data.get(key, default)
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, str):
        try:
            return int(value)
        except (TypeError, ValueError):
            raise ValueError(
                f"config_json.{key} must be a valid integer, got {value!r}"
            ) from None
    raise ValueError(
        f"config_json.{key} must be a number, got {type(value).__name__}"
    )


def _get_int_or_none(data: dict[str, object], key: str) -> int | None:
    value = data.get(key)
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return None


def _get_dict(data: dict[str, object], key: str) -> dict[str, str | int | float | bool]:
    value = data.get(key)
    if not isinstance(value, dict):
        return {}
    result: dict[str, str | int | float | bool] = {}
    for k, v in value.items():
        if isinstance(v, (str, int, float, bool)):
            result[k] = v
    return result


def _parse_connection(raw: object) -> SourceConnectionData:
    """从 config_json 字典解析单个连接 DTO。"""
    if not isinstance(raw, dict):
        raise ValueError(f"connection must be a dict, got {type(raw).__name__}")
    return SourceConnectionData(
        host=_get_str(raw, "host", default="localhost"),
        port=_get_int(raw, "port", default=4840),
        ied_name=_get_str(raw, "ied_name", default="IED1"),
        ld_name=_get_str(raw, "ld_name", default="LD1"),
        namespace_uri=_get_str(raw, "namespace_uri", default=""),
        params=_get_dict(raw, "params"),
    )


def _parse_item(raw: object) -> AcquisitionItemData:
    """从 config_json 字典解析单个采集点位 DTO。"""
    if not isinstance(raw, dict):
        raise ValueError(f"item must be a dict, got {type(raw).__name__}")
    return AcquisitionItemData(
        key=_get_str(raw, "key"),
        profile_item_id=_get_int(raw, "profile_item_id", default=1),
        relative_path=_get_str(raw, "relative_path"),
    )
