# Claude Code / Codex 共用执行入口

本文件是本仓库 AI coding agent 的主入口规则。Claude Code 应直接读取本文件；Codex 通过根目录 `AGENTS.md` 被要求读取本文件。

所有 Claude Code / Codex 输出默认使用中文。除非用户明确要求英文，否则不得用英文作为主要反馈语言。

## 1. 角色定位

本项目的方案讨论、边界判断、prompt 生成主要在 ChatGPT / Gemini / DeepSeek 网页端完成。

Claude Code / Codex 的定位是：

```text
代码执行器 + 仓库操作执行器
```

执行器应按用户给出的上下文无关 prompt、当前仓库源码和公共规则完成工作，不主动扩展架构设计。

## 2. 优先级

1. 用户当前消息优先。
2. 用户提供的本轮执行 prompt 优先。
3. 当前仓库源码、测试、配置、schema 是事实来源。
4. 本文件优先于旧配置。
5. `ai_shared/rules/` 是公共规则源。
6. `ai_shared/memory/project_tree.md` 只用于导航，不替代读取当前源码。

用户 prompt 可以限定任务目标和范围，但不得要求 agent 跳过事实确认、跳过必要测试、削弱断言、忽略当前源码或绕过公共规则。

## 3. 不默认读取全部文档

禁止启动时或任务开始时无差别读取所有文档。

执行任务时按需读取：

1. 本文件。
2. `ai_shared/rules/routing.md`。
3. routing 指定的必要规则。
4. 必要时读取 `ai_shared/memory/project_tree.md`。
5. 必要时查找并读取 `ai_shared/memory/` 下所有文件名含"项目说明"的文件。
6. 当前相关源码、测试、配置、schema。

普通代码修改不读取完整项目说明，不读取全部 ADR，不读取全部规则。

## 4. 固定编码流程

非平凡编码任务必须按以下流程执行：

1. 读取本文件。
2. 读取 `ai_shared/rules/routing.md`。
3. 根据任务类型读取必要规则。
4. 如果需要文件定位、跨模块影响判断、新增文件位置判断，执行 `project-tree-read` 流程。
5. 读取当前相关源码、测试、配置、schema。
6. 编码、测试、必要注释修改同轮完成。
7. 根据 `ai_shared/rules/validation-routing.md` 执行最小必要验证。
8. 修复本轮引入的失败。
9. 如果新增、删除、移动、重命名文件，或文件职责变化，执行 `project-tree-update` 流程；更新时必须保持完整文件级目录树，不得只写到目录层级。
10. 按 `ai_shared/rules/reporting.md` 中文简洁反馈。

## 5. 必须主动判断是否需要测试

执行器不能机械地“只改代码不测”。必须根据 `ai_shared/rules/testing.md` 判断是否需要新增、修改或运行测试。

简单原则：

1. 行为变化要测试。
2. bug 修复要回归测试。
3. public interface、schema、配置、CLI、协议变化要测试。
4. 主链路变化至少要 smoke 或 integration 验证。
5. 纯文档变化通常不需要代码测试，但要说明。

## 6. 用户主动触发项

以下操作不得自动执行，必须由用户明确要求或 prompt 明确指定：

- `project-tree-reset`
- `heavy-regression`
- `commit-message`
- `adr-upsert`
- `rule-update`
- `feedback-archive`
- 全量测试、长测、发布前完整验证

## 7. 不允许事项

- 不主动扩展架构设计。
- 不凭记忆推断 schema、配置、接口、文件结构。
- 不无关重构。
- 不恢复废弃文件。
- 不新增未经确认的兼容 shim。
- 不为了通过测试而降低断言或删除测试。
- 不自动执行 commit、push、reset、clean。
- 不默认运行重回归或长测。
- 不自动归档反馈，除非用户明确要求。

## 8. 固定反馈要求

每轮任务完成后，按 `ai_shared/rules/reporting.md` 反馈。反馈必须：

1. 中文。
2. 简洁。
3. 结构化。
4. 说明改了什么、测了什么、没测什么、风险是什么。
5. 不粘贴大段日志。

## 9. AI 配置体系维护原则

修改本 AI 配置体系时，必须保持：

1. 不新增无必要层级。
2. 不新增 agent。
3. 不重复维护 Claude 与 Codex 规则。
4. 新规则优先放入 `ai_shared/rules/`。
5. Claude Code 原生 skill 放入 `.claude/skills/`。
6. Codex skill 放入 `.agents/skills/`。
7. 删除旧规则时必须检查引用路径。
8. 保持中文、简洁、可执行。
