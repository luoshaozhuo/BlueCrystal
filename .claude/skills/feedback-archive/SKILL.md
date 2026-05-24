---
name: feedback-archive
description: 在用户明确要求时，将 agent 简洁反馈归档到 ai_shared/reports。
---

# feedback-archive

## 功能

在用户明确要求时，将 agent 简洁反馈归档到 ai_shared/reports。

## 通用要求

1. 使用中文输出。
2. 不默认读取所有文档。
3. 只读取完成本技能所需的文件。
4. 当前仓库文件是事实来源。
5. 反馈必须简洁。

## 步骤

1. 确认用户明确要求归档反馈。
2. 读取 `ai_shared/rules/reporting.md`。
3. 将本轮反馈压缩成归档格式。
4. 保存到 `ai_shared/reports/YYYYMMDD-HHMM-short-topic.md`。
5. 不归档大段日志或完整 diff。
