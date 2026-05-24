# ADR-20260523-002-source-lab-task-facade-boundary

## Status

Accepted

## Keywords

- source_lab
- facade pattern
- task facade
- protocol client facade
- probe
- capacity
- profile

## Context

对 `tools/source_lab` 的源码探查显示，其公开入口主要围绕三类任务组织：

1. `probe`：现场端点探测。
2. `capacity`：容量扫描。
3. `profile`：性能画像与诊断。

这些入口屏蔽了 provider、runner、registry、simulator、native process 等内部细节，具备 Facade Pattern 特征。

但它们抽象的不是生产协议 client，而是测试与测量任务。生产 client 需要的是 `connect -> read / subscribe / write -> close` 这类长期运行接口，而当前 `tools/source_lab` 的 facade 入口返回的是探测结果、容量结果或画像结果。

因此，需要单独固化 `tools/source_lab` 的 facade 类型，避免后续把它误解为生产协议 client facade。

本 ADR 只记录 `tools/source_lab` 的 facade 类型和对外 API 定位，不重复规定 source_lab / shared/source / ingest 的总依赖边界，也不定义 write port。

## Decision

### 1. Facade 类型

`tools/source_lab` 当前被定义为 **Task Facade**，不是 **Protocol Client Facade**。

它封装的是任务流程：

```text
CLI / test
  -> probe / capacity / profile facade
  -> provider
  -> runner
  -> simulator or native process
  -> report / metrics / result
```

它不封装生产 client 生命周期：

```text
connect
  -> read / subscribe / write
  -> close
```

### 2. Task Facade 的职责

`tools/source_lab` 的 facade 入口允许继续围绕以下任务组织：

- `field_probe.py`
- `field_capacity.py`
- `field_profile.py`
- `access/probe.py`
- `access/capacity.py`
- `access/profile.py`
- `access/runners/registry.py`
- `access/providers/*`

其职责是：

- 降低 CLI 与测试调用复杂度。
- 统一 field 文件、provider、runner、simulator、native process 的组织方式。
- 生成容量、画像、探针报告。
- 验证协议接入能力。
- 为生产 client 抽象提供证据。

### 3. 不是 Protocol Client Facade

`tools/source_lab` 不提供以下生产 client API：

- `connect()`
- `prepare_read()`
- `read_tick()`
- `subscribe()`
- `write()`
- `close()`

如果未来需要生产 client facade，应在 `src/whale/shared/source/access` 中建设，而不是复用 source_lab 的 task facade。

### 4. Facade 泄漏约束

后续维护 `tools/source_lab` 时，应避免继续扩大 facade 泄漏：

- CLI 不应直接拼装过多底层 runner 细节。
- capacity/profile/probe 的请求对象应保持任务语义。
- 不应把生产 client 参数塞进 capacity/profile 配置。
- 不应把 `server_count_start/hz_step/profile_duration` 等测量参数带入 shared/source。
- 不应把 `WorkerRawStats` 作为生产采集结果模型。

### 5. 可以复用的内容

`tools/source_lab` 中可以被生产 client 设计参考或抽取的内容包括：

- native stdout/stderr 协议解析经验。
- protocol capability registry 的能力元数据思想。
- simulator 与 client 的端到端测试矩阵。
- 协议参数映射规则。
- 错误分类和超时参数。
- 端口分配、进程启动、stderr drain 等底层经验。

但这些内容进入生产路径时，必须通过 `shared/source` 重新封装为生产 client 语义。

## Consequences

### 收益

- 明确 `tools/source_lab` 的 facade 是任务外观，不是生产 client 外观。
- 避免后续把 capacity/profile runner 直接接入 ingest。
- 保留 source_lab 作为测试实验室的灵活性。
- 降低生产 client API 被测试任务模型污染的风险。
- 为后续在 shared/source 建设真正的 protocol client facade 留出边界。

### 代价

- source_lab 与 shared/source 之间不能简单复用同一 facade。
- 后续多协议生产 client 需要单独建设 `shared/source/access/{protocol}.py`。
- 一些 runner/native process 管理逻辑可能需要抽取公共底层模块，而不是直接复用 task facade。

### 约束

- 不允许把 `scan_capacity()`、`run_profile()`、`run_probe()` 当作生产采集 API。
- 不允许让 ingest adapter 依赖 `CapacityRunner` 或 `SubscriptionRunner` 的测试结果模型。
- 不允许将 `tools/source_lab/access` 作为生产协议 client 包。
- 如果 source_lab README 或模块 docstring 表述不清，应补充“Task Facade / 测试工具”定位说明。

## Rejected Options

### 方案一：把 source_lab 定义为 Protocol Client Facade

拒绝。

原因：

- 当前入口围绕 probe/capacity/profile，不围绕 connect/read/write。
- 当前返回结果是测试统计和诊断结果，不是采集 batch。
- 当前配置包含容量扫描参数，不适合生产采集。
- 当前无 write/control API。

### 方案二：将 source_lab facade 直接下沉到 shared/source

拒绝。

原因：

- 会把任务模型带入生产 client 层。
- 会混淆测试工具与生产运行时。
- shared/source 应定义稳定生产 client 接口，而不是复用 source_lab 任务入口。

### 方案三：删除 source_lab facade，改成纯底层 runner 调用

拒绝。

原因：

- source_lab 的价值正在于统一组织 probe/capacity/profile。
- 删除 facade 会增加 CLI、测试和容量验证复杂度。
- 当前 Task Facade 对本地开发和现场验证仍然必要。

## Related Files

- `tools/source_lab/field_probe.py`
- `tools/source_lab/field_capacity.py`
- `tools/source_lab/field_profile.py`
- `tools/source_lab/access/probe.py`
- `tools/source_lab/access/capacity.py`
- `tools/source_lab/access/profile.py`
- `tools/source_lab/access/providers/base.py`
- `tools/source_lab/access/providers/field.py`
- `tools/source_lab/access/providers/simulator.py`
- `tools/source_lab/access/runners/base.py`
- `tools/source_lab/access/runners/registry.py`
- `tools/source_lab/access/runners/native_runner_map.py`

## Supersedes / Superseded By

None.
