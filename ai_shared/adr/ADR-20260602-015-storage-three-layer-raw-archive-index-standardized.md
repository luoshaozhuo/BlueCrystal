# ADR-20260602-015-storage-three-layer-raw-archive-index-standardized

## Status

Accepted

## Keywords

- storage, raw_archive, raw_index, standardized, TDengine, HDFS, Object Storage, warehouse, mart, serving_cache

## Context

Whale 存储层需要分层保存不同粒度和用途的数据。业界常见的能源数据平台分层包括：
- raw archive：原始数据归档（压缩文件，用于长期留存和回溯）。
- raw index：带时间索引的原始数据（支持按时间范围快速查询原始值）。
- standardized：清洗和标准化后的数据（统一 schema、质量码、时间基准对齐）。

TDengine 作为时序数据库擅长时序索引查询，但不适合存储大块压缩归档文件。HDFS/Object Storage 适合归档但不适合毫秒级时序查询。

## Decision

1. `src/whale/storage/` 实现三层存储分层：
   - raw_archive.py：压缩文件归档接口（FileArchiveSinkPort），提供本地压缩（LocalCompressedArchiveSink）、HDFS（HdfsArchiveSinkAdapter）和 Object Storage（ObjectStorageArchiveSinkAdapter）。ManifestRepositoryPort 管理归档清单。
   - raw_index.py：TDengine 时序索引（TdengineRawIndexSink），MemoryRawIndexSink 用于开发测试。
   - standardized.py：清洗后标准数据（TdengineStandardizedSink），MemoryStandardizedSink 用于开发测试。
2. raw_archive 使用压缩文件（HDFS/Object Storage），**不使用 TDengine** 做归档存储。
3. raw_index 和 standardized 使用 TDengine（时序数据库），支持可替换的端口抽象。
4. warehouse.py 和 mart.py 当前仅定义了端口接口（WarehouseSinkPort/MartSinkPort）和 InMemory stub，不标为 L3 verified。
5. serving_cache.py 定义 ServingCachePort 和 InMemoryServingCache。
6. HDFS/S3/TDengine 真实环境当前标注 environment-pending。

## Consequences

- 分层边界清晰：raw_archive 用文件归档，raw_index/standardized 用时序 DB。
- 端口抽象允许未来替换底层存储（如将 TDengine 替换为 TimescaleDB）。
- warehouse/mart 标记为端口+stub，避免高估实现进度。
- 当前全部通过 InMemory sink 验证端口契约和 pipeline 逻辑。

## Rejected Options

- 全部使用 TDengine：归档文件存入 TDengine 性能差且不符合其设计目标。
- 全部使用文件存储：时序查询效率低，无法满足近实时查询需求。
- raw_index 和 standardized 合并为一层：二者数据质量不同，schema 不同，生命周期不同。

## Related Files

- `src/whale/storage/raw_archive.py`
- `src/whale/storage/raw_index.py`
- `src/whale/storage/standardized.py`
- `src/whale/storage/warehouse.py`
- `src/whale/storage/mart.py`
- `src/whale/storage/serving_cache.py`
- `tests/unit/test_storage_raw_archive.py`
- `tests/unit/test_storage_raw_index.py`
- `tests/unit/test_storage_standardized.py`
