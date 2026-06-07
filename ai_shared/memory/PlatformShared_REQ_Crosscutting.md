# PlatformShared_REQ_Crosscutting

## 一、文件定位

本文件描述 `src/platform_shared` 全系统公共基础库需求。`platform_shared` 为 Whale、Turtle、Octopus、Dolphin、Jellyfish、Manta 提供可复用、无业务归属、无运行状态或弱状态的基础代码能力。

本文件不描述 Whale 数据底座内部 source/persistence 能力，不描述 Turtle 的治理、安全、审计、合规策略，不描述 Octopus 的监控平台、告警平台、部署执行和自动化恢复实现。

`src/whale/shared/crosscutting` 应删除，不再作为公共横切能力入口。

## 二、上承项目级需求

| 项目级需求 | 本模块承接方式 |
|---|---|
| P-NFR-002 | 提供 retry、backoff、timeout、deadline、circuit breaker、error classifier 等韧性基础工具 |
| P-NFR-004 | 提供 logging、metrics、trace、diagnostic context、debug snapshot 等基础 SDK/helper |
| P-NFR-003 | 通过公共契约和工具支撑各组件可替换、可扩展和低耦合接入 |
| P-AR-003 | 承接全系统公共基础库依赖边界 |

## 三、功能需求

### PS-FR-001 observability 基础工具

- 类型：功能
- 优先级：高
- 需求描述：
  - `platform_shared.crosscutting.observability` 应提供轻量 structured logging、metrics、tracing、correlation context 和 event context 基础工具。
- 验收要点：
  - 支持 trace_id、span_id、correlation_id、causation_id。
  - 支持 counter、histogram、gauge 等指标 helper。
  - 不承载审计策略、审计归集、合规证据和运维 dashboard。

### PS-FR-002 resilience 基础工具

- 类型：功能
- 优先级：高
- 需求描述：
  - `platform_shared.crosscutting.resilience` 应提供 retry、backoff、timeout、deadline、circuit breaker 和错误分类能力。
- 验收要点：
  - 支持同步/异步调用包装。
  - 支持策略参数配置。
  - 不承载自动化恢复执行，不替代 Octopus automation。

### PS-FR-003 debug 与诊断上下文

- 类型：功能
- 优先级：高
- 需求描述：
  - `platform_shared.crosscutting.debug` 应提供本地诊断上下文、ring buffer、debug snapshot 和 trace helper。
- 验收要点：
  - debug dump 默认关闭。
  - 诊断输出必须可脱敏。
  - 不承载谁能开启 debug 的治理策略，该策略归 Turtle。

### PS-FR-004 通用契约与基础 kernel

- 类型：功能
- 优先级：高
- 需求描述：
  - `platform_shared.contracts` 和 `platform_shared.kernel` 应提供跨组件通用错误模型、分页模型、Result/Outcome、healthz/readyz 模型、时间工具、ID 工具、序列化工具和校验工具。
- 验收要点：
  - 不包含业务模型。
  - 不包含数据库业务 ORM。
  - 不依赖任何上层组件。

### PS-FR-005 messaging 基础模型

- 类型：功能
- 优先级：高
- 需求描述：
  - `platform_shared.messaging` 应提供跨组件消息 envelope、correlation、schema_version 基础模型。
- 验收要点：
  - 不包含 Kafka/Pulsar 具体 adapter。
  - 具体 broker 适配仍归 Whale message_pipeline。

### PS-FR-006 security primitives

- 类型：功能
- 优先级：高
- 需求描述：
  - `platform_shared.security_primitives` 应提供无策略的 masking、redaction、hash、checksum、digest 等基础工具。
- 验收要点：
  - 不保存脱敏策略。
  - 不进行权限判断。
  - 数据分类、安全区、合规脱敏策略归 Turtle。

## 四、非功能需求

### PS-NFR-001 低侵入复用

- 类型：非功能
- 优先级：高
- 需求描述：
  - platform_shared 能力应通过 helper、decorator、wrapper、middleware 或 composition 接入，不要求业务模块继承 mixin。
- 验收要点：
  - 不污染 use case 核心逻辑。
  - 可按组件选择启用。

### PS-NFR-002 稳定依赖边界

- 类型：非功能
- 优先级：高
- 需求描述：
  - platform_shared 必须保持最小依赖，不得反向依赖任何业务组件或平台组件。
- 验收要点：
  - 不 import whale、turtle、octopus、dolphin、jellyfish、manta。
  - 仅依赖标准库和明确允许的轻量第三方库。

## 五、架构约束

### PS-AR-001 platform_shared 依赖边界

- 类型：架构约束
- 优先级：高
- 需求描述：
  - Whale、Turtle、Octopus、Dolphin、Jellyfish、Manta 可以依赖 platform_shared；platform_shared 不得依赖它们。
- 验收要点：
  - import boundary gate 覆盖该约束。

### PS-AR-002 whale.shared.crosscutting 删除约束

- 类型：架构约束
- 优先级：高
- 需求描述：
  - `src/whale/shared/crosscutting` 必须删除，原 debug/observability/resilience 迁入 `src/platform_shared/crosscutting`。
- 验收要点：
  - `src/whale/shared/crosscutting` 目录不存在。
  - 全仓无 `whale.shared.crosscutting` import。

## 六、测试与验收需求

### PS-TEST-001 platform_shared 质量门禁

- 类型：测试与验收
- 优先级：高
- 需求描述：
  - platform_shared 必须具备单元测试、import boundary 测试和接入型集成测试。
- 验收要点：
  - compileall 通过。
  - ruff 通过。
  - mypy 通过。
  - 全仓旧路径 import 扫描通过。
  - Whale ingest、message_pipeline、speed_layer、storage 关键测试不回退。

## 七、禁止事项

- 不得把 platform_shared 做成垃圾桶。
- 不得放业务模型、协议 client、数据库业务 ORM、Kafka/Pulsar adapter、TDengine/HDFS adapter。
- 不得放 IAM 策略、审计归集、合规规则、部署编排、运维监控平台。
- 不得保留 `whale.shared.crosscutting` 兼容壳。

## 八、需求跟踪表

| 编号 | 上承需求 | 标题 | 类型 | 优先级 | 责任模块 | 验证等级 | 实现状态 | 实现证据 | 验收测试 | 差距 | 下一步 | 更新时间 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PS-FR-001 | P-NFR-004 | observability 基础工具 | FR | 高 | platform_shared | L3 simulator | 已实现并收口 | `src/platform_shared/crosscutting/observability/` (audit.py/logging.py/metrics.py)；6 个业务文件 import 已更新为 platform_shared.*；全仓 0 个 whale.shared.crosscutting import | boundary 79 passed + compileall/ruff/mypy strict clean | context 子包为空壳；完整 tracing/correlation 骨架待填充 | 实现 crosscutting/context 完整能力 | 2026-06-02 |
| PS-FR-002 | P-NFR-002 | resilience 基础工具 | FR | 高 | platform_shared | L3 simulator | 已实现并收口 | `src/platform_shared/crosscutting/resilience/` (backoff.py/circuit_breaker.py/deadline.py/error_classifier.py/retry.py)；关键集成测试和 source_lab 门禁不回退 | boundary 79 passed + compileall/ruff/mypy strict clean + ingest resilience tests 回归 | 无 | 持续维护 | 2026-06-02 |
| PS-FR-003 | P-NFR-004 | debug 与诊断上下文 | FR | 高 | platform_shared | L3 simulator | 已实现并收口 | `src/platform_shared/crosscutting/debug/` (diagnostics.py/ring_buffer.py/trace.py)；import boundary gate 覆盖 platform_shared 全部 22 文件 | boundary 79 passed + compileall/ruff/mypy strict clean | debug dump 治理策略归 Turtle 控制面 | Turtle 治理策略集成 | 2026-06-02 |
| PS-FR-004 | P-NFR-003 | 通用契约与基础 kernel | FR | 高 | platform_shared | L0 | 骨架就绪 | `src/platform_shared/contracts/__init__.py`; `src/platform_shared/kernel/__init__.py` 为空壳骨架 | import 可用（boundary gate 覆盖） | 错误模型/分页/Result/health/API envelope 等尚未实现 | 实现 contracts 和 kernel 完整能力 | 2026-06-02 |
| PS-FR-005 | P-FR-002/P-NFR-003 | messaging 基础模型 | FR | 高 | platform_shared | L0 | 骨架就绪 | `src/platform_shared/messaging/__init__.py` 为空壳骨架 | import 可用（boundary gate 覆盖） | envelope/correlation/schema_version 尚未实现 | 实现 messaging 完整能力 | 2026-06-02 |
| PS-FR-006 | P-NFR-005/P-SCR-001 | security primitives | FR | 高 | platform_shared | L3 simulator | 已实现并收口 | `src/platform_shared/security_primitives/masking.py` (SensitiveDataMasker)；security_primitives/__init__.py 正确导出 | boundary 79 passed（test_platform_shared_symbols_importable 含 SensitiveDataMasker） | hash/redaction 工具尚未实现 | 补充 hash/checksum/redaction helper | 2026-06-02 |
| PS-NFR-001 | P-AR-001 | 低侵入复用 | NFR | 高 | platform_shared | L3 | 已验证 | 迁移通过 decorator/wrapper 模式保持低侵入；8 类横切能力 6 个业务文件 import 均已更新 | boundary 79 passed + compileall/ruff/mypy | 无 | 持续维护 | 2026-06-02 |
| PS-NFR-002 | P-NFR-003 | 稳定依赖边界 | NFR | 高 | platform_shared | L3 | 已验证 | AST 扫描确认 platform_shared 0 个上层依赖（不 import whale/turtle/octopus/dolphin/jellyfish/manta）；仅依赖标准库和明确允许的轻量第三方库 | boundary 79 passed（test_platform_shared_no_upper_dependency） | 无 | 持续维护 | 2026-06-02 |
| PS-AR-001 | P-AR-001 | platform_shared 依赖边界 | AR | 高 | platform_shared | L3 | 已验证并收口 | boundary gate 79 tests + AST scan 确认：platform_shared 不依赖 whale/turtle/octopus/dolphin/jellyfish/manta；whale/turtle/octopus 可正常 import platform_shared | test_platform_shared_no_upper_dependency (AST scan) + test_whale/turtle/octopus_can_import_platform_shared | 无 | 持续维护 | 2026-06-02 |
| PS-AR-002 | P-AR-003 | whale.shared.crosscutting 删除约束 | AR | 高 | platform_shared + whale.shared | L3 | 已验证并收口 | `src/whale/shared/crosscutting/` 整棵目录已物理删除；全仓 AST 扫描 0 个 whale.shared.crosscutting import；11 个旧路径 import 均触发 ImportError | boundary 79 passed（test_crosscutting_directory_deleted + test_whale_no_crosscutting_imports + test_old_crosscutting_paths_raise_import_error） | 无 | 持续维护 boundary gate | 2026-06-02 |
| PS-TEST-001 | P-NFR-004 | platform_shared 质量门禁 | TEST | 高 | platform_shared | L3 | 已通过 | compileall PASS；ruff PASS；mypy (platform_shared strict) PASS；boundary 79/79 PASS；关键 ingest/source_lab 测试不回退 | boundary 79 tests + compileall + ruff + mypy | 无；质量门禁全部收口 | 保持 CI gate 防退化 | 2026-06-02 |
