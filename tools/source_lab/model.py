"""source_lab 统一数据模型。

本文件只定义 simulator、profile、capacity 共用的轻量模型，不负责数据库访问、
协议驱动或生产 runtime 装配。新增字段需要保持对既有 simulator/facade 的
最小侵入兼容。
"""

from __future__ import annotations

from dataclasses import dataclass, field

ProtocolValue = str | int | float | bool


@dataclass(frozen=True, slots=True)
class UpdateConfig:
    """Fleet 周期更新配置。"""

    enabled: bool = True
    interval_seconds: float = 5.0
    update_ratio: float = 1.0
    update_count: int | None = None

    def __post_init__(self) -> None:
        if self.interval_seconds <= 0:
            raise ValueError("interval_seconds must be greater than 0")
        if not 0 < self.update_ratio <= 1:
            raise ValueError("update_ratio must be between 0 and 1")
        if self.update_count is not None and self.update_count <= 0:
            raise ValueError("update_count must be greater than 0")


@dataclass(frozen=True, slots=True)
class SecurityConfig:
    """工业协议共用的安全配置摘要。"""

    enabled: bool = False
    policy: str | None = None
    mode: str | None = None
    tls_enabled: bool = False
    certificate_path: str | None = None
    private_key_path: str | None = None
    ca_certificate_path: str | None = None


@dataclass(frozen=True, slots=True)
class AuthConfig:
    """协议认证配置摘要。"""

    username: str | None = None
    password: str | None = None
    token: str | None = None
    auth_type: str | None = None


@dataclass(frozen=True, slots=True)
class HeartbeatConfig:
    """长连接协议使用的心跳与保活配置。"""

    enabled: bool = False
    interval_seconds: float | None = None
    timeout_seconds: float | None = None
    reconnect_backoff_seconds: float | None = None


@dataclass(frozen=True, slots=True)
class TimeoutConfig:
    """工业协议常见超时配置。"""

    connect_timeout_seconds: float | None = None
    request_timeout_seconds: float | None = None
    read_timeout_seconds: float | None = None
    write_timeout_seconds: float | None = None


@dataclass(frozen=True, slots=True)
class SourceConnection:
    """Transport-level connection details for one simulated source.

    ``protocol`` 是旧 CLI 别名（如 opcua / modbus_tcp / iec61850_goose）；
    ``application_protocol`` / ``service_type`` 是三元组新字段。
    构造时提供旧 ``protocol`` 即可，新字段可通过 factory 方法自动推导。
    """

    name: str
    ied_name: str
    ld_name: str
    host: str
    port: int
    transport: str
    protocol: str
    application_protocol: str | None = None
    service_type: str | None = None
    namespace_uri: str | None = None
    security: SecurityConfig = field(default_factory=SecurityConfig)
    auth: AuthConfig = field(default_factory=AuthConfig)
    heartbeat: HeartbeatConfig = field(default_factory=HeartbeatConfig)
    timeouts: TimeoutConfig = field(default_factory=TimeoutConfig)
    params: dict[str, str | int | float | bool] = field(default_factory=dict)

    @classmethod
    def from_protocol(cls, *, name: str, ied_name: str, ld_name: str,
                      host: str, port: int, protocol: str,
                      transport: str | None = None,
                      namespace_uri: str | None = None,
                      security: SecurityConfig | None = None,
                      auth: AuthConfig | None = None,
                      heartbeat: HeartbeatConfig | None = None,
                      timeouts: TimeoutConfig | None = None,
                      params: dict[str, str | int | float | bool] | None = None) -> SourceConnection:
        """从旧式 protocol 名称创建 SourceConnection，自动解析三元组。

        Args:
            name: 连接名称。
            ied_name: IED 名称。
            ld_name: 逻辑设备名称。
            host: 主机地址。
            port: 端口号。
            protocol: 旧式协议别名（如 opcua / modbus_tcp）。
            transport: 传输协议，默认从三元组推断。
            namespace_uri: 可选的命名空间 URI。
            security: 可选的安全配置。
            auth: 可选的认证配置。
            heartbeat: 可选的心跳配置。
            timeouts: 可选的超时配置。
            params: 可选的协议参数字典。

        Returns:
            填充了 application_protocol、service_type、transport 的 SourceConnection。

        Raises:
            无；resolve_service_triple 在无法解析时返回 None，自动使用空字符串填充。
        """
        from tools.source_lab.access.runners.registry import resolve_service_triple
        triple = resolve_service_triple(protocol)
        if triple is None:
            # 无法解析时使用空三元组
            app_proto, svc_type, tport = ("", "", "")
        else:
            app_proto, svc_type, tport = triple
        return cls(
            name=name, ied_name=ied_name, ld_name=ld_name,
            host=host, port=port, transport=transport or tport,
            protocol=protocol,
            application_protocol=app_proto,
            service_type=svc_type,
            namespace_uri=namespace_uri,
            security=security or SecurityConfig(),
            auth=auth or AuthConfig(),
            heartbeat=heartbeat or HeartbeatConfig(),
            timeouts=timeouts or TimeoutConfig(),
            params=params or {},
        )


@dataclass(frozen=True, slots=True)
class SimulatedPoint:
    """协议无关的单点位描述。

    `address` 用于承载协议层地址；`protocol_params` 用于最小侵入保留点位级
    协议参数，避免把协议专用字段挤回公共主字段。
    """

    ln_name: str
    do_name: str
    unit: str | None
    data_type: str
    initial_value: str | int | float | bool | None = None
    address: str | None = None
    protocol_params: dict[str, ProtocolValue] = field(default_factory=dict)

    @property
    def key(self) -> str:
        if self.ln_name and self.do_name:
            return f"{self.ln_name}.{self.do_name}"
        return self.do_name

    @property
    def locator(self) -> str:
        return self.address or self.key

    @property
    def display_name(self) -> str:
        return self.do_name or self.address or self.key

    @property
    def point_kind(self) -> str:
        return "status" if self.data_type.upper() == "BOOLEAN" else "measurement"


@dataclass(frozen=True, slots=True)
class SimulatedSource:
    """单个模拟源及其连接、点位元数据。"""

    connection: SourceConnection
    points: tuple[SimulatedPoint, ...]
