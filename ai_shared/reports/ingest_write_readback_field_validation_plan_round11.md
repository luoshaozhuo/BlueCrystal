# Round 11: ingest 写入 readback 现场验证计划

## 结论

本轮补齐 `I-READY-005` 的证据边界和可执行入口，但**没有**把 simulator/native/L2/L3 证据写成 field-ready。

当前结论：

1. write/control 默认关闭、授权、lease、fencing、审计链路已具备基础实现。
2. 三协议已有 contract / simulator / native integration 证据。
3. 在通过真实设备或真实现场网关 readback 之前，**不得**将 ingest 标为 production-write-ready。

## 当前证据等级

| 协议 | 现有证据 | 等级 | 说明 | 是否可用于 production-write-ready |
| --- | --- | --- | --- | --- |
| OPC UA | `tests/unit/test_opcua_source_write_adapter.py`; `tests/integration/test_ingest_opcua_source_write.py` | L2 + L3 | mock contract + open62541 simulator/native runner readback smoke | 否 |
| Modbus TCP | `tests/unit/test_modbus_source_write_adapter.py`; `tests/integration/test_ingest_modbus_source_write.py` | L2 + L3 | mock contract + Modbus simulator/native runner readback smoke | 否 |
| IEC 61850 MMS | `tests/unit/test_iec61850_source_write_adapter.py`; `tests/integration/test_ingest_iec61850_mms_source_write.py` | L2 + L3 | mock contract + simulator server/native runner 多类型 write-then-readback | 否 |

## 本轮新增可执行入口

1. simulator/native smoke：
   - `scripts/run_ingest_write_readback_smoke.sh`
   - 运行三协议现有 integration tests
   - 证据等级仍然是 L3，不等于现场设备
2. shared_source runner 生产边界：
   - 默认不再隐式落回 `tools/source_lab/native/build`
   - 若要本地联调，必须显式设置每协议 runner 环境变量或启用 dev fallback

## 现场验证计划（L5 pending）

### 阶段 1：部署前准入

1. 明确目标协议、目标设备/网关、地址清单、写入点白名单。
2. 确认生产 runner artifact 已独立安装，不依赖 `tools/source_lab/native/build`。
3. 确认 `WHALE_INGEST_SOURCE_WRITE_ENABLED=true` 仅在受控窗口、受控 actor、受控资源范围内开启。
4. 确认外部 access policy 为 fail-closed，审计 sink 可落本地保底。

### 阶段 2：现场单点 readback

每个协议至少选择 1 个低风险可逆点位，执行：

1. baseline read
2. authorized write
3. immediate readback
4. second delayed readback
5. 审计核对：actor、resource、lease、fencing token、decision、result
6. 回写原值并再次 readback

必须记录：

1. target endpoint / device / gateway
2. write payload
3. first readback latency
4. delayed readback consistency
5. operator approval / rollback result

### 阶段 3：失败场景

每个协议至少验证：

1. unauthorized write 被拒绝
2. lease holder mismatch / fencing token stale 被拒绝
3. source timeout / runner unavailable 返回显式错误，不得静默成功
4. 审计仍可追踪失败动作

## 建议执行命令

本地/实验室 smoke：

```bash
bash scripts/run_ingest_write_readback_smoke.sh
```

现场验证建议以受控 runbook 执行，不建议直接复用 CI 命令替代现场证据。

## 阻塞结论

`I-READY-005` 本轮仍未收口。阻塞项：

1. 无真实设备 / 真实网关 / 真实现场授权的 L5 readback 证据；
2. 现场失败回滚与多角色审批尚未归档；
3. 因此 ingest 仍不能标记为 production-write-ready。
