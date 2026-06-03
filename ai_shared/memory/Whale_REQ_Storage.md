# Whale_REQ_Storage

## 一、文件定位

本文件描述 Whale 存储层需求，包括 raw layer、standard layer、warehouse/mart layer 和 serving cache。

本文件不描述 source 协议采集，不描述 processing 的清洗算法。

## 二、上承项目级需求

| 项目级需求 | 本模块承接方式 |
|---|---|
| P-FR-002 | 承接实时链路 raw 写入和 serving cache |
| P-FR-004 | 承接标准层与数仓层存储 |
| P-DGR-001 | 承接 schema、版本与血缘治理 |

## 三、功能需求

### ST-FR-001 raw storage 原始层

- 类型：功能
- 优先级：高
- 需求描述：
  - storage 模块应提供 raw layer，用于保存原始状态、原始事件、原始时序和原始消息归档。
- 验收要点：
  - 支持按 source_id、device_id、node_key、timestamp 查询。
  - 支持原始消息或原始值可追溯。

### ST-FR-002 standard storage 标准层

- 类型：功能
- 优先级：高
- 需求描述：
  - storage 模块应提供 standard layer，用于保存清洗、标准化、质量处理后的数据。
- 验收要点：
  - 支持 schema version。
  - 支持质量码。
  - 支持时间基准对齐。

### ST-FR-003 warehouse / mart 层

- 类型：功能
- 优先级：高
- 需求描述：
  - storage 模块应支持面向分析、聚合、报表和服务的数据仓库与数据集市层。
- 验收要点：
  - 支持主题数据组织。
  - 支持查询和服务接口承接。

### ST-FR-004 serving cache

- 类型：功能
- 优先级：高
- 需求描述：
  - storage 模块应支持业务侧近实时 serving cache。
- 验收要点：
  - 支持按业务 key 更新和读取。
  - 支持 TTL、stale、乱序保护。

## 四、非功能需求

### ST-NFR-001 存储性能、TTL 与冷热分层

- 类型：非功能
- 优先级：高
- 需求描述：
  - storage 模块应支持高频写入、范围查询、TTL、归档和冷热分层。
- 验收要点：
  - 支持写入吞吐指标。
  - 支持时间范围查询。
  - 支持归档策略。

## 五、数据治理需求

### ST-DGR-001 存储 schema 与血缘

- 类型：数据治理
- 优先级：高
- 需求描述：
  - storage 模块应维护 raw、standard、warehouse/mart 的 schema、版本和血缘关系。
- 验收要点：
  - schema 变更可追踪。
  - raw 到 standard 的处理链路可追溯。

## 六、测试与验收需求

### ST-TEST-001 存储层 E2E

- 类型：测试与验收
- 优先级：高
- 需求描述：
  - storage 模块必须具备 raw、standard、warehouse/mart、serving cache 的写入和查询测试。
- 验收要点：
  - 验证写入、查询、TTL、归档、schema 兼容。

## 七、需求跟踪表

| 编号 | 上承需求 | 标题 | 类型 | 优先级 | 责任模块 | 验证等级 | 实现状态 | 实现证据 | 验收测试 | 差距 | 下一步 | 更新时间 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ST-FR-001 | P-FR-002 | raw storage 原始层 | FR | 高 | storage | L1/L4/L5 (L5: S3/MinIO verified; HDFS env-pending) | 真实适配器 L5 verified (S3/MinIO Round 5 E2E) | raw_archive: S3RawArchiveSink (boto3 put_object/head_bucket+gzip+JSONL+S3ManifestRepository) 独立于 TDengine (raw_archive=S3/MinIO, raw_index=TDengine)；LocalCompressedArchiveSink L4 通过；Round 5: S3/MinIO L5 E2E 3/3 tests passed (health/head_bucket, write gzip+readback, manifest record) + 2 integration passed；HDFS env-pending (skip) | test_storage_raw_archive (L1), test_storage_raw_index (L1), test_speed_layer_raw_archive_pipeline, test_whale_field_minimal_smoke, test_whale_l5_storage_e2e (L5: S3 3/3 passed, HDFS 1 skipped) | HDFS L5 env-pending；S3/MinIO L5 Round 6需Docker容器运行（Round 5已验证） | HDFS 真实环境 L5 E2E；S3/MinIO容器恢复后E2E回归 | 2026-06-03 (Round 6) |
| ST-FR-002 | P-FR-004 | standard storage 标准层 | FR | 高 | storage | L1/L4/L5 (L5: TDengine verified) | 真实适配器 L5 verified (TDengine Round 5 E2E; Round 6: TDengine容器未运行E2E degraded) | TdengineStandardizedSink 真实适配器 (全量 required fields: schema_version/quality_code/source_id/message_id/node_key/variable_key/value/value_type/observed_at/received_at + readback + TDengine REST API)；MemoryStandardizedSink L4 通过；Round 5: TDengine L5 E2E 3/3 tests passed (REST API write+readback 10 standardized fields, raw_index INSERT, health) + 2 integration passed | test_storage_standardized (L1), test_speed_layer_index_standardized_pipeline, test_whale_field_minimal_smoke, test_whale_l5_storage_e2e (L5: TDengine 3/3 passed) | Round 6: TDengine Docker容器未运行导致E2E返回failed(environment degraded)，Round 5 3/3 E2E verified | 恢复TDengine Docker容器后L5回归 | 2026-06-03 (Round 6) |
| ST-FR-003 | P-FR-005 | warehouse / mart 层 | FR | 高 | storage | L1 | 端口+stub | WarehouseSinkPort/InMemoryWarehouseSink + MartSinkPort/InMemoryMartSink；仅为端口定义+InMemory stub，非 L3 verified | 无专项测试 | 全部（无真实实现） | 实现 warehouse/mart 真实存储后端 | 2026-06-03 (Round 6) |
| ST-FR-004 | P-FR-002 | serving cache | FR | 高 | storage | L1/L4/L5 (L5: Redis verified) | 真实适配器 L5 verified (Redis Round 5 E2E) | RedisServingCache 真实适配器 (redis-py SETEX/GET/DEL/PING/TTL/stale/乱序保护) + InMemoryServingCache 双后端；E2E smoke L4 通过；L1 单测 9 tests passed；Round 5: Redis L5 E2E 4/4 tests passed (SET/GET/TTL, stale detection, out-of-order protection, health) + integration 1/1 passed | test_storage_serving_cache (9 tests L1), test_whale_field_minimal_smoke, test_whale_l5_storage_e2e (L5: Redis 4/4 passed) | 无 (L5 verified) | 持续维护 L5 回归 | 2026-06-03 (Round 6) |
| ST-NFR-001 | P-NFR-001 | 存储性能、TTL 与冷热分层 | NFR | 高 | storage | L1 | 端口已定义 | 归档/索引/标准化 sink 端口已定义，无性能/TTL/冷热分层验证 | 无专项性能测试 | 全部（无真实环境性能数据） | 真实环境下性能测试与冷热分层策略 | 2026-06-03 (Round 6) |
| ST-DGR-001 | P-DGR-001 | 存储 schema 与血缘 | DGR | 高 | storage | L2 | schema 已定义 | Envelope schema_version + raw/standard schema 已通过端口契约定义 | 无血缘追踪测试 | 完整 schema 演变和血缘追踪未实现 | 实现 schema registry + 血缘追踪 | 2026-06-03 (Round 6) |
| ST-TEST-001 | P-NFR-004 | 存储层 E2E | TEST | 高 | storage | L1/L4/L5 (L5: S3/TDengine/Redis all verified; HDFS env-pending) | 已通过 (L4: smoke 7/7; L5: S3 3/3 + TDengine 3/3 + Redis 4/4 all verified) | Round 3: E2E smoke 7/7 (L4)；4 个模块 L1 单测全部通过 (46 tests)；Kafka pipeline L5 E2E 4 tests passed (real Kafka->SpeedLayerWiring->local)；Round 5: S3/MinIO L5 E2E 3/3 (health/write+readback+gzip/manifest)，TDengine L5 E2E 3/3 (write+readback 10 fields/raw_index/health)，Redis L5 E2E 4/4 (SET/GET/TTL/stale/out-of-order/health)；120 tests passed, 0 failures, 4 skipped (HDFS/Pulsar/Flink env-pending) | test_storage_serving_cache (9), test_storage_raw_archive, test_storage_raw_index, test_storage_standardized (46 total L1), test_whale_field_minimal_smoke (L4: 7), test_whale_l5_kafka_pipeline_e2e (L5: 4), test_whale_l5_storage_e2e (L5: 10 all passed), run_whale_l5_external_dependency_probe.sh (multi-level) | HDFS L5 env-pending；warehouse/mart 无测试 | HDFS 真实环境 L5 E2E + warehouse/mart 实现与测试 | 2026-06-03 (Round 6) |
