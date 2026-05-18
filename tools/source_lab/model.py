"""Data models for source lab simulators and profile tests."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class UpdateConfig:
    """Shared periodic update config used by the fleet scheduler."""

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
    """Security settings common across industrial communication protocols."""

    enabled: bool = False
    policy: str | None = None
    mode: str | None = None
    tls_enabled: bool = False
    certificate_path: str | None = None
    private_key_path: str | None = None
    ca_certificate_path: str | None = None


@dataclass(frozen=True, slots=True)
class AuthConfig:
    """Authentication settings used by protocols that require credentials."""

    username: str | None = None
    password: str | None = None
    token: str | None = None
    auth_type: str | None = None


@dataclass(frozen=True, slots=True)
class HeartbeatConfig:
    """Heartbeat and keepalive settings for persistent industrial sessions."""

    enabled: bool = False
    interval_seconds: float | None = None
    timeout_seconds: float | None = None
    reconnect_backoff_seconds: float | None = None


@dataclass(frozen=True, slots=True)
class TimeoutConfig:
    """Timeout settings commonly used by field communication protocols."""

    connect_timeout_seconds: float | None = None
    request_timeout_seconds: float | None = None
    read_timeout_seconds: float | None = None
    write_timeout_seconds: float | None = None


@dataclass(frozen=True, slots=True)
class SourceConnection:
    """Transport-level connection details for one simulated source."""

    name: str
    ied_name: str
    ld_name: str
    host: str
    port: int
    transport: str
    protocol: str
    namespace_uri: str | None = None
    security: SecurityConfig = field(default_factory=SecurityConfig)
    auth: AuthConfig = field(default_factory=AuthConfig)
    heartbeat: HeartbeatConfig = field(default_factory=HeartbeatConfig)
    timeouts: TimeoutConfig = field(default_factory=TimeoutConfig)
    params: dict[str, str | int | float | bool] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class SimulatedPoint:
    """Protocol-agnostic description of one simulated point."""

    ln_name: str
    do_name: str
    unit: str | None
    data_type: str
    initial_value: str | int | float | bool | None = None

    @property
    def key(self) -> str:
        if self.ln_name and self.do_name:
            return f"{self.ln_name}.{self.do_name}"
        return self.do_name

    @property
    def locator(self) -> str:
        return self.key

    @property
    def display_name(self) -> str:
        return self.do_name

    @property
    def point_kind(self) -> str:
        return "status" if self.data_type.upper() == "BOOLEAN" else "measurement"


@dataclass(frozen=True, slots=True)
class SimulatedSource:
    """One simulated source plus all connection and point metadata."""

    connection: SourceConnection
    points: tuple[SimulatedPoint, ...]
