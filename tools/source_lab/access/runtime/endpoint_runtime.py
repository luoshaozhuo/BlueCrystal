"""Endpoint-level runtime models for dynamic source_lab adjustment."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum

from whale.shared.source.access.model import SourceEndpointSpec, SourcePointSpec
from tools.source_lab.access.providers.base import SourceRuntimeSpec

SENSITIVE_PARAM_KEYS = {
    "password",
    "token",
    "secret",
    "private_key",
    "private_key_path",
    "certificate",
    "certificate_path",
    "ca_certificate_path",
    "username",
    "security_params",
    "security_password",
}


class EndpointMode(str, Enum):
    POLLING = "polling"
    SUBSCRIBE = "subscribe"
    REPORT = "report"
    STREAMING = "streaming"


class EndpointRuntimeState(str, Enum):
    CREATED = "created"
    STARTING = "starting"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"
    FAILED = "failed"
    REPLACING = "replacing"
    DELETED = "deleted"


def utc_now_iso() -> str:
    return datetime.now(tz=UTC).isoformat()


def redact_sensitive_mapping(values: dict[str, object]) -> dict[str, object]:
    redacted: dict[str, object] = {}
    for key, value in values.items():
        if key.lower() in SENSITIVE_PARAM_KEYS:
            redacted[key] = "***REDACTED***"
            continue
        if isinstance(value, dict):
            redacted[key] = redact_sensitive_mapping(value)
            continue
        redacted[key] = value
    return redacted


@dataclass(frozen=True, slots=True)
class EndpointRuntimeConfig:
    """Immutable endpoint configuration tracked by the runtime registry."""

    endpoint_id: str
    protocol: str
    mode: EndpointMode
    source: SourceRuntimeSpec
    target_hz: float | None = None
    publishing_interval_ms: float | None = None
    read_timeout_s: float = 5.0
    config_version: int = 1

    def expected_period_ms(self) -> float:
        if self.mode == EndpointMode.POLLING:
            hz = self.target_hz or 1.0
            return max(1.0, 1000.0 / hz)
        if self.publishing_interval_ms is not None:
            return max(1.0, self.publishing_interval_ms)
        return 1000.0

    def to_dict(self) -> dict[str, object]:
        return {
            "endpoint_id": self.endpoint_id,
            "protocol": self.protocol,
            "mode": self.mode.value,
            "target_hz": self.target_hz,
            "publishing_interval_ms": self.publishing_interval_ms,
            "read_timeout_s": self.read_timeout_s,
            "config_version": self.config_version,
            "source": {
                "endpoint": {
                    "name": self.source.endpoint.name,
                    "host": self.source.endpoint.host,
                    "port": self.source.endpoint.port,
                    "protocol": self.source.endpoint.protocol,
                    "transport": self.source.endpoint.transport,
                    "namespace_uri": self.source.endpoint.namespace_uri,
                    "ied_name": self.source.endpoint.ied_name,
                    "ld_name": self.source.endpoint.ld_name,
                    "params": dict(self.source.endpoint.params),
                    "redacted_params": redact_sensitive_mapping(
                        dict(self.source.endpoint.params)
                    ),
                },
                "points": [
                    {
                        "address": point.address,
                        "name": point.name,
                        "data_type": point.data_type,
                        "ln_name": point.ln_name,
                        "do_name": point.do_name,
                        "unit": point.unit,
                    }
                    for point in self.source.points
                ],
            },
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "EndpointRuntimeConfig":
        source_data = dict(data["source"])
        endpoint_data = dict(source_data["endpoint"])
        points_data = list(source_data["points"])
        source = SourceRuntimeSpec(
            endpoint=SourceEndpointSpec(
                name=str(endpoint_data["name"]),
                host=str(endpoint_data["host"]),
                port=int(endpoint_data["port"]),
                protocol=str(endpoint_data["protocol"]),
                transport=str(endpoint_data.get("transport", "tcp")),
                namespace_uri=endpoint_data.get("namespace_uri"),
                ied_name=str(endpoint_data.get("ied_name", "")),
                ld_name=str(endpoint_data.get("ld_name", "")),
                params=dict(endpoint_data.get("params", {})),
            ),
            points=tuple(
                SourcePointSpec(
                    address=str(point["address"]),
                    name=point.get("name"),
                    data_type=point.get("data_type"),
                    ln_name=point.get("ln_name"),
                    do_name=point.get("do_name"),
                    unit=point.get("unit"),
                )
                for point in points_data
            ),
            runtime_handle=None,
        )
        return cls(
            endpoint_id=str(data["endpoint_id"]),
            protocol=str(data["protocol"]),
            mode=EndpointMode(str(data["mode"])),
            source=source,
            target_hz=float(data["target_hz"]) if data.get("target_hz") is not None else None,
            publishing_interval_ms=(
                float(data["publishing_interval_ms"])
                if data.get("publishing_interval_ms") is not None
                else None
            ),
            read_timeout_s=float(data.get("read_timeout_s", 5.0)),
            config_version=int(data.get("config_version", 1)),
        )


@dataclass(slots=True)
class EndpointRuntime:
    endpoint_id: str
    protocol: str
    mode: str
    config_version: int
    state: EndpointRuntimeState
    stagger_offset_ns: int
    runner_handle: object | None = None
    created_at: str = field(default_factory=utc_now_iso)
    updated_at: str = field(default_factory=utc_now_iso)
    last_started_at: str | None = None
    last_stopped_at: str | None = None
    last_error: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "endpoint_id": self.endpoint_id,
            "protocol": self.protocol,
            "mode": self.mode,
            "config_version": self.config_version,
            "state": self.state.value,
            "stagger_offset_ns": self.stagger_offset_ns,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "last_started_at": self.last_started_at,
            "last_stopped_at": self.last_stopped_at,
            "last_error": self.last_error,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "EndpointRuntime":
        return cls(
            endpoint_id=str(data["endpoint_id"]),
            protocol=str(data["protocol"]),
            mode=str(data["mode"]),
            config_version=int(data["config_version"]),
            state=EndpointRuntimeState(str(data["state"])),
            stagger_offset_ns=int(data.get("stagger_offset_ns", 0)),
            created_at=str(data.get("created_at", utc_now_iso())),
            updated_at=str(data.get("updated_at", utc_now_iso())),
            last_started_at=(
                str(data["last_started_at"]) if data.get("last_started_at") is not None else None
            ),
            last_stopped_at=(
                str(data["last_stopped_at"]) if data.get("last_stopped_at") is not None else None
            ),
            last_error=str(data["last_error"]) if data.get("last_error") is not None else None,
        )
