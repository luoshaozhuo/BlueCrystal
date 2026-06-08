# Starfish Requirements

> Starfish -- 多协议 server simulator 工具层。承接 Seahorse 导出的 ServerPlan JSON 契约，提供协议 server 模拟运行时，供平台调试、联调和数字孪生前置验证使用。
> 最后更新: 2026-06-07 (Round 21: **Starfish 能力增强阶段总收口** — 第 21 轮文档定版与剩余项清理。**本轮核心动作**：修复 test-validator 识别的 6 处文档与代码不一致（见 §6 一致性扫描）+ 建立最终协议能力矩阵（12 协议 final state）+ 清理已完成但仍 deferred 的旧项（Seahorse flaky、LinkLayer timer skeleton、balanced FCB auto flip、retry ERROR、ShortFloat duck typing、Modbus facade register_encoding 接入、IEC101 C_SE_TA_1/C_SE_TB_1/C_SE_TC_1 均已收口于 Round 19/20）+ 保留真实剩余项（6 类：真实 IEC101 server / 真实串口 / 完整 balanced/unbalanced runtime / GOOSE/SV L2 / Beckhoff_ADS 真实环境 / Modbus 真实设备 / 现场部署）。**测试统计定版**：**1416 stable passed（1215 starfish + 15 architecture + 186 seahorse = 180 stable + 5 新 daily_power 稳定性测试 + 1 原 daily_power_preset）** / **0 failed** / **0 flaky**（test-validator 独立验证连续 12 次 0 flaky；`test_curve_daily_power_preset` **根因已修复**——`src/seahorse/strategies/curve_generation.py` 在 noise 叠加后强制 `min(values) >= floor_ratio * baseline = 0.2 * 1500.0 = 300.0`，连续 10 次 0 flaky，**不**再列入 pre-existing flaky）；**协议能力矩阵 12 协议最终态**（按实现形态分类）：HTTP_REST -> real；MODBUS_TCP -> real + register_encoding typed helper；MODBUS_RTU -> rtu-lightweight + register_encoding typed helper；MQTT -> lightweight real + subscribe；OPC_UA -> native runner real-mode / env-dependent；IEC104 -> native runner real-mode / env-dependent；IEC61850_MMS -> native runner real-mode / env-dependent；IEC61850_Report -> native runner real-mode + ReportQueue / env-dependent；IEC101 -> codec-enhanced-plus + LinkLayer runtime skeleton，非 server；Beckhoff_ADS -> codebase-pending / dependency probe；GOOSE -> environment-pending；SV -> environment-pending。**显式边界声明**（**不得**改写为 true）：`supports_server=false` / `supports_serial_runtime=false` / `supports_write_runtime=false` / `register_encoding_runtime=false`。**已清理 legacy 清单**（Round 19/20 已收口，本轮仅做文档同步）：Seahorse `test_curve_daily_power_preset` flaky（**根因已修复**，floor 钳制 floor_ratio=0.2）；IEC101 LinkLayer timer skeleton（**已实现**——LinkLayerTimerService 抽象 + Default threading.Timer + Fake + 完整 send/receive/on_timeout 状态机）；balanced FCB auto flip（**已实现**——ACK+FCV=1+mode=BALANCED 自动翻；NACK/timeout/FCV disabled/unbalanced 不翻）；retry ERROR（**已实现**——retry_count > max_retries 显式进入 ERROR）；ShortFloat duck typing（**已实现**——int / float / `numbers.Real` / `__float__` 统一入口，**不引入 numpy 硬依赖**）；Modbus facade register_encoding 接入（**已实现**——encode_register_value / decode_register_value / register_encoding_capabilities 三个公共方法真实调用工具）；IEC101 C_SE_TA_1 / C_SE_TB_1 / C_SE_TC_1（**已实现**于 Round 19）。**真实剩余项**（**不**得高估为已实现）：真实 IEC101 server / 真实串口通信 / 完整 balanced/unbalanced runtime / GOOSE/SV L2 环境 / Beckhoff_ADS 真实环境 / Modbus 真实设备验证 / 现场部署。本仓库项目名为 BlueCrystal，**BlueOcean_REQ_*.md 在仓库中不存在**，本轮沿用 BlueCrystal_REQ_*.md 体系（已通过 git mv 从原 Whale_REQ_*.md 改名，保留 git 历史），**不新建 BlueOcean_REQ_*.md**；本轮不创建 ADR（理由：Starfish 能力增强阶段总收口属于文档/状态定版，未引入新接口契约、schema 变化或架构边界变化；可在未来 IEC101 完整 server 立项时一并建档）；20→21 轮总收口完成)

## 1. 模块定位

`Starfish` 是协议仿真与协议验证工具层，与 `Seahorse` 并列。它负责多协议 server simulator、probe、profile、capacity 和 native runner 管理。

Starfish 负责：

```text
OPC UA / Modbus / IEC 101/104 / IEC 61850 / MQTT / HTTP REST / GOOSE / SV / ADS 等协议 simulator
统一 ServerSimulatorFacade
probe / profile / capacity
协议 read/write/subscribe/report 能力验证
native runner 构建、发现、启动、停止和资源清理
为 SharedSource production client、ingest E2E 和 Seahorse 场景提供外部仿真端点
读取 Seahorse 导出的 starfish_server_plan.json 纯 JSON 契约文件
```

Starfish 不负责：

```text
生成全平台 ORM 样例数据
生成完整场站拓扑和业务语义
替代 SharedSource production client
进入 ingest 生产运行路径
替代真实现场设备验证
写生产数据库
调用 whale.ingest / whale.message_pipeline / whale.speed_layer / whale.storage
```

安全边界：

```text
禁止：Starfish -> seahorse（任何 import）
禁止：Starfish -> whale.ingest
禁止：Starfish -> whale.shared.source
允许：Starfish -> PlatformShared
允许：Seahorse -> Starfish（通过纯 JSON 文件 handoff，非运行时 import）
禁止：BlueCrystal ingest production runtime -> Starfish
禁止：SharedSource production client -> Starfish
禁止：Starfish / Seahorse 冒充现场生产环境验证
```

当前能力声明（Round 13 收口时）：

```text
declared capability: JSON 契约加载与 9 项校验（SF-FR-001）
declared capability: in-memory/local stub simulator facade（SF-FR-002，fallback）
declared capability: read initial_values（SF-FR-003）
declared capability: NOT_IMPLEMENTED write/subscribe/report（SF-FR-004）
declared capability: CLI load-server-plan / smoke-server-plan（SF-FR-005）
declared capability: HTTP_REST 真实 server（SF-FR-006，ThreadingHTTPServer, GET /points）
declared capability: MODBUS_TCP 真实 server（SF-FR-007，TCP socket, FC03/FC06, write 为真实 FC06）
declared capability: RuntimeRegistry 5 模式协议 dispatch + native runner dispatch（SF-FR-008，HTTP_REST/MODBUS_TCP/MQTT/OPC_UA/IEC104/IEC61850_MMS/IEC61850_Report -> real，IEC101/MODBUS_RTU/Beckhoff_ADS -> codebase-pending，GOOSE/SV -> environment-pending）
declared capability: smoke-server-plan per-endpoint mode 输出（SF-FR-009）
declared capability: MQTT lightweight JSON-line TCP facade（SF-FR-010，TCP socket server, daemon accept, JSON-line pub）
declared capability: subscribe 语义（SF-FR-011，SubscriptionQueue queue.Queue, MqttFacade）
declared capability: probe 最小工具能力（SF-FR-012，启动-健康-读取探测，PASS/FAIL/NOT_RUN + reason，已扩展至 12 协议）
declared capability: profile 最小工具能力（SF-FR-013，read N 次采样耗时统计，已扩展至 12 协议）
declared capability: capacity 最小工具能力（SF-FR-014，端点/点位/读取容量扫描，已扩展至 12 协议）
declared capability: OPC_UA real mode（SF-FR-015，open62541 C runner 子进程）
declared capability: IEC104 real mode（SF-FR-016，iec104_simulator_server C runner 子进程）
declared capability: dependency probe 与 unavailable 语义（SF-FR-017，二进制探测 + 文件大小 + 可执行权限）
declared capability: IEC61850 MMS real mode（SF-FR-018，iec61850_simulator_server C runner 子进程；read 为内存点位，非真实 MMS 协议帧）
declared capability: IEC61850 Report real mode + ReportQueue event 语义（SF-FR-019，iec61850_report_runner C runner 子进程 + ReportQueue put/get/drain/FIFO；events 来自 Python 侧非子进程）
declared capability: IEC101 codec-skeleton mode（SF-FR-027，TypeId/COT/ASDUHeader/IOA/CA 编解码骨架；非完整 IEC101 server）
declared capability: IEC101 codec-enhanced mode（SF-FR-028，SIQ/QDS 质量描述符 + NVA 归一化值 + M_SP_NA_1/M_DP_NA_1/M_ME_NA_1/C_SC_NA_1 信息对象 + ASDU 信息对象列表 SQ=0/SQ=1 + FT1.2 固定/可变帧 + checksum + 未知 TypeId 安全解码；非完整 IEC101 server）
declared capability: IEC101 codec-enhanced-plus mode（SF-FR-029，**Round 18 扩展**：14 TypeId 矩阵 — 4 不带时标监视 M_SP_NA_1/M_DP_NA_1/M_ME_NA_1/C_SC_NA_1 + 1 不带时标标度化 M_ME_NB_1（Round 18 新增）+ 1 不带时标短浮点 M_ME_NC_1（Round 18 新增）+ 4 不带时标命令 C_SE_NA_1/C_SE_NB_1/C_SE_NC_1（Round 18 新增）+ 5 带时标监视 M_SP_TA_1/M_DP_TA_1/M_ME_TA_1/M_ME_TB_1/M_ME_TC_1；分组：4 不带时标监视 + 1 不带时标标度化 + 1 不带时标短浮点 + 4 不带时标命令 + 5 带时标监视 = 14 个；**C_SE_TA_1 / C_SE_TB_1 / C_SE_TC_1 显式 deferred，Round 19+ 计划项，避免与既有 5 个带时标监视 TypeId CP56Time2a 路径耦合**）+ Round 17 既有：CP56Time2a 7 字节时标 IE（位级 + datetime 转换 + IV/SU/SB 标志）+ ShortFloat IEEE 754 32-bit IE（NaN/Inf 严格拒绝 + 0.0/-0.0/极值边界）+ C_SC_NA_1 QU 字段结构化（CommandPulse 枚举 + SingleCommandQualifier 显式字段 select_execute/qualifier/ql_value/persistent/pulse + 旧位级 roundtrip 兼容）+ 链路层最小状态机骨架扩展（5 态 IDLE/WAIT_ACK/SEND/RECEIVE/ERROR + LinkLayerTimers + t1/t2/t3 常量 + FCB/FCV helper + sequence flip / retry 骨架 + balanced/unbalanced 差异化 skeleton 行为）+ ScaledValue IE（16-bit signed，Round 18 新增）+ QOS 结构化 SetPointQualifier 枚举 + SetPointCommandQualifier（Round 18 新增）；**Iec101Facade.codec_capabilities() 显式 supports_write_runtime=false（C_SE_* command codec 不得被高估为真实写能力，Iec101Facade.write() 仍抛 UnsupportedOperation）+ supports_command_codec=true + supports_scaled_value=true + supports_server=false + supports_serial_runtime=false + supported_measurement_type_ids + supported_command_type_ids + supported_time_tagged_type_ids 分组**；**不是** IEC101 server / 真实串口 / 完整 t1/t2/t3 计时器线程 / 完整 balanced FCB 自动翻转 / 真实 write runtime；Round 16 残留的 health() reason_text codec-enhanced-plus 分支缺失**已修复**）
declared capability: Modbus register_encoding 工具子包（SF-FR-030，**Round 18 新增 + Round 19 facade 接入**）：`src/starfish/protocols/modbus/__init__.py` + `register_encoding.py`；纯 Python CPU 辅助层，5 种 value_type（uint16/int16/uint32/int32/float32）× 4 byte/word 组合（big-endian 16+16 / little-endian 16+16 / byte-swap 16+16 / word-swap 16+16）= 20 组合 + NaN/Inf 拒绝（float32 严格拒绝）+ 越界/长度错误检测；**Round 19 新增**：`modbus_tcp_facade.py` + `modbus_rtu_facade.py` 三个新公共方法 `encode_register_value` / `decode_register_value` / `register_encoding_capabilities`，**真实调用 register_encoding 工具**（非仅 capabilities 文案），facade 接入是纯 CPU 辅助层；**`register_encoding_runtime=false` 显式声明**（facade 接入**不**等于 Modbus 真实设备验证，不得被高估为真实设备验证）；MODBUS_TCP 既有 FC03/FC04/FC06/FC16 + MODBUS_RTU 既有 FC01-06/FC15/FC16 不回退；为可选 CPU 工具层，facade 可独立调用
declared capability: MODBUS_RTU rtu-lightweight PTY-backed real mode（SF-FR-021，ModbusRtuFacade，8 FCs (FC01-06/FC15/FC16) + 4 异常码 (0x01-0x04)/PTY 生命周期，不等同真实串口现场）
declared capability: Beckhoff ADS facade 与 codebase-pending 定版（SF-FR-022，AdsFacade stub，增强探测 dotnet/TwinCAT，无 Python 原生 ADS 实现）
declared capability: GOOSE facade 与 environment-pending 定版（SF-FR-023，GooseFacade stub，L2 veth 网络未就绪）
declared capability: SV facade 与 environment-pending 定版（SF-FR-024，SvFacade stub，L2 veth + PTP 时间同步未就绪）
declared capability: native runner 管理框架（SF-FR-025，NativeRunnerSpec + probe_native_runner + NativeProcessHandle 子进程生命周期管理）
actual runtime availability: HTTP_REST、MODBUS_TCP 和 MQTT 为 real mode（真实 TCP server 进程启动），
  OPC_UA 为 real mode（open62541 C runner 子进程），IEC104 为 real mode（iec104_simulator_server C runner 子进程），
  IEC61850_MMS 为 real mode（iec61850_simulator_server C runner 子进程，27144 bytes），
  IEC61850_Report 为 real mode（iec61850_report_runner C runner 子进程，26568 bytes，含 ReportQueue event 语义）；
  MODBUS_RTU 为 rtu-lightweight mode（PTY-backed，CRC16/FC03/FC06，不等同真实串口现场）；
  MODBUS_TCP write 为真实 FC06 写入且可通过 FC03 回读验证；
  MQTT subscribe 为真实 SubscriptionQueue（queue.Queue），publish 触发队列入队；
	  IEC101 为 codec-enhanced-plus mode（CP56Time2a 7 字节时标 IE + M_SP_TA_1/M_DP_TA_1/M_ME_TA_1 带时标 TypeID + C_SC_NA_1 QU 结构化 + 链路层最小状态机骨架 IDLE/WAIT_ACK/ERROR；非完整 IEC101 server，无真实串口 / 无完整 balanced-unbalanced 状态机 / 无 t1/t2/t3 定时器 / 无 FCB-FCV 翻转 / 无 persistent session）；
  GOOSE/SV 为 environment-pending mode（facade stub 已定版，运行环境未就绪）
NOT_IMPLEMENTED: HTTP_REST write/subscribe；MODBUS_TCP subscribe；MQTT write；
  OpcUaFacade/Iec104Facade/Iec61850MmsFacade/Iec61850ReportFacade write/subscribe；
  Iec101Facade/AdsFacade/GooseFacade/SvFacade write/subscribe/report；
  ModbusRtuFacade subscribe/report
unavailable: 当 C 二进制不存在时，OpcUaFacade/Iec104Facade/Iec61850MmsFacade/Iec61850ReportFacade mode="unavailable" + reason，不等同 PASS
codebase-pending: Beckhoff_ADS — facade stub 已定版 + 增强探针，但无 Python 原生 ADS 实现
environment-pending: GOOSE/SV — facade 已定版（stub），运行环境条件未就绪（L2 veth/PTP），不得写成 PASS
probe/profile/capacity IEC61850: real mode 时 PASS（子进程生命周期正常），unavailable 时 NOT_RUN + reason
report 语义已起步：IEC61850 Report facade 已实现 ReportQueue（put/get/drain/FIFO），report 不再是全 NOT_IMPLEMENTED
native runner 管理框架已建立：NativeRunnerSpec/runner_spec.py、probe_native_runner/runner_probe.py、NativeProcessHandle/process_handle.py
已实现工具层闭环：probe/profile/capacity 为最小工具层闭环（不等同生产容量验收），已扩展至 12 协议（含 5 个 pending 协议 NOT_RUN）
source_lab 清理：tools/source_lab/ 已于 Round 11 整目录物理删除（57755 行代码），所有协议能力由 Starfish 提供
dead path / dead fixture 清理：Round 12 完成 runner_resolution.py dev fallback 路径迁移（tools/source_lab -> src/starfish/native/bin）、conftest.py 死 fixture 删除、scripts/whale_test.sh source_lab 残留清零、全仓 dead import 路径清零（零 import tools.xxx）；12 轮递进建设全部完成
MODBUS_RTU PTY 实现：Round 13 完成 MODBUS_RTU rtu-lightweight PTY-backed real mode（CRC16/FC03/FC06/PTY 生命周期 47 tests）；IEC101/ADS 探针增强（lib60870/PTY/dotnet/TwinCAT 探测）；459 passed + 27 skipped；13 轮递进建设完成
Round 14 功能码扩展 + IEC101 编解码骨架：MODBUS_RTU 功能码从 2 个 (FC03/FC06) 扩展至 8 个 (FC01-06/FC15/FC16) + 异常码从 3 个 (0x01-0x03) 扩展至 4 个 (0x01-0x04)；IEC101 codec-skeleton 实现（TypeId/COT 枚举、ASDUHeader/IOA/CA encode/decode）；76 MODBUS_RTU tests + 30 IEC101 codec tests；736 passed + zero failures；14 轮递进建设完成
```

## 2. 需求编号规则

| 层级 | 前缀 | 示例 |
|---|---|---|
| Starfish Module | SF | SF-FR-001 |

需求类型：

```text
FR     功能需求
NFR    非功能需求
AR     架构约束
TEST   测试与验收需求
```

## 3. 当前阶段定义

Starfish 采用分轮次递进建设：

| Round | 主题 | 范围 |
|---|---|---|
| Round 5 | ServerPlan loader + facade stub + CLI | ServerPlan JSON 加载器（9 项校验 + payload_hash 复算）、ServerSimulatorFacade in-memory stub（start/stop/health/read/load_points/update_values/capabilities）、RuntimeRegistry（create_facades 工厂）、CLI（load-server-plan/smoke-server-plan）、import boundary 6 向验证 |
| Round 6 | 真实协议 server 起步（HTTP_REST + MODBUS_TCP） | HttpRestFacade（ThreadingHTTPServer, GET /points 真实 HTTP 服务端）、ModbusTcpFacade（TCP socket, FC03/FC06 真实 Modbus 帧编码）、RuntimeRegistry 协议 dispatch（real/stub/unavailable 三模式）、CLI smoke-server-plan per-endpoint mode 输出、39 个协议 facade 测试 |
| Round 7+ | 多协议扩展 | OPC_UA/IEC104/IEC101/IEC61850/Beckhoff ADS/GOOSE/SV 等协议真实 server 启动；report 语义（待规划） |
| Round 7 | MQTT lightweight + probe/profile/capacity + subscribe 语义 | MQTT lightweight JSON-line TCP facade（SF-FR-010）、subscribe 语义 SubscriptionQueue（SF-FR-011）、probe/profile/capacity 最小工具层闭环（SF-FR-012/013/014）、CLI 5 子命令、MqttFacade 37 tests + probe/profile/capacity 21 tests、RuntimeRegistry MQTT dispatch（mqtt-lightweight mode）、source_lab MQTT 标记待淘汰、HTTP_REST/MODBUS_TCP 回归无回退 |
| Round 8 | OPC_UA/IEC104 真实 server + dependency probe | OPC_UA real mode open62541 C runner 子进程（SF-FR-015）、IEC104 real mode iec104_simulator_server C runner 子进程（SF-FR-016）、dependency probe 与 unavailable 语义（SF-FR-017）、RuntimeRegistry native runner dispatch（SF-FR-008 更新）、probe/profile/capacity OPC_UA/IEC104 扩展（SF-FR-012/013/014 更新）、58 new tests、source_lab OPC_UA/IEC104 标记待淘汰、HTTP_REST/MODBUS_TCP/MQTT 回归无回退、455 total passed
| Round 9 | IEC61850 MMS/Report 真实 server + report 语义起步 | IEC61850 MMS real mode iec61850_simulator_server C runner 子进程（SF-FR-018）、IEC61850 Report real mode iec61850_report_runner C runner 子进程 + ReportQueue event 语义（SF-FR-019）、probe/profile/capacity IEC61850 扩展（SF-FR-012/013/014 更新）、71 new tests、source_lab IEC61850 MMS/Report 标记待淘汰 GOOSE/SV 保留、HTTP_REST/MODBUS_TCP/MQTT/OPC_UA/IEC104 回归无回退、526 total passed |
| Round 10 | 剩余协议 facade 定版 + native runner 框架 + 最终收口 | 5 个 pending protocol facade 与状态定版（SF-FR-020~024：IEC101/MODBUS_RTU/Beckhoff_ADS codebase-pending，GOOSE/SV environment-pending）、native runner 管理框架（SF-FR-025：NativeRunnerSpec + probe_native_runner + NativeProcessHandle 子进程生命周期管理）、runtime_registry codebase-pending/environment-pending dispatch、probe/profile/capacity 扩展至 12 协议、71 new tests、436 starfish + 181 seahorse + 11 architecture = 628 total passed |
| Round 11 | SourceLab / Tools 物理删除与 Legacy Purge 总收口 | tools/source_lab/ 整目录物理删除（57755 行）、3 个 source_lab shell 脚本删除、tests/support/source_lab_runtime.py 删除、3 个 source_lab 集成测试删除、5 个 Starfish facade C binary 路径迁移至 src/starfish/native/bin/、全仓零 import tools.source_lab、621 passed + 27 skipped |
| Round 12 | Dead Path / Dead Fixture / 过时入口最终清理 | runner_resolution.py `_dev_fallback_candidate()` 和 `is_source_lab_dev_runner_path()` 内部路径改为 `src/starfish/native/bin`；conftest.py 6 个死 fixture（opcua_sim_fleet、opcua_server_runtime 等）删除；scripts/whale_test.sh 无 source_lab 组件残留；全仓 `import tools.xxx` 零结果；全仓零 dead import 路径；629 passed（394 starfish + 181 seahorse + 15 architecture + 31 shared persistence + 6 runner_resolution + 2 ingest boundary）+ 27 skipped（环境 pending，非本轮引入）；validate_shared_source_production_runner.sh ALL VALIDATIONS PASSED；import boundary starfish/seahorse/whale 三方清洁；12 轮递进建设全部完成 |
| Round 14 | MODBUS_RTU FC 扩展 + IEC101 codec-skeleton | MODBUS_RTU 功能码从 FC03/FC06 扩展至 8 个 (FC01-06/FC15/FC16) + 异常码 0x01-0x04；IEC101 codec-skeleton (TypeId/COT 枚举、ASDUHeader/IOA/CA encode/decode)；Iec101Facade mode 从 codebase-pending 升级为 codec-skeleton；RuntimeRegistry 新增 _CODEC_SKELETON_PROTOCOLS；+29 MODBUS_RTU tests (76 total) + 30 IEC101 codec tests；736 passed (540 starfish + 15 architecture + 181 seahorse)；compileall/ruff/mypy 全通过；import boundary 清洁；14 轮递进建设完成 |
| Round 15 | IEC101 codec-enhanced 编解码器增强 | 5 个新 codec 模块（quality / information_elements / information_object / frame / codec）+ SIQ/QDS 质量描述符 + NVA 归一化值 + M_SP_NA_1/M_DP_NA_1/M_ME_NA_1/C_SC_NA_1 信息对象 + ASDU 信息对象列表 SQ=0/SQ=1 编解码 + FT1.2 固定/可变帧 + checksum + 未知 TypeId 安全解码 + 帧长度/校验和不一致检测；Iec101Facade.mode 从 codec-skeleton 升级为 codec-enhanced（带 capabilities 显式 supports_server=false / supports_serial_runtime=false）；+108 IEC101 codec tests (138 total) + 638 starfish total + 15 architecture + 181 seahorse = 838 passed；CP56Time2a 7 字节时标 IE 显式 deferred；third_party 零新增；import boundary 清洁；15 轮递进建设完成 |
| Round 16 | IEC101 codec-enhanced-plus 时标 + 链路层最小状态机骨架 | 2 个新 codec 模块（time.py CP56Time2a 7 字节时标 IE + link_layer.py 链路层最小状态机骨架）+ 1 个新测试文件（test_iec101_link_layer.py 40 tests）；既有测试扩展 test_iec101_information_elements.py +27（CP56Time2a 共 51 tests）、test_iec101_asdu_objects.py +37（带时标 + QU 共 75 tests）；CP56Time2a 7 字节时标 IE 完整实现（位级 + datetime 转换 + IV/SU/SB 标志位）；3 个带时标 TypeID 支持（M_SP_TA_1 / M_DP_TA_1 / M_ME_TA_1，M_ME_TB_1 / M_ME_TC_1 deferred 依赖 ShortFloat 完整实现）；C_SC_NA_1 QU 字段结构化（SingleCommandQualifier dataclass 兼容旧位级 roundtrip）；链路层最小状态机骨架（IDLE/WAIT_ACK/ERROR + LinkControlHelper + feed_frame，**仅 skeleton 非 server**）；Iec101Facade.mode 升级为 codec-enhanced-plus（5 级，新增 supports_link_layer_skeleton=true）；capabilities 显式 supports_server=false / supports_serial_runtime=false / supports_link_layer_skeleton=true / supports_cp56time2a=true / supported_time_tagged_type_ids=M_SP_TA_1,M_DP_TA_1,M_ME_TA_1；+104 IEC101 codec tests (242 total) + 742 starfish total + 15 architecture + 181 seahorse = 938 passed；third_party 零新增；import boundary 清洁；显式风险：Iec101Facade.health() reason_text 分支缺失 codec-enhanced-plus（Round 17 修复项，**不得隐瞒**）；16 轮递进建设完成 |
| Round 17 | IEC101 codec-enhanced-plus 一次性收口（4 类 Round 16 残留 deferred 项全部修复/实现） | `information_elements.py` 扩展 ShortFloat IEEE 754 32-bit IE（NaN/Inf 严格拒绝 + 0.0/-0.0/极值边界）+ `M_ME_TB_1_Object`（TypeId=11，10 字节 = SVA(4)+QDS(1)+CP56Time2a(7)）+ `M_ME_TC_1_Object`（TypeId=13，12 字节 = ShortFloat(4)+QDS(1)+CP56Time2a(7)）；`information_object.py` 扩展 `C_SC_NA_1_QU_QUALIFIER` 枚举 + `CommandPulse` 枚举 + `SingleCommandQualifier` 显式字段（select_execute/qualifier/ql_value/persistent/pulse）+ 旧位级 roundtrip 兼容；`link_layer.py` 扩展 `LinkState` 增 SEND/RECEIVE 中间态（5 态） + `LinkLayerTimers`（t1/t2/t3 常量）+ `LinkControlHelper` FCB/FCV helper + `LinkLayer` sequence flip / retry 骨架 + balanced/unbalanced 差异化 skeleton 行为；`Iec101Facade.health()` reason_text 显式 codec-enhanced-plus 分支（**移除 Round 16 残留风险**）+ `codec_enhanced_plus_ready` 诊断字段；`Iec101Facade.codec_capabilities()` 显式 `codec_mode=codec-enhanced-plus` + `supported_type_ids` 增 M_ME_TB_1/M_ME_TC_1（共 7+ TypeId）+ `supports_short_float=true` + `supports_link_layer_skeleton=true` + `supports_server=false` + `supports_serial_runtime=false`；既有测试扩展 test_iec101_information_elements.py +（ShortFloat IEEE 754 + M_ME_TB_1/M_ME_TC_1）、test_iec101_asdu_objects.py +（带时标短浮点 + QU 显式化）、test_iec101_link_layer.py +（FCB/FCV/timers/balanced-unbalanced）；+137 IEC101 codec tests (379 total) + 848 starfish total + 15 architecture + 181 seahorse = 1044 passed；Round 16 残留的 health() reason_text 风险**已修复**（**不得继续列为风险**）；third_party 零新增；import boundary 清洁；17 轮递进建设完成 |
| Round 13 | IEC101/MODBUS_RTU/Beckhoff_ADS 能力增强 | MODBUS_RTU rtu-lightweight PTY-backed real mode 实现（CRC16 标准算法 0xA001 5 个已知向量、FC03/FC06 帧编解码、pty.openpty() PTY 生命周期）；IEC101/ADS facade enhanced probe（lib60870 存在性/PTY 可用性、dotnet/TwinCAT 环境检测）；RuntimeRegistry MODBUS_RTU 动态 dispatch（PTY 可用→rtu-lightweight，不可用→codebase-pending）；47 new tests (test_modbus_rtu_facade.py)；459 passed (444 starfish + 15 architecture) + 27 skipped (环境 pending) + 181 seahorse passed；compileall/ruff/mypy 全通过；import boundary 清洁；13 轮递进建设完成 |
| Round 18 | IEC101 剩余 TypeID + Modbus 寄存器编码增强 | IEC101 codec-enhanced-plus **14 TypeId 矩阵扩展（4 不带时标监视 + 1 不带时标标度化 M_ME_NB_1 + 1 不带时标短浮点 M_ME_NC_1 + 4 不带时标命令 C_SE_NA_1/C_SE_NB_1/C_SE_NC_1 + 5 带时标监视 = 14 个；C_SE_TA_1/C_SE_TB_1/C_SE_TC_1 显式 deferred Round 19+，避免与既有 5 个带时标监视 TypeId CP56Time2a 路径耦合）** + ScaledValue IE（16-bit signed，Round 18 新增）+ QOS 结构化（SetPointQualifier 枚举 QOS 0-7 标准子字段 + SetPointCommandQualifier dataclass 显式 select/qualifier/ql_value，Round 18 新增）+ `Iec101Facade.codec_capabilities()` 新增 supports_command_codec=true / supports_scaled_value=true / supports_write_runtime=false（**C_SE_* command codec 不得被高估为真实写能力，Iec101Facade.write() 仍抛 UnsupportedOperation**）+ supported_measurement_type_ids / supported_command_type_ids / supported_time_tagged_type_ids 分组 + **Modbus register_encoding 工具子包（SF-FR-030，Round 18 新增）**：`src/starfish/protocols/modbus/__init__.py` + `register_encoding.py`，5 value_type（uint16/int16/uint32/int32/float32）× 4 byte_order 组合（big-big/little-little/big-little/little-big）= 20 组合 + NaN/Inf 拒绝 + 越界/长度错误检测；纯 Python CPU 辅助层，**不是** Modbus 真实设备验证，**Modbus facade（modbus_tcp_facade.py / modbus_rtu_facade.py）未重构**（避免破坏 Round 13-14 baseline）；既有测试文件扩展 test_iec101_information_elements.py +（ScaledValue IE）、test_iec101_asdu_objects.py +（5 新信息对象 + QOS）、test_iec101_codec.py +（capabilities 显式声明断言）；新增 test_modbus_register_encoding.py（164 tests）；535 IEC101 codec tests + 1091 starfish total + 15 architecture + 181 seahorse = 1287 passed（+243 净增 vs Round 17 1044）；Round 17 baseline 379 IEC101 codec tests 不回退；third_party 零新增；import boundary 清洁；Iec101Facade.write/subscribe/report 仍为 UnsupportedOperation；IEC101 不是 server / 真实串口 / 真实 write runtime / 真实设备验证；18 轮递进建设完成 |
| Round 19 | IEC101 带时标设定值命令 + Modbus Facade 接入寄存器编码工具 | IEC101 codec-enhanced-plus **14 → 17 TypeId 矩阵扩展**（**3 新 C_SE_TA_1 / C_SE_TB_1 / C_SE_TC_1 带时标命令** + 既有 14 TypeId 维持；以 capability 实际值 17 为准，**严禁硬写 13/14/15/18**）：C_SE_TA_1（TypeId=58，5+7=12 字节 = NVA+QOS+CP56Time2a）+ C_SE_TB_1（TypeId=59，5+7=12 字节 = SVA+QOS+CP56Time2a）+ C_SE_TC_1（TypeId=60，5+7=14 字节 = ShortFloat+QOS+CP56Time2a）；`Iec101Facade.codec_capabilities()` 显式 `supported_command_type_ids` 从 4 升级至 7（**C_SC_NA_1 + C_SE_NA_1 + C_SE_NB_1 + C_SE_NC_1 + C_SE_TA_1 + C_SE_TB_1 + C_SE_TC_1，以 capability 实际值 7 为准**）+ `supported_time_tagged_type_ids` 从 5 升级至 8（5 既有 + 3 新 C_SE_TA_1/TB_1/TC_1）+ 新增 `supported_time_tagged_command_type_ids=C_SE_TA_1,C_SE_TB_1,C_SE_TC_1`（**以 capability 实际值 3 为准**）+ `supports_time_tagged_command_codec=true` + 维持 `supports_write_runtime=false`（**Iec101Facade.write/subscribe/report 仍抛 UnsupportedOperation；C_SE_T* command codec 不得被高估为真实写能力**）+ `probe_iec101_codec_enhanced_plus()` 验证 17 TypeId 矩阵；`Iec101Facade.health()` reason_text 同步 codec-enhanced-plus 17 TypeId 分支 + `codec_enhanced_plus_ready` 诊断字段同步；**Modbus TCP / RTU facade 接入 register_encoding 工具**（`modbus_tcp_facade.py` + `modbus_rtu_facade.py` 三个新公共方法 `encode_register_value` / `decode_register_value` / `register_encoding_capabilities`，**真实调用 register_encoding 工具，非仅 capabilities 文案**），5 value_type × 4 byte/word 组合 = 20 组合 + NaN/Inf 拒绝 + 越界/长度错误检测；MODBUS_TCP 既有 FC03/FC04/FC06/FC16 + MODBUS_RTU 既有 FC01-06/FC15/FC16 不回退；**`register_encoding_runtime=false` 显式声明**：facade 接入是纯 CPU 辅助层，**不是** Modbus 真实设备验证，不得被高估为真实设备验证；既有 14 TypeId 维持不变；既有 `protocols/modbus/register_encoding.py` 不修改，仅 facade 接入；既有测试文件扩展 test_iec101_asdu_objects.py +6 个 C_SE_T* test classes（test_c_se_ta_1_roundtrip + test_c_se_tb_1_roundtrip + test_c_se_tc_1_roundtrip + test_c_se_t_a_byte_layout + test_c_se_t_b_byte_layout + test_c_se_t_c_byte_layout 验证 12/12/14 字节布局与 COT 字段）+ test_iec101_codec.py +TestIec101CodecRound19 capabilities 17/7/3 数字断言 + test_modbus_rtu_facade.py +encode_register_value/decode_register_value/register_encoding_capabilities 三方法 + test_protocol_facade.py +Modbus TCP/RTU facade register_encoding 集成测试；580+ IEC101 codec tests + 1144 starfish total + 15 architecture + 181 seahorse（**180 stable + 1 pre-existing flaky** test_curve_daily_power_preset）= **1339 stable passed（+52 net vs Round 18 1287）**，0 failed；seahorse `test_curve_daily_power_preset` Round 19 阶段为偶发 min(values)=90.952 < 100 阈值（**Round 20 根因已修复**，floor 钳制 floor_ratio=0.2，min(values) >= 300.0，连续 10+ 次 0 flaky；本轮**不**再列为 pre-existing flaky）；third_party 零新增；import boundary 清洁；Iec101Facade.write/subscribe/report 仍为 UnsupportedOperation；Modbus facade 接入 register_encoding_runtime=false；IEC101 不是 server / 真实串口 / 真实 write runtime / 真实设备验证；19 轮递进建设完成 |
| Round 20 | Seahorse Flaky 根因修复 + IEC101 LinkLayer Runtime Skeleton 增强 + ShortFloat 兼容扩展 | **Seahorse 根因修复**（`src/seahorse/strategies/curve_generation.py`）：`daily_power_curve` 在 noise 叠加后强制 `min(values) >= floor_ratio * baseline`（floor_ratio=0.2, baseline=1500.0，**min(values) >= 300.0**），从根因消除 `min(values)=90.952 < 100 阈值` 的统计噪声；**未使用 skip/xfail/删除测试/扩大阈值**；`tests/unit/seahorse/test_strategies.py` 连续 10 次运行 0 flaky（独立 Python 20 次复现 min(values)=300.00，test-validator 独立验证连续 **12 次 0 flaky**）；新增 5 个 daily_power 稳定性测试（`test_daily_power_preset_min_floor_enforced` / `test_daily_power_preset_cross_run_consistency` / `test_daily_power_preset_high_noise_compatible` / `test_other_curves_have_no_floor_behavior` / `test_daily_power_preset_stable_5x_runs`）；**IEC101 LinkLayer runtime skeleton 增强**（`src/starfish/protocols/iec101/link_layer.py`）：`LinkLayerTimerService` 抽象 + `DefaultLinkLayerTimerService`（threading.Timer 实现）+ `FakeLinkLayerTimerService`（无 wall-clock）三实现；`start_timer` / `cancel_timer` / `cancel_all` / `on_timeout` API；**send/receive/on_timeout 完整状态机**（send_user_data -> WAIT_ACK / receive_ack -> IDLE / receive_nack -> bump_retry/ERROR / on_timeout -> bump_retry/ERROR）；**balanced FCB auto flip**（ACK + FCV=1 + mode=BALANCED 自动翻 send_sequence；NACK/timeout/FCV disabled/unbalanced **不翻**）；`retry_count > max_retries` 进入 `ERROR` 状态；**默认 `enable_timers=False`**（保持 Round 17 行为完全一致；生产需显式 `enable_timers=True` + 注入 TimerService）；**ShortFloat 兼容扩展**（`src/starfish/protocols/iec101/information_elements.py`）：`encode_short_float` 接受 int / float / `numbers.Real` / `__float__` duck typing 统一入口；NaN/Inf **仍严格拒绝**（`ShortFloatValueError`）；**不引入 numpy 硬依赖**（仅 `numbers` stdlib + duck typing 探测）；`Iec101Facade.codec_capabilities()` **新增 3 个 capabilities**：`supports_link_layer_timers=true` / `supports_balanced_fcb_auto_flip=true` / `supports_retry_skeleton=true`（**3 新增 + 3 维持** supports_server=false / supports_serial_runtime=false / supports_write_runtime=false）；`Iec101Facade.health()` reason_text 同步 codec-enhanced-plus + LinkLayer runtime skeleton 分支；新增测试：`tests/unit/starfish/test_iec101_link_layer.py` +8 个 test classes（LinkLayerTimerService 抽象 + Default + Fake + balanced FCB auto flip + retry ERROR + sequence 状态机）/ `tests/unit/starfish/test_iec101_information_elements.py` +TestShortFloatRound20Compat（int / Decimal / Fraction / `__float__` duck typing）/ `tests/unit/starfish/test_iec101_codec.py` +TestIec101CodecRound20（3 新 capabilities 数字断言）/ `tests/unit/starfish/test_probe_profile_capacity.py` +TestIec101Round20Capabilities（codec_capabilities 显式声明）；600+ IEC101 codec tests + 1215 starfish total + 15 architecture + 186 seahorse（**180 stable + 5 新 daily_power 稳定性测试 + 1 原 daily_power_preset**）= **1416 stable passed（+77 net 增量 vs Round 19 1339）**，0 failed；**明确不是** IEC101 server / 真实串口 / 真实 runtime / 真实设备验证（`supports_server=false` / `supports_serial_runtime=false` 维持 + 真实 socket/pty/serial 0 命中）；**默认 `enable_timers=False`**（保持 Round 17 行为完全一致）；probe/profile/capacity 对 IEC101 仍 NOT_RUN/CODEC_ONLY；third_party 零新增；import boundary 清洁；本仓库项目名为 BlueCrystal，**BlueOcean_REQ_*.md 在仓库中不存在**，本轮沿用 BlueCrystal_REQ_*.md 体系（已通过 git mv 从原 Whale_REQ_*.md 改名，保留 git 历史），**不新建 BlueOcean_REQ_*.md**；本轮不创建 ADR（理由：codec/skeleton/Seahorse 范围内增量演进，未引入新接口契约、schema 变化或架构边界变化，与 Round 15-19 同口径）；20 轮递进建设完成 |

## 4. 需求功能描述

### SF-FR-001 ServerPlan JSON loader

Starfish 提供 `load_server_plan` 函数，读取 Seahorse 导出的 `starfish_server_plan.json` 纯 JSON 文件，执行结构校验、字段完整性检查和 payload_hash 一致性验证，构建 `StarfishServerPlan` 内存模型。

输入：文件路径（str | Path），JSON 文件 UTF-8。

校验项（9 项）：

1. **必填字段存在性**：schema_version / scenario_id / synthetic / endpoints / points / capabilities / initial_values / payload_hash 必须存在。
2. **schema_version 匹配**：必须等于 `1.0.0`，不匹配时警告。
3. **scenario_id 存在性**：必须非空。
4. **synthetic 标识**：必须为布尔类型，False 时警告。
5. **endpoints 结构**：必须为非空 list，每个元素必须为 dict 且有 endpoint_id 和 protocol。
6. **points 结构**：必须为非空 list，每个元素必须为 dict 且有 point_id。
7. **capabilities 类型**：必须为 list。
8. **initial_values 类型**：必须为 dict。
9. **payload_hash 复算**：重新计算 payload_hash（排除 generated_at 和 payload_hash 自身），与存储值比较，不匹配时报错。存储值为空时仅警告。

输出：`LoadResult`（包含解析后的 `StarfishServerPlan` 或 None、`ValidationResult` 校验明细、`file_path`）。

边界错误：文件不存在抛出 `FileNotFoundError`；JSON 解析失败抛出 `json.JSONDecodeError`；顶层非 dict 抛出 `ValueError`。

安全边界：不得 import seahorse；不得 import whale.ingest / whale.shared.source；文件 I/O 仅读取。

### SF-FR-002 ServerSimulatorFacade 最小工具层生命周期

Starfish 提供 `ServerSimulatorFacade` 类，实现协议 server 模拟的最小门面，用于验证 ServerPlan 加载、点位读取和基本健康检查。

当前为 in-memory stub 实现，不启动真实协议 server 进程。

已实现方法：

- `start()` -- 启动门面，设置 runtime 状态为 started，记录启动时间。幂等安全。
- `stop()` -- 停止门面，设置 runtime 状态为 stopped。不删除已加载数据。幂等安全。
- `health() -> dict` -- 返回可观测健康状态（status/plan_loaded/point_count/endpoint_count/capabilities/started_at/synthetic）。
- `load_points(plan)` -- 从 StarfishServerPlan 加载点位定义和 initial_values 到内存存储。
- `read(point_ids=None) -> dict` -- 读取当前点位值（无参数时返回全部）。
- `update_values(values)` -- 批量更新点位值到内存存储。
- `capabilities() -> list[str]` -- 返回已加载 plan 的能力声明列表。

NOT_IMPLEMENTED 方法（见 SF-FR-004）：

- `write(point_id, value)` -- 抛出 UnsupportedOperation。
- `subscribe(point_ids)` -- 抛出 UnsupportedOperation。
- `report()` -- 抛出 UnsupportedOperation。

安全边界：不得 import seahorse / whale.ingest / whale.shared.source；不得伪装真实协议 server 已完成。

### SF-FR-003 read initial_values

`load_points(plan)` 从 `plan.initial_values` 填充内存存储，`read()` 可读取这些初始值。

行为：

- `load_points` 使用 `dict(plan.initial_values)` 复制 initial_values 到内存。
- 已存在的值被覆盖（重新 load 场景）。
- `read()` 无参数返回全部已加载点位值。
- 指定 point_ids 时，不存在的点位返回 `None`。
- empty plan（无 initial_values）时，read() 返回空 dict。

不负责：从真实协议 server 同步初始值；初始值的业务正确性校验。

### SF-FR-004 unsupported write/subscribe/report 返回 NOT_IMPLEMENTED

当前未实现的方法必须明确抛出 `UnsupportedOperation` 异常，不得假装操作已完成。

方法：

- `write(point_id, value)` -- `UnsupportedOperation("write", "ServerSimulatorFacade.write 尚未实现，...")`
- `subscribe(point_ids)` -- `UnsupportedOperation("subscribe", "ServerSimulatorFacade.subscribe 尚未实现，...")`
- `report()` -- `UnsupportedOperation("report", "ServerSimulatorFacade.report 尚未实现，...")`

`UnsupportedOperation` 为自定义异常类，构造参数 `(operation: str, reason: str = "")`，异常消息格式为 `"NOT_IMPLEMENTED: {operation} — {reason}"`，中文错误信息。

行为：这些方法不得返回正常值、不得写日志伪装成功、不得静默吞操作。

### SF-FR-005 CLI load-server-plan / smoke-server-plan

Starfish 提供两个 CLI 子命令（`python -m starfish`）：

**load-server-plan**：从 JSON 文件加载并校验 ServerPlan 契约。

- `--input`（必填）：`starfish_server_plan.json` 文件路径。
- 行为：加载文件、执行 9 项校验、输出详细报告（errors/warnings/passed_checks）。
- 校验通过时输出 scenario_id、endpoints 数量、points 数量、capabilities、synthetic。
- 校验失败时返回非零退出码。

**smoke-server-plan**：加载 ServerPlan 并执行最简 smoke 验证。

- `--input`（必填）：`starfish_server_plan.json` 文件路径。
- 行为：加载文件 -> 校验通过 -> 创建 facade -> load_points -> health -> start -> read initial_values -> capabilities -> NOT_IMPLEMENTED 三项验证 -> stop。
- 不启动真实协议 server 进程。
- 校验失败返回非零；smoke 步骤中任何一步失败返回非零。

安全边界：不连接生产数据库；不调用 whale.ingest / seahorse；不启动真实协议 server；仅操作本地文件系统（读）。

### SF-FR-006 HTTP_REST 真实 server 生命周期

Starfish 提供 `HttpRestFacade`，使用 Python 标准库 `http.server.ThreadingHTTPServer` 启动真实 HTTP REST 协议服务端，监听指定 host:port。

URL 端点：

- `GET /points` -- 返回当前内存点位值的 JSON 对象，格式 `{"point_id": value, ...}`。
- 其他路径返回 HTTP 404。

已实现方法：

- `start()` -- 启动 ThreadingHTTPServer（daemon 线程 serve_forever）。已在运行时抛 `RuntimeError`。幂等安全。
- `stop()` -- shutdown 并 server_close，join 线程。幂等安全。
- `health() -> dict` -- TCP connect 探测确认端口可达。返回 status/running/plan_loaded/point_count/endpoint_count。
- `load_points(plan)` -- 从 StarfishServerPlan 加载点位定义和 initial_values。
- `read(point_ids=None) -> dict` -- 从内存读取点位值（与 `GET /points` 语义一致）。
- `update_values(values)` -- 批量更新点位值到内存。
- `capabilities() -> list[str]` -- 返回 plan 能力声明列表。

NOT_IMPLEMENTED：

- `write()` -- 抛出 `UnsupportedOperation("write", ...)`（HTTP REST server 仅支持 GET 读取）。
- `subscribe()` -- 抛出 `UnsupportedOperation("subscribe", ...)`。
- `report()` -- 抛出 `UnsupportedOperation("report", ...)`。

协议特征：零外部二进制依赖（纯 Python 标准库）；可在单元测试中通过 localhost 动态端口稳定运行。

安全边界：不得 import seahorse / whale.ingest / whale.shared.source；所有数据标注 synthetic。

### SF-FR-007 MODBUS_TCP 真实 server 生命周期

Starfish 提供 `ModbusTcpFacade`，使用 Python 标准库 `socket` 启动真实 Modbus TCP 服务端，监听指定 host:port，处理 Modbus 客户端请求。

已实现功能码：

- **FC03（Read Holding Registers）**：客户端读取多个保持寄存器，返回当前点位值的 Modbus 帧编码响应。每点位占 1 个寄存器（16-bit 无符号整数）。
- **FC06（Write Single Register）**：客户端写入单个寄存器，写入成功后内部点位值同步更新，可通过 FC03 回读验证。

点位到寄存器地址映射：将 `plan.initial_values` 的 key 按字典序排序后，按索引分配寄存器地址（0-based）。映射在 `load_points` 时确定，start/stop 不影响。

已实现方法：

- `start()` -- 创建 TCP socket，bind 并 listen，daemon 线程 accept 循环处理客户端连接（每连接独立线程）。已在运行时抛 `RuntimeError`。幂等安全。
- `stop()` -- 关闭 server socket，join 线程。幂等安全。
- `health() -> dict` -- TCP connect 探测确认端口可达。
- `load_points(plan)` -- 加载点位定义、initial_values，建立 point_id -> register 映射。
- `read(point_ids=None) -> dict` -- 从内存读取点位值。
- `write(point_id, value)` -- 真实写入内存点位值（与 FC06 写入等价）。
- `update_values(values)` -- 批量更新点位值到内存。
- `capabilities() -> list[str]` -- 返回 plan 能力声明列表。

NOT_IMPLEMENTED：

- `subscribe()` -- 抛出 `UnsupportedOperation("subscribe", ...)`。
- `report()` -- 抛出 `UnsupportedOperation("report", ...)`。

当前限制：未实现 Modbus RTU 串行通信；未实现异常码完整矩阵；未实现浮点/32-bit 寄存器编解码；未实现多单元 ID 支持。

协议特征：零外部二进制依赖（纯 Python 标准库）；可在单元测试中通过 localhost 动态端口稳定运行。

安全边界：不得 import seahorse / whale.ingest / whale.shared.source；所有数据标注 synthetic。

### SF-FR-008 RuntimeRegistry 协议 dispatch（real/stub/unavailable 三模式 + native runner dispatch）

`RuntimeRegistry.create_facade_for_endpoint()` 根据 `endpoint.protocol` 分发到对应的 facade 实现。

dispatch 规则：

- `HTTP_REST` -> `HttpRestFacade`（mode="real"，真实 ThreadingHTTPServer）
- `MODBUS_TCP` -> `ModbusTcpFacade`（mode="real"，真实 TCP socket server）
- `MQTT` -> `MqttFacade`（mode="mqtt-lightweight"，轻量 JSON-line TCP server）
- `OPC_UA` -> `OpcUaFacade`（mode="real"，open62541 C runner 子进程；二进制不存在时 mode="unavailable" + reason）
- `IEC104` -> `Iec104Facade`（mode="real"，iec104_simulator_server C runner 子进程；二进制不存在时 mode="unavailable" + reason）
- 其他协议 -> `ServerSimulatorFacade`（mode="stub"，in-memory fallback）

native runner dispatch：OpcUaFacade 和 Iec104Facade 内部经 `_NATIVE_RUNNER_PROTOCOLS` 表 dispatch 到对应 C 子进程。dependency probe 检测二进制存在性（stat + 文件大小 + 可执行权限），二进制存在且可执行时 mode="real"，否则 mode="unavailable" + reason（如 "open62541 binary not found" 或 "iec104_simulator_server binary too small (< 1024 bytes)"）。

数据结构：

- `FacadeEntry`：包含 endpoint、facade 实例、available（bool）、reason（str）、mode（"real"/"stub"/"mqtt-lightweight"/"unavailable"）。
- `RuntimeRegistry`：管理一个 ServerPlan 对应的全部 facade，提供 `start_all()`、`stop_all()`、`health_all()` 统一入口。

`get_supported_protocols()` 返回已实现真实 server 的协议列表（当前 `["HTTP_REST", "MODBUS_TCP", "MQTT", "OPC_UA", "IEC104"]`）。

`create_facades(plan)` 为 plan 中所有 endpoint 创建 facade 并返回完整 RuntimeRegistry。

协议名归一化：大小写不敏感，连字符转换为下划线。

安全边界：不得 import seahorse；不得 import whale.ingest / whale.shared.source；不得调用 whale shared_source production client。

### SF-FR-009 smoke-server-plan per-endpoint mode 输出

`smoke-server-plan` CLI 子命令增强为按 endpoint 输出 facade 工厂 dispatch 结果和逐 endpoint mode 标注。

输出内容（每个 endpoint）：

- `endpoint_id` -- 端点标识。
- `protocol` -- 协议名。
- `point_count` -- 已加载点位数量。
- `capabilities` -- 端点能力声明。
- `mode` -- 运行模式（"real"/"stub"/"unavailable"）。
- `reason` -- stub mode 时说明原因。

stub mode 时，额外验证 NOT_IMPLEMENTED write/subscribe/report 三项。

smoke 流程不变：load -> 校验 -> create_facades -> 逐 endpoint smoke（health/start/read/capabilities/NOT_IMPLEMENTED/stop）-> 聚合 status。

安全边界：不连接生产数据库；不调用 whale.ingest / seahorse；仅操作本地文件系统。

### SF-FR-010 MQTT lightweight JSON-line TCP facade

Starfish 提供 `MqttFacade`，使用 Python 标准库 `socket` 启动轻型 MQTT 风格 TCP 服务端，监听指定 host:port。**这是 lightweight JSON-line TCP facade，不是完整 MQTT broker。**不实现 MQTT CONNECT/CONNACK、QoS、topic 订阅树、retained message、will message、session 等标准 MQTT 协议特性。

`MqttFacade` 使用 TCP socket bind/listen/accept 并 daemon 线程处理客户端连接。通信协议为 JSON-line：客户端每行发送一个 JSON 对象，server 每行回复一个 JSON 对象。

已实现方法：

- `start()` -- 创建 TCP socket，bind 并 listen，daemon 线程 accept 循环处理客户端连接（每连接独立线程）。已在运行时抛 `RuntimeError`。幂等安全。使用自动分配端口（port=0）。
- `stop()` -- 关闭 server socket，join 线程。幂等安全。
- `health() -> dict` -- TCP connect 探测确认端口可达。
- `load_points(plan)` -- 从 StarfishServerPlan 加载点位定义和 initial_values。
- `read(point_ids=None) -> dict` -- 从内存读取点位值。
- `update_values(values)` -- 批量更新点位值到内存，并通过 subscribe 队列通知订阅者。
- `capabilities() -> list[str]` -- 返回已加载 plan 的能力声明列表。
- `subscribe(point_ids=None) -> SubscriptionQueue` -- 返回 `SubscriptionQueue`（`queue.Queue` 封装），订阅指定点位或全部点位的值更新。每次 `update_values` 或 TCP publish 时通知所有活跃 subscriber。`load_points` 重新加载时清空旧订阅队列。
- `protocol` 属性返回 `"MQTT"`。
- `mode` 属性返回 `"mqtt-lightweight"`。

`SubscriptionQueue` 封装 `queue.Queue`，提供 `get(timeout=None)`（阻塞等待）和 `get_nowait()`（非阻塞取队首值或返回 None）。

NOT_IMPLEMENTED：

- `write()` -- 抛出 `UnsupportedOperation("write", ...)`。
- `report()` -- 抛出 `UnsupportedOperation("report", ...)`。

TCP 协议操作语义：JSON-line read/publish 操作通过 socket 客户端发送/接收 JSON 对象。

协议特征：零外部二进制依赖（纯 Python 标准库）。不等同于完整 MQTT broker。可在单元测试中通过 localhost 动态端口稳定运行。

安全边界：不得 import seahorse / whale.ingest / whale.shared.source；所有数据标注 synthetic。

### SF-FR-011 subscribe 语义 — SubscriptionQueue

`MqttFacade.subscribe(point_ids=None)` 返回 `SubscriptionQueue` 实例（封装 `queue.Queue`），支持真实订阅通知语义。

行为：

- `subscribe()` 无参数时订阅所有已加载点位。
- `subscribe(point_ids_list)` 订阅指定点位集合。
- `update_values(values)` 后，所有匹配的 subscriber 队列收到通知（包含 `{point_id: new_value}` 字典）。
- TCP publish（客户端通过 socket 发送 JSON publish）触发 `update_values`，从而通知所有 subscriber。
- `load_points(plan)` 重新加载时清空所有已有订阅队列引用（旧 subscriber 不会再收到通知）。
- 多个 subscriber 可同时订阅同一点位，各自独立接收通知。
- `SubscriptionQueue.get(timeout=N)` 阻塞等待最多 N 秒；`get_nowait()` 非阻塞，队列空时返回 None。

安全边界：不依赖外部 MQTT broker。`SubscriptionQueue` 为内存队列，不持久化、不跨进程。

限制：当前仅 `MqttFacade` 实现 subscribe 语义。`HttpRestFacade`、`ModbusTcpFacade` 和 `ServerSimulatorFacade` 的 subscribe 仍为 `UnsupportedOperation`。

### SF-FR-012 probe 最小工具能力

Starfish 提供 `tools/probe.py` — `run_probe(facade, plan, point_ids=None, skip_start=False)` 对 facade 执行最简可用性探测。已覆盖 stub/HTTP_REST/MODBUS_TCP/MQTT/OPC_UA/IEC104 六种 facade。

探测序列：
1. 若未跳过启动且 facade 未运行，执行 `facade.start()`。
2. 执行 `facade.health()` 健康检查。
3. 如需加载且未加载，执行 `facade.load_points(plan)`。
4. 读取一个或多个点位 `facade.read(point_ids)`。
5. 返回 `ProbeResult`（status="PASS"|"FAIL"|"NOT_RUN"、reason 说明）。

`ProbeResult` dataclass 字段：`endpoint_id`、`protocol`、`status`、`reason`、`point_values`、`health`。

NOT_RUN 条件：plan 为空（reason="no plan provided"）、unsupported protocol（reason="unsupported protocol"）、facade mode="unavailable"（reason="dependency unavailable"）。FAIL 条件：start/health/read 任一步骤异常。

OPC_UA/IEC104 behavior：real mode 时 probe 执行子进程 start -> READY 信号 -> TCP connect health -> read -> stop 完整序列。unavailable mode 时返回 NOT_RUN + reason（如 "open62541 binary not found"）。

安全边界：不得 import seahorse / whale.ingest / whale.shared.source；不做生产级诊断。

### SF-FR-013 profile 最小工具能力

Starfish 提供 `tools/profile.py` — `run_profile(facade, plan, iterations=10, point_ids=None)` 对 facade 执行 `iterations` 次 `facade.read(point_ids)` 操作并统计耗时。已覆盖 stub/HTTP_REST/MODBUS_TCP/MQTT/OPC_UA/IEC104 六种 facade。

返回 `ProfileResult` dataclass 字段：`endpoint_id`、`protocol`、`iterations`、`count`（成功完成的读取次数）、`min_ms`、`max_ms`、`avg_ms`、`total_ms`。

iterations <= 0 时返回 `ProfileResult` status="FAIL"（reason="iterations must be > 0"）。

OPC_UA/IEC104 behavior：real mode 时 profile 通过子进程 facade read 执行采样。unavailable mode 时返回 NOT_RUN + reason。

profile 不替代生产级性能测试，不做伪性能结论。仅提供本地点位读取的轻量耗时统计。

安全边界：不得 import seahorse / whale.ingest / whale.shared.source。

### SF-FR-014 capacity 最小工具能力

Starfish 提供 `tools/capacity.py` — `run_capacity(facade, plan, point_ids=None, read_iterations=100)` 对 facade 执行轻量端点/点位/读取容量扫描。

返回 `CapacityResult` dataclass 字段：`endpoint_id`、`protocol`、`status`（"PASS"|"FAIL"|"NOT_RUN"）、`point_count`、`tested_point_count`、`read_iterations`、`reason`。

NOT_RUN 条件：unsupported protocol（facade not available）、point_count=0（reason="no points to test"）、facade mode="unavailable"（reason="dependency unavailable"）。FAIL 条件：read 操作连续异常。

支持 HTTP_REST / MODBUS_TCP / MQTT / OPC_UA / IEC104 已实现真实 facade 的容量扫描。不做生产级容量规划或压测。

OPC_UA/IEC104 behavior：real mode 时 capacity 通过子进程 facade read 执行容量扫描。unavailable mode 时返回 NOT_RUN + reason。

安全边界：不得 import seahorse / whale.ingest / whale.shared.source。

### SF-FR-015 OPC_UA real mode — open62541 C runner 子进程

Starfish 提供 `OpcUaFacade`，使用 open62541 C 原生运行器子进程实现 OPC UA 协议服务端生命周期。

核心行为：

- `dependency probe`：`probe_opcua_binary()` 检测 open62541 二进制文件是否存在（stat + st_size + 可执行权限位 os.R_OK）。
  - 二进制不存在或大小 < threshold：mode="unavailable" + reason（如 "open62541 binary not found"）。
  - 二进制存在且可执行：mode="real"。
- `start()`：`subprocess.Popen` 启动 open62541 C runner 子进程，等待 READY 信号（读 stdout 输出），随后 TCP connect 确认端口可达。已在运行时抛 RuntimeError。幂等安全。
- `stop()`：terminate + wait 子进程。幂等安全。
- `health() -> dict`：TCP connect 探测确认端口可达。
- `load_points(plan)`：从 StarfishServerPlan 加载点位定义和 initial_values。
- `read(point_ids=None) -> dict`：从内存读取点位值。
- `update_values(values)`：批量更新点位值到内存。
- `capabilities() -> list[str]`：返回 plan 能力声明列表。
- `mode` 属性：返回 "real" 或 "unavailable"。

NOT_IMPLEMENTED：

- `write()` -- 抛出 `UnsupportedOperation("write", ...)`。
- `subscribe()` -- 抛出 `UnsupportedOperation("subscribe", ...)`。
- `report()` -- 抛出 `UnsupportedOperation("report", ...)`。

**不得把 unavailable 写为 PASS**。dependency probe 返回 unavailable 时，facade start/stop 不执行子进程（mode="unavailable" + reason 说清原因）。

协议特征：依赖外部 C 二进制（open62541 runner）。不等同于完整 OPC UA server（仅最简生命周期：start/stop/health/read）。可在有二进制环境中通过 localhost 动态端口稳定运行。

安全边界：不得 import seahorse / whale.ingest / whale.shared.source；所有数据标注 synthetic；不得伪装生产 OPC UA 设备。

### SF-FR-016 IEC104 real mode — iec104_simulator_server C runner 子进程

Starfish 提供 `Iec104Facade`，使用 iec104_simulator_server C 原生运行器子进程实现 IEC 104 协议服务端生命周期。

核心行为：

- `dependency probe`：`probe_iec104_binary()` 检测 iec104_simulator_server 二进制文件是否存在（stat + st_size + 可执行权限位 os.R_OK）。
  - 二进制不存在或大小 < threshold：mode="unavailable" + reason（如 "iec104_simulator_server binary not found"）。
  - 二进制存在且可执行：mode="real"。
- `start()`：`subprocess.Popen` 启动 iec104_simulator_server C runner 子进程，等待 READY 信号（读 stdout 输出）。已在运行时抛 RuntimeError。幂等安全。
- `stop()`：terminate + wait 子进程。幂等安全。
- `health() -> dict`：TCP connect 探测确认端口可达。
- `load_points(plan)`：从 StarfishServerPlan 加载点位定义和 initial_values。
- `read(point_ids=None) -> dict`：从内存读取点位值。
- `update_values(values)`：批量更新点位值到内存。
- `capabilities() -> list[str]`：返回 plan 能力声明列表。
- `mode` 属性：返回 "real" 或 "unavailable"。

NOT_IMPLEMENTED：

- `write()` -- 抛出 `UnsupportedOperation("write", ...)`。
- `subscribe()` -- 抛出 `UnsupportedOperation("subscribe", ...)`。
- `report()` -- 抛出 `UnsupportedOperation("report", ...)`。

**不得把 unavailable 写为 PASS**。dependency probe 返回 unavailable 时，facade start/stop 不执行子进程。

协议特征：依赖外部 C 二进制（iec104_simulator_server runner）。不等同于完整 IEC 104 server（仅最简生命周期）。可在有二进制环境中通过 localhost 动态端口稳定运行。

安全边界：不得 import seahorse / whale.ingest / whale.shared.source；所有数据标注 synthetic；不得伪装生产 IEC 104 设备。

### SF-FR-017 dependency probe 与 unavailable 语义

Starfish 提供统一的 dependency probe 机制，用于检测 native C runner 二进制是否存在、是否可执行。

行为规范：

- `probe_xxx_binary()` 使用 `os.stat(path)` 获取文件大小（st_size），使用 `os.access(path, os.R_OK)` 检测可执行权限。
- 探测时检查：
  1. 文件存在性（os.stat 不抛异常）。
  2. 文件大小 >= 阈值（如 1024 bytes）防止错误文件路径。
  3. 可执行权限位（os.R_OK）。
- 探测通过时：二进制可用，facade mode="real"。
- 探测未通过时：facade mode="unavailable" + reason（明确说清哪项检查失败，如 "open62541 binary too small (64 bytes)"）。

**unavailable 语义规则**：

- **mode="unavailable" 不得写为 PASS**。这是明确的"不可用"状态。
- facade start()/stop() 在 unavailable 时不执行子进程（method is a no-op with reason logged）。
- health() 在 unavailable 时返回 status="unavailable" + reason。
- probe/profile/capacity 对 unavailable facade 返回 NOT_RUN + reason（如 "OPC_UA facade unavailable: open62541 binary not found"）。
- RuntimeRegistry FacadeEntry.available 字段为 False，reason 包含探测失败原因。

安全边界：dependency probe 不启动子进程、不建立网络连接、不修改文件系统。仅做本地文件系统读取。

### SF-FR-018 IEC61850 MMS real mode -- iec61850_simulator_server C runner 子进程

Starfish 提供 `Iec61850MmsFacade`，使用 iec61850_simulator_server C 原生运行器子进程实现 IEC 61850 MMS 协议服务端生命周期。

核心行为：

- `dependency probe`：`probe_iec61850_binary("iec61850_simulator_server")` 检测 iec61850_simulator_server 二进制文件是否存在（stat + st_size + 可执行权限位 os.R_OK）。
  - 二进制不存在或大小 < threshold：mode="unavailable" + reason（如 "iec61850_simulator_server binary not found"）。
  - 二进制存在且可执行：mode="real"。
- `start()`：`subprocess.Popen` 启动 iec61850_simulator_server C runner 子进程，等待 READY 信号（读 stdout 输出），随后 TCP connect 确认端口可达。已在运行时抛 RuntimeError。幂等安全。
- `stop()`：terminate + wait 子进程。幂等安全。
- `health() -> dict`：TCP connect 探测确认端口可达。
- `load_points(plan)`：从 StarfishServerPlan 加载点位定义和 initial_values。
- `read(point_ids=None) -> dict`：**从内存读取点位值（非真实 MMS 协议帧）**。
- `update_values(values)`：批量更新点位值到内存。
- `capabilities() -> list[str]`：返回 plan 能力声明列表。
- `mode` 属性：返回 "real" 或 "unavailable"。

NOT_IMPLEMENTED：

- `write()` -- 抛出 `UnsupportedOperation("write", ...)`。
- `subscribe()` -- 抛出 `UnsupportedOperation("subscribe", ...)`。

**不得把 unavailable 写为 PASS**。dependency probe 返回 unavailable 时，facade start/stop 不执行子进程（mode="unavailable" + reason 说清原因）。

**关键限制**：read 为内存点位值，非通过 MMS 协议帧读取。这不等同于真实 MMS 数据交换验证。

协议特征：依赖外部 C 二进制（iec61850_simulator_server runner，27144 bytes）。不等同于完整 IEC 61850 MMS server（仅最简生命周期：start/stop/health/read 内存点位）。可在有二进制环境中通过 localhost 动态端口稳定运行。

安全边界：不得 import seahorse / whale.ingest / whale.shared.source；所有数据标注 synthetic；不得伪装生产 IEC 61850 MMS 设备。

### SF-FR-019 IEC61850 Report real mode + ReportQueue event 语义

Starfish 提供 `Iec61850ReportFacade`，使用 iec61850_report_runner C 原生运行器子进程实现 IEC 61850 Report 服务端生命周期，并引入 `ReportQueue` 作为 report event 队列。

核心行为：

- `dependency probe`：`probe_iec61850_binary("iec61850_report_runner")` 检测 iec61850_report_runner 二进制文件是否存在（stat + st_size + 可执行权限位 os.R_OK）。
  - 二进制不存在或大小 < threshold：mode="unavailable" + reason（如 "iec61850_report_runner binary not found"）。
  - 二进制存在且可执行：mode="real"。
- `start()`：`subprocess.Popen` 启动 iec61850_report_runner C runner 子进程，等待 READY 信号（读 stdout 输出）。已在运行时抛 RuntimeError。幂等安全。
- `stop()`：terminate + wait 子进程。幂等安全。
- `health() -> dict`：TCP connect 探测确认端口可达。
- `load_points(plan)`：从 StarfishServerPlan 加载点位定义和 initial_values。
- `read(point_ids=None) -> dict`：从内存读取点位值。
- `update_values(values)`：批量更新点位值到内存。
- `capabilities() -> list[str]`：返回 plan 能力声明列表。
- `mode` 属性：返回 "real" 或 "unavailable"。
- `report_queue` 属性：返回 `ReportQueue` 实例。

**ReportQueue event 语义**（SF-FR-019 核心新增）：

- `ReportQueue` 封装 `queue.Queue`，提供 `put(event)`、`get(timeout=None)`（阻塞等待）、`get_nowait()`（非阻塞取队首值或返回 None）、`drain()`（排空队列返回 list）。
- 队列为 FIFO 语义（先入先出）。
- 当前 events 来自 Python 侧（`update_values` 调用时推入 report queue），非来自子进程的真实 report 数据流。

NOT_IMPLEMENTED：

- `write()` -- 抛出 `UnsupportedOperation("write", ...)`。
- `subscribe()` -- 抛出 `UnsupportedOperation("subscribe", ...)`。

**report 语义已起步**：IEC61850 Report facade 已不再将 report 列为 NOT_IMPLEMENTED。`ReportQueue` 提供了 put/get/drain/FIFO 基础队列语义。但 events 当前来自 Python 侧（非子进程真实 report 数据），不等同于完整 IEC 61850 Report 数据交换。

**不得把 unavailable 写为 PASS**。dependency probe 返回 unavailable 时，facade start/stop 不执行子进程。

**关键限制**：
- Report runner 子进程在 real mode 测试中未实际启动（events 来自 Python 侧）。
- 不等同于真实 IEC 61850 Report 数据交换验证。

协议特征：依赖外部 C 二进制（iec61850_report_runner，26568 bytes）。不等同于完整 IEC 61850 Report server。可在有二进制环境中通过 localhost 动态端口稳定运行。

安全边界：不得 import seahorse / whale.ingest / whale.shared.source；所有数据标注 synthetic；不得伪装生产 IEC 61850 Report 设备。

### SF-FR-020 IEC101 facade 与 codec-enhanced mode（含 SIQ/QDS/NVA/M_SP_NA_1/M_DP_NA_1/M_ME_NA_1/C_SC_NA_1/ASDU 列表 SQ=0/SQ=1/FT1.2 帧）

Starfish 提供 `Iec101Facade`，作为 IEC 101 协议服务端模拟门面。当前以 in-memory stub 模式提供基础点位管理能力，mode 在编解码器增强就绪时为 `"codec-enhanced"`，未就绪时回退为 `"codec-skeleton"`。

核心行为：

- **mode（Round 15 更新）**：`"codec-enhanced"`（默认，增强编解码器全部可用）/ `"codec-skeleton"`（仅头部编解码回退）/ `"environment-pending"`（C runner 已编译但编解码器骨架不可用）/ `"codebase-pending"`（C runner 未编译且编解码器不可用）。由 `probe_iec101_codec_enhanced()` 和 `probe_iec101_codec()` 动态判定。
- `start()`/`stop()`/`health()`/`load_points(plan)`/`read(point_ids=None)`/`update_values(values)`/`capabilities()` -- in-memory stub 实现。
- `health()` 返回增强诊断信息：含 pty_available、lib60870_exists、native/bin/ 下 iec101 相关 binary 列表、codec_skeleton_ready、codec_enhanced_ready。
- **codec_capabilities()（Round 15 新增）**：返回 IEC101 增强编解码器能力声明列表：`codec_mode=codec-enhanced`、`supported_type_ids=M_SP_NA_1,M_DP_NA_1,M_ME_NA_1,C_SC_NA_1`、`supports_ft12_frame_codec=true`、`supports_server=false`、`supports_serial_runtime=false`。即使未加载 plan 也可查询。
- **protocol codec（Round 14 头部 + Round 15 增强）**：`src/starfish/protocols/iec101/` 提供：
  - `types.py` — TypeId 枚举（26 values，实测数量，以源码为准；M_SP_NA_1/M_SP_TA_1/M_DP_NA_1/M_DP_TA_1/M_ST_NA_1/M_ST_TA_1/M_BO_NA_1/M_ME_NA_1/M_ME_TA_1/M_ME_NB_1/M_ME_TB_1/M_ME_NC_1/M_ME_TC_1/M_IT_NA_1/M_IT_TA_1/C_SC_NA_1/C_DC_NA_1/C_RC_NA_1/C_SE_NA_1/C_SE_NB_1/C_SE_NC_1/M_EI_NA_1/C_IC_NA_1/C_CI_NA_1/C_RD_NA_1/C_CS_NA_1）+ COT 枚举（CauseOfTransmission，26 values；范围 1-63）。
  - `asdu.py` — ASDUHeader encode/decode（6 字节标准头部，含 TypeId/VSQ/COT/CA 字段）。
  - `ioa.py` — IOA encode/decode（3 字节信息对象地址，范围 0-16777215）。
  - `common_address.py` — CA encode/decode（2 字节公共地址，范围 0-65535）。
  - `quality.py`（Round 15 新增） — SIQ 单点信息质量描述符（IntFlag 位：value/blocked/substituted/not_topical/invalid 等）+ QDS 测量值质量描述符。
  - `information_elements.py`（Round 15 新增） — NVA 归一化值（16-bit signed，范围 [-1.0, +1.0 - 1/32768]）+ encode/decode。
  - `information_object.py`（Round 15 新增） — M_SP_NA_1（1）/ M_DP_NA_1（3）/ M_ME_NA_1（9）/ C_SC_NA_1（45）信息对象类。
  - `codec.py`（Round 15 新增） — ASDU 信息对象列表编解码（SQ=0 独立地址/SQ=1 顺序地址），未知 TypeId 返回 `UnknownAsduError`（不抛异常，安全解码）。
  - `frame.py`（Round 15 新增） — FT1.2 固定/可变帧编解码（含 checksum 校验和计算、长度不一致检测）。
  - 编解码函数为纯 Python 实现，zero external dependency。不等同完整 IEC101 server。

NOT_IMPLEMENTED：

- `write()` -- 抛出 `UnsupportedOperation("write", ...)`。
- `subscribe()` -- 抛出 `UnsupportedOperation("subscribe", ...)`。
- `report()` -- 抛出 `UnsupportedOperation("report", ...)`。
- IEC101 server 生命周期（非 stub）；平衡/非平衡传输模式状态机；真实串口/RS-232/RS-485 通信层；CP56Time2a 7 字节时标 IE（本轮 deferred，详见 SF-FR-028 边界）。

**codec-enhanced 定版说明（Round 15）**：

IEC 101 是串行通信链路协议（基于 RS-232/RS-485）。Round 14 在 `src/starfish/protocols/iec101/` 增加了 TypeId/COT 枚举和 ASDUHeader/IOA/CA 帧字段编解码骨架，使 `Iec101Facade` 的 mode 从 `"codebase-pending"` 升级为 `"codec-skeleton"`。Round 15 进一步增加信息体质量描述符（SIQ/QDS）、信息体元素（NVA）、信息对象（M_SP_NA_1/M_DP_NA_1/M_ME_NA_1/C_SC_NA_1）、ASDU 列表 SQ=0/SQ=1 编解码和 FT1.2 固定/可变帧 + checksum 编解码，使 mode 升级为 `"codec-enhanced"`。编解码函数为纯 Python 实现，zero external dependency。但这不是完整的 IEC101 server（无串口通信层、无 IEC 60870-5-101 状态机、无平衡/非平衡传输模式、无链路层控制字段）。`third_party/lib60870/` 中的 `iec101_simulator_slave.c` 可作为后续完整 server 实现的参考。

**不得把 codec-enhanced 写成 PASS**。codec-enhanced 表示编解码函数已实现但无完整 server 生命周期，不等同生产级 IEC101 server。`capabilities()` 显式声明 `supports_server=false` 和 `supports_serial_runtime=false`，调用方应据此区分。

协议特征：零外部二进制依赖（纯 Python stub），不等同于真实 IEC 101 设备。可在不依赖串口的单元测试中验证。

安全边界：不得 import seahorse / whale.ingest / whale.shared.source；所有数据标注 synthetic。



Starfish 提供 `ModbusRtuFacade`，使用 Python 标准库 `pty.openpty()` 创建 PTY pair 作为串口替代，实现 Modbus RTU 协议的轻量级 PTY server。

**两模式 dispatch**：

- PTY 可用：`mode="rtu-lightweight"`（真实 PTY server，不等同真实串口现场）
- PTY 不可用：`mode="codebase-pending"`（in-memory stub fallback）

**核心行为**：

- `dependency probe`（Round 13 增强）：`probe_modbus_rtu_binary()` 检查 pty 模块可用性并尝试创建 PTY pair 验证。PTY 可用时返回 (True, reason + "不等同真实串口")，不可用时返回 (False, reason + "codebase-pending")。
- `start()`：`pty.openpty()` 创建 master/slave PTY pair，master 端设 O_NONBLOCK，daemon 线程循环读取 RTU 帧并响应。codebase-pending 模式仅设内存状态。幂等安全。
- `stop()`：设置停止信号，关闭 PTY fd（master + slave），join 线程。幂等安全。
- `health()`：检查 PTY fd 有效性，含 note="PTY 不等同真实串口现场"。codebase-pending 模式 running=False。
- `load_points(plan)`：加载点位定义和 initial_values，按字典序建立 point_id -> register_address 双向映射。
- `read(point_ids=None)`：从内存读取点位值，线程安全。
- `write(point_id, value)`：rtu-lightweight 模式写入内存（等效 FC06 写入效果）；codebase-pending 抛出 UnsupportedOperation。
- `update_values(values)`：批量更新点位值，线程安全。
- `capabilities()`：返回 plan 能力声明列表。

**CRC16 算法**：多项式 0xA001（0x8005 反转），初始值 0xFFFF，无最终异或。5 个已知向量回归测试全通过。

**RTU 帧处理（Round 14 扩展，覆盖全部 4 个数据区）**：
- **Coils 区**：FC01 Read Coils（位读取，请求帧 [slave(1)][fc01(1)][start_addr(2)][quantity(2)][crc(2)]，响应位列表）；FC05 Write Single Coil（位写入，请求 [slave(1)][fc05(1)][addr(2)][value(2)][crc(2)]，value=0xFF00 ON/0x0000 OFF）；FC15 Write Multiple Coils（批量位写入）。
- **Discrete Inputs 区**：FC02 Read Discrete Inputs（位只读，帧格式同 FC01）。
- **Holding Registers 区**：FC03 Read Holding Registers（字读取）；FC06 Write Single Register（字写入，回显）；FC16 Write Multiple Registers（批量字写入）。
- **Input Registers 区**：FC04 Read Input Registers（字只读，帧格式同 FC03）。
- 异常码 0x01（illegal function）、0x02（illegal data address）、0x03（illegal data value）、0x04（server device failure）支持。
- 异常码 0x01（illegal function）、0x02（illegal data address）、0x03（illegal data value）支持。

**帧边界策略**：RTU 规范要求帧间 3.5 字符间隔。PTY 无真实串口时序，使用 CRC 逐字节探测帧边界。不等同真实串口现场。

NOT_IMPLEMENTED：

- `subscribe()` -- Modbus RTU 协议不支持服务端主动推送。
- `report()` -- 待后续轮次实现。

**关键限制**：

- PTY 不等同真实串口：无 RS-232/RS-485 电气特性、波特率、奇偶校验、停止位等物理层特性。
- 帧边界通过 CRC 逐字节探测模拟，无真实 3.5 字符间隔。
- 未实现异常码完整矩阵、浮点/32-bit 寄存器编解码、多从站 ID。

**不得把 rtu-lightweight 写成真实串口现场验证**。

协议特征：零外部二进制依赖（纯 Python 标准库 `pty` + `fcntl`）。不等同于真实 Modbus RTU 设备。可在单元测试中通过 PTY 稳定运行，47 个新测试全部通过。

安全边界：不得 import seahorse / whale.ingest / whale.shared.source；所有数据标注 synthetic。

### SF-FR-022 Beckhoff ADS facade 与 codebase-pending 定版（含增强探针）

Starfish 提供 `AdsFacade`，作为 Beckhoff ADS 协议服务端模拟门面。当前以 in-memory stub 模式提供基础点位管理能力，mode 恒为 "codebase-pending"。

核心行为：

- **mode**：固定为 `"codebase-pending"`。
- `start()`/`stop()`/`health()`/`load_points(plan)`/`read(point_ids=None)`/`update_values(values)`/`capabilities()` -- in-memory stub 实现。
- `health()` 返回增强诊断信息：含 dotnet_available、dotnet_path、TwinCAT 环境变量（TWINCAT_DIR/TWINCAT3_DIR/TC_REGISTRY/ADS_AMS_NET_ID）。
- **dependency probe（Round 13 增强）**：`probe_ads_binary()` 使用 shutil.which("dotnet") 探测 .NET runtime、检查 native/bin/ 下 ADS binary、检查 TwinCAT 环境变量。始终返回 (False, reason)，因为无 Python 原生 ADS 实现。

NOT_IMPLEMENTED：

- `write()` -- 抛出 `UnsupportedOperation("write", ...)`。
- `subscribe()` -- 抛出 `UnsupportedOperation("subscribe", ...)`。
- `report()` -- 抛出 `UnsupportedOperation("report", ...)`。

**codebase-pending 定版说明**：

Beckhoff ADS 协议依赖 .NET/TwinCAT runtime，当前开发环境（Linux）无法运行。source_lab 中有 ADS dotnet 参考实现（`tools/source_lab/protocols/beckhoff_ads/`），但需 Windows + TwinCAT 环境。`AdsFacade` 以 in-memory stub 定版，待后续有 .NET runtime 环境或 Python 原生实现后可升级为 real mode。

**不得把 codebase-pending 写成 PASS**。

协议特征：零外部二进制依赖（纯 Python stub），不等同于真实 Beckhoff ADS 设备。

安全边界：不得 import seahorse / whale.ingest / whale.shared.source；所有数据标注 synthetic。
Starfish 提供 `ModbusRtuFacade` 的 rtu-lightweight 模式，使用 Python 标准库 `pty.openpty()` 创建 PTY pair 作为串口替代，在 daemon 线程中从 master 端读取 RTU 帧并响应全部 8 个功能码（FC01-06/FC15/FC16）覆盖 4 个数据区。
### SF-FR-026 MODBUS_RTU rtu-lightweight PTY-backed real mode

Starfish 提供 `ModbusRtuFacade` 的 rtu-lightweight 模式，使用 Python 标准库 `pty.openpty()` 创建 PTY pair 作为串口替代，在 daemon 线程中从 master 端读取 RTU 帧并响应 FC03（Read Holding Registers）和 FC06（Write Single Register）。

**核心组件**：

- **CRC-16-IBM（多项式 0xA001）**：标准 Modbus RTU 循环冗余校验算法，初始值 0xFFFF，无最终异或。用于帧完整性校验和响应帧生成。5 个已知向量回归测试全通过。

- **FC03 Read Holding Registers**：解析请求帧 [slave(1)][fc03(1)][start_addr(2)][quantity(2)][crc(2)]，从寄存器映射读取值，构造响应帧。

- **FC06 Write Single Register**：解析请求帧 [slave(1)][fc06(1)][reg_addr(2)][reg_value(2)][crc(2)]，写入内部存储，回显请求帧作为响应。

- **PTY 生命周期管理**：`pty.openpty()` 创建 master/slave PTY pair；master 端设置为 O_NONBLOCK；daemon 线程循环读取 RTU 帧；帧间通过 CRC 探测边界（非真实 3.5 字符间隔）；stop() 关闭 fd 并 join 线程。

- **帧边界策略**：RTU 规范要求帧间 3.5 字符间隔。PTY 是本地模拟无真实串口时序，使用 CRC 逐字节探测帧边界。不等同真实串口现场。

**运行模式**：

- `mode="rtu-lightweight"`：PTY 可用时的轻量级 Modbus RTU PTY server。
- `mode="codebase-pending"`：PTY 不可用时的 in-memory stub fallback。

**已实现方法**：

- `start()` -- `pty.openpty()` 创建 PTY pair，daemon 线程循环读取 RTU 帧。幂等安全。
- `stop()` -- 设置停止信号，关闭 PTY fd（master + slave），join 线程。幂等安全。
- `health() -> dict` -- 检查 PTY fd 有效性。含 note="PTY 不等同真实串口现场"。codebase-pending 模式 running=False。
- `load_points(plan)` -- 加载点位和初始值，构建 point_id -> register_address 双向映射（字典序排序）。
- `read(point_ids=None) -> dict` -- 从内存读取点位值，线程安全。
- `write(point_id, value)` -- rtu-lightweight 模式写入内部存储（等效 FC06）；codebase-pending 抛出 UnsupportedOperation。
- `update_values(values)` -- 批量更新点位值，线程安全。
- `capabilities() -> list[str]` -- 返回 plan 能力声明列表。

**NOT_IMPLEMENTED**：

- `subscribe()` -- Modbus RTU 协议不支持服务端主动推送。
- `report()` -- 待后续轮次实现。

**关键限制**：

- PTY 不等同真实串口：无 RS-232/RS-485 电气特性、波特率、奇偶校验、停止位等物理层特性。
- 帧间边界通过 CRC 逐字节探测模拟，无真实 3.5 字符间隔。
- 未实现浮点/32-bit 寄存器编解码、多从站 ID、广播地址支持。异常码矩阵已实现 4 个 (0x01-0x04)。
- 仅用于本地功能验证，不能替代真实串口现场测试。

**dependency probe 增强**：`probe_modbus_rtu_binary()` 检查 `pty` 模块可用性并尝试创建 PTY pair。PTY 可用时返回 (True, reason + "不等同真实串口")，不可用时返回 (False, reason + "codebase-pending")。

**协议特征**：零外部二进制依赖（纯 Python 标准库，`pty` + `fcntl`）。不等同真实 Modbus RTU 设备。可在不依赖真实串口的单元测试中验证。

**安全边界**：不得 import seahorse / whale.ingest / whale.shared.source；所有数据标注 synthetic。

### SF-FR-027 IEC101 codec-skeleton -- TypeId/COT/ASDUHeader/IOA/CA 编解码骨架

Starfish 提供 `src/starfish/protocols/iec101/` 包，包含 IEC 101 协议帧字段编解码骨架（纯 Python，zero external dependency）。这不是完整的 IEC101 server（无串口通信层、无链路层控制字段、无平衡/非平衡传输模式、无 IEC 60870-5-101 状态机）。

**核心组件**：

- **`types.py` — TypeId 枚举**：26 个标准 IEC 101 类型标识符值（实测数量，以源码为准；Round 14 文档中曾写 34 values，Round 15 复核为 26 个，命名空间为 M_* 监视方向 + C_* 控制方向 + 系统信息），含 M_SP_NA_1（单点信息）、M_ME_NA_1（归一化测量值）、C_SC_NA_1（单点命令）、C_IC_NA_1（总召唤命令）、C_CS_NA_1（时钟同步命令）等。支持整数值和字符串名称双向查询。
- **`types.py` — COT 枚举**：`CauseOfTransmission` 枚举（实测数量，以源码为准；Round 14 文档中曾写 54 values，Round 15 复核为 26 个在用枚举值），含 PERIODIC（周期性）、SPONTANEOUS（突发）、INTERROGATION_STATION（站总召唤）、INTERROGATION_GROUP_1-6（组 1-6 总召唤）等。支持整数值和字符串名称双向查询。注意：P/N 位（bit 6）作为整数整体编码，枚举值仅表示原因码本体（不含 P/N 位）。
- **`asdu.py` — ASDUHeader encode/decode**：6 字节标准 ASDU 头部编解码。结构为 [type_id(1)][vsq(1)][cot(1)][ca(2)][ioa(1)]。含 VSQ（bit 0-6 = IO 数量、bit 7 = SQ 标志）、COT（bit 0-5 = 原因码、bit 6 = P/N、bit 7 = T 试验）字段。完整 encode/decode 含字节序处理（little-endian）。
- **`ioa.py` — IOA encode/decode**：3 字节信息对象地址编解码。encode_information_object_address(addr) -> bytes[3]，decode_information_object_address(bytes) -> int。范围 0-16777215（24-bit）。边界校验。
- **`common_address.py` — CA encode/decode**：2 字节公共地址编解码。encode_common_address(addr) -> bytes[2]，decode_common_address(bytes) -> int。范围 0-65535（16-bit）。边界校验。

**NOT_IMPLEMENTED 声明**：

- 串口通信层（RS-232/RS-485 物理链路、字节流收发）
- IEC 60870-5-101 链路层控制字段和帧格式（FT1.2 固定/可变帧长 — Round 15 已部分实现）
- 平衡/非平衡传输模式状态机
- 完整 ASDU 信息体（仅帧头编解码，不含信息体元素列表 — Round 15 已部分实现）
- 链路地址字段（A-field）编解码
- 完整 IEC101 server/subscriber/simulator
- CP56Time2a 7 字节时标 IE（本轮 deferred，详见 SF-FR-028）

**不得把 codec-skeleton 写成完整 IEC101 server 或生产级实现**。

协议特征：纯 Python 实现，零外部二进制依赖。不等同于完整 IEC 101 server。可在不依赖串口的单元测试中验证（30 tests）。

安全边界：不得 import seahorse / whale.ingest / whale.shared.source；所有数据标注 synthetic。

### SF-FR-028 IEC101 codec-enhanced -- 信息体 + ASDU 列表 + FT1.2 帧编解码（Round 15 新增）

Starfish 在 SF-FR-027 codec-skeleton 基础上，新增 5 个编解码模块 + 3 个测试文件，使 `Iec101Facade` 的 mode 从 `"codec-skeleton"` 升级为 `"codec-enhanced"`（默认）。

**核心组件**（全部为纯 Python，zero external dependency）：

- **`quality.py` — SIQ / QDS 质量描述符**：
  - `SIQ`（Single-point Information Quality descriptor）：1 字节 IntFlag 位标志（value/blocked/substituted/not_topical/invalid 等），附在 M_SP_NA_1/M_SP_TA_1 等单点信息体之后。
  - `QDS`（Quality Descriptor for Measured Values）：1 字节 IntFlag 位标志，附在 M_ME_NA_1/M_ME_NB_1/M_ME_NC_1 等测量值信息体之后。
  - `encode_siq(siq) -> bytes[1]`、`decode_siq(bytes) -> SIQ`、`encode_qds(qds) -> bytes[1]`、`decode_qds(bytes) -> QDS`。
  - `SIQFlags`/`QDSFlags` 显式枚举位含义。

- **`information_elements.py` — 信息体元素（IE）**：
  - `NVA`（Normalized Value）：16-bit signed 归一化值，范围 [-1.0, +1.0 - 1/32768]，对应 M_ME_NA_1。
  - 常量 `NVA_LENGTH=2`、`NVA_MIN=-1.0`、`NVA_MAX=1.0 - 1/32768`。
  - `encode_normalized_value(value) -> bytes[2]`、`decode_normalized_value(bytes) -> float`。
  - `NormalizedValue` dataclass。
  - SVA/ShortFloat 占位（不导出）。

- **`information_object.py` — 信息对象（IO）**：
  - `M_SP_NA_1_Object`（TypeId=1，单点信息，不带时标）：信息体 = SIQ(1 byte)。
  - `M_DP_NA_1_Object`（TypeId=3，双点信息，不带时标）：信息体 = DPI(2 bits) + RES(2 bits) 共 1 字节。
  - `M_ME_NA_1_Object`（TypeId=9，归一化测量值，不带时标）：信息体 = NVA(2 bytes) + QDS(1 byte)。
  - `C_SC_NA_1_Object`（TypeId=45，单命令，不带时标）：信息体 = SCS(1 bit) + SE(1 bit) + QU(5 bits) + RES(1 bit) 共 1 字节（QU 字段语义简化，详见限制）。
  - 每个类提供 `.encode() -> bytes` 和 `.classmethod .decode(bytes)`。

- **`codec.py` — ASDU 信息对象列表编解码**：
  - `Asdu` dataclass：包含 ASDUHeader + ioa_list（int 列表）+ information_objects 列表。
  - `encode_asdu(asdu) -> bytes` / `decode_asdu(bytes) -> Asdu`。
  - 支持 SQ=0（独立地址，每个对象前置 IOA）和 SQ=1（顺序地址，仅首个对象前置 IOA，后续 IOA = first_ioa + i）。
  - 未知 TypeId 安全解码：返回 `UnknownAsduError` 异常（不抛崩溃，由调用方决定如何处理）。

- **`frame.py` — FT1.2 链路层帧编解码**：
  - **固定长度帧（FixedFrame）**：5 字节 = start(0x10) + control(1) + checksum(1) + end(0x16)，用于链路层控制/确认/请求等短帧。`FixedFrame(control=N).encode() -> bytes`、`FixedFrame.decode(bytes) -> FixedFrame`。
  - **可变长度帧（VariableFrame）**：start(0x68) + length(1) + length(1) + data(length) + checksum(1) + end(0x16)，最小 5 字节，最大 length=255 时总长 261 字节。`VariableFrame(data=bytes).encode() -> bytes`、`VariableFrame.decode(bytes) -> VariableFrame`。
  - `compute_checksum(data) -> int`：校验和 = (sum(data) & 0xFF) 取补码。
  - `verify_checksum(data) -> bool`：校验和验证。
  - `decode_frame(bytes) -> FrameDecodeResult`：自动识别固定/可变帧并解码。
  - `FrameError` 自定义异常（checksum 不匹配、长度不一致、起始/结束字符错误等）。
  - **长度不一致检测**：可变帧两个 length 字段必须一致；data 长度必须等于 length。

**能力声明（`Iec101Facade.codec_capabilities()` 返回）**：

```text
codec_mode=codec-enhanced
supported_type_ids=M_SP_NA_1,M_DP_NA_1,M_ME_NA_1,C_SC_NA_1
supports_ft12_frame_codec=true
supports_server=false
supports_serial_runtime=false
```

**模式分级与动态判定**：

`Iec101Facade.mode` 属性在 `codec-enhanced` / `codec-skeleton` / `environment-pending` / `codebase-pending` 四级中动态判定：
1. 优先调用 `probe_iec101_codec_enhanced()`，验证 SIQ/QDS/NVA/4 个信息对象/ASDU 列表/FT1.2 帧/校验和均可用 -> mode="codec-enhanced"。
2. 回退调用 `probe_iec101_codec()`，验证 ASDU/COT/IOA/CA 编解码可用 -> mode="codec-skeleton"。
3. 检查 `native/bin/iec101_simulator_slave` 存在性 -> mode="environment-pending"。
4. 其余情况 -> mode="codebase-pending"。

**NOT_IMPLEMENTED 声明**：

- IEC101 server 生命周期（无真实子进程或 PTY server 启动）。
- 平衡/非平衡传输模式状态机。
- 真实串口/RS-232/RS-485 通信层（`supports_serial_runtime=false`）。
- IEC101 server/subscriber/simulator 完整实现（`supports_server=false`）。
- **CP56Time2a 7 字节时标 IE（本轮 deferred，详见限制）**。
- 完整 ASDU 类型矩阵（仅 4 个最常用 TypeId；TypeId=2/4/5/6/7/10/11/12/13/14/15/16/46/47/48/49/50/70/100/101/102/103 已枚举但未编解码）。

**关键限制**：

- **CP56Time2a 7 字节时标 IE 显式 deferred**：`information_elements.py` 中未实现 `cp56time2a` encode/decode 函数。理由：带时标 TypeId（M_SP_TA_1/M_DP_TA_1/M_ST_TA_1/M_ME_TA_1/M_ME_TB_1/M_ME_TC_1/M_IT_TA_1）的信息体编解码依赖时标 IE，本轮未涉及。建议 Round 16 处理：补齐 CP56Time2a IE（7 字节，含毫秒/分/时/日/月/年/品质）+ 带时标 TypeId 信息对象。
- **QU 字段语义简化**（C_SC_NA_1_Object）：C_SC_NA_1 单命令的 QU（Qualifier of Command）5 位字段在标准协议中含 S/E（Select/Execute）位、QL（Qualifier）位等多重含义；本轮实现仅做位级别编解码，语义上简化为"单命令控制字"。
- **QU 字段语义简化**（C_SC_NA_1_Object）：C_SC_NA_1 单命令的 QU（Qualifier of Command）5 位字段在标准协议中含 S/E（Select/Execute）位、QL（Qualifier）位等多重含义；本轮实现仅做位级别编解码，未拆分 S/E 和 QL 子字段。
- **probe/profile/capacity 仍 NOT_RUN/CODEC_ONLY**：即使 mode=codec-enhanced，probe/profile/capacity 工具层对 IEC101 仍返回 NOT_RUN/CODEC_ONLY + reason（"IEC101 codec-only, supports_server=false"），不得写 PASS。
- **不等同真实串口通信**：codec-enhanced 是编码/解码能力，不等于真实 IEC101 server 与设备交互。`supports_serial_runtime=false` 必须显式声明。

**不得把 codec-enhanced 写成完整 IEC101 server 或生产级实现**。

协议特征：纯 Python 实现，零外部二进制依赖，zero third_party 引入。不等同于完整 IEC 101 server。可在不依赖串口的单元测试中验证（138 tests：codec 40 + information_elements 24 + asdu_objects 38 + ft12_frame 36 = 138）。

安全边界：不得 import seahorse / whale.ingest / whale.shared.source；不得 import `third_party.lib60870` 或任何第三方 IEC101 实现；所有数据标注 synthetic；不得 spawn 真实 C runner 子进程作为编解码主路径。

### SF-FR-029 IEC101 codec-enhanced-plus -- CP56Time2a 时标 IE + **17 TypeID 矩阵（Round 18 扩展 14 + Round 19 扩展 3 C_SE_T*）** + ShortFloat 短浮点 + QU 显式化 + ScaledValue IE + QOS 结构化 + 5 态链路层骨架 + FCB/FCV/timers（Round 16 起步，Round 17 一次性收口，Round 18 扩展，Round 19 扩展 3 C_SE_T*）

Starfish 在 SF-FR-028 codec-enhanced 基础上，Round 16 新增 2 个 codec 模块（`time.py` CP56Time2a 时标 IE + `link_layer.py` 链路层最小状态机骨架）+ 1 个新测试文件（`test_iec101_link_layer.py` 40 tests），并扩展既有 `information_object.py`（3 带时标 TypeID + C_SC_NA_1 QU 结构化）、`test_iec101_information_elements.py`（+27 CP56Time2a tests）、`test_iec101_asdu_objects.py`（+37 带时标 + QU tests），使 `Iec101Facade.mode` 从 `"codec-enhanced"` 升级为 `"codec-enhanced-plus"`（5 级）。Round 17 在 codec-enhanced-plus 范围内**一次性收口**：补齐 ShortFloat IEEE 754 32-bit IE + M_ME_TB_1 / M_ME_TC_1 带时标短浮点信息对象 + C_SC_NA_1 QU 字段显式化（CommandPulse 枚举 + SingleCommandQualifier 子字段）+ LinkLayer skeleton 扩展（5 态 + LinkLayerTimers + t1/t2/t3 + FCB/FCV helper + balanced/unbalanced 差异化）+ 修复 `Iec101Facade.health()` reason_text codec-enhanced-plus 显式分支（**移除 Round 16 残留风险**）。Round 18 在 codec-enhanced-plus 范围内**扩展**：补齐 5 个新信息对象（M_ME_NB_1 不带时标标度化 / M_ME_NC_1 不带时标短浮点 / C_SE_NA_1 / C_SE_NB_1 / C_SE_NC_1 不带时标命令） + ScaledValue IE（16-bit signed）+ QOS 结构化 SetPointQualifier 枚举 + SetPointCommandQualifier dataclass + `Iec101Facade.codec_capabilities()` 显式 `supports_write_runtime=false`（**C_SE_* command codec 不得被高估为真实写能力，Iec101Facade.write() 仍抛 UnsupportedOperation**） + `supports_command_codec=true` + `supports_scaled_value=true` + `supported_measurement_type_ids` / `supported_command_type_ids` / `supported_time_tagged_type_ids` 分组。Round 19 在 codec-enhanced-plus 范围内**继续扩展**：补齐 3 个**新 C_SE_TA_1/C_SE_TB_1/C_SE_TC_1 带时标命令信息对象**（从 Round 18 deferred 转为已实现）+ `Iec101Facade.codec_capabilities()` 显式 `supported_command_type_ids` 从 4 升级至 7（`C_SC_NA_1 + C_SE_NA_1 + C_SE_NB_1 + C_SE_NC_1 + C_SE_TA_1 + C_SE_TB_1 + C_SE_TC_1`，**以 capability 实际值 7 为准**）+ `supported_time_tagged_type_ids` 从 5 升级至 8（5 既有 + 3 新）+ 新增 `supported_time_tagged_command_type_ids=C_SE_TA_1,C_SE_TB_1,C_SE_TC_1`（**以 capability 实际值 3 为准**）+ `supports_time_tagged_command_codec=true` + 维持 `supports_write_runtime=false`（**Iec101Facade.write/subscribe/report 仍抛 UnsupportedOperation，C_SE_T* command codec 不得被高估为真实写能力**）；**17 TypeId 矩阵（以 capability 实际值 17 为准；严禁硬写 13/14/15/18；Round 18 描述"13"和"4+2+4+5=15"已修正为 14，Round 19 进一步从 14 扩展至 17）**：4 不带时标监视（M_SP_NA_1/M_DP_NA_1/M_ME_NA_1/C_SC_NA_1）+ 1 不带时标标度化（M_ME_NB_1）+ 1 不带时标短浮点（M_ME_NC_1）+ 4 不带时标命令（C_SE_NA_1/C_SE_NB_1/C_SE_NC_1 + C_SC_NA_1 [按设计归监视，命令分组独立列示]）+ 3 带时标命令（C_SE_TA_1/C_SE_TB_1/C_SE_TC_1，Round 19 新增）+ 5 带时标监视（M_SP_TA_1/M_DP_TA_1/M_ME_TA_1/M_ME_TB_1/M_ME_TC_1）。

**核心组件**（全部为纯 Python，zero external dependency / zero third_party）：

- **`information_elements.py` 扩展**（**Round 17 新增** ShortFloat IEEE 754 32-bit IE）：
  - `ShortFloat` dataclass（32-bit IEEE 754 LE 编码）：`value: float` 字段；提供 `encode_short_float(value) -> bytes[4]` / `decode_short_float(data) -> ShortFloat` 辅助函数。
  - **严格拒绝 NaN/Inf**：`encode_short_float` 在 value 为 NaN/Inf 时抛出 `ShortFloatValueError`（**不**做特殊编码，不静默接受）。
  - **0.0/-0.0 区分**：encode 时区分 +0.0 和 -0.0（IEEE 754 符号位保留）；decode 时还原 +0.0 和 -0.0。
  - **极值边界**：±FLT_MAX / ±FLT_MIN / FLT_EPSILON 边界 roundtrip 通过。
  - **字节序**：IEEE 754 32-bit 小端字节序（LE），与 IEC 60870-5-101 ShortFloat 规范一致。
  - 常量：`SHORT_FLOAT_LENGTH=4`、`SHORT_FLOAT_SIGN_MASK=0x80000000`、`SHORT_FLOAT_EXPONENT_MASK=0x7F800000`、`SHORT_FLOAT_MANTISSA_MASK=0x007FFFFF`。
  - 兼容：与 IEC 60870-5-101 §7.2.6.7 ShortFloat 编码一致；与 IEC 60870-5-104 7 字节时标 + ShortFloat 编码相同（不实现 5-104 特殊差异）。
  - **Round 20 兼容扩展**（`encode_short_float` 接受更宽输入类型）：支持 **int / float / `numbers.Real` / `__float__` duck typing 统一入口**（探测 `isinstance(value, numbers.Real)` 优先，再 `hasattr(value, "__float__")` 走 duck typing；均失败时抛 `TypeError`）；NaN/Inf **仍严格拒绝**（`ShortFloatValueError`）；**不引入 numpy 硬依赖**（仅 `numbers` stdlib + duck typing 探测，numpy 用户可显式 `import numpy` 后传入 `np.float32` 实例）；**不等同**于支持 numpy 全部类型（仅 duck typing 兼容）。

- **`time.py` — CP56Time2a 7 字节时标 IE**：
  - `CP56Time2a` dataclass：milliseconds（0-59999）/ minute（0-59）/ hour（0-23）/ day_of_month（1-31）/ day_of_week（0-7，0=未指定）/ month（1-12）/ year（0-99，2000+year 映射）/ invalid（IV）/ summer_time（SU）/ substituted（SB）字段。
  - 字节布局（7 字节，按顺序）：byte 0-1 = uint16 LE milliseconds（0-59999）/ byte 2 = minute / byte 3 = hour / byte 4 = day_of_month 低 5 位 + 保留位 / byte 5 = month 低 4 位 + 4 保留位 / byte 6 = year 低 7 位 + IV 标志位（bit 7）。
  - `encode_cp56time2a(time) -> bytes[7]` / `decode_cp56time2a(data) -> CP56Time2a`。
  - `to_datetime(time) -> datetime.datetime` / `from_datetime(dt) -> CP56Time2a` 互转辅助函数。
  - 显式字段级校验：milliseconds 0..59999、minute 0..59、hour 0..23、day_of_month 1..31、month 1..12、year 0..99、day_of_week 0..7。
  - 常量：`CP56TIME2A_LENGTH=7`、`MILLISECONDS_MIN=0`、`MILLISECONDS_MAX=59999`、`YEAR_MIN=0`、`YEAR_MAX=99`、`MONTH_MIN=1`、`MONTH_MAX=12`、`HOUR_MIN/MAX`、`MINUTE_MIN/MAX`、`DAY_OF_MONTH_MIN/MAX`。
  - 兼容：编码与 IEC 60870-5-4 + IEC 60870-5-101 时标子集布局一致；与 IEC 60870-5-104 7 字节时标编码相同（不实现 5-104 特殊差异）。

- **`link_layer.py` — 链路层最小状态机骨架（**Round 16 起步，Round 17 扩展 5 态 + FCB/FCV + timers + balanced/unbalanced 差异化；Round 20 增强 LinkLayerTimerService + send/receive/on_timeout 状态机 + balanced FCB auto flip + retry ERROR；仅 skeleton 非 server**）**：
  - `LinkLayerMode(str, Enum)`：`BALANCED = "balanced"` / `UNBALANCED = "unbalanced"`。
  - `LinkState(str, Enum)`（Round 17 扩展至 5 态）：`IDLE = "idle"` / `WAIT_ACK = "wait_ack"` / `SEND = "send"` / `RECEIVE = "receive"` / `ERROR = "error"`。
  - `LinkLayerTimers` 常量 dataclass（Round 17 新增）：`T1_DEFAULT_MS=15000`（链路确认超时）/ `T2_DEFAULT_MS=10000`（响应超时）/ `T3_DEFAULT_MS=20000`（空闲超时）；提供 `t1` / `t2` / `t3` 属性访问。**仅常量，**不实现真实计时器线程**。
  - **`LinkLayerTimerService` 抽象**（**Round 20 新增**）：`start_timer(duration_ms, callback) -> TimerHandle` / `cancel_timer(handle) -> bool` / `cancel_all() -> int` / `on_timeout() -> None` API；TimerHandle 标识符。
  - **`DefaultLinkLayerTimerService`**（**Round 20 新增**）：基于 `threading.Timer` 的真实实现；timer daemon 线程，timeout 触发 callback；可注入 LinkLayer 启用计时。
  - **`FakeLinkLayerTimerService`**（**Round 20 新增**）：无 wall-clock 实现；`start_timer` 注册到内部 list，`cancel_timer` 移除，`cancel_all` 清空；不真正触发 timeout（**便于单测**）；**单测不依赖 sleep**。
  - `LinkEvent` dataclass：previous_state / new_state / frame_type / control / sequence / reason 字段。
  - `LinkControlHelper` 构造工具（静态方法）：`build_ack()` / `build_nack()` / `build_reset()` / `build_reset_ack()` / `build_user_data(payload)` 返回 `FixedFrame` / `VariableFrame` 帧。
  - `LinkControlHelper` FCB/FCV helper（Round 17 新增）：`fcb_bit_for_sequence(sequence: int) -> int`（按 send_sequence 计算 FCB 翻转位）；`fcv_bit(expected: bool) -> int`（FCV 帧计数有效位）。**仅 helper 计算，不维护真实 FCB session 状态**。
  - `LinkLayer` 类：维护当前 mode / state / send_sequence / retry_count；`feed_frame(frame) -> LinkEvent` 按状态机驱动转移；`bump_send_sequence() -> int` / `mark_waiting_ack()` / `mark_sending()` / `mark_receiving()` / `reset()` / `snapshot() -> dict` 暴露状态。
  - `LinkLayer` sequence flip / retry 骨架（Round 17 新增）：`flip_send_sequence() -> int`（balanced 模式 FCB 翻转由调用方手动控制，**不自动**）；`increment_retry_count() -> int`（错误后重试计数）；`should_retry(max_retries: int) -> bool`（达到 max_retries 返回 False）。
  - **`send_user_data(payload) -> LinkEvent`**（**Round 20 新增**）：发起 user_data 帧，状态从 IDLE -> SEND -> WAIT_ACK；**balanced + FCV=1** 时**自动**翻 send_sequence（`flip_send_sequence`）。
  - **`receive_ack() -> LinkEvent`**（**Round 20 新增**）：处理 ACK 帧；状态 WAIT_ACK -> IDLE；**balanced + FCV=1** 时**自动**翻 send_sequence（**balanced FCB auto flip 核心**）；NACK/timeout/FCV disabled/unbalanced **不翻**。
  - **`receive_nack() -> LinkEvent`**（**Round 20 新增**）：处理 NACK 帧；状态 WAIT_ACK -> ERROR（**不翻** send_sequence）；调用 `increment_retry_count`。
  - **`on_timeout() -> LinkEvent`**（**Round 20 新增**）：处理 timer 超时；**`retry_count += 1`**；`retry_count > max_retries` 进入 `ERROR` 状态；否则保留 WAIT_ACK（**等下一次 timeout 或 ACK/NACK**）。
  - **`balanced FCB auto flip 规则**（**Round 20 新增**）**：ACK + FCV=1 + mode=BALANCED 三条件同时满足时**自动**翻 send_sequence；任何条件不满足（NACK/timeout/FCV disabled/unbalanced）**不翻**；unbalanced 模式下 send_sequence 始终保持 0。
  - **`retry ERROR 规则**（**Round 20 新增**）**：`retry_count > max_retries` 显式进入 `ERROR` 状态；`max_retries` 由调用方注入（默认 3）；进入 ERROR 后必须 `reset()` 才能恢复。
  - **`enable_timers=False` 默认**（**Round 20 显式**）：保持 Round 17 行为完全一致（仅 in-process 状态机 + 帧 codec 复用，不启 timer）；**生产需显式 `enable_timers=True` + 注入 TimerService** 才能触发真实 timer + on_timeout；FakeLinkLayerTimerService 用于单测零 wall-clock 验证。
  - 状态转移规则（5 态）：
    - IDLE + ACK/NACK/USER_DATA -> IDLE（no-op 或保持）
    - IDLE + RESET/RESET_ACK -> IDLE
    - IDLE -> SEND（mark_sending 显式发起）
    - IDLE -> RECEIVE（mark_receiving 显式接收）
    - SEND + USER_DATA -> WAIT_ACK（等待 ACK）
    - SEND + ACK -> IDLE
    - SEND + NACK -> ERROR
    - WAIT_ACK + ACK -> IDLE
    - WAIT_ACK + NACK -> ERROR
    - WAIT_ACK + RESET -> WAIT_ACK 保留（等 ACK）
    - WAIT_ACK + RESET_ACK -> IDLE
    - WAIT_ACK + USER_DATA -> WAIT_ACK 保留
    - RECEIVE + USER_DATA -> RECEIVE（连续接收）
    - RECEIVE + ACK -> IDLE（接收完成）
    - ERROR + RESET/RESET_ACK -> IDLE（恢复）
    - ERROR + 其他 -> ERROR（保持）
    - 未知 control -> 保持当前状态
  - **balanced/unbalanced 差异化 skeleton 行为**（Round 17 新增 + Round 20 自动化）：
    - `BALANCED` 模式：FCB/FCV 翻转规则启用（**Round 20 升级**：`receive_ack` 自动翻 sequence）；send_sequence 在每次 USER_DATA 后 +1（flip_send_sequence），ACK 后保留 sequence。
    - `UNBALANCED` 模式：FCB/FCV 翻转**不**启用，send_sequence 始终保持 0；USER_DATA 直接进入 WAIT_ACK，不依赖 FCB 验证。
  - **零 Popen / threading（仅 timer 可选）/ socket / pty / serial**（默认 `enable_timers=False` 时仅 in-process 状态机 + 帧 codec 复用；启 timer 后用 `threading.Timer` daemon 线程，但**不连接任何真实串口/字节流/网络 IO**）。
  - **不是 server**：不连接任何真实串口 / 字节流 / 网络 IO；纯 codec + 状态机 + 可选 timer 辅助。

- **`information_object.py` 扩展**（3 带时标 TypeID + C_SC_NA_1 QU 显式化 + 2 带时标短浮点 M_ME_TB_1/M_ME_TC_1 + **3 带时标命令 C_SE_TA_1/C_SE_TB_1/C_SE_TC_1**）：
  - `M_SP_TA_1_Object`（TypeId=2，8 字节 = SIQ(1) + CP56Time2a(7)）：`.encode() -> bytes` / `.classmethod .decode(bytes)`。
  - `M_DP_TA_1_Object`（TypeId=4，8 字节 = DPI(1) + CP56Time2a(7)）：`.encode() -> bytes` / `.classmethod .decode(bytes)`。
  - `M_ME_TA_1_Object`（TypeId=10，10 字节 = NVA(2) + QDS(1) + CP56Time2a(7)）：`.encode() -> bytes` / `.classmethod .decode(bytes)`。
  - `M_ME_TB_1_Object`（TypeId=11，**Round 17 新增**，10 字节 = SVA(4) + QDS(1) + CP56Time2a(7)，标度化测量值带时标）：`.encode() -> bytes` / `.classmethod .decode(bytes)`；SVA 字段基于 NVA 同范围整数（[-32768, 32767]）；长度校验 `M_ME_TB_1_OBJECT_SIZE=10`。
  - `M_ME_TC_1_Object`（TypeId=13，**Round 17 新增**，12 字节 = ShortFloat(4) + QDS(1) + CP56Time2a(7)，短浮点测量值带时标）：`.encode() -> bytes` / `.classmethod .decode(bytes)`；ShortFloat 基于 IEEE 754 32-bit LE 编码；长度校验 `M_ME_TC_1_OBJECT_SIZE=12`。
  - `C_SE_TA_1_Object`（**Round 19 新增**，TypeId=58，**12 字节 = NVA(2) + QOS(1) + CP56Time2a(7)**，归一化值带时标命令）：`.encode() -> bytes` / `.classmethod .decode(bytes)`；与 IEC 60870-5-101 §7.2.6.9 对齐；长度校验 `C_SE_TA_1_OBJECT_SIZE=12`。
  - `C_SE_TB_1_Object`（**Round 19 新增**，TypeId=59，**12 字节 = SVA(2) + QOS(1) + CP56Time2a(7)**，标度化值带时标命令）：`.encode() -> bytes` / `.classmethod .decode(bytes)`；与 IEC 60870-5-101 §7.2.6.10 对齐；长度校验 `C_SE_TB_1_OBJECT_SIZE=12`。
  - `C_SE_TC_1_Object`（**Round 19 新增**，TypeId=60，**14 字节 = ShortFloat(4) + QOS(1) + CP56Time2a(7)**，短浮点值带时标命令）：`.encode() -> bytes` / `.classmethod .decode(bytes)`；与 IEC 60870-5-101 §7.2.6.11 对齐；长度校验 `C_SE_TC_1_OBJECT_SIZE=14`。
  - `C_SC_NA_1_QU_QUALIFIER` 枚举（**Round 17 新增**，标准协议 QU 5 bits 子字段拆分）：`NOT_PERMITTED=0` / `SHORT_PULSE=1` / `LONG_PULSE=2` / `PERSISTENT_OUTPUT=3` 等（按 IEC 60870-5-101 §7.2.6.3 QU 字段定义）。
  - `CommandPulse` 枚举（**Round 17 新增**）：`SHORT = "short"` / `LONG = "long"` / `PERSISTENT = "persistent"`。
  - `SingleCommandQualifier` 扩展（**Round 17 字段显式化**）：`scs(1)` / `select_execute: bool`（S/E 位）/ `qualifier: C_SC_NA_1_QU_QUALIFIER`（5 bits）/ `ql_value: int`（QL 0-31 数值）/ `persistent: bool`（持续输出位）/ `pulse: CommandPulse`（脉冲类型）+ `to_byte() -> int` / `from_byte(value) -> SingleCommandQualifier` / `sync_qu_bit()` 兼容旧位级 roundtrip。**保留** Round 15 旧位级 roundtrip 兼容（`sync_qu_bit()` 保证 38 tests 不回退）。
  - `C_SC_NA_1_Object` 扩展：保留原位级 encode/decode（向后兼容 Round 15），新增 `qu_bit: SingleCommandQualifier` 显式字段；`sync_qu_bit()` 方法同步 qu_bit 字段到内部位级表示。

- **`Iec101Facade` 升级**（**Round 17 一次性收口 + Round 18 扩展 + Round 19 扩展 3 C_SE_T* + Round 20 LinkLayer runtime skeleton + ShortFloat 兼容 + 3 新 capabilities**）：
  - `mode` 动态判定 5 级 codec-enhanced-plus / codec-enhanced / codec-skeleton / environment-pending / codebase-pending；优先调用 `probe_iec101_codec_enhanced_plus()`，验证 CP56Time2a/ShortFloat/3 带时标 TypeID+2 带时标短浮点/**3 带时标命令 C_SE_TA_1/C_SE_TB_1/C_SE_TC_1**/QU 结构化/LinkLayer 5 态骨架/**Round 20 LinkLayerTimerService + send/receive/on_timeout 状态机 + balanced FCB auto flip + retry ERROR（enable_timers 默认 False）**均可用 -> mode="codec-enhanced-plus"。
  - `health()` reason_text 显式 codec-enhanced-plus 分支（**Round 17 修复 Round 16 残留风险 + Round 19 同步 17 TypeId 矩阵 + Round 20 同步 LinkLayer runtime skeleton + 3 新 capabilities**）：包含 7 强制要点 — (1) codec_mode=codec-enhanced-plus / (2) CP56Time2a + ShortFloat 时标 / 短浮点 IE / (3) **17 TypeID 矩阵（Round 19 升级，4 不带时标监视 + 1 不带时标标度化 + 1 不带时标短浮点 + 4 不带时标命令 + 3 带时标命令 + 5 带时标监视 = 17，以 capability 实际值 17 为准，**严禁硬写 13/14/15/18**）** / (4) QU 字段结构化 / (5) 5 态 LinkLayer skeleton + FCB/FCV + timers / (6) **Round 20 LinkLayer runtime skeleton（LinkLayerTimerService 抽象 + Default threading.Timer + Fake 三实现 + send/receive/on_timeout 完整状态机 + balanced FCB auto flip + retry ERROR；默认 enable_timers=False 保持 Round 17 行为完全一致）** + supports_link_layer_timers=true / supports_balanced_fcb_auto_flip=true / supports_retry_skeleton=true / (7) supports_server=false / supports_serial_runtime=false / supports_write_runtime=false / supports_command_codec=true / supports_scaled_value=true / supports_time_tagged_command_codec=true。**不**再回退到 codec-enhanced 文案。
  - `health()` 新增 `codec_enhanced_plus_ready: bool` 诊断字段：与 codec_enhanced_ready / codec_skeleton_ready 同级。
  - `codec_capabilities()` 显式声明：
    - `codec_mode=codec-enhanced-plus`（默认）
    - `supported_type_ids=M_SP_NA_1,M_DP_NA_1,M_ME_NA_1,C_SC_NA_1,M_ME_NB_1,M_ME_NC_1,C_SE_NA_1,C_SE_NB_1,C_SE_NC_1,C_SE_TA_1,C_SE_TB_1,C_SE_TC_1,M_SP_TA_1,M_DP_TA_1,M_ME_TA_1,M_ME_TB_1,M_ME_TC_1`（4 不带时标监视 M_SP_NA_1/M_DP_NA_1/M_ME_NA_1/C_SC_NA_1 + 1 不带时标标度化 M_ME_NB_1 + 1 不带时标短浮点 M_ME_NC_1 + 4 不带时标命令 C_SC_NA_1/C_SE_NA_1/C_SE_NB_1/C_SE_NC_1 + **3 带时标命令 C_SE_TA_1/C_SE_TB_1/C_SE_TC_1（Round 19 新增）** + 5 带时标监视 M_SP_TA_1/M_DP_TA_1/M_ME_TA_1/M_ME_TB_1/M_ME_TC_1 = **17 TypeId**，**Round 19 扩展**，以 capability 实际值 17 为准；**严禁硬写 13/14/15/18**）
    - `supported_measurement_type_ids=M_SP_NA_1,M_DP_NA_1,M_ME_NA_1,C_SC_NA_1,M_ME_NB_1,M_ME_NC_1,M_SP_TA_1,M_DP_TA_1,M_ME_TA_1,M_ME_TB_1,M_ME_TC_1`（**Round 18 新增分组**：不带时标测量+带时标测量，共 11 个；C_SC_NA_1 按监视分组）
    - `supported_command_type_ids=C_SC_NA_1,C_SE_NA_1,C_SE_NB_1,C_SE_NC_1,C_SE_TA_1,C_SE_TB_1,C_SE_TC_1`（**Round 19 升级**至 7 个：4 不带时标命令 C_SC_NA_1/C_SE_NA_1/C_SE_NB_1/C_SE_NC_1 + 3 带时标命令 C_SE_TA_1/C_SE_TB_1/C_SE_TC_1；**以 capability 实际值 7 为准**）
    - `supported_time_tagged_command_type_ids=C_SE_TA_1,C_SE_TB_1,C_SE_TC_1`（**Round 19 新增分组**：3 带时标命令；**以 capability 实际值 3 为准**）
    - `supported_time_tagged_type_ids=M_SP_TA_1,M_DP_TA_1,M_ME_TA_1,M_ME_TB_1,M_ME_TC_1,C_SE_TA_1,C_SE_TB_1,C_SE_TC_1`（**Round 19 升级**至 8 个：5 带时标监视 + 3 带时标命令）
    - `supports_cp56time2a=true`
    - `supports_short_float=true`（Round 17 既有）
    - `supports_ft12_frame_codec=true`
    - `supports_link_layer_skeleton=true`（Round 17 既有：5 态 + FCB/FCV + timers + balanced/unbalanced 差异化）
    - `supports_link_layer_timers=true`（**Round 20 新增**：LinkLayerTimerService 抽象 + Default (threading.Timer) + Fake 三实现；`start_timer` / `cancel_timer` / `cancel_all` / `on_timeout` API；**默认 `enable_timers=False`** 保持 Round 17 行为完全一致；生产需显式 `enable_timers=True` + 注入 TimerService）
    - `supports_balanced_fcb_auto_flip=true`（**Round 20 新增**：balanced 模式下 ACK + FCV=1 时自动翻 send_sequence；NACK/timeout/FCV disabled/unbalanced **不翻**）
    - `supports_retry_skeleton=true`（**Round 20 新增**：retry_count 累加 + `retry_count > max_retries` 进入 ERROR 状态）
    - `supports_command_codec=true`（**Round 18 新增**：5 个不带时标命令信息对象 codec 能力显式声明）
    - `supports_time_tagged_command_codec=true`（**Round 19 新增**：3 个带时标命令信息对象 codec 能力显式声明）
    - `supports_scaled_value=true`（**Round 18 新增**：ScaledValue IE 16-bit signed 显式声明）
    - `supports_write_runtime=false`（**Round 18 维持 / Round 19 维持 / Round 20 维持**：**C_SE_T* / C_SE_N* command codec 不得被高估为真实写能力；Iec101Facade.write() 仍抛 UnsupportedOperation**）
    - `supports_server=false`（**不创建 server**）
    - `supports_serial_runtime=false`（**不连接真实串口**）

**模式分级与动态判定（5 级）**：

`Iec101Facade.mode` 在 `codec-enhanced-plus` / `codec-enhanced` / `codec-skeleton` / `environment-pending` / `codebase-pending` 5 级中动态判定：
1. 优先调用 `probe_iec101_codec_enhanced_plus()`，验证 CP56Time2a IE / 3 带时标 TypeID / QU 结构化 / LinkLayer 骨架均可用 -> mode="codec-enhanced-plus"。
2. 回退调用 `probe_iec101_codec_enhanced()`，验证 SIQ/QDS/NVA/4 信息对象/ASDU 列表/FT1.2 帧/校验和均可用 -> mode="codec-enhanced"。
3. 回退调用 `probe_iec101_codec()`，验证 ASDU/COT/IOA/CA 编解码可用 -> mode="codec-skeleton"。
4. 检查 `native/bin/iec101_simulator_slave` 存在性 -> mode="environment-pending"。
5. 其余情况 -> mode="codebase-pending"。

**NOT_IMPLEMENTED 声明**（与 codec-enhanced 一致 + Round 16/17 显式补充）：

- IEC101 server 生命周期（无真实子进程或 PTY server 启动）。
- **真实串口/RS-232/RS-485 通信层**（`supports_serial_runtime=false`）。
- **IEC101 server/subscriber/simulator 完整实现**（`supports_server=false`）。
- 链路层**真实计时器线程**（t1/t2/t3 常量已定义，但不实现真实计时器线程与超时回调）。
- balanced 模式 FCB **自动翻转策略**（FCB 翻转由调用方通过 `flip_send_sequence()` 手动控制，不实现自动翻转策略）。
- persistent session / 跨调用状态保留（每次 `LinkLayer` 实例独立维护本地状态）。
- ShortFloat 对 **numpy scalar 真实类型完整支持**（**Round 20 已收口 duck typing 兼容**：int / float / `numbers.Real` / `__float__` 统一入口；**不引入 numpy 硬依赖**；用户若传 `np.floating` 实例，依赖其实现 `__float__` duck typing 协议；**不**等于自动 detect np.floating 类型）。
- 完整 ASDU 类型矩阵（仅 17 个最常用 TypeId：M_SP_NA_1/M_DP_NA_1/M_ME_NA_1/C_SC_NA_1/M_ME_NB_1/M_ME_NC_1/C_SE_NA_1/C_SE_NB_1/C_SE_NC_1/C_SE_TA_1/C_SE_TB_1/C_SE_TC_1 + M_SP_TA_1/M_DP_TA_1/M_ME_TA_1/M_ME_TB_1/M_ME_TC_1；TypeId=5/6/7/14/15/16/46/47/70/100/101/102/103 已枚举但未编解码；TypeId=11/12/13/48/49/50 在 Round 18/19 扩展为 5/3 命令对象后已覆盖）。
- **C_SE_T* command codec 不得被高估为真实写能力**：Iec101Facade.write() 仍抛 UnsupportedOperation（`supports_write_runtime=false` 显式）。

**关键限制**：

- **链路层 skeleton 仅 5 态（IDLE/WAIT_ACK/SEND/RECEIVE/ERROR）**：不代表完整 IEC 60870-5-101 链路层；不实现超时回调、真实计时器线程、自动 FCB 翻转策略、persistent session。`LinkLayer.feed_frame()` 在不连接任何真实串口的情况下按状态机驱动转移；不重试、不起线程。t1/t2/t3 仅为常量骨架，不启动后台计时。
- **probe/profile/capacity 仍 NOT_RUN/CODEC_ONLY**：即使 mode=codec-enhanced-plus，probe/profile/capacity 工具层对 IEC101 仍返回 NOT_RUN/CODEC_ONLY + reason（"IEC101 codec-only, supports_server=false"），不得写 PASS。
- **不得把 link-layer skeleton PASS 写成 IEC101 server PASS**。skeleton 是 codec + 状态机辅助，不等同真实 IEC101 server 与设备交互。
- **不得把 probe/profile 的 stub PASS 写成 IEC101 真实协议能力**。`supports_server=false` / `supports_serial_runtime=false` 必须显式声明。
- **不等同真实串口通信**：codec-enhanced-plus 是编码/解码 + skeleton 状态机能力，不等于真实 IEC101 server 与设备交互。`supports_serial_runtime=false` 必须显式声明。
- **CP56Time2a day_of_week 处理**：编码时使用 IEC 60870-5-4 字节 4 布局（day_of_month 1..31 + 保留位），`day_of_week` 字段作为概念层属性独立存放，不参与字节 4 编码（兼容常见 5-101 编码）。
- **ShortFloat NaN/Inf 严格拒绝**：`encode_short_float` 在 value 为 NaN/Inf 时抛出 `ShortFloatValueError`，调用方需自行处理（**不**做特殊编码，不静默接受）。

**显式风险（Round 16 残留项，**Round 17 已修复，不得继续列为风险**）**：

- ~~**Iec101Facade.health() reason_text 分支缺失 codec-enhanced-plus**~~（**Round 17 修复**）：`Iec101Facade.health()` reason_text 已显式 codec-enhanced-plus 分支，覆盖 6 强制要点（codec_mode / CP56Time2a + ShortFloat / 7+ TypeID 矩阵 / QU 字段结构化 / 5 态 LinkLayer skeleton + FCB/FCV + timers / supports_server=false + supports_serial_runtime=false）。`test_iec101_codec.py` 中新增 codec-enhanced-plus mode 断言 + reason 文本一致性验证。**本项**不再列为风险。

**§7 后续工作（Round 21+ 计划项；Round 18 已收口 5 个新 IEC101 信息对象 + ScaledValue IE + QOS + Modbus register_encoding 工具；Round 19 已收口 3 个 C_SE_T* 带时标命令 + Modbus facade 接入 register_encoding 工具；**Round 20 已收口 Seahorse flaky 根因修复 + LinkLayer runtime skeleton（TimerService 抽象 + Default + Fake + balanced FCB auto flip + retry ERROR）+ ShortFloat 兼容（int/numbers.Real/`__float__` duck typing，**不引入 numpy 硬依赖**）**）**：

- 真实 IEC101 server（link_layer 真实串口 / 真实写能力 / persistent session；**当前 skeleton 不连接任何真实串口 / 字节流 / 网络 IO**）。
- Modbus 真实设备验证（`register_encoding_runtime=true` 升级，仅在真实 Modbus TCP/RTU 设备或 simulator server 接通后启用）。
- ~~ShortFloat numpy scalar 真实兼容~~（**Round 20 已收口**：duck typing 兼容 int / float / `numbers.Real` / `__float__`，**不引入 numpy 硬依赖**；**不**得再列 deferred；本轮文档已清理）。
- ~~LinkLayer 真实串口接入~~（**Round 20 已收口 runtime skeleton 形态**：TimerService 抽象 + Default threading.Timer + Fake 三实现 + 完整 send/receive/on_timeout 状态机 + balanced FCB auto flip + retry ERROR；**仅 skeleton 非 server**，**仍不**连接真实 socket/pty/serial；本轮文档已清理）。

**不得把 codec-enhanced-plus 写成完整 IEC101 server 或生产级实现**。

**third_party 放置约束执行结果**（Round 16/17 累积）：
- 未在 `third_party/` 下新增任何 C 源码或预编译库。
- `src/starfish/protocols/iec101/time.py` / `link_layer.py` / `information_object.py` / `information_elements.py` 均为纯 Python 实现，零外部依赖。
- import boundary 验证：starfish -> seahorse / whale.ingest / whale.shared.source 仍 15 tests 通过。

协议特征：纯 Python 实现，零外部二进制依赖，zero third_party 引入。不等同于完整 IEC 101 server。可在不依赖串口的单元测试中验证（**Round 19 累计 580+ IEC101 codec tests**：codec 40 + information_elements（含 ShortFloat/M_ME_TB_1/M_ME_TC_1/ScaledValue）+ asdu_objects（含 5 新对象 + QOS + 3 C_SE_T*）+ ft12_frame 36 + link_layer；**Round 19 累计 164 Modbus register encoding tests**；**Round 19 累计 1144 starfish + 15 architecture + 181 seahorse（180 stable + 1 pre-existing flaky）= 1339 stable passed**；**Round 20 累计 1215 starfish + 15 architecture + 186 seahorse（180 stable + 5 新 daily_power 稳定性测试 + 1 原 daily_power_preset，**`test_curve_daily_power_preset` 根因已修复，**不**再列 pre-existing flaky）= 1416 stable passed**；**Round 21 总收口测试统计定版 1416 stable passed / 0 failed / 0 flaky**）。

安全边界：不得 import seahorse / whale.ingest / whale.shared.source；不得 import `third_party.lib60870` 或任何第三方 IEC101 实现；所有数据标注 synthetic；不得 spawn 真实 C runner 子进程作为编解码主路径。

### SF-FR-023 GOOSE facade 与 environment-pending 定版

Starfish 提供 `GooseFacade`，继承 `ServerSimulatorFacade` in-memory stub 实现，作为 IEC 61850 GOOSE（Generic Object Oriented Substation Event）二层多播协议服务端模拟门面。

核心行为：

- **mode**：固定为 `"environment-pending"`。
- `start()`/`stop()`/`health()`/`load_points(plan)`/`read(point_ids=None)`/`update_values(values)`/`capabilities()` -- 继承 in-memory stub 实现。
- `dependency probe`：`probe_goose_binary()` 检测 go 二进制或 L2 veth 环境可用性。当前探测函数定义但默认返回 unavailable（L2 veth 网络未就绪）。

NOT_IMPLEMENTED：

- `write()` -- 抛出 `UnsupportedOperation("write", ...)`。
- `subscribe()` -- 抛出 `UnsupportedOperation("subscribe", ...)`。
- `report()` -- 抛出 `UnsupportedOperation("report", ...)`。

**environment-pending 定版说明**：

GOOSE 是 IEC 61850 定义的二层多播协议（Ethertype 0x88B8），需要 L2 veth 网络环境和 raw socket（CAP_NET_RAW）。`GooseFacade` 以 in-memory stub 定版，`ieee61850_goose_publisher_simulator.c` 已存在于 `third_party/libiec61850/`，但运行需要 L2 veth 环境。待环境就绪后可升级为 real mode。

**不得把 environment-pending 写成 PASS**。

协议特征：零外部二进制依赖（纯 Python stub），不等同于真实 GOOSE 发布设备。

安全边界：不得 import seahorse / whale.ingest / whale.shared.source；所有数据标注 synthetic。

### SF-FR-024 SV facade 与 environment-pending 定版

Starfish 提供 `SvFacade`，继承 `ServerSimulatorFacade` in-memory stub 实现，作为 IEC 61850 SV（Sampled Values）二层多播协议服务端模拟门面。

核心行为：

- **mode**：固定为 `"environment-pending"`。
- `start()`/`stop()`/`health()`/`load_points(plan)`/`read(point_ids=None)`/`update_values(values)`/`capabilities()` -- 继承 in-memory stub 实现。
- `dependency probe`：`probe_sv_binary()` 检测 go 二进制或 L2 veth 环境可用性。当前探测函数定义但默认返回 unavailable（L2 veth + PTP 时间同步未就绪）。

NOT_IMPLEMENTED：

- `write()` -- 抛出 `UnsupportedOperation("write", ...)`。
- `subscribe()` -- 抛出 `UnsupportedOperation("subscribe", ...)`。
- `report()` -- 抛出 `UnsupportedOperation("report", ...)`。

**environment-pending 定版说明**：

SV 是 IEC 61850 定义的二层多播采样值协议（Ethertype 0x88BA），需要 L2 veth 网络环境、raw socket（CAP_NET_RAW）和硬件 PTP（IEEE 1588）时间同步。`SvFacade` 以 in-memory stub 定版，`ieee61850_sv_publisher_simulator.c` 已存在于 `third_party/libiec61850/`，但运行需要 L2 veth + PTP 环境。待环境就绪后可升级为 real mode。

**不得把 environment-pending 写成 PASS**。

协议特征：零外部二进制依赖（纯 Python stub），不等同于真实 SV 发布设备（合并单元 MU）。

安全边界：不得 import seahorse / whale.ingest / whale.shared.source；所有数据标注 synthetic。

### SF-FR-025 native runner 管理框架

Starfish 提供统一的 native runner 管理框架（`src/starfish/native/`），包含 runner 规格定义、统一 binary 探查和子进程生命周期管理三个模块，供 OPC_UA/IEC104/IEC61850 等依赖 C runner 子进程的 protocol facade 使用。

**模块组成**：

1. **`runner_spec.py` — `NativeRunnerSpec` dataclass**：
   - 字段：`binary_path`（二进制路径）、`host`（监听地址）、`port`（监听端口）、`protocol`（协议标识）、`working_dir`（工作目录）、`env`（环境变量）、`startup_timeout`（启动超时秒数）、`ready_pattern`（READY 信号匹配规则）。
   - 纯 dataclass，无外部依赖，可序列化/反序列化。

2. **`runner_probe.py` — `probe_native_runner()`**：
   - 统一 binary 探测函数，接收 `NativeRunnerSpec` 或 binary path。
   - 探测序列：stat（文件存在性） -> st_size（>= 阈值，默认 1024 bytes） -> os.access(X_OK)（可执行权限）。
   - 返回 `(available: bool, reason: str)` 元组。
   - 探测失败时 reason 明确说清哪项检查失败（如 "binary not found" / "binary too small (N bytes)" / "binary not executable"）。

3. **`process_handle.py` — `NativeProcessHandle`**：
   - 封装子进程生命周期管理。
   - `start()`：`subprocess.Popen` 启动指定 binary，等待 READY 信号（读 stdout），设置 `_running=True`。
   - `stop()`：发送 SIGTERM（`terminate()`），等待最多 5 秒，超时后 SIGKILL（`kill()`），清理 PID 文件（`pid_file`）。
   - `health()`：检查 `_process.poll()` 是否为 None（进程仍在运行），是则返回 running。
   - `pid` 属性：返回子进程 PID（进程不存在时返回 None）。
   - `_cleanup_pid_file()`：内部方法，`stop()` 时自动清理 PID 文件。
   - 幂等安全：`start()` 已在运行时抛 `RuntimeError`；`stop()` 幂等。
   - 上下文管理器支持：`with NativeProcessHandle(...) as handle:`。

**安全边界**：

- 不得 import seahorse / whale.ingest / whale.shared.source。
- 本框架只提供底层通用原语，不自行启动 protocol server。
- 不连接生产二进制路径，所有路径由调用方显式传入。
- 子进程终止信号为 SIGTERM（默认 5 秒超时后 SIGKILL），不得使用 SIGKILL 作为首选。

**当前使用方**：OpcUaFacade、Iec104Facade、Iec61850MmsFacade、Iec61850ReportFacade 可迁移使用本框架统一管理子进程生命周期。当前 Round 10 native runner 框架已建立，但各 facade 尚未内部迁移至此框架（仍使用各自内部 subprocess.Popen 逻辑）。

### SF-AR-001 Starfish 是工具层 stub，不是完整协议 simulator

Starfish 当前（Round 10 收口时）实现状态：
- HTTP_REST 真实 server（ThreadingHTTPServer，GET /points）已实现（SF-FR-006）。
- MODBUS_TCP 真实 server（TCP socket，FC03/FC06）已实现，write 为真实 FC06（SF-FR-007）。
- MQTT lightweight JSON-line TCP facade（TCP socket, JSON-line pub, daemon accept）已实现（SF-FR-010）。不是完整 MQTT broker。
- subscribe 语义已实现（SF-FR-011，MqttFacade SubscriptionQueue queue.Queue）。
- OPC_UA real mode（open62541 C runner 子进程）已实现（SF-FR-015），不等同完整 OPC UA server。
- IEC104 real mode（iec104_simulator_server C runner 子进程）已实现（SF-FR-016），不等同完整 IEC 104 server。
- dependency probe 与 unavailable 语义已建立（SF-FR-017）。
- IEC61850 MMS real mode（iec61850_simulator_server C runner 子进程）已实现（SF-FR-018），read 为内存点位非真实 MMS 协议帧，不等同完整 IEC 61850 MMS server。
- IEC61850 Report real mode（iec61850_report_runner C runner 子进程）已实现（SF-FR-019），含 ReportQueue event 语义（put/get/drain/FIFO，events 来自 Python 侧），不等同完整 IEC 61850 Report server。
- IEC101 facade 已定版 + codec-enhanced（SF-FR-020/027/028，Iec101Facade mode="codec-enhanced" 默认（回退 codec-skeleton），TypeId/COT/ASDUHeader/IOA/CA 编解码 + SIQ/QDS/NVA + 4 信息对象 + ASDU 列表 SQ=0/SQ=1 + FT1.2 帧 + checksum 已实现；非完整 server，supports_server=false/supports_serial_runtime=false）。
- MODBUS_RTU facade 已定版（SF-FR-021，ModbusRtuFacade mode="codebase-pending"，串口/PTY 链路未就绪）。
- Beckhoff ADS facade 已定版（SF-FR-022，AdsFacade mode="codebase-pending"，.NET/TwinCAT runtime 未就绪）。
- GOOSE facade 已定版（SF-FR-023，GooseFacade mode="environment-pending"，L2 veth 网络未就绪）。
- SV facade 已定版（SF-FR-024，SvFacade mode="environment-pending"，L2 veth + PTP 时间同步未就绪）。
- native runner 管理框架已建立（SF-FR-025，NativeRunnerSpec + probe_native_runner + NativeProcessHandle）。
- probe/profile/capacity 最小工具层闭环已实现（SF-FR-012/013/014），已扩展至 12 协议（含 5 个 pending 协议 NOT_RUN）。
- `report` 语义已起步（IEC61850 Report facade ReportQueue），**不再是全 NOT_IMPLEMENTED**。
- HTTP_REST `write/subscribe`、MODBUS_TCP `subscribe`、MQTT `write`、OpcUaFacade `write/subscribe/report`、Iec104Facade `write/subscribe/report`、Iec61850MmsFacade `write/subscribe`、Iec61850ReportFacade `write/subscribe` 明确 NOT_IMPLEMENTED。
- Iec101Facade/ModbusRtuFacade/AdsFacade/GooseFacade/SvFacade `write/subscribe/report` 明确 NOT_IMPLEMENTED。
- 不连接真实现场设备。
- 不得写成 production source client。
- 不得伪装为完整多协议 simulator 完成状态。
- **不得把 unavailable/codebase-pending/environment-pending 写为 PASS。**

差距分析：

```text
IEC101 真实 server                   codebase-pending（facade stub 已定版，增强探测 lib60870/PTY，但无 ASDU/COT/IOA 帧编解码器）
Beckhoff ADS 真实 server            codebase-pending（facade stub 已定版，增强探测 dotnet/TwinCAT，但无 Python 原生 ADS 实现）
GOOSE 真实 server                   environment-pending（facade stub 已定版，需 L2 veth 环境）
SV 真实 server                      environment-pending（facade stub 已定版，需 L2 veth + PTP 时间同步）
report 语义                          已起步（IEC61850 Report facade ReportQueue），其余协议仍 NOT_IMPLEMENTED
MMS read                            codebase-pending（当前为内存点位，非真实 MMS 协议帧）
Report runner events                codebase-pending（当前来自 Python 侧，非子进程真实 report 数据）
MODBUS_RTU 真实串口现场              codebase-pending（rtu-lightweight 为 PTY 本地模拟，不等同 RS-232/RS-485 现场）
HTTP_REST write/subscribe           NOT_IMPLEMENTED（仅 GET 读取）
MODBUS_TCP subscribe                NOT_IMPLEMENTED
MQTT write                          NOT_IMPLEMENTED
OpcUaFacade write/subscribe/report  NOT_IMPLEMENTED
Iec104Facade write/subscribe/report NOT_IMPLEMENTED
Iec61850MmsFacade write/subscribe   NOT_IMPLEMENTED
Iec61850ReportFacade write/subscribe NOT_IMPLEMENTED
Iec101Facade write/subscribe/report NOT_IMPLEMENTED（codebase-pending）
AdsFacade write/subscribe/report    NOT_IMPLEMENTED（codebase-pending）
GooseFacade write/subscribe/report  NOT_IMPLEMENTED（environment-pending）
SvFacade write/subscribe/report     NOT_IMPLEMENTED（environment-pending）
native runner 迁移                   codebase-pending（框架已建立，各 facade 尚未内部迁移至此框架）
```

### SF-AR-002 Starfish 不 import seahorse/whale.ingest/whale.shared.source

硬边界约束，通过 AST 扫描 + grep 验证：

| 规则 | 方向 | 验证方式 | 状态 |
|---|---|---|---|
| starfish 不得 import seahorse | `starfish` -> `seahorse` | AST 扫描 | 通过（Round 9 验证，含新增 iec61850_mms_facade.py/iec61850_report_facade.py） |
| starfish 不得 import whale.ingest | `starfish` -> `whale.ingest` | AST 扫描 | 通过（Round 9 验证，含 2 个新增源文件） |
| starfish 不得 import whale.shared.source | `starfish` -> `whale.shared.source` | AST 扫描 | 通过（Round 9 验证，含 2 个新增源文件） |
| seahorse 不得 import starfish | `seahorse` -> `starfish` | AST 扫描 | 通过 |
| whale.ingest 不得 import starfish | `whale.ingest` -> `starfish` | AST 扫描 | 通过 |
| whale.ingest 不得 import seahorse | `whale.ingest` -> `seahorse` | AST 扫描 | 通过 |

Starfish 与 Seahorse 的交互仅通过读入纯 JSON 文件完成，双方均不得运行时 import 对方。

Starfish 与 whale.ingest / whale.shared.source 之间完全隔离，不得有任何运行时依赖。

### SF-AR-003 RuntimeRegistry 支持 real/stub 协议 dispatch

`RuntimeRegistry.create_facade_for_endpoint()` 根据 `endpoint.protocol` 分发到协议专用 facade：

- `HTTP_REST` -> `HttpRestFacade`（mode="real"，真实 ThreadingHTTPServer，SF-FR-006）
- `MODBUS_TCP` -> `ModbusTcpFacade`（mode="real"，真实 TCP socket server，SF-FR-007）
- `MQTT` -> `MqttFacade`（mode="mqtt-lightweight"，轻量 JSON-line TCP server，SF-FR-010）
- `OPC_UA` -> `OpcUaFacade`（mode="real" 或 "unavailable"，open62541 C runner 子进程，SF-FR-015）
- `IEC104` -> `Iec104Facade`（mode="real" 或 "unavailable"，iec104_simulator_server C runner 子进程，SF-FR-016）
- `IEC61850_MMS` -> `Iec61850MmsFacade`（mode="real" 或 "unavailable"，iec61850_simulator_server C runner 子进程，SF-FR-018）
- `IEC61850_Report` -> `Iec61850ReportFacade`（mode="real" 或 "unavailable"，iec61850_report_runner C runner 子进程，SF-FR-019）
- `IEC101`/`IEC_101` -> `Iec101Facade`（mode="codec-enhanced" 默认，回退 codec-skeleton，TypeId/COT/ASDUHeader/IOA/CA + SIQ/QDS/NVA + 4 信息对象 + ASDU 列表 SQ=0/SQ=1 + FT1.2 帧编解码已实现，SF-FR-020/027/028）
- `MODBUS_RTU` -> `ModbusRtuFacade`（mode="codebase-pending"，stub，串口/PTY 链路未就绪，SF-FR-021）
- `BECKHOFF_ADS`/`ADS` -> `AdsFacade`（mode="codebase-pending"，stub，.NET/TwinCAT runtime 未就绪，SF-FR-022）
- `GOOSE` -> `GooseFacade`（mode="environment-pending"，stub，L2 veth 网络未就绪，SF-FR-023）
- `SV` -> `SvFacade`（mode="environment-pending"，stub，L2 veth + PTP 时间同步未就绪，SF-FR-024）
- 其他协议 -> `ServerSimulatorFacade`（mode="stub"，in-memory fallback）

每个 facade 条目包含 `mode` 属性（"real"/"mqtt-lightweight"/"stub"/"unavailable"/"codec-enhanced"/"codec-skeleton"/"codebase-pending"/"environment-pending"/"rtu-lightweight"），供 CLI 和外部查询使用。OPC_UA/IEC104/IEC61850_MMS/IEC61850_Report 的 mode 由 dependency probe 动态确定（二进制存在 -> real，不存在 -> unavailable + reason）。IEC101 默认 "codec-enhanced"（增强编解码器就绪时），回退 "codec-skeleton"。MODBUS_RTU 为动态 dispatch（PTY 可用->rtu-lightweight，不可用->codebase-pending），Beckhoff_ADS 固定为 "codebase-pending"，GOOSE/SV 固定为 "environment-pending"。

RuntimeRegistry 新增 `_CODABASE_PENDING_PROTOCOLS` 和 `_ENVIRONMENT_PENDING_PROTOCOLS` 两个 frozenset，`get_supported_protocols()` 返回全部已注册 12 协议，新增 `get_codebase_pending_protocols()` 和 `get_environment_pending_protocols()` 查询函数。

## 6. 需求跟踪表

| 编号 | 上承需求 | 标题 | 类型 | 优先级 | 责任模块 | 验证等级 | 实现状态 | 实现证据 | 验收测试 | 差距 | 下一步 | 更新时间 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| SF-FR-001 | 总体逻辑设计 8.2/8.3 | ServerPlan JSON loader（9 项校验 + payload_hash 复算） | FR | 高 | starfish.loader | P1+P2 | 已完成 | `src/starfish/loader/server_plan_loader.py`；load_server_plan 支持文件加载、9 项校验（必填字段/schema_version/scenario_id/synthetic/endpoints/points/capabilities/initial_values/payload_hash 复算）、LoadResult/ValidationResult 结构化返回；边界错误 FileNotFoundError/JSONDecodeError/ValueError | `tests/unit/starfish/test_server_plan_loader.py` -> ~30 tests passed | 无立即差距；校验规则后续可按需扩展 | 持续维护 | 2026-06-04 |
| SF-FR-002 | 总体逻辑设计 8.2/8.3 | ServerSimulatorFacade 最小工具层生命周期（start/stop/health/read/load_points/update_values/capabilities） | FR | 高 | starfish.facade | P1 | 已完成 | `src/starfish/facade/server_simulator_facade.py`；in-memory stub 实现；7 个已实现方法：start/stop/health/load_points/read/update_values/capabilities；幂等安全 | `tests/unit/starfish/test_server_simulator_facade.py` -> ~30 tests passed | write/subscribe/report 为 NOT_IMPLEMENTED；真实协议 server 未启动 | Round 6+：按协议实现真实 server 启动 | 2026-06-04 |
| SF-FR-003 | 总体逻辑设计 8.2/8.3 | read initial_values（load_points 从 plan.initial_values 填充） | FR | 高 | starfish.facade | P1 | 已完成 | load_points 复制 plan.initial_values；read() 返回存储值；覆盖/空 initial_values/reload 场景通过 | `tests/unit/starfish/test_server_simulator_facade.py` -> read/load_points/initial_values 测试通过 | 无 | 无 | 2026-06-04 |
| SF-FR-004 | 总体逻辑设计 8.2 | unsupported write/subscribe/report 返回 NOT_IMPLEMENTED（UnsupportedOperation 异常） | FR | 高 | starfish.facade, starfish.models | P1 | 已完成 | `UnsupportedOperation` 自定义异常；write/subscribe/report 三个方法明确抛出 NOT_IMPLEMENTED 中文错误；CLI smoke 验证三项 | `tests/unit/starfish/test_server_simulator_facade.py` -> NOT_IMPLEMENTED 测试通过；`tests/unit/starfish/test_starfish_cli.py` -> smoke CLI 验证通过 | 不得伪装实现完成 | 待后续轮次实现后移除异常 | 2026-06-04 |
| SF-FR-005 | 总体逻辑设计 8.2/8.3 | CLI load-server-plan / smoke-server-plan（2 子命令） | FR | 高 | starfish.__main__ | P1 | 已完成 | `src/starfish/__main__.py`；load-server-plan（--input 加载+校验+输出报告）；smoke-server-plan（--input 全流程 smoke 含 NOT_IMPLEMENTED 验证 + per-endpoint mode 输出）；文件不存在/无效 JSON 返回非零 | `tests/unit/starfish/test_starfish_cli.py` -> ~20 tests passed | 无 | 后续可选增加更多子命令 | 2026-06-05 |
| SF-FR-006 | 总体逻辑设计 8.2/8.3 | HTTP_REST 真实 server 生命周期（ThreadingHTTPServer, GET /points） | FR | 高 | starfish.facade | P1 | 已完成 | `src/starfish/facade/http_rest_facade.py`；HttpRestFacade 使用 http.server.ThreadingHTTPServer 启动真实 HTTP 服务端；GET /points 返回 JSON；start/stop/health/load_points/read/update_values/capabilities 实现；write/subscribe/report 为 UnsupportedOperation | `tests/unit/starfish/test_protocol_facade.py` -> HttpRestFacade 测试通过（start/stop/health/read/initial_values/update_values/capabilities/NOT_IMPLEMENTED/real HTTP GET） | HTTP_REST write 为 NOT_IMPLEMENTED；subscribe/report 为 NOT_IMPLEMENTED | 后续按需实现 write 语义 | 2026-06-05 |
| SF-FR-007 | 总体逻辑设计 8.2/8.3 | MODBUS_TCP 真实 server 生命周期（TCP socket, FC03/FC06） | FR | 高 | starfish.facade | P1 | 已完成 | `src/starfish/facade/modbus_tcp_facade.py`；ModbusTcpFacade 使用 Python 标准库 socket 启动真实 TCP server；支持 FC03 Read Holding Registers（真实 Modbus 帧编码）和 FC06 Write Single Register（写入后 FC03 回读验证）；start/stop/health/load_points/read/write/update_values/capabilities 实现；subscribe/report 为 UnsupportedOperation | `tests/unit/starfish/test_protocol_facade.py` -> ModbusTcpFacade 测试通过（FC03/FC06 真实读写/start/stop/health/read/write/update_values/capabilities/NOT_IMPLEMENTED） | 未实现异常码完整矩阵/浮点寄存器/多单元 ID；subscribe/report 为 NOT_IMPLEMENTED | 后续按需扩展 Modbus 功能码和异常码 | 2026-06-05 |
| SF-FR-008 | 总体逻辑设计 8.2/8.3 | RuntimeRegistry 协议 dispatch + native runner dispatch（real/stub/unavailable 三模式） | FR | 高 | starfish.registry | P1 | 已完成（Round 9 更新） | `src/starfish/registry/runtime_registry.py`；create_facade_for_endpoint 根据 protocol 分发：HTTP_REST->HttpRestFacade（mode="real"）、MODBUS_TCP->ModbusTcpFacade（mode="real"）、MQTT->MqttFacade（mode="mqtt-lightweight"）、OPC_UA->OpcUaFacade（mode="real"|"unavailable"）、IEC104->Iec104Facade（mode="real"|"unavailable"）、IEC61850_MMS->Iec61850MmsFacade（mode="real"|"unavailable"）、IEC61850_Report->Iec61850ReportFacade（mode="real"|"unavailable"）、其他->ServerSimulatorFacade（mode="stub"）；_NATIVE_RUNNER_PROTOCOLS dispatch 表；get_supported_protocols 返回 ["HTTP_REST", "MODBUS_TCP", "MQTT", "OPC_UA", "IEC104", "IEC61850_MMS", "IEC61850_Report"] | `tests/unit/starfish/test_protocol_facade.py` -> registry dispatch 通过（~42 tests，含 OPC_UA/IEC104/IEC61850_MMS/IEC61850_Report real/unavailable dispatch）；`tests/unit/starfish/test_opcua_iec104_facade.py` -> 58 tests；`tests/unit/starfish/test_iec61850_facade.py` -> 71 tests | 其他协议真实 server 启动为 codebase-pending | 后续按协议增加 real mode factory | 2026-06-05 |
| SF-FR-009 | 总体逻辑设计 8.2/8.3 | smoke-server-plan per-endpoint mode 输出 | FR | 高 | starfish.__main__ | P1 | 已完成 | `src/starfish/__main__.py` _run_smoke；按 endpoint 输出 protocol/point_count/capabilities/mode/reason；stub mode 时额外验证 NOT_IMPLEMENTED 三项 | `tests/unit/starfish/test_starfish_cli.py` -> smoke 含 mode 输出验证通过 | 无 | 持续维护 | 2026-06-05 |
| SF-FR-010 | 总体逻辑设计 8.2/8.3 | MQTT lightweight JSON-line TCP facade（不是完整 MQTT broker） | FR | 高 | starfish.facade | P1 | 已完成 | `src/starfish/facade/mqtt_facade.py`；MqttFacade 使用 Python 标准库 socket bind/listen/accept daemon 线程 TCP server；JSON-line 通信；SubscriptionQueue 封装 queue.Queue；start/stop/health/load_points/read/update_values/capabilities/subscribe 实现；write/report 为 UnsupportedOperation | `tests/unit/starfish/test_mqtt_facade.py` -> 37 tests passed（SubscriptionQueue/lifecycle/data/subscribe/NOT_IMPLEMENTED/TCP protocol/smoke flow） | MQTT 不等同于完整 MQTT broker（无 CONNECT/CONNACK/QoS/topic tree/retained/session）；write 为 NOT_IMPLEMENTED；report 为 NOT_IMPLEMENTED | 后续按需扩展为标准 MQTT v3.1.1 broker | 2026-06-05 |
| SF-FR-011 | 总体逻辑设计 8.2/8.3 | subscribe 语义 — SubscriptionQueue（queue.Queue 封装） | FR | 高 | starfish.facade | P1 | 已完成 | `MqttFacade.subscribe` 返回 `SubscriptionQueue`（queue.Queue 封装）；update_values 后通知所有匹配 subscriber；TCP publish 触发 subscribe 通知；多个独立 subscriber 各自接收；load_points 清空旧订阅；get/get_nowait 阻塞/非阻塞取 | `tests/unit/starfish/test_mqtt_facade.py` -> TestMqttFacadeSubscribe 7 tests passed（subscribe queue/update notify/multiple points/unrelated filter/multiple subscribers/clear on reload/TCP publish sync） | 当前仅 MqttFacade 实现 subscribe；HttpRestFacade/ModbusTcpFacade/ServerSimulatorFacade subscribe 仍为 UnsupportedOperation | 后续扩展其他 facades 的 subscribe 语义 | 2026-06-05 |
| SF-FR-012 | 总体逻辑设计 8.2 | probe 最小工具能力（启动-健康-读取探测，已扩展至 OPC_UA/IEC104/IEC61850） | FR | 高 | starfish.tools | P1 | 已完成（Round 9 更新） | `src/starfish/tools/probe.py`；run_probe 对 facade 执行 start/health/read 探测序列；ProbeResult dataclass；支持 skip_start；OPC_UA/IEC104/IEC61850 real mode 时 PASS，unavailable 时 NOT_RUN + reason | `tests/unit/starfish/test_probe_profile_capacity.py` -> probe 部分 ~15 tests passed（stub/http_rest/modbus/mqtt/opcua/iec104/iec61850_mms/iec61850_report/specific_points/skip_start） | 不等同生产级诊断工具 | 持续维护 | 2026-06-05 |
| SF-FR-013 | 总体逻辑设计 8.2 | profile 最小工具能力（read N 次采样耗时统计，已扩展至 OPC_UA/IEC104/IEC61850） | FR | 高 | starfish.tools | P1 | 已完成（Round 9 更新） | `src/starfish/tools/profile.py`；run_profile 对 facade 执行 iterations 次 read 统计耗时；OPC_UA/IEC104/IEC61850 real mode 时 PASS，unavailable 时 NOT_RUN + reason | `tests/unit/starfish/test_probe_profile_capacity.py` -> profile 部分 ~10 tests passed（stub/http_rest/mqtt/opcua/iec104/iec61850_mms/iec61850_report/zero_iterations） | 不等同生产级性能测试 | 持续维护 | 2026-06-05 |
| SF-FR-014 | 总体逻辑设计 8.2 | capacity 最小工具能力（端点/点位/读取容量扫描，已扩展至 OPC_UA/IEC104/IEC61850） | FR | 高 | starfish.tools | P1 | 已完成（Round 9 更新） | `src/starfish/tools/capacity.py`；run_capacity 对 facade 执行轻量容量扫描；支持 HTTP_REST/MODBUS_TCP/MQTT/OPC_UA/IEC104/IEC61850_MMS/IEC61850_Report | `tests/unit/starfish/test_probe_profile_capacity.py` -> capacity 部分 ~11 tests passed（http_rest/modbus/mqtt/opcua/iec104/iec61850_mms/iec61850_report/unsupported_protocol/zero_points） | 不等同生产容量验收或压测 | 持续维护 | 2026-06-05 |
| SF-FR-015 | 总体逻辑设计 8.2/8.3 | OPC_UA real mode — open62541 C runner 子进程（dependency probe + start/stop/health/read） | FR | 高 | starfish.facade | P1 | 已完成 | `src/starfish/facade/opcua_facade.py`；OpcUaFacade 使用 open62541 C runner 子进程；dependency probe 检测二进制存在性；mode="real"|"unavailable"；start->subprocess.Popen->READY signal->TCP connect；幂等安全；write/subscribe/report 为 UnsupportedOperation | `tests/unit/starfish/test_opcua_iec104_facade.py` -> OpcUaFacade 测试通过（start/stop/health/dependency probe/unavailable/reason/subprocess Popen/READY/TCP connect/NOT_IMPLEMENTED）；`tests/unit/starfish/test_protocol_facade.py` -> registry dispatch OPC_UA real/unavailable | write/subscribe/report NOT_IMPLEMENTED；不等同完整 OPC UA server | 后续按需扩展 read 真实 OPC UA 数据交换 | 2026-06-05 |
| SF-FR-016 | 总体逻辑设计 8.2/8.3 | IEC104 real mode — iec104_simulator_server C runner 子进程（dependency probe + start/stop/health/read） | FR | 高 | starfish.facade | P1 | 已完成 | `src/starfish/facade/iec104_facade.py`；Iec104Facade 使用 iec104_simulator_server C runner 子进程；dependency probe 检测二进制存在性；mode="real"|"unavailable"；start->subprocess.Popen->READY signal；幂等安全；write/subscribe/report 为 UnsupportedOperation | `tests/unit/starfish/test_opcua_iec104_facade.py` -> Iec104Facade 测试通过（start/stop/health/dependency probe/unavailable/reason/subprocess Popen/READY/NOT_IMPLEMENTED）；`tests/unit/starfish/test_protocol_facade.py` -> registry dispatch IEC104 real/unavailable | write/subscribe/report NOT_IMPLEMENTED；不等同完整 IEC 104 server | 后续按需扩展 read 真实 IEC 104 数据交换 | 2026-06-05 |
| SF-FR-017 | 总体逻辑设计 8.2 | dependency probe 与 unavailable 语义（二进制探测 + 文件大小 + 可执行权限） | FR | 高 | starfish.facade | P1 | 已完成（Round 9 更新） | `OpcUaFacade.probe_opcua_binary()`、`Iec104Facade.probe_iec104_binary()`、`Iec61850MmsFacade.probe_iec61850_binary()`、`Iec61850ReportFacade.probe_iec61850_binary()` 使用 os.stat + os.access 检测；mode="unavailable" 时 start/stop 不执行子进程；probe/profile/capacity 返回 NOT_RUN + reason | `tests/unit/starfish/test_opcua_iec104_facade.py` -> dependency probe 测试通过（存在/不存在/太小/不可执行/unavailable reason）；`tests/unit/starfish/test_iec61850_facade.py` -> dependency probe 测试通过；`tests/unit/starfish/test_probe_profile_capacity.py` -> probe/profile/capacity OPC_UA/IEC104/IEC61850 PASS + NOT_RUN | 不得把 unavailable 写为 PASS | 持续维护依赖探测逻辑 | 2026-06-05 |
| SF-FR-018 | 总体逻辑设计 8.2/8.3 | IEC61850 MMS real mode -- iec61850_simulator_server C runner 子进程（dependency probe + start/stop/health/read 内存点位） | FR | 高 | starfish.facade | P1 | 已完成 | `src/starfish/facade/iec61850_mms_facade.py`；Iec61850MmsFacade 使用 iec61850_simulator_server C runner 子进程（27144 bytes）；dependency probe 检测二进制存在性；mode="real"|"unavailable"；start->subprocess.Popen->READY signal->TCP connect；幂等安全；read 为内存点位（非真实 MMS 协议帧）；write/subscribe 为 UnsupportedOperation | `tests/unit/starfish/test_iec61850_facade.py` -> Iec61850MmsFacade 测试通过（start/stop/health/dependency probe/unavailable/reason/subprocess Popen/READY/TCP connect/NOT_IMPLEMENTED write/subscribe）；`tests/unit/starfish/test_protocol_facade.py` -> registry dispatch IEC61850_MMS real/unavailable；`tests/unit/starfish/test_probe_profile_capacity.py` -> probe/profile/capacity IEC61850_MMS PASS/NOT_RUN | MMS read 为内存点位非真实协议帧；write/subscribe NOT_IMPLEMENTED；不等同完整 IEC 61850 MMS server | 后续按需实现真实 MMS 协议帧 read | 2026-06-05 |
| SF-FR-019 | 总体逻辑设计 8.2/8.3 | IEC61850 Report real mode + ReportQueue event 语义（iee61850_report_runner C runner 子进程 + ReportQueue put/get/drain/FIFO） | FR | 高 | starfish.facade | P1 | 已完成 | `src/starfish/facade/iec61850_report_facade.py`；Iec61850ReportFacade 使用 iec61850_report_runner C runner 子进程（26568 bytes）；dependency probe 检测二进制存在性；mode="real"|"unavailable"；start->subprocess.Popen->READY signal；ReportQueue 封装 queue.Queue（put/get/get_nowait/drain/FIFO）；events 来自 Python 侧（非子进程真实 report 数据）；write/subscribe 为 UnsupportedOperation | `tests/unit/starfish/test_iec61850_facade.py` -> Iec61850ReportFacade 测试通过（start/stop/health/dependency probe/unavailable/reason/ReportQueue put/get/drain/FIFO/NOT_IMPLEMENTED write/subscribe）；`tests/unit/starfish/test_protocol_facade.py` -> registry dispatch IEC61850_Report real/unavailable；`tests/unit/starfish/test_probe_profile_capacity.py` -> probe/profile/capacity IEC61850_Report PASS/NOT_RUN | report runner 子进程在 real mode 测试中未实际启动（events 来自 Python 侧）；write/subscribe NOT_IMPLEMENTED；不等同完整 IEC 61850 Report server | 后续按需实现子进程真实 report 数据流 | 2026-06-05 |
| SF-FR-020 | 总体逻辑设计 8.2 | IEC101 facade 与 codec-enhanced mode（含 SIQ/QDS/NVA/M_SP_NA_1/M_DP_NA_1/M_ME_NA_1/C_SC_NA_1/ASDU 列表 SQ=0/SQ=1/FT1.2 帧/codec_capabilities 显式声明） | FR | 中 | starfish.facade | P1 | 已完成（Round 15 升级为 codec-enhanced） | `src/starfish/facade/iec101_facade.py`；Iec101Facade in-memory stub；mode 动态判定（codec-enhanced/codec-skeleton/environment-pending/codebase-pending 4 级）；health() 含增强诊断（pty_available/lib60870_exists/iec101 binaries/codec_skeleton_ready/codec_enhanced_ready）；codec_capabilities() 返回 [codec_mode, supported_type_ids, supports_ft12_frame_codec, supports_server=false, supports_serial_runtime=false]；probe_iec101_codec_enhanced() 验证信息体/对象/列表/帧/校验和全部可用 | `tests/unit/starfish/test_remaining_protocols.py` -> Iec101Facade 测试通过（stub lifecycle + NOT_IMPLEMENTED + mode 验证）；`tests/unit/starfish/test_iec101_codec.py` -> 40 tests；`test_iec101_information_elements.py` -> 24 tests；`test_iec101_asdu_objects.py` -> 38 tests；`test_iec101_ft12_frame.py` -> 36 tests（138 IEC101 codec tests passed） | 无串口通信层、无 IEC 60870-5-101 状态机、无平衡/非平衡模式、CP56Time2a 时标 IE deferred、QU 字段语义简化 | 待后续实现串口通信层+状态机+CP56Time2a IE 后升级为 real mode | 2026-06-06 |
| SF-FR-021 | 总体逻辑设计 8.2 | MODBUS_RTU rtu-lightweight PTY-backed real mode（含 CRC16/8 FCs/4 异常码） | FR | 高 | starfish.facade | P1 | 已完成（Round 14 升级） | `src/starfish/facade/modbus_rtu_facade.py`；ModbusRtuFacade 使用 pty.openpty() PTY pair 实现两模式 dispatch（PTY 可用→rtu-lightweight，不可用→codebase-pending）；CRC16 标准算法（0xA001 多项式）；8 个功能码覆盖全部 4 个数据区（Coils: FC01/FC05/FC15；Discrete Inputs: FC02；Input Registers: FC04；Holding Registers: FC03/FC06/FC16）；4 个异常码（0x01-0x04）支持；PTY 生命周期（openpty/start/stop/health）；write(read) 线程安全 | `tests/unit/starfish/test_modbus_rtu_facade.py` -> 76 tests passed（CRC16 5 向量/8 FCs 帧编解码/异常码 0x01-0x04/PTY 生命周期/两模式 dispatch/codebase-pending fallback/NOT_IMPLEMENTED subscribe/report） | PTY 不等同真实串口（无 RS-232/RS-485 电气特性、波特率、奇偶校验、停止位）；帧边界通过 CRC 逐字节探测模拟（非真实 3.5 字符间隔）；未实现浮点/32-bit 寄存器编解码、多从站 ID、广播地址支持 | 真实串口现场验证需 RS-232/RS-485 硬件环境 | 2026-06-06 |
| SF-FR-022 | 总体逻辑设计 8.2 | Beckhoff ADS facade 与 codebase-pending 定版（含增强探针） | FR | 中 | starfish.facade | P1 | 已完成（Round 13 增强探测） | `src/starfish/facade/ads_facade.py`；AdsFacade in-memory stub；mode="codebase-pending"；health() 含增强诊断（dotnet_available/dotnet_path/TwinCAT 环境变量）；probe_ads_binary() 增强：探测 dotnet CLI 可用性 (shutil.which) + native/bin/ ADS binary + TwinCAT 环境变量（TWINCAT_DIR/TWINCAT3_DIR/TC_REGISTRY/ADS_AMS_NET_ID）；始终返回 (False, reason) 因为无 Python 原生 ADS 实现 | `tests/unit/starfish/test_remaining_protocols.py` -> AdsFacade 测试通过（stub lifecycle + NOT_IMPLEMENTED + mode 验证） | .NET/TwinCAT runtime 未就绪（Linux 环境不可用）；无 Python 原生 ADS 实现（需 AMS NetId 配置、ADS 路由、TwinCAT ADS 库） | 待 .NET runtime 环境或 Python 原生实现就绪后升级为 real mode | 2026-06-05 |
| SF-FR-023 | 总体逻辑设计 8.2 | GOOSE facade 与 environment-pending 定版 | FR | 中 | starfish.facade | P1 | 已完成 | `src/starfish/facade/goose_facade.py`；GooseFacade 继承 ServerSimulatorFacade in-memory stub；mode="environment-pending"；GooseFacade lifecycle (start/stop/health/read/load_points/update_values/capabilities) 继承 in-memory stub；write/subscribe/report 为 NOT_IMPLEMENTED；probe_goose_binary 探测函数定义 | `tests/unit/starfish/test_remaining_protocols.py` -> GooseFacade 测试通过（stub lifecycle + NOT_IMPLEMENTED + mode 验证）；`tests/unit/starfish/test_iec61850_facade.py` -> GOOSE/SV stub -> environment-pending | L2 veth 网络环境未就绪（需 raw socket CAP_NET_RAW）；ieee61850_goose_publisher_simulator.c 已存在于 third_party/ | 待 L2 veth 环境就绪后升级为 real mode | 2026-06-05 |
| SF-FR-024 | 总体逻辑设计 8.2 | SV facade 与 environment-pending 定版 | FR | 中 | starfish.facade | P1 | 已完成 | `src/starfish/facade/sv_facade.py`；SvFacade 继承 ServerSimulatorFacade in-memory stub；mode="environment-pending"；SvFacade lifecycle (start/stop/health/read/load_points/update_values/capabilities) 继承 in-memory stub；write/subscribe/report 为 NOT_IMPLEMENTED；probe_sv_binary 探测函数定义 | `tests/unit/starfish/test_remaining_protocols.py` -> SvFacade 测试通过（stub lifecycle + NOT_IMPLEMENTED + mode 验证） | L2 veth + PTP 时间同步环境未就绪（需 raw socket CAP_NET_RAW + IEEE 1588）；ieee61850_sv_publisher_simulator.c 已存在于 third_party/ | 待 L2 veth + PTP 环境就绪后升级为 real mode | 2026-06-05 |
| SF-FR-025 | 总体逻辑设计 8.2 | native runner 管理框架（NativeRunnerSpec + probe_native_runner + NativeProcessHandle） | FR | 高 | starfish.native | P1 | 已完成 | `src/starfish/native/runner_spec.py` — NativeRunnerSpec dataclass；`src/starfish/native/runner_probe.py` — probe_native_runner() 统一 binary 探测；`src/starfish/native/process_handle.py` — NativeProcessHandle 子进程生命周期管理（start/stop/health/pid/pid_file cleanup）；所有函数中英文 docstring 完整 | `tests/unit/starfish/test_native_runner_framework.py` -> 66 tests passed（NativeRunnerSpec 构造/字段/序列化；probe_native_runner 二元/缺失/太小/不可执行/unavailable reason；NativeProcessHandle start/stop/health/pid/pid_file/cleanup/lifecycle edge cases/subprocess integration） | 各 facade 尚未内部迁移至此框架（仍使用各自 subprocess.Popen 逻辑） | 后续逐协议迁移 facade 子进程管理层至 native runner 框架 | 2026-06-05 |
| SF-FR-026 | 总体逻辑设计 8.2 | MODBUS_RTU rtu-lightweight PTY-backed real mode（CRC16/8 FCs/4 异常码） | FR | 高 | starfish.facade | P1 | 已完成（Round 14 升级） | `src/starfish/facade/modbus_rtu_facade.py`；CRC16 标准算法（0xA001 多项式 5 个已知向量）；8 个功能码覆盖全部 4 个数据区；4 个异常码（0x01-0x04）；pty.openpty() PTY 生命周期（openpty/start/stop/health）；两模式 dispatch（PTY 可用→rtu-lightweight，不可用→codebase-pending） | `tests/unit/starfish/test_modbus_rtu_facade.py` -> 76 tests passed（CRC16 5 向量/8 FCs 帧编解码/异常码 0x01-0x04/PTY 生命周期/两模式 dispatch/codebase-pending fallback/NOT_IMPLEMENTED subscribe/report） | PTY 不等同真实串口（无 RS-232/RS-485 电气特性/波特率/奇偶校验/停止位）；帧边界 CRC 逐字节探测（非 3.5 字符间隔）；未实现浮点/32-bit 寄存器编解码/多从站 ID/广播地址支持 | 真实串口现场验证需 RS-232/RS-485 硬件 | 2026-06-06 |
| SF-FR-027 | 总体逻辑设计 8.2 | IEC101 codec-skeleton -- TypeId/COT/ASDUHeader/IOA/CA 编解码骨架 | FR | 高 | starfish.protocols.iec101 | P1 | 已完成（Round 14 新增，Round 15 文档统一为实测 26 values） | `src/starfish/protocols/iec101/` 含 types.py(TypeId 26/COT 26 枚举，实测)、asdu.py(ASDUHeader 6 bytes encode/decode)、ioa.py(IOA 3 bytes encode/decode)、common_address.py(CA 2 bytes encode/decode)；纯 Python 实现，zero external dependency | `tests/unit/starfish/test_iec101_codec.py` -> 40 tests passed（TypeId/COT 枚举值验证 + ASDUHeader/IOA/CA encode/decode + 边界） | 无串口通信层、无链路层控制字段、无 IEC 60870-5-101 状态机、无完整 server 生命周期；非完整 IEC101 server | 待后续实现完整串口通信层和状态机后可与 facade 集成为完整 IEC101 server | 2026-06-06 |
| SF-FR-028 | 总体逻辑设计 8.2 | IEC101 codec-enhanced -- 信息体 + ASDU 列表 SQ=0/SQ=1 + FT1.2 帧 + checksum | FR | 高 | starfish.protocols.iec101, starfish.facade | P1 | 已完成（Round 15 新增） | `src/starfish/protocols/iec101/quality.py` SIQ/QDS 质量描述符 + `information_elements.py` NVA 归一化值（16-bit signed，[-1.0, +1.0-1/32768]）+ `information_object.py` M_SP_NA_1/M_DP_NA_1/M_ME_NA_1/C_SC_NA_1 信息对象 + `codec.py` ASDU 信息对象列表编解码（SQ=0 独立地址/SQ=1 顺序地址 + UnknownAsduError 安全解码）+ `frame.py` FT1.2 固定/可变帧 + checksum + 长度不一致检测；`Iec101Facade.codec_capabilities()` 返回 codec_mode/supported_type_ids/supports_ft12_frame_codec=true/supports_server=false/supports_serial_runtime=false | `tests/unit/starfish/test_iec101_information_elements.py` -> 24 tests（NVA encode/decode roundtrip/边界/容差）+ `test_iec101_asdu_objects.py` -> 38 tests（4 信息对象 roundtrip/SIQ/QDS/C_SC_NA_1 QU/ASDU 列表 SQ=0/SQ=1/UnknownAsduError 容错）+ `test_iec101_ft12_frame.py` -> 36 tests（FixedFrame/VariableFrame encode/decode/checksum compute/verify/长度不一致检测/FrameError）；138 IEC101 codec tests passed | 4 TypeId 限制（M_SP_NA_1/M_DP_NA_1/M_ME_NA_1/C_SC_NA_1）；QU 字段语义简化；CP56Time2a 7 字节时标 IE 显式 deferred；非完整 server（supports_server=false/supports_serial_runtime=false）；不平衡/非平衡状态机未实现 | 待 Round 16 补齐 CP56Time2a IE + 带时标 TypeId + 链路层最小状态机 | 2026-06-06 |
| SF-FR-029 | 总体逻辑设计 8.2 | IEC101 codec-enhanced-plus -- CP56Time2a 7 字节时标 IE + **17 TypeID 矩阵（Round 19 扩展 14 → 17：4 不带时标监视 + 1 不带时标标度化 + 1 不带时标短浮点 + 4 不带时标命令 + 3 带时标命令 C_SE_TA_1/C_SE_TB_1/C_SE_TC_1（Round 19 新增）+ 5 带时标监视 = 17 个；以 capability 实际值 17 为准，严禁硬写 13/14/15/18）** + ShortFloat IEEE 754 32-bit IE + ScaledValue IE（16-bit signed，Round 18 新增）+ QOS 结构化（SetPointQualifier 枚举 + SetPointCommandQualifier dataclass，Round 18 新增）+ C_SC_NA_1 QU 显式化（CommandPulse + SingleCommandQualifier 子字段 select_execute/qualifier/ql_value/persistent/pulse）+ 5 态链路层 skeleton（IDLE/WAIT_ACK/SEND/RECEIVE/ERROR）+ LinkLayerTimers + t1/t2/t3 + FCB/FCV helper + balanced/unbalanced 差异化 + **supports_command_codec=true / supports_scaled_value=true / supports_write_runtime=false（Round 18 新增）** + **supports_time_tagged_command_codec=true / supported_command_type_ids=7 / supported_time_tagged_command_type_ids=3 / supported_time_tagged_type_ids=8（Round 19 新增）** | FR | 高 | starfish.protocols.iec101, starfish.facade | P1 | 已完成（Round 16 起步，Round 17 一次性收口，Round 18 扩展 14，Round 19 扩展 17） | Round 19 增量：`information_object.py` 扩展 **C_SE_TA_1_Object**（TypeId=58，**12 字节 = NVA(2)+QOS(1)+CP56Time2a(7)**，IEC 60870-5-101 §7.2.6.9 对齐，**Round 19 新增**）+ **C_SE_TB_1_Object**（TypeId=59，**12 字节 = SVA(2)+QOS(1)+CP56Time2a(7)**，IEC 60870-5-101 §7.2.6.10 对齐，**Round 19 新增**）+ **C_SE_TC_1_Object**（TypeId=60，**14 字节 = ShortFloat(4)+QOS(1)+CP56Time2a(7)**，IEC 60870-5-101 §7.2.6.11 对齐，**Round 19 新增**）；`codec.py` 扩展 3 个新带时标命令信息对象到 `_TYPE_ID_OBJECT_SIZE` dispatcher；`Iec101Facade.codec_capabilities()` 显式 `supported_command_type_ids` 从 4 升级至 7（`C_SC_NA_1+C_SE_NA_1+C_SE_NB_1+C_SE_NC_1+C_SE_TA_1+C_SE_TB_1+C_SE_TC_1`，以 capability 实际值 7 为准）+ `supported_time_tagged_command_type_ids=C_SE_TA_1,C_SE_TB_1,C_SE_TC_1`（Round 19 新增，3 个）+ `supported_time_tagged_type_ids` 从 5 升级至 8（5 既有 + 3 新 C_SE_T*）+ `supports_time_tagged_command_codec=true`（Round 19 新增）+ 维持 `supports_write_runtime=false`（**Iec101Facade.write/subscribe/report 仍抛 UnsupportedOperation**）；`Iec101Facade.health()` reason_text 同步 codec-enhanced-plus 17 TypeId 分支 + `codec_enhanced_plus_ready` 诊断字段同步；`probe_iec101_codec_enhanced_plus()` 验证 17 TypeId 矩阵；Round 18 既有：ScaledValue IE（16-bit signed）+ 5 个新信息对象（M_ME_NB_1/M_ME_NC_1/C_SE_NA_1/C_SE_NB_1/C_SE_NC_1）+ SetPointQualifier/SetPointCommandQualifier + capabilities 显式分组；Round 17 既有：CP56Time2a + ShortFloat + M_ME_TB_1/M_ME_TC_1 + QU 显式化 + 5 态 LinkLayer + FCB/FCV + timers + health() reason_text 修复；Round 16 起步：3 带时标 TypeID + LinkLayer 骨架；**Round 20 增量**（已收口）：`link_layer.py` 扩展 `LinkLayerTimerService` 抽象 + `DefaultLinkLayerTimerService`（threading.Timer）+ `FakeLinkLayerTimerService` 三实现 + `start_timer` / `cancel_timer` / `cancel_all` / `on_timeout` API + 完整 send/receive/on_timeout 状态机 + **balanced FCB auto flip**（ACK+FCV=1+mode=BALANCED 自动翻；NACK/timeout/FCV disabled/unbalanced **不**翻）+ `retry_count > max_retries` 进入 `ERROR` + 默认 `enable_timers=False` 保持 Round 17 行为 + `information_elements.py` ShortFloat duck typing 兼容（int / `numbers.Real` / `__float__`） + 3 新 capabilities 显式（`supports_link_layer_timers=true` / `supports_balanced_fcb_auto_flip=true` / `supports_retry_skeleton=true`） | `tests/unit/starfish/test_iec101_asdu_objects.py`（**Round 19 扩展 +6 个 C_SE_T* test classes**：test_c_se_ta_1_roundtrip + test_c_se_tb_1_roundtrip + test_c_se_tc_1_roundtrip + test_c_se_t_a_byte_layout + test_c_se_t_b_byte_layout + test_c_se_t_c_byte_layout 验证 12/12/14 字节布局与 COT 字段）+ `tests/unit/starfish/test_iec101_codec.py`（**Round 19 增 TestIec101CodecRound19 class**：capabilities 17/7/3 数字断言 + supported_time_tagged_command_type_ids 断言 + supports_time_tagged_command_codec 断言）+ 既有 Round 16/17/18 测试 + **Round 20 增 TestIec101CodecRound20**：3 新 capabilities 数字断言 + reason_text 7 强制要点验证；`test_iec101_link_layer.py` 增 8 个 test classes（LinkLayerTimerService + Default + Fake + balanced FCB auto flip + retry ERROR + sequence 状态机）；`test_iec101_information_elements.py` 增 TestShortFloatRound20Compat（int / Decimal / Fraction / `__float__` duck typing 4 路输入）；580+ IEC101 codec tests passed | 链路层 skeleton 仅 5 态（不实现真实计时器线程 / **balanced FCB 自动翻转已 Round 20 收口（**仅规则**；不连接 socket/pty/serial）** / persistent session）；**不是** IEC101 server / 真实串口 / 完整链路层 / 真实 write runtime；ShortFloat **Round 20 已收口 duck typing 兼容**（int / float / `numbers.Real` / `__float__`，**不引入 numpy 硬依赖**）；**C_SE_T* command codec 不得被高估为真实写能力，Iec101Facade.write() 仍抛 UnsupportedOperation** | 真实 IEC101 server + Modbus 真实设备验证（真实串口 / 现场设备 / 完整 balanced/unbalanced runtime 仍 deferred） | 2026-06-07 |
| SF-AR-001 | 总体逻辑设计 2.1/8.2/8.3 | Starfish 是工具层 stub，不是完整协议 simulator | AR | 高 | 全组件 | P2 | 已建立并通过（**Round 18 扩展 + Round 19 扩展 + Round 20 增强 + Round 21 总收口**） | `__init__.py` 明确声明可用能力和 NOT_IMPLEMENTED；HTTP_REST/MODBUS_TCP/MQTT/OPC_UA/IEC104/IEC61850_MMS/IEC61850_Report 为 real mode，MODBUS_RTU 为 rtu-lightweight mode（8 FCs + 4 异常码，不等同真实串口），IEC101 为 codec-enhanced-plus mode（**Round 17 一次性收口 + Round 18 扩展 + Round 19 扩展 + Round 20 增强**：ShortFloat IEEE 754 + ShortFloat **duck typing 兼容**（Round 20 收口） + M_ME_TB_1/M_ME_TC_1 + QU 显式化 + 5 态 LinkLayer skeleton + FCB/FCV + timers + balanced/unbalanced 差异化 + **LinkLayerTimerService 抽象 + Default (threading.Timer) + Fake 三实现 + 完整 send/receive/on_timeout 状态机 + balanced FCB auto flip（Round 20 收口） + retry ERROR（Round 20 收口）** + **17 TypeID 矩阵（Round 19 扩展：4 不带时标监视 + 1 不带时标标度化 M_ME_NB_1 + 1 不带时标短浮点 M_ME_NC_1 + 4 不带时标命令 C_SC_NA_1/C_SE_NA_1/C_SE_NB_1/C_SE_NC_1 + 3 带时标命令 C_SE_TA_1/C_SE_TB_1/C_SE_TC_1（Round 19 收口）+ 5 带时标监视 = 17；以 capability 实际值 17 为准，严禁硬写 13/14/15/18）** + ScaledValue IE 16-bit signed + QOS 结构化 SetPointQualifier/SetPointCommandQualifier + supports_short_float=true/supports_link_layer_skeleton=true/supports_command_codec=true/supports_scaled_value=true/supports_write_runtime=false/supports_server=false/supports_serial_runtime=false/supports_time_tagged_command_codec=true（Round 19 收口）+ **supports_link_layer_timers=true/supports_balanced_fcb_auto_flip=true/supports_retry_skeleton=true（Round 20 收口）** + supported_measurement_type_ids（11 个）/supported_command_type_ids=7（Round 19 升级）/supported_time_tagged_command_type_ids=3（Round 19 收口）/supported_time_tagged_type_ids=8（Round 19 升级） 分组），Beckhoff_ADS 为 codebase-pending mode（增强探针），GOOSE/SV 为 environment-pending mode；**Modbus register_encoding 工具子包（SF-FR-030，Round 18 收口）** + **Modbus TCP/RTU facade 接入 register_encoding 工具（Round 19 收口）**：`modbus_tcp_facade.py` + `modbus_rtu_facade.py` 三个新公共方法 `encode_register_value` / `decode_register_value` / `register_encoding_capabilities`，**真实调用 register_encoding 工具**，5 value_type × 4 byte/word 组合 = 20 组合 + NaN/Inf 拒绝 + 越界/长度错误检测；纯 Python CPU 辅助层，**`register_encoding_runtime=false` 显式**，facade 接入**不是** Modbus 真实设备验证（不得被高估为真实设备验证）；MODBUS_TCP 既有 FC03/FC04/FC06/FC16 + MODBUS_RTU 既有 FC01-06/FC15/FC16 不回退；MQTT subscribe 已实现（SubscriptionQueue）；OPC_UA/IEC104/IEC61850 通过 C runner 子进程实现；probe/profile/capacity 最小工具层闭环已实现，已扩展至 13 协议（含 MODBUS_RTU rtu-lightweight）；report 语义已起步（ReportQueue）；native runner 框架已建立；不进入 BlueCrystal 生产链路；import boundary 15 tests 全通过 | import boundary AST 扫描 + grep 零违规；**1416 stable passed（1215 starfish + 15 architecture + 186 seahorse：180 stable + 5 新 daily_power 稳定性测试 + 1 原 daily_power_preset；0 failed / 0 flaky，test-validator 独立验证连续 12 次 0 flaky）** | 1 个协议 codebase-pending（Beckhoff_ADS）；2 个协议 environment-pending（GOOSE/SV）；IEC101 为 codec-enhanced-plus（5 级 mode，非完整 server）；**Round 16/17/18/19 残留 deferred 项已全部收口**（Round 16 残留 4 类：ShortFloat / M_ME_TB_1 / M_ME_TC_1 / QU 显式化 / LinkLayer 5 态 + FCB/FCV + timers / health() reason_text 修复；Round 18 5 个新信息对象 + ScaledValue IE + QOS + Modbus register_encoding 工具子包；Round 19 3 个带时标命令 C_SE_TA_1/C_SE_TB_1/C_SE_TC_1 + Modbus TCP/RTU facade 接入 register_encoding 工具）；**Round 20 已收口**（Seahorse flaky 根因修复 + LinkLayer runtime skeleton + balanced FCB auto flip + retry ERROR + ShortFloat duck typing + 3 新 capabilities）；**Round 21 总收口真实剩余项**（**不**得高估为已实现）：真实 IEC101 server / 真实串口通信 / 完整 balanced/unbalanced runtime / GOOSE/SV L2 环境 / Beckhoff_ADS 真实环境 / Modbus 真实设备验证 / 现场部署；MODBUS_RTU 不等同真实串口现场；report 语义仅 IEC61850 Report facade；MMS read 为内存点位；Report events 来自 Python 侧；MQTT 非完整 broker；OPC_UA/IEC104/IEC61850 非完整协议 server；Modbus register_encoding 工具 + facade 接入均非真实设备验证 | Starfish 能力增强阶段总收口（除现场部署外） | 2026-06-07 |
| SF-AR-002 | 总体逻辑设计 2.1/8.2/8.3 | Starfish 不 import seahorse/whale.ingest/whale.shared.source | AR | 高 | 全组件 | P2 | 已建立并通过（Round 10 验证） | `tests/architecture/test_starfish_import_boundary.py` -> 11 tests passed（6 向 AST 扫描 + 目录结构检查含 native/ 子包）；AST 扫描 + grep 零违规；所有 6 边界 import 清洁（新增 7 个源文件 不引入 seahorse/ingest/source 依赖） | import boundary 双向验证通过 | 无立即差距 | 持续监控 | 2026-06-05 |
| SF-AR-003 | 总体逻辑设计 8.2 | RuntimeRegistry 支持 real/stub/mqtt-lightweight/codec-enhanced-plus/codec-enhanced/codec-skeleton/rtu-lightweight/codebase-pending/environment-pending + native runner dispatch（13 协议 9 模式） | AR | 高 | starfish.registry | P1 | 已完成（**Round 18 扩展 + Round 19 扩展 + Round 20 增强 + Round 21 总收口**） | `RuntimeRegistry.create_facade_for_endpoint` 根据 protocol 分发：HTTP_REST->HttpRestFacade(mode="real")；MODBUS_TCP->ModbusTcpFacade(mode="real")；MQTT->MqttFacade(mode="mqtt-lightweight")；OPC_UA->OpcUaFacade(mode="real"|"unavailable")；IEC104->Iec104Facade(mode="real"|"unavailable")；IEC61850_MMS->Iec61850MmsFacade(mode="real"|"unavailable")；IEC61850_Report->Iec61850ReportFacade(mode="real"|"unavailable")；IEC101->Iec101Facade(mode="codec-enhanced-plus" 5 级动态判定，**Round 17 一次性收口 + Round 18 扩展 + Round 19 扩展 + Round 20 增强 + Round 21 总收口**：ShortFloat + ShortFloat **duck typing 兼容**（Round 20 收口） + M_ME_TB_1/M_ME_TC_1 + QU 显式化 + 5 态 LinkLayer + FCB/FCV + timers + balanced/unbalanced 差异化 + **LinkLayerTimerService 抽象 + Default (threading.Timer) + Fake 三实现 + 完整 send/receive/on_timeout 状态机 + balanced FCB auto flip（Round 20 收口） + retry ERROR（Round 20 收口）**，**Round 18 增量**：14 TypeId 矩阵（M_ME_NB_1/M_ME_NC_1/C_SE_NA_1/C_SE_NB_1/C_SE_NC_1 新增；C_SE_TA_1/TB_1/TC_1 显式 deferred 至 Round 19 收口）+ ScaledValue IE + QOS + supports_command_codec=true/supports_scaled_value=true/supports_write_runtime=false + supported_measurement_type_ids/supported_command_type_ids/supported_time_tagged_type_ids 分组，**Round 19 增量**：17 TypeId 矩阵（C_SE_TA_1/C_SE_TB_1/C_SE_TC_1 收口，3 个带时标命令）+ supported_command_type_ids=7（升级）+ supported_time_tagged_command_type_ids=3（收口）+ supported_time_tagged_type_ids=8（升级）+ supports_time_tagged_command_codec=true（收口）+ 维持 supports_write_runtime=false，**Round 20 增量**：3 新 capabilities（supports_link_layer_timers=true / supports_balanced_fcb_auto_flip=true / supports_retry_skeleton=true）+ ShortFloat duck typing 兼容，**health() reason_text 显式 codec-enhanced-plus 分支**（Round 20 同步 7 强制要点）+ codec_enhanced_plus_ready 诊断字段，capabilities supports_short_float=true/supports_link_layer_skeleton=true/supports_command_codec=true/supports_scaled_value=true/supports_write_runtime=false/supports_time_tagged_command_codec=true/supports_server=false/supports_serial_runtime=false/supports_link_layer_timers=true/supports_balanced_fcb_auto_flip=true/supports_retry_skeleton=true，**supported_type_ids 17 TypeId（Round 19 扩展，**严禁硬写 13/14/15/18**）**，优先 codec-enhanced-plus，回退 codec-enhanced / codec-skeleton)；MODBUS_TCP->ModbusTcpFacade + **Round 19 收口三个公共方法 encode_register_value/decode_register_value/register_encoding_capabilities**（真实调用 register_encoding 工具，非仅 capabilities 文案，**register_encoding_runtime=false 显式**）；MODBUS_RTU->ModbusRtuFacade(mode="rtu-lightweight" PTY 可用时，mode="codebase-pending" PTY 不可用时，动态 dispatch）+ **Round 19 收口三个公共方法 encode_register_value/decode_register_value/register_encoding_capabilities**（同 MODBUS_TCP 语义）；Beckhoff_ADS->AdsFacade(mode="codebase-pending")；GOOSE->GooseFacade(mode="environment-pending")；SV->SvFacade(mode="environment-pending")；FacadeEntry 含 mode 属性；新增 `_CODEC_SKELETON_PROTOCOLS` frozenset | `tests/unit/starfish/test_protocol_facade.py` -> registry dispatch 通过（含 rtu-lightweight + codec-skeleton + codec-enhanced + codec-enhanced-plus + codebase-pending fallback + **Modbus TCP/RTU facade register_encoding 集成测试，Round 19 收口**）；`tests/unit/starfish/test_modbus_rtu_facade.py` -> 76 tests passed + **Round 19 收口 encode_register_value/decode_register_value/register_encoding_capabilities 三方法测试**；`tests/unit/starfish/test_iec101_codec.py` -> 40 tests + **TestIec101CodecRound19（Round 19 收口）**：capabilities 17/7/3 数字断言 + supported_time_tagged_command_type_ids 断言 + supports_time_tagged_command_codec 断言 + **TestIec101CodecRound20（Round 20 收口）**：3 新 capabilities 数字断言 + reason_text 7 强制要点验证；`test_iec101_information_elements.py` -> 扩展 ShortFloat + M_ME_TB_1/M_ME_TC_1 + ScaledValue IE（Round 18 收口）+ **TestShortFloatRound20Compat（Round 20 收口）**：int / Decimal / Fraction / `__float__` duck typing 4 路输入；`test_iec101_asdu_objects.py` -> 扩展带时标短浮点 + QU 显式化 + 5 新信息对象 + QOS（Round 18 收口）+ **6 个 C_SE_T* test classes（Round 19 收口）**：test_c_se_ta_1_roundtrip + test_c_se_tb_1_roundtrip + test_c_se_tc_1_roundtrip + test_c_se_t_a_byte_layout + test_c_se_t_b_byte_layout + test_c_se_t_c_byte_layout 验证 12/12/14 字节布局与 COT 字段；`test_iec101_ft12_frame.py` -> 36 tests + `test_iec101_link_layer.py` -> 扩展 FCB/FCV/timers/balanced-unbalanced 差异化（Round 17 收口）+ **8 个 Round 20 收口 test classes**：LinkLayerTimerService + Default + Fake + balanced FCB auto flip + retry ERROR + sequence 状态机 + **`test_modbus_register_encoding.py` -> 164 tests passed（Round 18 收口）**（**580+ IEC101 codec tests + 164 Modbus register encoding tests + Modbus facade register_encoding 集成测试 + LinkLayer 8 test classes + ShortFloat Round20Compat** = **1416 stable passed**：1215 starfish + 15 architecture + 186 seahorse = 180 stable + 5 新 daily_power 稳定性测试 + 1 原 daily_power_preset；0 failed / 0 flaky） | 1 个协议 codebase-pending（Beckhoff_ADS）/ 2 个协议 environment-pending（GOOSE/SV）；IEC101 为 codec-enhanced-plus（5 级 mode，capabilities 显式 supports_server=false/supports_serial_runtime=false/supports_link_layer_skeleton=true/supports_cp56time2a=true/supports_short_float=true/supports_command_codec=true/supports_time_tagged_command_codec=true/supports_scaled_value=true/supports_write_runtime=false/supports_link_layer_timers=true/supports_balanced_fcb_auto_flip=true/supports_retry_skeleton=true，非完整 server）；**C_SE_TA_1/C_SE_TB_1/C_SE_TC_1 已收口（Round 19）**；**balanced FCB auto flip 已收口（Round 20，仅规则）**；**LinkLayer runtime skeleton 已收口（Round 20，TimerService 抽象 + Default + Fake + 完整 send/receive/on_timeout）**；**ShortFloat duck typing 已收口（Round 20，int / float / `numbers.Real` / `__float__`，不引入 numpy 硬依赖）**；MODBUS_RTU rtu-lightweight 不等同真实串口；**Modbus register_encoding 工具子包 + Modbus TCP/RTU facade 接入 register_encoding 工具均非 Modbus 真实设备验证**（`register_encoding_runtime=false` 显式） | 条件就绪后升级 pending 协议为 real mode；真实 IEC101 server + Modbus 真实设备验证（**仍 deferred**：真实串口 / 现场设备 / 完整 balanced/unbalanced runtime） | 2026-06-07 |

## 7. 实现文件清单

```text
src/starfish/
├── __init__.py                        — 包入口，架构分层与安全边界声明
├── __main__.py                        — CLI 入口（5 子命令：load-server-plan/smoke-server-plan/probe-server-plan/profile-server-plan/capacity-server-plan，含 per-endpoint mode 输出）
│
├── models/                            — Starfish 侧最小契约模型
│   ├── __init__.py                   — 导出入口
│   └── plan.py                       — StarfishServerPlan / StarfishEndpointPlan / StarfishPointPlan / LoadResult / ValidationResult / UnsupportedOperation
│
├── loader/                            — ServerPlan 加载器
│   ├── __init__.py                   — 导出入口
│   └── server_plan_loader.py        — load_server_plan（9 项校验 + payload_hash 复算 + JSON 解析）
│
├── facade/                            — 协议 server 模拟门面
│   ├── __init__.py                   — 导出入口（导出 ServerSimulatorFacade / HttpRestFacade / ModbusTcpFacade / MqttFacade / OpcUaFacade / Iec104Facade / Iec61850MmsFacade / Iec61850ReportFacade / SubscriptionQueue / ReportQueue）
│   ├── server_simulator_facade.py    — ServerSimulatorFacade（in-memory stub：start/stop/health/read/load_points/update_values/capabilities + NOT_IMPLEMENTED write/subscribe/report）
│   ├── http_rest_facade.py           — HttpRestFacade（HTTP REST 真实 server：ThreadingHTTPServer, GET /points）
│   ├── modbus_tcp_facade.py          — ModbusTcpFacade（Modbus TCP 真实 server：TCP socket, FC03/FC06）
│   ├── mqtt_facade.py                — MqttFacade（lightweight JSON-line TCP server：socket bind/listen/accept, JSON-line pub, SubscriptionQueue subscribe；不是完整 MQTT broker）
│   ├── opcua_facade.py               — OpcUaFacade（OPC UA real mode：open62541 C runner 子进程，dependency probe + start/stop + unavailable 语义）
│   ├── iec104_facade.py              — Iec104Facade（IEC104 real mode：iec104_simulator_server C runner 子进程，dependency probe + start/stop + unavailable 语义）
│   ├── iec61850_mms_facade.py        — Iec61850MmsFacade（IEC61850 MMS real mode：iec61850_simulator_server C runner 子进程（27144 bytes），dependency probe + start/stop + unavailable；read 为内存点位非真实 MMS 协议帧；write/subscribe 为 NOT_IMPLEMENTED）
│   ├── iec61850_report_facade.py     — Iec61850ReportFacade（IEC61850 Report real mode：iec61850_report_runner C runner 子进程（26568 bytes），dependency probe + start/stop + unavailable + ReportQueue（put/get/drain/FIFO）；events 来自 Python 侧非子进程；write/subscribe 为 NOT_IMPLEMENTED）
│   ├── iec101_facade.py              — Iec101Facade（codebase-pending stub + 增强探针：探测 lib60870/PTY/native binary；无 ASDU/COT/IOA 帧编解码器；write/subscribe/report NOT_IMPLEMENTED）
│   ├── modbus_rtu_facade.py          — ModbusRtuFacade（Round 13 重写：rtu-lightweight PTY-backed real mode，CRC16/FC03/FC06/PTY 生命周期；PTY 不可用时 codebase-pending fallback；write 已实现/ subscribe+report NOT_IMPLEMENTED）
│   ├── ads_facade.py                 — AdsFacade（codebase-pending stub + 增强探针：探测 dotnet/TwinCAT 环境变量；无 Python 原生 ADS 实现；write/subscribe/report NOT_IMPLEMENTED）
│   ├── goose_facade.py               — GooseFacade（environment-pending stub：L2 veth 网络未就绪；write/subscribe/report NOT_IMPLEMENTED）
│   └── sv_facade.py                  — SvFacade（environment-pending stub：L2 veth + PTP 时间同步未就绪；write/subscribe/report NOT_IMPLEMENTED）
│
├── native/                             — Native Runner 管理框架
│   ├── __init__.py                   — 导出入口（导出 NativeRunnerSpec/probe_native_runner/NativeProcessHandle）
│   ├── runner_spec.py                — NativeRunnerSpec dataclass（binary path/host/port/protocol/working_dir/env/timeout）
│   ├── runner_probe.py               — probe_native_runner() 统一 binary 探测函数（stat + 文件大小 + 可执行权限）
│   └── process_handle.py             — NativeProcessHandle 子进程生命周期管理（start/stop/health/pid/pid_file cleanup）
│
├── tools/                             — 工具层（probe/profile/capacity）
│   ├── __init__.py                   — 导出入口（导出 ProbeResult/ProfileResult/CapacityResult + run_probe/run_profile/run_capacity）
│   ├── probe.py                      — run_probe 最小启动-健康-读取探测（PASS/FAIL/NOT_RUN + reason）
│   ├── profile.py                    — run_profile N 次 read 采样耗时统计（count/min/max/avg）
│   └── capacity.py                   — run_capacity 端点/点位/读取容量扫描（不等同生产容量验收）

├── protocols/                          — 协议层编解码器
│   ├── __init__.py                 — 包入口，协议编解码器注册
│   ├── iec101/                      — IEC101 编解码器骨架 + 增强（Round 15 codec-enhanced + Round 16 codec-enhanced-plus 起步 + Round 17 一次性收口 + **Round 18 扩展 14 TypeId** + **Round 19 扩展 17 TypeId（3 C_SE_T*）**）
│   │   ├── __init__.py             — 导出 TypeId/COT/ASDUHeader/IOA/CA/SIQ/QDS/NVA/4+5 信息对象（4 不带时标监视 + 1 不带时标标度化 + 1 不带时标短浮点 + 4 不带时标命令 + 3 带时标命令 C_SE_TA_1/C_SE_TB_1/C_SE_TC_1（**Round 19 新增**）+ 5 带时标监视 = **17 TypeId，Round 19 扩展，以 capability 实际值 17 为准**）/ScaledValue IE/ASDU 列表/FT1.2 帧/CP56Time2a 时标 IE/ShortFloat 短浮点 IE/**17 TypeID 矩阵（Round 19 升级，**严禁硬写 13/14/15/18**）**/QU 显式化/QOS/SetPointQualifier/SetPointCommandQualifier/5 态链路层状态机骨架 编解码函数
│   │   ├── types.py                — TypeId 枚举(26 values)/COT 枚举(26 values，实测)
│   │   ├── asdu.py                 — ASDUHeader 6 字节 encode/decode
│   │   ├── ioa.py                  — IOA 3 字节 encode/decode
│   │   ├── common_address.py      — CA 2 字节 encode/decode
│   │   ├── quality.py             — SIQ 单点信息质量描述符 + QDS 测量值质量描述符（IntFlag 位）
│   │   ├── information_elements.py — NVA 归一化值（16-bit signed, [-1.0, +1.0-1/32768]）+ encode/decode + ShortFloat IEEE 754 32-bit IE（NaN/Inf 严格拒绝 + 0.0/-0.0/极值边界，Round 17 新增）+ **ScaledValue IE（16-bit signed, range [-32768, 32767]，Round 18 新增）**
│   │   ├── information_object.py   — M_SP_NA_1/M_DP_NA_1/M_ME_NA_1/C_SC_NA_1 + M_SP_TA_1/M_DP_TA_1/M_ME_TA_1 带时标 + M_ME_TB_1（10 字节 SVA+QDS+CP56Time2a，Round 17 新增）+ M_ME_TC_1（12 字节 ShortFloat+QDS+CP56Time2a，Round 17 新增）+ **M_ME_NB_1（5 字节 SVA+QDS，不带时标标度化，Round 18 新增）+ M_ME_NC_1（5 字节 ShortFloat+QDS，不带时标短浮点，Round 18 新增）+ C_SE_NA_1（5 字节 NVA+QOS，不带时标归一化值命令，Round 18 新增）+ C_SE_NB_1（5 字节 SVA+QOS，不带时标标度化值命令，Round 18 新增）+ C_SE_NC_1（5 字节 ShortFloat+QOS，不带时标短浮点值命令，Round 18 新增）+ C_SE_TA_1（**12 字节 NVA+QOS+CP56Time2a，Round 19 新增，与 IEC 60870-5-101 §7.2.6.9 对齐**）+ C_SE_TB_1（**12 字节 SVA+QOS+CP56Time2a，Round 19 新增，与 IEC 60870-5-101 §7.2.6.10 对齐**）+ C_SE_TC_1（**14 字节 ShortFloat+QOS+CP56Time2a，Round 19 新增，与 IEC 60870-5-101 §7.2.6.11 对齐**）** + C_SC_NA_1_QU_QUALIFIER 枚举 + CommandPulse 枚举 + SingleCommandQualifier 显式字段（select_execute/qualifier/ql_value/persistent/pulse）+ 旧位级 roundtrip 兼容（Round 17 显式化）+ **SetPointQualifier 枚举（QOS 0-7 标准子字段，Round 18 新增）+ SetPointCommandQualifier 显式字段（select/qualifier/ql_value，Round 18 新增）** 信息对象 encode/decode
│   │   ├── codec.py               — ASDU 信息对象列表 SQ=0/SQ=1 编解码 + UnknownAsduError 容错 + **5 新信息对象 dispatcher（Round 18 扩展 confirmed in `_TYPE_ID_OBJECT_SIZE`）+ 3 新 C_SE_T* dispatcher（Round 19 扩展）** = 17 TypeId
│   │   ├── frame.py               — FT1.2 固定/可变帧 + checksum compute/verify + 长度不一致检测
│   │   ├── time.py                — CP56Time2a 7 字节时标 IE（milliseconds/minute/hour/day_of_month/day_of_week/month/year/IV/SU/SB 字段级 + encode/decode + to/from_datetime 转换）— Round 16 新增
│   │   └── link_layer.py          — IEC 60870-5-101 链路层最小状态机骨架（**Round 17 扩展** LinkLayerMode balanced/unbalanced + LinkState 5 态 IDLE/WAIT_ACK/SEND/RECEIVE/ERROR + **LinkLayerTimers t1/t2/t3 常量** + LinkEvent + LinkControlHelper build_ack/build_nack/build_reset/build_reset_ack/build_user_data + **fcb_bit_for_sequence/fcv_bit helper** + LinkLayer feed_frame/bump_send_sequence/**flip_send_sequence**/mark_waiting_ack/**mark_sending/mark_receiving**/**should_retry**/reset/snapshot，**balanced/unbalanced 差异化 skeleton 行为**，零 Popen/threading/socket/pty/serial，**仅 skeleton 非 server**）— Round 16 起步，Round 17 扩展
│   └── modbus/                      — Modbus register_encoding 工具子包（**Round 18 新增 SF-FR-030 + Round 19 facade 接入**，纯 Python CPU 辅助层，非真实设备验证；`modbus_tcp_facade.py` + `modbus_rtu_facade.py` 三个新公共方法真实调用 register_encoding 工具，**`register_encoding_runtime=false` 显式**）
│       ├── __init__.py             — 导出 register_encoding 模块（5 value_type × 4 byte/word 组合 = 20 组合 + NaN/Inf 拒绝 + 越界/长度错误检测）
│       └── register_encoding.py    — encode_register(value, value_type, byte_order) / decode_register(registers, value_type, byte_order)；value_type ∈ {uint16, int16, uint32, int32, float32}；byte_order ∈ {big-big, little-little, big-little, little-big}；float32 NaN/Inf 严格拒绝；Round 18 工具实现，Round 19 由 facade 接入（**register_encoding.py 不修改**）
│
└── registry/                          — 运行时注册表
    ├── __init__.py                   — 导出入口
    └── runtime_registry.py           — RuntimeRegistry / create_facade_for_endpoint / create_facades/get_supported_protocols/get_codec_skeleton_protocols/get_codebase_pending_protocols/get_environment_pending_protocols（工厂，real/stub/mqtt-lightweight/codec-enhanced-plus/codec-enhanced/codec-skeleton/rtu-lightweight/codebase-pending/environment-pending 9 模式 dispatch — Round 16 新增 codec-enhanced-plus）

## 8. 测试文件清单

```text
tests/unit/starfish/
├── __init__.py
├── test_server_plan_loader.py        — ServerPlan loader（~30 tests：有效加载/必填字段缺失/schema_version 不匹配/payload_hash mismatch/endpoints 结构/points 结构/synthetic 校验/文件不存在/JSON 解析错误/Seahorse 导出 bundle roundtrip）
├── test_server_simulator_facade.py   — ServerSimulatorFacade in-memory stub（~30 tests：start/stop/health/load_points/read/update_values/capabilities/NOT_IMPLEMENTED write/subscribe/report/registry factory）
├── test_protocol_facade.py           — 协议专用 facade（~47 tests：HttpRestFacade 真实 HTTP server start/stop/health/read/NOT_IMPLEMENTED；ModbusTcpFacade 真实 TCP socket FC03/FC06 读写/start/stop/health/write/capabilities；RuntimeRegistry dispatch 含 OPC_UA/IEC104/IEC61850_MMS/IEC61850_Report/IEC101/MODBUS_RTU/Beckhoff_ADS/GOOSE/SV real/unavailable/codec-enhanced/codebase-pending/environment-pending 12 协议；**Round 19 扩展** +Modbus TCP/RTU facade register_encoding 集成测试 encode_register_value/decode_register_value/register_encoding_capabilities + 5 value_type × 4 byte/word 组合 + register_encoding 工具输出一致性 + register_encoding_runtime=false 边界）
├── test_mqtt_facade.py               — MqttFacade 轻量 TCP server（37 tests：SubscriptionQueue 5 tests, lifecycle 5 tests, data operations 10 tests, subscribe 7 tests, NOT_IMPLEMENTED 2 tests, TCP protocol 5 tests, smoke flow 1 test）
├── test_probe_profile_capacity.py    — probe/profile/capacity 工具层（~41 tests：probe/profile/capacity 覆盖 12 协议；real mode PASS + unavailable/pending/codec-only NOT_RUN + reason）
├── test_opcua_iec104_facade.py       — OPC_UA/IEC104 facade 生命周期 + dependency probe（58 tests：OpcUaFacade start/stop/health/dependency probe/unavailable/reason/subprocess Popen/READY/TCP connect/NOT_IMPLEMENTED write/subscribe/report；Iec104Facade start/stop/health/dependency probe/unavailable/reason/subprocess Popen/READY/NOT_IMPLEMENTED write/subscribe/report）
├── test_iec61850_facade.py           — IEC61850 MMS/Report facade 生命周期 + dependency probe + ReportQueue（71 tests：Iec61850MmsFacade start/stop/health/dependency probe/unavailable/reason/subprocess Popen/READY/TCP connect/NOT_IMPLEMENTED write/subscribe；Iec61850ReportFacade start/stop/health/dependency probe/unavailable/reason/ReportQueue put/get/drain/FIFO/NOT_IMPLEMENTED write/subscribe；GOOSE/SV stub -> environment-pending dispatch）
├── test_starfish_cli.py              — CLI（~30 tests：load-server-plan/smoke-server-plan/probe-server-plan/profile-server-plan/capacity-server-plan + per-endpoint mode 输出/--help/边界）
├── test_modbus_rtu_facade.py         — Modbus RTU facade 测试（76 tests：CRC16 5 已知向量/8 FCs (FC01-06/FC15/FC16) 完整帧编解码/异常码 0x01-0x04/PTY 生命周期/两模式 dispatch rtu-lightweight+codebase-pending/NOT_IMPLEMENTED subscribe/report；**Round 19 扩展** +encode_register_value/decode_register_value/register_encoding_capabilities 三方法 +5 value_type × 4 byte/word 组合 = 20 组合 roundtrip + register_encoding 工具输出一致性 + register_encoding_runtime=false 边界）
├── test_iec101_codec.py              — IEC101 编解码器头部测试（40 tests：TypeId 26/COT 26 枚举值验证 + ASDUHeader 6 bytes encode/decode + IOA 3 bytes encode/decode + CA 2 bytes encode/decode + 边界 + Iec101Facade codec_capabilities 显式声明 supports_server=false/supports_serial_runtime=false/supports_short_float/supports_link_layer_skeleton；**Round 17 增 codec-enhanced-plus reason 文本一致性断言 + codec_enhanced_plus_ready 诊断字段断言**；**Round 18 增 supports_command_codec=true/supports_scaled_value=true/supports_write_runtime=false 显式声明断言 + 14 TypeId 矩阵分组断言**；**Round 19 增 TestIec101CodecRound19** capabilities 17/7/3 数字断言 + supported_time_tagged_command_type_ids=3 断言 + supported_command_type_ids=7 断言 + supports_time_tagged_command_codec=true 断言 + probe_iec101_codec_enhanced_plus 验证 17 TypeId 矩阵断言）
├── test_iec101_information_elements.py — IEC101 信息体元素测试（**Round 17 扩展**至包含 ShortFloat IEEE 754 32-bit IE 测试 + M_ME_TB_1/M_ME_TC_1 元素级测试；NVA 归一化值 24 tests（encode/decode roundtrip + 边界 + 1/32768 容差 + 极值）+ CP56Time2a 27 tests（位级编码/datetime 转换/字段级校验/IV/SU/SB 标志/极值/容差）+ ShortFloat IEEE 754 测试（NaN/Inf 严格拒绝 + 0.0/-0.0/极值边界 + ±FLT_MAX/±FLT_MIN/FLT_EPSILON + IE 边界 4 字节）+ M_ME_TB_1/M_ME_TC_1 元素级 roundtrip；**Round 18 扩展 +ScaledValue IE 测试（16-bit signed, encode/decode roundtrip + 边界 [-32768, 32767] + 极值）**；— Round 16 扩展，Round 17 一次性收口，Round 18 扩展）
├── test_iec101_asdu_objects.py       — IEC101 信息对象 + ASDU 列表测试（**Round 17 扩展**至包含带时标短浮点 M_ME_TB_1/M_ME_TC_1 roundtrip + C_SC_NA_1 QU 显式化（CommandPulse + SingleCommandQualifier 子字段）+ 旧位级 roundtrip 兼容；M_SP_NA_1/M_DP_NA_1/M_ME_NA_1/C_SC_NA_1 + M_SP_TA_1/M_DP_TA_1/M_ME_TA_1 带时标 roundtrip + M_ME_TB_1/M_ME_TC_1 带时标短浮点 roundtrip + C_SC_NA_1_QU_QUALIFIER/CommandPulse 枚举 + SingleCommandQualifier 显式字段（select_execute/qualifier/ql_value/persistent/pulse）+ 旧位级 roundtrip 兼容 + SIQ/QDS 质量描述符 + ASDU 列表 SQ=0 独立地址/SQ=1 顺序地址 + UnknownAsduError 容错；**Round 18 扩展 +5 新信息对象（M_ME_NB_1/M_ME_NC_1/C_SE_NA_1/C_SE_NB_1/C_SE_NC_1）roundtrip + QOS 结构化 SetPointQualifier 枚举（QOS 0-7 标准子字段）+ SetPointCommandQualifier 显式字段（select/qualifier/ql_value）测试**；**Round 19 扩展 +6 个 C_SE_T* test classes**：test_c_se_ta_1_roundtrip（12 字节 NVA+QOS+CP56Time2a roundtrip）+ test_c_se_tb_1_roundtrip（12 字节 SVA+QOS+CP56Time2a roundtrip）+ test_c_se_tc_1_roundtrip（14 字节 ShortFloat+QOS+CP56Time2a roundtrip）+ test_c_se_t_a_byte_layout（12 字节布局 + COT 字段验证）+ test_c_se_t_b_byte_layout（12 字节布局）+ test_c_se_t_c_byte_layout（14 字节布局）；— Round 16 扩展，Round 17 一次性收口，Round 18 扩展，Round 19 扩展）
├── test_iec101_ft12_frame.py         — IEC101 FT1.2 链路帧测试（36 tests：FixedFrame/VariableFrame encode/decode roundtrip + compute_checksum/verify_checksum + 长度不一致检测 + FrameError + 起始/结束字符错误）
├── test_iec101_link_layer.py         — IEC101 链路层最小状态机骨架测试（**Round 17 扩展**至包含 LinkLayerTimers t1/t2/t3 常量 + LinkControlHelper FCB/FCV helper + LinkLayer 5 态 IDLE/WAIT_ACK/SEND/RECEIVE/ERROR 转移 + flip_send_sequence/should_retry 骨架 + balanced/unbalanced 差异化 skeleton 行为；LinkLayerMode/LinkState/LinkEvent/LinkControlHelper build_ack/build_nack/build_reset/build_reset_ack/build_user_data + fcb_bit_for_sequence/fcv_bit + LinkLayer state transitions + feed_frame bytes 解析 + RESET 恢复 + snapshot — Round 16 起步，Round 17 扩展）
├── test_modbus_register_encoding.py  — **Modbus register_encoding 工具子包测试（Round 18 新增 SF-FR-030，164 tests）**：5 value_type（uint16/int16/uint32/int32/float32）× 4 byte_order 组合（big-big/little-little/big-little/little-big）= 20 组合 roundtrip + 边界 + 极值 + 越界检测 + 长度错误检测 + float32 NaN/Inf 严格拒绝；**纯 Python CPU 辅助层，非 Modbus 真实设备验证**
├── test_remaining_protocols.py       — 3 个 pending facade 测试（3 tests：Beckhoff_ADS/GOOSE/SV stub 生命周期 + NOT_IMPLEMENTED + mode 验证 + 增强探针诊断；IEC101 已升级至 codec-enhanced，MODBUS_RTU 已升级至 rtu-lightweight）
└── test_native_runner_framework.py   — Native Runner 框架测试（66 tests：NativeRunnerSpec 构造/字段/序列化；probe_native_runner 二元存在/缺失/太小/不可执行/unavailable reason；NativeProcessHandle start/stop/health/pid/pid_file/cleanup/lifecycle edge cases/subprocess integration）

tests/architecture/
└── test_starfish_import_boundary.py  — starfish import boundary（15 tests：starfish->seahorse/ingest/source + seahorse->starfish + ingest->starfish + 6 目录结构检查含 native/ 子包；新增 IEC101 codec-enhanced 5 模块 + Round 16 codec-enhanced-plus 2 模块（time.py / link_layer.py）+ **Round 17 一次性收口（ShortFloat + M_ME_TB_1/M_ME_TC_1 + QU 显式化 + 5 态 LinkLayer）** + **Round 18 扩展（5 新 IEC101 信息对象 + ScaledValue IE + QOS + Modbus register_encoding 工具子包）** + **Round 19 扩展（3 C_SE_T* 带时标命令 + Modbus TCP/RTU facade 接入 register_encoding 工具）** + 第三方代码零入侵验证）
```

## 9. 清理记录

### Round 11 物理删除（已完成）

以下项目已于 Round 11 完成物理删除：

| 删除项 | 说明 |
|---|---|
| `tools/source_lab/` 整目录 | 57755 行代码物理删除。含 access/、protocols/、native/、tests/ 等所有子目录 |
| `scripts/run_source_lab_raw_socket_dynamic_gate.sh` | 物理删除 |
| `scripts/run_source_lab_l2_standalone_gate.sh` | 物理删除 |
| `scripts/source_lab_l2_test_env.sh` | 物理删除 |
| `tests/support/source_lab_runtime.py` | 物理删除 |
| `tests/integration/test_source_lab_scada_profile.py` | 物理删除 |
| `tests/integration/test_source_lab_scada_profile_postgres.py` | 物理删除 |
| `tests/integration/test_source_lab_beckhoff_ads_runtime.py` | 物理删除 |
| `tests/unit/test_source_simulation_support_sources.py` | 物理删除 |

### 迁移记录

| 迁移项 | 旧路径 | 新路径 |
|---|---|---|
| OPC_UA C binary | `tools/source_lab/native/build/open62541_simulator_server` | `src/starfish/native/bin/open62541_simulator_server` |
| IEC104 C binary | `tools/source_lab/native/build/iec104_simulator_server` | `src/starfish/native/bin/iec104_simulator_server` |
| IEC61850 MMS C binary | `tools/source_lab/native/build/iec61850_simulator_server` | `src/starfish/native/bin/iec61850_simulator_server` |
| IEC61850 Report C binary | `tools/source_lab/native/build/iec61850_report_runner` | `src/starfish/native/bin/iec61850_report_runner` |
| MODBUS_TCP C binary | `tools/source_lab/native/build/modbus_simulator_server` | `src/starfish/native/bin/modbus_simulator_server` |

### 保留项（非本轮清理范围）

- **旧路径 wrapper（`src/whale/shared/persistence/template/`）**：保留。生产路径消费者 `src/whale/ingest/framework/persistence/init_db.py` 和 `src/whale/shared/persistence/init_db.py` 仍通过旧路径访问模板数据。handoff 禁止修改 ingest 目录。
- **`src/whale/shared/source/runner_resolution.py`**：保留。含 `tools/source_lab/native/build` dev fallback 文件系统路径字符串，不在本轮清理范围。
- **`ai_shared/reports/`** 历史报告中的 source_lab 字样：保留（历史事实）。

### 剩余旧引用清单

以下文件仍通过旧路径 `from whale.shared.persistence.template` 导入模板数据：

| 文件 | 说明 |
|---|---|
| `src/whale/shared/persistence/init_db.py` | 生产路径持久化初始化，消费模板数据 |
| `src/whale/ingest/framework/persistence/init_db.py` | 生产路径 ingest 持久化初始化，消费模板数据 |
| `tests/unit/shared/persistence/test_scada_protocol_params.py` | SCADA 协议参数模板单测 |
| `tests/unit/shared/persistence/test_scada_sample_data_protocol_coverage.py` | SCADA 样例数据协议覆盖单测 |
| `tests/unit/shared/persistence/test_scada_protocol_views.py` | SCADA 协议视图单测 |
| `tests/unit/seahorse/test_compat_wrappers.py` | 兼容性 wrapper 测试（验证旧路径仍可用） |

以上旧路径引用均指向 DeprecationWarning wrapper，不影响功能。生产路径禁止修改；测试文件引用为迁移期兼容，后续可平滑迁移。
