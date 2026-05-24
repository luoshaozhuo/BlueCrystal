# Codex 入口

Codex 会自动读取 `AGENTS.md`。本仓库的详细执行规则不在本文件展开，避免重复维护。

Codex 必须将 `CLAUDE.md` 视为本仓库主执行规则。不要只读取 `AGENTS.md` 后直接执行任务。

请先读取并遵守：

```text
CLAUDE.md
```

然后按照 `CLAUDE.md` 指示继续读取：

```text
ai_shared/rules/routing.md
```

要求：

1. 默认用中文回答和反馈。
2. 不维护 Codex 专属规则副本。
3. 不默认读取全部文档。
4. 当前源码、测试、配置、schema 是事实来源。
5. 如本文件与 `CLAUDE.md` 冲突，以 `CLAUDE.md` 为准。
