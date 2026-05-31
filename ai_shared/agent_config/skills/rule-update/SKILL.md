# rule-update

## 1. 目的

用户明确要求更新公共规则时，最小修改 `ai_shared/rules/` 和相关 agent/skill/hook 配置。

## 2. 触发条件

必须使用：
- 用户明确要求更新规则。
- handoff 明确指定规则体系变化。
- 现有 rules / agents / skills / hooks 出现语义冲突。
- 某条规则从 skill 下沉为 rule，或某个 skill 被删除。

禁止使用：
- 普通代码修改。
- 只为单个任务临时增加约束。

## 3. 操作步骤

1. 读取受影响规则、agents、skills、hooks、templates。
2. 判断哪些内容应放在 rule，哪些保留为 skill。
3. 删除或合并无独立闭环的 skill。
4. 保持单一规则源。
5. 多语言规则不得退化为 Python-only。
6. 更新 routing、CLAUDE/AGENTS、agent 定义、prompt template。
7. 输出迁移说明和删除清单。

## 4. 输出格式

```text
skill result:
- skill: rule-update
- rules changed:
- agents changed:
- skills kept:
- skills removed:
- hooks changed:
- templates changed:
- migration notes:
- risk:
```
