# Whale L5 Definition + REQ Cleanup Round 4 收口报告

> 日期: 2026-06-03
> 范围: L5 Round 4 -- L5 定义修正、field_readback 删除、SP-FR-004 L4 集成证据对齐、REQ 跟踪表诚实状态同步、project_tree 更新
> 状态: 收口完成
> 证据来源: project-steward 独立执行 + Git 工作区 + test-validator Round 4 独立验证证据

## 1. 总览

| 项 | 结果 |
|---|---|
| L5 定义修正 | "真实外部环境/现场环境验证通过" -> "准生产真实外部依赖环境验证通过" |
| 现场环境验证定位 | 不作为需求跟踪表验证等级，只能作为独立交付/验收/运维证据归档 |
| field_readback 目录 | 已删除（原为一个 untracked 目录，7 文件，全部 PENDING） |
| L5 marker 修正 | 6 个 InMemory-backed tests 的 L5 marker 已移除（0 残留），14 个真实外部依赖测试 L5 marker 保留 |
| SP-FR-004 升级 | L1 -> L1+L4 integrated（LightProcessingPipeline -> _LightFilteredSource -> SpeedLayerWiring.with_light_processor()，6 新 L4 集成测试） |
| 测试最终状态 | 67 passed (50 unit + 13 integration + 4 e2e), 0 failures |
| 静态检查 | compileall clean, mypy 0 errors, ruff clean, import boundary clean |
| REQ 文件更新 | 6 文件更新（Project/MessagePipeline/SpeedLayer/Storage/Ingest/README） |
| project_tree 更新 | field_readback 移除，runner.py 描述更新，脚本描述对齐 |

## 2. 修改文件

| 文件 | 操作 | 说明 |
|---|---|---|
| ai_shared/field_readback/ | 删除 | 整个目录删除（7 文件：README + 5 runbook + evidence template） |
| ai_shared/memory/Whale_REQ_README.md | 修改 | L5 定义修正 + L4 定义澄清 + 维护规则新增（现场环境验证不替代 L0-L5） |
| ai_shared/memory/Whale_REQ_Project.md | 修改 | P-FR-002 诚实状态对齐（Kafka/PG L5 verified, S3/TDengine/Redis/Pulsar/Flink/HDFS env-pending, warehouse/mart=batch layer=stub），时间戳更新 |
| ai_shared/memory/Whale_REQ_MessagePipeline.md | 修改 | MP-FR-001/003 诚实标签：Pulsar contract/env-pending，DLQ InMemory L4 verified + Round 4 L5 marker 修正说明，时间戳更新 |
| ai_shared/memory/Whale_REQ_SpeedLayer.md | 修改 | SP-FR-004 从 L1 升级至 L1/L4 (6 新 L4 集成测试证据)，SP-FR-001 新增 SpeedLayerWiring L4 集成证据，时间戳更新 |
| ai_shared/memory/Whale_REQ_Storage.md | 修改 | 保持 ST-FR-001/002/004 为 L1+L4 (L5 env-pending)，时间戳更新 |
| ai_shared/memory/Whale_REQ_Ingest.md | 修改 | field_readback 目录引用移除（3 处），Round 28 摘要更新为 Round 4 状态，阻塞项重新分类，时间戳更新 |
| ai_shared/memory/project_tree.md | 修改 | field_readback 子树删除，runner.py 描述更新（_LightFilteredSource, with_light_processor），check_l5_field_readback_env 描述对齐，header 时间戳更新 |
| ai_shared/reports/whale_l5_definition_req_cleanup_round4_closure_report.md | 新增 | 本报告 |

## 3. 行为变化

- **L5 定义修正**: 从"真实外部环境 / 现场环境验证通过"修正为"准生产真实外部依赖环境验证通过"。移除"现场环境验证通过"。这是对验证等级语义的澄清，非功能退化。
- **现场环境验证定位**: 现场真实电站、真实设备、真实生产网络环境验证不作为本项目需求跟踪表验证等级；若发生，只能作为独立交付/验收/运维证据归档，不替代 L0-L5。
- **L4 定义澄清**: 从"本地或 prodlike 运行闭环通过"修正为"本地可复现准生产集成验证通过"，强调可复现性。
- **field_readback 目录删除**: 该目录作为 untracked 文件（不在 git 版本控制中）被物理删除。L5 验证的准生产外部依赖环境需求通过环境预检脚本和 REQ 跟踪表 env-pending 状态表达。
- **SP-FR-004 状态升级**: 从 Round 3 的 L1 verified 升级为 L1+L4 integrated。核心变化是 `LightProcessingPipeline` 通过 `_LightFilteredSource` wrapper 集成到 `SpeedLayerWiring.with_light_processor()` 构建流程中，新增 6 个 L4 集成测试验证 wiring builds、valid flow、dedup、out-of-order、quality_code、invalid->DLQ。

## 4. 检查与测试

本 round 不执行代码修改，只做文档/REQ/目录树更新。以下为 test-validator 在 Round 4 独立验证中给出的证据摘要：

| 命令/检查 | 结果 | 分类 | 说明 |
|---|---|---|---|
| L5 marker audit | 6 removed, 14 retained | 审计 | 6 InMemory-backed tests L5 marker 已移除；14 real external dependency tests L5 marker 保留 |
| SP-FR-004 L4 integration | 6 passed | L4 | TestSpeedLayerWiringWithLightProcessor: wiring builds/valid flow/dedup/out-of-order/quality_code/invalid->DLQ |
| SP-FR-004 L1 unit | 26 passed | L1 | LightProcessingPipeline 全组件单元测试 |
| Backward compatibility | verified | 架构 | 不传 light_processor 行为与之前一致 |
| compileall | passed | 静态 | 编译无错误 |
| mypy | passed (0 errors) | 静态 | 类型检查 clean |
| ruff | passed | 静态 | lint clean |
| import boundary | CLEAN | 架构 | 0 forbidden imports |
| 67 tests total | 50 unit + 13 integration + 4 e2e | 综合 | 0 failures |

## 5. 证据与需求状态

### 5.1 L5 定义变更

| 版本 | 定义 | 问题 |
|---|---|---|
| Round 3 及之前 | L5：真实外部环境 / 现场环境验证通过 | 混淆"准生产外部依赖环境"与"真实电站现场设备环境" |
| Round 4 | L5：准生产真实外部依赖环境验证通过 | 明确 L5 适用于 Kafka/PG/S3/TDengine/Redis 等可 Docker Compose 复现的外部依赖 |

### 5.2 L5 Marker 修正摘要

| 分组 | 测试数 | marker | 状态 |
|---|---|---|---|
| TCP probe tests (Kafka/Redis/PG) | 5 | @pytest.mark.l5 | 保留（真实外部依赖） |
| Kafka pub/consume tests | 2 | @pytest.mark.l5 | 保留（真实外部依赖） |
| TDengine REST tests | 2 | @pytest.mark.l5 | 保留（真实外部依赖，env-pending） |
| HDFS/S3 tests | 2 | @pytest.mark.l5 | 保留（真实外部依赖，env-pending） |
| InMemory-backed tests (原标记 L5) | 6 | L5 marker 已移除 | Round 4 修正为 L4 |
| **合计** | **14 保留 + 6 移除 = 20** | | 0 个 InMemory L5 marker 残留 |

### 5.3 SP-FR-004 状态对比

| 维度 | Round 3 | Round 4 |
|---|---|---|
| 验证等级 | L1 | L1/L4 (L5 env-pending) |
| L1 tests | 26 (LightProcessingPipeline 组件) | 26 (不变) |
| L4 integration tests | 0 (未集成) | 6 (TestSpeedLayerWiringWithLightProcessor) |
| Wiring 集成 | 未实现 | with_light_processor() + build() |
| 实现证据 | EnvelopeValidator/Deduplicator/QualityCode/OutOfOrder/Pipeline | 同上 + _LightFilteredSource wrapper + LocalPipelineRunner 接受 optional light_processor |
| 差距 | 未集成到 Wiring (L4 pending) | 未在真实外部依赖环境验证 (L5 env-pending) |

### 5.4 最终 10-Segment Status Matrix (Round 4)

| # | Segment | 实现状态 | 证据等级 | L5 状态 |
|---|---|---|---|---|
| 1 | ingest->message_pipeline | Kafka adapter real | L5 verified | Kafka real pub/consume E2E passed |
| 2 | broker adapter | Kafka real, Pulsar contract | L2 (Pulsar) | Pulsar env-pending |
| 3 | message_pipeline->speed_layer | REAL consumer.poll() + SpeedLayerWiring (with_light_processor L4 integrated) | L5 verified (Kafka) | Kafka consumer group isolation E2E passed |
| 4 | speed_layer->raw_archive | S3RawArchiveSink REAL (boto3) + LocalCompressedArchiveSink | L1 (L5 env-pending) | S3/MinIO env-pending |
| 5 | speed_layer->raw_index | TdengineRawIndexSink REAL | L1 (L5 env-pending) | TDengine env-pending |
| 6 | speed_layer->standardized | TdengineStandardizedSink REAL | L1 (L5 env-pending) | TDengine env-pending |
| 7 | speed_layer->serving_cache | RedisServingCache REAL (redis-py) | L1 (L5 env-pending) | Redis L5 env-pending |
| 8 | DLQ/replay | InMemory full chain L4 passed | L4 | Real broker DLQ env-pending |
| 9 | writer switchover | L4 8/8 passed | L4 | Real broker env-pending |
| 10 | import boundary | CLEAN (79 tests) | L3 | CLEAN |

### 5.5 环境可用性矩阵（2026-06-03）

| 外部依赖 | TCP | Driver | L5 状态 |
|---|---|---|---|
| Kafka (9092) | available | ok | **L5 verified** |
| PostgreSQL (5432) | available | ok | **L5 verified** |
| Redis (16379) | available | driver-missing | **env-pending** |
| S3/MinIO (9000) | unavailable | driver-missing | **env-pending** |
| TDengine (6041) | unavailable | env-pending | **env-pending** |
| Pulsar (6650) | unavailable | env-pending | **env-pending** |
| Flink (8081) | unavailable | env-pending | **env-pending** |
| HDFS (9870) | unavailable | env-pending | **env-pending** |

### 5.6 REQ 同步摘要

| REQ 文件 | 更新行数 | 关键变化 |
|---|---|---|
| Whale_REQ_README.md | L5 定义行 + L4 定义行 + 维护规则行 | L5 定义修正，L4 定义澄清，新增现场环境验证不替代 L0-L5 规则 |
| Whale_REQ_Project.md | P-FR-002 行 | 诚实标签：Kafka/PG L5 verified，S3/TDengine/Redis/Pulsar/Flink/HDFS env-pending，warehouse/mart=batch layer=stub |
| Whale_REQ_MessagePipeline.md | MP-FR-001, MP-FR-003, 时间戳 x2 | Pulsar contract/env-pending 明确，DLQ InMemory L4 + Round 4 L5 marker 修正说明 |
| Whale_REQ_SpeedLayer.md | SP-FR-004, SP-FR-001, 时间戳 x4 | SP-FR-004 L1->L1/L4 (6 新 L4 集成测试)，SP-FR-001 新增 Wiring L4 集成证据 |
| Whale_REQ_Storage.md | 时间戳 x4 | 保持 L1/L4 (L5 env-pending)，诚实不升级 |
| Whale_REQ_Ingest.md | 3 处 field_readback 引用 + Round 28 摘要 + 时间戳 | field_readback 引用全部替换或移除，阻塞项重分类 |

## 6. project_tree / ADR / 规则

- **project_tree**: 已更新（field_readback 子树移除，runner.py 描述更新，header 时间戳 2026-06-03）
- **ADR**: 无需新增。L5 定义修正是验证等级语义澄清，不改变架构边界。SP-FR-004 L4 集成是在 ADR-20260602-014 定义的速度层管线边界内完成。
- **rules**: 无需更新。L5 定义修正和维护规则都写入 Whale_REQ_README.md，属于需求文档范畴，不涉及 ai_shared/rules/ 下的公共规则。

## 7. 剩余风险

1. **8 个外部依赖中仅 2 个 L5 verified**: Kafka + PostgreSQL L5 verified。S3/TDengine/Redis/Pulsar/Flink/HDFS 全部 env-pending。真实适配器代码路径（S3RawArchiveSink/TdengineRawIndexSink/TdengineStandardizedSink/RedisServingCache）L1 验证通过但 L5 无法验证。
2. **SP-FR-004 L5 env-pending**: L1+L4 通过（26 + 6 tests），但未在真实外部依赖环境验证。LightProcessingPipeline 管线逻辑正确但 production 环境下的性能/行为未覆盖。
3. **warehouse/mart 仅 stub**: 数仓与数据集市层无真实实现，批处理链路未实现（Lambda arm 缺失）。
4. **真实设备/现场环境不在验证等级内**: Round 4 已明确 OPC UA/Modbus TCP/IEC 61850 MMS/IEC104/IEC 61850 Report 的真实设备验证不属于本项目需求跟踪表验证等级，但作为独立交付证据仍需要。

## 8. 下一步建议

### P0（环境准备）
1. 安装 boto3、redis-py、taos 驱动包
2. 启动 docker-compose.whale-l5.yaml 全量环境（S3/MinIO/TDengine/Redis 容器）

### P1（L5 证据扩展）
3. S3RawArchiveSink L5 E2E 验证
4. TdengineRawIndexSink + TdengineStandardizedSink L5 E2E 验证
5. RedisServingCache L5 E2E 验证
6. Pulsar 真实 broker 环境 L5 验证

### P2（能力补齐）
7. warehouse/mart 真实后端实现
8. batch layer 实现（Lambda arm）
9. Flink 真实环境部署与 L5 验证
