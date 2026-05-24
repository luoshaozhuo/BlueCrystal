# Claude Code Project Memory

## 固定记忆

1. 默认用中文回答和反馈。
2. 不默认读取所有项目文档。
3. 主入口规则为根目录 `CLAUDE.md`。
4. 公共规则位于 `ai_shared/rules/`。
5. 项目目录树位于 `ai_shared/memory/project_tree.md`。
6. 复杂方案通常由用户在 ChatGPT / Gemini / DeepSeek 中讨论后，以执行 prompt 交给 Claude Code。
7. 当前源码、测试、配置、schema 是事实来源。
