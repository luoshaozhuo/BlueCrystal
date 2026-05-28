# changed-files-gate

## 功能

获取本轮真实变更范围，供实现、验证、文档更新使用。

## 必须执行

```bash
git status --short
git diff --name-only
git diff --cached --name-only
```

## 输出

```text
unstaged files:
staged files:
new files:
deleted files:
renamed files:
python files:
test files:
docs files:
config/schema files:
```

## 使用要求

1. code-implementer 编码前必须执行一次。
2. code-implementer 编码后必须输出一次。
3. test-validator 验证前必须执行一次。
4. project-steward 更新文档前必须执行一次。
5. 不得只依赖上一个 agent 的口头说明。
