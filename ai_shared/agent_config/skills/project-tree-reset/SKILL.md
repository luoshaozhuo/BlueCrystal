---
name: project-tree-reset
description: Use when the user explicitly requests a full rebuild of ai_shared/memory/project_tree.md from the real repository contents instead of an incremental update.
---

# project-tree-reset

## 1. 目的

用户主动触发时，全量重建 `ai_shared/memory/project_tree.md`。

## 2. 触发条件

必须用户明确要求，或 handoff 明确指定。

禁止使用：
- 普通新增、删除、移动、重命名文件；这些使用 project-tree-update。
- 仅为了格式化 project_tree。

## 3. 操作步骤

1. 扫描仓库真实文件。
2. 排除 `.git`、虚拟环境、cache、build、dist、tmp、日志、生成产物、第三方库。
3. 读取必要文件头、README、入口代码，确认职责。
4. 重建完整文件级目录树。
5. 输出与旧树主要差异。

## 4. 输出格式

```text
skill result:
- skill: project-tree-reset
- files scanned:
- files omitted:
- project_tree changed:
- major differences:
- risk:
```
