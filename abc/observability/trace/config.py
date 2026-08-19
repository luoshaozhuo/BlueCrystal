from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from .policy import TracePolicy
from .sampler import BlueCrystalSampler
def configure_trace(*,service_name:str,policy:TracePolicy,otlp_endpoint:str="http://localhost:4317") -> TracerProvider:
    provider=TracerProvider(sampler=BlueCrystalSampler(policy),resource=Resource.create({"service.name":service_name}))
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=otlp_endpoint,insecure=otlp_endpoint.startswith("http://"))))
    trace.set_tracer_provider(provider); return provider
