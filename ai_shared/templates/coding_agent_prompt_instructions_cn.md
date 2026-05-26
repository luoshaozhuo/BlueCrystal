# Coding Agent Prompt 使用说明

## 1. 文件用途

本说明与 `coding_agent_prompt_template_cn.txt` 配套使用。

二者分工：

```text
coding_agent_prompt_template_cn.txt
  只放任务模板骨架，供每一轮 prompt 复制、替换、填写。

coding_agent_prompt_instructions_cn.md
  说明模板中的固定规则、文档治理方式、ADR / project_tree / report 的更新条件。
```

使用时建议：

```text
1. 先把 template 复制为本轮 prompt。
2. 替换所有 {...} 占位符。
3. 保留 template 的章节顺序。
4. 不要把本说明全文塞进每一轮 prompt；只保留 template 中必要引用。
5. 如果 coding agent 没有长期记忆，可在项目级 CLAUDE.md / AGENTS.md 中引用本说明。
```

---

## 2. 目录预设

本模板适用于统一配置过的 coding agent 项目。默认存在：

```text
ai_shared/
├── adr/
│   ├── ADR索引.md
│   └── ADR-YYYYMMDD-NNN-domain-topic-decision.md
├── memory/
│   └── project_tree.md
└── reports/
    └── *.md
```

含义：

```text
ai_shared/adr/
  保存长期有效的架构决策记录。

ai_shared/memory/project_tree.md
  保存项目文件级目录树与简短职责说明，帮助 coding agent 快速导航。

ai_shared/reports/
  保存每轮任务执行报告，记录事实、测试、剩余风险和下一步建议。
```

如果某个项目目录不同，应优先遵守该项目已有的 CLAUDE.md / AGENTS.md / skill / rules，不要自行创造重复目录。

---

## 3. ADR 是什么

ADR 是 Architecture Decision Record，即“架构决策记录”。

ADR 只记录长期有效的内容：

```text
1. 架构边界。
2. 依赖方向。
3. 分层职责。
4. 长期接口契约。
5. 端口 / adapter / facade / factory / registry 等机制。
6. 数据 schema、字段语义、消息格式、缓存 key、事件格式。
7. 协议约定、stdout/stderr 协议、跨语言进程通信协议。
8. CI / gate / release 阻断规则。
9. 废弃旧路径、旧模块、旧机制的不可逆决策。
```

ADR 不应记录：

```text
1. 普通任务流水账。
2. 临时 bugfix。
3. 测试输出全文。
4. 每个函数的实现细节。
5. 纯代码风格调整。
6. 与后续任务无长期影响的局部修改。
```

---

## 4. 什么时候必须更新 ADR

满足任一条件时必须更新或新建 ADR：

```text
1. 改变模块边界、依赖方向、分层职责。
2. 新增或改变长期接口契约、端口、DTO、协议格式。
3. 改变 capability / unsupported / NOT_IMPLEMENTED 的长期规则。
4. 新增通用 facade / factory / registry / adapter 机制。
5. 改变数据 schema、字段语义、消息格式、缓存 key、事件格式。
6. 改变 CI / gate / release 阻断规则。
7. 废弃旧路径、旧模块、旧机制，或引入不可逆迁移。
8. 本轮结论会影响后续多个开发任务。
```

---

## 5. 什么时候不应更新 ADR

以下情况通常不需要 ADR：

```text
1. 纯 bugfix，且不改变长期设计。
2. 只新增测试，不改变边界或契约。
3. 只调整注释、日志、错误文案。
4. 只更新任务报告。
5. 局部实现细节变化，对外契约不变。
```

如果不确定，优先检查已有 ADR。不要为了显得“完整”而新建重复 ADR。

---

## 6. ADR 更新方式

优先使用项目已有 skill，例如：

```text
adr-upsert
```

通用流程：

```text
1. 读取 ai_shared/adr/ADR索引.md。
2. 检索已有 ADR。
3. 有相关 ADR 时优先补充或修正。
4. 无相关 ADR 时才新建。
5. 新建命名遵循：
   ADR-YYYYMMDD-NNN-domain-topic-decision.md
6. 被替代的 ADR 标记 Superseded，并指向新 ADR。
7. ADR 索引必须同步更新。
8. 多个 ADR 职责必须互斥，不要重复记录同一决策。
```

ADR 推荐结构：

```text
# ADR-YYYYMMDD-NNN-domain-topic-decision

## Status

Draft / Accepted / Superseded

## Keywords

- ...

## Context

说明为什么需要这个决策。

## Decision

说明最终决策。

## Consequences

说明收益、代价、约束和影响。

## Rejected Options

说明被拒绝方案及原因。

## Related Files

列出相关文件。

## Supersedes / Superseded By

如适用，说明替代关系。
```

---

## 7. project_tree 是什么

`project_tree.md` 是项目文件级目录树与简短职责说明。

它的作用：

```text
1. 帮助 coding agent 快速定位文件。
2. 帮助人类审查目录结构变化。
3. 记录文件职责，而不是记录任务过程。
```

它不是：

```text
1. 源码替代品。
2. API 文档。
3. 函数列表。
4. 任务日志。
5. 测试报告。
```

---

## 8. 什么时候必须更新 project_tree

满足任一条件时必须更新：

```text
1. 新增文件。
2. 删除文件。
3. 移动或重命名文件。
4. 新增目录或删除目录。
5. 文件职责发生明显变化。
```

---

## 9. 什么时候不需要更新 project_tree

以下情况通常不需要：

```text
1. 只修改文件内部实现，文件职责不变。
2. 只改测试断言，文件职责不变。
3. 只改注释、日志、错误文案。
4. 只更新报告或 ADR 内容。
```

---

## 10. project_tree 更新方式

要求：

```text
1. 保持文件级目录树。
2. 每个 item 附简短职责说明。
3. 职责说明不超过项目约定长度；如无约定，控制在 40 个中文字符或 40 个英文词以内。
4. 不要把每个函数都写进 project_tree。
5. 忽略第三方库、构建产物、缓存、.gitignore 中排除的内容。
6. 不要把任务日志写进 project_tree。
7. 如删除文件，应从目录树中移除，而不是标注“已删除”。
```

---

## 11. report 是什么

report 是每轮任务的事实记录。

默认位置：

```text
ai_shared/reports/
```

report 用于记录：

```text
1. 本轮改了什么。
2. 为什么改。
3. 测了什么。
4. 哪些通过。
5. 哪些跳过。
6. 哪些风险剩余。
7. 下一轮建议。
```

report 不等于 ADR。报告可以记录细节、过程、测试输出摘要；ADR 只记录长期决策。

---

## 12. 每轮报告必须包含什么

建议报告包含：

```text
A. 修改文件清单
B. 本轮目标完成情况
C. 核心能力实现说明
D. E2E / smoke / gate 矩阵
E. 关键指标验证
F. unsupported / NOT_IMPLEMENTED / limitation / capability 更新
G. 架构边界检查
H. 构建与 CI 命令
I. 回归测试结果
J. ADR / project_tree 更新
K. 剩余风险
L. 下一轮建议
```

报告命名建议：

```text
ai_shared/reports/{project_or_stage}_round{round_no}_{short_topic}_report.md
```

示例：

```text
ai_shared/reports/source_lab_round5_2_iec101_modbus_rtu_capacity_profile_e2e_report.md
ai_shared/reports/cache_round2_kafka_publish_outbox_report.md
```

---

## 13. prompt 填写原则

每一轮 prompt 应该做到：

```text
1. 一轮内多做相关任务，不要拆太碎。
2. 每轮有明确边界，防止 coding agent 扩散。
3. 每轮有明确“允许修改”和“禁止事项”。
4. 每轮要求测试命令。
5. 每轮要求报告。
6. 每轮要求说明 ADR / project_tree 是否更新。
7. 每轮要求 failed/skipped 明细。
8. 每轮要求剩余风险和下一步建议。
```

---

## 14. 常用占位符说明

```text
{ROUND_NO}
  当前轮次，例如 1。

{TOTAL_ROUNDS}
  当前阶段总轮次，例如 5。

{TASK_TITLE}
  本轮任务标题，建议简短但具体。

{PROJECT_OR_STAGE_NAME}
  项目名或阶段名。

{BASELINE_*}
  当前已完成事实。

{GOAL_*}
  本轮可验收目标。

{BOUNDARY_*}
  不允许破坏的边界。

{WORK_ITEM_*}
  本轮具体工作项。

{MATRIX_ITEM_*}
  需要进入能力矩阵、E2E 矩阵或门禁矩阵的项目。

{REPORT_FILE_NAME}
  本轮报告文件名，不含路径或含路径均可，但模板建议写完整路径。

{ADR_FILE_TO_UPDATE}
  本轮预计更新的 ADR；如无需更新，在最终报告说明原因。
```

---

## 15. 对 coding agent 的强制约束建议

可以在项目级 CLAUDE.md / AGENTS.md 中加入：

```text
1. 每轮任务必须先读取 prompt 指定文件。
2. 当前源码和测试是事实来源，旧报告只作背景。
3. 禁止 fake OK。
4. 禁止把 skip 写成 PASS。
5. 禁止把环境缺失伪装成功能完成。
6. 修改文件结构时必须更新 project_tree。
7. 影响长期架构或契约时必须使用 adr-upsert 更新 ADR。
8. 每轮必须输出 ai_shared/reports/ 下的报告。
```
