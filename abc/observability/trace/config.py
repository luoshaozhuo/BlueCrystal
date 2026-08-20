"""OpenTelemetry Trace Provider 配置。"""

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from .policy import TracePolicy
from .sampler import BlueCrystalSampler


def configure_trace(
    *,
    service_name: str,
    policy: TracePolicy,
    otlp_endpoint: str = "http://localhost:4317",
) -> TracerProvider:
    """配置全局 OpenTelemetry Trace Provider。

    Args:
        service_name: OpenTelemetry 服务名。
        policy: Trace 策略。
        otlp_endpoint: OTLP gRPC Exporter 地址。

    Returns:
        已配置的 Trace Provider。
    """
    provider = TracerProvider(
        sampler=BlueCrystalSampler(policy),
        resource=Resource.create({"service.name": service_name}),
    )
    exporter = OTLPSpanExporter(
        endpoint=otlp_endpoint,
        insecure=otlp_endpoint.startswith("http://"),
    )
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    return provider
