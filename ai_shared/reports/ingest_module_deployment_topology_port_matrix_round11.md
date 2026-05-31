# Round 11: ingest 模块部署拓扑 / 端口矩阵 / 通信方向矩阵

## 范围说明

本报告只覆盖 ingest 模块边界，不扩展为全厂站网络设计。目标是满足 `I-READY-004` 的模块级准入证据。

明确排除：

1. `tools/source_lab` 不进入 ingest production runtime path。
2. GOOSE/SV raw socket、L2 namespace、simulator fleet 仍属于工具/实验边界，不计入 ingest 生产部署拓扑。

## 模块拓扑

| 组件 | 部署区位 | 入口通信 | 出口通信 | 说明 |
| --- | --- | --- | --- | --- |
| `ingest-api` | 应用区 / control-plane | HTTP `:8000`（host 示例 `18000:8000`） | PostgreSQL 5432, Redis 6379, Kafka 9092, audit sink, access policy | 提供 API、`healthz/readyz`、bundle 导入、审计入口 |
| `ingest-worker` (`worker-a`,`worker-b`) | 应用区 / execution-plane | 无公网入口；由调度/DB 驱动 | PostgreSQL 5432, Redis 6379, Kafka 9092, shared_source/source endpoint | 执行 acquisition / publish / write jobs |
| `api-worker` | 小规模部署可与 API 同容器命令切换 | HTTP `:8000` + worker 内部 loop | 同 API + worker | 仅模块级紧凑部署；生产推荐分离 API / worker |
| `migrate` | 发布/运维区 | 无长驻入口 | PostgreSQL 5432 | 仅发布/变更窗口调用 |
| Runtime DB (PostgreSQL) | 数据区 | 5432 仅对 ingest runtime 开放 | 无 | 存 runtime job/lease/audit/fencing |
| Redis state cache | 数据区 | 6379 仅对 ingest runtime 开放 | 无 | source state/cache path |
| Kafka | 消息区 | 9092 仅对 ingest runtime 开放 | 下游消费方 | cache->message / state publish |
| Access policy | 安全服务区 | HTTP(S) from ingest only | 无 | 生产 write/control 应 fail-closed |
| Audit sink / SIEM forwarder | 审计区 | HTTP(S)/DB/file from ingest only | 无 | 需与本地审计保底策略配套 |
| shared_source runner artifact | 应用区本地文件系统 | 无网络入口 | source endpoint TCP/serial/L2 gateway | 本轮已与 `tools/source_lab/native/build` 默认路径脱耦 |

## 端口矩阵

| 源 | 目的 | 协议/端口 | 最小开放面 | 是否生产需要 |
| --- | --- | --- | --- | --- |
| Operator / upstream control plane | `ingest-api` | HTTP 8000（host 示例 18000） | 仅 API ingress | 是 |
| `ingest-api` | PostgreSQL | TCP 5432 | 仅 runtime DB | 是 |
| `ingest-api` | Redis | TCP 6379 | 若启用 Redis state cache | 视部署路径 |
| `ingest-api` | Kafka | TCP 9092 | 若 API 承担 publish / pipeline 操作 | 视部署路径 |
| `ingest-api` | Access policy | HTTP(S) custom | 仅授权服务出口 | 生产 write/control 是 |
| `ingest-api` | Audit sink | HTTP(S)/DB/file | 仅审计出口 | 合规生产建议是 |
| `ingest-worker-*` | PostgreSQL | TCP 5432 | 必需 | 是 |
| `ingest-worker-*` | Redis | TCP 6379 | state cache 路径需要 | 视部署路径 |
| `ingest-worker-*` | Kafka | TCP 9092 | publish path 需要 | 视部署路径 |
| `ingest-worker-*` | Source endpoint | 协议端口依协议而定（OPC UA 4840 / Modbus 502 / IEC104 2404 / IEC61850 MMS 102 等） | 仅对目标 source/gateway 开放，按白名单最小化 | 对应协议 job 才需要 |
| `migrate` | PostgreSQL | TCP 5432 | 发布窗口临时开放 | 是 |
| Bundle import client | `ingest-api` | HTTP 8000 | 离线导入入口 | 是 |

## 通信方向约束

1. ingest 到 source 仅允许由 worker 主动发起；source 不应反向调用 ingest worker。
2. API 负责 northbound ingress；worker 不应直接暴露公网写控制入口。
3. bundle 导入是离线/受控操作，经 API 边界进入，不允许直接写 DB 或直接触发 `source_lab`。
4. write/control 默认 disabled；只有授权、lease/fencing、审计链路齐备时才允许放行。
5. `source_lab` 只能作为 dev/test/simulator/tool 路径存在，不进入 ingest 生产运行拓扑。

## 是否允许跨区实时控制

默认不允许把跨区实时控制作为开放能力直接发布。若必须启用：

1. 只能经 `ingest-api` 的授权/审计/lease/fencing 边界进入；
2. 只能由 worker 到目标 source/gateway 单向发起控制；
3. 未完成真实设备 readback 和现场授权联调前，不得标 production-write-ready。

## bundle 离线导入边界

1. bundle 经 API 导入或发布脚本注入，不直接开放 DB 写入口。
2. bundle 只承载配置/资源快照，不替代 source runtime 实时链路。
3. bundle redaction 与最小化原则仍适用，不应承载生产密钥明文。

## 结论

`I-READY-004` 所需的模块级部署拓扑、端口矩阵、通信方向矩阵已补齐为可追溯证据。
但 ingest 仍未 production-ready，原因不在拓扑描述缺失，而在：

1. field write-readback 尚未达到真实设备等级；
2. PostgreSQL 网络分区/旧主恢复仍未闭合；
3. 若启用 write/control，现场 IAM / SIEM / source runner artifact 交付仍需进一步验收。
