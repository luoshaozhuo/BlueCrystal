# ADR-20260604-017-model-asset-simulation-metadata-boundary

## Status

Accepted

## Keywords

- model_asset, simulation, metadata, boundary, Dolphin, raw_archive, PostgreSQL, TDengine, SimulationResultTimeSeriesSinkPort, SimulationImportManifest

## Context

Whale 需要承接仿真模型资产（FAST、OpenFAST、WindFarm、Bladed、Simulink 等）和仿真结果的元数据管理与文件归档。仿真计算的深度解析和引擎调度由独立的 Dolphin 组件负责，Whale 只管理元数据、文件归档和结果存储端口。

仿真结果包含大规模时序数据（多通道浮点数组），与实时采集的标准化点值在 schema、访问模式和生命周期上差异显著，不应混入同一张标准化点值表。

## Decision

1. `src/whale/model_asset/` 定位为仿真资产元数据管理与导入包，不作为独立顶级模块：
   - models.py：定义 SimulationFileType 枚举、ModelAssetImportRequest/SimulationCaseImportRequest/SimulationResultImportRequest/SimulationImportManifest DTO。
   - detector.py：SimulationFileTypeDetector 根据文件扩展名和 magic bytes 检测仿真文件类型（.fst/.fast/.fstf->FAST，.wnd/.wfp->WINDFARM，.prj/.bld->BLADED，.slx/.mdl->SIMULINK 等）。
   - archive.py：SimulationArchiveService 复用 `src/whale/storage/raw_archive.py` 的 FileArchiveSinkPort，将仿真文件归档至 raw_archive。
   - repository.py：ModelAssetRepository 对 PostgreSQL 进行四表 CRUD 操作。
   - service.py：ModelAssetImportService 编排 detect->archive->repository 导入流程。

2. 四表 ORM 模型 (`src/whale/shared/persistence/orm/model_asset.py`)：
   - ModelAsset：model_code (unique)、model_name、model_type、asset_scope、version、parent_model_code (self-ref FK)、owner_asset_code、status、metadata。
   - SimulationCase：case_code (unique)、case_name、model_code (FK->ModelAsset)、case_type、input_file_uri、parameters、scenario、created_by。
   - SimulationResult：result_code (unique)、case_code (FK->SimulationCase)、result_type、result_file_uri、time_series_backend、time_series_ref、summary、metrics、status。
   - SimulationArtifact：artifact_code、model_asset_id (FK->ModelAsset)、artifact_type、file_uri、checksum_sha256、file_size。
   - 唯一约束：model_code、case_code、result_code。FK 链：SimulationCase->ModelAsset，SimulationResult->SimulationCase，SimulationArtifact->ModelAsset。parent_model_code 自引用 FK。

3. 仿真结果时序存储端口 (`src/whale/storage/simulation_result.py`)：
   - SimulationResultTimeSeriesSinkPort：定义仿真结果时序数据的写入端口。
   - InMemorySimulationResultTimeSeriesSink：用于 P1 开发期验证。
   - TdengineSimulationResultTimeSeriesSink：真实 REST API adapter（Round C: 已从 contract-only 升级为真实 TDengine REST API write()/readback()），当前环境 taosAdapter 不可用（P5 集成测试 4 FAIL, MISSING_ENVIRONMENT）。正确行为：连接失败时不抛异常，write() 返回 False，readback() 返回 []。
   - 仿真结果时序数据不进入标准化点值表（TdengineStandardizedSink），也不经过 speed_layer preprocessing pipeline。

4. Alembic migration (`alembic/versions/20260527_000004_add_model_asset_tables.py`)：
   - upgrade()：按 FK 依赖顺序创建四表（ModelAsset -> SimulationCase -> SimulationResult -> SimulationArtifact）。
   - downgrade()：按反向顺序删除四表。

5. Whale 与 Dolphin 边界：
   - Whale 管理 model_asset/simulation_case/simulation_result 元数据与文件归档。
   - Dolphin 负责仿真计算与深度解析（如 FAST linearization 分析、Campbell 图等）。
   - 仿真结果时序数据由 Whale storage.simulation_result 端口写入 TDengine。
   - 仿真时序结果不进入实时 state view（Redis serving cache）。
   - 文件本体走 raw_archive（S3/Local）；PostgreSQL 仅存 URI/checksum/metadata。

## Consequences

- model_asset 包不依赖 Dolphin 或 simulation engine，运行时无 Dolphin import。
- 仿真文件类型检测基于表面特征（文件扩展名），不执行深度解析（深度解析归 Dolphin）。
- 四表 ORM 当前通过 SQLite :memory: 验证；PostgreSQL FK/并发/索引真实行为未验证（MISSING_ENVIRONMENT）。
- TDengine 仿真结果 sink 已实现为真实 REST API adapter（Round C），当前环境 taosAdapter 不可用导致 P5 集成测试 FAIL（MISSING_ENVIRONMENT，非代码缺陷）。
- 仿真结果时序数据与实时采集数据物理隔离，避免 schema 混淆和性能互扰。
- simulation_result.py 与 waveform.py 同为真实 REST API adapter（Round C: 均已从 contract-only 升级），当前环境 TDengine taosAdapter 不可用致 P5 集成测试 FAIL。未来可统一替换底层时序存储。

## Rejected Options

- 将模型资产表合并入 ingest 运行库 schema：模型资产生命周期独立于采集任务，合并将导致 schema 耦合和迁移冲突。
- 将仿真结果时序数据写入 TdengineStandardizedSink 同一张表：schema 不匹配（10 required fields vs. multi-channel float array），写入模式冲突。
- 在 model_asset 中实现 Dolphin 仿真引擎调度：仿真引擎调度是 Dolphin 职责，Whale 不应跨组件。
- 将仿真结果直接存入 PostgreSQL BLOB：大规模时序数据不适合关系型存储，应使用 TDengine 或文件存储。

## Related Files

- `src/whale/model_asset/__init__.py`
- `src/whale/model_asset/models.py`
- `src/whale/model_asset/detector.py`
- `src/whale/model_asset/archive.py`
- `src/whale/model_asset/repository.py`
- `src/whale/model_asset/service.py`
- `src/whale/shared/persistence/orm/model_asset.py`
- `src/whale/storage/simulation_result.py`
- `alembic/versions/20260527_000004_add_model_asset_tables.py`
- `tests/unit/test_model_asset_models.py`
- `tests/unit/test_model_asset_detector.py`
- `tests/unit/test_model_asset_repository.py`
- `tests/unit/test_model_asset_service.py`
- `tests/unit/test_storage_simulation_result.py`
- `tests/integration/test_storage_simulation_result_tdengine_integration.py` (Round C: 5 tests, 4 FAIL MISSING_ENVIRONMENT)
- `tests/integration/test_model_asset_postgres_integration.py` (Round C: 16 tests NOT_RUN, MISSING_ENVIRONMENT)
- `tests/unit/shared/persistence/test_model_asset_orm.py`
- `tests/integration/test_model_asset_integration.py`
- `tests/integration/test_model_asset_alembic_migration.py`

## Supersedes / Superseded By

无。本 ADR 为新增边界决策，不替代已有 ADR。
