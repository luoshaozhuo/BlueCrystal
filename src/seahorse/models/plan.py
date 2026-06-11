"""seahorse 核心模型 —— 种子计划与端点规划。

本模块定义 Seahorse 输出的计划结构，用于描述将要生成的场景
包含哪些资产、端点、点位、采集任务和服务端配置。

安全边界：
- 本模块不得 import whale.ingest。
- 本模块不得访问生产数据库。
- 本模块不得 import starfish；与 Starfish 的交互仅通过 JSON/dict 契约完成。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SeedEntity:
    """单个种子实体 —— 代表场景中一个可区分的逻辑设备或传感器。

    Attributes:
        entity_id: 实体唯一标识。
        entity_type: 实体类型，例如 "WTG"、"PV"、"SUBSTATION"。
        display_name: 显示名称。
        parent_entity_id: 父实体 ID（可选），用于层次化结构。
    """

    entity_id: str
    entity_type: str = "WTG"
    display_name: str = ""
    parent_entity_id: str | None = None


@dataclass
class SignalProfileItemPlan:
    """信号点位规划 —— 描述单个信号点位的生成意图。

    不包含实际信号值，只定义点位的标识、单位、数据类型和采样配置。

    Attributes:
        signal_id: 点位唯一标识。
        signal_name: 点位名称（如 "ActivePower"）。
        unit: 工程单位（如 "kW"）。
        data_type: 数据类型（如 "FLOAT64"）。
        ln_class: 逻辑节点类（如 "MMXU"）。
        cdc: 公共数据类（如 "MV"）。
        sample_interval_ms: 采样间隔（毫秒）。
        generation_hint: 生成策略提示，例如 "RAMP"、"SINUSOIDAL"、"RANDOM_WALK"。
    """

    signal_id: str
    signal_name: str = ""
    unit: str = ""
    data_type: str = "FLOAT64"
    ln_class: str = ""
    cdc: str = "MV"
    sample_interval_ms: int = 100
    generation_hint: str = "RANDOM"


@dataclass
class SignalProfilePlan:
    """信号点表计划 —— 描述一套信号点位的完整规划。

    Attributes:
        profile_id: 点表标识。
        profile_name: 点表名称。
        standard_family: 标准族（如 "GB_T_30966"）。
        items: 包含的信号点位规划列表。
    """

    profile_id: str
    profile_name: str = ""
    standard_family: str = ""
    items: list[SignalProfileItemPlan] = field(default_factory=list)


@dataclass
class EndpointPlan:
    """端点规划 —— 描述单个通信端点的规划信息。

    不绑定运行时连接，只描述协议、服务和传输参数。

    Attributes:
        endpoint_id: 端点标识。
        application_protocol: 应用协议（如 "OPC_UA"、"MODBUS"）。
        service_type: 服务类型（如 "READ"、"SUBSCRIBE"）。
        transport: 传输方式（如 "TCP"、"SERIAL"）。
        host: 主机地址。
        port: 端口号。
        endpoint_params: 端点参数键值对。
    """

    endpoint_id: str
    application_protocol: str = ""
    service_type: str = ""
    transport: str = "TCP"
    host: str | None = None
    port: int | None = None
    endpoint_params: dict[str, str | int | float | bool] = field(default_factory=dict)


@dataclass
class AcquisitionTaskPlan:
    """采集任务规划 —— 描述采集模式、超时与并发参数。

    Attributes:
        task_id: 任务标识。
        acquisition_mode: 采集模式（"POLLING"、"SUBSCRIBE"、"REPORT"）。
        poll_interval_ms: 轮询间隔（毫秒）。
        request_timeout_ms: 请求超时（毫秒）。
        associated_endpoint_id: 关联的端点 ID。
        associated_profile_id: 关联的点表 ID。
    """

    task_id: str
    acquisition_mode: str = "POLLING"
    poll_interval_ms: int = 100
    request_timeout_ms: int = 500
    associated_endpoint_id: str = ""
    associated_profile_id: str = ""


@dataclass
class SeedPlan:
    """种子计划 —— 描述场景包含的全部资产、点表和采集任务规划。

    Attributes:
        plan_id: 计划唯一标识。
        scenario_id: 关联的场景 ID。
        entities: 种子实体列表。
        signal_profiles: 信号点表计划列表。
        endpoints: 端点规划列表。
        acquisition_tasks: 采集任务规划列表。
    """

    plan_id: str
    scenario_id: str = ""
    entities: list[SeedEntity] = field(default_factory=list)
    signal_profiles: list[SignalProfilePlan] = field(default_factory=list)
    endpoints: list[EndpointPlan] = field(default_factory=list)
    acquisition_tasks: list[AcquisitionTaskPlan] = field(default_factory=list)


@dataclass
class ServerEndpointConfig:
    """服务端点配置 —— 描述单个 server member 对外暴露的端点。

    同时表达绑定层信息和 Starfish 契约层信息。bind_host/bind_port 描述
    服务端实际监听地址；host/port 描述 Starfish runtime 感知的连接地址；
    对于本地模拟场景两者通常一致，在容器化或 NAT 场景下可能不同。

    Attributes:
        endpoint_name: 端点名称，用于内部标识。
        endpoint_id: 端点唯一标识，用于 Starfish 契约引用。
        protocol: 协议（如 "OPC_UA_TCP"、"MODBUS_TCP"）。
        bind_host: 服务端绑定地址，用于 socket listen。
        bind_port: 服务端绑定端口，用于 socket listen。
        host: Starfish 契约层感知的主机地址。
        port: Starfish 契约层感知的端口号。
    """

    endpoint_name: str
    endpoint_id: str = ""
    protocol: str = ""
    bind_host: str = "0.0.0.0"
    bind_port: int = 0
    host: str = ""
    port: int = 0


@dataclass
class ServerPointConfig:
    """服务点位配置 —— 描述单个 server member 暴露的点位。

    同时包含 Seahorse 内部信号关联信息和 Starfish 契约层的
    node_key/variable_key/value_type 字段，确保点位的完整契约可导出。

    Attributes:
        point_id: 点位标识。
        point_name: 点位名称。
        data_type: Seahorse 内部数据类型（如 "FLOAT64"）。
        access_mode: 访问模式（"RO"、"WO"、"RW"）。
        associated_signal_id: 关联的信号 ID。
        node_key: Starfish 契约层的节点键（如 OPC UA NodeId）。
        variable_key: Starfish 契约层的变量键（如 OPC UA 属性路径）。
        value_type: Starfish 契约层的数据类型（如 "Float"、"Int32"）。
    """

    point_id: str
    point_name: str = ""
    data_type: str = "FLOAT64"
    access_mode: str = "RO"
    associated_signal_id: str = ""
    node_key: str = ""
    variable_key: str = ""
    value_type: str = ""


@dataclass
class ServerMemberConfig:
    """单个 server member 配置。

    对应 Starfish 运行期内一个可被统一启动/停止/读写的逻辑 server，
    语义上更接近 whale ORM 中的 `LDInstance + CommunicationEndpoint + SignalProfile`
    组合，而不是单个裸 endpoint。

    Attributes:
        server_id: server member 唯一标识。
        server_name: server member 可读名称。
        source_name: 上游源名称，可映射到 IED 名称。
        logical_device_name: 逻辑设备名称，可映射到 LDInstance.ld_name。
        endpoints: 该 member 暴露的端点列表。
        points: 该 member 使用的点位配置列表。
        capabilities: 能力声明列表。
        update_policy: 点位更新策略。
        initial_values: 初始值映射，key 为 point_id。
        synthetic: 合成数据标记，通常沿用顶层 ServerConfig.synthetic。
    """

    server_id: str
    server_name: str = ""
    source_name: str = ""
    logical_device_name: str = ""
    endpoints: list[ServerEndpointConfig] = field(default_factory=list)
    points: list[ServerPointConfig] = field(default_factory=list)
    capabilities: list[str] = field(default_factory=list)
    update_policy: dict[str, Any] = field(default_factory=dict)
    initial_values: dict[str, Any] = field(default_factory=dict)
    synthetic: bool = True


@dataclass
class ServerConfig:
    """服务端配置 —— 描述一组模拟服务端的完整配置。

    顶层不再假设“一个 server_name + 多 endpoint + 一套共享点位”，而是
    明确表达一组 server members。每个 member 可拥有独立 endpoint 和点位集，
    也可在上游生成阶段复用同构点位内容。
    """

    config_id: str
    scenario_id: str = ""
    config_name: str = ""
    servers: list[ServerMemberConfig] = field(default_factory=list)
    synthetic: bool = True
    strategy_id: str = ""
