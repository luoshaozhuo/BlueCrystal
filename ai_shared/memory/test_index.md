# Whale 测试索引

本文件是 Whale 项目唯一测试索引。不另建其他回归索引文件（如 `issue_regression_index.md`）。

初版为目录级完整、关键链路文件级。不追求全仓逐文件穷尽。

## 1. 文件定位

- 路径: `ai_shared/memory/test_index.md`
- 用途: 测试资产导航、回归测试索引、回归套件定义
- 受众: code-implementer、test-validator、project-steward
- 更新规则: 新增/删除测试文件或回归测试时必须更新

## 2. 生命周期阶段定义

| 阶段 | 说明 | 典型 marker | 典型目录 |
|------|------|------------|---------|
| 开发期验证 | 验证本地逻辑、接口约束、纯计算行为 | `unit` | `tests/unit/`、`tools/source_lab/tests/` 不含外部依赖的测试 |
| 构建期验证 | 验证代码可编译、可导入、lint 和类型检查通过 | 非 pytest | `py_compile`、`ruff`、`mypy`、`cmake --build` |
| 模块集成期验证 | 验证模块内组件协作、fake/mock/stub/in-memory 闭环 | `integration` | `tests/integration/` 中不依赖外部服务的测试 |
| 跨模块联调期验证 | 验证跨模块数据流、消息管道、存储链路 | `integration`、`e2e` | docker-compose 或 simulator 全链路测试 |
| 准生产依赖验证期 | 验证真实外部依赖下的系统行为 | `l5` | 需 Kafka/PG/Redis/S3/TDengine 的测试 |
| 部署前验收期 | 验证部署配置、环境预检、最小数据链路 | `e2e`、`smoke` | `tests/e2e/test_whale_field_*.py`、部署脚本 |
| 发布后运维验证期 | 生产环境运行时状态、健康检查、故障恢复 | 非 pytest | 运维脚本、监控 probe |

## 3. 测试资产索引

### 3.1 Whale 主平台测试 (tests/)

#### 开发期验证 (unit)

| 测试文件 | 测试对象 | 外部依赖 | NOT_RUN 条件 |
|---------|---------|---------|------------|
| `tests/unit/test_config.py` | 配置解析 | 无 | 无 |
| `tests/unit/test_fleet_update_selection.py` | 机群更新选择 | 无 | 无 |
| `tests/unit/test_kafka_message_publisher.py` | Kafka 发布器 | mock Kafka | 无 |
| `tests/unit/test_message_pipeline_adapters.py` | InMemory/DLQ/SchemaRegistry | 无 | 无 |
| `tests/unit/test_message_pipeline_envelope.py` | Envelope/model | 无 | 无 |
| `tests/unit/test_message_pipeline_kafka_adapter.py` | Kafka adapter | mock Kafka | 无 |
| `tests/unit/test_message_pipeline_ports.py` | 端口契约 | 无 | 无 |
| `tests/unit/test_modbus_source_acquisition_adapter.py` | Modbus TCP 采集 | mock | 无 |
| `tests/unit/test_modbus_source_write_adapter.py` | Modbus TCP 写入 | mock | 无 |
| `tests/unit/test_mqtt_backend.py` | MQTT client backend | mock | 无 |
| `tests/unit/test_mqtt_source_acquisition_adapter.py` | MQTT 采集适配器 | mock | 无 |
| `tests/unit/test_http_rest_backend.py` | HTTP REST backend | mock | 无 |
| `tests/unit/test_http_rest_source_acquisition_adapter.py` | HTTP REST 采集适配器 | mock | 无 |
| `tests/unit/test_iec104_backend.py` | IEC104 backend | mock | 无 |
| `tests/unit/test_iec104_source_acquisition_adapter.py` | IEC104 采集适配器 | mock | 无 |
| `tests/unit/test_iec104_source_write_adapter.py` | IEC104 写入适配器 | mock | 无 |
| `tests/unit/test_modbus_rtu_backend.py` | Modbus RTU backend | mock | 无 |
| `tests/unit/test_modbus_rtu_source_acquisition_adapter.py` | Modbus RTU 采集适配器 | mock | 无 |
| `tests/unit/test_iec101_backend.py` | IEC101 backend | mock | 无 |
| `tests/unit/test_iec101_source_acquisition_adapter.py` | IEC101 采集适配器 | mock | 无 |
| `tests/unit/test_opcua_adapter_resolution.py` | OPC UA 适配器解析 | mock | 无 |
| `tests/unit/test_opcua_source_acquisition_adapter.py` | OPC UA 采集适配器 | mock | 无 |
| `tests/unit/test_opcua_source_write_adapter.py` | OPC UA 写入适配器 | mock | 无 |
| `tests/unit/test_iec61850_mms_backend.py` | IEC61850 MMS backend | mock | 无 |
| `tests/unit/test_iec61850_source_acquisition_adapter.py` | IEC61850 MMS 采集适配器 | mock | 无 |
| `tests/unit/test_iec61850_source_write_adapter.py` | IEC61850 MMS 写入适配器 | mock | 无 |
| `tests/unit/test_iec61850_report_backend.py` | IEC61850 Report backend | mock | 无 |
| `tests/unit/test_iec61850_report_acquisition_adapter.py` | IEC61850 Report 采集适配器 | mock | 无 |
| `tests/unit/test_open62541_backend.py` | open62541 backend | mock | 无 |
| `tests/unit/test_polling_acquisition_role.py` | 轮询角色 | mock | 无 |
| `tests/unit/test_subscription_acquisition_role.py` | 订阅角色 | mock | 无 |
| `tests/unit/test_subscription_reconnect_baseline.py` | 订阅重连基线 | mock | 无 |
| `tests/unit/test_subscription_reconnect_runtime.py` | 订阅重连运行时 | mock | 无 |
| `tests/unit/test_redis_source_state_cache.py` | Redis 状态缓存 | mock Redis | 无 |
| `tests/unit/test_redis_streams_message_publisher.py` | Redis Streams 发布器 | mock Redis | 无 |
| `tests/unit/test_relational_outbox_message_publisher.py` | Outbox 发布器 | mock DB | 无 |
| `tests/unit/test_ingest_api_app.py` | FastAPI app | mock | 无 |
| `tests/unit/test_ingest_audit_event_schema.py` | 审计事件 schema | 无 | 无 |
| `tests/unit/test_ingest_audit_redaction.py` | 审计脱敏 | 无 | 无 |
| `tests/unit/test_ingest_metrics_events.py` | metrics 事件 | 无 | 无 |
| `tests/unit/test_ingest_no_source_lab_imports.py` | import 边界门禁 | 无 | 无 |
| `tests/unit/test_turtle_octopus_import_boundary.py` | turtle/octopus import 边界 | 无 | 无 |
| `tests/unit/test_ingest_observability_sink.py` | 观测 sink | mock | 无 |
| `tests/unit/test_ingest_source_adapter_capability_matrix.py` | 适配器能力矩阵 | 无 | 无 |
| `tests/unit/test_ingest_security_partition_config.py` | 安全分区配置 | 无 | 无 |
| `tests/unit/test_ingest_bundle_checksum.py` | bundle 摘要 | 无 | 无 |
| `tests/unit/test_ingest_bundle_redaction.py` | bundle 脱敏 | 无 | 无 |
| `tests/unit/test_ingest_composition_injection.py` | 注入完整性 | mock | 无 |
| `tests/unit/test_ingest_job_lease.py` | 作业租约 | mock | 无 |
| `tests/unit/test_ingest_runtime_entrypoint.py` | 运行入口 | mock | 无 |
| `tests/unit/test_ingest_runtime_modes.py` | runtime 模式 | mock | 无 |
| `tests/unit/test_ingest_runtime_orm_models.py` | runtime ORM | mock | 无 |
| `tests/unit/test_ingest_runtime_scheduler_import.py` | scheduler 导入 | 无 | 无 |
| `tests/unit/test_ingest_write_lease.py` | 写入租约 | mock | 无 |
| `tests/unit/test_ingest_write_lease_fencing.py` | 写入租约 fencing | mock | 无 |
| `tests/unit/test_ingest_write_security_profile.py` | 写入安全配置 | mock | 无 |
| `tests/unit/test_ingest_readyz.py` | readyz 8 组件聚合 | mock | 无 |
| `tests/unit/test_scheduler_job_routes.py` | 调度任务持久化 | mock DB | 无 |
| `tests/unit/test_worker_runtime_do_execute.py` | WorkerRuntime dispatch | mock | 无 |
| `tests/unit/test_acquisition_job_handler.py` | AcquisitionJobHandler | mock | 无 |
| `tests/unit/test_dual_node_write_lease_conflict.py` | 双节点写入冲突 | mock | 无 |
| `tests/unit/test_source_acquisition_port_registry.py` | 端口注册表 | mock | 无 |
| `tests/unit/test_source_acquisition_use_case.py` | 采集用例 | mock | 无 |
| `tests/unit/test_source_command_write_lease_guard.py` | 写入租约守卫 | mock | 无 |
| `tests/unit/test_source_command_use_case.py` | 命令写入用例 | mock | 无 |
| `tests/unit/test_source_command_lease_release.py` | 写入租约释放 | mock | 无 |
| `tests/unit/test_source_command_audit.py` | 命令审计 | mock | 无 |
| `tests/unit/test_source_command_authorization_guard.py` | 命令授权守卫 | mock | 无 |
| `tests/unit/test_shared_source_runner_resolution.py` | shared_source runner 解析 | mock | 无 |
| `tests/unit/test_state_snapshot_publish_use_case.py` | 快照发布用例 | mock | 无 |
| `tests/unit/test_source_runtime_config_repository.py` | 运行时配置仓库 | mock DB | 无 |
| `tests/unit/test_source_scheduling.py` | 调度 | mock | 无 |
| `tests/unit/test_source_simulation_support_sources.py` | 模拟源 | mock | 无 |
| `tests/unit/test_source_write_port_registry.py` | 写入端口注册表 | mock | 无 |
| `tests/unit/test_speed_layer_light_processor.py` | light_processor | 无 (in-memory) | 无 |
| `tests/unit/test_speed_layer_pipeline_runner.py` | pipeline runner | 无 (in-memory) | 无 |
| `tests/unit/test_storage_raw_archive.py` | raw_archive | 无 (in-memory) | 无 |
| `tests/unit/test_storage_raw_index.py` | raw_index | 无 (in-memory) | 无 |
| `tests/unit/test_storage_standardized.py` | standardized | 无 (in-memory) | 无 |
| `tests/unit/test_storage_serving_cache.py` | serving_cache | 无 (in-memory) | 无 |
| `tests/unit/shared/persistence/test_scada_protocol_params.py` | SCADA 协议参数模板 | 无 | 无 |
| `tests/unit/shared/persistence/test_scada_sample_data_protocol_coverage.py` | SCADA 样例数据协议覆盖 | 无 | 无 |
| `tests/unit/shared/persistence/test_scada_protocol_views.py` | SCADA 协议视图 | 无 | 无 |

#### 模块集成期验证 (integration)

| 测试文件 | 测试对象 | 外部依赖 | NOT_RUN 条件 |
|---------|---------|---------|------------|
| `tests/integration/test_ingest_api_acquisition_task_crud.py` | acquisition task CRUD | SQLite/TestClient | 无 |
| `tests/integration/test_ingest_api_audit.py` | API 审计 | SQLite/TestClient | 无 |
| `tests/integration/test_ingest_api_authorization_deny.py` | API 授权拒绝 | SQLite/TestClient | 无 |
| `tests/integration/test_ingest_api_bundle_metadata_crud.py` | bundle metadata CRUD | SQLite/TestClient | 无 |
| `tests/integration/test_ingest_api_dry_run_all_mutating_routes.py` | API dry-run | SQLite/TestClient | 无 |
| `tests/integration/test_ingest_api_full_audit_matrix.py` | API 全审计矩阵 | SQLite/TestClient | 无 |
| `tests/integration/test_ingest_api_idempotency_all_mutating_routes.py` | API 幂等性 | SQLite/TestClient | 无 |
| `tests/integration/test_ingest_api_idempotency_dry_run.py` | 幂等性 dry-run | SQLite/TestClient | 无 |
| `tests/integration/test_ingest_api_idempotency_dry_run_interaction.py` | 幂等性 dry-run 交互 | SQLite/TestClient | 无 |
| `tests/integration/test_ingest_api_node_lease_audit_query.py` | node/lease 审计查询 | SQLite/TestClient | 无 |
| `tests/integration/test_ingest_api_runtime_config_audit.py` | runtime config 审计 | SQLite/TestClient | 无 |
| `tests/integration/test_ingest_api_runtime_config_crud.py` | runtime config CRUD | SQLite/TestClient | 无 |
| `tests/integration/test_ingest_api_scheduler_job_crud.py` | scheduler job CRUD | SQLite/TestClient | 无 |
| `tests/integration/test_ingest_api_security_partition_crud.py` | security partition CRUD | SQLite/TestClient | 无 |
| `tests/integration/test_ingest_audit_db_jsonl_consistency.py` | DB/JSONL 审计一致性 | SQLite/临时文件 | 无 |
| `tests/integration/test_ingest_bundle_import_export.py` | bundle 导入导出 | SQLite | 无 |
| `tests/integration/test_ingest_bundle_offline_one_way_flow.py` | bundle 单向流 | SQLite | 无 |
| `tests/integration/test_ingest_runtime_alembic_migration.py` | Alembic 迁移 | SQLite | 无 |
| `tests/integration/test_ingest_runtime_db_init.py` | runtime DB 初始化 | SQLite | 无 |
| `tests/integration/test_ingest_runtime_entrypoint_smoke.py` | entrypoint 烟测 | SQLite | 无 |
| `tests/integration/test_message_pipeline_inmemory_e2e.py` | InMemory message_pipeline E2E | 无 | 无 |
| `tests/integration/test_speed_layer_dlq_replay.py` | DLQ/replay | 无 (in-memory) | 无 |
| `tests/integration/test_speed_layer_index_standardized_pipeline.py` | index/standardized/serving_cache | 无 (in-memory) | 无 |
| `tests/integration/test_speed_layer_raw_archive_pipeline.py` | raw_archive pipeline | 临时文件 | 无 |
| `tests/integration/test_whale_writer_failure_recovery.py` | writer 故障恢复 | 无 (in-memory) | 无 |
| `tests/integration/test_whale_writer_switchover.py` | writer 主备切换 | 无 (in-memory) | 无 |
| `tests/integration/test_http_rest_acquisition_chain.py` | HTTP REST 全链路采集 | mock HTTP | 无 |
| `tests/integration/test_iec104_acquisition_chain.py` | IEC104 全链路采集 | mock subprocess | 无 |
| `tests/integration/test_mqtt_acquisition_chain.py` | MQTT 全链路采集 | mock MQTT | 无 |
| `tests/integration/test_modbus_rtu_acquisition_chain.py` | Modbus RTU 全链路 | mock subprocess | 无 |
| `tests/integration/test_iec101_acquisition_chain.py` | IEC101 全链路 | mock subprocess | 无 |

#### 跨模块联调期验证 (integration/e2e + docker-compose)

| 测试文件 | 测试对象 | 外部依赖 | NOT_RUN 条件 |
|---------|---------|---------|------------|
| `tests/integration/test_ingest_prodlike_kafka_publish.py` | Kafka 发布 | docker-compose | MISSING_ENVIRONMENT |
| `tests/integration/test_ingest_prodlike_postgres_runtime_db.py` | PostgreSQL runtime DB | docker-compose | MISSING_ENVIRONMENT |
| `tests/integration/test_ingest_prodlike_redis_cache.py` | Redis 缓存 | docker-compose | MISSING_ENVIRONMENT |
| `tests/integration/test_ingest_scheduler_apscheduler_runtime.py` | APScheduler 运行时 | docker-compose | MISSING_ENVIRONMENT |
| `tests/integration/test_ingest_scheduler_cluster_assignment.py` | 调度器集群分配 | docker-compose | MISSING_ENVIRONMENT |
| `tests/integration/test_ingest_scheduler_active_standby_failover.py` | 调度器主备故障转移 | docker-compose | MISSING_ENVIRONMENT |
| `tests/integration/test_ingest_scheduler_graceful_shutdown.py` | 调度器优雅关闭 | docker-compose | MISSING_ENVIRONMENT |
| `tests/integration/test_ingest_prodlike_worker_failover.py` | worker failover | docker-compose | MISSING_ENVIRONMENT |
| `tests/integration/test_ingest_source_acquisition_to_redis.py` | 采集到 Redis | docker-compose | MISSING_ENVIRONMENT |
| `tests/integration/test_ingest_source_cache_message_e2e.py` | 源缓存消息 E2E | docker-compose | MISSING_ENVIRONMENT |
| `tests/integration/test_message_pipeline_kafka_e2e.py` | Kafka message_pipeline E2E | docker-compose | MISSING_ENVIRONMENT |

#### 准生产依赖验证期 (l5 marker)

| 测试文件 | 测试对象 | 外部依赖 | NOT_RUN 条件 |
|---------|---------|---------|------------|
| `tests/integration/test_l5_external_dependency_verification.py` | 5 大外部服务验证 | Kafka/PG/Redis/S3/TDengine | MISSING_ENVIRONMENT |
| `tests/e2e/test_whale_l5_kafka_pipeline_e2e.py` | Kafka pipeline E2E | Kafka/S3/TDengine/Redis | MISSING_ENVIRONMENT |
| `tests/e2e/test_whale_l5_storage_e2e.py` | 存储 E2E | S3/TDengine/Redis | MISSING_ENVIRONMENT |

#### 部署前验收期

| 测试文件 | 测试对象 | 外部依赖 | NOT_RUN 条件 |
|---------|---------|---------|------------|
| `tests/e2e/test_whale_field_minimal_smoke.py` | 现场最小数据链路 | docker-compose | MISSING_ENVIRONMENT |
| `scripts/run_whale_field_ready_smoke.sh` | 一键预检脚本 | docker-compose | MISSING_ENVIRONMENT |

### 3.2 source_lab 工具测试 (tools/source_lab/tests/)

source_lab 变更只触发 source_lab 生命周期验证。详细测试资产索引见 `tools/source_lab/tests/TEST_AUDIT.md`。

| 目录/文件 | 生命周期阶段 | 说明 |
|----------|------------|------|
| `tools/source_lab/tests/access/` | 开发期验证 | access 层 parser/metrics/reporter/runner 单测 |
| `tools/source_lab/tests/test_factory.py` | 开发期验证 | 工厂协议调度验证 |
| `tools/source_lab/tests/test_fleet_*.py` | 开发期验证 | 机群控制验证 |
| `tools/source_lab/tests/test_open62541_source_simulation_single_server_smoke.py` | 模块集成期验证 | native 单服务器 smoke |
| `tools/source_lab/tests/test_source_simulation_multi_server_*.py` | 模块集成期验证 | 多服务器容量/画像 (通过 CLI subprocess) |
| `tools/source_lab/tests/access/test_beckhoff_ads_real_protocol_readback.py` | 准生产依赖验证期 | 需 dotnet + AdsServer + AdsLib runner |

## 4. 回归测试索引

### 回归来源分类

| 分类 | 说明 | 状态 |
|------|------|------|
| defect-regression | bug 修复后新增的回归测试 | 见下表 |
| operation-regression | 故障恢复、主备切换、重启恢复 | 见下表 |
| compatibility-regression | 协议版本、消息格式、API 版本兼容性 | 见下表 |
| chain-regression | 跨模块链路验证 | 见下表 |
| release-regression | 发布前指令套件 | 见下表 |

### 回归测试列表

| 测试 | 回归分类 | 状态 | 说明 |
|------|---------|------|------|
| `test_subscription_reconnect_baseline.py` | defect-regression | ACTIVE | 订阅重连基线验证 |
| `test_subscription_reconnect_runtime.py` | defect-regression | ACTIVE | 订阅重连运行时验证 |
| `test_dual_node_write_lease_conflict.py` | defect-regression | ACTIVE | 双节点写入冲突 |
| `test_ingest_write_lease_fencing.py` | defect-regression | ACTIVE | 写入租约 fencing |
| `test_ingest_prodlike_kafka_fault_injection.py` | operation-regression | ACTIVE | Kafka 故障注入恢复 |
| `test_ingest_prodlike_postgres_fault_injection.py` | operation-regression | ACTIVE | PostgreSQL 故障注入恢复 |
| `test_ingest_prodlike_redis_fault_injection.py` | operation-regression | ACTIVE | Redis 故障注入恢复 |
| `test_ingest_scheduler_active_standby_failover.py` | operation-regression | ACTIVE | 调度器主备故障转移 |
| `test_ingest_prodlike_worker_failover.py` | operation-regression | ACTIVE | worker crash/failover |
| `test_whale_writer_failure_recovery.py` | operation-regression | ACTIVE | writer 故障恢复 |
| `test_whale_writer_switchover.py` | operation-regression | ACTIVE | writer 主备切换 |
| `test_ingest_iec104_source_write.py` | defect-regression | ACTIVE | IEC104 写入验证 |
| `test_ingest_modbus_source_write.py` | defect-regression | ACTIVE | Modbus TCP 写入验证 |
| `test_ingest_opcua_source_write.py` | defect-regression | ACTIVE | OPC UA 写入验证 |
| `test_ingest_iec61850_mms_source_write.py` | defect-regression | ACTIVE | IEC61850 MMS 写入验证 |
| `test_ingest_prodlike_endurance_smoke.py` | operation-regression | ACTIVE | 耐久性烟测 |
| `test_ingest_prodlike_scheduler_backpressure.py` | operation-regression | ACTIVE | 调度背压与 missed tick |

## 5. 回归套件定义

| 套件 | 定义 | 执行时机 | 典型范围 |
|------|------|---------|---------|
| affected regression | 本轮变更影响的测试 | 每次变更 | 变更文件的对应测试 + 相关回归 |
| module regression | 模块内所有测试 | 修改 public interface/schema/config/protocol 时 | 模块 unit+integration |
| chain regression | 上下游链路测试 | 跨模块影响时 | 上下游模块的集成测试 |
| release regression | 发布前全量回归 | 发布前 | 全部 ACTIVE 状态回归测试 + module regression |

### 套件执行命令参考

```bash
# affected regression (由 code-implementer 按变更范围选择)
pytest tests/unit/ -k "<related>" -q
pytest tests/integration/ -k "<related>" -q

# module regression (以 ingest 为例)
pytest tests/unit/ -k "ingest" -q
pytest tests/integration/ -k "ingest" -q

# chain regression (以 speed_layer->storage 为例)
pytest tests/unit/test_speed_layer_*.py tests/unit/test_storage_*.py -q
pytest tests/integration/test_speed_layer_*.py -q

# release regression (全量，不包括 slow/load/stress)
pytest -m "not slow and not load and not stress" -q
```

## 6. source_lab 测试边界

### 隔离规则

1. source_lab 测试 (`tools/source_lab/tests/`) 与 Whale 测试 (`tests/`) 独立。
2. source_lab 变更只触发 source_lab 生命周期验证。
3. 除非变更影响 `src/whale/shared/source/` 或 `src/whale/ingest/`，不跑 Whale 全量。
4. Whale 测试不得依赖 source_lab 运行时。

### 扩跑条件

| source_lab 变更 | 需额外验证的 Whale 测试 |
|----------------|----------------------|
| `tools/source_lab/access/runners/*` | 对应的 `src/whale/shared/source/*/reader.py` + `backend` 测试 |
| `tools/source_lab/protocols/*/simulator.py` | 对应的 `src/whale/ingest/adapters/source/*_adapter.py` 测试 |
| `tools/source_lab/native/*` | 对应的 native backend 测试 |

## 7. 维护规则

1. 新增测试文件：在此索引的"测试资产索引"中添加条目。
2. 新增回归测试：在"回归测试列表"中添加条目，标注回归分类和状态。
3. 删除测试文件：从此索引中移除条目；如涉及回归测试，将其状态改为 RETIRED 或 SUPERSEDED。
4. 回归测试状态变更（ACTIVE/RETIRED/SUPERSEDED）：在"回归测试列表"中更新状态和原因。
5. 目录结构变化：同步更新"测试资产索引"中的目录路径。
6. 不在此文件中维护具体测试函数名；只维护到文件级别（关键链路可维护到类级别）。
7. 不另建其他回归索引文件（如 `issue_regression_index.md`）。
8. 保留本文件为中文，测试文件和类名保留英文。
