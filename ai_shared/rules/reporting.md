# Agent 中文反馈与归档规则

所有 agent 默认必须用中文反馈。

## 1. Agent result 格式

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

## 3. 禁止事项

1. 不粘贴大段日志。
2. 不把未执行命令写成通过。
3. 不把环境 pending 写成通过。
4. 不把 skipped、mock、fake 写成真实通过。
