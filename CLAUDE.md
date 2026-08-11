# Claude Code / Codex 执行入口

所有输出默认使用中文。除非用户明确要求英文，否则不得以英文作为主要反馈语言。

## 0. 确认环境

确认当前conda环境是BlueCrystal，否则报错，不要执行任何指令。先执行source .env.local获得当前系统变量。

## 1. 执行定位

Claude Code / Codex 是代码执行器和仓库操作执行器。

必须按用户当前 prompt、当前源码、测试、配置、schema 和公共规则执行；不得主动扩展架构设计、重写需求边界或偏离本轮任务范围。

## 2. 共享规则源

本仓库只维护一套公共规则源：

```text
ai_shared/rules/
ai_shared/templates/
ai_shared/agent_config/skills/
ai_shared/agent_config/hooks/
```

工具专用目录只是薄适配层：

```text
.claude/
.codex/
.agents/
```

不得复制并维护两套语义不同的规则。需要规则变更时，以 `ai_shared/rules/` 和 `ai_shared/agent_config/skills/` 为准。

## 3. 最小读取策略

禁止启动时无差别读取全部项目文档。

普通编码任务由 subagent 按 handoff 读取必要材料。所有 agent 默认只读取：

```text
ai_shared/rules/routing.md
routing 指定规则
handoff 指定文件
当前相关源码、测试、配置、schema
```

只有涉及项目目标、长期需求、安全合规、架构边界、部署形态时，才读取项目说明或历史 reports。

`ai_shared/memory/project_tree.md` 只用于定位和导航，不能替代当前源码读取；定位后必须二次读取真实源码、测试、配置和 schema。

## 4. 任务等级 light/standard/full

主会话只负责编排、handoff、收口，不直接编码、不直接验证、不直接归档长期文档。所有非平凡任务必须先判断任务等级，再决定链路与验证深度。

### 4.0 任务等级定义

| 等级 | 典型场景 | 链路 | 验证 | 报告 |
|---|---|---|---|---|
| `light` | typo、纯文档/注释/规则文字、查询、REQ 状态调整、目录树更新 | 主会话直接处理，不委派任何 subagent | 不进入验证阶段 | 一句话反馈（reporting.md §3.0） |
| `standard` | 改源码但不改变对外契约 | `code-implementer` → 主会话收口 | 受影响 unit + syntax + lint 最小集 | 4 字段 `Agent result`（reporting.md §2.2） + standard 主会话反馈（reporting.md §3.2） |
| `full` | 用户显式要求；或 `standard` 命中白名单自动升级 | `code-implementer` → `test-validator` → `project-steward` → 主会话收口 | 完整 8 项质量门禁 + 验证路由表 | 12 字段 `Agent result`（reporting.md §2.1） + 报告文件 + full 主会话反馈（reporting.md §3.1） |

`tier_hint` 由 `changed-files-gate` 给出，但最终 `task_tier` 由主会话判断；命中白名单时由 `code-implementer` 声明 `require_full_validation=true` 自动升级。

### 4.1 light 任务

1. 主会话直接处理：Edit / Write / Bash 等同于一次普通编辑。
2. 不启动 `code-implementer` / `test-validator` / `project-steward`。
3. 不调用 `code-quality-gate`。
4. 反馈使用 reporting.md §3.0 的一句话模板。
5. 不写报告文件。

### 4.2 standard 任务（默认）

1. 主会话只委派 `code-implementer`。
2. `code-implementer` 跑受影响 unit + syntax + lint 最小集，按 reporting.md §2.2 输出 4 字段 `Agent result`。
3. `code-implementer` 在白名单命中时声明 `require_full_validation=true`，主会话据此追加 `test-validator` 和 `project-steward`，并向用户事后告知。
4. 不委派 `test-validator`（除非自动升级触发）。
5. `project-steward` 仅在文件增删/重命名/职责变化、需求状态变化、规则变化时启动。

handoff 必须包含 `task_tier: standard` 字段；code-implementer 必须按 routing.md §2 的 `task_tier=standard` 读取策略跳过 `validation-routing.md` 全文。

`code-implementer` 必须完成：

1. 使用 `changed-files-gate` 获取编码前变更范围。
2. 读取 handoff 指定背景资料、需求、报告或设计资料。
3. 必要时读取 `ai_shared/memory/project_tree.md` 定位候选文件；该读取是普通导航动作，不使用 skill。
4. 在修改前识别目标路径或模块是否已有稳定的分层方式、依赖方向、扩展缝和职责切分，并判断本轮是否只是既有架构中的局部扩展。
5. 若属于既有架构中的局部扩展，默认沿用当前模式、边界和装配方式；只有用户 prompt 明确要求，或现有实现已与任务约束冲突时，才改变设计方式，并在结果中说明原因。
6. 涉及目录归属或新文件落点时，先判断该内容属于运行时代码还是部署交付资产；运行时代码留在既有源码目录，部署清单、样例配置、环境模板、发布/回滚 runbook 等落入 `deploy/`，不得为了集中管理把运行时代码迁入 `deploy/`。
7. 读取当前相关源码、测试、配置、schema，二次确认，不得只依赖 project_tree。
8. 读取 `ai_shared/rules/routing.md`，并按 `task_tier=standard` 跳过 `validation-routing.md` 全文。
9. 使用 `code-quality-gate` 的 standard 子集（syntax + 受影响 unit + 注释/类型最小集）。
10. 编码、必要注释、语言惯用文档注释、相关测试修改同轮完成。
11. 执行可负担的初步验证。
12. 使用 `changed-files-gate` 输出编码后真实变更范围。
13. 按 4 字段 `Agent result` 格式返回；若命中白名单则额外声明 `require_full_validation=true` 并说明命中条款。

### 4.3 full 任务

1. 主会话按 `code-implementer` → `test-validator` → `project-steward` → 主会话收口 全链路委派。
2. `code-implementer` 跑完整 8 项质量门禁，按 reporting.md §2.1 输出 12 字段 `Agent result`。
3. `test-validator` 独立验证，必须基于 Git 工作区真实状态判断影响范围，按验证路由表执行 must-run / should-run。
4. `project-steward` 必启动，按 `documentation.md` + `reporting.md` 更新文档、目录树、需求跟踪、报告归档。
5. 主会话反馈使用 reporting.md §3.1 full 模板，并输出报告文件至 `ai_shared/reports/`。

handoff 必须包含 `task_tier: full` 字段；三个 subagent 都按 routing.md 对应段的 `task_tier=full` 读取策略全读规则。

`code-implementer` 必须完成：

1. 使用 `changed-files-gate` 获取编码前变更范围。
2. 读取 handoff 指定背景资料、需求、报告或设计资料。
3. 必要时读取 `ai_shared/memory/project_tree.md` 定位候选文件；该读取是普通导航动作，不使用 skill。
4. 在修改前识别目标路径或模块是否已有稳定的分层方式、依赖方向、扩展缝和职责切分，并判断本轮是否只是既有架构中的局部扩展。
5. 若属于既有架构中的局部扩展，默认沿用当前模式、边界和装配方式；只有用户 prompt 明确要求，或现有实现已与任务约束冲突时，才改变设计方式，并在结果中说明原因。
6. 涉及目录归属或新文件落点时，先判断该内容属于运行时代码还是部署交付资产；运行时代码留在既有源码目录，部署清单、样例配置、环境模板、发布/回滚 runbook 等落入 `deploy/`，不得为了集中管理把运行时代码迁入 `deploy/`。
7. 读取当前相关源码、测试、配置、schema，二次确认，不得只依赖 project_tree。
8. 读取 `ai_shared/rules/routing.md`，按 `task_tier=full` 全读规则。
9. 使用 `code-quality-gate` 走完整 8 项。
10. 编码、必要注释、语言惯用文档注释、相关测试修改同轮完成。
11. 执行可负担的初步验证。
12. 使用 `changed-files-gate` 输出编码后真实变更范围。
13. 按 12 字段 `Agent result` 格式返回。

`test-validator` 必须完成：

1. 使用 `changed-files-gate` 获取当前真实变更范围。
2. 读取 `ai_shared/rules/testing.md`、`validation-routing.md`、`quality-gate.md`、`python-docstring-cn.md`。
3. 使用 `code-quality-gate` 选择适合 changed files 语言和影响范围的验证命令。
4. 不依赖 `code-implementer` 的口头说明，必须基于 Git 工作区和实际文件判断影响范围。
5. 运行 handoff 指定命令和必要补充命令。
6. 检查生产路径不得引入工具/实验模块依赖。
7. 对 failed、skipped、pending、flaky、环境失败分类。
8. 按 12 字段 `Agent result` 格式返回。

`test-validator` 不得修改源码、测试或文档。若验证失败，主会话必须再次使用 `code-implementer` 修复，并再次使用 `test-validator` 验证。

`project-steward` 必须完成：

1. 使用 `changed-files-gate` 获取当前真实变更范围。
2. 读取 `ai_shared/rules/documentation.md` 和 `reporting.md`。
3. 新增、删除、移动、重命名文件，或文件职责变化时，使用 `project-tree-update`。
4. 需求状态变化时，使用 `requirement-trace`。
5. 需要归档报告时，直接按 `reporting.md` 写入 `ai_shared/reports/`，不再使用 report-archive skill。
6. 规则体系变化时，使用 `rule-update`。
7. 只根据已验证证据更新状态，不得把 skipped、mock、fake、health check、TCP connect、脚本存在、环境 pending 写成真实通过。
8. 按 12 字段 `Agent result` 格式返回。

`project-steward` 不得修改源码和测试，除非 handoff 明确授权。

### 4.4 standard → full 自动升级白名单

`code-implementer` 收到 `task_tier=standard` handoff 时，按以下白名单判定；命中任一条即自动升级为 `full`，在 Agent result 中声明 `require_full_validation=true` 并说明命中条款，主会话据此追加 `test-validator` 与 `project-steward`，并向用户事后告知：

1. 改 public interface / API / CLI / handler。
2. 改 schema / migration / 配置 / 环境变量。
3. 改消息格式 / 协议 / 文件格式。
4. 改 adapter / repository / external client / gateway。
5. 改 runtime / scheduler / worker / lease / fencing。
6. 改安全 / 权限 / 审计 / 凭据。
7. 改 `deploy/` / docker / compose / helm / terraform。
8. 跨 ≥3 个 module（按 `src/<module>/` 一级目录计数）。
9. handoff 显式标注 `task_tier=full`。
10. handoff 显式引用 `heavy-regression` skill。

### 4.5 反馈格式按等级区分

- `light`：reporting.md §3.0 一句话反馈。
- `standard`：reporting.md §2.2 的 4 字段 `Agent result` + §3.2 的 standard 主会话反馈。
- `full`：reporting.md §2.1 的 12 字段 `Agent result` + §3.1 的 full 主会话反馈 + `ai_shared/reports/<scope>_<topic>_<date>.md` 报告文件。

### 4.6 主会话职责

主会话只负责编排、handoff、收口，不直接编码、不直接验证、不直接归档长期文档。这一原则在三种等级下一致生效；`light` 任务的"主会话直接处理"是主会话本身动手 Edit / Write，不是委派给 subagent。

## 5. Agent result 格式

按 `task_tier` 选择对应模板，完整定义在 [ai_shared/rules/reporting.md](ai_shared/rules/reporting.md) §2：

- `light`：不输出 `Agent result`。
- `standard`：4 字段（reporting.md §2.2）— `files changed` / `passed` / `failed` / `not-run`。
- `full`：12 字段（reporting.md §2.1）：

```text
Agent result:
- agent:
- files read:
- files changed:
- rules used:
- skills used:
- commands run:
- passed:
- failed:
- skipped:
- pending:
- evidence:
- risk:
- next handoff suggestion:
```

## 6. 编码、注释、文档注释硬要求

1. 新增或修改的 public interface 应有类型、签名或 schema。
2. public interface、use case、port、adapter、runner、复杂调度、协议解析、错误边界、性能指标必须有必要文档注释。
3. 使用目标语言惯用文档注释格式：Python docstring、JSDoc/TSDoc、JavaDoc/KDoc、Go doc comment、Rust doc comment、Doxygen、Shell 函数注释等。
4. 注释默认使用项目主要语言，除非引用外部协议字段、第三方 API、日志常量、异常类名、命令或英文原文。
5. 注释解释原因、边界、假设和风险，不重复代码表面行为。
6. 不允许无解释的类型/lint 抑制指令、裸 catch/except/rescue、静默吞异常、fake OK。
7. 不允许通过降低断言、删除测试、扩大 skip 制造通过。

## 7. 用户主动触发项

以下操作不得自动执行，必须由用户明确要求或 prompt 明确指定：

```text
project-tree-reset
heavy-regression
commit-message
rule-update
全量测试、长测、发布前完整验证
commit / push / reset / clean
其他会修改 Git 历史、工作区状态或远端仓库状态的 Git/GitHub 写操作
```

如果流程中需要判断是否执行 `requirement-trace`、`project-tree-update`，由 `project-steward` 按规则判断；真正创建或修改规则文件时，必须有 handoff 或用户 prompt 支持。

## 8. 禁止事项

- 不主动扩展架构设计。
- 不凭记忆推断 schema、配置、接口、文件结构。
- 不无关重构。
- 不恢复废弃文件。
- 不新增未经确认的兼容 shim。
- 不为了通过测试而降低断言或删除测试。
- 不自动执行 commit、push、reset、clean。
- 不自动执行其他会修改 Git 历史、工作区状态或远端仓库状态的 Git/GitHub 写操作。
- 不默认运行重回归或长测。
- 不把工具/实验模块引入生产路径。

## 9. 固定反馈

每轮完成后按 `ai_shared/rules/reporting.md` 反馈。
