# ADR-20260523-003-source-production-client-and-write-port-boundary

## Status

Accepted

## Keywords

- production client
- shared/source
- write port
- command use case
- SourceAcquisitionPort
- SourceWritePort
- clean architecture

## Context

Whale 项目当前已经实现 `source -> cache` 链路：

```text
SourceAcquisitionUseCase
  -> PollingAcquisitionRole / SubscriptionAcquisitionRole
  -> SourceAcquisitionPort
  -> Source adapter
  -> SourceStateCachePort
```

该链路的核心职责是从 source 读取状态并写入 cache。

后续需要补充生产 client 的完整能力，除 read / subscribe 外，还需要 write / control 能力，例如：

- OPC UA 写变量。
- Modbus 写寄存器或线圈。
- IEC 104 遥控 / 遥调 / 设点。
- IEC 61850 MMS control。
- HTTP REST POST / PUT / PATCH。
- MQTT publish。

write/control 与 read/acquisition 的业务语义不同：

- read 是采集状态。
- write 是发起命令或控制。
- read 可连续轮询。
- write 通常需要权限、审计、幂等、超时、确认、失败补偿。
- write 可能有更高安全风险。

因此，write/control 不应塞进现有 `SourceAcquisitionPort` 或 `SourceAcquisitionUseCase`，而应作为独立 port 和独立 use case 演进。

本 ADR 只记录 production client 与 write port 的设计边界，不重复规定 source_lab 是 Task Facade，也不重新定义 source_lab / ingest 的总依赖方向。

## Decision

### 1. Production client 位置

生产 source client 统一在 `src/whale/shared/source` 演进。

长期目标是形成可复用的 source access 能力：

```text
shared/source/access/
  -> protocol-independent source access adapter interfaces
shared/source/{protocol}/
  -> protocol-specific reader/backend/client
```

现有 OPC UA 生产读取路径继续作为第一条生产 client 基线。

非 OPC UA 协议不得直接从 `tools/source_lab` 接入 ingest，而应先在 `shared/source` 中形成生产级 backend / adapter。

### 2. Read / subscribe 继续使用 SourceAcquisitionPort

`SourceAcquisitionPort` 继续只表达采集能力：

- `read(...)`
- `supports_subscription(...)`
- `start_subscription(...)`
- `close(...)`

它不承担 write/control。

`SourceAcquisitionUseCase` 继续只负责编排 source acquisition，不处理控制命令。

### 3. 新增独立 SourceWritePort

后续实现 write/control 时，应新增独立 port：

```text
src/whale/ingest/ports/source/source_write_port.py
```

建议职责：

- 表达 ingest 对 source 写入 / 控制能力的抽象需求。
- 支持单点写入与批量写入。
- 返回明确的 per-item write result。
- 承载 timeout、trace_id、operator/context 等命令上下文。
- 不暴露具体协议 API。
- 不依赖 source_lab。

### 4. 新增独立 SourceCommandUseCase

后续实现 write/control 时，应新增独立 use case：

```text
src/whale/ingest/usecases/source_command_use_case.py
```

建议职责：

- 校验命令请求。
- 做权限 / 审计 / trace 上下文衔接。
- 调用 `SourceWritePort`。
- 处理 write result。
- 不修改 cache 采集语义。
- 不嵌入 polling/subscription role。

### 5. Write adapter

协议写入 adapter 应位于：

```text
src/whale/ingest/adapters/source/
```

例如：

```text
opcua_source_write_adapter.py
modbus_source_write_adapter.py
iec104_source_write_adapter.py
```

adapter 通过 `shared/source` 的生产 client / backend 完成具体协议写入。

### 6. shared/source write 能力

`shared/source` 后续应补齐生产级 write 能力：

- backend protocol 增加 write 方法。
- access adapter 增加 write 方法。
- native runner 增加 WRITE stdin/stdout 协议行。
- simulator 增加可验证写入回显。
- 测试覆盖 write 后再 read 验证。

### 7. 安全与审计约束

write/control 属于高风险能力，后续实现时必须预留：

- operator / actor 上下文。
- trace_id。
- command_id。
- timeout。
- per-item status。
- reason / error code。
- audit hook。
- authorization hook。
- dry-run 或 validation-only 模式。

第一轮实现可以最小化，但接口不能封死这些字段。

## Consequences

### 收益

- 保持 read/acquisition 与 write/control 职责分离。
- 避免 `SourceAcquisitionUseCase` 膨胀成万能 source use case。
- 保持 clean architecture 边界稳定。
- 为命令审计、权限、幂等和安全策略预留空间。
- 支持后续多协议 write 能力逐步接入。

### 代价

- 需要新增 port、DTO、use case、adapter 和测试。
- read client 与 write client 可能短期存在部分重复连接管理。
- 需要在 shared/source 中扩展生产 backend，不可直接复用 source_lab runner。
- 需要新增 simulator write 验证能力。

### 约束

- 不允许在 `SourceAcquisitionPort` 中直接增加 write 方法。
- 不允许在 `SourceAcquisitionUseCase` 中处理命令写入。
- 不允许让 write 操作复用 polling/subscription role。
- 不允许绕过 port 直接从 use case 调 native runner。
- 不允许在未设计审计和权限边界前开放生产控制 API。
- 不允许把 source_lab task runner 当作 write adapter。

## Rejected Options

### 方案一：在 SourceAcquisitionPort 中增加 write 方法

拒绝。

原因：

- 读采集与写控制语义不同。
- 会导致采集 port 膨胀。
- 会污染现有 polling/subscription role。
- 会增加 source->cache 主链路风险。

### 方案二：在 SourceAcquisitionUseCase 中增加 command 分支

拒绝。

原因：

- use case 当前职责是 acquisition。
- command/write 需要独立权限、审计和安全策略。
- 混入后会破坏现有测试边界。

### 方案三：直接调用 source_lab runner 执行 write

拒绝。

原因：

- source_lab runner 是任务测试 worker，不是生产 client。
- 当前 runner 无 write/control 协议。
- 即使补齐 native WRITE，也应先进入 shared/source 生产 client 层，再由 ingest adapter 使用。

### 方案四：先只在 adapter 私有实现 write，不定义 port

拒绝。

原因：

- use case 无法依赖稳定抽象。
- 破坏 clean architecture。
- 不利于多协议替换与测试。

## Related Files

- `src/whale/shared/source/`
- `src/whale/shared/source/access/`
- `src/whale/shared/source/opcua/`
- `src/whale/ingest/usecases/source_acquisition_use_case.py`
- `src/whale/ingest/usecases/roles/polling_acquisition_role.py`
- `src/whale/ingest/usecases/roles/subscription_acquisition_role.py`
- `src/whale/ingest/ports/source/source_acquisition_port.py`
- `src/whale/ingest/adapters/source/opcua_source_acquisition_adapter.py`
- `tools/source_lab/native/open62541/open62541_client_runner.c`
- `tools/source_lab/native/libmodbus/modbus_tcp_polling_runner.c`
- `tools/source_lab/native/lib60870/iec104_client_runner.c`
- `tools/source_lab/native/libiec61850/iec61850_mms_client_runner.c`

## Supersedes / Superseded By

None.

## Implementation Status

2026-05-23: First production write slice completed.

### Completed

1. **SourceWritePort** at `src/whale/ingest/ports/source/source_write_port.py`
   - Independent from SourceAcquisitionPort.
   - Supports per-item write with structured results.
   - No write method added to SourceAcquisitionPort.

2. **SourceCommandUseCase** at `src/whale/ingest/usecases/source_command_use_case.py`
   - Named `source_command_use_case` per industrial control convention.
   - Independent from SourceAcquisitionUseCase.
   - Validates request, resolves protocol via registry, calls write port.
   - Does not write cache, does not publish Kafka.

3. **StaticSourceWritePortRegistry** at `src/whale/ingest/adapters/source/static_source_write_port_registry.py`
   - Style-aligned with StaticSourceAcquisitionPortRegistry.

4. **OpcUaSourceWriteAdapter** at `src/whale/ingest/adapters/source/opcua_source_write_adapter.py`
   - Implements SourceWritePort via OpcUaSourceReader.
   - No import of tools/source_lab.

5. **shared/source OPC UA write extension**
   - RawWriteItemResult added to `backends/base.py`.
   - `write()` method on OpcUaClientBackend Protocol.
   - `write()` and `write_batch()` on Open62541OpcUaClientBackend.
   - `write()` on OpcUaSourceReader facade.

6. **Native C runner WRITE** in `open62541_client_runner.c`
   - ADD WRITE stdin/stdout protocol (connect → write → disconnect → WRITE_RESULT).
   - Supports bool, int32, uint32, int64, uint64, float, double, string types.
   - --version flag added.
   - Existing READY/RESULT/VALUE/POLL_DONE protocol unchanged.

7. **Safety guards**
   - dry_run support in both use case and adapter.
   - WHALE_INGEST_SOURCE_WRITE_ENABLED env var: defaults to disabled.
   - Non-dry_run writes rejected when disabled.
   - Actor/trace_id extension fields preserved.

8. **Capability registry update**
   - OPC UA: production_client_write=true, simulator_write_injection=true.
   - All other protocols: production_client_write=false with clear limitation text.

### Not Yet Implemented (in scope)

- Non-OPC UA write (Modbus FC05/06/15/16, IEC104 C_SC/C_SE/C_BO, IEC61850 Oper).
- Write audit hook integration (field reserved in DTO).
- Write authorization hook (field reserved).
- Batch write optimization in native runner.
- Cache → Kafka message pipeline (separate use case).
