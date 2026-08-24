# 规则读取路由

## 1. 所有会话必读

```text
ai_shared/rules/routing.md
```

## 2. 编码阶段

触发：用户在普通会话中要求修改代码。

必读：

```text
ai_shared/rules/coding.md
ai_shared/rules/python-docstring-cn.md
用户指定文件
当前相关源码、配置、schema
```

由当前主会话直接执行。默认不读 `testing.md`、`validation-routing.md`、`quality-gate.md`，不启动或委派其他 agent，不执行检查命令。

## 3. 测试阶段

触发：用户显式调用 `/test`（Codex 为 `$test` 或从 `/skills` 选择）。

必读：

```text
ai_shared/rules/testing.md
ai_shared/rules/quality-gate.md
ai_shared/rules/python-docstring-cn.md
staged diff 直接涉及的源码、配置、schema 和测试
```

由当前主会话直接执行。仅处理 staged 变更直接修改的代码。允许修改测试，原则上不修改生产代码。

## 4. 验证阶段

触发：用户显式调用 `/validate`（Codex 为 `$validate` 或从 `/skills` 选择）。

必读：

```text
ai_shared/rules/testing.md
ai_shared/rules/validation-routing.md
ai_shared/rules/quality-gate.md
ai_shared/rules/python-docstring-cn.md
staged diff 及其真实引用方、依赖方、装配路径和测试
```

由当前主会话直接执行。只读执行，不得修改源码、测试或文档。

## 5. 全量测试阶段

触发：用户显式调用 `/test-all`（Codex 为 `$test-all` 或从 `/skills` 选择）。

必读：

```text
ai_shared/rules/testing.md
ai_shared/rules/validation-routing.md
ai_shared/rules/quality-gate.md
ai_shared/rules/python-docstring-cn.md
仓库定义的全量工具链和测试入口
```

由当前主会话直接执行。对当前整个工作区执行常规全量测试。只读执行；只有用户同时指定 `include-heavy` 时才执行高成本项。

## 6. 规则、需求、报告和 project_tree

仅在用户明确要求时由当前主会话更新规则、需求、报告或 project_tree，不因编码、测试或验证阶段自动触发。

规则修改使用 `rule-update`；需求状态修改使用 `requirement-trace`；project_tree 仅在用户明确要求时使用对应 skill。

## 7. 执行主体

所有阶段和用户显式触发项均由当前主会话直接执行，不启动、委派或切换到独立 agent。

## 8. 上下文节省

默认不读取全部项目说明、全部 reports、完整 project_tree 或全仓源码。`project_tree.md` 只用于导航，不能替代真实文件。
