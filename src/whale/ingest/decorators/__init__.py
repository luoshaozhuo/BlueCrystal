"""装饰器模块。

为采集、写入、缓存等横切关注点提供装饰器封装。
"""

from whale.ingest.decorators.source_acquisition import (
    AuditedSourceAcquisitionPort,
    AuthorizedSourceAcquisitionPort,
    DebugSourceAcquisitionPort,
    LoggingSourceAcquisitionPort,
    RetryingSourceAcquisitionPort,
)
from whale.ingest.decorators.source_write import AuthorizedSourceWritePort
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
    "AuthorizedSourceWritePort",
    "DebugSourceAcquisitionPort",
    "DebugStateCachePort",
    "LoggingSourceAcquisitionPort",
    "LoggingStateCachePort",
    "MetricsStateCachePort",
    "RetryingSourceAcquisitionPort",
]

