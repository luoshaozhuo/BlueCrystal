# ingest 写入回读 L5 现场验证证据模板

> 模板用途：对 OPC UA / Modbus TCP / IEC 61850 MMS 执行真实设备/网关 write-readback 现场验证时，
> 按本模板逐项填写并归档。本模板不替代现场 runbook，仅提供证据收集最小字段集和判定指引。
>
> 证据等级：L5 field（需真实设备/网关环境）。
> 无真实设备时不得填写 L5 结论，应标记为 L3 simulator/native 或 L4 integration。

## 一、站点与环境标识

| 字段 | 填写值 |
|---|---|
| 站点/电场名称 | |
| 安全区 | (管理区 / 采集区 / 控制区) |
| 环境类型 | (生产 / 预生产 / 测试) |
| 网络隔离描述 | |
| 验证日期/时间窗口 | |
| 验证人 | |
| 审批人 | |

## 二、设备/网关信息

| 字段 | 填写值 |
|---|---|
| 协议 | (OPC UA / Modbus TCP / IEC 61850 MMS) |
| 设备/网关型号 | |
| 固件/软件版本 | |
| 设备地址 (IP:port 或 endpoint URL) | |
| 通信方式 | (直连 / 网关代理 / 串口服务器) |
| 认证方式 | (无 / 用户名密码 / 证书 / Token) |
| 安全策略/加密模式 | |

## 三、点位信息

| 字段 | 写入前填写 | 说明 |
|---|---|---|
| 点位标识 (NodeId/Register/Reference) | | 写入目标点位唯一标识 |
| 点位类型 | | BOOL/INT/FLOAT/STRING/... |
| 点位可逆性 | | 可逆（写入后可恢复原值）/ 不可逆（写入后不可恢复） |
| 风险等级 | | 低风险（可逆、非控制）/ 中风险 / 高风险（控制命令） |
| WRITE_ENABLED 确认 | | true |
| CONFIRM_FLAG 确认 | | true |
| actor | | 操作人标识 |
| reason | | 操作原因/工单号 |
| trace_id | | 写入链路追踪 ID |
| command_id | | 写入命令唯一标识 |

## 四、写入验证记录

### 4.1 写入前基线读取 (baseline read)

| 字段 | 填写值 |
|---|---|
| 基线读取时间 | |
| 基线读取值 | |
| 基线读取质量码 | |
| 基线读取耗时 (ms) | |

### 4.2 授权写入 (authorized write)

| 字段 | 填写值 |
|---|---|
| 写入时间 | |
| 写入值 | |
| 写入结果 | (SUCCESS / PARTIAL / FAILED / TIMEOUT / DENIED) |
| 写入耗时 (ms) | |
| write lease ID | |
| fencing token | |
| 审计事件 ID | |

### 4.3 即时回读 (immediate readback)

| 字段 | 填写值 |
|---|---|
| 回读时间 | |
| 回读值 | |
| 与写入值一致性 | (一致 / 不一致 / 在容差范围内) |
| 回读耗时 (ms) | |
| 回读质量码 | |

### 4.4 延迟回读 (delayed readback)

| 字段 | 填写值 | 说明 |
|---|---|---|
| 延迟回读时间 | | 建议写入后 5-30 秒 |
| 延迟回读值 | | 验证值是否保持 |
| 与写入值一致性 | | 一致 / 不一致 |
| 回读耗时 (ms) | | |

### 4.5 值恢复 (value restoration, 可逆点位必填)

| 字段 | 填写值 |
|---|---|
| 恢复时间 | |
| 回写原值 | |
| 恢复后回读时间 | |
| 恢复后回读值 | |
| 与基线值一致性 | (一致 / 不一致 / N/A) |
| 恢复审计事件 ID | |

## 五、失败场景验证

### 5.1 未授权写入

| 字段 | 填写值 |
|---|---|
| 测试时间 | |
| 预期行为 | DENIED / FORBIDDEN |
| 实际行为 | |
| 审计事件是否正确记录 denied | (是 / 否) |

### 5.2 lease 冲突/过期

| 字段 | 填写值 |
|---|---|
| 测试时间 | |
| 冲突场景 | (lease holder mismatch / fencing token stale) |
| 预期行为 | CONFLICT / DENIED |
| 实际行为 | |

### 5.3 source timeout / runner unavailable

| 字段 | 填写值 |
|---|---|
| 测试时间 | |
| 故障注入方式 | |
| 预期行为 | 显式错误，不得静默成功 |
| 实际行为 | |
| 审计是否可追踪失败动作 | (是 / 否) |

## 六、审计与可追溯性

| 字段 | 填写值 |
|---|---|
| audit output 路径 | |
| evidence report 路径 | |
| 失败截图/日志路径 | |
| 审计事件中 actor 是否正确 | (是 / 否) |
| 审计事件中 resource 是否正确 | (是 / 否) |
| 审计事件中 lease/fencing token 是否正确 | (是 / 否) |
| 审计事件中 decision/result 是否正确 | (是 / 否) |
| 凭据是否在日志/审计中泄露 | (否 — 确认未泄露) |

## 七、风险控制措施确认

| 检查项 | 状态 | 说明 |
|---|---|---|
| WRITE_ENABLED 仅验证窗口开启 | |
| 写入前已获得设备管理员授权 | |
| 可逆点位优先选择 | |
| 写入后恢复原值 | |
| 低风险点位优先验证 | |
| 有回滚方案 | |
| 非控制命令（设点/配置类）优先 | |
| 有现场监护人员 | |

## 八、证据等级判定

| 判定项 | 结果 |
|---|---|
| 是否使用真实设备/网关 | (是 / 否) |
| 证据等级 | L5 field（真实设备） / L4 integration（受控依赖） / L3 simulator |
| 是否可用于 production-write-ready | (是 — 仅当 L5 field 全部通过 / 否) |
| 验证人签名 | |
| 审批人签名 | |

## 九、协议特定补充字段

### 9.1 OPC UA

| 字段 | 填写值 |
|---|---|
| endpoint URL | (opc.tcp://...) |
| NodeId (ns=...;s=... 或 ns=...;i=...) | |
| SecurityPolicy | |
| MessageSecurityMode | |
| authentication 类型 | (anonymous / username / certificate) |

### 9.2 Modbus TCP

| 字段 | 填写值 |
|---|---|
| IP:port | |
| Unit ID (Slave ID) | |
| Register 地址 | |
| Function Code | (FC03 / FC06 / FC16) |
| Register 数量 | |
| Endianness | (big-endian / little-endian) |

### 9.3 IEC 61850 MMS

| 字段 | 填写值 |
|---|---|
| IED 名称 | |
| endpoint (MMS URL) | |
| LD/LN/DO/DA 引用路径 | |
| functional constraint (FC) | |
| write 方式 | (MMS Write / Select-Before-Operate) |
| control model | (direct-with-normal-security / sbo-with-normal-security / ...) |

## 十、验证结论

```
[ ] L5 field readback 全部通过 — ingest 写入控制可标 production-write-ready
[ ] L5 field readback 部分通过 — 仍有阻塞项，见差距栏
[ ] 未执行真实设备验证 — 不得标 L5，当前为 L4 integration / L3 simulator
```

### 差距与阻塞

| 差距项 | 阻塞程度 | 说明 |
|---|---|---|
| | | |

### 下一步

| 动作 | 负责人 | 预计完成时间 |
|---|---|---|
| | | |
