# Agent 中文反馈与报告归档规则

所有 agent 和主会话默认必须使用中文反馈。除非用户明确要求英文，否则不得以英文作为主要输出语言。

## 1. Agent result 格式

所有 subagent 必须使用以下格式，不得自造格式：

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

## 2. 主会话最终反馈格式

```text
修改文件：
- ...

行为变化：
- ...

Agent 使用：
- code-implementer:
- test-validator:
- project-steward:

检查与测试：
- 已执行：
- failed：
- skipped：
- pending：
- 未执行及原因：

project_tree：
- 已更新 / 无需更新 / 未更新原因：

ADR：
- 已更新 / 无需更新 / 建议更新：

报告：
- ...

是否收口：
- 是/否：
- 理由：

剩余风险：
- ...

下一步：
- ...
```

## 3. 报告输出位置

1. 所有任务报告必须输出到：

```text
ai_shared/reports/
```

2. 不得把任务报告写入长期规则、ADR、需求文档或 project_tree。
3. 如果只是主会话简短反馈，不需要创建报告文件；只有 handoff 指定 `report target` 或用户要求归档时才写报告。
4. 报告文件必须使用 `.md`。

## 4. 报告命名规则

报告文件名使用小写英文、数字和下划线，格式推荐：

```text
<scope>_<topic>_<round_or_date>.md
```

示例：

```text
ingest_scheduler_fix_round2.md
source_lab_native_readiness_round4.md
rules_agents_skills_update_20260528.md
```

禁止：

```text
report.md
final.md
new.md
临时报告.md
未命名.md
```

## 5. 报告正文格式

报告必须包含以下结构。可按任务裁剪，但不得缺少“状态、证据、风险、测试/检查”四类信息。

```markdown
# <标题>

> 日期:
> 范围:
> 状态:
> 证据来源:

## 1. 总览

| 项 | 结果 |
|---|---|

## 2. 修改文件

| 文件 | 操作 | 说明 |
|---|---|---|

## 3. 行为变化

- ...

## 4. 检查与测试

| 命令/检查 | 结果 | 分类 | 说明 |
|---|---|---|---|

## 5. 证据与需求状态

| 条目 | 证据等级 | 状态 | 说明 |
|---|---|---|---|

## 6. project_tree / ADR / 规则

- project_tree:
- ADR:
- rules:

## 7. 剩余风险

- ...

## 8. 下一步建议

- ...
```

## 6. 证据等级写法

报告必须明确证据等级：

```text
L1 unit/mock
L2 contract/stub
L3 simulator
L4 integration
L5 e2e/field
```

如果没有测试证据，写：

```text
未验证
environment-pending
insufficient-evidence
```

不得把低等级证据写成真实生产验证完成。

## 7. 命令结果写法

命令结果必须写真实状态：

```text
passed
failed
skipped
pending
not-run
environment-failed
flaky
```

如果命令未执行，必须写：

```text
not-run：<原因>
```

不得写成 passed。

## 8. 禁止事项

1. 不粘贴大段日志。
2. 不把未执行命令写成通过。
3. 不把环境 pending 写成通过。
4. 不把 skipped、mock、fake 写成真实通过。
5. 不把低等级测试证据写成高等级真实闭环。
6. 不在报告中重复粘贴完整规则、完整 diff 或完整测试日志。
7. 不创建与本规则冲突的第二套报告格式。
