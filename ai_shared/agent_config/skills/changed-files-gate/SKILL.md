# changed-files-gate

## 1. 目的

获取本轮真实变更范围，供实现、验证、文档更新使用。

## 2. 触发条件

必须使用：
- code-implementer 编码前和编码后。
- test-validator 验证前。
- project-steward 更新文档、需求、ADR、规则或 project_tree 前。

禁止使用：
- 用上一个 agent 的口头说明替代真实 Git 状态。

## 3. 操作步骤

执行：

```bash
git status --short
git diff --name-only
git diff --cached --name-only
```

必要时补充：

```bash
git diff --name-status
git diff --cached --name-status
git ls-files --others --exclude-standard
```

## 4. 输出格式

```text
skill result:
- skill: changed-files-gate
- unstaged files:
- staged files:
- untracked files:
- deleted files:
- renamed files:
- source files:
- test files:
- docs files:
- config/schema files:
- risk:
```

## 5. 判定规则

1. 出现 untracked 文件时必须列出。
2. 出现删除、移动、重命名或职责变化时，project-steward 必须判断 project-tree-update。
3. 如果工作区存在与本轮无关的既有变更，必须标注，避免误改。
