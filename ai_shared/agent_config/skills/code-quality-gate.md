# code-quality-gate

## 功能

根据真实变更范围确认编码、注释、类型、测试和验证门禁。

## 必须读取

```text
ai_shared/rules/coding.md
ai_shared/rules/testing.md
ai_shared/rules/validation-routing.md
ai_shared/rules/quality-gate.md
ai_shared/rules/python-docstring-cn.md
```

## 必须判断

1. 是否需要中文注释。
2. 是否需要 Google-style docstring。
3. 是否需要类型标注修正。
4. 是否需要新增或修改测试。
5. 是否需要 py_compile / ruff / mypy / pytest。
6. 是否涉及 source_lab 生产路径隔离。
