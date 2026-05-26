# 规则读取路由

本文件决定 coding agent 在不同任务下读取哪些规则。

本文件只决定读取哪些规则，不要求读取所有规则文件。除非任务明确需要，不读取项目说明、ADR 全文、reports、完整 project_tree。

## 1. 所有任务必读

```text
CLAUDE.md
ai_shared/rules/routing.md
```

## 2. 编码任务

涉及源码、脚本、配置、schema、测试修改时读取：

```text
ai_shared/rules/coding.md
ai_shared/rules/testing.md
ai_shared/rules/validation-routing.md
ai_shared/rules/reporting.md
```

## 3. 文档 / ADR / 规则修改

读取：

```text
ai_shared/rules/documentation.md
ai_shared/rules/reporting.md
```

## 4. Python

适用于 `.py`、Python 测试、Python 工具脚本。

遵循：

- 仓库 ruff / mypy / pytest 配置。
- PEP 8。
- public interface 的 Google-style docstring。
- 当前文件局部风格。

## 5. C / C++ / Native

适用于 `.c`、`.h`、`.cpp`、`.hpp`、native runner。

遵循：

- 仓库编译配置。
- 当前 native 代码风格。
- 明确资源所有权、返回码、错误处理。
- stdout/stderr 协议边界。
- native 与 Python adapter 的兼容契约。

## 6. TypeScript / JavaScript / HTML / CSS

适用于前端、Web App、UI、图表、配置页面。

遵循：

- 仓库 formatter / linter / tsconfig。
- 当前组件风格。
- 语义清晰、结构稳定、样式边界清楚。
- 修改行为时同步验证。

## 7. SQL / ORM / Migration / 数据模型

额外读取：

```text
ai_shared/memory/*项目说明*
```

并必须读取当前 ORM、migration、schema、repository、相关测试。不得凭记忆推断字段。

## 8. YAML / TOML / JSON / env / CLI 配置

必须检查：

- 当前配置解析代码。
- 默认值。
- 示例配置。
- 测试。
- CLI 使用说明。

## 9. 项目背景类任务

只有涉及项目目标、长期需求、非功能需求、安全合规、技术可替换性时，才读取：

```text
ai_shared/memory/*项目说明*
```

普通代码修改不读取项目说明全文。

## 10. 没有专门规则的语言

遵循：

1. 仓库工具配置。
2. 当前文件局部风格。
3. 该语言通用工程标准。
4. 最小充分修改。
5. 必要验证。
