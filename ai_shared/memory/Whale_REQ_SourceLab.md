# Whale_REQ_SourceLab

## 一、文件定位

本文件描述 Whale `tools/source_lab` 模块承担的 simulator、probe、profile、capacity、协议验证和本地开发测试需求。

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
| iec104 | 已验证 | 已验证 | NOT_IMPLEMENTED | facade 不支持 | NOT_IMPLEMENTED | 已验证 | 已验证 | 已验证 | 测试通过 |
| iec61850_mms | 已验证 | 已验证 | 已验证 | NOT_IMPLEMENTED | NOT_IMPLEMENTED | 已验证 | 已验证 | 已验证 | 测试通过 |
| iec61850_report | 已验证 | NOT_IMPLEMENTED | NOT_IMPLEMENTED | 已验证 | 已验证 | 已验证 | 已验证 | 已验证 | 测试通过 |
| iec101 | 已验证 | gateway 已验证 | NOT_IMPLEMENTED | facade 不支持 | NOT_IMPLEMENTED | 已验证 | 已验证 | 已验证 | gateway mode |
| modbus_rtu | 已验证 | gateway 已验证 | NOT_IMPLEMENTED | NOT_IMPLEMENTED | NOT_IMPLEMENTED | 已验证 | 已验证 | 已验证 | gateway mode |
| mqtt | 已验证 | NOT_IMPLEMENTED | NOT_IMPLEMENTED | 已验证 | NOT_IMPLEMENTED | 已验证 | 已验证 | 已验证 | 测试通过 |
| http_rest | 已验证 | 已验证 | NOT_IMPLEMENTED | NOT_IMPLEMENTED | NOT_IMPLEMENTED | 已验证 | 已验证 | 已验证 | 测试通过 |
| goose | framework closure | NOT_IMPLEMENTED | NOT_IMPLEMENTED | CI pending | NOT_IMPLEMENTED | 已验证 | CI pending | CI pending | 需 CAP_NET_RAW/root |
| sv | framework closure | NOT_IMPLEMENTED | NOT_IMPLEMENTED | CI pending | NOT_IMPLEMENTED | 已验证 | CI pending | CI pending | 需 CAP_NET_RAW/root |

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

## 八、需求跟踪表

| 编号 | 上承需求 | 标题 | 类型 | 优先级 | 责任模块 | 验证等级 | 实现状态 | 实现证据 | 验收测试 | 差距 | 下一步 | 更新时间 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| SL-FR-001 | P-FR-001 | 统一 ServerSimulatorFacade | FR | 高 | source_lab | L3 | 测试通过 | `tools/source_lab/protocols/common/simulator_facade.py`; `tools/source_lab/protocols/registry.py`; `tools/source_lab/tests/access/test_server_simulator_facade_contract.py` | `pytest tools/source_lab/tests/access/test_server_simulator_facade_contract.py -q` -> 137 passed; `pytest tools/source_lab/tests/access/test_source_lab_final_protocol_matrix.py -q` -> 3 passed | 无主要差距；GOOSE/SV 仍按 CI pending 单独标注 | 第3轮复核最终矩阵无回退 | 2026-05-25 |
| SL-FR-002 | P-FR-001 | 协议 server simulator | FR | 高 | source_lab | L3 | 代码完成待验证 | `tools/source_lab/protocols/`; `tools/source_lab/native/`; `ai_shared/reports/source_lab_round5_5_final_protocol_gate_and_goose_sv_ci_validation_report.md`; 本轮补 native target 构建归档 | `cmake -S tools/source_lab/native -B tools/source_lab/native/build && cmake --build tools/source_lab/native/build --target iec61850_goose_subscriber_runner iec61850_sv_subscriber_runner iec61850_goose_publisher_simulator iec61850_sv_publisher_simulator` -> built; `pytest -k "goose or sv" tools/source_lab/tests/access -q -rs` -> 54 passed, 12 skipped | GOOSE/SV true event/sample 仍需 CAP_NET_RAW/root CI；不得写运行闭环通过 | 保持 CI pending 边界，待有权限 runner 补真 PASS | 2026-05-26 |
| SL-FR-003 | P-NFR-001 | probe/profile/capacity 工具 | FR | 高 | source_lab | L4 | 测试通过 | `tools/source_lab/access/`; `tools/source_lab/tests/access/test_server_simulator_facade_capacity_profile_e2e.py`; Round5-5 final report；本轮 load gate 归档 | `pytest -m load tools/source_lab/tests -q` -> 9 passed, 649 deselected；`pytest -k "goose or sv" tools/source_lab/tests/access -q -rs` -> 54 passed, 12 skipped | GOOSE/SV profile/capacity 仍因 raw socket 权限 skip | 在有权限 runner 上补 GOOSE/SV load 侧归档 | 2026-05-26 |
| SL-FR-004 | P-NFR-004 | 多协议 native runner 管理 | FR | 高 | source_lab | L3 | 测试通过 | `tools/source_lab/access/runners/native_cmd.py`; `tools/source_lab/access/runners/native_runner_map.py`; `tools/source_lab/tests/access/test_native_runners_availability.py` | `pytest tools/source_lab/tests/access/test_native_runners_availability.py -q` -> 17 passed, 2 skipped | 可选库缺失场景仍会 skip；GOOSE/SV 运行依赖 CAP_NET_RAW | 保持 build hint/version gate；CI 补权限验证 | 2026-05-25 |
| SL-NFR-001 | P-NFR-001 | 真实性与可复现性 | NFR | 高 | source_lab | L3 | 部分实现 | `tools/source_lab/tests/access/test_source_lab_final_protocol_matrix.py`; Round5-5 final report；本轮 GOOSE/SV 权限探测、native build 与 load gate 归档 | `pytest -m load tools/source_lab/tests -q` -> 9 passed, 649 deselected；`pytest -k "goose or sv" tools/source_lab/tests/access -q -rs` -> 54 passed, 12 skipped；skip 原因明确为 `raw_socket_permission_missing` | GOOSE/SV CI true PASS 未完成；Modbus RTU/IEC101 为 gateway mode | 维持 simulator closure/production ready 区分，不上调为运行闭环 | 2026-05-26 |
| SL-NFR-002 | P-NFR-002 | 稳定性与资源清理 | NFR | 高 | source_lab | L3 | 测试通过 | `tools/source_lab/fleet.py`; `tools/source_lab/access/runners/native_process.py`; access 全量测试；native target 可重复构建；load gate 归档 | `cmake -S tools/source_lab/native -B tools/source_lab/native/build && cmake --build tools/source_lab/native/build --target iec61850_goose_subscriber_runner iec61850_sv_subscriber_runner iec61850_goose_publisher_simulator iec61850_sv_publisher_simulator` -> built; `pytest -m load tools/source_lab/tests -q` -> 9 passed, 649 deselected | raw socket 权限场景未真跑；GOOSE/SV true PASS 仍 pending | 后续在具备权限与资源的 CI 跑有权限 raw-socket 归档 | 2026-05-26 |
| SL-AR-001 | P-AR-002 | 工具层边界 | AR | 高 | source_lab | L2 | 测试通过 | `ai_shared/adr/ADR-20260523-001-source-lab-server-client-ingest-boundary.md`; `src/whale/ingest/`; `tests/unit/test_ingest_no_source_lab_imports.py` | `pytest tests/unit/test_ingest_no_source_lab_imports.py -q` -> 1 passed; `pytest tests/integration -q` -> 37 passed | 测试可使用 source_lab simulator；生产路径不得引入 | 第3轮复核 ingest import 边界 | 2026-05-26 |
| SL-AR-002 | P-AR-002 | protocols / native / access 分层 | AR | 高 | source_lab | L2 | 测试通过 | `tools/source_lab/protocols/`; `tools/source_lab/native/`; `tools/source_lab/access/`; `test_protocol_directory_structure.py` | `pytest tools/source_lab/tests/access/test_protocol_directory_structure.py -q` -> 26 passed | 无主要差距；旧 `tools/source_lab/opcua` 仍需持续门禁 | 第3轮复核旧路径未回归 | 2026-05-25 |
| SL-TEST-001 | P-NFR-004 | simulator contract 与真实协议测试 | TEST | 高 | source_lab | L3 | 测试通过 | `test_server_simulator_facade_contract.py`; `test_server_simulator_facade_real_protocol_smoke.py`; `test_source_lab_final_protocol_matrix.py` | `pytest tools/source_lab/tests/access/test_server_simulator_facade_contract.py -q` -> 137 passed; `pytest tools/source_lab/tests/access/test_source_lab_final_protocol_matrix.py -q` -> 3 passed | GOOSE/SV 真实事件/采样 smoke 仅条件 skip，不计 passed | 第2/3轮在 CAP_NET_RAW CI 补 GOOSE/SV smoke | 2026-05-25 |
| SL-TEST-002 | P-NFR-001 | capacity/profile E2E | TEST | 高 | source_lab | L4 | 测试通过 | `test_server_simulator_facade_capacity_profile_e2e.py`; Round5-5 final report；本轮 load marker 归档 | `pytest tools/source_lab/tests/access/test_server_simulator_facade_capacity_profile_e2e.py -q` -> 26 passed, 4 skipped；`pytest -m load tools/source_lab/tests -q` -> 9 passed, 649 deselected | GOOSE/SV capacity/profile 仍是 CI pending | 在具备权限的 runner 上补 GOOSE/SV load 归档 | 2026-05-26 |
