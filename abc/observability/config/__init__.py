"""Observability unified configuration models."""

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class LoggingConfig:
    level: str = "INFO"


@dataclass(frozen=True, slots=True)
class MetricsConfig:
    namespace: str = "bluecrystal"
    subsystem: str | None = None


@dataclass(frozen=True, slots=True)
class TraceConfig:
    enabled: bool = True
    service_name: str = "bluecrystal"
    normal_sample_rate: float = 0.001


@dataclass(frozen=True, slots=True)
class ObservabilityConfig:
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    metrics: MetricsConfig = field(default_factory=MetricsConfig)
    trace: TraceConfig = field(default_factory=TraceConfig)
