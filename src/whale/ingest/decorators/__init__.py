"""Decorator-style port wrappers for ingest crosscutting concerns."""

from whale.ingest.decorators.source_acquisition import (
    AuditedSourceAcquisitionPort,
    AuthorizedSourceAcquisitionPort,
    DebugSourceAcquisitionPort,
    LoggingSourceAcquisitionPort,
    RetryingSourceAcquisitionPort,
)
from whale.ingest.decorators.state_cache import (
    AuditedStateCachePort,
    DebugStateCachePort,
    LoggingStateCachePort,
    MetricsStateCachePort,
)

__all__ = [
    "AuditedSourceAcquisitionPort",
    "AuditedStateCachePort",
    "AuthorizedSourceAcquisitionPort",
    "DebugSourceAcquisitionPort",
    "DebugStateCachePort",
    "LoggingSourceAcquisitionPort",
    "LoggingStateCachePort",
    "MetricsStateCachePort",
    "RetryingSourceAcquisitionPort",
]

