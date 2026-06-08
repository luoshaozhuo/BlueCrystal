# BlueCrystal_REQ_SourceLab

## 一、文件定位

本文件描述 BlueCrystal `tools/source_lab` 模块承担的 simulator、probe、profile、capacity、协议验证和本地开发测试需求。

本文件不描述 ingest 生产 use case，不描述 shared_source production client 内部实现。

## 二、上承项目级需求

| 项目级需求 | 本模块承接方式 |
|---|---|
| P-FR-001 | 提供 server simulator、probe、profile、capacity 作为协议准入验证 |
| P-NFR-001 | 提供容量与性能画像工具 |
| P-AR-002 | 保持工具层定位，不进入 ingest 生产依赖 |

## 三、协议能力矩阵

| 协议 | simulator | read | write | subscribe | report | probe | profile | capacity | 状态 |
|---|---|---|---|---|---|---|---|---|---|
| opcua | 已验证 | 已验证 | 已验证 | 已验证 | NOT_IMPLEMENTED | 已验证 | 已验证 | 已验证 | 测试通过 |
| modbus_tcp | 已验证 | 已验证 | 已验证 | NOT_IMPLEMENTED | NOT_IMPLEMENTED | 已验证 | 已验证 | 已验证 | 测试通过 |
| iec104 | 已验证 | 已验证 | NOT_IMPLEMENTED（工具层）；PROTOCOL_CAPABILITIES write=True（生产客户端已完成） | facade 不支持 | NOT_IMPLEMENTED | 已验证 | 已验证 | 已验证 | 测试通过（工具层）；生产采集+写入已 production-ready（shared_source/ingest，Round 26） |
| iec61850_mms | 已验证 | 已验证 | 已验证 | NOT_IMPLEMENTED | NOT_IMPLEMENTED | 已验证 | 已验证 | 已验证 | 测试通过 |
| iec61850_report | 已验证 | NOT_IMPLEMENTED | NOT_IMPLEMENTED | 已验证 | 已验证 | 已验证 | 已验证 | 已验证 | 测试通过；动态runtime已验证 |
| iec101 | 已验证 | 已验证（shared_source production backend：real os/termios/fcntl serial，FT1.2+ASDU interrogation，read-only） | NOT_IMPLEMENTED（shared_source/ingest 均 NOT_IMPLEMENTED） | facade 不支持 | NOT_IMPLEMENTED | 已验证 | 已验证 | 已验证 | acquisition-ready（read-only serial；L4/L5 serial hardware=environment-pending；ingest adapter 已注册 composition.py） |
| modbus_rtu | 已验证 | 已验证（shared_source production backend：real os/termios/fcntl serial，CRC16+FC03 read-only） | NOT_IMPLEMENTED（shared_source/ingest 均 NOT_IMPLEMENTED） | NOT_IMPLEMENTED | NOT_IMPLEMENTED | 已验证 | 已验证 | 已验证 | acquisition-ready（read-only serial；L4/L5 serial hardware=environment-pending；ingest adapter 已注册 composition.py） |
| mqtt | 已验证 | NOT_IMPLEMENTED | NOT_IMPLEMENTED | 已验证 | NOT_IMPLEMENTED | 已验证 | 已验证 | 已验证 | 测试通过 |
| http_rest | 已验证 | 已验证 | NOT_IMPLEMENTED | NOT_IMPLEMENTED | NOT_IMPLEMENTED | 已验证 | 已验证 | 已验证 | 测试通过 |
| goose | 已验证 | NOT_IMPLEMENTED | NOT_IMPLEMENTED | 已验证 | NOT_IMPLEMENTED | 已验证 | 已验证 | 已验证 | 测试通过；需受控L2环境 |
| sv | 已验证 | NOT_IMPLEMENTED | NOT_IMPLEMENTED | 已验证 | NOT_IMPLEMENTED | 已验证 | 已验证 | 已验证 | 测试通过；需受控L2环境 |
| beckhoff_ads | 已验证（in_process） | 已验证（in_process） | 已验证（in_process） | NOT_IMPLEMENTED | NOT_IMPLEMENTED | environment-pending | environment-pending | environment-pending | environment-pending；三类backend（in_process 34 passed / beckhoff_dotnet 7 skipped / native_adslib 1 skipped）；ADS_NOTIFICATION NOT_IMPLEMENTED |

## 三、功能需求

### SL-FR-001 统一 ServerSimulatorFacade

- 类型：功能
- 优先级：高
- 需求描述：
  - source_lab 应为所有协议 server simulator 提供统一 ServerSimulatorFacade。
- 验收要点：
  - 所有协议 facade 均实现 start、stop、health、load_points、read、write、subscribe、report、update_values、capabilities。
  - 不支持能力返回 NOT_IMPLEMENTED。
  - capability 声明必须与测试一致。

### SL-FR-002 协议 server simulator

- 类型：功能
- 优先级：高
- 需求描述：
  - source_lab 应为声明支持的协议提供可本地启动的 server simulator。
- 验收要点：
  - simulator 可启动、可停止、可健康检查。
  - simulator 可根据点表加载变量或明确返回 NOT_IMPLEMENTED。
  - 支持 read/write 的协议必须能 readback。
  - 支持 subscribe/report 的协议必须能触发真实事件。

### SL-FR-003 probe/profile/capacity 工具

- 类型：功能
- 优先级：高
- 需求描述：
  - source_lab 应提供现场和本地 server 的 probe、性能画像和容量扫描工具。
- 验收要点：
  - probe 验证 endpoint、协议握手、认证参数、点位映射和最小读取。
  - profile 输出 tick latency、read duration、callback delay、jitter、p50/p95/p99、period_samples。
  - capacity 支持扫描 server_count、point_count、frequency，并输出 pass/fail、瓶颈原因和最大稳定容量。

### SL-FR-004 多协议 native runner 管理

- 类型：功能
- 优先级：高
- 需求描述：
  - source_lab 应管理多协议 native runner 和 simulator 的构建、发现、启动、停止和协议行解析。
- 验收要点：
  - 支持二进制预检。
  - 缺失二进制返回清晰 unavailable。
  - 错误消息包含 protocol、runner、path、build hint。
  - 支持 stdout/stderr 分离。

### SL-FR-005 动态 EndpointRuntime

- 类型：功能
- 优先级：高
- 需求描述：
  - source_lab 应提供 endpoint-level dynamic runtime，用于对 polling、subscribe、report、streaming 采集对象进行运行期局部 stop/pause/resume/update/replace，并用 continuity metrics、operation journal、state recovery 证明未调整 endpoint 不受影响。
- 验收要点：
  - 支持 endpoint runtime registry。
  - 支持 endpoint-level session replacement。
  - 支持 config_version 与 expected_version 冲突检测。
  - 支持 stagger offset 保持。
  - 支持 continuity metrics。
  - 支持 operation journal。
  - 支持 RuntimeStateStore recovery / checksum / backup / repair。
  - 支持 CLI accepted state import/export/validate/schema。
  - 支持 Modbus/HTTP/MQTT/OPC UA/IEC61850 Report/GOOSE/SV 动态隔离验证。

## 四、非功能需求

### SL-NFR-001 真实性与可复现性

- 类型：非功能
- 优先级：高
- 需求描述：
  - source_lab 的协议验证必须走真实协议、真实 runner 和真实 simulator，并可在本地和 CI 环境复现。
- 验收要点：
  - read/write/readback 不能只读写内部字典。
  - subscribe/report 必须有 callback/event。
  - 测试不得仅验证 lifecycle 或 TCP health。
  - 构建命令、native 依赖、skip 原因必须明确。

### SL-NFR-002 稳定性与资源清理

- 类型：非功能
- 优先级：高
- 需求描述：
  - source_lab 工具应能稳定启动、停止和清理资源。
- 验收要点：
  - 无 zombie process。
  - stdout noise = 0。
  - runner crash 可观测。
  - timeout 可配置。
  - 多轮运行无端口残留。

## 五、架构约束

### SL-AR-001 工具层边界

- 类型：架构约束
- 优先级：高
- 需求描述：
  - source_lab 是测试、验证和诊断工具层，不是生产 ingest 运行时依赖。
- 验收要点：
  - ingest 不 import tools.source_lab。
  - source_lab runner 不作为 production client。
  - source_lab 可验证 shared_source production client，但不替代 shared_source。

### SL-AR-002 protocols / native / access 分层

- 类型：架构约束
- 优先级：高
- 需求描述：
  - protocols 目录承载 simulator facade、协议资源和轻量包装；native 目录承载 C runner / simulator；access 目录承载 probe/profile/capacity 任务。
- 验收要点：
  - protocols 不承载 production client。
  - native C simulator 不移动到 protocols。
  - tools/source_lab/opcua 旧路径不得回归。

## 六、测试与验收需求

### SL-TEST-001 simulator contract 与真实协议测试

- 类型：测试与验收
- 优先级：高
- 需求描述：
  - 所有协议 facade 必须通过统一 contract 测试，声明支持的 read/write/subscribe/report 必须有真实协议 smoke。
- 验收要点：
  - 方法集完整。
  - capabilities 可读取。
  - unsupported 能力返回 NOT_IMPLEMENTED。
  - 真实协议 smoke 通过。
  - failed = 0。

### SL-TEST-002 capacity/profile E2E

- 类型：测试与验收
- 优先级：高
- 需求描述：
  - capacity/profile 必须基于 ServerSimulatorFacade 做端到端验证。
- 验收要点：
  - 至少覆盖 modbus_tcp、iec61850_mms。
  - 支持 protocol 参数切换。
  - period_samples > 0。
  - load 测试有独立 marker。

## 七、禁止事项

- 不得用 fake OK。
- 不得用 TCP health 冒充协议能力。
- 不得把 simulator 等同 production client。
- 不得恢复 tools/source_lab/opcua。

## 八、工具模块部署准入与证据边界

本章只描述 `source_lab` 作为独立工具模块的部署准入、权限边界和证据边界。`source_lab` 不是 production source client，不进入 `ingest` production runtime path，也不替代 `shared_source` 的真实 production client 能力。

### SL-READY-001 source_lab 独立工具部署准入

- 类型：工具部署准入
- 优先级：高
- 需求描述：
  - source_lab 应能作为独立工具模块运行 simulator、probe、profile、capacity 和 native runner 预检。
- 验收要点：
  - 可独立运行 simulator / probe / profile / capacity。
  - native runner 预检清晰。
  - 缺少 native binary 时返回明确 unavailable，并给出 protocol、runner、path、build hint。
  - stdout/stderr 协议稳定，不把噪声输出解析为有效数据。
  - timeout 和资源清理可验证。
  - 不依赖 ingest production runtime。
  - 不替代 SharedSource production client。

### SL-READY-002 source_lab 权限与运行环境边界

- 类型：工具部署准入
- 优先级：高
- 需求描述：
  - source_lab 涉及 native runner、raw socket、GOOSE/SV、network namespace 等能力时，必须显式说明运行权限和环境边界。
- 验收要点：
  - source_lab 不进入 ingest production runtime path。
  - source_lab 不作为 production client。
  - raw socket / GOOSE / SV 只能在受控 L2 环境运行。
  - 需要 root、capability、network namespace、veth 或 raw socket 权限时必须显式说明。
  - 运行后必须清理进程、端口、临时文件和网络命名空间。
  - source_lab 不得默认部署到生产控制区。

### SL-READY-003 source_lab 证据边界

- 类型：工具部署准入
- 优先级：高
- 需求描述：
  - source_lab 的测试通过结果必须保留工具证据边界，不得自动外推为 ingest 或 shared_source 的生产就绪。
- 验收要点：
  - source_lab PASS 只能证明 simulator/tool/protocol validation。
  - source_lab PASS 不能自动证明 ingest production-ready。
  - PROTOCOL_CAPABILITIES 静态声明不能作为 runtime readiness 事实来源。
  - gateway mode、NOT_IMPLEMENTED、受控 L2 环境必须保留证据标签。
  - GOOSE/SV true PASS 必须带受控 L2 环境条件。
  - SharedSource production client 的真实协议能力仍以 SharedSource 需求和测试为准。

## 九、需求跟踪表

| 编号 | 上承需求 | 标题 | 类型 | 优先级 | 责任模块 | 验证等级 | 实现状态 | 实现证据 | 验收测试 | 差距 | 下一步 | 更新时间 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| SL-FR-001 | P-FR-001 | 统一 ServerSimulatorFacade | FR | 高 | source_lab | L3（simulator facade）+ L4（shared persistence 输入契约消费）+ L2 contract（beckhoff_dotnet/native_adslib preflight） | 部分实现 | `tools/source_lab/protocols/common/simulator_facade.py`; `tools/source_lab/protocols/registry.py`; `tools/source_lab/protocols/beckhoff_ads/`; `tools/source_lab/access/providers/scada_profile.py`; `tools/source_lab/access/providers/simulator.py`; `tools/source_lab/access/runners/beckhoff_ads_polling.py`; `tools/source_lab/access/runners/registry.py`; `tools/source_lab/access/runners/native_runner_map.py`; `tools/source_lab/tests/access/test_server_simulator_facade_contract.py`; `tools/source_lab/tests/access/test_scada_profile_provider.py`; `tools/source_lab/tests/access/test_scada_profile_runtime_coverage.py`; `tools/source_lab/tests/access/test_scada_profile_facade_smoke.py`; `tools/source_lab/tests/access/test_beckhoff_ads_simulator_contract.py`; `tools/source_lab/tests/access/test_beckhoff_ads_client_runner_protocol.py`; `tools/source_lab/tests/access/test_beckhoff_ads_capacity_profile_gate.py`; `tools/source_lab/tests/access/test_beckhoff_ads_dotnet_virtual_server.py`; `tools/source_lab/tests/access/test_beckhoff_ads_environment_probe.py`; `tools/source_lab/tests/access/test_beckhoff_ads_native_preflight.py`; `tools/source_lab/tests/access/test_beckhoff_ads_real_protocol_readback.py`; `tests/integration/test_source_lab_scada_profile.py`; `tests/integration/test_source_lab_scada_profile_postgres.py`; `tests/integration/test_source_lab_beckhoff_ads_runtime.py`; `tests/support/scada_sample_db.py`; `src/whale/shared/persistence/template/protocol_param_data.py`; `src/whale/shared/persistence/template/sample_data.py`; `tests/integration/test_shared_persistence_sample_data_init.py` | `pytest tools/source_lab/tests/access/test_server_simulator_facade_contract.py -q` -> 137 passed；`pytest tools/source_lab/tests/access/test_scada_profile_provider.py -q` -> 4 passed；`pytest tools/source_lab/tests/access/test_scada_profile_runtime_coverage.py -q` -> 17 passed；`pytest tools/source_lab/tests/access/test_scada_profile_facade_smoke.py -q` -> 15 passed；`pytest tools/source_lab/tests/access/test_beckhoff_ads_simulator_contract.py -q` -> 4 passed；`pytest tools/source_lab/tests/access/test_beckhoff_ads_client_runner_protocol.py -q` -> 3 passed；`pytest tools/source_lab/tests/access/test_beckhoff_ads_capacity_profile_gate.py -q` -> 2 passed；`pytest tests/integration/test_source_lab_scada_profile.py -q` -> 2 passed；`pytest tests/integration/test_source_lab_scada_profile_postgres.py -q` -> 1 passed；`pytest tests/integration/test_source_lab_beckhoff_ads_runtime.py -q` -> 2 passed；`pytest tools/source_lab/tests/access/test_beckhoff_ads_dotnet_virtual_server.py -q` -> 1 passed, 2 skipped（environment-pending）；`pytest tools/source_lab/tests/access/test_beckhoff_ads_environment_probe.py -q` -> 0 passed, 1 skipped（environment-pending）；`pytest tools/source_lab/tests/access/test_beckhoff_ads_native_preflight.py -q` -> 2 passed, 1 skipped（environment-pending）；`pytest tools/source_lab/tests/access/test_beckhoff_ads_real_protocol_readback.py -q` -> 0 passed, 4 skipped（environment-pending） | source_lab 现已真实从 shared persistence SCADA sample DB 读取 16 组 protocol-service 并构造 `SimulatedSource/SimulatedPoint`；PostgreSQL 临时样例库也已被 provider 真实消费。Round 22 已实现三类 ADS backend 代码和 contract 测试：in_process（34 passed L2/L3/L4）、beckhoff_dotnet（L2 contract 通过，7 skipped environment-pending）、native_adslib（L2 preflight 通过，1 skipped environment-pending）。但真实 Beckhoff ADS 协议证据（L4+ real protocol）仍未获得——所有 7 个 skipped 均缺 Windows+TwinCAT+ADS Router 或 AdsLib binary。ADS_NOTIFICATION 仍显式 `NOT_IMPLEMENTED`。这仍不等于 shared_source production ADS backend 完成，也不等于 ingest production-ready | Round 23: 解除 environment-pending（至少 beckhoff_dotnet 或 native_adslib 一个通过）；之后单独启动 shared_source ADS backend 设计与实现，不与 source_lab 工具层证据混淆。Round 23 审计发现 2 项 metadata test failure（test_protocol_registry 缺少 beckhoff_ads 条目、test_protocol_production_readiness_gate 中 beckhoff_ads production_client_write 误标为 True而应改为 False）| 2026-06-01 |
| SL-FR-002 | P-FR-001 | 协议 server simulator | FR | 高 | source_lab | L3 | 测试通过（受控L2环境） | `tools/source_lab/protocols/`; `tools/source_lab/native/`; `scripts/source_lab_l2_test_env.sh`; `scripts/run_source_lab_l2_standalone_gate.sh`; `ai_shared/reports/source_lab_goose_sv_l2_env_and_native_subscriber_closure_report.md` | `bash scripts/run_source_lab_l2_standalone_gate.sh` -> GOOSE/SV standalone PASS；`unshare -Urn ... pytest tools/source_lab/tests/access/test_iec61850_goose_sv_streaming_e2e.py -q -rs` -> 6 passed | 宿主机 `lo/eth0` 仍不稳定；GOOSE/SV true PASS 依赖受控 `veth/netns` L2 环境 | 保持宿主机普通接口 failed 历史归档；CI 优先复用受控 L2 环境 | 2026-05-26 |
| SL-FR-003 | P-NFR-001 | probe/profile/capacity 工具 | FR | 高 | source_lab | L4 | 部分实现 | `tools/source_lab/access/`; `tools/source_lab/access/runners/beckhoff_ads_polling.py`; `tools/source_lab/access/runners/registry.py`; `tools/source_lab/protocols/beckhoff_ads/ads_client.py`; `tools/source_lab/protocols/beckhoff_ads/dotnet_virtual_server.py`; `tools/source_lab/tests/access/test_server_simulator_facade_capacity_profile_e2e.py`; `tools/source_lab/tests/access/test_beckhoff_ads_capacity_profile_gate.py`; `tools/source_lab/tests/access/test_beckhoff_ads_environment_probe.py`; `tools/source_lab/tests/access/test_beckhoff_ads_native_preflight.py`; `tools/source_lab/tests/access/test_iec61850_goose_sv_streaming_e2e.py`; `ai_shared/reports/source_lab_goose_sv_l2_env_and_native_subscriber_closure_report.md`; `ai_shared/reports/beckhoff_ads_real_protocol_round22.md` | `pytest tools/source_lab/tests/access/test_beckhoff_ads_capacity_profile_gate.py -q` -> 2 passed；`pytest tools/source_lab/tests/access/test_beckhoff_ads_environment_probe.py -q` -> 0 passed, 1 skipped（environment-pending）；`pytest tools/source_lab/tests/access/test_beckhoff_ads_native_preflight.py -q` -> 2 passed, 1 skipped（environment-pending）；`unshare -Urn ... pytest tools/source_lab/tests/access/test_iec61850_goose_sv_streaming_e2e.py -q -rs` -> 6 passed | ADS polling capacity 已有最小 smoke，且缺失 AdsLib binary 时会通过 preflight 显式降级；GOOSE/SV capacity/profile 仍依赖受控 L2 环境；ADS_NOTIFICATION 尚未进入 profile/streaming ready；ADS 真实环境探测（dotnet/TwinCAT/ADS Router）与 AdsLib native runner 预检代码就绪但 environment-pending；真实 ADS readback 仍未获得任何 L4+ 证据 | 在 Windows+TwinCAT 或 AdsLib binary 就绪后解除 environment-pending；不把 Python in_process tool runner 写成 production client | 2026-06-01 |
| SL-FR-004 | P-NFR-004 | 多协议 native runner 管理 | FR | 高 | source_lab | L3 | 测试通过 | `tools/source_lab/access/runners/native_cmd.py`; `tools/source_lab/access/runners/native_runner_map.py`; `tools/source_lab/access/runners/registry.py`; `tools/source_lab/tests/access/test_native_runners_availability.py`; `tools/source_lab/tests/access/test_native_cmd_timeout.py`; `tools/source_lab/tests/access/test_protocol_production_readiness_gate.py`; `tools/source_lab/access/profile.py` | `pytest tools/source_lab/tests/access/test_native_runners_availability.py -q` -> 17 passed, 2 skipped; `pytest tools/source_lab/tests/access/test_native_cmd_timeout.py -q` -> 3 passed; `pytest tools/source_lab/tests/access/test_protocol_production_readiness_gate.py -q` -> 34 passed | Round 12: `PROTOCOL_CAPABILITIES` 重命名为 `DECLARED_PROTOCOL_CAPABILITIES`（标注 static metadata only），保留向后兼容别名；registry.py mypy 8 errors 清零；runtime readiness API 仍应作为调用方首选 | 继续迁移非 gate 调用方到 runtime readiness API | 2026-05-30 |
| SL-FR-005 | P-FR-001 | 动态 endpoint runtime | FR | 高 | source_lab | L4 | 运行闭环通过 | `tools/source_lab/access/runtime/`; `tools/source_lab/tests/access/test_dynamic_polling_endpoint_adjustment.py`; `tools/source_lab/tests/access/test_dynamic_subscription_endpoint_adjustment.py`; `tools/source_lab/tests/access/test_dynamic_opcua_polling_endpoint_adjustment.py`; `tools/source_lab/tests/access/test_dynamic_opcua_subscription_endpoint_adjustment.py`; `tools/source_lab/tests/access/test_dynamic_iec61850_report_endpoint_adjustment.py`; `tools/source_lab/tests/access/test_dynamic_goose_sv_streaming_endpoint_adjustment.py`; `ai_shared/reports/source_lab_goose_sv_l2_env_and_native_subscriber_closure_report.md` | `pytest tools/source_lab/tests/access/test_dynamic_goose_sv_permission_gate.py -q` -> 2 passed；`pytest tools/source_lab/tests/access/test_source_lab_final_protocol_matrix.py -q` -> 3 passed；`unshare -Urn ... pytest tools/source_lab/tests/access/test_dynamic_goose_sv_streaming_endpoint_adjustment.py -q -rs` -> 7 passed；`unshare -Urn ... pytest tools/source_lab/tests/access -q` -> 734 passed, 3 skipped | GOOSE/SV dynamic true PASS 依赖受控 `veth/netns`；accepted state raw export 仍可能包含连接参数；state store 非加密 | 保持 raw accepted-state 风险边界；将受控 L2 环境作为 streaming dynamic 推荐执行方式 | 2026-05-26 |
| SL-NFR-001 | P-NFR-001 | 真实性与可复现性 | NFR | 高 | source_lab | L3 | 运行闭环通过 | `tools/source_lab/tests/access/test_source_lab_final_protocol_matrix.py`; `tools/source_lab/tests/access/test_dynamic_goose_sv_streaming_endpoint_adjustment.py`; `tools/source_lab/tests/access/test_iec61850_goose_sv_streaming_e2e.py`; `scripts/source_lab_l2_test_env.sh`; `ai_shared/reports/source_lab_goose_sv_l2_env_and_native_subscriber_closure_report.md` | `pytest tools/source_lab/tests/access/test_source_lab_final_protocol_matrix.py -q` -> 3 passed；`unshare -Urn ... pytest tools/source_lab/tests/access/test_iec61850_goose_sv_streaming_e2e.py -q -rs` -> 6 passed；`unshare -Urn ... pytest tools/source_lab/tests/access/test_dynamic_goose_sv_streaming_endpoint_adjustment.py -q -rs` -> 7 passed；`unshare -Urn ... pytest tools/source_lab/tests -q` -> 743 passed, 12 skipped | 宿主机 `lo/eth0` 仍不可作为默认复现环境；Modbus RTU/IEC101 仍为 gateway mode | 将受控 L2 环境脚本纳入 raw-socket 推荐验证路径 | 2026-05-26 |
| SL-NFR-002 | P-NFR-002 | 稳定性与资源清理 | NFR | 高 | source_lab | L3 | 运行闭环通过 | `tools/source_lab/fleet.py`; `tools/source_lab/access/runners/native_process.py`; `tools/source_lab/access/runtime/state_store.py`; `scripts/source_lab_l2_test_env.sh`; `ai_shared/reports/source_lab_goose_sv_l2_env_and_native_subscriber_closure_report.md` | `pytest tools/source_lab/tests/access/test_dynamic_runtime_state_store_integrity.py -q` -> 6 passed；`pytest tools/source_lab/tests/access/test_dynamic_runtime_state_store_retention.py -q` -> 5 passed；`pytest tools/source_lab/tests/access/test_dynamic_runtime_state_store_repair_cli.py -q` -> 3 passed；`unshare -Urn ... pytest tools/source_lab/tests/access -q` -> 734 passed, 3 skipped | state store 仍非加密；raw accepted-state 仍需受控目录 | 保持工具级持久化边界，不扩展为生产 secret storage | 2026-05-26 |
| SL-AR-001 | P-AR-002 | 工具层边界 | AR | 高 | source_lab | L2 | 测试通过 | `src/whale/ingest/`; `tests/unit/test_ingest_no_source_lab_imports.py`; source_lab/server-client-ingest boundary evidence | `pytest tests/unit/test_ingest_no_source_lab_imports.py -q` -> 1 passed; `pytest tests/integration -q` -> 37 passed | 测试可使用 source_lab simulator；生产路径不得引入 | 第3轮复核 ingest import 边界 | 2026-05-26 |
| SL-AR-002 | P-AR-002 | protocols / native / access 分层 | AR | 高 | source_lab | L2 | 测试通过 | `tools/source_lab/protocols/`; `tools/source_lab/native/`; `tools/source_lab/access/`; `test_protocol_directory_structure.py` | `pytest tools/source_lab/tests/access/test_protocol_directory_structure.py -q` -> 26 passed | 无主要差距；旧 `tools/source_lab/opcua` 仍需持续门禁 | 第3轮复核旧路径未回归 | 2026-05-25 |
| SL-TEST-001 | P-NFR-004 | simulator contract 与真实协议测试 | TEST | 高 | source_lab | L3 | 运行闭环通过 | `test_server_simulator_facade_contract.py`; `test_server_simulator_facade_real_protocol_smoke.py`; `test_source_lab_final_protocol_matrix.py`; `test_dynamic_iec61850_report_endpoint_adjustment.py`; `test_dynamic_goose_sv_streaming_endpoint_adjustment.py`; `test_dynamic_goose_sv_permission_gate.py`; `ai_shared/reports/source_lab_goose_sv_l2_env_and_native_subscriber_closure_report.md` | `pytest tools/source_lab/tests/access/test_server_simulator_facade_contract.py -q` -> 137 passed；`pytest tools/source_lab/tests/access/test_source_lab_final_protocol_matrix.py -q` -> 3 passed；`unshare -Urn ... pytest tools/source_lab/tests/access/test_iec61850_goose_sv_streaming_e2e.py -q -rs` -> 6 passed；`unshare -Urn ... pytest tools/source_lab/tests/access/test_dynamic_goose_sv_streaming_endpoint_adjustment.py -q -rs` -> 7 passed | 受控 L2 环境是 GOOSE/SV 真实事件 smoke 的必要前提；宿主机普通接口仍不稳定 | 保留 `lo/eth0` failed 历史诊断，不回写成 pending | 2026-05-26 |
| SL-TEST-002 | P-NFR-001 | capacity/profile E2E | TEST | 高 | source_lab | L4 | 运行闭环通过 | `test_server_simulator_facade_capacity_profile_e2e.py`; `test_iec61850_report_capacity_profile_gate.py`; `test_iec61850_goose_sv_streaming_e2e.py`; `ai_shared/reports/source_lab_goose_sv_l2_env_and_native_subscriber_closure_report.md` | `pytest tools/source_lab/tests/access/test_server_simulator_facade_capacity_profile_e2e.py -q` -> 26 passed, 4 skipped；`pytest tools/source_lab/tests/access/test_iec61850_report_capacity_profile_gate.py -q` -> 13 passed；`unshare -Urn ... pytest tools/source_lab/tests/access/test_iec61850_goose_sv_streaming_e2e.py -q -rs` -> 6 passed；`unshare -Urn ... pytest tools/source_lab/tests/access -q` -> 734 passed, 3 skipped | GOOSE/SV capacity/profile 通过依赖受控 `veth/netns`，宿主机普通接口仍不作为默认通过证据 | 将 raw-socket E2E 与 full access 回归都固定到受控 L2 环境 | 2026-05-26 |

| SL-READY-001 | P-NFR-001/P-AR-002 | source_lab 独立工具部署准入 | READY | 高 | source_lab | L3 | 部分实现 | `ai_shared/reports/source_lab_mypy_phase1_closure_round13.md`; `ai_shared/reports/source_lab_mypy_phase2_closure_round14.md`; `ai_shared/reports/source_lab_tests_mypy_closure_round15.md`; `tools/source_lab/`; native runner 管理；profile/capacity tests；`tools/source_lab/access/profile.py` | Round 15: source_lab 全量 mypy 0 errors / 202 files（cmd/src/tests 全覆盖）——这是 mypy 治理终点；compileall PASS；ruff PASS；import boundary PASS | raw L2 权限边界依旧需要显式环境约束；10 个 source_lab access 测试 environment-failed（native runner 二进制缺失，非代码问题）；source_lab mypy 治理已 closed，但仍有 L5 field readback pending | 补 native runner 二进制构建/部署自动化；补 GOOSE/SV L2 环境权限矩阵固定 | 2026-05-31 |
| SL-READY-002 | P-NFR-005/P-AR-002 | source_lab 权限与运行环境边界 | READY | 高 | source_lab | L3 | 部分实现 | `scripts/source_lab_l2_test_env.sh`; GOOSE/SV L2 tests; dynamic runtime tests | 受控 L2 环境下 GOOSE/SV 证据已归档 | raw socket/root/capability/netns 运行边界需持续显式化；source_lab 不得默认部署到生产控制区 | 补工具运行权限矩阵和清理验证 | 待更新 |
| SL-READY-003 | P-AR-002 | source_lab 证据边界 | READY | 高 | source_lab | L4（PostgreSQL shared persistence 输入基线）+ L4（provider 消费）+ L4（runtime coverage）+ L2 contract（beckhoff_dotnet/native_adslib preflight） | 部分实现 | `tools/source_lab/access/providers/scada_profile.py`; `tools/source_lab/access/providers/simulator.py`; `tools/source_lab/protocols/beckhoff_ads/__init__.py`; `tools/source_lab/protocols/beckhoff_ads/runtime.py`; `tools/source_lab/protocols/beckhoff_ads/simulator.py`; `tools/source_lab/protocols/beckhoff_ads/ads_client.py`; `tools/source_lab/protocols/beckhoff_ads/dotnet_virtual_server.py`; `tools/source_lab/access/runners/beckhoff_ads_polling.py`; `tools/source_lab/tests/access/test_scada_profile_provider.py`; `tools/source_lab/tests/access/test_scada_profile_runtime_coverage.py`; `tools/source_lab/tests/access/test_scada_profile_facade_smoke.py`; `tools/source_lab/tests/access/test_beckhoff_ads_simulator_contract.py`; `tools/source_lab/tests/access/test_beckhoff_ads_client_runner_protocol.py`; `tools/source_lab/tests/access/test_beckhoff_ads_capacity_profile_gate.py`; `tools/source_lab/tests/access/test_beckhoff_ads_dotnet_virtual_server.py`; `tools/source_lab/tests/access/test_beckhoff_ads_environment_probe.py`; `tools/source_lab/tests/access/test_beckhoff_ads_native_preflight.py`; `tools/source_lab/tests/access/test_beckhoff_ads_real_protocol_readback.py`; `tests/integration/test_shared_persistence_sample_data_init.py`; `tests/integration/test_source_lab_scada_profile.py`; `tests/integration/test_source_lab_scada_profile_postgres.py`; `tests/integration/test_source_lab_beckhoff_ads_runtime.py`; `tests/support/scada_sample_db.py`; `tools/source_lab/access/runners/registry.py`; `tools/source_lab/access/profile.py`; `test_protocol_production_readiness_gate.py`; final protocol matrix; `src/whale/shared/persistence/session.py`; `src/whale/shared/persistence/init_db.py`; `src/whale/shared/persistence/template/protocol_param_data.py`; `src/whale/shared/persistence/template/protocol_view_defs.py`; `src/whale/shared/persistence/template/sample_data.py`; `ai_shared/reports/beckhoff_ads_real_protocol_round22.md` | 本轮 `compileall` passed；`ruff` passed；`pytest tests/integration/test_shared_persistence_sample_data_init.py -q` -> 1 passed；`pytest tests/integration/test_source_lab_scada_profile_postgres.py -q` -> 1 passed；`pytest tools/source_lab/tests/access/test_scada_profile_provider.py -q` -> 4 passed；`pytest tools/source_lab/tests/access/test_scada_profile_runtime_coverage.py -q` -> 17 passed；`pytest tools/source_lab/tests/access/test_scada_profile_facade_smoke.py -q` -> 15 passed；`pytest tools/source_lab/tests/access/test_beckhoff_ads_simulator_contract.py -q` -> 4 passed；`pytest tools/source_lab/tests/access/test_beckhoff_ads_client_runner_protocol.py -q` -> 3 passed；`pytest tools/source_lab/tests/access/test_beckhoff_ads_capacity_profile_gate.py -q` -> 2 passed；`pytest tools/source_lab/tests/access/test_beckhoff_ads_dotnet_virtual_server.py -q` -> 1 passed, 2 skipped（environment-pending）；`pytest tools/source_lab/tests/access/test_beckhoff_ads_environment_probe.py -q` -> 0 passed, 1 skipped（environment-pending）；`pytest tools/source_lab/tests/access/test_beckhoff_ads_native_preflight.py -q` -> 2 passed, 1 skipped（environment-pending）；`pytest tools/source_lab/tests/access/test_beckhoff_ads_real_protocol_readback.py -q` -> 0 passed, 4 skipped（environment-pending）；`pytest tests/integration/test_source_lab_scada_profile.py -q` -> 2 passed；`pytest tests/integration/test_source_lab_beckhoff_ads_runtime.py -q` -> 2 passed；`mypy` 对本轮目标范围 passed；import boundary PASS | Round 22 实现了三类 ADS backend 的明确证据边界：（1）`in_process` — 34 passed，仅限 source_lab 工具层；（2）`beckhoff_dotnet` — contract 通过，真实协议 7 skipped environment-pending，需 Windows+TwinCAT+ADS Router；（3）`native_adslib` — preflight 通过，真实协议 1 skipped environment-pending，需 AdsLib binary。所有 7 个 environment-pending 不得写成真实 Beckhoff ADS 协议闭环。shared_source production ADS backend 和 ingest ADS adapter 仍未开始，ADS_NOTIFICATION 仍为 NOT_IMPLEMENTED | Round 23: 准备 Windows+TwinCAT 环境（或编译 AdsLib Linux binary）以解除 environment-pending；至少一个真实 backend 通过后才能启动 shared_source ADS backend 设计；保持三类证据分开追踪。Round 23 审计确认 2 项 metadata test failure（protocol_registry 缺少 beckhoff_ads、production_client_write 应改为 False），均属 Round 22 引入的 metadata 缺陷 | 2026-06-01 |
