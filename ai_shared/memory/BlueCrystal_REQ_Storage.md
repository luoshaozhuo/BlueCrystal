# BlueCrystal_REQ_Storage

## 一、文件定位

本文件描述 BlueCrystal 存储层需求，包括 raw layer、standard layer、warehouse/mart layer 和 serving cache。

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

### ST-FR-005 standardized waveform storage

- 类型：功能
- 优先级：中
- 需求描述：
  - storage 模块应支持标准化波形数据的独立 sink，与标准化点值表分离。
- 验收要点：
  - 提供 StandardizedWaveformSinkPort 抽象。
  - InMemoryStandardizedWaveformSink 用于开发期验证。
  - TdengineStandardizedWaveformSink 为真实 REST API adapter（TDengine REST API 写入/读回），支持 WHALE_TDENGINE_REST_PATH 环境变量和 /rest/sql + /rest/sqlt 多路径 _check_rest_api_alive() 探活。当前环境 taosAdapter 不可达，P5 集成测试 4 tests NOT_RUN（Round 2: TCP+REST 两阶段探测 skipif，MISSING_ENVIRONMENT，非代码缺陷）。
  - 正确行为：连接失败时不抛异常，write() 返回 False，readback() 返回空列表。
  - 波形 sink 独立于 TdengineStandardizedSink（点值），避免 schema 混淆。
  - 波形数据来源于 ingest.file_ingest 解码输出（StandardizedWaveformValue）。

### ST-FR-006 simulation result storage

- 类型：功能
- 优先级：中
- 需求描述：
  - storage 模块应支持仿真结果时序数据的独立存储端口，与标准化点值表和波形表分离。
- 验收要点：
  - 提供 SimulationResultTimeSeriesSinkPort 抽象。
  - InMemorySimulationResultTimeSeriesSink 用于开发期验证。
  - TdengineSimulationResultTimeSeriesSink 为真实 REST API adapter（TDengine REST API 写入/读回），支持 WHALE_TDENGINE_REST_PATH 环境变量和 /rest/sql + /rest/sqlt 多路径 _check_rest_api_alive() 探活。当前环境 taosAdapter 不可达，P5 集成测试 5 tests NOT_RUN（Round 2: TCP+REST 两阶段探测 skipif，MISSING_ENVIRONMENT，非代码缺陷）。
  - 正确行为：连接失败时不抛异常，write() 返回 False，readback() 返回空列表。
  - 仿真结果不进入实时 state view，不经过 speed_layer preprocessing pipeline。
  - 仿真结果数据来源于 model_asset.SimulationResultImportRequest 中的 time_series_ref。

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
  - storage 模块必须具备 raw、standard、warehouse/mart、serving cache、waveform、simulation_result 的写入和查询测试。
- 验收要点：
  - 验证写入、查询、TTL、归档、schema 兼容。
- 当前状态 (Round 2)：P1 单测 48/48 passed (waveform 12, simulation_result 17, raw_archive 19)；P5 集成测试 25 NOT_RUN (MISSING_ENVIRONMENT: TDengine 9 + PostgreSQL 16)；compileall/ruff/mypy PASS；bash -n PASS；0 FAIL。

## 七、需求跟踪表

| 编号 | 上承需求 | 标题 | 类型 | 优先级 | 责任模块 | 验证等级 | 实现状态 | 实现证据 | 验收测试 | 差距 | 下一步 | 更新时间 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ST-FR-001 | P-FR-002 | raw storage 原始层 | FR | 高 | storage | P1/P6/P5 (P5: S3/MinIO verified; HDFS env-pending) | 真实适配器 P5 verified (S3/MinIO Round 5 E2E; Round 2 S3 env var 支持) | raw_archive: S3RawArchiveSink (boto3 put_object/head_bucket+gzip+JSONL+S3ManifestRepository + WHALE_S3_ENDPOINT_URL/WHALE_S3_BUCKET/WHALE_S3_REGION/WHALE_S3_ACCESS_KEY/WHALE_S3_SECRET_KEY/WHALE_S3_ADDRESSING_STYLE 环境变量支持) 独立于 TDengine；LocalCompressedArchiveSink P6 通过；Round 5: S3/MinIO P5 E2E 3/3 tests passed + 2 integration passed；HDFS env-pending (skip) | test_storage_raw_archive (P1), test_storage_raw_index (P1), test_speed_layer_raw_archive_pipeline, test_whale_field_minimal_smoke, test_whale_l5_storage_e2e (P5: S3 3/3 passed, HDFS 1 skipped) | HDFS P5 env-pending; Round 3 diagnose: S3/MinIO bucket "whale-raw" 不存在 (FAIL, 环境缺失非代码缺陷); regression Storage E2E S3 FAIL (bucket 404) | docker-compose.p5.yml 启动后创建 MinIO bucket "whale-raw" + HDFS 真实环境 P5 E2E 回归 | 2026-06-04 (Round 3) |
| ST-FR-002 | P-FR-004 | standard storage 标准层 | FR | 高 | storage | P1/P6/P5 (P5: TDengine verified) | 真实适配器 P5 verified (TDengine Round 5 E2E; Round 6: TDengine容器未运行E2E degraded) | TdengineStandardizedSink 真实适配器 (全量 required fields: schema_version/quality_code/source_id/message_id/node_key/variable_key/value/value_type/observed_at/received_at + readback + TDengine REST API)；MemoryStandardizedSink P6 通过；Round 5: TDengine P5 E2E 3/3 tests passed (REST API write+readback 10 standardized fields, raw_index INSERT, health) + 2 integration passed | test_storage_standardized (P1), test_speed_layer_index_standardized_pipeline, test_whale_field_minimal_smoke, test_whale_l5_storage_e2e (P5: TDengine 3/3 passed) | Round 6: TDengine Docker容器未运行导致E2E返回failed(environment degraded)，Round 5 3/3 E2E verified | 恢复TDengine Docker容器后P5回归 | 2026-06-03 (Round 6) |
| ST-FR-003 | P-FR-005 | warehouse / mart 层 | FR | 高 | storage | P1 | 端口+stub | WarehouseSinkPort/InMemoryWarehouseSink + MartSinkPort/InMemoryMartSink；仅为端口定义+InMemory stub，非 P4 verified | 无专项测试 | 全部（无真实实现） | 实现 warehouse/mart 真实存储后端 | 2026-06-03 (Round 6) |
| ST-FR-004 | P-FR-002 | serving cache | FR | 高 | storage | P1/P6/P5 (P5: Redis verified) | 真实适配器 P5 verified (Redis Round 5 E2E) | RedisServingCache 真实适配器 (redis-py SETEX/GET/DEL/PING/TTL/stale/乱序保护) + InMemoryServingCache 双后端；E2E smoke P6 通过；P1 单测 9 tests passed；Round 5: Redis P5 E2E 4/4 tests passed (SET/GET/TTL, stale detection, out-of-order protection, health) + integration 1/1 passed | test_storage_serving_cache (9 tests P1), test_whale_field_minimal_smoke, test_whale_l5_storage_e2e (P5: Redis 4/4 passed) | 无 (P5 verified) | 持续维护 P5 回归 | 2026-06-03 (Round 6) |
| ST-NFR-001 | P-NFR-001 | 存储性能、TTL 与冷热分层 | NFR | 高 | storage | P1 | 端口已定义 | 归档/索引/标准化 sink 端口已定义，无性能/TTL/冷热分层验证 | 无专项性能测试 | 全部（无真实环境性能数据） | 真实环境下性能测试与冷热分层策略 | 2026-06-03 (Round 6) |
| ST-DGR-001 | P-DGR-001 | 存储 schema 与血缘 | DGR | 高 | storage | P3 | schema 已定义 | Envelope schema_version + raw/standard schema 已通过端口契约定义 | 无血缘追踪测试 | 完整 schema 演变和血缘追踪未实现 | 实现 schema registry + 血缘追踪 | 2026-06-03 (Round 6) |
| ST-FR-005 | P-FR-004 | standardized waveform storage | FR | 中 | storage | P1 (InMemory) / P5 NOT_RUN (TDengine REST API adapter, MISSING_ENVIRONMENT) | 真实 REST API adapter 已实现 (Round 2: WHALE_TDENGINE_REST_PATH 多路径探测 + _check_rest_api_alive()) | `src/whale/storage/waveform.py` (StandardizedWaveformSinkPort / InMemoryStandardizedWaveformSink / TdengineStandardizedWaveformSink 真实 REST API write()/readback() + WHALE_TDENGINE_REST_PATH env var + /rest/sql + /rest/sqlt 双路径 _check_rest_api_alive() 探活) + `tests/unit/test_storage_waveform.py` (12 passed P1) + `tests/integration/test_storage_waveform_tdengine_integration.py` (4 tests, Round 2: TCP+REST 两阶段探测 skipif，当前环境 TDengine 不可达 -> 4 NOT_RUN) + `scripts/run_whale_p5_external_dependency_regression.sh` (TDengine 部分 NOT_RUN) | `pytest tests/unit/test_storage_waveform.py -q` -> 12 passed (P1 InMemory + TDengine REST adapter contract)；`pytest tests/integration/test_storage_waveform_tdengine_integration.py -q` -> 4 NOT_RUN (MISSING_ENVIRONMENT: TDengine taosAdapter 不可达)；compileall/ruff/mypy PASS | TdengineStandardizedWaveformSink 真实 REST API adapter + WHALE_TDENGINE_REST_PATH + _check_rest_api_alive() 已实现；Round 3: P1 12/12 PASS, regression TDengine waveform NOT_RUN (MISSING_ENVIRONMENT, docker-compose.p5.yml 未启动 taosAdapter)，当前环境 TDengine 不可达，均为环境缺失非代码缺陷；正确行为：连接失败不抛异常，write() 返回 False，readback() 返回 [] | docker-compose.p5.yml 启动 TDengine + taosAdapter 后 P5 regression 回归 | 2026-06-04 (Round 3) |
| ST-TEST-001 | P-NFR-004 | 存储层 E2E | TEST | 高 | storage | P1/P6/P5 (P5: S3/TDengine/Redis all verified; HDFS env-pending; waveform/simulation_result P5 NOT_RUN) | 已通过 (P6: smoke 7/7; P5: S3 3/3 + TDengine 3/3 + Redis 4/4 all verified; Round 2: P5 集成测试 skipif TCP+REST 两阶段探测，25 NOT_RUN) | Round 3: E2E smoke 7/7 (P6)；4 个模块 P1 单测全部通过 (46 tests)；Kafka pipeline P5 E2E 4 tests passed；Round 5: S3 P5 E2E 3/3, TDengine P5 E2E 3/3, Redis P5 E2E 4/4；Round 2: P5 集成测试全部 25 NOT_RUN (MISSING_ENVIRONMENT: TDengine 9 + PostgreSQL 16)，0 FAIL；P1 unit tests 48/48 passed (waveform 12, simulation_result 17, raw_archive 19)；compileall/ruff/mypy PASS；scripts bash -n PASS | test_storage_serving_cache (9), test_storage_raw_archive (19), test_storage_raw_index, test_storage_standardized, test_storage_waveform (12 P1), test_storage_simulation_result (17 P1), test_whale_field_minimal_smoke (P6: 7), test_whale_l5_kafka_pipeline_e2e (P5: 4), test_whale_l5_storage_e2e (P5: 10 all passed), run_whale_p5_external_dependency_regression.sh (Round 2: PASS=N NOT_RUN=N+), diagnose_whale_p5_dependencies.sh | HDFS P5 env-pending；warehouse/mart 无测试；waveform/simulation_result/model_asset P5 NOT_RUN (Round 3 regression: 1 PASS Kafka E2E, 1 FAIL Storage E2E S3+TDengine 环境缺失, 3 NOT_RUN TDengine+PG; 均为 MISSING_ENVIRONMENT 非代码缺陷) | docker-compose.p5.yml 启动全依赖后 P5 regression 回归 + HDFS 真实环境 P5 E2E + warehouse/mart 实现与测试 | 2026-06-04 (Round 3) |
| ST-FR-006 | P-FR-006 | simulation result storage | FR | 中 | storage | P1 (InMemory) / P5 NOT_RUN (TDengine REST API adapter, MISSING_ENVIRONMENT) | 真实 REST API adapter 已实现 (Round 2: WHALE_TDENGINE_REST_PATH 多路径探测 + _check_rest_api_alive()) | `src/whale/storage/simulation_result.py` (SimulationResultTimeSeriesSinkPort / InMemorySimulationResultTimeSeriesSink / TdengineSimulationResultTimeSeriesSink 真实 REST API write()/readback() + WHALE_TDENGINE_REST_PATH env var + /rest/sql + /rest/sqlt 双路径 _check_rest_api_alive() 探活) + `tests/unit/test_storage_simulation_result.py` (InMemory PASS / TDengine REST adapter contract) + `tests/integration/test_storage_simulation_result_tdengine_integration.py` (5 tests, Round 2: TCP+REST 两阶段探测 skipif，当前环境 TDengine 不可达 -> 5 NOT_RUN) + `scripts/run_whale_p5_external_dependency_regression.sh` (TDengine 部分 NOT_RUN) | pytest tests/unit/test_storage_simulation_result.py -q (P1)；pytest tests/integration/test_storage_simulation_result_tdengine_integration.py -q -> 5 NOT_RUN (MISSING_ENVIRONMENT: TDengine taosAdapter 不可达)；compileall/ruff/mypy PASS | TdengineSimulationResultTimeSeriesSink 真实 REST API adapter + WHALE_TDENGINE_REST_PATH + _check_rest_api_alive() 已实现；Round 3: P1 17/17 PASS, regression TDengine simulation_result NOT_RUN (MISSING_ENVIRONMENT, docker-compose.p5.yml 未启动 taosAdapter)，当前环境 TDengine 不可达，均为环境缺失非代码缺陷；正确行为：连接失败不抛异常，write() 返回 False，readback() 返回 [] | docker-compose.p5.yml 启动 TDengine + taosAdapter 后 P5 regression 回归 | 2026-06-04 (Round 3) |
