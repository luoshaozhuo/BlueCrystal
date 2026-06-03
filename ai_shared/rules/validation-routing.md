# 验证路由规则

## 1. 规则定位

本规则用于根据真实变更范围选择验证阶段和验证命令。具体命令以仓库工具链、测试索引和任务 handoff 为准。

## 2. 执行优先级

| 优先级 | 含义 | 收口要求 |
|---|---|---|
| must-run | 本次变更风险必须覆盖 | FAIL 或 NOT_RUN 时不得收口，除非任务明确调整范围 |
| should-run | 建议执行，可由任务范围裁剪 | 未执行时写入后续建议并说明原因 |
| manual-or-expensive | 需要人工、专门环境或高成本资源 | 不自动执行，需记录触发条件 |
| not-run | 与本次变更无关 | 不执行，必要时说明排除理由 |

## 3. 通用路由

| 变更类型 | must-run | should-run | manual-or-expensive |
|---|---|---|---|
| 纯文档、报告、注释文字 | 格式、链接、路径或规则一致性检查 | 相关索引或目录树检查 | 无 |
| 生产源码行为 | 构建期验证、开发期验证 | 模块集成期验证 | 跨模块联调期验证 |
| public interface / API / CLI | 构建期验证、开发期验证、契约测试 | 模块集成期验证、调用方验证 | 跨模块联调期验证 |
| schema / migration / 配置 | 解析和兼容性验证、构建期验证 | 模块集成期验证、部署配置检查 | 数据迁移演练 |
| 消息格式 / 协议 / 文件格式 | parser/serializer、兼容性测试 | 跨模块联调期验证 | 准生产依赖验证期 |
| adapter / repository / external client | 构建期验证、开发期验证、模块集成期验证 | 准生产依赖验证期 | 故障注入、长稳 |
| runtime / scheduler / worker / lease | 构建期验证、开发期验证、模块集成期验证 | 跨模块联调期验证 | failover、并发、长稳 |
| 安全 / 权限 / 审计 / 凭据 | deny/conflict/failure path、审计检查 | 模块集成期验证 | 安全评审、渗透或合规检查 |
| Docker / Compose / deployment / scripts | 脚本语法、配置检查、部署前 smoke | 准生产依赖验证期 | 发布演练、回滚演练 |
| 工具/实验模块 | 工具自身构建期和开发期验证 | 工具自身模块集成期验证 | 只有影响生产边界时才扩展到生产链路 |

## 4. 验证计划输出

执行验证前应形成简短计划：

```text
Validation plan:
- must-run:
- should-run:
- manual-or-expensive:
- not-run:
```

计划应说明阶段、对象、命令或测试索引项。未执行项必须使用 `testing.md` 定义的 NOT_RUN 原因。

## 5. 收口规则

1. `must-run` 中存在 FAIL 时不得收口。
2. `must-run` 中存在 NOT_RUN 时不得收口，除非任务范围明确排除该验证。
3. `should-run` 未执行时，必须记录原因和后续建议。
4. 只执行局部验证时，反馈和报告必须说明局部范围。
5. 工具、mock、fake、stub、simulator 验证不得写成生产真实闭环。
6. 本次变更新增失败不得进入下一阶段。
