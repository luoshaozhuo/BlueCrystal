# 测试生命周期化重构与全仓规则审核 Round 1 收口报告

> 日期: 2026-06-03
> 范围: 测试体系生命周期化重构 -> 全仓规则审核 -> 目录树/报告收口
> 状态: 收口完成（本轮目标全部达成，无 FAIL）
> 验证生命周期阶段: 文档/规则/报告变化（构建期验证 should-run）

## 1. 总览

| 项 | 结果 |
|---|---|
| 修改文件 | 7 个（5 规则修改 + 2 新增） |
| 新增文件 | `ai_shared/memory/test_index.md`、`scripts/whale_test.sh` |
| 验证命令 | 3 个，全部 PASS |
| 规则语义冲突 | 无新增冲突（quality-gate.md 既有不一致已记录） |
| project_tree 更新 | 已完成（增量更新） |
| ADR | 无需更新（本轮为规则重构，不涉及架构决策） |
| 全仓审核 | 已完成（9 条发现） |
| 生命周期阶段迁移 | testing.md：7 阶段完成，L1-L5 证据等级已移除 |
| NOT_RUN 枚举 | 6 个枚举值统一应用于 testing/reporting/validation-routing |

## 2. 修改文件

| 文件 | 操作 | 说明 |
|---|---|---|
| `ai_shared/rules/testing.md` | 修改 | 39行->276行：补齐七个生命周期阶段、回归测试规则、NOT_RUN 枚举、测试目录边界、test_index 规则 |
| `ai_shared/rules/validation-routing.md` | 修改 | 65行->231行：补齐变更类型->生命周期阶段->优先级路由、5 组件按子模块路由细化、收口和失败分类规则 |
| `ai_shared/rules/reporting.md` | 修改 | 209行->242行：移除 pending/skipped 字段、新增 NOT_RUN 原因枚举、next handoff 分类、禁止 L1-L5 引用 |
| `ai_shared/rules/coding.md` | 修改 | 补齐测试同步规则、测试失败判断优先级、测试行为约束 |
| `ai_shared/rules/python-docstring-cn.md` | 修改 | 补齐生命周期阶段要求、测试文件头 6 项说明、NOT_RUN 条件 |
| `ai_shared/memory/test_index.md` | 新增 | 初版：目录级完整+关键链路文件级；Whale 测试资产索引（7 阶段）+ source_lab 索引 + 回归测试索引 + 回归套件定义 |
| `scripts/whale_test.sh` | 新增 | Whale 测试统一入口（dry-run）：支持 --stage/--component/--module/--suite 参数，输出测试计划 |

## 3. 行为变化

- **testing.md**: 从 L1-L5 证据等级主轴迁移为七个生命周期阶段主轴（开发期验证 -> 发布后运维验证期）。L5 marker 保留为技术标签，语义等同于"准生产依赖验证期"。
- **validation-routing.md**: 从简单规则路由扩展为变更类型->生命周期阶段->必须/建议/手动三级优先级路由。细化到 ingest/message_pipeline/speed_layer/storage/shared_source 子模块级命令。
- **reporting.md**: Agent result 格式移除 `pending` 和 `skipped` 字段，统一为 `passed/failed/not-run`。pytest skipped 测试归入 NOT_RUN。新增 NOT_RUN 6 原因枚举和 next handoff 13 分类。
- **coding.md/python-docstring-cn.md**: 补齐测试同步规则、测试文件头生命周期阶段要求、NOT_RUN 条件说明。
- **test_index.md**: 建立唯一回归索引文件，禁止新建 `issue_regression_index.md` 等旁路索引。
- **whale_test.sh**: 测试统一入口（dry-run），不执行实际测试命令，按参数输出测试计划。

## 4. 生命周期测试分类

按 `testing.md` 定义，所有测试归属到七个生命周期阶段：

| 阶段 | 典型 marker | 典型目录 | 核心特征 |
|---|---|---|---|
| 开发期验证 | `unit` | `tests/unit/` | 纯逻辑、接口约束、无外部依赖 |
| 构建期验证 | 非 pytest | `py_compile`/`ruff`/`mypy`/`cmake` | 编译、lint、type-check、import 边界 |
| 模块集成期验证 | `integration` | `tests/integration/` 无外部服务 | SQLite/fake/mock/stub/in-memory 闭环 |
| 跨模块联调期验证 | `integration`/`e2e` | docker-compose 测试 | 跨模块数据流、消息管道、simulator 全链路 |
| 准生产依赖验证期 | `l5` | 需外部服务 | 真实 Kafka/PG/Redis/S3/TDengine |
| 部署前验收期 | `e2e`/`smoke` | field smoke 测试 | 部署配置、环境预检、最小数据链路 |
| 发布后运维验证期 | 非 pytest | 运维脚本、监控 probe | 健康检查、故障恢复、主备切换 |

**l5 marker 保留说明**: `l5` 作为历史技术标签保留在 pyproject.toml 中，语义等同于"准生产依赖验证期"。后续可逐步迁移为 `external` 或 `prodlike`，旧测试不需要迁移。

## 5. PASS / FAIL / NOT_RUN 规则

### 测试执行结果三元组

| 结果 | 含义 |
|---|---|
| **PASS** | 测试通过 |
| **FAIL** | 测试失败 |
| **NOT_RUN** | 未执行，必须说明原因枚举 |

### NOT_RUN 原因枚举

| 原因 | 说明 |
|---|---|
| `OUT_OF_SCOPE` | 不属本轮验证范围 |
| `MISSING_ENVIRONMENT` | 环境不满足（缺少服务、配置、硬件） |
| `MISSING_DEPENDENCY` | 依赖缺失（库、二进制、工具） |
| `MANUAL_REQUIRED` | 需人工操作（物理设备、手动步骤） |
| `TOO_EXPENSIVE_FOR_THIS_ROUND` | 本轮流价太高（长时间运行、资源消耗） |
| `USER_NOT_REQUESTED` | 用户未要求执行 |

### 禁止规则

- 不允许 `pending` 作为 Agent result 字段（已从格式中移除）
- pytest skipped 测试归入 NOT_RUN 并说明 skip 原因
- 不做把 skipped/mock/fake/health check 写成真实通过
- 不做把单文件 passed 声称全量通过

## 6. test_index 初版说明

- **路径**: `ai_shared/memory/test_index.md`
- **定位**: Whale 项目唯一测试索引，不另建其他回归索引文件
- **覆盖范围**:
  - 3.1 Whale 主平台测试 (tests/)：开发期验证 82 文件、模块集成期验证 30 文件、跨模块联调期验证 11 文件、准生产依赖验证期 3 文件、部署前验收期 2 文件
  - 3.2 source_lab 工具测试 (tools/source_lab/tests/)：开发期验证、模块集成期验证、准生产依赖验证期
- **回归测试索引**: 17 条回归测试，按 defect-regression/operation-regression 分类，状态全部 ACTIVE
- **回归套件**: affected/module/chain/release 四套件定义

## 7. 回归测试统一索引设计

回归测试统一进入 `test_index.md`，不另建其他回归索引文件。

### 回归来源分类

| 分类 | 说明 |
|---|---|
| defect-regression | bug 修复后新增的回归测试 |
| operation-regression | 故障恢复、主备切换、重启恢复 |
| compatibility-regression | 协议版本、消息格式、API 版本兼容性 |
| chain-regression | 跨模块链路验证 |
| release-regression | 发布前指令套件 |

### 回归套件执行时机

| 套件 | 执行时机 | 典型范围 |
|---|---|---|
| affected regression | 每次变更 | 变更文件对应测试 + 相关回归 |
| module regression | 修改 public interface/schema/config | 模块 unit+integration |
| chain regression | 跨模块影响 | 上下游模块集成测试 |
| release regression | 发布前 | 全部 ACTIVE 回归 + module regression |

## 8. reporting/testing 去耦合结果

### reporting.md 变更

- 移除 `pending` 和 `skipped` 字段，Agent result 统一为 `passed/failed/not-run`
- pytest skipped 测试归入 NOT_RUN（而非单独 skipped 列）
- 不再引用 L1-L5 证据等级（改为引用 testing.md 的生命周期阶段）
- 报告中的验证范围必须说明生命周期阶段和测试来源
- 报告不重复定义测试分类（以 testing.md 为准）

### testing.md 变更

- 从 L1-L5 主轴迁移为七个生命周期阶段主轴
- L5 保留为历史技术标签（语义等同准生产依赖验证期）
- 不引用 reporting.md（保持独立）

### 去耦合验证

- testing.md 定义测试分类和生命周期阶段
- reporting.md 定义报告格式，引用 testing.md 的阶段定义
- 两文件无循环引用，无语义冲突

## 9. 全仓 repo 审核清单

审核范围: `ai_shared/`、`scripts/`、`docs/`、`.claude/`

| 路径 | 类型 | 当前职责 | 问题类型 | 严重度 | 建议动作 | 是否本轮处理 | 理由 |
|---|---|---|---|---|---|---|---|
| `ai_shared/rules/quality-gate.md` | 规则 | 代码质量门禁规则 | doc-rule-overlap | 中 | update-now | 否（待第2轮） | 第49行"未执行 / environment-pending"使用旧格式，第52行"环境 pending"与新 NOT_RUN 枚举不一致。failure 分类表未对齐 testing.md 的 NOT_RUN 枚举 |
| `docs/测试策略.md` | 文档 | 旧版测试策略指南（1421行，Codex 向） | doc-rule-overlap, obsolete | 高 | needs-user-decision | 否（待第2轮） | 与 testing.md/test_index.md/validation-routing.md 语义重叠；使用旧 unit/integration/smoke/e2e/performance 分层（非生命周期阶段）；提及 L1-L5；格式为 Codex policy 而非当前 agent 规则体系 |
| `docs/代码质量与注释.md` | 文档 | 代码质量与注释规范 | doc-rule-overlap | 低 | needs-user-decision | 否（待第2轮） | 与 coding.md/python-docstring-cn.md 语义重叠；作为 docs/ 文档可能被误认为权威规则源 |
| `docker-compose.whale-l5.yaml` | 配置 | L5 外部依赖 5-service Docker 环境 | legacy | 低 | keep（rename later） | 否 | 文件名使用历史 "l5" 标签；配置内容正确，重命名需同步更新引用脚本 |
| `ai_shared/reports/whale_l5_*.md` (5 文件) | 报告 | Round 2-6 历史收口报告 | legacy | 低 | keep | 否 | 历史报告，命名使用旧 "L5" 标签；保留以维持历史记录完整性 |
| `ai_shared/rules/documentation.md` | 规则 | 文档与目录树维护规则 | unclear-boundary | 低 | keep | 否 | 第29行"必须降级或标注 pending"指需求跟踪状态而非测试执行结果，语义正确，不与 NOT_RUN 规则冲突 |
| `ai_shared/rules/coding.md` | 规则 | 编码规范 | unclear-boundary | 低 | keep | 否 | 第162行"标注 pending"同属需求跟踪状态上下文，不与 NOT_RUN 规则冲突 |
| `scripts/whale_test.sh` | 脚本 | 测试统一入口（dry-run） | script-overlap | 低 | keep | 是（本轮新增） | 与 ci_ingest_runtime_gate.sh/run_quality_gate.py 功能边界不同：whale_test.sh 是测试计划输出（dry-run），CI 脚本是实际执行 |
| `.claude/skills/commit-message/SKILL.md` | 技能 | 提交信息生成 | legacy | 低 | keep | 否 | 在 git status 中显示为 MM（staged + unstaged），当前职责不变 |

## 10. 下一轮 tests 与 source_lab/tests 目录治理建议

### 10.1 高优先级（第2轮建议处理）

1. **quality-gate.md 对齐更新**
   - 将 failure 分类表对齐 testing.md 的 NOT_RUN 枚举
   - 将"未执行 / environment-pending"替换为 NOT_RUN 语义
   - 建议动作: `update-now`

2. **docs/测试策略.md 处置决策**
   - 选项 A: 删除，全部规则以 `ai_shared/rules/testing.md` 为准
   - 选项 B: 改名为 `docs/测试策略-历史参考.md` 并标注已过时
   - 选项 C: 精简为面向人类开发者的高层测试原则介绍，去 Codex 化
   - 建议动作: `needs-user-decision`

3. **docs/代码质量与注释.md 处置决策**
   - 选项 A: 删除，指向 coding.md + python-docstring-cn.md
   - 选项 B: 精简为快速参考卡片
   - 建议动作: `needs-user-decision`

### 10.2 中优先级

4. **test_index.md 持续完善**
   - 补充 chain-regression/compatibility-regression/release-regression 的回归测试条目
   - 补充 source_lab 回归测试索引
   - 当有新的缺陷修复或运维故障修复时，追加回归测试条目

5. **whale_test.sh 执行模式补齐**
   - 第2轮实现非 dry-run 模式，支持实际执行 pytest/shell 命令
   - 添加 --no-dry-run 参数

6. **L5 marker 渐进迁移方案**
   - 新增准生产依赖验证测试使用 `l5` marker
   - 评估 `external` 或 `prodlike` 作为新 marker 名称
   - 不强制迁移旧测试

### 10.3 长期观察

7. **source_lab/tests/ 目录治理**
   - 当前 source_lab tests 按 access/ 子目录组织，结构合理
   - 考虑在 tools/source_lab/tests/ 中增加 `integration/` 子目录
   - 保持 source_lab 与 Whale 测试边界隔离

8. **docker-compose.whale-l5.yaml 重命名**
   - 当 L5 marker 正式迁移后，同步重命名 docker-compose 文件
   - 同步更新所有引用脚本

## 11. project_tree / ADR / 规则

- **project_tree**: 已增量更新。新增 `test_index.md`（ai_shared/memory/）、`whale_test.sh`（scripts/）。更新 5 个规则文件职责说明（testing/validation-routing/reporting/coding/python-docstring-cn）。
- **ADR**: 无需更新。本轮为规则体系重构和测试体系生命周期化，不涉及长期架构决策、接口契约、schema 或部署策略变化。
- **rules**: 5 个规则文件已在本轮修改完成。quality-gate.md 的对齐更新建议排入第2轮。

## 12. 验证命令结果

| 命令 | 结果 | 说明 |
|---|---|---|
| `test ! -d ai_shared/field_readback` | PASS | field_readback 目录不存在，确认已清理 |
| `test ! -f ai_shared/memory/issue_regression_index.md` | PASS | 无旁路回归索引文件 |
| `grep -R "pending" ai_shared/rules ai_shared/memory/test_index.md` | PASS | 仅在否定语境（不应/禁止使用 pending）和 environment_pending marker 定义中出现，未发现将 pending 用作测试执行结果的违规 |

## 13. 剩余风险

- **quality-gate.md 语义滞后**: 当前 COVERAGE.md/gate 仍使用"环境 pending"旧术语，可能在质量门禁判断时产生歧义。建议第2轮优先对齐。
- **docs/测试策略.md 双轨风险**: 如果持有两份测试体系文档（docs/测试策略.md + ai_shared/rules/testing.md），可能造成 agent 和开发者使用不同规则体系。建议尽快处置。
- **test_index.md 维护成本**: 测试资产索引需随测试文件增删持续维护。当前初版已完成目录级完整覆盖，后续需保持同步。

## 14. 下一步建议

1. **docs/ 文档处置**: 用户决策 docs/测试策略.md 和 docs/代码质量与注释.md 的保留/删除/重构方案。
2. **quality-gate.md 对齐**: code-implementer 修改 quality-gate.md 的 failure 分类表和"环境 pending"引用，对齐 testing.md 的 NOT_RUN 枚举。
3. **whale_test.sh 执行模式**: 实现非 dry-run 模式，支持实际测试执行。
4. **回归测试索引完善**: 补充 chain-regression/compatibility-regression/release-regression 条目。
