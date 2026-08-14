---
name: changed-files-gate
description: Use when you need the real changed-file set from the current Git workspace before or after implementation, validation, or project stewardship work, and when Git status must not be inferred from another agent's summary.
---

# changed-files-gate

## 1. 目的

获取本轮真实变更范围，供实现、验证、文档更新使用。

## 2. 触发条件

必须使用：
- code-implementer 编码前和编码后。
- test-validator 验证前。
- project-steward 更新文档、需求、规则或 project_tree 前。

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
- tier_hint: light|standard|full
```

## 5. 判定规则

1. 出现 untracked 文件时必须列出。
2. 不根据文件变化自动判断或触发 `project-tree-update` / `project-tree-reset`；两者仅响应用户的明确要求，handoff 必须转述该请求。
3. 如果工作区存在与本轮无关的既有变更，必须标注，避免误改。

## 6. tier_hint 判定

`tier_hint` 是基于 changed files 路径模式给出的建议任务等级，主会话据其判断 `task_tier`。判定优先级自上而下，首条命中即返回：

```text
1. 命中白名单路径（任一即返回 full）：
   - public interface / API / CLI / handler：src/.../api/、src/.../cli/、src/.../handlers/、*handler*.py、*endpoint*.py
   - schema / migration / 配置 / 环境变量：migrations/、alembic/、*.sql、.env*、config/*.yaml、config/*.toml
   - 消息格式 / 协议 / 文件格式：src/.../protocols/、src/.../codec/、src/.../schemas/、*schema*.py、*.proto、*.avsc
   - adapter / repository / external client / gateway：src/.../adapters/、src/.../repository/、src/.../gateway/、src/.../clients/
   - runtime / scheduler / worker / lease / fencing：src/.../runtime/、src/.../scheduler/、src/.../workers/、*lease*.py、*fencing*.py
   - 安全 / 权限 / 审计 / 凭据：src/.../auth/、src/.../security/、*permission*.py、*audit*.py、*credentials*.py
   - deploy/ / docker / compose / helm / terraform：deploy/、Dockerfile*、docker-compose*、charts/、*.tf、*.tfvars
2. handoff 显式引用 heavy-regression skill → full
3. 跨 ≥3 个 module（按 src/<module>/ 一级目录计数）→ full
4. 命中 src/ 或 tests/（未命中白名单）→ standard
5. 命中 ai_shared/、docs/、*.md（非规则改造）→ light
6. 其他 → light
```

说明：tier_hint 是建议值，最终 task_tier 由主会话在收到 code-implementer 的 `require_full_validation` 声明后确认。
