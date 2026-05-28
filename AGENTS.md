# OpenAI Codex 入口

本仓库 OpenAI Codex 与 Claude Code 共用根目录 `CLAUDE.md` 作为主入口规则。

Codex 执行任务前必须读取：

```text
CLAUDE.md
ai_shared/rules/routing.md
```

然后按 `CLAUDE.md` 和 `routing.md` 执行，不要默认读取全部 docs / ADR / reports / project_tree。

当 `CLAUDE.md` 要求使用 Claude Code agent：

```text
@agent-code-implementer
@agent-test-validator
@agent-project-steward
```

Codex 应使用项目 custom agent 执行等价委派：

```text
spawn code-implementer
spawn test-validator
spawn project-steward
```

除此之外，不在本文件复制或改写规则。
