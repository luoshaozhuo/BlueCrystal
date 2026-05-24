"""Explicit ingest composition root for acquisition, latest-state caching, and source write/control."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from whale.ingest.adapters.source.modbus_source_acquisition_adapter import (
    ModbusSourceAcquisitionAdapter,
)
from whale.ingest.adapters.source.modbus_source_write_adapter import (
    ModbusSourceWriteAdapter,
)
from whale.ingest.adapters.source.opcua_source_acquisition_adapter import (
    OpcUaSourceAcquisitionAdapter,
)
from whale.ingest.adapters.source.opcua_source_write_adapter import (
    OpcUaSourceWriteAdapter,
)
from whale.ingest.adapters.source.static_source_acquisition_port_registry import (
    StaticSourceAcquisitionPortRegistry,
)
from whale.ingest.adapters.source.static_source_write_port_registry import (
    StaticSourceWritePortRegistry,
)
from whale.ingest.adapters.state.redis_source_state_cache import (
    RedisHashClient,
    RedisSourceStateCache,
    RedisSourceStateCacheSettings,
)
from whale.ingest.decorators import (
    AuditedSourceAcquisitionPort,
    AuditedStateCachePort,
    AuthorizedSourceAcquisitionPort,
    DebugSourceAcquisitionPort,
    DebugStateCachePort,
    LoggingSourceAcquisitionPort,
    LoggingStateCachePort,
    MetricsStateCachePort,
    RetryingSourceAcquisitionPort,
)
from whale.ingest.ports.source.source_acquisition_port import (
    SourceAcquisitionError,
    SourceAcquisitionPort,
)
from whale.ingest.ports.source.source_write_port import SourceWritePort
from whale.ingest.ports.source.source_acquisition_port_registry import (
    SourceAcquisitionPortRegistry,
)
from whale.ingest.ports.source.source_write_port_registry import (
    SourceWritePortRegistry,
)
from whale.ingest.ports.message import MessagePublisherPort
from whale.ingest.ports.state import SourceStateCachePort, SourceStateSnapshotReaderPort
from whale.ingest.usecases import SourceAcquisitionUseCase, StateSnapshotPublishUseCase
from whale.ingest.usecases.roles.polling_acquisition_role import PollingAcquisitionRole
from whale.ingest.usecases.roles.subscription_acquisition_role import (
    SubscriptionAcquisitionRole,
)
from whale.ingest.usecases.source_command_use_case import SourceCommandUseCase
from whale.shared.crosscutting.auth import (
    AccessDecision,
    AccessPolicyPort,
    Permission,
    Principal,
)
from whale.shared.crosscutting.compliance import AuditEvent, AuditEventSinkPort
from whale.shared.crosscutting.debug import DebugTraceContext, DebugTraceSinkPort
from whale.shared.crosscutting.observability import MetricsSinkPort, SensitiveDataMasker
from whale.shared.crosscutting.resilience import (
    BackoffPolicy,
    ClassifiedError,
    ErrorClassifier,
    RetryPolicy,
)

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class IngestAcquisitionComposition:
    """Resolved ingest acquisition object graph."""

    use_case: SourceAcquisitionUseCase
    acquisition_port: SourceAcquisitionPort
    state_cache_port: SourceStateCachePort
    snapshot_reader: SourceStateSnapshotReaderPort


@dataclass(frozen=True, slots=True)
class IngestWriteComposition:
    """Resolved ingest write/control object graph."""

    command_use_case: SourceCommandUseCase
    write_port: SourceWritePort
    write_port_registry: SourceWritePortRegistry
    acquisition_port_registry: SourceAcquisitionPortRegistry


def build_source_acquisition_composition(
    *,
    redis_settings: RedisSourceStateCacheSettings | None = None,
    redis_client: RedisHashClient | None = None,
    audit_sink: AuditEventSinkPort | None = None,
    metrics_sink: MetricsSinkPort | None = None,
    trace_sink: DebugTraceSinkPort | None = None,
    trace_context: DebugTraceContext | None = None,
    access_policy: AccessPolicyPort | None = None,
    principal: Principal | None = None,
    logger: logging.Logger | None = None,
) -> IngestAcquisitionComposition:
    """Build the ingest acquisition chain with explicit wrappers.

    Notes:
        - Local/test composition defaults to an allow-all access policy.
        - Production deployments should inject an explicit policy implementation.
        - Audit is best-effort by default through a no-op sink.
        - Single-read retry is capped at one attempt to avoid retry storms on
          top of PollingAcquisitionRole's periodic retry loop.
    """

    resolved_logger = logger or LOGGER
    resolved_audit_sink = audit_sink or _NullAuditEventSink()
    resolved_metrics_sink = metrics_sink or _NullMetricsSink()
    resolved_trace_sink = trace_sink or _NullDebugTraceSink()
    resolved_trace_context = trace_context or DebugTraceContext(enabled=False)
    resolved_access_policy = access_policy or _AllowAllAccessPolicy()
    resolved_principal = principal or Principal(
        principal_id="ingest",
        principal_type="service",
        roles=("ingest",),
    )

    raw_acquisition = OpcUaSourceAcquisitionAdapter()
    acquisition_port: SourceAcquisitionPort = RetryingSourceAcquisitionPort(
        inner=raw_acquisition,
        retry_policy=RetryPolicy(
            max_attempts=1,
            retryable_error_codes=frozenset({"source_read_timeout", "source_read_failed"}),
        ),
        backoff_policy=BackoffPolicy(initial_delay_seconds=0.0),
        error_classifier=_DefaultSourceErrorClassifier(),
    )
    acquisition_port = AuthorizedSourceAcquisitionPort(
        inner=acquisition_port,
        principal=resolved_principal,
        access_policy=resolved_access_policy,
    )
    acquisition_port = LoggingSourceAcquisitionPort(
        inner=acquisition_port,
        logger=resolved_logger,
        masker=SensitiveDataMasker(),
    )
    acquisition_port = AuditedSourceAcquisitionPort(
        inner=acquisition_port,
        audit_sink=resolved_audit_sink,
    )
    acquisition_port = DebugSourceAcquisitionPort(
        inner=acquisition_port,
        trace_context=resolved_trace_context,
        trace_sink=resolved_trace_sink,
    )

    raw_cache = RedisSourceStateCache(settings=redis_settings, client=redis_client)
    state_cache_port: SourceStateCachePort = MetricsStateCachePort(
        inner=raw_cache,
        metrics_sink=resolved_metrics_sink,
    )
    state_cache_port = LoggingStateCachePort(inner=state_cache_port, logger=resolved_logger)
    state_cache_port = AuditedStateCachePort(
        inner=state_cache_port,
        audit_sink=resolved_audit_sink,
    )
    state_cache_port = DebugStateCachePort(
        inner=state_cache_port,
        trace_context=resolved_trace_context,
        trace_sink=resolved_trace_sink,
    )

    use_case = SourceAcquisitionUseCase(
        polling_role=PollingAcquisitionRole(
            acquisition_port=acquisition_port,
            state_cache_port=state_cache_port,
        ),
        subscription_role=SubscriptionAcquisitionRole(
            acquisition_port=acquisition_port,
            state_cache_port=state_cache_port,
        ),
    )
    return IngestAcquisitionComposition(
        use_case=use_case,
        acquisition_port=acquisition_port,
        state_cache_port=state_cache_port,
        snapshot_reader=raw_cache,
    )


class _DefaultSourceErrorClassifier(ErrorClassifier):
    """Classify source acquisition exceptions into stable codes."""

    def classify(self, error: Exception) -> ClassifiedError:
        if isinstance(error, SourceAcquisitionError):
            return ClassifiedError(
                error_code=_normalize_error_code(str(error)),
                category="source",
                retryable=True,
                message=str(error) or type(error).__name__,
            )
        return ClassifiedError(
            error_code=_normalize_error_code(type(error).__name__),
            category="source",
            retryable=False,
            message=str(error) or type(error).__name__,
        )


class _AllowAllAccessPolicy(AccessPolicyPort):
    """Default access policy used by the composition root."""

    def evaluate(self, principal: Principal, permission: Permission) -> AccessDecision:
        del principal, permission
        return AccessDecision(allowed=True)


class _NullAuditEventSink(AuditEventSinkPort):
    """Default no-op audit sink."""

    def emit(self, event: AuditEvent) -> None:
        del event


class _NullMetricsSink(MetricsSinkPort):
    """Default no-op metrics sink."""

    def increment(self, metric_name: str, value: int = 1, **labels: str) -> None:
        del metric_name, value, labels

    def observe_duration(
        self,
        metric_name: str,
        duration_seconds: float,
        **labels: str,
    ) -> None:
        del metric_name, duration_seconds, labels


class _NullDebugTraceSink(DebugTraceSinkPort):
    """Default no-op debug trace sink."""

    def emit(self, event_name: str, context: DebugTraceContext, **payload: str) -> None:
        del event_name, context, payload


def _normalize_error_code(value: str) -> str:
    """Normalize one free-form error string into a stable code shape."""

    lowered = value.strip().lower()
    if "timeout" in lowered:
        return "source_read_timeout"
    if "unsupported" in lowered:
        return "subscription_unsupported"
    if "batch_mismatch" in lowered:
        return "batch_mismatch"
    if "protocol_error" in lowered:
        return "protocol_error"
    if "runner_not_available" in lowered:
        return "runner_not_available"
    if "read_failed" in lowered:
        return "source_read_failed"
    return lowered.replace(" ", "_").replace(":", "_") or "source_error"


def build_source_write_composition(
    *,
    write_port_registry: SourceWritePortRegistry | None = None,
    logger: logging.Logger | None = None,
) -> IngestWriteComposition:
    """Build the ingest write/control composition.

    Args:
        write_port_registry: Optional custom write port registry.
            Defaults to a static registry with OPC UA support only.
        logger: Optional logger instance.

    Returns:
        Resolved write object graph.

    Notes:
        - Default composition only supports OPC UA.
        - Write is DISABLED by default (WHALE_INGEST_SOURCE_WRITE_ENABLED must be set).
    """
    resolved_logger = logger or LOGGER

    # Build write ports
    opcua_write_port: SourceWritePort = OpcUaSourceWriteAdapter()
    modbus_write_port: SourceWritePort = ModbusSourceWriteAdapter()
    resolved_write_port_registry = write_port_registry or StaticSourceWritePortRegistry(
        ports_by_protocol={
            "opcua": opcua_write_port,
            "modbus_tcp": modbus_write_port,
            "modbustcp": modbus_write_port,
        },
    )

    # Build acquisition port registry (used by write composition for resolution)
    opcua_acquisition_port: SourceAcquisitionPort = OpcUaSourceAcquisitionAdapter()
    modbus_acquisition_port: SourceAcquisitionPort = ModbusSourceAcquisitionAdapter()
    resolved_acquisition_registry: SourceAcquisitionPortRegistry = StaticSourceAcquisitionPortRegistry(
        ports_by_protocol={
            "opcua": opcua_acquisition_port,
            "modbus_tcp": modbus_acquisition_port,
            "modbustcp": modbus_acquisition_port,
        },
    )

    command_use_case = SourceCommandUseCase(
        write_port_registry=resolved_write_port_registry,
    )

    resolved_logger.info(
        "Source write composition built: protocols=%s",
        sorted(["opcua", "modbus_tcp"]),
    )

    return IngestWriteComposition(
        command_use_case=command_use_case,
        write_port=opcua_write_port,
        write_port_registry=resolved_write_port_registry,
        acquisition_port_registry=resolved_acquisition_registry,
    )


def build_default_write_composition(
    logger: logging.Logger | None = None,
) -> IngestWriteComposition:
    """Build a default write composition with OPC UA support.

    Convenience wrapper for tests and simple deployments.
    """
    return build_source_write_composition(logger=logger)


@dataclass(frozen=True, slots=True)
class IngestPublishComposition:
    """Resolved state-snapshot publish object graph."""

    use_case: StateSnapshotPublishUseCase
    reader: SourceStateSnapshotReaderPort
    publisher: MessagePublisherPort


def build_state_snapshot_publish_composition(
    *,
    reader: SourceStateSnapshotReaderPort | None = None,
    publisher: MessagePublisherPort | None = None,
    station_id: str | None = None,
    redis_settings: RedisSourceStateCacheSettings | None = None,
    redis_client: RedisHashClient | None = None,
    logger: logging.Logger | None = None,
) -> IngestPublishComposition:
    """Build the state-snapshot publish object graph.

    Args:
        reader: Optional snapshot reader. Defaults to a new RedisSourceStateCache.
        publisher: Optional message publisher. Must be injected by the caller
            (KafkaMessagePublisher or test fake).
        station_id: Local station identifier. Defaults to the configured
            station_id from Redis settings.
        redis_settings: Redis settings used when creating a default reader.
        redis_client: Optional shared Redis client.
        logger: Optional logger instance.

    Returns:
        Resolved publish object graph.
    """
    resolved_logger = logger or LOGGER

    # Resolve snapshot reader (default: RedisSourceStateCache)
    resolved_reader = reader or RedisSourceStateCache(
        settings=redis_settings,
        client=redis_client,
    )

    # Publisher must be injected (no default — caller decides backend)
    if publisher is None:
        raise TypeError(
            "build_state_snapshot_publish_composition() missing required argument: "
            "'publisher'. Inject a MessagePublisherPort implementation "
            "(e.g. KafkaMessagePublisher, RedisStreamsMessagePublisher, "
            "or a test fake)."
        )

    # Resolve station_id from settings or argument
    if station_id is None and redis_settings is not None:
        station_id = redis_settings.station_id  # type: ignore[union-attr]
    resolved_station_id = station_id or "unknown-station"

    use_case = StateSnapshotPublishUseCase(
        reader=resolved_reader,
        publisher=publisher,
        station_id=resolved_station_id,
    )

    resolved_logger.info(
        "State-snapshot publish composition built: publisher=%s, station_id=%s",
        type(publisher).__name__,
        resolved_station_id,
    )

    return IngestPublishComposition(
        use_case=use_case,
        reader=resolved_reader,
        publisher=publisher,
    )
