"""OpenTelemetry Trace backend 的创建与生命周期实现。"""

from __future__ import annotations

from collections.abc import Mapping
from contextlib import AbstractContextManager
from typing import Any, cast

from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
    SpanExporter,
)
from opentelemetry.sdk.trace.sampling import TraceIdRatioBased
from opentelemetry.trace import Span, Tracer
from opentelemetry.util.types import AttributeValue

from ..config import ServiceConfig, TracingConfig


class TracingBackend:
    """持有独立 TracerProvider，并负责 exporter 生命周期。"""

    def __init__(self, service: ServiceConfig, config: TracingConfig) -> None:
        """按配置构造 OTel provider，不写入进程全局 provider。"""
        if config.provider != "opentelemetry":
            raise ValueError(f"tracing.provider: unsupported provider {config.provider!r}")
        controlled = {"resource", "sampler"}
        conflict = controlled.intersection(config.provider_options)
        if conflict:
            raise ValueError(
                "tracing.provider_options conflicts with runtime-controlled keys: "
                + ", ".join(sorted(conflict))
            )
        resource_attributes: dict[str, AttributeValue] = {
            "service.name": service.name,
            **service.attributes,
        }
        if service.instance_id:
            resource_attributes["service.instance.id"] = service.instance_id
        if service.environment:
            resource_attributes["deployment.environment.name"] = service.environment
        self.provider = TracerProvider(
            resource=Resource.create(resource_attributes),
            sampler=TraceIdRatioBased(config.sample_rate),
            **config.provider_options,
        )
        exporter: SpanExporter | None
        if config.exporter == "otlp_grpc":
            exporter = cast(Any, OTLPSpanExporter)(**config.exporter_options)
        elif config.exporter == "console":
            exporter = cast(Any, ConsoleSpanExporter)(**config.exporter_options)
        elif config.exporter == "none":
            exporter = None
        else:
            raise ValueError(f"tracing.exporter: unsupported exporter {config.exporter!r}")
        if exporter is not None:
            self.provider.add_span_processor(BatchSpanProcessor(exporter))
        self.tracer: Tracer = self.provider.get_tracer("observability")

    def span(
        self,
        name: str,
        *,
        attributes: Mapping[str, object] | None = None,
    ) -> AbstractContextManager[Span]:
        """创建当前 backend 的 span 作用域。"""
        normalized = (
            {key: _attribute_value(value) for key, value in attributes.items()}
            if attributes
            else None
        )
        return self.tracer.start_as_current_span(name, attributes=normalized)

    def close(self) -> None:
        """刷新并关闭 span processors。"""
        self.provider.shutdown()


def _attribute_value(value: object) -> AttributeValue:
    """把应用扩展属性收敛为 OTel 支持的低风险标量。"""
    if isinstance(value, (str, bool, int, float)):
        return value
    return repr(value)
