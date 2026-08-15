"""
统一的 source 层数据模型，用于 read / subscription batch 处理。
包括节点值、batch、连接参数、节点信息等。
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

# -----------------------------
# 外部回调类型
# -----------------------------
SubscriptionCallback = Callable[["Batch"], Any]
"""外部数据变化回调类型，接收统一 Batch 对象。"""

# -----------------------------
# 连接参数支持类型
# -----------------------------
ConnectionParamValue = str | int | float | bool | None
"""可用于连接参数的类型，支持基本类型和 None。"""

# -----------------------------
# 连接配置
# -----------------------------
@dataclass(frozen=True, slots=True)
class SourceConnectionProfile:
    """协议层连接参数。"""

    endpoint: str
    """设备或服务端点，例如 OPC UA endpoint URL"""

    namespace_uri: str | None = None
    """命名空间 URI，用于定位节点类型，可选"""

    timeout_seconds: float = 4.0
    """单次 server 通信超时时间（秒）"""

    params: dict[str, ConnectionParamValue] = field(default_factory=dict)
    """可扩展参数字典，例如认证信息、协议特定参数等"""

# -----------------------------
# 节点值变化
# -----------------------------
@dataclass(frozen=True, slots=True)
class NodeValueChange:
    """节点值变化对象，用于 read / subscription batch。

    每个对象对应一个节点的变化信息。
    """

    node_key: str
    """节点唯一标识符（如 ns=2;s=Device1.Tag1）"""

    value: Any
    """节点的值"""

    quality: str | None = None
    """数据质量标记，例如 GOOD / BAD / UNCERTAIN"""

    source_timestamp: datetime | None = None
    """节点采集端的时间戳，即节点实际观测到数据的时间"""

    server_timestamp: datetime | None = None
    """节点服务器端时间戳"""

    client_sequence: int | None = None
    """客户端在接收 batch 内节点的序列号，用于去重和排序"""

    attributes: dict[str, Any] = field(default_factory=dict)
    """可扩展属性，例如标记 fastmode、异常类型等"""

# -----------------------------
# Batch
# -----------------------------
@dataclass(frozen=True, slots=True)
class Batch:
    """统一的 batch 对象，用于回调下游。

    Batch 是一次 read 或 subscription flush 的集合，包含多个 NodeValueChange。
    """

    changes: tuple[NodeValueChange, ...]
    """本批次节点变化集合"""

    batch_observed_at: datetime
    """数据在采集端被观测或生成的时间。
    通常取 batch 内变化最早节点的 source_timestamp，
    或 flush 时刻的 UTC 时间。用于时序分析和历史回放。
    """

    client_received_at: datetime
    """数据到达客户端的时间，反映网络传输延迟。
    对滞后监控、网络异常判定和延迟统计非常重要。
    """

    availability_status: str = "VALID"
    """数据可用性状态：
    - VALID：有效
    - ERROR：读取异常
    - STALE：数据滞后
    - OFFLINE：网络断开
    - UNKNOWN：未知
    """

    attributes: dict[str, Any] = field(default_factory=dict)
    """可扩展属性，例如异常原因、retry_count、网络滞后等"""

# -----------------------------
# 节点基本信息
# -----------------------------
@dataclass(frozen=True, slots=True)
class SourceNodeInfo:
    """可读变量节点的基本信息。"""

    node_path: str
    """节点路径"""

    data_type: str
    """节点数据类型，如 Int32, Float, Boolean 等"""

    ld_name: str
    """逻辑设备名称"""

    ln_name: str
    """逻辑节点名称"""

    do_name: str
    """数据对象名称"""