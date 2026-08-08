# Claude Code / Codex 执行入口

所有输出默认使用中文。除非用户明确要求英文，否则不得以英文作为主要反馈语言。

## 0. 确认环境

确认当前conda环境是BlueCrystal，否则报错，不要执行任何指令。

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

## 4. 固定三段式流程

对于非平凡编码任务必须使用以下流程。主会话只负责编排、handoff、收口，不直接编码、不直接验证、不直接归档长期文档。

```text
code-implementer -> test-validator -> project-steward -> 主会话收口
```

### 4.1 委派实现

主会话必须使用 `code-implementer` 执行源码、测试、脚本或配置修改。

handoff 必须包含：

```text
Agent handoff:
- task:
- allowed paths:
- forbidden:
- required files:
- changed files:
- evidence available:
- rules to read:
- skills to use:
- commands to run:
- expected output:
```

`code-implementer` 必须完成：

1. 使用 `changed-files-gate` 获取编码前变更范围。
2. 读取 handoff 指定背景资料、需求、报告或设计资料。
3. 必要时读取 `ai_shared/memory/project_tree.md` 定位候选文件；该读取是普通导航动作，不使用 skill。
4. 在修改前识别目标路径或模块是否已有稳定的分层方式、依赖方向、扩展缝和职责切分，并判断本轮是否只是既有架构中的局部扩展。
5. 若属于既有架构中的局部扩展，默认沿用当前模式、边界和装配方式；只有用户 prompt 明确要求，或现有实现已与任务约束冲突时，才改变设计方式，并在结果中说明原因。
6. 涉及目录归属或新文件落点时，先判断该内容属于运行时代码还是部署交付资产；运行时代码留在既有源码目录，部署清单、样例配置、环境模板、发布/回滚 runbook 等落入 `deploy/`，不得为了集中管理把运行时代码迁入 `deploy/`。
7. 读取当前相关源码、测试、配置、schema，二次确认，不得只依赖 project_tree。
8. 读取 `ai_shared/rules/routing.md`，并按 routing 读取编码、测试、验证、注释相关规则。
9. 使用 `code-quality-gate` 判断注释、文档注释、类型、测试和验证要求。
10. 编码、必要注释、语言惯用文档注释、相关测试修改同轮完成。
11. 执行可负担的初步验证。
12. 使用 `changed-files-gate` 输出编码后真实变更范围。
13. 按统一 `Agent result` 格式返回。

### 4.2 委派验证

`code-implementer` 返回后，主会话必须使用 `test-validator` 做独立验证。

`test-validator` 必须完成：

1. 使用 `changed-files-gate` 获取当前真实变更范围。
2. 读取 `ai_shared/rules/testing.md`、`validation-routing.md`、`quality-gate.md`、`python-docstring-cn.md`。
3. 使用 `code-quality-gate` 选择适合 changed files 语言和影响范围的验证命令。
4. 不依赖 `code-implementer` 的口头说明，必须基于 Git 工作区和实际文件判断影响范围。
5. 运行 handoff 指定命令和必要补充命令。
6. 检查生产路径不得引入工具/实验模块依赖。
7. 对 failed、skipped、pending、flaky、环境失败分类。
8. 按统一 `Agent result` 格式返回。

`test-validator` 不得修改源码、测试或文档。若验证失败，主会话必须再次使用 `code-implementer` 修复，并再次使用 `test-validator` 验证。

### 4.3 委派文档、目录树、需求追踪和报告

验证通过或明确存在未验证项后，主会话必须使用 `project-steward` 处理文档、目录树、需求跟踪和报告。

`project-steward` 必须完成：

1. 使用 `changed-files-gate` 获取当前真实变更范围。
2. 读取 `ai_shared/rules/documentation.md` 和 `reporting.md`。
3. 新增、删除、移动、重命名文件，或文件职责变化时，使用 `project-tree-update`。
4. 需求状态变化时，使用 `requirement-trace`。
5. 需要归档报告时，直接按 `reporting.md` 写入 `ai_shared/reports/`，不再使用 report-archive skill。
6. 规则体系变化时，使用 `rule-update`。
7. 只根据已验证证据更新状态，不得把 skipped、mock、fake、health check、TCP connect、脚本存在、环境 pending 写成真实通过。
8. 按统一 `Agent result` 格式返回。

`project-steward` 不得修改源码和测试，除非 handoff 明确授权。

## 5. Agent result 格式

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
