# code-quality-gate

## 1. 目的

根据真实变更范围确认编码、注释/文档注释、类型、测试和验证门禁。

## 2. 触发条件

必须使用：
- code-implementer 修改前，用于制定质量计划。
- test-validator 验证前，用于独立选择验证命令。

禁止使用：
- 替代真实 lint、type-check 或测试命令。
- 只输出“已检查”但不列判断结果。

## 3. 输入

```text
changed-files-gate 结果
handoff 任务
routing 指定规则
相关源码、测试、配置、schema
```

## 4. 必读规则

```text
ai_shared/rules/coding.md
ai_shared/rules/testing.md
ai_shared/rules/validation-routing.md
ai_shared/rules/quality-gate.md
ai_shared/rules/python-docstring-cn.md
```

## 5. 必须判断

1. 是否需要补充或修正文档注释。
2. 是否需要补充普通注释说明原因、边界、假设或风险。
3. 是否需要类型、schema、签名或契约修正。
4. 是否需要新增或修改测试。
5. 应执行哪些语法/编译、lint、type-check、pytest 或其他语言验证命令。
6. 是否涉及生产路径与工具/实验路径隔离。
7. 是否涉及安全、审计、权限、lease、fencing、事务、重试、回滚、子进程、socket 或外部系统调用。
8. 是否需要 project-tree-update / requirement-trace / rule-update，由 project-steward 后续处理。

## 6. 输出格式

```text
skill result:
- skill: code-quality-gate
- changed files:
- comment/doc gate:
- type/schema gate:
- test gate:
- validation commands:
- docs/tree/requirement impact:
- risk:
- pending:
```
