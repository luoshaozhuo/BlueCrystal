# Whale_REQ_SpeedLayer

## 一、文件定位

本文件描述 Whale 速度层需求。速度层消费 message pipeline 的实时数据，写入 raw storage，并更新业务侧 serving cache。

本文件不描述 ingest 采集，不描述批处理层复杂重算。

## 二、上承项目级需求

| 项目级需求 | 本模块承接方式 |
|---|---|
| P-FR-002 | 承接实时链路中的消费、raw 写入和 serving cache 更新 |
| P-NFR-002 | 承接实时链路恢复和 offset 管理 |

## 三、功能需求

### SP-FR-001 消费 ingest 消息

- 类型：功能
- 优先级：高
- 需求描述：
  - speed layer 应从 message pipeline 消费 ingest 发布的实时消息。
- 验收要点：
  - 支持 consumer group。
  - 支持 offset 管理。
  - 支持消息 schema 校验。

### SP-FR-002 写入 raw storage

- 类型：功能
- 优先级：高
- 需求描述：
  - speed layer 应将实时消息写入 raw storage。
- 验收要点：
  - 支持幂等写入。
  - 支持失败重试。
  - 支持原始消息或原始状态保留。

### SP-FR-003 更新 serving cache

- 类型：功能
- 优先级：高
- 需求描述：
  - speed layer 应更新业务侧 serving cache，支撑近实时监视与业务查询。
- 验收要点：
  - 支持按 source/device/node 更新。
  - 支持 stale 和 TTL。
  - 支持乱序保护。

### SP-FR-004 实时轻处理

- 类型：功能
- 优先级：高
- 需求描述：
  - speed layer 应执行实时链路中的轻量去重、质量状态处理、时间戳校验和必要格式转换。
- 验收要点：
  - 支持重复消息识别。
  - 支持迟到或乱序数据策略。
  - 支持质量码透传。

## 四、非功能需求

### SP-NFR-001 近实时延迟与吞吐

- 类型：非功能
- 优先级：高
- 需求描述：
  - speed layer 应满足近实时消费、写 raw 和更新 serving cache 的时延要求。
- 验收要点：
  - 输出消费延迟、写入延迟、cache 更新延迟、consumer lag。

## 五、架构约束

### SP-AR-001 实时链路职责边界

- 类型：架构约束
- 优先级：高
- 需求描述：
  - speed layer 不承担复杂批处理、全量重算和数仓分层职责。
- 验收要点：
  - 复杂清洗、标准化和全量重算由 batch/processing 承担。

## 六、测试与验收需求

### SP-TEST-001 speed layer E2E

- 类型：测试与验收
- 优先级：高
- 需求描述：
  - speed layer 必须具备 message -> raw -> serving cache 的 E2E 测试。
- 验收要点：
  - 验证消费、幂等写入、cache 更新、失败恢复和 offset 管理。

## 七、需求跟踪表

| 编号 | 上承需求 | 标题 | 类型 | 优先级 | 责任模块 | 验证等级 | 实现状态 | 实现证据 | 验收测试 | 差距 | 下一步 | 更新时间 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| SP-FR-001 | P-FR-002 | 消费 ingest 消息 | FR | 高 | speed_layer | L4/L5 (L5: Kafka verified) | 已实现 | PipelineRunner/LocalPipelineRunner 通过 MessageSourcePort 消费；KafkaSourceAdapter.consume() REAL consumer.poll()；Kafka consumer group isolation L5 verified (test_whale_l5_kafka_pipeline_e2e, 4 tests)；Kafka real pub/consume L5 verified；Round 4: SpeedLayerWiring 支持 with_light_processor() builder 集成 LightProcessingPipeline (_LightFilteredSource wrapper)，6 L4 integration tests 通过；Round 5: 120 tests passed, 0 failures, 4 skipped (Pulsar/Flink/HDFS env-pending) | test_speed_layer_pipeline_runner (44 passed), test_speed_layer_raw_archive_pipeline, test_speed_layer_index_standardized_pipeline, test_whale_field_minimal_smoke, test_whale_l5_kafka_pipeline_e2e (L5: 4 tests), TestSpeedLayerWiringWithLightProcessor (6 tests L4: wiring builds/valid flow/dedup/out-of-order/quality_code/invalid->DLQ), run_whale_l5_external_dependency_probe.sh (multi-level) | Flink/Pulsar real 标记 environment-pending | Flink/Pulsar 真实环境验证 | 2026-06-03 (Round 6) |
| SP-FR-002 | P-FR-002 | 写入 raw storage | FR | 高 | speed_layer | L1/L4/L5 (L5: S3/MinIO verified; TDengine verified; HDFS env-pending) | 真实适配器 L5 verified (Round 5 E2E) | S3RawArchiveSink (boto3 put_object/head_bucket+gzip+JSONL+S3ManifestRepository) + TdengineRawIndexSink (INSERT STABLE TAGS SQL+REST API) 真实适配器 L1 verified；LocalCompressedArchiveSink + MemoryRawIndexSink L4 通过 (E2E smoke)；Round 5: S3/MinIO L5 E2E 3/3 tests passed (health/head_bucket, write gzip+readback, manifest record)，TDengine L5 E2E 3/3 tests passed (REST API write+readback, raw_index INSERT, health)；HDFS env-pending (skip) | test_storage_raw_archive (L1), test_storage_raw_index (L1), test_speed_layer_raw_archive_pipeline, test_speed_layer_index_standardized_pipeline, test_whale_field_minimal_smoke, test_whale_writer_failure_recovery, test_whale_writer_switchover, test_whale_l5_storage_e2e (L5: S3 3/TDengine 3 passed, HDFS 1 skipped) | HDFS L5 env-pending；Round 6: S3/TDengine Docker容器未运行导致E2E degraded（Round 5 L5 verified） | HDFS 真实环境 L5 E2E；S3/TDengine容器恢复后回归 | 2026-06-03 (Round 6) |
| SP-FR-003 | P-FR-002 | 更新 serving cache | FR | 高 | speed_layer | L1/L4/L5 (L5: Redis verified) | 真实适配器 L5 verified (Round 5 E2E) | RedisServingCache 真实适配器 (redis-py SETEX/GET/DEL/PING/TTL/stale/乱序保护) + InMemoryServingCache 双后端；E2E smoke 7/7 验证 serving cache 链路 (InMemory, L4)；SpeedLayerWiring.with_redis_cache() 组装真实后端就绪；L1 单测 9 tests passed；Round 5: Redis L5 E2E 4/4 tests passed (SET/GET/TTL, stale detection, out-of-order protection, health) + integration 1/1 passed | test_storage_serving_cache (9 tests L1), test_speed_layer_index_standardized_pipeline (serving_cache 部分), test_whale_field_minimal_smoke, test_whale_l5_storage_e2e (L5: Redis 4/4 tests passed) | 无 (L5 verified) | 持续维护 L5 回归 | 2026-06-03 (Round 6) |
| SP-FR-004 | P-FR-002 | 实时轻处理 | FR | 高 | speed_layer | L1/L4 (L5: no direct external dependency) | 已实现，L1+L4 integrated | LightProcessingPipeline 完整管线已实现：EnvelopeValidator (schema_version/message_type/items 校验)、MessageDeduplicator (message_id 幂等去重，OrderedDict LRU)、QualityCodePassThrough (质量码透传)、OutOfOrderGuard (observed_at 乱序保护 + grace period + DLQ 路由)、LightProcessingPipeline (编排器组合上述四个处理器)；26 L1 unit tests passed；Round 4: LightProcessingPipeline 通过 _LightFilteredSource wrapper 集成到 SpeedLayerWiring.with_light_processor() + build() 构建流程中，新增 6 L4 集成测试 (TestSpeedLayerWiringWithLightProcessor 全部通过)；Round 5: 120 tests total, 0 failures (light processor 无独立外部依赖，L5 不适用) | test_speed_layer_light_processor (26 tests L1), TestSpeedLayerWiringWithLightProcessor (6 tests L4): test_wiring_builds_with_light_processor/test_valid_message_flow/test_dedup_duplicate_message/test_out_of_order_message/test_quality_code_passthrough/test_invalid_message_to_dlq | L5 不适用（无独立外部依赖，L5 覆盖由 SP-FR-001/002/003 端到端管线承载） | 持续维护 L4 集成回归 | 2026-06-03 (Round 6) |
| SP-NFR-001 | P-NFR-001 | 近实时延迟与吞吐 | NFR | 高 | speed_layer | L1 | 端口已定义 | MetricsCollectorPort + InMemoryMetricsCollector | 无专项性能测试 | 消费延迟/写入延迟/consumer lag 未采集 | 真实环境下性能测试 | 2026-06-03 (Round 6) |
| SP-AR-001 | P-FR-002 | 实时链路职责边界 | AR | 高 | speed_layer | L3 | 已验证 | 分层正确性验证 CORRECT，speed_layer 不承担 batch/processing 复杂清洗 | import boundary 30 passed, 分层正确性检查 | 无 | 无 | 2026-06-03 (Round 6) |
| SP-TEST-001 | P-NFR-004 | speed layer E2E | TEST | 高 | speed_layer | L4/L5 (L5: Kafka/S3/TDengine/Redis all verified) | 已通过 | Round 3: Kafka E2E L5 verified (4 tests: real pub/consume + consumer group + SpeedLayerWiring + Kafka->local chain)；InMemory E2E (DLQ/replay 8 + index/standardized/serving_cache 4 + raw_archive 5, L4)；E2E smoke 7/7 (L4)；writer failure recovery 8/8 + switchover 8/8 (L4)；Round 5: S3/MinIO L5 verified (3/3 E2E: health/write+readback+gzip/manifest)，TDengine L5 verified (3/3 E2E: write+readback 10 fields/raw_index/health)，Redis L5 verified (4/4 E2E: SET/GET/TTL/stale/out-of-order/health)；120 tests passed, 0 failures, 4 skipped (HDFS/Pulsar/Flink env-pending) | test_speed_layer_dlq_replay, test_speed_layer_index_standardized_pipeline, test_speed_layer_raw_archive_pipeline, test_whale_field_minimal_smoke, test_whale_writer_failure_recovery, test_whale_writer_switchover, test_whale_l5_kafka_pipeline_e2e (L5: 4 tests), test_whale_l5_storage_e2e (L5: 10 tests all passed), run_whale_l5_external_dependency_probe.sh (multi-level) | HDFS/Pulsar/Flink 真实环境未覆盖 | HDFS/Pulsar/Flink 真实环境 E2E | 2026-06-03 (Round 6) |
