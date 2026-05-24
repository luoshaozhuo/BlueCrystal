---
name: project-tree-read
description: 开发前读取 project_tree.md，定位候选目录和文件；只导航，不替代源码读取。
---

# project-tree-read

## 功能

开发前读取 project_tree.md，定位候选目录和文件；只导航，不替代源码读取。

## 通用要求

1. 使用中文输出。
2. 不默认读取所有文档。
3. 只读取完成本技能所需的文件。
4. 当前仓库文件是事实来源。
5. 反馈必须简洁。

## 步骤

1. 读取 `ai_shared/memory/project_tree.md`。
2. 根据任务目标定位候选目录、候选源码文件、候选测试文件。
3. 输出需要进一步读取确认的文件。
4. 明确说明 project_tree 只用于导航。
