# report-archive

## 功能

根据本轮已验证事实生成 `ai_shared/reports/` 下的简短任务报告。

## 必须读取

```text
ai_shared/rules/reporting.md
```

## 必须依据

```text
code-implementer Agent result
test-validator Agent result
project-steward handoff 中的 report target
真实变更文件
真实验证命令和结果
```

## 禁止事项

1. 不粘贴完整日志。
2. 不把 skipped、mock、fake、health check、TCP connect、脚本存在、环境 pending 写成真实通过。
3. 不创建与 `reporting.md` 冲突的第二套报告格式。
