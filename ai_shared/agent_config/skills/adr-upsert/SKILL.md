# adr-upsert

## 1. 目的

优先查找并修正已有 ADR，必要时新建 ADR。

## 2. 触发条件

必须判断：
- 影响长期架构。
- 改变接口契约、schema 原则、协议契约、部署策略、运行时能力声明、证据等级规则。
- 记录 rejected option。
- 用户明确要求 ADR。

通常不使用：
- 普通 bugfix。
- 临时测试结果。
- 任务流水账。
- 局部注释修复。
- 纯格式调整。

## 3. 输入

```text
ai_shared/adr/ADR索引.md
相关既有 ADR
变更说明
验证证据
备选方案和拒绝理由
```

## 4. 操作步骤

1. 读取 ADR 索引。
2. 搜索是否已有同主题 ADR。
3. 优先更新已有 ADR，避免重复。
4. 如需新建 ADR，使用递增编号或仓库既有命名规则。
5. 更新 ADR 索引。
6. ADR 只能记录稳定决策，不写未验证结论。

## 5. 新建 ADR 最小结构

```markdown
# ADR-<date-or-id>-<title>

## 状态

Accepted / Proposed / Deprecated / Superseded

## 背景

## 决策

## 影响

## 备选方案

## 拒绝理由

## 验证与后续
```

## 6. 输出格式

```text
skill result:
- skill: adr-upsert
- adr updated:
- adr created:
- index updated:
- decision:
- evidence:
- risk:
```
