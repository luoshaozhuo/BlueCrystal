# 质量门禁规则

## 1. changed-files-gate

每个 agent 开始工作前必须使用 `changed-files-gate`，获取真实变更范围。

## 2. Python 门禁

修改 Python 文件时，必须优先执行或说明未执行原因：

```bash
python -m py_compile <changed-python-files>
ruff check <changed-python-files-or-related-package>
mypy <affected-package-or-files>
pytest <affected-tests> -q
```

## 3. 文档门禁

新增、删除、移动、重命名文件，或文件职责变化时，必须触发 `project-tree-update` 判断。

## 4. 禁止事项

1. 不允许无说明 `type: ignore`。
2. 不允许裸 `except`。
3. 不允许静默吞异常。
4. 不允许把未执行的工具写成通过。
