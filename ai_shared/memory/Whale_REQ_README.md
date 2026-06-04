# Whale Requirements

## 1. 目录定位

本目录维护 Whale 数据底座及其关联平台组件的项目级和模块级功能/非功能需求。

业务目标与价值愿景以《业务目标与价值愿景.md》为准；总体逻辑边界以《总体逻辑设计.md》为准。本目录保存可验收需求、模块承接关系和需求跟踪表。

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
├── PlatformShared_REQ_Crosscutting.md
├── Turtle_REQ.md
└── Octopus_REQ.md
```

`Whale_REQ_Crosscutting.md` 已废止，应删除，不再维护。原 `whale.shared.crosscutting` 中的 `debug / observability / resilience` 迁入 `platform_shared.crosscutting`；原 `auth / security / compliance / audit / policy` 归入 `Turtle`；监控、告警、诊断执行、自动化恢复归入 `Octopus`。

## 3. 文件职责

| 文件 | 职责 |
|---|---|
| Whale_REQ_Project.md | Whale 数据底座项目级需求、总体架构、模块承接关系 |
| Whale_REQ_Ingest.md | source 接入、状态缓存、消息发布、写入控制 |
| Whale_REQ_SourceLab.md | simulator、probe、profile、capacity、协议验证工具 |
| Whale_REQ_SharedSource.md | production source client、协议 backend |
| Whale_REQ_MessagePipeline.md | 消息主题、schema、分区、回放、DLQ、consumer group |
| Whale_REQ_SpeedLayer.md | 消费消息、写 raw、更新 serving cache、实时轻处理 |
| Whale_REQ_Storage.md | raw_archive、raw_index、standardized、warehouse/mart、serving cache 等存储层 |
| Whale_REQ_Processing.md | 清洗、标准化、质量处理、时间对齐 |
| Whale_REQ_BatchLayer.md | 周期调度、raw -> standardized 批处理、回灌 |
| Whale_REQ_Aggregation.md | 实时聚合、周期聚合、业务主题聚合 |
| PlatformShared_REQ_Crosscutting.md | 全系统公共基础库：observability、debug、resilience、context、contracts、kernel、messaging、security_primitives |
| Turtle_REQ.md | 治理、安全、审计、合规、策略、部署准入、变更控制 |
| Octopus_REQ.md | 运维观测、统一部署编排、监控、告警、诊断、自动化恢复、回滚和运行报告 |

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
| PlatformShared | PS | PS-FR-001 |
| Turtle | TU | TU-FR-001 |
| Octopus | OC | OC-FR-001 |

需求类型：

```text
FR     功能需求
NFR    非功能需求
AR     架构约束
DGR    数据治理需求
SCR    安全合规需求
TEST   测试与验收需求
READY  部署/生产准入需求
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

验证等级按 `ai_shared/rules/testing.md` 软件生命周期测试阶段定义，使用简短编号引用：

- P1 开发期验证 — 本地逻辑、接口约束、边界条件和错误路径
- P2 构建期验证 — 可构建、可导入、可静态检查
- P3 模块集成期验证 — 单一模块内部组件协作
- P4 跨模块联调期验证 — 多模块数据流和调用链路
- P5 准生产依赖验证期 — 真实或等价外部依赖下的行为
- P6 部署前验收期 — 部署配置、运行入口、预检、smoke
- P7 发布后运维验证期 — 故障恢复、容量、性能、可观测性

NOT_RUN 原因码（MISSING_ENVIRONMENT、OUT_OF_SCOPE 等）适用，
表示该阶段在当前环境下未执行。

原 L0"代码存在"不再作为验证等级——代码存在是开发事实而非验证结果。

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
- `platform_shared` 不得依赖 Whale、Turtle、Octopus、Dolphin、Orca、Manta。
- `whale.shared` 只服务 Whale 内部，不得被其他并列组件依赖。
- 现场真实电站、真实设备、真实生产网络环境验证不作为本项目需求跟踪表验证等级；若发生，只能作为独立交付/验收/运维证据归档，不替代 P1-P7。
