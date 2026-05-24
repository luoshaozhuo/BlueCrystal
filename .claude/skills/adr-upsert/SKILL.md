---
name: adr-upsert
description: 优先查找并修正已有 ADR，必要时新建 ADR。
---

# adr-upsert

## 功能

优先查找并修正已有 ADR，必要时新建 ADR。

## 触发时机

当任务产生以下内容之一时，必须判断是否需要 ADR：

1. 长期架构边界。
2. use case / role / port / adapter 职责划分。
3. 协议接入、server/client 边界、生产能力等级。
4. 数据契约、消息契约、缓存契约、schema 原则。
5. 技术路线取舍，例如 Kafka、Redis、native runner、outbox。
6. 重要 rejected option，且以后可能反复讨论。
7. 代码阅读报告中形成了可长期复用的架构结论。

普通 bugfix、一次性任务日志、临时测试结果、未稳定的猜测不写 ADR。

## 通用要求

1. 使用中文输出。
2. 不默认读取所有文档。
3. 只读取完成本技能所需的文件。
4. 当前仓库文件是事实来源。
5. 反馈必须简洁。
6. 不把普通任务报告写成 ADR。
7. ADR 只记录长期有效的决策、边界、约束和被拒绝方案。
8. 如结论来自探查报告，必须区分“事实”“判断”“决策”，不得把未验证推测写成 Accepted。

## 步骤

1. 读取 `ai_shared/adr/ADR索引.md`。
2. 检索 `ai_shared/adr/` 下已有 ADR 文件名和标题。
3. 判断是否已有相关 ADR。
4. 有相关 ADR 时优先补充或修正。
5. 若新决策替代旧决策，将旧 ADR 标记为 `Superseded`，并在 `Superseded By` 中指向新 ADR。
6. 无相关 ADR 时新建。
7. 新建命名遵循 `ADR-YYYYMMDD-NNN-domain-topic-decision.md`。
8. 新建或修改后，更新 `ai_shared/adr/ADR索引.md`。
9. 在反馈中列出新增/修改的 ADR 文件、状态、核心决策和是否更新索引。

## ADR 内容要求

ADR 必须包含：

1. `Status`
2. `Keywords`
3. `Context`
4. `Decision`
5. `Consequences`
6. `Rejected Options`
7. `Related Files`
8. `Supersedes / Superseded By`

## 状态规则

- `Draft`：决策仍需用户确认。
- `Accepted`：用户已明确要求记录，或该决策已成为后续开发约束。
- `Superseded`：已被新 ADR 替代。

## 质量要求

1. 文件名必须便于检索。
2. 标题必须体现 domain、topic、decision。
3. Context 只写必要背景，不写完整任务日志。
4. Decision 写清楚“以后必须怎么做”。
5. Consequences 同时写收益、代价和约束。
6. Rejected Options 必须说明为什么不用。
7. Related Files 写路径，不凭记忆虚构不存在文件。
