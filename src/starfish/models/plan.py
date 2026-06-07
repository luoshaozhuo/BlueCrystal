"""starfish 侧最小契约模型。

本模块定义 Starfish runtime 消费 ServerPlan JSON 后的内存模型，
镜像 Seahorse 导出的 JSON 契约结构。所有模型为纯 @dataclass，
不 import seahorse Python 类型。

StarfisServerPlan 的 JSON 契约 schema:
    - schema_version: 契约版本号 ("1.0.0")
    - scenario_id: 场景唯一标识
    - synthetic: 合成数据标识（始终为 True）
    - generator_version: Seahorse 生成器版本
    - generated_at: 生成时间 (ISO 8601)
    - server_name: 服务端名称
    - strategy_id: 生成策略标识
    - endpoints: 端点列表
    - points: 点位列表
    - capabilities: 能力声明列表 (READ/WRITE/SUBSCRIBE/REPORT)
    - update_policy: 点位更新策略
    - initial_values: 初始值映射 (point_id -> value)
    - payload_hash: SHA256 内容哈希

安全边界：
- 不得 import seahorse。
- 不得 import whale.ingest / whale.shared.source。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class StarfishEndpointPlan:
    """服务端点契约模型 —— 描述单个协议端点的连接信息。

    不负责：实际 socket 监听、协议握手、TLS 配置。
    仅作为 JSON 反序列化后的契约数据载体。

    Attributes:
        endpoint_id: 端点唯一标识。
        protocol: 协议名（如 "OPC_UA"、"MODBUS_TCP"）。
        host: 连接地址。
        port: 端口号。
        bind_host: 绑定地址（容器化场景可能不同于 host）。
        bind_port: 绑定端口（容器化场景可能不同于 port）。
        endpoint_name: 端点可读名称。
    """

    endpoint_id: str = ""
    protocol: str = ""
    host: str = ""
    port: int = 0
    bind_host: str | None = None
    bind_port: int | None = None
    endpoint_name: str | None = None


@dataclass
class StarfishPointPlan:
    """点位契约模型 —— 描述单个数据点的标识与访问属性。

    不负责：信号值生成、协议帧编解码、数据断言。
    仅作为 JSON 反序列化后的契约数据载体。

    Attributes:
        point_id: 点位唯一标识。
        point_name: 点位可读名称。
        node_key: 协议节点键（如 OPC UA NodeId）。
        variable_key: 协议变量键（如 OPC UA 属性路径）。
        value_type: 协议层数据类型（如 "Float"、"Int32"）。
        access_mode: 访问模式（"RO"、"WO"、"RW"）。
        data_type: Seahorse 内部数据类型（如 "FLOAT64"）。
    """

    point_id: str = ""
    point_name: str = ""
    node_key: str = ""
    variable_key: str = ""
    value_type: str = ""
    access_mode: str = "RO"
    data_type: str = "FLOAT64"


@dataclass
class StarfishServerPlan:
    """服务端计划契约模型 —— Starfish runtime 启动的核心数据载体。

    从 Seahorse 导出的 starfish_server_plan.json 文件反序列化得到。
    包含完整的端点、点位、能力声明和初始值信息。

    不负责：实际协议 server 启动、网络 I/O、数据持久化。
    仅作为契约数据的结构化内存表示。

    Attributes:
        schema_version: 契约 schema 版本号（如 "1.0.0"）。
        scenario_id: 场景唯一标识。
        generator_version: Seahorse 生成器组件版本。
        generated_at: ISO 8601 生成时间字符串。
        synthetic: 合成数据标识，始终为 True。
        server_name: 服务端可读名称。
        strategy_id: 生成策略标识。
        endpoints: 服务端点列表。
        points: 服务点位列表。
        capabilities: 服务能力声明列表。
        update_policy: 点位更新策略 dict。
        initial_values: 初始值映射（point_id -> 初始值）。
        payload_hash: 内容 SHA256 哈希值，用于完整性校验。
    """

    schema_version: str = "1.0.0"
    scenario_id: str = ""
    generator_version: str = ""
    generated_at: str = ""
    synthetic: bool = True
    server_name: str = ""
    strategy_id: str = ""
    endpoints: list[StarfishEndpointPlan] = field(default_factory=list)
    points: list[StarfishPointPlan] = field(default_factory=list)
    capabilities: list[str] = field(default_factory=list)
    update_policy: dict[str, Any] = field(default_factory=dict)
    initial_values: dict[str, Any] = field(default_factory=dict)
    payload_hash: str = ""


@dataclass
class ValidationResult:
    """加载或校验结果模型。

    用于 ServerPlan 加载器返回结构化校验明细，
    支持 errors/warnings/passed_checks 三通道。

    Attributes:
        errors: 错误消息列表（阻止正常使用的致命问题）。
        warnings: 警告消息列表（可降级但不阻止使用的问题）。
        passed_checks: 通过的检查项描述列表。
    """

    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    passed_checks: list[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        """无错误即视为有效。警告不阻止通过。"""
        return len(self.errors) == 0

    def add_error(self, message: str) -> None:
        """添加一条错误消息。

        Args:
            message: 错误描述。
        """
        self.errors.append(message)

    def add_warning(self, message: str) -> None:
        """添加一条警告消息。

        Args:
            message: 警告描述。
        """
        self.warnings.append(message)

    def add_pass(self, message: str) -> None:
        """添加一条通过的检查项描述。

        Args:
            message: 检查项描述。
        """
        self.passed_checks.append(message)


@dataclass
class LoadResult:
    """JSON 加载结果 —— 包含解析出的 ServerPlan 和校验结论。

    Attributes:
        plan: 加载成功的 StarfishServerPlan，加载失败时为 None。
        validation: 加载过程中的校验结果。
        file_path: 已加载的 JSON 文件路径。
    """

    plan: StarfishServerPlan | None = None
    validation: ValidationResult = field(default_factory=ValidationResult)
    file_path: str = ""


class UnsupportedOperation(Exception):
    """操作尚未实现的标准异常。

    用于 ServerSimulatorFacade 中尚未实现的方法
    （如 write/subscribe/report），明确表达 NOT_IMPLEMENTED 语义，
    不假装操作已完成。

    Attributes:
        operation: 未实现的操作名称。
        reason: 可选的原因说明。
    """

    def __init__(self, operation: str, reason: str = "") -> None:
        self.operation = operation
        self.reason = reason
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        """格式化异常消息。

        包含操作名和可选原因，确保调用方和日志可清晰识别。
        """
        msg = f"NOT_IMPLEMENTED: {self.operation}"
        if self.reason:
            msg += f" — {self.reason}"
        return msg


__all__ = [
    "StarfishServerPlan",
    "StarfishEndpointPlan",
    "StarfishPointPlan",
    "LoadResult",
    "ValidationResult",
    "UnsupportedOperation",
]
