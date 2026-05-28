# 文档、目录树、ADR 与规则维护

## 1. 基本原则

1. 长期文档只记录稳定事实、规则、决策、背景。
2. 不把普通任务日志写进长期文档。
3. 不把未验证项写成通过。
4. 不重复维护两套规则。

## 2. project_tree

1. `project_tree.md` 必须保持完整文件级目录树。
2. 新增、删除、移动、重命名文件，或文件职责变化时必须更新。
3. 每个 item 职责说明应简短，通常不超过 40 个中文字符或 40 个英文词。
4. 不得只写到目录层级。

## 3. ADR

影响长期架构、接口契约、schema、部署策略或 rejected option 时，必须判断是否需要 ADR。

## 4. 需求跟踪

需求状态变化时必须使用 `requirement-trace`。不得把 skipped、mock、fake、health check、TCP connect、脚本存在、环境 pending 写成真实通过。
