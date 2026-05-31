# 文档、目录树、ADR 与规则维护

## 1. 基本原则

1. 长期文档只记录稳定事实、规则、决策、背景。
2. 不把普通任务日志写进长期文档；任务过程和验证结果进入 `ai_shared/reports/`。
3. 不把未验证项写成通过。
4. 不重复维护两套规则。
5. 规则文档必须保持单一来源和通用表达；语言差异应作为通用规则下的分节，不另建语义冲突的语言专用规则。
6. 文档、需求和报告不得把 mock、fake、stub、health check、脚本存在、单文件 passed、environment-pending 写成真实闭环。

## 2. project_tree

1. `project_tree.md` 必须保持完整文件级目录树。
2. 新增、删除、移动、重命名文件，或文件职责变化时必须更新。
3. 每个 item 职责说明应简短，通常不超过 40 个中文字符或 40 个英文词。
4. 不得只写到目录层级。
5. `project_tree.md` 只用于导航，不能替代读取真实源码、测试、配置和 schema。
6. 读取 project_tree 是普通规则，不再单独设置 skill；更新 project_tree 才使用 `project-tree-update`。

## 3. ADR

影响长期架构、接口契约、schema、部署策略、运行时能力声明、证据等级规则或 rejected option 时，必须判断是否需要 ADR。

## 4. 需求跟踪

1. 需求状态变化时必须使用 `requirement-trace`。
2. 不得把 skipped、mock、fake、health check、TCP connect、脚本存在、环境 pending 写成真实通过。
3. 如果发现状态高估，必须降级或标注 pending。
4. 证据等级必须和测试实际类型一致。

## 5. 报告归档

1. 报告归档是 project-steward 的常规职责，不单独设置 `report-archive` skill。
2. 报告必须遵守 `reporting.md` 的语言、位置、命名、格式和证据规则。
