"""Source write request DTOs for the write/control use case.

工业现场写入通常属于遥控/遥调/设点命令，因此使用 ``source_command_use_case`` 命名。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from pacific.whale.ingest.usecases.dtos.source_connection_data import SourceConnectionData


@dataclass(slots=True)
class SourceWriteItemData:
    """描述一个待写入点位。"""

    key: str
    """点位业务 key，对应采集系统中的 profile_item_key。"""

    node_id: str
    """协议层节点地址，如 OPC UA node_id。"""

    value_type: str
    """写入值的类型提示，如 bool / int32 / uint32 / float / double / string。"""

    value: str
    """字符串编码的写入值。"""


@dataclass(slots=True)
class SourceWriteExecutionOptions:
    """描述一次写入执行的选项。"""

    protocol: str
    transport: str

    request_timeout_ms: int = 10000
    """单次写入超时（毫秒）。"""

    dry_run: bool = False
    """为 True 时不执行真实写入，只校验和模拟。"""

    actor: str | None = None
    """操作者身份标识，用于审计预留。"""

    params: dict[str, str | int | float | bool] = field(default_factory=dict)
    """协议专属扩展参数。"""


@dataclass(slots=True)
class SourceWriteRequest:
    """描述一次完整的 source 写入请求。"""

    request_id: str
    """请求唯一标识，用于追踪和审计。"""

    command_id: str | None = None
    """命令唯一标识，建议由上游控制平面生成。"""

    trace_id: str | None = None
    """链路追踪标识，用于跨 use case/adapter 关联。"""

    task_id: int = 0
    """关联的任务 ID（可选）。"""

    execution: SourceWriteExecutionOptions = field(default_factory=lambda: SourceWriteExecutionOptions(protocol="", transport=""))
    """写入执行选项。"""

    connections: list[SourceConnectionData] = field(default_factory=list)
    """目标 source 连接列表。当前只取第一个 connection。"""

    items: list[SourceWriteItemData] = field(default_factory=list)
    """待写入点位列表。"""

    client_requested_at: datetime | None = None
    """客户端发起请求的时间戳。"""
