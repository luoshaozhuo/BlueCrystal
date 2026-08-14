# Agent 反馈与报告归档规则

## 1. 规则定位

本规则定义 agent 反馈、主会话反馈和报告归档格式。测试分类、生命周期阶段和 NOT_RUN 原因以测试规则为准；本规则只规定反馈必须呈现哪些信息。

默认使用项目主要语言反馈；用户明确指定其他语言时除外。

## 2. Agent result 格式

### 2.1 full 12 字段（task_tier=full 必填）

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

字段要求：

1. `passed` 记录已执行且通过的检查或测试。
2. `failed` 记录已执行且失败的检查或测试。
3. `skipped` 记录被主动跳过且已说明原因的检查或测试。
4. `pending` 记录等待环境、条件或后续输入后才能执行的项。
5. `evidence` 记录每条结论对应的真实证据（命令、文件路径、字段名、行号或状态值）。
6. `risk` 记录本轮残留风险、未覆盖范围、潜在回退点或升级触发条件。
7. `next handoff suggestion` 可按任务需要使用简短标签，例如 coding、test、validation、fix、cleanup、documentation、requirement、architecture、security、performance、deployment、operation、regression。标签不是封闭枚举；重点是说明后续动作、触发条件和风险。
8. 不使用未定状态字段。
9. 测试框架 skip 不单独作为结果字段；未执行时归入 `pending` 或在 `skipped` 中说明。

### 2.2 standard 4 字段（task_tier=standard 必填）

```text
Agent result:
- files changed: <列表>
- passed: <受影响的 syntax + lint + unit 简表>
- failed: <0 / 列表>
- not-run: <未跑项 + 原因码>
```

字段要求：

1. `files changed` 给出本轮实际修改/新增/删除的文件清单。
2. `passed` 用一行或简短列表列出受影响的语法、lint 与 unit 检查结果。
3. `failed` 默认 `0`；存在失败时列出命令与失败项。
4. `not-run` 列出本轮未跑项与原因码（按需，例如 `NOT_RUN: heavy-regression`, `NOT_RUN: 跨模块联调`）。
5. 不要求 12 字段完整版；只在该任务由 standard 自动升级到 full 时，按 §2.1 输出。

## 3. 主会话反馈

### 3.0 light 反馈（task_tier=light）

```text
已完成：<一句话说明本轮做了什么>
```

说明：light 任务由主会话直接处理，不启动任何 subagent；不写报告文件，不引用 Agent result。

### 3.1 full 反馈（task_tier=full）

未生成报告文件时，主会话反馈使用以下结构：

```text
修改文件:
- ...

行为变化:
- ...

Agent 使用:
- code-implementer:
- test-validator:
- project-steward:

验证范围:
- 阶段:
- 来源:
- 命令:

检查与测试:
- passed:
- failed:
- skipped:
- pending:

project_tree:
- 已按明确指令更新 / 未手动请求（未检查）:

报告:
- 无 / 路径:

是否收口:
- 是/否:
- 理由:

剩余风险:
- ...

下一步:
- ...
```

已生成报告文件时，主会话只需给出：

```text
报告:
- <报告路径>

是否收口:
- 是/否:

关键结果:
- passed:
- failed:
- not-run:

下一步:
- ...
```

窗口反馈不得与报告结论不一致，不应重复报告全文。

### 3.2 standard 反馈（task_tier=standard）

```text
修改文件: <列表>
检查与测试:
- passed:
- failed:
- not-run:
是否收口: 是/否
剩余风险: <一行>
下一步: <一行>
```

说明：standard 任务默认不启动 test-validator / project-steward，不写报告文件；若主会话或 code-implementer 触发自动升级到 full，则按 §3.1 输出。

## 4. 报告输出位置

任务报告默认输出到：

```text
ai_shared/reports/
```

如果项目另有报告目录，以任务 handoff 或仓库规则为准。报告必须使用 `.md`，不得把任务报告写入长期规则、需求文档或目录树。

## 5. 报告命名

报告文件名使用小写英文、数字、下划线，推荐格式：

```text
<scope>_<topic>_<round_or_date>.md
```

避免使用：

```text
report.md
final.md
new.md
临时报告.md
未命名.md
```

## 6. 报告正文结构

报告应包含以下信息，可按任务裁剪：

```markdown
# <标题>

> 日期:
> 范围:
> 状态:
> 验证范围:

## 1. 总览

| 项 | 结果 |
|---|---|

## 2. 修改文件

| 文件 | 操作 | 说明 |
|---|---|---|

## 3. 行为变化

- ...

## 4. 检查与测试

| 命令/检查 | 结果 | 未执行原因 | 说明 |
|---|---|---|---|

## 5. 验证覆盖

| 对象 | 阶段 | 来源 | 结果 | 说明 |
|---|---|---|---|---|

## 6. project_tree / 规则

- project_tree: 已按明确指令更新 / 未手动请求（未检查）
- rules:

## 7. 剩余风险

- ...

## 8. 下一步建议

- ...
```

## 7. 命令结果写法

命令和检查结果使用真实状态：

```text
PASS
FAIL
NOT_RUN: <原因>: <详情>
```

未执行命令必须写 `NOT_RUN`，不得写成 PASS。

## 8. 禁止事项

1. 不粘贴大段日志。
2. 不把未执行命令写成通过。
3. 不把 mock、fake、stub、health check、脚本存在、单文件通过写成真实闭环。
4. 不重复粘贴完整规则、完整 diff 或完整测试日志。
5. 不创建与本规则冲突的第二套报告格式。
