"""Whale 数据底座存储层。

包含五层存储抽象：
- raw_archive: 不可变原始事实层（HDFS/Object Storage + 压缩文件）。
- raw_index: 原始时序索引层（TDengine，快速查询入口）。
- standardized: 标准时序层（TDengine，清洗后数据）。
- warehouse: 数据仓库层（面向主题分析）。
- mart: 数据集市层（面向业务服务的预聚合）。
- serving_cache: 业务侧近实时缓存层。

所有外部依赖（TDengine/HDFS/S3）标记 environment-pending，
提供 contract adapter 和配置校验，不硬编码 SDK 调用。
"""

from __future__ import annotations

from whale.storage.raw_archive import (
    FileArchiveSinkPort,
    HdfsArchiveSinkAdapter,
    InMemoryManifestRepository,
    LocalCompressedArchiveSink,
    ManifestRepositoryPort,
    S3ManifestRepository,
    S3RawArchiveSink,
)
from whale.storage.raw_index import (
    MemoryRawIndexSink,
    RawIndexSinkPort,
    TdengineRawIndexSink,
)
from whale.storage.standardized import (
    MemoryStandardizedSink,
    StandardizedTimeSeriesSinkPort,
    TdengineStandardizedSink,
)
from whale.storage.warehouse import (
    InMemoryWarehouseSink,
    WarehouseSinkPort,
)
from whale.storage.mart import (
    InMemoryMartSink,
    MartSinkPort,
)
from whale.storage.serving_cache import (
    InMemoryServingCache,
    RedisServingCache,
    ServingCachePort,
)

__all__ = [
    # raw_archive
    "FileArchiveSinkPort",
    "HdfsArchiveSinkAdapter",
    "InMemoryManifestRepository",
    "LocalCompressedArchiveSink",
    "ManifestRepositoryPort",
    "S3ManifestRepository",
    "S3RawArchiveSink",
    # raw_index
    "MemoryRawIndexSink",
    "RawIndexSinkPort",
    "TdengineRawIndexSink",
    # standardized
    "MemoryStandardizedSink",
    "StandardizedTimeSeriesSinkPort",
    "TdengineStandardizedSink",
    # warehouse
    "InMemoryWarehouseSink",
    "WarehouseSinkPort",
    # mart
    "InMemoryMartSink",
    "MartSinkPort",
    # serving_cache
    "InMemoryServingCache",
    "RedisServingCache",
    "ServingCachePort",
]
