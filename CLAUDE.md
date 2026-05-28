# Claude Code 执行入口

所有输出默认使用中文。除非用户明确要求英文，否则不得以英文作为主要反馈语言。

## 1. 执行定位

Claude Code 是代码执行器和仓库操作执行器。

必须按用户当前 prompt、当前源码、测试、配置、schema 和公共规则执行；不得主动扩展架构设计、重写需求边界或偏离本轮任务范围。

## 2. 共享规则源

本仓库只维护一套公共规则源：

```text
ai_shared/rules/
ai_shared/templates/
ai_shared/agent_config/skills/
```

Claude Code 与 OpenAI Codex 的专用目录只是薄适配层：

```text
.claude/   # Claude Code settings / agents / skills
.codex/    # Codex config / agents / hooks
.agents/   # Codex skills 发现路径，软链接到 .claude/skills
```

不得复制并维护两套语义不同的规则。

## 3. 最小读取策略

禁止启动时无差别读取全部项目文档。

普通编码任务由 subagent 按 handoff 读取必要材料。所有 agent 默认只读取：

```text
ai_shared/rules/routing.md
routing 指定规则
handoff 指定文件
当前相关源码、测试、配置、schema
```

只有涉及项目目标、长期需求、安全合规、架构边界、部署形态时，才读取项目说明、ADR 或历史 reports。

`ai_shared/memory/project_tree.md` 只用于定位和导航，不能替代当前源码读取；定位后必须二次读取真实源码、测试、配置和 schema。

## 4. 固定编码流程

所有编码任务必须使用以下 subagent 流程。主会话只负责编排、handoff、收口，不直接编码、不直接验证、不直接归档文档。

### 4.1 委派实现

主会话必须使用 `@agent-code-implementer` 执行编码实现。

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
2. 必要时使用 `project-tree-read` 定位候选文件。
3. 读取 handoff 指定背景资料、需求、报告或 ADR。
4. 读取当前相关源码、测试、配置、schema，二次确认，不得只依赖 project_tree。
5. 读取 `ai_shared/rules/routing.md`，并按 routing 读取编码、测试、验证、注释相关规则。
6. 使用 `code-quality-gate` 判断注释、docstring、类型、测试和验证要求。
7. 编码、必要中文注释、Google-style docstring、相关测试修改同轮完成。
8. 执行可负担的初步验证。
9. 使用 `changed-files-gate` 输出编码后真实变更范围。
10. 按统一 `Agent result` 格式返回。

### 4.2 委派验证

`code-implementer` 返回后，主会话必须使用 `@agent-test-validator` 做独立验证。

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

`test-validator` 必须完成：

1. 使用 `changed-files-gate` 获取当前真实变更范围。
2. 读取 `ai_shared/rules/testing.md`、`ai_shared/rules/validation-routing.md`、`ai_shared/rules/quality-gate.md`、`ai_shared/rules/python-docstring-cn.md`。
3. 使用 `code-quality-gate` 选择 py_compile、ruff、mypy、pytest 等验证。
4. 不依赖 `code-implementer` 的口头说明，必须基于 Git 工作区和实际文件判断影响范围。
5. 运行 handoff 指定命令和必要补充命令。
6. 检查 `tools.source_lab` 不得进入生产路径。
7. 对 failed、skipped、pending、flaky、环境失败分类。
8. 按统一 `Agent result` 格式返回。

`test-validator` 不得修改源码、测试或文档。若验证失败，主会话必须再次使用 `@agent-code-implementer` 修复，并再次使用 `@agent-test-validator` 验证。

### 4.3 委派文档、目录树、ADR、需求追踪和报告

验证通过或明确存在未验证项后，主会话必须使用 `@agent-project-steward` 处理文档、目录树、ADR、需求跟踪和报告。

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

`project-steward` 必须完成：

1. 使用 `changed-files-gate` 获取当前真实变更范围。
2. 读取 `ai_shared/rules/documentation.md` 和 `ai_shared/rules/reporting.md`。
3. 新增、删除、移动、重命名文件，或文件职责变化时，使用 `project-tree-update`。
4. 影响长期架构、接口契约、schema、部署策略或 rejected option 时，判断是否使用 `adr-upsert`。
5. 需求状态变化时，使用 `requirement-trace`。
6. 需要归档报告时，使用 `report-archive`。
7. 规则体系变化时，使用 `rule-update`。
8. 只根据已验证证据更新状态，不得把 skipped、mock、fake、health check、TCP connect、脚本存在、环境 pending 写成真实通过。
9. 按统一 `Agent result` 格式返回。

`project-steward` 不得修改源码和测试，除非 handoff 明确授权。

### 4.4 主会话收口

主会话收到 subagent 结果后，必须完成：

1. 汇总修改文件、行为变化、测试结果、文档变化。
2. 检查是否仍有 failed、未验证项、证据不足或状态高估。
3. 必要时继续委派对应 subagent 修复、验证或更新文档。
4. 按 `ai_shared/rules/reporting.md` 中文简洁反馈。

主会话不得把 subagent 的口头结论当成最终证据；最终反馈必须基于文件变更、测试命令、报告或需求跟踪表中的可核验证据。

## 5. 统一 handoff 与返回格式

### 5.1 Agent handoff

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

### 5.2 Agent result

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

主会话最终反馈必须能由各 agent 的 `Agent result` 直接合成，不得要求用户再整理日志。

## 6. 编码、注释、docstring 硬要求

1. Python 新增或修改的 public class / public function / public method 应有类型标注。
2. public interface、use case、port、adapter、复杂调度、协议解析、错误边界、性能指标必须有必要 docstring。
3. Python docstring 使用 Google-style；正文和说明默认中文。
4. 代码注释默认中文，除非引用外部协议字段、第三方 API、日志常量、异常类名或英文原文。
5. 注释解释原因、边界、假设和风险，不重复代码表面行为。
6. 不允许无解释 `type: ignore`、裸 `except`、静默吞异常、fake OK。
7. 不允许通过降低断言、删除测试、扩大 skip 制造通过。

## 7. 用户主动触发项

以下操作不得自动执行，必须由用户明确要求或 prompt 明确指定：

```text
project-tree-reset
heavy-regression
commit-message
adr-upsert
rule-update
feedback-archive
全量测试、长测、发布前完整验证
commit / push / reset / clean
```

说明：如果流程中需要判断是否执行 `adr-upsert`、`requirement-trace`、`project-tree-update`，由 `project-steward` 按规则判断；真正创建或修改 ADR、规则文件时，必须有 handoff 或用户 prompt 支持。

## 8. 禁止事项

- 不主动扩展架构设计。
- 不凭记忆推断 schema、配置、接口、文件结构。
- 不无关重构。
- 不恢复废弃文件。
- 不新增未经确认的兼容 shim。
- 不为了通过测试而降低断言或删除测试。
- 不自动执行 commit、push、reset、clean。
- 不默认运行重回归或长测。
- 不把 `tools.source_lab` 引入 `src/whale/ingest` 或 `src/whale/shared/source` 生产路径。

## 9. 固定反馈

每轮完成后按 `ai_shared/rules/reporting.md` 反馈，必须说明：

```text
修改文件
行为变化
Agent / subagent 使用情况
检查与测试
未验证项
project_tree / ADR / report 状态
剩余风险
下一步建议
```
