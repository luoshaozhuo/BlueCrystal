# Codex / Agent 执行入口

本文件是 Codex 自动读取入口。具体执行规则以 `CLAUDE.md` 和 `ai_shared/rules/` 为准。

## 1. 必读

```text
CLAUDE.md
ai_shared/rules/routing.md
```

## 2. 执行原则

1. 默认中文反馈。
2. 不复制维护第二套规则。
3. 不默认读取全仓文档；按 handoff 和 routing 读取必要文件。
4. `ai_shared/memory/project_tree.md` 只用于导航，不能替代读取真实源码、测试、配置和 schema。
5. 编码任务必须使用固定三段式流程：
   ```text
   @agent-code-implementer -> @agent-test-validator -> @agent-project-steward -> 主会话收口
   ```
6. 任何验证结论必须来自真实命令、真实文件、真实测试或明确 evidence。
7. 不把 skipped、mock、fake、health check、脚本存在、单文件 passed、environment-pending 写成真实通过。
8. 不把工具/实验模块引入生产路径。
9. 不自动执行 commit、push、reset、clean；其他会修改 Git 历史、工作区状态或远端仓库状态的命令也默认禁止自动执行。
10. 不默认运行重回归或长测。
11. `project-tree-update` 和 `project-tree-reset` 仅在用户明确要求时手动执行；handoff 必须转述该用户请求，不得例行检查或自动触发。
