"""starfish 领域契约模型。

本模块定义 Starfish 消费 server 配置 JSON 后的内存模型，
镜像 Seahorse 导出的 handoff 契约结构。所有模型为纯 @dataclass，
不 import seahorse Python 类型。

当前 server config 的 JSON 契约 schema:
    - schema_version: 契约版本号 ("1.0.0")
    - scenario_id: 场景唯一标识
    - synthetic: 合成数据标识（始终为 True）
    - generator_version: Seahorse 生成器版本
    - generated_at: 生成时间 (ISO 8601)
    - config_name: 配置名称
    - strategy_id: 生成策略标识
    - servers: server member 列表
    - payload_hash: SHA256 内容哈希

安全边界：
- 不得 import seahorse。
- 不得 import whale.ingest / whale.shared.source。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class StarfishEndpointConfig:
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
class StarfishPointConfig:
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
class StarfishServerMemberConfig:
    """单个 server member 契约模型。

    表达一个可被 Starfish 独立装配、启动和读写的逻辑 server。
    每个 member 可包含一个或多个 endpoint，并拥有自己的点位与初始值集。
    """

    server_id: str = ""
    server_name: str = ""
    source_name: str = ""
    logical_device_name: str = ""
    endpoints: list[StarfishEndpointConfig] = field(default_factory=list)
    points: list[StarfishPointConfig] = field(default_factory=list)
    capabilities: list[str] = field(default_factory=list)
    update_policy: dict[str, Any] = field(default_factory=dict)
    initial_values: dict[str, Any] = field(default_factory=dict)
    synthetic: bool = True


@dataclass(init=False)
class StarfishServerConfig:
    """服务端配置契约模型 —— Starfish 启动一组 servers 的核心数据载体。

    从 Seahorse 导出的 server config JSON 文件反序列化得到。
    包含完整的 server members、能力声明和元数据。

    不负责：实际协议 server 启动、网络 I/O、数据持久化。
    仅作为契约数据的结构化内存表示。

    Attributes:
        schema_version: 契约 schema 版本号（如 "1.0.0"）。
        scenario_id: 场景唯一标识。
        generator_version: Seahorse 生成器组件版本。
        generated_at: ISO 8601 生成时间字符串。
        synthetic: 合成数据标识，始终为 True。
        config_name: 配置可读名称。
        strategy_id: 生成策略标识。
        servers: server member 列表。
        payload_hash: 内容 SHA256 哈希值，用于完整性校验。
    """

    schema_version: str = "1.0.0"
    scenario_id: str = ""
    generator_version: str = ""
    generated_at: str = ""
    synthetic: bool = True
    config_name: str = ""
    strategy_id: str = ""
    servers: list[StarfishServerMemberConfig] = field(default_factory=list)
    payload_hash: str = ""

    def __init__(
        self,
        schema_version: str = "1.0.0",
        scenario_id: str = "",
        generator_version: str = "",
        generated_at: str = "",
        synthetic: bool = True,
        config_name: str = "",
        strategy_id: str = "",
        servers: list[StarfishServerMemberConfig] | None = None,
        payload_hash: str = "",
        *,
        server_name: str = "",
        endpoints: list[StarfishEndpointConfig] | None = None,
        points: list[StarfishPointConfig] | None = None,
        capabilities: list[str] | None = None,
        update_policy: dict[str, Any] | None = None,
        initial_values: dict[str, Any] | None = None,
    ) -> None:
        """初始化 StarfishServerConfig，并兼容旧的单 server 扁平构造方式。"""
        normalized_servers = list(servers or [])
        if not normalized_servers and (
            server_name
            or endpoints is not None
            or points is not None
            or capabilities is not None
            or update_policy is not None
            or initial_values is not None
        ):
            normalized_servers = [
                StarfishServerMemberConfig(
                    server_id=f"{scenario_id}_server" if scenario_id else "",
                    server_name=server_name or config_name,
                    endpoints=list(endpoints or []),
                    points=list(points or []),
                    capabilities=list(capabilities or []),
                    update_policy=dict(update_policy or {}),
                    initial_values=dict(initial_values or {}),
                    synthetic=synthetic,
                )
            ]

        self.schema_version = schema_version
        self.scenario_id = scenario_id
        self.generator_version = generator_version
        self.generated_at = generated_at
        self.synthetic = synthetic
        self.config_name = config_name or server_name
        self.strategy_id = strategy_id
        self.servers = normalized_servers
        self.payload_hash = payload_hash

    def _single_server(self) -> StarfishServerMemberConfig:
        """返回单 server 兼容视图；多 server 配置下拒绝扁平访问。"""
        if len(self.servers) != 1:
            raise ValueError("该配置包含多个 servers，不能使用扁平单 server 视图。")
        return self.servers[0]

    @property
    def server_name(self) -> str:
        """兼容旧代码的单 server 名称访问。"""
        return self._single_server().server_name

    @property
    def endpoints(self) -> list[StarfishEndpointConfig]:
        """兼容旧代码的单 server endpoints 访问。"""
        return self._single_server().endpoints

    @property
    def points(self) -> list[StarfishPointConfig]:
        """兼容旧代码的单 server points 访问。"""
        return self._single_server().points

    @property
    def capabilities(self) -> list[str]:
        """兼容旧代码的单 server capabilities 访问。"""
        return self._single_server().capabilities

    @property
    def update_policy(self) -> dict[str, Any]:
        """兼容旧代码的单 server update_policy 访问。"""
        return self._single_server().update_policy

    @property
    def initial_values(self) -> dict[str, Any]:
        """兼容旧代码的单 server initial_values 访问。"""
        return self._single_server().initial_values


@dataclass
class ValidationResult:
    """加载或校验结果模型。

    用于 server config 加载器返回结构化校验明细，
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
    """JSON 加载结果 —— 包含解析出的 server config 和校验结论。

    Attributes:
        config: 加载成功的 StarfishServerConfig，加载失败时为 None。
        validation: 加载过程中的校验结果。
        file_path: 已加载的 JSON 文件路径。
    """

    config: StarfishServerConfig | None = None
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
    "StarfishServerConfig",
    "StarfishServerMemberConfig",
    "StarfishEndpointConfig",
    "StarfishPointConfig",
    "LoadResult",
    "ValidationResult",
    "UnsupportedOperation",
]
