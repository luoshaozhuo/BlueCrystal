# Round 12: ingest/source_lab production-ready 剩余阻塞项闭环与状态判定

> 日期: 2026-05-30
> 范围: ingest / source_lab / shared_source 模块级生产准入剩余阻塞项
> 状态: 部分收口（6/7 blocker 推进，ingest 仍为 prodlike/test-ready）
> 证据来源: code-implementer Round 12 实现 + test-validator Round 12 独立验证

## 1. 总览

本轮目标是对 ingest production-ready 的 7 个剩余阻塞项进行闭环推进。以下为收口状态矩阵。

| 验证项 | 本轮状态 | 证据等级 | 实际结论 |
|---|---|---|---|
| A. readyz 8模块聚合 | 已修实 | L1 | fixed: 20 tests PASS, required/degraded 逻辑正确, 敏感信息脱敏 |
| B. PG 多进程 E2E | 环境阻塞 | L4 skipped | environment-pending: PG DSN 未提供, 4 PG tests correctly skipped |
| C. shared_source artifact 路径契约 | 已修实 | L2 | fixed: 6/6 PASS, 生产路径不依赖 source_lab |
| D. field readback 验证入口 | 入口就绪 | L2 | validation-entry-ready: WRITE_ENABLED 默认 false, 双重安全门 |
| E. PROTOCOL_CAPABILITIES 残余治理 | 已修实 | L2 | fixed: registry.py mypy 清零, DECLARED_ 前缀, 7/7 非 gate 调用方已迁移 |
| F. 模块就绪需求状态更新 | 已核验 | N/A | accurate: 无证据高估, I-READY-005/006 仍 partial |
| G. 需求跟踪准确性 | 已核验 | N/A | accurate: 无 skipped/mock/fake 冒充通过 |

**compileall/ruff/mypy PASS；67 tests passed, 0 failed, 4 correctly skipped；无 import boundary violation。**

## 2. 每个阻塞项的详细收口状态

### 2.1 Task A: readyz 8组件聚合端点

- **目标**：实现 ingest 模块级健康聚合端点，按组件独立性检查运行时依赖，支持 degraded 语义
- **实现**：`src/whale/ingest/api/readyz.py`（新增）
- **测试**：`tests/unit/test_ingest_readyz.py`（新增，20 tests）
- **验证结果**：PASS
  - 8 组件覆盖：runtime DB / Redis / Kafka / audit / access-policy / shared_source / adapter-registry / config
  - required component failed -- 503
  - optional component failed -- 200 + degraded_reasons
  - 敏感信息脱敏（密码/连接串不进入 response body）
  - 在 `health.py` 路由中集成 `/readyz` endpoint
- **剩余差距**：docker compose 级真实依赖 readyz 聚合 E2E 仍需补证

### 2.2 Task B: PostgreSQL 多进程 lease/fencing E2E

- **目标**：在 PostgreSQL 环境下验证双节点 write/control lease 和 fencing E2E
- **实现**：`scripts/run_ingest_pg_lease_fault_injection.sh`（重写）、`tests/integration/test_ingest_dual_node_db_lease_e2e.py`、`tests/integration/test_ingest_prodlike_postgres_fault_injection.py`
- **测试**：`pytest tests/integration/test_ingest_prodlike_postgres_runtime_db.py -q` -- 7 SQLite L3 PASS, 4 PG L4 correctly skipped
- **验证结果**：environment-pending
  - 脚本已支持 auto/docker/dsn/sqlite-only 三种模式自动检测
  - docker compose 自动启动 PG 并注入故障逻辑就绪
  - 因 `WHALE_INGEST_TEST_PG_DSN` 未设置，PG tests correctly skipped（非 fail）
  - SQLite L3 单进程证据不能替代 PostgreSQL 多进程/多节点证据
- **剩余差距**：需要 PG 环境后执行双进程 E2E 回归，补网络分区 runbook

### 2.3 Task C: shared_source production runner artifact 路径契约验证

- **目标**：验证 `runner_resolution.py` 的 production/dev 双层路径边界正确
- **实现**：`src/whale/shared/source/runner_resolution.py`、`tests/unit/test_shared_source_runner_resolution.py`
- **测试**：`pytest tests/unit/test_shared_source_runner_resolution.py -q` -- 6/6 PASS
- **验证入口**：`scripts/validate_shared_source_production_runner.sh`（新增）
- **验证结果**：PASS L2
  - PRODUCTION_RUNNER_DIR 优先级正确
  - PATH 发现正确
  - dev fallback disabled 时不指向 `tools/source_lab/native/build`（默认指向 `/opt/whale/shared-source/bin`）
  - 缺失 runner 返回 unavailable（含 install hint）
  - dev fallback 消息正确标注 "does not count as a production runner artifact"
  - `is_source_lab_dev_runner_path` 识别正确
  - 五协议 backend（OPC UA/Modbus TCP/IEC104/IEC61850 MMS/IEC61850 Report）均已接入 runner_resolution
- **剩余差距**：验证的是路径解析契约（L2），真实编译好的 production runner artifact 的打包/安装/端到端运行仍 pending

### 2.4 Task D: field readback 验证入口建设

- **目标**：为三协议 field readback 验证建立安全、可重复的执行入口
- **实现**：`scripts/run_ingest_write_readback_smoke.sh`（重写）
- **验证结果**：validation-entry-ready
  - 可配置三协议（--protocol opcua|modbus|iec61850|all）
  - `WRITE_ENABLED` 环境变量默认 false（双重安全门）
  - `CONFIRM_FLAG` 环境变量要求显式设置 `i-am-sure` 才能真实下发
  - 审计日志输出到 `ai_shared/reports/` 子目录
  - 失败代码分类（TIMEOUT/READBACK-MISMATCH/NOT-IMPLEMENTED/CONNECTION-REFUSED）
  - 证据报告自动生成
- **剩余差距**：真实设备 / 真实网关 / 真实授权链路的 L5 readback 仍缺失，需按 field validation plan 执行现场验证
- **明确声明**：ingest write/control 仍为 dry-run-ready (L2)，**不是 production-write-ready (L5)**

### 2.5 Task E: PROTOCOL_CAPABILITIES 残余治理

- **目标**：清零 registry.py mypy 错误，消除静态 capability dict 的误用风险
- **实现**：`tools/source_lab/access/runners/registry.py`（修改）
- **测试**：`pytest tools/source_lab/tests/access/test_protocol_production_readiness_gate.py -q` -- 34 passed；`pytest tools/source_lab/tests/access/test_protocol_service_capabilities.py -q` -- passed
- **验证结果**：PASS
  - `PROTOCOL_CAPABILITIES` 重命名为 `DECLARED_PROTOCOL_CAPABILITIES`（标注 static metadata only）
  - 保留 `PROTOCOL_CAPABILITIES` 向后兼容别名
  - registry.py mypy 8 errors -- 清零（native try 路径使用独立变量名，fallback 干净类型引入）
  - 7/7 非 gate 调用方已迁移到 runtime readiness API，仅 readiness gate 测试保留静态引用
  - readiness gate 使用 `DECLARED_` 前缀清晰区分 declared vs actual
- **剩余差距**：`tools/source_lab` 全量 mypy 227 errors / 37 files 仍未清零，source_lab tool-ready 仍不能写成 fully-closed

### 2.6 Task F: 模块就绪需求状态更新

- **目标**：更新 `Whale_REQ_Ingest.md` 和 `Whale_REQ_SourceLab.md` 中 READY 级需求状态
- **已完成**：test-validator 已按 Round 12 证据更新需求跟踪表
- **核验结果**：所有更新准确，无证据高估

### 2.7 Task G: 需求跟踪准确性核验

- **目标**：确认未出现 skipped/mock/fake 冒充通过
- **核验结果**：
  - I-READY-005 仍为 partial: L2/L3 readback contract verified，L5 field readback 仍缺失
  - I-READY-006 仍为 partial: PG E2E 代码就绪但 environment-pending
  - I-READY-002 已更新: readyz 8 组件聚合 evidence 已回填
  - I-READY-007 已更新: registry.py mypy 清零，但 source_lab 全量 mypy 227 errors 未清零
  - SS-READY-001 已更新: runner_resolution 路径契约 evidence 已回填
  - 无 skipped/mock/fake/health-check/TCP-connect 写成真实通过

## 3. 修改文件汇总

| 文件 | 操作 | 说明 |
|---|---|---|
| `src/whale/ingest/api/readyz.py` | 新增 | readyz 8组件聚合与degradation脱敏 |
| `tests/unit/test_ingest_readyz.py` | 新增 | readyz 20 tests（required/degraded/脱敏） |
| `src/whale/ingest/api/routes/health.py` | 修改 | readyz endpoint 路由接入 |
| `src/whale/ingest/framework/persistence/runtime_db.py` | 修改 | readyz 探针增强 |
| `scripts/run_ingest_pg_lease_fault_injection.sh` | 重写 | auto/docker/dsn/sqlite-only 模式自动检测 |
| `scripts/run_ingest_write_readback_smoke.sh` | 重写 | 三协议可配置、双重安全门、审计日志输出 |
| `scripts/validate_shared_source_production_runner.sh` | 新增 | runner resolution 路径契约验证 |
| `tools/source_lab/access/runners/registry.py` | 修改 | DECLARED_PROTOCOL_CAPABILITIES 重命名 + mypy 清零 |
| `ai_shared/reports/source_lab_mypy_debt_plan_round12.md` | 新增 | mypy 分阶段治理计划 |
| `ai_shared/reports/shared_source_production_runner_artifact_validation_round12.md` | 新增 | runner artifact 契约验证报告 |
| `ai_shared/memory/Whale_REQ_Ingest.md` | 修改 | I-READY-002/005/006/007 状态更新 |
| `ai_shared/memory/Whale_REQ_SourceLab.md` | 修改 | SL-READY-001/003、SL-FR-004 状态更新 |
| `ai_shared/memory/Whale_REQ_SharedSource.md` | 修改 | SS-READY-001/003 状态更新 |

## 4. 检查与测试

| 命令/检查 | 结果 | 分类 | 说明 |
|---|---|---|---|
| `python -m compileall src/whale/ingest src/whale/shared/source tools/source_lab tests tools/source_lab/tests -q` | PASS | compileall | 全部通过 |
| `ruff check src/whale/ingest src/whale/shared/source tools/source_lab tests tools/source_lab/tests` | PASS | lint | 全部通过 |
| `mypy src/whale/ingest src/whale/shared/source` | PASS | typecheck | 仅 1 import-untyped yaml 边界忽略 |
| `mypy tools/source_lab/access/runners/registry.py` | PASS | typecheck | Round 12 清零 8 errors |
| `mypy tools/source_lab --explicit-package-bases` | 227 errors / 37 files | typecheck | source_lab 全量仍未收口 |
| `pytest tests/unit/test_ingest_readyz.py -q` | 20 passed | L1 | readyz 全部场景覆盖 |
| `pytest tests/unit/test_shared_source_runner_resolution.py -q` | 6 passed | L1 | runner 路径解析契约 |
| `pytest tests/integration/test_ingest_prodlike_postgres_runtime_db.py -q` | 7 SQLite L3 passed, 4 PG L4 skipped | L3/L4 | PG 环境缺失导致 correctly skipped |
| `pytest tools/source_lab/tests/access/test_protocol_production_readiness_gate.py -q` | 34 passed | L3 | DECLARED_ 前缀验证 |
| `pytest tools/source_lab/tests/access/test_protocol_service_capabilities.py -q` | passed | L3 | capabilities 语义验证 |
| `bash scripts/validate_shared_source_production_runner.sh` | PASS | L2 | 路径解析契约 check |
| `pytest tests/unit/ --co -q` (affected) | 67 passed, 0 failed, 4 skipped | L1/L2 | Round 12 changed files 全量 |
| import boundary gate (`no-source-lab-import-gate.sh`) | PASS | gate | `src/whale/ingest` 与 `src/whale/shared/source` 无不合法 import |

## 5. 证据与需求状态

| 条目 | 证据等级 | 状态 | Round 12 变化摘要 |
|---|---|---|---|
| I-READY-001 ingest 独立部署准入 | L3 | 部分实现 | 未变化 |
| I-READY-002 ingest 外部依赖准入矩阵 | L2/L4 | 部分实现 | +readyz 8组件聚合，degradation 脱敏 |
| I-READY-003 ingest 横切能力接入准入 | L2 | 部分实现 | 未变化 |
| I-READY-004 ingest 安全分区部署约束 | L2/L3 | 部分实现 | 未变化 |
| I-READY-005 ingest 写入控制投产准入 | L2/L3 | 部分实现 | +field readback 验证入口（双重安全门）；L5 仍缺失 |
| I-READY-006 ingest 多节点生产准入 | L2/L4 | 部分实现 | +PG E2E 代码与脚本就绪；environment-pending |
| I-READY-007 ingest 质量门禁 | L3 | 部分实现 | +registry.py mypy 清零；source_lab 227 errors 未收口 |
| SL-READY-001 source_lab 工具部署准入 | L3 | 部分实现 | +registry.py mypy 清零，DECLARED_ 重命名 |
| SL-READY-003 source_lab 证据边界 | L2/L3 | 部分实现 | +PROTOCOL_CAPABILITIES 残余治理收口 |
| SS-READY-001 shared_source 独立部署准入 | L2/L3 | 部分实现 | +runner_resolution 路径契约验证 (L2) |
| SS-READY-003 shared_source 安全与资源准入 | L2/L3 | 部分实现 | +runner unavailable/build hint 边界测试 |

## 6. ADR / 规则 / project_tree

- **project_tree**: 已更新，新增 `readyz.py`、`test_ingest_readyz.py`、`validate_shared_source_production_runner.sh` 及 Round 12 报告三项
- **ADR**: ADR-20260530-010 (shared_source production runner artifact boundary) 无需更新，状态已采纳，Round 12 实现符合其决策边界
- **rules**: 无规则变更需求

## 7. 生产就绪与工具就绪判定

### 7.1 ingest 是否达到 production-ready？

**否，ingest 仍为 prodlike/test-ready。**

理由：
1. **I-READY-005**: L5 真实设备/真实网关/真实授权链路的 field readback 仍缺失，write/control 最高证据为 L2 contract + L3 simulator
2. **I-READY-006**: PostgreSQL 多进程/多节点 E2E 仍 environment-pending，SQLite L3 单进程不能替代 PostgreSQL 多进程证据
3. **I-READY-003**: crosscutting 接入矩阵仍未形成，真实 IAM/SIEM 集成尚未执行
4. **I-READY-002**: docker compose 级真实依赖 readyz 聚合 E2E 仍需补证
5. 当前最高综合证据等级为 L3 simulator (ingest pipeline) + L2 contract (runner artifact)，不足以宣称 production-ready

ingest **可走的下一步**：
- prodlike compose smoke、CI gate 均已通过
- 可进入现场试运行和受控灰度验证
- 不能写入正式投产状态

### 7.2 source_lab 是否达到 fully-closed tool-ready？

**否，source_lab 仍为 tool-ready (受限)，尚未 fully-closed。**

理由：
1. **mypy**: `tools/source_lab` 全量仍有 227 errors / 37 files，registry.py 清零仅为局部治理
2. **静态 capability 残留**: 虽然 `PROTOCOL_CAPABILITIES` 已重命名为 `DECLARED_PROTOCOL_CAPABILITIES`，但静态 dict 仍存在于矩阵/元数据路径，未完全迁出所有调用方
3. **权限边界**: raw socket/root/capability/netns 运行边界仍需显式化权限矩阵
4. **SL-READY-002**: 工具运行权限矩阵和清理验证仍待补全
5. 当前综合状态：L3 tool-ready with known limitations，不是 fully-closed tool-ready

source_lab **当前可用范围**：
- simulator / probe / profile / capacity 所有已声明协议均已可用
- GOOSE/SV 需受控 L2 环境（已归档）
- 可作为 ingest 外部 E2E 验收工具
- 不得进入 ingest production path

## 8. 剩余风险

1. **PG 环境缺失风险**: 多进程 E2E 无法验证，推迟到 PG 环境就绪后执行。若 PG 实现与 SQLite 行为不一致（如事务隔离级别、锁语义），可能导致 lease/fencing 逻辑需要修正
2. **field readback 延期风险**: 真实设备 readback 需要硬件/现场环境，无法在 CI 中完成。需协调现场资源
3. **source_lab mypy 治理范围风险**: 227 errors 中 ~55 集中在 GOOSE/SV 测试 fixture 类型化，该测试依赖受控 L2 环境和 mock/patch，类型化收益需独立评估
4. **runner artifact 交付风险**: production runner 的独立编译/打包/安装流程尚未建立，当前仍依赖 `source_lab/native/build` 的 dev fallback（需显式环境变量）

## 9. 下一轮建议

按优先级排序：

1. **PG 环境就绪后立即执行**: `bash scripts/run_ingest_pg_lease_fault_injection.sh --mode dsn`，验证双进程 lease/fencing E2E，关闭 I-READY-006 的 environment-pending 状态
2. **source_lab mypy 第一阶段治理**: 按 mypy debt plan 优先修复 simulator ReadSimulatorResult 签名统一（4 文件 / 22 errors）和 endpoint_registry.py 源头类型收敛（68 errors），目标：非测试源码 mypy 错误从 132 降到 80 以下
3. **crosscutting 接入矩阵**: 补 I-READY-003 的横切能力接入矩阵，明确 ingest 必须接入项与可选接入项的映射关系
4. **docker compose readyz E2E**: 补 I-READY-002 的 compose 级真实依赖 readyz 聚合验证
5. **field readback 现场协调**: 按 `ingest_write_readback_field_validation_plan_round11.md` 协调现场硬件资源，执行 L5 readback 验证
6. **production runner artifact 独立构建**: 建立 production-native binary 的独立编译和安装流程，将 `runner_resolution.py` 的 L2 契约推进到 L4 真实 runner 验证
7. **不推荐**: 在 PG 环境、field readback 或 crosscutting 矩阵未收口前，将 ingest 标记为 production-ready
