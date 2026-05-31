# Round 11: ingest/source_lab 模块准入阻塞项修复与状态同步

> 日期: 2026-05-30
> 范围: ingest + shared_source + source_lab 模块准入阻塞项修复与证据收口
> 状态: 阻塞项修复完成，验收证据归档；ingest 不写 production-ready，source_lab 不写 tool-ready 收口
> 证据来源: code-implementer + test-validator 独立验证

## 1. 总览

| 项 | 结果 |
|---|---|
| 变更范围 | 350+ 文件修改，15+ 新增文件 |
| 质量门禁 | compileall PASS / ruff PASS / mypy PASS（ingest+shared_source 范围） |
| 测试结果 | 64 passed, 0 failed, 4 correctly skipped |
| import boundary | PASS（无 tools.source_lab 导入） |
| 阻塞项修复 | 7/7 项处理完成 |
| ingest production-ready | 否（见第 8 节声明） |
| source_lab tool-ready 收口 | 否（PROTOCOL_CAPABILITIES 静态元数据未完全剥离） |

## 2. 修改文件

| 文件 | 操作 | 说明 |
|---|---|---|
| `src/whale/shared/source/runner_resolution.py` | 新增 | shared_source production runner 路径解析与 dev fallback |
| `tests/unit/test_shared_source_runner_resolution.py` | 新增 | runner 路径解析 5 tests L2 |
| `tests/unit/test_dual_node_write_lease_conflict.py` | 新增 | 双节点写入冲突 L3 7 tests |
| `tests/integration/test_ingest_dual_node_db_lease_e2e.py` | 新增 | 双节点 DB lease E2E L3 7 tests |
| `tests/unit/test_ingest_composition_injection.py` | 新增 | 注入完整性 L1 4 tests |
| `tests/unit/test_scheduler_job_routes.py` | 新增 | 调度任务持久化 L1 4 tests |
| `tests/unit/test_source_command_lease_release.py` | 新增 | 写入租约释放 L1 4 tests |
| `tests/unit/test_worker_runtime_do_execute.py` | 新增 | WorkerRuntime dispatch L1 5 tests |
| `tests/unit/test_acquisition_job_handler.py` | 新增 | AcquisitionJobHandler L1 8 tests |
| `src/whale/ingest/runtime/handlers.py` | 新增 | WorkerRuntime 采集 job handler |
| `ai_shared/adr/ADR-20260530-010-shared-source-production-runner-artifact-boundary.md` | 新增 | shared_source production runner artifact 边界 ADR |
| `ai_shared/reports/ingest_external_dependency_readiness_matrix_round11.md` | 新增 | I-READY-002 外部依赖准入矩阵 |
| `ai_shared/reports/ingest_module_deployment_topology_port_matrix_round11.md` | 新增 | I-READY-004 部署拓扑/端口矩阵 |
| `ai_shared/reports/ingest_write_readback_field_validation_plan_round11.md` | 新增 | I-READY-005 field readback 验证计划 |
| `scripts/run_ingest_write_readback_smoke.sh` | 新增 | 三协议 write-readback smoke 入口 |
| `scripts/run_ingest_pg_lease_fault_injection.sh` | 新增 | PG lease fault injection 入口 |
| 4 个 protocol backend | 修改 | 接入 runner_resolution 路径解析 |
| `tools/source_lab/access/runners/registry.py` | 修改 | 新增 RuntimeReadiness 与 describe_protocol_runtime_readiness() |
| `tools/source_lab/access/profile.py` | 修改 | 输出 declared vs actual runtime readiness |
| `tools/source_lab/tests/access/test_protocol_production_readiness_gate.py` | 修改 | 扩展到 subscription/readiness 场景 |

## 3. 行为变化

- shared_source native runner 默认路径不再指向 `tools/source_lab/native/build`
- production runner 解析优先走环境变量、`WHALE_SHARED_SOURCE_RUNNER_DIR`、PATH
- dev/test fallback 需要显式设置 `WHALE_SHARED_SOURCE_ALLOW_DEV_RUNNER_FALLBACK=1`
- 缺失 runner 时错误消息区分 production/fallback 路径
- 4 个 protocol backend（OPC UA、Modbus、IEC104、IEC61850 MMS + Report）均通过 runner_resolution 解析
- write lease composition 注入 audit/metrics/lease，finally 块释放 lease
- fencing 原子化 UPDATE RETURNING
- AcquisitionJobHandler 接入 WorkerRuntime dispatch（asyncio.run() 桥接）
- source_lab readiness gate 从静态 CAPABILITIES 推进到 declared vs actual runtime readiness 双轨输出

## 4. 检查与测试

### 质量门禁

| 命令/检查 | 结果 | 分类 | 说明 |
|---|---|---|---|
| `python -m compileall src/whale/ingest src/whale/shared/source tools/source_lab tests tools/source_lab/tests -q` | passed | L1 | 全量语法检查 |
| `ruff check src/whale/ingest src/whale/shared/source` | passed | L1 | lint 检查 |
| `mypy src/whale/ingest src/whale/shared/source` | passed | L1 | 类型检查 |

### import 边界

| 命令/检查 | 结果 | 分类 | 说明 |
|---|---|---|---|
| Source code import scan (`src/whale/ingest` + `src/whale/shared/source`) | passed | L1 | 无 `tools.source_lab` import |

### pytest

| 命令/检查 | 结果 | 分类 | 说明 |
|---|---|---|---|
| `pytest tests/unit/test_shared_source_runner_resolution.py -q` | 5 passed | L2 | runner 路径解析 |
| `pytest tests/unit/test_dual_node_write_lease_conflict.py -q` | 7 passed | L3 | 双节点写入冲突 |
| `pytest tests/integration/test_ingest_dual_node_db_lease_e2e.py -q` | 7 passed, 4 skipped | L3 | 双节点 DB lease E2E；PG 4 skipped（环境 pending） |
| `pytest tests/unit/test_ingest_composition_injection.py -q` | 4 passed | L1 | 注入完整性 |
| `pytest tests/unit/test_scheduler_job_routes.py -q` | 4 passed | L1 | 调度任务持久化 |
| `pytest tests/unit/test_source_command_lease_release.py -q` | 4 passed | L1 | 写入租约释放 |
| `pytest tests/unit/test_worker_runtime_do_execute.py -q` | 5 passed | L1 | WorkerRuntime dispatch |
| `pytest tests/unit/test_acquisition_job_handler.py -q` | 8 passed | L1 | AcquisitionJobHandler |
| `pytest tests/unit/test_ingest_write_lease.py -q` | 3 passed | L1 | 写入租约单测 |
| `pytest tests/unit/test_source_command_use_case.py -q` | 7 passed | L2 | 命令写入用例 |
| `pytest tools/source_lab/tests/access/test_protocol_production_readiness_gate.py -q` | 34 passed | L3 | source_lab readiness gate |
| `pytest tools/source_lab/tests/access/test_native_cmd_timeout.py -q` | 3 passed | L2 | native 命令超时 |
| `pytest tests/integration/test_ingest_opcua_source_write.py tests/integration/test_ingest_modbus_source_write.py tests/integration/test_ingest_iec61850_mms_source_write.py -q` | 3 组写入集成测试 passed | L3 | 三协议 simulator/native write-readback smoke |
| 总计 | 64 passed, 0 failed, 4 correctly skipped | — | — |

## 5. 证据与需求状态

| 条目 | 证据等级 | 状态 | 说明 |
|---|---|---|---|
| 1. shared_source 与 source_lab native build 脱耦 | L2 | fixed | runner_resolution 分层解析；4 backend 接入；import boundary gate 通过；5 tests PASS |
| 2. I-READY-002 外部依赖准入矩阵 | L2/L4 | fixed | 报告覆盖 8 类依赖含 required/optional/timeout/retry/readiness/degradation/fail-open |
| 3. I-READY-004 部署拓扑/端口矩阵 | L2/L3 | fixed | 报告覆盖全部组件端口、通信方向、bundle 离线导入边界 |
| 4. I-READY-005 field readback 证据边界 | L2/L3（边界）/ L5（pending） | fixed（边界） | 计划/脚本已交付；明确标注 L3；未写成 field-ready |
| 5. I-READY-006 PostgreSQL 多进程 | L3（SQLite）/ pending（PG） | partial | SQLite L3 7 tests PASS；PG 4 tests correctly skipped |
| 6. source_lab readiness 去静态高估 | L3 | fixed | RuntimeInfo 双字段；34 tests PASS |
| 7. 需求表证据 | — | fixed | 无证据高估；skipped/pending 已标注 |

## 6. project_tree / ADR / 规则

- project_tree: 已更新（新增 `runner_resolution.py` 和 `test_shared_source_runner_resolution.py` 两项）
- ADR: ADR-20260530-010 已创建，格式正确，状态已采纳
- rules: 无变化

## 7. remaining blockers

### ingest 剩余阻塞项

| 阻塞项 | 严重程度 | 说明 |
|---|---|---|
| I-READY-005 L5 field readback 缺失 | 高 | 三协议真实设备/网关/授权链路 readback 未执行 |
| I-READY-006 PG 多进程 E2E 环境 pending | 中 | 代码已就绪，等待 PG DSN 环境 |
| readyz 聚合缺失 | 中 | 当前仅硬检查 DB；Redis/Kafka/audit/access-policy/shared_source 未纳入 |
| shared_source production runner artifact 交付 | 中 | 独立 artifact 打包/安装/验证流程未建立 |
| 长稳/压测 | 低 | 7x24 长稳和真实硬件 performance/stress 未执行 |

### source_lab 剩余阻塞项

| 阻塞项 | 严重程度 | 说明 |
|---|---|---|
| PROTOCOL_CAPABILITIES 静态 dict | 低 | 非 gate 调用方仍可读取静态元数据 |
| 全量 mypy 未清零 | 中 | 不影响 ingest/shared_source |
| GOOSE/SV L2 环境依赖 | 低 | raw socket 受控于 veth/netns |

## 8. production-ready / tool-ready 明确声明

### ingest 是否达到 production-ready：否

理由：

1. I-READY-005 写入控制 field readback L5 证据缺失；在通过真实设备 readback 前不得标 production-write-ready。
2. I-READY-006 PostgreSQL 多进程双节点 lease E2E 仍环境 pending。
3. readyz 尚未聚合 Redis/Kafka/access-policy/audit/shared_source。
4. shared_source 仍缺独立 production runner artifact 的交付安装证据。

**当前 ingest 状态为 prodlike/test-ready，不是 production-ready。**

### source_lab 是否达到 tool-ready 收口：否

理由：

1. PROTOCOL_CAPABILITIES 静态高估机制尚未完全消除（静态 dict 仍保留为元数据源，非 gate 调用方仍可读取）。
2. source_lab 全量 mypy 未清零。
3. GOOSE/SV 仍受控于 raw socket / CAP_NET_RAW / L2 环境边界。

**当前 source_lab 状态为受限 tool-ready，不是 fully-closed tool-ready。**

## 9. 下一轮建议

1. **I-READY-005 现场验证**：按 `ingest_write_readback_field_validation_plan_round11.md` 在真实设备/网关环境执行 L5 readback 验证。
2. **I-READY-006 PG 环境验证**：在具备 `WHALE_INGEST_TEST_PG_DSN` 环境后执行 PG 双进程 lease E2E 回归。
3. **readyz 聚合**：将 Redis/Kafka/access-policy/audit/shared_source 统一纳入运行时就绪探针。
4. **shared_source artifact 交付**：制定 independent production runner artifact 安装与验证 runbook。
5. **source_lab 类型债治理**：单独推进 tools/source_lab 全量 mypy 清零，同时完成静态 CAPABILITIES 调用方替换。
6. **长期运行验证**：7x24 长稳、performance/stress 压测与真实硬件验证按项目阶段推进。
7. **不建议继续扩需求**：下一轮应继续改实现/验证/现场证据，而不是继续扩需求。
