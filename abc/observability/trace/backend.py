"""OpenTelemetry Trace backend 的创建与生命周期实现。"""

from __future__ import annotations

import sys
from collections.abc import Mapping
from contextlib import AbstractContextManager
from typing import Any, cast

from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
    SimpleSpanProcessor,
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
        
        self.tracer_provider = TracerProvider(
            resource=Resource.create(resource_attributes),
            sampler=TraceIdRatioBased(config.sample_rate),
            **config.provider_options,
        )
        # ``provider`` 是既有属性；FastAPI adapter 使用语义更明确的公开名称。
        self.provider = self.tracer_provider

        if config.exporter == "otlp_grpc":
            exporter: SpanExporter = cast(Any, OTLPSpanExporter)(**config.exporter_options)
            if "span_exporter" in config.processor_options:
                raise ValueError(
                    "tracing.processor_options conflicts with: span_exporter"
                )
            processor = BatchSpanProcessor(
                exporter,
                **config.processor_options,
            )
        elif config.exporter == "console":
            if config.processor_options:
                raise ValueError(
                    "tracing.processor_options is only supported by otlp_grpc"
                )
            exporter: SpanExporter = cast(Any, ConsoleSpanExporter)(out=sys.stdout, **config.exporter_options)
            processor = SimpleSpanProcessor(exporter)
        else:
            raise ValueError(f"tracing.exporter: unsupported exporter {config.exporter!r}")
        
        self.tracer_provider.add_span_processor(processor)
        self.tracer: Tracer = self.tracer_provider.get_tracer("observability")

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
        # 用了 BatchSpanProcessor（见 backend.py:53 一段），它会先入队再异步发。
        # 因此在关闭 provider 前，需要调用 shutdown 确保所有 span 都被导出。
        self.tracer_provider.shutdown()


def _attribute_value(value: object) -> AttributeValue:
    """把应用扩展属性收敛为 OTel 支持的低风险标量。"""
    if isinstance(value, (str, bool, int, float)):
        return value
    return repr(value)
