# Whale Requirements

## 1. 目录定位

本目录维护 Whale 项目的项目级和模块级功能/非功能需求。

`ai_shared/memory/Whale项目说明.md` 保存项目背景、长期边界和工程原则；本目录保存可验收需求、模块承接关系和需求跟踪表。

## 2. 文件清单

```text
ai_shared/requirements/
├── Whale_REQ_README.md
├── Whale_REQ_Project.md
├── Whale_REQ_Ingest.md
├── Whale_REQ_SourceLab.md
├── Whale_REQ_SharedSource.md
├── Whale_REQ_MessagePipeline.md
├── Whale_REQ_SpeedLayer.md
├── Whale_REQ_Storage.md
├── Whale_REQ_Processing.md
├── Whale_REQ_BatchLayer.md
├── Whale_REQ_Aggregation.md
└── Whale_REQ_Crosscutting.md
```

## 3. 文件职责

| 文件 | 职责 |
|---|---|
| Whale_REQ_Project.md | 项目级需求、总体架构、模块承接关系 |
| Whale_REQ_Ingest.md | source 接入、状态缓存、消息发布、写入控制 |
| Whale_REQ_SourceLab.md | simulator、probe、profile、capacity、协议验证工具 |
| Whale_REQ_SharedSource.md | production source client、协议 backend |
| Whale_REQ_MessagePipeline.md | 消息主题、schema、分区、回放、DLQ、consumer group |
| Whale_REQ_SpeedLayer.md | 消费消息、写 raw、更新 serving cache、实时轻处理 |
| Whale_REQ_Storage.md | raw、standard、warehouse/mart、serving cache 等存储层 |
| Whale_REQ_Processing.md | 清洗、标准化、质量处理、时间对齐 |
| Whale_REQ_BatchLayer.md | 周期调度、raw -> standard 批处理、回灌 |
| Whale_REQ_Aggregation.md | 实时聚合、周期聚合、业务主题聚合 |
| Whale_REQ_Crosscutting.md | 日志、指标、追踪、审计、安全、韧性、诊断 |

## 4. 编号规则

| 层级 | 前缀 | 示例 |
|---|---|---|
| Project | P | P-FR-001 |
| Ingest | I | I-FR-001 |
| SourceLab | SL | SL-FR-001 |
| SharedSource | SS | SS-FR-001 |
| MessagePipeline | MP | MP-FR-001 |
| SpeedLayer | SP | SP-FR-001 |
| Storage | ST | ST-FR-001 |
| Processing | PR | PR-FR-001 |
| BatchLayer | BL | BL-FR-001 |
| Aggregation | AG | AG-FR-001 |
| Crosscutting | CT | CT-FR-001 |

需求类型：

```text
FR     功能需求
NFR    非功能需求
AR     架构约束
DGR    数据治理需求
SCR    安全合规需求
TEST   测试与验收需求
```

## 5. 实现状态与验证等级

实现状态：

- 未实现
- 部分实现
- 代码完成待验证
- 测试通过
- 运行闭环通过
- 暂不支持
- 已废弃

验证等级：

- L0：代码存在
- L1：单元测试通过
- L2：集成测试通过
- L3：simulator E2E 通过
- L4：profile/capacity 通过
- L5：运行闭环通过

## 6. 跟踪表字段

每个需求文件必须包含独立跟踪表：

```text
| 编号 | 上承需求 | 标题 | 类型 | 优先级 | 责任模块 | 验证等级 | 实现状态 | 实现证据 | 验收测试 | 差距 | 下一步 | 更新时间 |
```

## 7. 维护规则

- 需求正文只描述系统必须具备的能力和验收标准。
- 实现状态、当前差距、下一步动作只写入需求跟踪表。
- 不得在需求描述中写“当前建议”“后续可以”“可能需要”。
- 修改实现状态必须读取源码、测试、报告或 ADR。
- skipped 测试不得作为完成证据。
- failed 必须明确处理。
