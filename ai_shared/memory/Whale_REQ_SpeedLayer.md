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
| SP-FR-001 | P-FR-002 | 消费 ingest 消息 | FR | 高 | speed_layer | P6/P5 (P5: Kafka verified, Round C P5 regression 2/2 PASS) | 已实现 | PipelineRunner/LocalPipelineRunner 通过 MessageSourcePort 消费；KafkaSourceAdapter.consume() REAL consumer.poll()；Kafka consumer group isolation P5 verified (test_whale_l5_kafka_pipeline_e2e, 4 tests)；Round 5: 120 tests passed, 0 failures, 4 skipped (Pulsar/Flink/HDFS env-pending)；Round C: P5 回归脚本 Kafka 2/2 PASS (probe/health check) | test_speed_layer_pipeline_runner (44 passed), test_whale_l5_kafka_pipeline_e2e (P5: 4 tests), run_whale_p5_external_dependency_regression.sh (Kafka 2/2 PASS) | Flink/Pulsar real 标记 environment-pending | Flink/Pulsar 真实环境验证 | 2026-06-04 (Round C) |
| SP-FR-002 | P-FR-002 | 写入 raw storage | FR | 高 | speed_layer | P1/P6/P5 (P5: S3/MinIO Round C FAIL, TDengine Round C FAIL, HDFS env-pending) | 真实适配器 P5 verified (Round 5 E2E)；Round C: S3/TDengine P5 回归 FAIL (MISSING_ENVIRONMENT) | S3RawArchiveSink + TdengineRawIndexSink 真实适配器已实现；Round 5: S3/MinIO P5 E2E 3/3 passed, TDengine P5 E2E 3/3 passed；Round C: P5 回归脚本 S3 2 FAIL (既有 boto3/MinIO API 问题), TDengine 4 FAIL (MISSING_ENVIRONMENT: taosAdapter 不可用)；HDFS env-pending | test_storage_raw_archive (P1), test_storage_raw_index (P1), test_whale_l5_storage_e2e (P5: Round 5 S3 3/TDengine 3 passed, HDFS 1 skipped), run_whale_p5_external_dependency_regression.sh (P5: S3 2 FAIL, TDengine 4 FAIL) | S3/TDengine P5 回归 FAIL (Round 3: S3/MinIO bucket "whale-raw" 不存在 404, TDengine taosAdapter 不可用, 均为 MISSING_ENVIRONMENT 非代码缺陷)；HDFS P5 env-pending | docker-compose.p5.yml 启动全依赖 + 创建 MinIO bucket "whale-raw" 后 P5 regression 回归 | 2026-06-04 (Round 3) |
| SP-FR-003 | P-FR-002 | 更新 serving cache | FR | 高 | speed_layer | P1/P6/P5 (P5: Redis verified, Round C P5 regression 2/2 PASS) | 真实适配器 P5 verified (Round 5 E2E)；Round C: P5 回归 Redis 2/2 PASS | RedisServingCache 真实适配器 (redis-py SETEX/GET/DEL/PING/TTL/stale/乱序保护) + InMemoryServingCache 双后端；Round 5: Redis P5 E2E 4/4 passed；Round C: P5 回归脚本 Redis 2/2 PASS (probe/health check) | test_storage_serving_cache (9 tests P1), test_whale_l5_storage_e2e (P5: Redis 4/4 passed), run_whale_p5_external_dependency_regression.sh (Redis 2/2 PASS) | 无 (P5 verified) | 持续维护 P5 回归 | 2026-06-04 (Round C) |
| SP-FR-004 | P-FR-002 | 实时轻处理 | FR | 高 | speed_layer | P1/P6 (P5: no direct external dependency); Round A: P1 PreprocessingPipeline; Round C: P5 waveform/simulation_result TDengine FAIL (MISSING_ENVIRONMENT) | 已实现，P1+P6 integrated；Round A: 固定 10 阶段 pipeline + OperatorRegistry 已实现；Round C: P5 回归 TDengine 4 FAIL (MISSING_ENVIRONMENT), Kafka/Redis 4 PASS | LightProcessingPipeline 完整管线已实现（26 P1 tests passed）；PreprocessingPipeline 固定 10 阶段 83 P1 tests PASSED；全量 165 tests PASSED；Round B: waveform sink 边界引用已定义；Round C: P5 回归脚本结果：Kafka 2/2 PASS, Redis 2/2 PASS, TDengine 4 FAIL (MISSING_ENVIRONMENT: taosAdapter 不可用，非代码缺陷), S3 2 FAIL (既有 boto3/MinIO API 问题) | test_speed_layer_light_processor, TestSpeedLayerWiringWithLightProcessor, test_speed_layer_preprocessing (83 tests), run_whale_p5_external_dependency_regression.sh (P5: 6 PASS/4 FAIL/1 NOT_RUN) | P5 TDengine waveform/simulation_result FAIL (Round 3: MISSING_ENVIRONMENT taosAdapter 不可用); S3/MinIO P5 FAIL (Round 3: bucket "whale-raw" 不存在 404, 均为环境缺失非代码缺陷) | docker-compose.p5.yml 启动 TDengine+taosAdapter + 创建 MinIO bucket 后 P5 regression 回归 | 2026-06-04 (Round 3) |
| SP-NFR-001 | P-NFR-001 | 近实时延迟与吞吐 | NFR | 高 | speed_layer | P1 | 端口已定义 | MetricsCollectorPort + InMemoryMetricsCollector | 无专项性能测试 | 消费延迟/写入延迟/consumer lag 未采集 | 真实环境下性能测试 | 2026-06-03 (Round 6) |
| SP-AR-001 | P-FR-002 | 实时链路职责边界 | AR | 高 | speed_layer | P4 | 已验证 | 分层正确性验证 CORRECT，speed_layer 不承担 batch/processing 复杂清洗 | import boundary 30 passed, 分层正确性检查 | 无 | 无 | 2026-06-03 (Round 6) |
| SP-TEST-001 | P-NFR-004 | speed layer E2E | TEST | 高 | speed_layer | P1/P6/P5 (P5: Kafka/Redis Round C PASS; S3/TDengine Round C FAIL; HDFS env-pending) | 已通过 (P1/P6)；P5 回归部分通过 (Kafka/Redis PASS, S3/TDengine FAIL) | Round 3: Kafka E2E P5 verified (4 tests)；Round 5: S3/TDengine/Redis P5 verified (10/10 E2E)；P1 165 tests passed (133 unit + 32 integration)；P6 smoke 7/7；Round C: P5 回归脚本结果 — Kafka 2/2 PASS, Redis 2/2 PASS, TDengine 4 FAIL (MISSING_ENVIRONMENT: taosAdapter 不可用), S3 2 FAIL (既有 boto3/MinIO API 问题), PostgreSQL 1 NOT_RUN；HDFS/Pulsar/Flink env-pending | test_speed_layer_dlq_replay, test_speed_layer_index_standardized_pipeline, test_speed_layer_raw_archive_pipeline, test_whale_l5_kafka_pipeline_e2e (P5: 4 tests), test_whale_l5_storage_e2e (P5: 10 tests all passed), test_speed_layer_preprocessing (83 tests), run_whale_p5_external_dependency_regression.sh (P5: 6 PASS/4 FAIL/1 NOT_RUN) | S3/TDengine P5 回归 FAIL (Round 3: regression 6 PASS Kafka+Redis, 4 FAIL S3+TDengine, 1 NOT_RUN PG; 均为 MISSING_ENVIRONMENT 非代码缺陷)；HDFS/Pulsar/Flink 真实环境未覆盖 | docker-compose.p5.yml 启动全依赖 + 创建 MinIO bucket 后 P5 regression 回归 + HDFS/Pulsar/Flink P5 验证 | 2026-06-04 (Round 3) |
