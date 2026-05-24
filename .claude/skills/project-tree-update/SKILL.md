---
name: project-tree-update
description: 文件新增、删除、移动、重命名或职责变化后，增量更新 project_tree.md。
---

# project-tree-update

## 功能

文件新增、删除、移动、重命名或职责变化后，增量更新 project_tree.md。

## 通用要求

1. 使用中文输出。
2. 不默认读取所有文档。
3. 只读取完成本技能所需的文件。
4. 当前仓库文件是事实来源。
5. 反馈必须简洁。

## 步骤

0. 必须保持完整文件级目录树，不得把已有文件级条目折叠回目录层级。
1. 执行 `git status` 或 `git diff --name-only` 获取本轮全部新增、删除、移动、重命名或职责变化的文件清单。
2. 对清单中每个文件，逐一检查 `ai_shared/memory/project_tree.md` 对应区域是否已有该条目。
   - 必须检查所有目录下的文件，不仅限于 `src/`、`tests/`、`tools/`。
   - 必须检查 `ai_shared/adr/`、`ai_shared/reports/`、`ai_shared/memory/`、`docs/`、`scripts/`、`.claude/` 等全部非 `.gitignore` 区域。
3. 读取 `ai_shared/memory/project_tree.md`。
4. 对每个缺失条目，定位到 project_tree 中对应目录片段，增量添加。
5. 每个新增 item 添加不超过 40 个中文字符或 40 个英文词的职责注释。
6. 只更新受影响片段，不修改无关内容。
7. 中文反馈更新内容，列出新增的条目路径。
