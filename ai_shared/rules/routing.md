# 规则读取路由

## 1. 所有 agent 必读

```text
ai_shared/rules/routing.md
```

## 2. code-implementer

必须读取：

```text
ai_shared/rules/coding.md
ai_shared/rules/testing.md
ai_shared/rules/validation-routing.md
ai_shared/rules/quality-gate.md
ai_shared/rules/python-docstring-cn.md
```

必要时读取：

```text
ai_shared/rules/documentation.md
```

## 3. test-validator

必须读取：

```text
ai_shared/rules/testing.md
ai_shared/rules/validation-routing.md
ai_shared/rules/quality-gate.md
ai_shared/rules/python-docstring-cn.md
```

## 4. project-steward

必须读取：

```text
ai_shared/rules/documentation.md
ai_shared/rules/reporting.md
```

如涉及需求状态，必须结合 `requirement-trace` skill。

如涉及 ADR，必须结合 `adr-upsert` skill。

如涉及 project_tree，必须结合 `project-tree-update` skill。

## 5. 上下文节省

默认不读取全部项目说明、全部 ADR、全部 reports、完整 project_tree 或全仓源码。

`project_tree.md` 只用于导航，不能替代二次读取真实源码、测试、配置和 schema。
