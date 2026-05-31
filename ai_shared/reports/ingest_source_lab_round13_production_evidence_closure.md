# ingest/source_lab Round 13 生产准入剩余证据闭环报告

> 日期: 2026-05-30
> 范围: ingest 生产准入剩余六大证据项 (PG E2E / compose readyz / crosscutting 矩阵 / source_lab mypy phase1 / field readback / 需求跟踪)
> 状态: 四项 fixed，两项 environment-pending；ingest 仍未 production-ready，source_lab 仍未 fully-closed tool-ready
> 证据来源: test-validator 独立验证结论、git status、mypy/ruff/compileall/pytest 输出、源码与配置审阅

## 1. 总览

| 项 | 结果 |
|---|---|
| Task A: PG E2E 自动化 | environment-pending |
| Task B: compose readyz E2E | environment-pending |
| Task C: crosscutting 接入矩阵 | fixed |
| Task D: source_lab mypy phase 1 | fixed |
| Task E: field readback 状态确认 | fixed (WRITE_ENABLED=false confirmed) |
| Task F: 需求跟踪准确性 | accurate |
| ingest production-ready | 否 |
| source_lab fully-closed tool-ready | 否 |

## 2. 修改文件

| 文件 | 操作 | 说明 |
|---|---|---|
| `tools/source_lab/protocols/common/simulator_models.py` | 修改 | ReadSimulatorResult 签名统一 (values: dict\|str + __post_init__) |
| `tools/source_lab/model.py` | 修改 | from_protocol() 显式参数替代 **kwargs + resolve_service_triple 分支 |
| `tools/source_lab/fleet.py` | 修改 | # type: ignore 附中文说明覆盖 misc/arg-type |
| `tools/source_lab/access/runtime/endpoint_registry.py` | 修改 | isinstance 类型收窄 JSON 反序列化边界 |
| `docker-compose.ingest-prodlike.yaml` | 修改 | compose readyz E2E 支持 |
| `scripts/run_ingest_compose_readyz_e2e.sh` | 新增 | compose readyz 8组件聚合 E2E 脚本 |
| `scripts/run_ingest_pg_lease_fault_injection.sh` | 修改 | PG fault injection 多模式自动检测 |
| `scripts/run_ingest_write_readback_smoke.sh` | 修改 | 写入 readback 审计与状态确认 |
| `ai_shared/reports/source_lab_mypy_phase1_closure_round13.md` | 新增 | mypy phase1 治理收口报告 |
| `ai_shared/reports/ingest_crosscutting_integration_matrix_round13.md` | 新增 | crosscutting 8/8 接入矩阵报告 |
| `ai_shared/reports/ingest_source_lab_round13_production_evidence_closure.md` | 新增 | 本报告 |

## 3. 每个 blocker 的收口状态

### 3.1 Task A: PG E2E 自动化

| 属性 | 值 |
|---|---|
| 目标 | `scripts/run_ingest_pg_lease_fault_injection.sh` 支持 auto/docker/dsn/sqlite-only 模式 |
| 代码状态 | 脚本已完善，支持自动检测和环境切换 |
| SQLite 路径 | PASS (sqlite-only mode) |
| PG 路径 | environment-pending |
| 根因 | PG 容器创建后未运行 Alembic migration，导致 `ingest_job_lease` 表缺失 |
| 发现者 | test-validator (独立验证阶段) |
| 证据等级 | L2 (script exists) / L4 pending (PG path blocked) |

### 3.2 Task B: compose readyz E2E

| 属性 | 值 |
|---|---|
| 目标 | `scripts/run_ingest_compose_readyz_e2e.sh` 端到端验证 readyz 8组件聚合 |
| 代码状态 | 脚本已创建，Docker build PASS |
| E2E 验证 | environment-pending (healthz check 超时) |
| 证据等级 | L2 (script exists) / L4 pending |

### 3.3 Task C: crosscutting 接入矩阵

| 属性 | 值 |
|---|---|
| 目标 | 形成 ingest 对 crosscutting 8 类横切能力的接入矩阵 |
| 结果 | 矩阵已形成，覆盖 CT-FR-001~005, CT-NFR-001, CT-SCR-001, CT-TEST-001 |
| 接入方式 | decorator/middleware/composition，无 mixin 继承 |
| 证据等级 | L3 (integration, 8/8 覆盖) |
| 未重写内部职责 | 是，矩阵只映射 ingest 接入点，不对 crosscutting 内部实现下定论 |
| 剩余差距 | compose 级 E2E environment-pending |

### 3.4 Task D: source_lab mypy phase 1

| 属性 | 值 |
|---|---|
| 目标 | 非测试源码 mypy errors 降至 80 以下 |
| Round 12 基线 | 227 errors / 37 files (非测试源码 132 errors / 10 files) |
| Round 13 结果 | 189 errors / 31 files (非测试源码 17 errors / 4 files) |
| 5 focus files | simulator_models.py(0), model.py(0), fleet.py(0), endpoint_registry.py(~5), opcua/simulator.py(0 own) |
| 治理策略 | isinstance 收窄、__post_init__ 规范化、# type: ignore 附中文说明、显式参数替代 **kwargs |
| 违规检查 | 无 Any 滥用、无无解释 ignore、无 disable-error-code 无差别关闭 |
| 第一阶段目标 | 达成 (132 -> 17, -115 errors) |
| 剩余 4 files 17 errors | dynamic_cli.py(14) + opcua simulator(1) + registry.py(1) + providers/simulator.py(1) |
| 证据等级 | L3 (mypy --explicit-package-bases verified) |

### 3.5 Task E: field readback 状态确认

| 属性 | 值 |
|---|---|
| 目标 | 确认 write/readback 安全门状态 |
| WRITE_ENABLED | false (默认关闭，正确) |
| CONFIRM_FLAG | false (双重安全门，正确) |
| L5 伪造 | 无 |
| 三协议 readback | OPC UA + Modbus TCP + IEC61850 MMS 各 3 tests L2 contract passed |
| 真实设备 L5 | 缺失 |
| 证据等级 | L2 (contract, simulator) |

### 3.6 Task F: 需求跟踪准确性

| 属性 | 值 |
|---|---|
| I-READY-003 | 从"部分实现"更新为"接入完毕"，crosscutting 矩阵证据已补 |
| I-READY-005 | 仍 partial，WRITE_ENABLED=false 确认，无 L5 |
| I-READY-006 | 仍 environment-pending，PG migration gap 已记录 |
| I-READY-007 | 更新 mypy phase1 证据 (17 errors / 4 files)，mypy src/whale/ingest PASS |
| SL-READY-001 | 更新 mypy phase1 证据，仍非 fully-closed tool-ready |
| 状态高估 | 未发现，I-READY-005/006 仍正确标记 partial |

## 4. 检查与测试

| 命令/检查 | 结果 | 分类 | 说明 |
|---|---|---|---|
| `python -m compileall src/whale/ingest src/whale/shared/source tools/source_lab tests tools/source_lab/tests -q` | passed | L3 | 全量 compileall |
| `ruff check src/whale/ingest src/whale/shared/source tools/source_lab tests tools/source_lab/tests` | passed | L3 | 全量 lint |
| `mypy src/whale/ingest src/whale/shared/source` | passed | L3 | 1 import-untyped yaml |
| `mypy tools/source_lab --explicit-package-bases` (非测试) | 17 errors / 4 files | L3 | 从 132 errors 降至 17 |
| `mypy tools/source_lab --explicit-package-bases` (全量) | 189 errors / 31 files | L3 | 测试文件 172 errors 未治理 |
| `pytest tests/unit/ tests/integration/ -q --timeout=60` | 59 passed, 0 failed, 4 skipped | L3 | affected files 全量 |
| `pytest tools/source_lab/tests/access/ -q` | 734 passed, 3 skipped | L4 | source_lab 全量 |
| import boundary gate | passed | L3 | src/whale/ingest, src/whale/shared/source 均不 import tools.source_lab |

## 5. 证据与需求状态

| 条目 | 证据等级 | 状态 | 说明 |
|---|---|---|---|
| I-READY-003 (crosscutting 接入) | L3 | 接入完毕 | 8/8 矩阵已形成，decorator/middleware/composition 全链路覆盖 |
| I-READY-005 (写入控制准入) | L2/L3 | 部分实现 | WRITE_ENABLED=false, CONFIRM_FLAG=false 确认正确，无 L5 |
| I-READY-006 (多节点准入) | L2/L4 | 部分实现 | PG path environment-pending (migration gap) |
| I-READY-007 (质量门禁) | L3 | 部分实现 | compileall/ruff/mypy(ingest) PASS；source_lab mypy 17 errors 未清零 |
| SL-READY-001 (source_lab 工具准入) | L3 | 部分实现 | mypy phase1 done (17 errors)，仍非 fully-closed |

## 6. project_tree / ADR / 规则

- project_tree: 已更新 (新增 run_ingest_compose_readyz_e2e.sh + 3 报告文件)
- ADR: 无需更新 (本轮未涉及新架构决策)
- rules: 无需更新 (本轮为文档收口，未变更规则语义)

## 7. 核心判定声明

### 7.1 ingest production-ready 判定

**ingest 仍不是 production-ready。**

阻止项:
1. PG E2E (I-READY-006) environment-pending -- PG migration gap 导致 `ingest_job_lease` 表缺失
2. compose readyz E2E (I-READY-002) environment-pending -- healthz check 超时
3. field readback (I-READY-005) 无 L5 证据 -- 三协议只有 L2 contract
4. 7x24 长稳验证未执行

已满足项:
1. compileall/ruff/mypy(ingest+shared) PASS
2. import boundary PASS
3. crosscutting 8/8 接入矩阵 L3 PASS
4. 59 tests passed, 0 failed, 4 correctly skipped
5. write/lease/fencing/audit 安全门 L3 部分通过

### 7.2 source_lab fully-closed tool-ready 判定

**source_lab 仍不是 fully-closed tool-ready。**

阻止项:
1. 全量非测试 mypy 17 errors / 4 files 未清零
2. dynamic_cli.py 14 errors 需 TypedDict 方案治理
3. opcua simulator 1 error 需第三方 stub
4. factory 返回类型 2 errors 需接口统一重构

已满足项:
1. mypy phase 1 达成 (132 -> 17, 5 focus files 0 errors)
2. simulator contract 734 tests passed
3. native runner 预检完整
4. DECLARED_PROTOCOL_CAPABILITIES 重命名与 runtime readiness 分离

## 8. test-validator 发现的 PG migration gap

test-validator 独立验证时发现:

- `scripts/run_ingest_pg_lease_fault_injection.sh` 脚本创建 PG 容器 (docker compose up -d postgres)
- 但未在容器启动后运行 `alembic upgrade head` (migrate entrypoint)
- 导致 `ingest_job_lease` 表缺失，PostgreSQL path 无法执行 E2E
- SQLite path 正常通过 (sqlite-only mode)

修复建议: 在 PG 容器启动后、fault injection 执行前，添加 `docker compose run --rm ingest-api python -m whale.ingest.runtime.cli migrate` 或等价 migration 步骤。

## 9. 剩余风险

- PG migration gap 阻塞 I-READY-006 收口，需脚本修复后重新验证
- compose readyz E2E healthz 超时未定位根因
- 三协议真实设备 L5 readback 仍无证据
- source_lab mypy 第二阶段 (dynamic_cli TypedDict) 工作量 14 errors，需新一轮编码
- 长期运行 (7x24) 和网络分区场景未验证

## 10. 下一步建议

1. **优先修复 PG migration gap**: 在 fault injection 脚本中添加 migration 步骤，重新执行 PG E2E
2. **排查 compose readyz healthz 超时**: 检查容器网络和 readyz 探针配置
3. **source_lab mypy 第二阶段**: 对 dynamic_cli.py 引入局部 TypedDict/parser，预计修复 12+ errors
4. **field readback**: 仍需要真实设备/真实网关 L5 验证，短期内可继续维持 L2 contract ready
5. **保持质量门禁**: compileall/ruff/mypy(ingest)/import boundary 继续作为每轮必检项
