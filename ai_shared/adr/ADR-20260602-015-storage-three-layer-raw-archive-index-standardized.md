# ADR-20260602-015-storage-three-layer-raw-archive-index-standardized

## Status

Accepted (v5: Round 3 — docker-compose.p5.yml 最小 P5 编排、start/stop/diagnose/regression 脚本、.env.p5.example 环境变量模板)

## Keywords

- storage, raw_archive, raw_index, standardized, TDengine, HDFS, Object Storage, warehouse, mart, serving_cache, waveform, simulation_result, S3 env var, TDengine REST path

## Context

Whale 存储层需要分层保存不同粒度和用途的数据。业界常见的能源数据平台分层包括：
- raw archive：原始数据归档（压缩文件，用于长期留存和回溯）。
- raw index：带时间索引的原始数据（支持按时间范围快速查询原始值）。
- standardized：清洗和标准化后的数据（统一 schema、质量码、时间基准对齐）。

TDengine 作为时序数据库擅长时序索引查询，但不适合存储大块压缩归档文件。HDFS/Object Storage 适合归档但不适合毫秒级时序查询。

Round 2 补录（2026-06-04）：Round 1 引入的 waveform/simulation_result TDengine REST API adapter 和 S3 raw_archive 在缺失环境变量配置时产生无必要的 FAIL。需要在配置回退、多路径探测和优雅降级方面做出决策。

Round 3 补录（2026-06-04）：P5 外部依赖（PostgreSQL/Redis/Kafka/MinIO/TDengine）的本地拉启、诊断和回归需要统一的最小化编排和脚本体系。现有 docker-compose.whale-l5.yaml 面向全系统场景，缺少仅包含 5 依赖的最小编排和对应的拉启/停止/诊断/回归标准化脚本。

## Decision

1. `src/whale/storage/` 实现三层存储分层：
   - raw_archive.py：压缩文件归档接口（FileArchiveSinkPort），提供本地压缩（LocalCompressedArchiveSink）、HDFS（HdfsArchiveSinkAdapter）和 Object Storage（ObjectStorageArchiveSinkAdapter）。ManifestRepositoryPort 管理归档清单。
   - raw_index.py：TDengine 时序索引（TdengineRawIndexSink），MemoryRawIndexSink 用于开发测试。
   - standardized.py：清洗后标准数据（TdengineStandardizedSink），MemoryStandardizedSink 用于开发测试。
2. raw_archive 使用压缩文件（HDFS/Object Storage），**不使用 TDengine** 做归档存储。
3. raw_index 和 standardized 使用 TDengine（时序数据库），支持可替换的端口抽象。
4. warehouse.py 和 mart.py 当前仅定义了端口接口（WarehouseSinkPort/MartSinkPort）和 InMemory stub，不标为 P4 verified。
5. serving_cache.py 定义 ServingCachePort 和 InMemoryServingCache。
6. HDFS/S3/TDengine 真实环境当前标注 environment-pending。
7. waveform.py 定义 StandardizedWaveformSinkPort + InMemoryStandardizedWaveformSink + TdengineStandardizedWaveformSink（Round C: 已从 contract-only 升级为真实 REST API adapter，实现 write()/readback() 通过 TDengine REST API）。
8. simulation_result.py 定义 SimulationResultTimeSeriesSinkPort + InMemorySimulationResultTimeSeriesSink + TdengineSimulationResultTimeSeriesSink（Round C: 已从 contract-only 升级为真实 REST API adapter，实现 write()/readback() 通过 TDengine REST API）。
9. (Round 2) TDengine REST API 路径支持 WHALE_TDENGINE_REST_PATH 环境变量覆盖（默认 /rest/sql），waveform 和 simulation_result sink 增加 _check_rest_api_alive() 方法，依次探测主路径和备选路径 /rest/sqlt，确保不同 TDengine 版本/部署的兼容性。
10. (Round 2) S3/MinIO raw_archive S3RawArchiveSink 支持 WHALE_S3_ENDPOINT_URL、WHALE_S3_BUCKET、WHALE_S3_REGION、WHALE_S3_ACCESS_KEY、WHALE_S3_SECRET_KEY、WHALE_S3_ADDRESSING_STYLE 环境变量回退，参数为空时自动读取对应环境变量。
11. (Round 2) 优雅降级模式统一：TDengine 不可达时 write() 返回 False、readback() 返回 []、health() 返回 False，不抛异常；P5 集成测试 skipif 使用 TCP + REST API SELECT 1 两阶段探测，区分 TCP 不可达和 REST API 不可达原因码。
12. (Round 2) P5 回归脚本 run_whale_p5_external_dependency_regression.sh 增加 S3 逐步骤输出、SUMMARY 行和 FAIL 时 exit 1；新增 diagnose_whale_p5_dependencies.sh 独立诊断脚本，逐项执行 TCP + TDengine REST path/SELECT 1 诊断。
13. (Round 3) docker-compose.p5.yml 作为最小 P5 本地编排，仅包含 PostgreSQL+Redis+Kafka/Redpanda+MinIO+TDengine+taosAdapter 5 个依赖服务，每个服务含 healthcheck 探活。区别于 docker-compose.whale-l5.yaml（全系统集成场景）。
14. (Round 3) start_whale_p5_dependencies.sh 作为 P5 依赖启动脚本，Docker 不可用时输出 NOT_RUN: MISSING_ENVIRONMENT 而非 FAIL。stop_whale_p5_dependencies.sh 作为对应停止/清理脚本。
15. (Round 3) .env.p5.example 作为 P5 环境变量模板，提供所有 5 依赖的连接参数示例，不含真实密钥。
16. (Round 3) diagnose_whale_p5_dependencies.sh 增强为覆盖 PostgreSQL/Redis/Kafka/S3/TDengine 全部 5 依赖的逐项诊断，每项执行 TCP connect + auth + minimal operation，输出脱敏且标 PASS/FAIL/NOT_RUN + reason。任一 FAIL -> exit 1，无 FAIL 但有 NOT_RUN -> exit 0。
17. (Round 3) run_whale_p5_external_dependency_regression.sh 增强为 5 个独立测试组（Kafka pipeline E2E、Storage E2E、TDengine waveform 集成、TDengine simulation_result 集成、PostgreSQL model_asset 集成），每组逐项输出、SUMMARY 行含 PASS 计数。FAIL 时 exit 1，无 FAIL 但有 NOT_RUN 时 exit 0。

## Consequences

- 分层边界清晰：raw_archive 用文件归档，raw_index/standardized 用时序 DB。
- 端口抽象允许未来替换底层存储（如将 TDengine 替换为 TimescaleDB）。
- warehouse/mart 标记为端口+stub，避免高估实现进度。
- 当前全部通过 InMemory sink 验证端口契约和 pipeline 逻辑。
- (Round 2) WHALE_TDENGINE_REST_PATH 和 WHALE_S3_* 环境变量回退使 adapter 可在无显式参数的环境下独立运行。
- (Round 2) _check_rest_api_alive() 多路径探测 + TCP+REST 两阶段 skipif 将环境缺失相关的 FAIL 准确归为 NOT_RUN，消除假阳性。
- (Round 2) Graceful degradation 模式（write() 返回 False / readback() 返回 []）确保 TDengine 不可达时不抛异常，调用方可安全处理降级路径。
- (Round 3) docker-compose.p5.yml + start/stop 脚本提供标准化 P5 环境拉起方式，消除"手动逐个启动每个依赖"的不确定性。
- (Round 3) diagnose + regression 脚本的 PASS/FAIL/NOT_RUN 统一分类和 exit code 规则，使环境缺失与代码缺陷可明确区分。
- (Round 3) .env.p5.example 提供单一环境变量来源，避免凭记忆或临时拼凑环境变量。

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
- `src/whale/storage/waveform.py` (StandardizedWaveformSinkPort + TdengineStandardizedWaveformSink 真实 REST API adapter，与 standardized.py 点值分离)
- `tests/unit/test_storage_waveform.py`
- `tests/integration/test_storage_waveform_tdengine_integration.py` (Round C: 4 tests; Round 2: TCP+REST 两阶段探测 skipif, 4 NOT_RUN MISSING_ENVIRONMENT)
- `src/whale/storage/simulation_result.py` (SimulationResultTimeSeriesSinkPort + TdengineSimulationResultTimeSeriesSink 真实 REST API adapter)
- `tests/unit/test_storage_simulation_result.py`
- `tests/integration/test_storage_simulation_result_tdengine_integration.py` (Round C: 5 tests; Round 2: TCP+REST 两阶段探测 skipif, 5 NOT_RUN MISSING_ENVIRONMENT)
- `scripts/run_whale_p5_external_dependency_regression.sh` (Round 2: S3 逐步骤输出/SUMMARY 行/FAIL 时 exit 1; Round 3: 5 测试组增强)
- `scripts/diagnose_whale_p5_dependencies.sh` (Round 2: 新增; Round 3: 5 依赖全覆盖 TCP+auth+minimal operation)
- `docker-compose.p5.yml` (Round 3: 最小 P5 编排 PG+Redis+Kafka/MinIO+TDengine+taosAdapter)
- `scripts/start_whale_p5_dependencies.sh` (Round 3: P5 依赖启动)
- `scripts/stop_whale_p5_dependencies.sh` (Round 3: P5 依赖停止/清理)
- `.env.p5.example` (Round 3: P5 环境变量模板)
