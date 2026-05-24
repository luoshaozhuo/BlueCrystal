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
