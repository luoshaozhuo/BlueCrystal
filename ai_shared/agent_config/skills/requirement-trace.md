---
name: commit-message
description: 根据当前 staged diff 生成提交说明；只生成，不执行 commit。
---

# commit-message

## 功能

根据当前已经 staged 的 diff 生成提交说明；只生成，不执行 commit。

## 通用要求

1. 使用中文输出。
2. 默认只读取 staged 变更。
3. 不默认读取所有文档。
4. 只读取完成本技能所需的文件。
5. 当前仓库文件是事实来源。
6. 反馈必须简洁。
7. 不执行 `git commit`。
8. 不把 unstaged 变更写入提交说明。
9. 如果没有 staged 变更，应明确提示用户先执行 `git add`。

## 步骤

1. 查看 staged diff stat、变更文件和关键 diff。
2. 判断本次 staged 变更的核心目的、影响范围和风险点。
3. 生成清晰、可检索、可直接使用的 commit message。
4. 只输出 commit message，不执行 commit。

## 推荐命令

```bash
git diff --staged --stat
git diff --staged --name-status
git diff --staged