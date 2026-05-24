# 文档、目录树、ADR 与规则维护

## 1. 文档维护原则

1. 长期文档只记录稳定事实、规则、决策、背景。
2. 不把普通任务日志写进长期文档。
3. 不做无关大改。
4. 新规则必须可执行、可审查、可复用。
5. 旧文档与新规则冲突时，优先修正旧文档。

## 2. project_tree.md

`ai_shared/memory/project_tree.md` 维护完整文件级目录树，每个 item 带简短职责注释。

使用规则：

- 开发前需要定位文件时，执行 project-tree-read。
- 文件新增、删除、移动、重命名或职责变化后，执行 project-tree-update。
- 严重过期、大重构、首次建立时，用户主动触发 project-tree-reset。
- project_tree 只用于导航，不替代读取当前源码。

职责注释要求：

- 每个 item 的职责注释不超过 40 个中文字符或 40 个英文词。
- 最多一句话。
- 不写历史。
- 不写冗长实现细节；必要时可说明职责边界。
- 不确定职责时标注“待确认”。

## 3. ADR

ADR 全称 Architecture Decision Record。

使用规则：

- ADR 记录长期架构、技术路线、接口边界、schema 原则、协议契约等决策。
- 不记录普通任务日志。
- 使用 adr-upsert 时必须先查找已有 ADR。
- 优先修正已有 ADR，避免重复新建。
- 新建 ADR 文件名必须便于检索。

命名建议：

```text
ADR-YYYYMMDD-NNN-domain-topic-decision.md
```

## 4. 规则更新

使用 rule-update 时必须：

1. 明确用户要求更新哪类规则。
2. 读取相关规则文件。
3. 最小修改。
4. 避免重复。
5. 保持中文、清晰、可执行。

## 5. project-tree-reset / update 质量要求

1. `project-tree-reset` 必须生成完整文件级目录树，不得只写目录层级。
2. `project-tree-update` 不得把已有文件级条目折叠回目录层级。
3. `src/whale/`、`tests/`、`tools/`、`ai_shared/` 等主要区域必须细到文件。
4. 注释可以略长，但不得超过 40 个中文字符或 40 个英文词。
