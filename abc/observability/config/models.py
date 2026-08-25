"""可观测性 YAML 的强类型配置契约。

稳定字段拒绝未知键；第三方库原生参数仅在 ``options`` 字段中保留为映射，
由对应 adapter 在创建第三方对象时完成最终校验。
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, RootModel


class _StrictModel(BaseModel):
    """为稳定配置字段提供严格的未知键检查。"""

    model_config = ConfigDict(extra="forbid", frozen=True)


class ServiceConfig(_StrictModel):
    name: str = Field(min_length=1)
    instance_id: str | None = None
    environment: str | None = None
    attributes: dict[str, str] = Field(default_factory=dict)


class FileLogConfig(_StrictModel):
    """固定文件日志配置；``path`` 是日志基准路径，按日期轮转写入。"""

    path: str = Field(min_length=1)
    rotation: str = Field(default="daily")
    max_bytes: int = Field(default=10 * 1024 * 1024, gt=0)
    backup_count: int = Field(default=5, ge=0)


class LoggingConfig(_StrictModel):
    """structlog 输出约定；``options`` 透传给 ``structlog.configure``。"""

    enabled: bool = True
    level: str = "INFO"
    handler_name: str = "bluecrystal"
    file: FileLogConfig | None = None
    options: dict[str, Any] = Field(default_factory=dict)


class MetricsConfig(_StrictModel):
    """Prometheus backend 配置。"""

    enabled: bool = True
    provider: str = "prometheus"
    subsystem: str = ""
    provider_options: dict[str, Any] = Field(default_factory=dict)


class TracingConfig(_StrictModel):
    """OpenTelemetry provider、exporter 与 span processor 配置。"""

    enabled: bool = True
    provider: str = "opentelemetry"
    exporter: str = "otlp_grpc"
    sample_rate: float = Field(default=0.001, ge=0, le=1)
    provider_options: dict[str, Any] = Field(default_factory=dict)
    exporter_options: dict[str, Any] = Field(default_factory=dict)
    processor_options: dict[str, Any] = Field(default_factory=dict)


class AuditConfig(_StrictModel):
    """审计存储配置；SQLite 是自研能力的默认实现。"""

    enabled: bool = False
    store: str = "sqlite"
    options: dict[str, Any] = Field(default_factory=dict)


class StatusConfig(_StrictModel):
    """运行状态快照能力配置。"""

    enabled: bool = True


class InstrumentationOptions(_StrictModel):
    """单个 instrumentation 的启停状态和第三方参数。"""

    enabled: bool = True
    options: dict[str, Any] = Field(default_factory=dict)


class InstrumentationConfig(RootModel[dict[str, InstrumentationOptions]]):
    """按名称保存可扩展的 instrumentation 配置集合。"""

    def get_options(self, name: str) -> InstrumentationOptions:
        """返回指定组件配置；未声明时使用启用的空配置。"""
        return self.root.get(name, InstrumentationOptions())


class ObservabilityConfig(_StrictModel):
    """运行时唯一可信的可观测性配置对象。"""

    service: ServiceConfig
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    metrics: MetricsConfig = Field(default_factory=MetricsConfig)
    tracing: TracingConfig = Field(default_factory=TracingConfig)
    audit: AuditConfig = Field(default_factory=AuditConfig)
    status: StatusConfig = Field(default_factory=StatusConfig)
    instrumentation: InstrumentationConfig = Field(
        default_factory=lambda: InstrumentationConfig(root={})
    )
