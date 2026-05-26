# ADR 索引

ADR 全称 Architecture Decision Record，即架构决策记录。

## 用途

只记录长期有效的架构、技术路线、边界、协议、schema 原则、数据契约等决策，不记录普通任务日志。

## 命名规则

```text
ADR-YYYYMMDD-NNN-domain-topic-decision.md
```

示例：

```text
ADR-20260523-001-cache-redis-default-backend.md
ADR-20260523-002-source-access-ingest-boundary.md
ADR-20260523-003-subscribe-recovery-poll-before-subscribe.md
```

## 维护原则

1. 使用 adr-upsert 时，先查找已有 ADR。
2. 优先修正或补充已有 ADR。
3. 只有没有相关 ADR 时才新建。
4. 被替代的 ADR 标记为 Superseded，并指向新 ADR。
5. 文件名必须便于检索。
6. 多个 ADR 必须职责互斥，不应重复记录同一决策。
7. 上游边界 ADR 只记录依赖方向和职责边界；细化 ADR 只记录专项决策。

## ADR 列表

| ADR | Status | 主题 | 边界 |
|---|---|---|---|
| ADR-20260523-001-source-lab-server-client-ingest-boundary.md | Accepted | source_lab / shared/source / ingest 总体边界 | 只记录三者依赖方向、server/simulator 与 production client 的位置，不记录 facade 类型和 write port 设计 |
| ADR-20260523-002-source-lab-task-facade-boundary.md | Accepted | source_lab Task Facade 类型 | 只记录 source_lab 是任务外观，不是生产协议 client 外观 |
| ADR-20260523-003-source-production-client-and-write-port-boundary.md | Accepted | production client 与 write port 边界 | 只记录生产 client 在 shared/source 演进、write/control 独立 port/use case |
| ADR-20260524-004-source-protocol-production-readiness-gate.md | Accepted | 生产协议准入与 capacity/profile 门禁规则 | 只记录 production_client_read/write 标记、capability registry 治理、capacity/profile 必须通过、不得 skipped、不得用 source_lab task facade 冒充 production client |
| ADR-20260524-005-cache-to-message-queue-publish-use-case.md | Accepted | 缓存快照到消息队列发布用例边界 | 只记录独立 publish use case 职责、端口复用、全量快照语义、字段映射 fallback、composition 显式注入 publisher |
| ADR-20260524-006-source-lab-protocol-directory-consolidation.md | Accepted | source_lab 协议目录统一治理 | 只记录 `tools/source_lab/opcua/` 迁移到 `protocols/opcua/`、删除旧目录、不保留兼容 shim |
| ADR-20260524-007-iec61850-mms-production-read-write-round1.md | Accepted | IEC 61850 MMS 生产读写第一闭环 | 只记录 MMS 直接读/写、每个命令独立建连、FC 从外部传入、写入类型白名单、协议行格式 |
| ADR-20260524-008-iec61850-report-subscription-boundary.md | Accepted (v3) | IEC 61850 Report 订阅采集收口 | 只记录 Report 是订阅能力、C 子进程 stdin/stdout、Report/GOOSE/SV 分离、Round 2 reconnect/composition/gate、Round 3 load 隔离/测试补充/回归确认 |
| ADR-20260524-009-source-lab-server-simulator-facade.md | Accepted (v10) | source_lab 统一 ServerSimulatorFacade 契约 | 只记录统一异步 Protocol、SimulatorStatus 状态码、默认 NOT_IMPLEMENTED 基类、各协议 facade 能力矩阵、工厂注册表、旧 opcua/ 目录删除收口；Round 2 能力降级；Round 3 MMS/Report/Modbus/OPC UA 真实读写；Round 3.5 OPC UA/Modbus TCP/IEC104 真实读、SimulatorSourceProvider 默认 facade 路径迁移；Round 4 CI E2E 验收 + capacity/profile 多协议 closure；Round 4.1 NativeCmdCapacityRunner 预检 + MMS 多点读取；Round 5-1 IEC104 C 子进程 facade + OPC UA/IEC104 capacity/profile E2E 全协议 4 矩阵收口；Round 5-2 IEC101/Modbus RTU 真实读 + E2E 6 矩阵；Round 5-3 HTTP REST 真实 HTTP GET、MQTT 真实 CONNECT/SUBSCRIBE、OPC UA 真实 asyncua subscribe、polling E2E 8 协议、streaming E2E 5 协议、报告模板治理；Round 5-4 IEC61850 GOOSE/SV native publisher/subscriber、streaming 条件 E2E、pytest-asyncio 依赖治理；Round 5-5 全协议最终 capability matrix、GOOSE/SV target/version gate、当前无 CAP_NET_RAW 时 CI pending 且不得写 PASS |
