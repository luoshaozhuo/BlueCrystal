---
name: project-tree-reset
description: 首次建立、严重过期或大重构后，全量重建 project_tree.md；仅用户主动触发。
---

# project-tree-reset

## 功能

首次建立、严重过期或大重构后，全量重建 project_tree.md；仅用户主动触发。

## 通用要求

1. 使用中文输出。
2. 不默认读取所有文档。
3. 只读取完成本技能所需的文件。
4. 当前仓库文件是事实来源。
5. 反馈必须简洁。

## 特定要求

1. 必须生成完整文件级目录树，不得只保留目录层级；`src/whale/`、`tests/`、`tools/`、`ai_shared/` 等主要区域必须细到文件。

## 步骤

1. 扫描仓库有意义文件。
2. 排除 `.git`、虚拟环境、cache、build、dist、tmp、日志、生成产物。
3. 先删除 `ai_shared/memory/project_tree.md`。
4. 给目录树中每一个目录或文件添加功能或职责说明，用中文或中英文混合，长度在10到40个中文字符或英文词之间。
5. 检查目录树是否符合特定要求，不符合重复步骤4。
6. 输出完成的 `ai_shared/memory/project_tree.md` 文件内容。
