# BlueCrystal 测试索引

本文件是 BlueCrystal 项目唯一测试索引。问题到测试的映射可补充记录在 `tests/issue_trace.md`，但不能替代本索引。

> 最后更新: 2026-06-07 (Round 21: **Starfish 能力增强阶段总收口** — 第 21 轮文档定版与剩余项清理。**本轮核心动作**：修复 test-validator 识别的 6 处文档与代码不一致（见 §6 一致性扫描）+ 建立最终测试统计（**1416 stable passed / 0 failed / 0 flaky**）+ 记录 Seahorse **186 passed（180 stable + 5 新 daily_power 稳定性测试 + 1 原 daily_power_preset）**——`test_curve_daily_power_preset` **根因已修复**（**不**再列 pre-existing flaky；连续 10+ 次 0 flaky）+ **Starfish 1215 + Architecture 15** + IEC101 codec 600+；**协议能力矩阵 12 协议最终态**：HTTP_REST -> real；MODBUS_TCP -> real + register_encoding typed helper；MODBUS_RTU -> rtu-lightweight + register_encoding typed helper；MQTT -> lightweight real + subscribe；OPC_UA -> native runner real-mode / env-dependent；IEC104 -> native runner real-mode / env-dependent；IEC61850_MMS -> native runner real-mode / env-dependent；IEC61850_Report -> native runner real-mode + ReportQueue / env-dependent；IEC101 -> codec-enhanced-plus + LinkLayer runtime skeleton，非 server；Beckhoff_ADS -> codebase-pending / dependency probe；GOOSE -> environment-pending；SV -> environment-pending。**显式边界声明**：`supports_server=false` / `supports_serial_runtime=false` / `supports_write_runtime=false` / `register_encoding_runtime=false`。**已清理 legacy 清单**（Round 19/20 已收口，本轮仅做文档同步）：Seahorse `test_curve_daily_power_preset` flaky（**根因已修复**）；IEC101 LinkLayer timer skeleton（**已实现**）；balanced FCB auto flip（**已实现**）；retry ERROR（**已实现**）；ShortFloat duck typing（**已实现**，不引入 numpy 硬依赖）；Modbus facade register_encoding 接入（**已实现**）；IEC101 C_SE_TA_1/TB_1/TC_1（**已实现**于 Round 19）。**真实剩余项**（**不**得高估为已实现）：真实 IEC101 server / 真实串口 / 完整 balanced/unbalanced runtime / GOOSE/SV L2 / Beckhoff_ADS 真实环境 / Modbus 真实设备 / 现场部署。本仓库项目名为 BlueCrystal，**BlueOcean_REQ_*.md 在仓库中不存在**，本轮沿用 BlueCrystal_REQ_*.md 体系（已通过 git mv 从原 Whale_REQ_*.md 改名，保留 git 历史），**不新建 BlueOcean_REQ_*.md**；20→21 轮总收口完成)

初版为目录级完整、关键链路文件级。不追求全仓逐文件穷尽。

## 1. 文件定位

- 路径: `ai_shared/memory/test_index.md`
- 用途: 测试资产导航、回归测试索引、回归套件定义
- 受众: code-implementer、test-validator、project-steward
- 更新规则: 新增/删除测试文件或回归测试时必须更新

## 2. 生命周期阶段定义

| 阶段 | 说明 | 典型 marker | 典型目录 |
|------|------|------------|---------|
| 开发期验证 | 验证本地逻辑、接口约束、纯计算行为 | `unit` | `tests/unit/`（含 `tests/unit/starfish/`、`tests/unit/seahorse/`）不含外部依赖的测试 |
| 构建期验证 | 验证代码可编译、可导入、lint 和类型检查通过 | 非 pytest | `py_compile`、`ruff`、`mypy`、`cmake --build` |
| 模块集成期验证 | 验证模块内组件协作、fake/mock/stub/in-memory 闭环 | `integration` | `tests/integration/` 中不依赖外部服务的测试 |
| 跨模块联调期验证 | 验证跨模块数据流、消息管道、存储链路 | `integration`、`e2e` | docker-compose 或 simulator 全链路测试 |
| 准生产依赖验证期 | 验证真实外部依赖下的系统行为 | `l5` | 需 Kafka/PG/Redis/S3/TDengine 的测试 |
| 部署前验收期 | 验证部署配置、环境预检、最小数据链路 | `e2e`、`smoke` | `tests/e2e/test_whale_field_*.py`、部署脚本 |
| 发布后运维验证期 | 生产环境运行时状态、健康检查、故障恢复 | 非 pytest | 运维脚本、监控 probe |

### 2.1 各阶段测试不能证明什么

测试通过不等于下级验证通过。各阶段测试只能证明本阶段覆盖的行为：

| 阶段 | 能证明什么 | 不能证明什么 |
|------|-----------|-------------|
| 开发期验证 | 本地逻辑、接口约束、mock/fake/stub 行为正确 | 真实外部依赖行为、模块间协作、真实协议交互 |
| 构建期验证 | 代码可编译/导入/静态检查通过 | 运行时行为、跨模块依赖、外部服务交互 |
| 模块集成期验证 (simulator) | 模块内组件协作、simulator-backed 链路 | 真实外部服务行为、多模块间完整数据流 |
| 跨模块联调期验证 (docker-compose) | 容器化环境下的跨模块数据流和契约 | 真实生产环境行为、硬件设备行为、长期稳定性 |
| 准生产依赖验证期 (真实服务) | 真实 Kafka/PG/Redis/S3/TDengine 行为 | 现场部署行为、硬件设备行为、7x24 长稳、性能极限 |
| 部署前验收期 | 部署配置、环境预检、最小数据链路 | 生产负载行为、故障恢复全场景、性能容量 |
| 发布后运维验证期 | 运行时健康状态、故障恢复路径 | 未发生的故障场景、极端负载、容量上限 |

**关键边界说明**：
- **已删除**：source_lab 工具测试（`tools/source_lab/tests/`）已于 Round 11 随 tools/ 整目录物理删除。协议测试由 `tests/unit/starfish/` 全面替代。
- simulator/fake/mock/stub 测试通过不等于真实设备/服务行为验证通过。
- 单模块测试通过不等于跨模块全链路通过。
- 短期跑通不等于长期稳定运行。
- contract-only adapter 测试通过不等于真实环境下该 adapter 可用。

**IEC101 codec-enhanced 测试关键边界（Round 15 新增）**：
- `test_iec101_codec.py` / `test_iec101_information_elements.py` / `test_iec101_asdu_objects.py` / `test_iec101_ft12_frame.py` 共 138 tests 通过 **仅证明**：纯 Python codec 函数的 encode/decode roundtrip 正确（TypeId/COT 枚举值、ASDUHeader/IOA/CA/SIQ/QDS/NVA/4 信息对象/ASDU 列表 SQ=0/SQ=1/FT1.2 帧 + checksum）、边界条件、容错行为。
- **不证明**：IEC101 协议与真实设备/从站/主站的数据交换能力。
- **不证明**：probe/profile/capacity 工具层对 Iec101Facade 的 stub PASS = 真实 IEC101 server 能力。Iec101Facade.mode=codec-enhanced 时 capabilities 显式 supports_server=false/supports_serial_runtime=false，probe/profile/capacity 必须返回 NOT_RUN/CODEC_ONLY。
- **不证明**：CP56Time2a 7 字节时标 IE 编解码能力（Round 15 显式 deferred，未实现 cp56time2a encode/decode）。
- **不证明**：QU 字段语义（QUALIFIER OF COMMAND 5 位，标准协议中含 S/E/QL 子字段）— 本轮仅做位级别编解码，未拆分 S/E 和 QL 子字段。
- **不证明**：平衡/非平衡传输模式状态机能力（codec-enhanced 不含状态机）。
- **不证明**：真实串口/RS-232/RS-485 通信能力（zero serial runtime）。

**IEC101 codec-enhanced-plus 测试关键边界（Round 16 起步，Round 17 一次性收口，Round 18 扩展，**Round 19 扩展 3 C_SE_T* 带时标命令**）**：
- `test_iec101_information_elements.py`（扩展至包含 ShortFloat IEEE 754 + M_ME_TB_1/M_ME_TC_1 元素级 + ScaledValue IE）/ `test_iec101_asdu_objects.py`（扩展至包含带时标短浮点 + C_SC_NA_1 QU 显式化 + 5 新信息对象 + QOS 结构化）/ `test_iec101_link_layer.py`（扩展至包含 FCB/FCV/timers/balanced-unbalanced 差异化）/ `test_iec101_codec.py`（新增 codec-enhanced-plus reason 文本一致性断言 + 14 TypeId 矩阵分组断言）共 535 tests 通过 **仅证明**：
  - **Round 16 起步**：CP56Time2a 7 字节时标 IE 位级 encode/decode（milliseconds/minute/hour/day_of_month/day_of_week/month/year/IV/SU/SB 字段级 + datetime 互转 + 边界/容差）；3 个带时标 TypeID（M_SP_TA_1 / M_DP_TA_1 / M_ME_TA_1）信息对象 roundtrip；C_SC_NA_1 QU 字段结构化（SingleCommandQualifier）+ 旧位级 roundtrip 兼容；链路层最小状态机骨架 IDLE/WAIT_ACK/ERROR 三态转移（ACK/NACK/RESET/RESET_ACK/USER_DATA/未知 control）正确。
  - **Round 17 一次性收口**：ShortFloat IEEE 754 32-bit IE 位级 encode/decode（NaN/Inf 严格拒绝 + 0.0/-0.0/极值边界 + ±FLT_MAX/±FLT_MIN/FLT_EPSILON）；M_ME_TB_1（10 字节 SVA+QDS+CP56Time2a）/ M_ME_TC_1（12 字节 ShortFloat+QDS+CP56Time2a）带时标短浮点信息对象 roundtrip；C_SC_NA_1 QU 显式化（CommandPulse 枚举 + SingleCommandQualifier 子字段 select_execute/qualifier/ql_value/persistent/pulse + 旧位级 roundtrip 兼容）；链路层 5 态 IDLE/WAIT_ACK/SEND/RECEIVE/ERROR 状态机 + LinkLayerTimers t1/t2/t3 常量 + LinkControlHelper FCB/FCV helper（fcb_bit_for_sequence/fcv_bit）+ LinkLayer flip_send_sequence/should_retry 骨架 + balanced/unbalanced 差异化 skeleton 行为；Iec101Facade.health() reason_text codec-enhanced-plus 显式分支 6 强制要点 + codec_enhanced_plus_ready 诊断字段。
  - **Round 18 扩展**：5 个新 IEC101 信息对象 roundtrip（**M_ME_NB_1** 不带时标标度化，5 字节 SVA+QDS；**M_ME_NC_1** 不带时标短浮点，5 字节 ShortFloat+QDS；**C_SE_NA_1** 不带时标归一化值命令，5 字节 NVA+QOS；**C_SE_NB_1** 不带时标标度化值命令，5 字节 SVA+QOS；**C_SE_NC_1** 不带时标短浮点值命令，5 字节 ShortFloat+QOS）；**ScaledValue IE** 位级 encode/decode（16-bit signed, range [-32768, 32767]）；**QOS 结构化**（SetPointQualifier 枚举 QOS 0-7 标准子字段 + SetPointCommandQualifier 显式字段 select/qualifier/ql_value）；`Iec101Facade.codec_capabilities()` 显式 `codec_mode=codec-enhanced-plus` + `supported_type_ids=14 TypeId`（**以 capability 实际值 14 为准**）+ `supported_measurement_type_ids`/`supported_command_type_ids`/`supported_time_tagged_type_ids` 分组 + `supports_command_codec=true` + `supports_scaled_value=true` + `supports_write_runtime=false`（**C_SE_* command codec 不得被高估为真实写能力**）。
  - **Round 19 扩展**：3 个新 C_SE_T* 带时标命令信息对象 roundtrip（**C_SE_TA_1** 带时标归一化值命令，TypeId=58，**12 字节 NVA+QOS+CP56Time2a**，与 IEC 60870-5-101 §7.2.6.9 对齐；**C_SE_TB_1** 带时标标度化值命令，TypeId=59，**12 字节 SVA+QOS+CP56Time2a**，与 §7.2.6.10 对齐；**C_SE_TC_1** 带时标短浮点值命令，TypeId=60，**14 字节 ShortFloat+QOS+CP56Time2a**，与 §7.2.6.11 对齐）；`Iec101Facade.codec_capabilities()` 显式 `supported_command_type_ids=7`（**以 capability 实际值 7 为准**：4 不带时标命令 C_SC_NA_1/C_SE_NA_1/C_SE_NB_1/C_SE_NC_1 + 3 带时标命令 C_SE_TA_1/C_SE_TB_1/C_SE_TC_1）+ `supported_time_tagged_command_type_ids=3`（**以 capability 实际值 3 为准**：C_SE_TA_1/C_SE_TB_1/C_SE_TC_1）+ `supported_time_tagged_type_ids=8`（5 既有 + 3 新）+ `supports_time_tagged_command_codec=true` + 维持 `supports_write_runtime=false`（**C_SE_T* command codec 不得被高估为真实写能力，Iec101Facade.write() 仍抛 UnsupportedOperation**）；`Iec101Facade.health()` reason_text 同步 codec-enhanced-plus 17 TypeId 分支；`probe_iec101_codec_enhanced_plus()` 验证 17 TypeId 矩阵。
  - **Round 20 扩展**（LinkLayer runtime skeleton + ShortFloat 兼容 + 3 新 capabilities）：`src/starfish/protocols/iec101/link_layer.py` **新增 `LinkLayerTimerService` 抽象** + `DefaultLinkLayerTimerService`（threading.Timer 实现）+ `FakeLinkLayerTimerService`（无 wall-clock，便于单测）三实现；`start_timer(duration_ms, callback) -> TimerHandle` / `cancel_timer(handle) -> bool` / `cancel_all() -> int` / `on_timeout() -> None` API；**send/receive/on_timeout 完整状态机**：`send_user_data(payload) -> WAIT_ACK` / `receive_ack() -> IDLE`（**balanced + FCV=1 时自动翻 send_sequence**）/ `receive_nack() -> bump_retry/ERROR`（**不翻**）/ `on_timeout() -> bump_retry/ERROR`；**balanced FCB auto flip 规则**（ACK + FCV=1 + mode=BALANCED 三条件同时满足时**自动**翻 send_sequence；NACK/timeout/FCV disabled/unbalanced **不翻**）；`retry_count > max_retries` 进入 `ERROR` 状态（`max_retries` 默认 3）；**默认 `enable_timers=False`**（保持 Round 17 行为完全一致；生产需显式 `enable_timers=True` + 注入 TimerService）；`src/starfish/protocols/iec101/information_elements.py` **ShortFloat 兼容扩展**：`encode_short_float` 接受 int / float / `numbers.Real` / `__float__` duck typing 统一入口（探测 `isinstance(value, numbers.Real)` 优先，再 `hasattr(value, "__float__")` 走 duck typing；均失败时抛 `TypeError`）；NaN/Inf **仍严格拒绝**（`ShortFloatValueError`）；**不引入 numpy 硬依赖**（仅 `numbers` stdlib + duck typing 探测）；`Iec101Facade.codec_capabilities()` **新增 3 个 capabilities**：`supports_link_layer_timers=true` / `supports_balanced_fcb_auto_flip=true` / `supports_retry_skeleton=true`（**3 新增 + 3 维持** supports_server=false / supports_serial_runtime=false / supports_write_runtime=false）；`Iec101Facade.health()` reason_text 同步 codec-enhanced-plus + LinkLayer runtime skeleton 分支（7 强制要点）。
- **不证明**：link-layer skeleton = 完整 IEC101 链路层。**仅 5 态**（IDLE/WAIT_ACK/SEND/RECEIVE/ERROR），**不实现真实计时器线程**（t1/t2/t3 仅为常量骨架；**默认 `enable_timers=False` 不启 timer**；`threading.Timer` 在 `DefaultLinkLayerTimerService` 中作为**可选**注入，生产需显式 `enable_timers=True` + 注入 TimerService；Fake 实现用于单测零 wall-clock 验证）、persistent session、完整 balanced/unbalanced 传输模式（FCB 翻转由调用方手动控制）。
- **不证明（Round 20 边界）**：**LinkLayer runtime skeleton 仍不是真实 IEC101 server**（默认 `enable_timers=False` + 零 socket/pty/serial + `supports_server=false` / `supports_serial_runtime=false` 维持）；ShortFloat 兼容**不**等同于支持 numpy 全部类型（仅 duck typing 兼容；**不引入 numpy 硬依赖**）；ShortFloat NaN/Inf **仍严格拒绝**。
- **不证明**：probe/profile 对 Iec101Facade 的 stub PASS = IEC101 真实协议能力。Iec101Facade.mode=codec-enhanced-plus 时 capabilities 显式 supports_server=false/supports_serial_runtime=false/supports_short_float=true/supports_link_layer_skeleton=true/**supports_link_layer_timers=true（Round 20 新增）**/**supports_balanced_fcb_auto_flip=true（Round 20 新增）**/**supports_retry_skeleton=true（Round 20 新增）**/supports_command_codec=true/supports_time_tagged_command_codec=true/supports_scaled_value=true/supports_write_runtime=false，probe/profile/capacity 必须返回 NOT_RUN/CODEC_ONLY。**不得把 skeleton PASS 写成 IEC101 server PASS**。**不得把 C_SE_T* command codec 写成 IEC101 真实 write runtime**。**Round 20 不得把 LinkLayer runtime skeleton PASS（TimerService 抽象 + send/receive/on_timeout + balanced FCB auto flip + retry ERROR）写成 IEC101 server / 真实串口 / 真实 write runtime PASS**。
- **不证明**：真实串口/RS-232/RS-485 通信能力（zero serial runtime）。link_layer.py 零 Popen/threading/socket/pty/serial。
- **不证明**：ShortFloat 对 numpy scalar 真实类型完整支持（**Round 20 已收口 duck typing 兼容**：int / float / `numbers.Real` / `__float__` 统一入口；**不引入 numpy 硬依赖**；用户若传 `np.floating` 实例，依赖其实现 `__float__` duck typing 协议；**不**等于自动 detect np.floating 类型）。
- **不证明**：C_SE_TA_1 / C_SE_TB_1 / C_SE_TC_1 已从 Round 18 deferred 转为 Round 19 已实现（3 个带时标命令 codec 能力 + 字节布局）；**C_SE_T* command codec 仍不得被高估为 IEC101 真实 write runtime**（Iec101Facade.write() 仍抛 UnsupportedOperation）。
- **Round 16 残留的 health() reason_text codec-enhanced-plus 分支缺失风险已修复**（**移除**，**不得继续列为风险**）：test_iec101_codec.py 中新增 codec-enhanced-plus reason 文本一致性断言 + codec_enhanced_plus_ready 诊断字段断言。

**Modbus register_encoding 工具子包测试关键边界（Round 18 新增 SF-FR-030 + Round 19 Modbus facade 接入）**：
- `test_modbus_register_encoding.py` 164 tests 通过 **仅证明**：
  - 5 value_type（uint16/int16/uint32/int32/float32）× 4 byte_order 组合（big-big/little-little/big-little/little-big）= 20 组合 roundtrip 正确；
  - 边界（uint16 [0, 65535] / int16 [-32768, 32767] / uint32/int32 边界 / float32 ±FLT_MAX/±FLT_MIN/FLT_EPSILON）+ 越界检测 + 长度错误检测（uint32/int32/float32 必须为偶数 2 个 16-bit 寄存器） + float32 NaN/Inf 严格拒绝（`ModbusFloatValueError` 异常）。
- **不证明**：Modbus 真实设备验证。register_encoding 工具是纯 CPU 辅助层，不连接 Modbus TCP/RTU slave、不发送/接收 Modbus 帧、不验证 CRC。
- **Round 19 Modbus facade 接入**：`modbus_tcp_facade.py` + `modbus_rtu_facade.py` 三个新公共方法 `encode_register_value` / `decode_register_value` / `register_encoding_capabilities`，**真实调用 register_encoding 工具**（非仅 capabilities 文案），5 value_type × 4 byte/word 组合 = 20 组合 roundtrip 与 register_encoding 工具输出一致；`test_modbus_rtu_facade.py`（Round 19 扩展）+ `test_protocol_facade.py`（Round 19 扩展，Modbus TCP/RTU facade register_encoding 集成测试）。
- **不证明**：Modbus facade 接入 = Modbus 真实设备验证。**`register_encoding_runtime=false` 显式**：facade 接入是纯 CPU 辅助层，不连接 Modbus TCP/RTU slave、不发送/接收 Modbus 帧、不验证 CRC。MODBUS_TCP 既有 FC03/FC04/FC06/FC16 + MODBUS_RTU 既有 FC01-06/FC15/FC16 行为不变（不重构既有 FC 路径）。**不得把 facade 接入写成 Modbus 真实设备验证**。

## 3. 测试资产索引

### 3.1 BlueCrystal 主平台测试 (tests/)

#### 开发期验证 (unit)

| 测试文件 | 测试对象 | 外部依赖 | NOT_RUN 条件 |
|---------|---------|---------|------------|
| `tests/unit/test_config.py` | 配置解析 | 无 | 无 |
| `tests/unit/test_fleet_update_selection.py` | 机群更新选择 | 无 | 无 |
| `tests/unit/test_kafka_message_publisher.py` | Kafka 发布器 | mock Kafka | 无 |
| `tests/unit/test_message_pipeline_adapters.py` | InMemory/DLQ/SchemaRegistry | 无 | 无 |
| `tests/unit/test_message_pipeline_envelope.py` | Envelope/model | 无 | 无 |
| `tests/unit/test_message_pipeline_kafka_adapter.py` | Kafka adapter | mock Kafka | 无 |
| `tests/unit/test_message_pipeline_ports.py` | 端口契约 | 无 | 无 |
| `tests/unit/test_modbus_source_acquisition_adapter.py` | Modbus TCP 采集 | mock | 无 |
| `tests/unit/test_modbus_source_write_adapter.py` | Modbus TCP 写入 | mock | 无 |
| `tests/unit/test_mqtt_backend.py` | MQTT client backend | mock | 无 |
| `tests/unit/test_mqtt_source_acquisition_adapter.py` | MQTT 采集适配器 | mock | 无 |
| `tests/unit/test_http_rest_backend.py` | HTTP REST backend | mock | 无 |
| `tests/unit/test_http_rest_source_acquisition_adapter.py` | HTTP REST 采集适配器 | mock | 无 |
| `tests/unit/test_iec104_backend.py` | IEC104 backend | mock | 无 |
| `tests/unit/test_iec104_source_acquisition_adapter.py` | IEC104 采集适配器 | mock | 无 |
| `tests/unit/test_iec104_source_write_adapter.py` | IEC104 写入适配器 | mock | 无 |
| `tests/unit/test_modbus_rtu_backend.py` | Modbus RTU backend | mock | 无 |
| `tests/unit/test_modbus_rtu_source_acquisition_adapter.py` | Modbus RTU 采集适配器 | mock | 无 |
| `tests/unit/test_iec101_backend.py` | IEC101 backend | mock | 无 |
| `tests/unit/test_iec101_source_acquisition_adapter.py` | IEC101 采集适配器 | mock | 无 |
| `tests/unit/test_opcua_adapter_resolution.py` | OPC UA 适配器解析 | mock | 无 |
| `tests/unit/test_opcua_source_acquisition_adapter.py` | OPC UA 采集适配器 | mock | 无 |
| `tests/unit/test_opcua_source_write_adapter.py` | OPC UA 写入适配器 | mock | 无 |
| `tests/unit/test_iec61850_mms_backend.py` | IEC61850 MMS backend | mock | 无 |
| `tests/unit/test_iec61850_source_acquisition_adapter.py` | IEC61850 MMS 采集适配器 | mock | 无 |
| `tests/unit/test_iec61850_source_write_adapter.py` | IEC61850 MMS 写入适配器 | mock | 无 |
| `tests/unit/test_iec61850_report_backend.py` | IEC61850 Report backend | mock | 无 |
| `tests/unit/test_iec61850_report_acquisition_adapter.py` | IEC61850 Report 采集适配器 | mock | 无 |
| `tests/unit/test_open62541_backend.py` | open62541 backend | mock | 无 |
| `tests/unit/test_polling_acquisition_role.py` | 轮询角色 | mock | 无 |
| `tests/unit/test_subscription_acquisition_role.py` | 订阅角色 | mock | 无 |
| `tests/unit/test_subscription_reconnect_baseline.py` | 订阅重连基线 | mock | 无 |
| `tests/unit/test_subscription_reconnect_runtime.py` | 订阅重连运行时 | mock | 无 |
| `tests/unit/test_redis_source_state_cache.py` | Redis 状态缓存 | mock Redis | 无 |
| `tests/unit/test_redis_streams_message_publisher.py` | Redis Streams 发布器 | mock Redis | 无 |
| `tests/unit/test_relational_outbox_message_publisher.py` | Outbox 发布器 | mock DB | 无 |
| `tests/unit/test_ingest_api_app.py` | FastAPI app | mock | 无 |
| `tests/unit/test_ingest_audit_event_schema.py` | 审计事件 schema | 无 | 无 |
| `tests/unit/test_ingest_audit_redaction.py` | 审计脱敏 | 无 | 无 |
| `tests/unit/test_ingest_metrics_events.py` | metrics 事件 | 无 | 无 |
| `tests/unit/test_ingest_no_source_lab_imports.py` | import 边界门禁 | 无 | 无 |
| `tests/unit/test_turtle_octopus_import_boundary.py` | turtle/octopus import 边界 | 无 | 无 |
| `tests/unit/test_ingest_observability_sink.py` | 观测 sink | mock | 无 |
| `tests/unit/test_ingest_source_adapter_capability_matrix.py` | 适配器能力矩阵 | 无 | 无 |
| `tests/unit/test_ingest_security_partition_config.py` | 安全分区配置 | 无 | 无 |
| `tests/unit/test_ingest_bundle_checksum.py` | bundle 摘要 | 无 | 无 |
| `tests/unit/test_ingest_bundle_redaction.py` | bundle 脱敏 | 无 | 无 |
| `tests/unit/test_ingest_composition_injection.py` | 注入完整性 | mock | 无 |
| `tests/unit/test_ingest_job_lease.py` | 作业租约 | mock | 无 |
| `tests/unit/test_ingest_runtime_entrypoint.py` | 运行入口 | mock | 无 |
| `tests/unit/test_ingest_runtime_modes.py` | runtime 模式 | mock | 无 |
| `tests/unit/test_ingest_runtime_orm_models.py` | runtime ORM | mock | 无 |
| `tests/unit/test_ingest_runtime_scheduler_import.py` | scheduler 导入 | 无 | 无 |
| `tests/unit/test_ingest_write_lease.py` | 写入租约 | mock | 无 |
| `tests/unit/test_ingest_write_lease_fencing.py` | 写入租约 fencing | mock | 无 |
| `tests/unit/test_ingest_write_security_profile.py` | 写入安全配置 | mock | 无 |
| `tests/unit/test_ingest_readyz.py` | readyz 8 组件聚合 | mock | 无 |
| `tests/unit/test_scheduler_job_routes.py` | 调度任务持久化 | mock DB | 无 |
| `tests/unit/test_worker_runtime_do_execute.py` | WorkerRuntime dispatch | mock | 无 |
| `tests/unit/test_acquisition_job_handler.py` | AcquisitionJobHandler | mock | 无 |
| `tests/unit/test_dual_node_write_lease_conflict.py` | 双节点写入冲突 | mock | 无 |
| `tests/unit/test_source_acquisition_port_registry.py` | 端口注册表 | mock | 无 |
| `tests/unit/test_source_acquisition_use_case.py` | 采集用例 | mock | 无 |
| `tests/unit/test_source_command_write_lease_guard.py` | 写入租约守卫 | mock | 无 |
| `tests/unit/test_source_command_use_case.py` | 命令写入用例 | mock | 无 |
| `tests/unit/test_source_command_lease_release.py` | 写入租约释放 | mock | 无 |
| `tests/unit/test_source_command_audit.py` | 命令审计 | mock | 无 |
| `tests/unit/test_source_command_authorization_guard.py` | 命令授权守卫 | mock | 无 |
| `tests/unit/test_shared_source_runner_resolution.py` | shared_source runner 解析 | mock | 无 |
| `tests/unit/test_state_snapshot_publish_use_case.py` | 快照发布用例 | mock | 无 |
| `tests/unit/test_source_runtime_config_repository.py` | 运行时配置仓库 | mock DB | 无 |
| `tests/unit/test_source_scheduling.py` | 调度 | mock | 无 |
| `tests/unit/test_source_write_port_registry.py` | 写入端口注册表 | mock | 无 |
| `tests/unit/test_speed_layer_light_processor.py` | light_processor | 无 (in-memory) | 无 |
| `tests/unit/test_speed_layer_pipeline_runner.py` | pipeline runner | 无 (in-memory) | 无 |
| `tests/unit/test_speed_layer_preprocessing.py` | preprocessing Round A（固定 10 阶段 pipeline + registry + 11 operator + 6 DTO） | 无 (in-memory) | 无 |
| `tests/unit/test_storage_raw_archive.py` | raw_archive | 无 (in-memory) | 无 |
| `tests/unit/test_storage_raw_index.py` | raw_index | 无 (in-memory) | 无 |
| `tests/unit/test_storage_standardized.py` | standardized | 无 (in-memory) | 无 |
| `tests/unit/test_storage_serving_cache.py` | serving_cache | 无 (in-memory) | 无 |
| `tests/unit/test_storage_waveform.py` | waveform sink (port/InMemory/Tdengine real REST adapter) | 无 (in-memory) | 无 |
| `tests/unit/test_storage_simulation_result.py` | simulation_result sink (InMemory/TDengine real REST adapter) | 无 (in-memory) | MISSING_ENVIRONMENT (需 TDengine 验证) |
| `tests/unit/test_ingest_file_ingest_models.py` | file_ingest FaultRecordBinary/SourceFile models | 无 | 无 |
| `tests/unit/test_ingest_file_ingest_detector.py` | file_ingest FileCompletionDetector | 无 | 无 |
| `tests/unit/test_ingest_file_ingest_decoder.py` | file_ingest FaultRecordBinaryDecoder | 无 | 无 |
| `tests/unit/test_ingest_file_ingest_repository.py` | file_ingest FileIngestJobRepository | 无 | 无 |
| `tests/unit/test_ingest_file_ingest_service.py` | file_ingest FileIngestService 编排 | 无 | 无 |
| `tests/unit/test_model_asset_models.py` | model_asset DTO/枚举（SimulationFileType/Manifest 等） | 无 (in-memory) | 无 |
| `tests/unit/test_model_asset_detector.py` | SimulationFileTypeDetector 文件类型检测 | 无 | 无 |
| `tests/unit/test_model_asset_repository.py` | ModelAssetRepository 四表 CRUD | SQLite :memory: | MISSING_ENVIRONMENT (需 PostgreSQL 验证 FK/indexes) |
| `tests/unit/test_model_asset_service.py` | ModelAssetImportService 导入编排 | 无 (in-memory/mock) | 无 |
| `tests/unit/shared/persistence/test_scada_protocol_params.py` | SCADA 协议参数模板 | 无 | 无 |
| `tests/unit/shared/persistence/test_scada_sample_data_protocol_coverage.py` | SCADA 样例数据协议覆盖 | 无 | 无 |
| `tests/unit/shared/persistence/test_scada_protocol_views.py` | SCADA 协议视图 | 无 | 无 |
| `tests/unit/shared/persistence/test_model_asset_orm.py` | model_asset ORM 四表（唯一约束/FK/自引用） | SQLite :memory: | MISSING_ENVIRONMENT (需 PostgreSQL 验证并发写/indexes) |
| `tests/unit/seahorse/test_reference_data_imports.py` | seahorse.reference_data 导入与导出完整性 | 无 | 无 |
| `tests/unit/seahorse/test_compat_wrappers.py` | 旧路径 DeprecationWarning wrapper 兼容性验证 | 无 | 无 |
| `tests/unit/seahorse/test_models.py` | 14 个核心 dataclass 构造/序列化/确定性 | 无 | 无 |
| `tests/unit/seahorse/test_strategies.py` | 三大策略 + StrategyRegistry：确定性、字段完整性、曲线类型（6 种）、回放边界（KeyError/ValueError/FileNotFoundError）、时间偏移、speed_factor、字段映射、**Round 20 根因修复：5 个 daily_power 稳定性测试**（`test_daily_power_preset_min_floor_enforced` 验证 `min(values) >= floor_ratio * baseline` 钳制生效 + `test_daily_power_preset_cross_run_consistency` 多次跨运行 0 flaky + `test_daily_power_preset_high_noise_compatible` noise_stdev=50 边界不破 floor + `test_other_curves_have_no_floor_behavior` 其它曲线无 floor 行为不变 + `test_daily_power_preset_stable_5x_runs` 5x 连续运行全通过；**非 skip/xfail/删除测试/扩大阈值**——根因修复：noise 叠加后强制 `min(values) >= 300.0`） | 临时文件（JSONL replay） | 无 |
| `tests/unit/seahorse/test_generators.py` | AlarmGenerator（4 种告警类型）+ ControlResultGenerator（7 种控制状态）：确定性、自定义处理器、批量生成、越限/品质/状态/通信告警 | 无 | 无 |
| `tests/unit/seahorse/test_orchestrator.py` | SeahorseGenerator 最小 + 完整 5 元组生成 + deterministic seed 三层验证（Random/Curve/Orchestrator） | 无 | 无 |
| `tests/unit/seahorse/test_bundle.py` | ScenarioBundle 16 字段 + JSON/JSONL 导出 + SHA256 校验和 + bundle validator 6 项校验 + CLI 3 子命令 + SeahorseGenerator 集成 | 临时文件（CLI smoke） | 无 |
| `tests/unit/seahorse/test_server_plan.py` | ServerPlan validator（9 项校验）+ handoff exporter（SHA256 payload_hash 原子写入）+ CLI export-server-plan smoke（31 tests） | 无（临时文件 CLI smoke） | 无 |
| `tests/unit/starfish/test_server_plan_loader.py` | Starfish ServerPlan JSON loader（~30 tests） | 无（临时文件 Seahorse roundtrip） | 无 |
| `tests/unit/starfish/test_server_simulator_facade.py` | ServerSimulatorFacade in-memory stub（~30 tests） | 无（纯内存） | 无 |
| `tests/unit/starfish/test_protocol_facade.py` | HttpRestFacade 真实 HTTP server + ModbusTcpFacade 真实 TCP socket FC03/FC06 + RuntimeRegistry dispatch 含 OPC_UA/IEC104/IEC61850_MMS/IEC61850_Report/codec-enhanced/codec-skeleton/codebase-pending/environment-pending 12 协议（~47 tests；**Round 19 扩展 +Modbus TCP/RTU facade register_encoding 集成测试** encode_register_value/decode_register_value/register_encoding_capabilities + 5 value_type × 4 byte/word 组合 = 20 组合 + register_encoding 工具输出一致性 + `register_encoding_runtime=false` 边界） | 无（纯 Python 标准库，localhost 动态端口） | 无 |
| `tests/unit/starfish/test_mqtt_facade.py` | MqttFacade lightweight JSON-line TCP server：SubscriptionQueue 5 tests + lifecycle 5 tests + data 10 tests + subscribe 7 tests + NOT_IMPLEMENTED 2 tests + TCP protocol 5 tests + smoke flow 1 test（37 tests） | 无（纯 Python 标准库，localhost 动态端口） | 无 |
| `tests/unit/starfish/test_probe_profile_capacity.py` | probe/profile/capacity 工具层：probe/profile/capacity 覆盖 12 协议（stub/http_rest/modbus/mqtt/opcua/iec104/iec61850_mms/iec61850_report + 5 pending 协议 NOT_RUN）（~41 tests；**Round 20 增 TestIec101Round20Capabilities**：验证 `Iec101Facade.codec_capabilities()` 显式声明 `supports_link_layer_timers=true` / `supports_balanced_fcb_auto_flip=true` / `supports_retry_skeleton=true` 3 新 capabilities + reason_text 7 强制要点验证） | 无（纯 Python 标准库，localhost 动态端口） | 无 |
| `tests/unit/starfish/test_opcua_iec104_facade.py` | OpcUaFacade open62541 C runner 子进程 + Iec104Facade iec104_simulator_server C runner 子进程：start/stop/health/dependency probe/unavailable/reason/subprocess lifecycle/NOT_IMPLEMENTED write/subscribe/report（58 tests） | C native 二进制（open62541/iec104_simulator_server） | NOT_RUN: MISSING_DEPENDENCY (二进制不存在时 unavailable 语义，由 dependency probe 检测) |
| `tests/unit/starfish/test_iec61850_facade.py` | Iec61850MmsFacade iec61850_simulator_server C runner 子进程 + Iec61850ReportFacade iec61850_report_runner C runner 子进程：start/stop/health/dependency probe/unavailable/reason/subprocess Popen/READY/TCP connect；ReportQueue put/get/drain/FIFO；NOT_IMPLEMENTED write/subscribe；GOOSE/SV stub -> environment-pending dispatch（71 tests） | C native 二进制（iec61850_simulator_server/iec61850_report_runner） | NOT_RUN: MISSING_DEPENDENCY (二进制不存在时 unavailable 语义，由 dependency probe 检测) |
| `tests/unit/starfish/test_starfish_cli.py` | Starfish CLI 5 子命令：validate-plan/describe/health/read/run（~30 tests；其中最小子集带 `starfish + smoke` marker） | 无（临时文件） | 无 |
| `tests/unit/starfish/test_modbus_rtu_facade.py` | Modbus RTU facade 测试：CRC16 5 已知向量/FC01（2 子模式）/FC02/FC03/FC04/FC05/FC06/FC15/FC16 完整帧编解码/异常码 0x01-0x04/PTY 生命周期 start/stop/health/write/read/两模式 dispatch（rtu-lightweight+codebase-pending fallback）/NOT_IMPLEMENTED subscribe/report（76 tests）；**Round 19 扩展 +encode_register_value/decode_register_value/register_encoding_capabilities 三方法** + 5 value_type × 4 byte/word 组合 = 20 组合 roundtrip + register_encoding 工具输出一致性 + `register_encoding_runtime=false` 边界） | 无（PTY + 纯 Python 标准库） | 无 |
| `tests/unit/starfish/test_remaining_protocols.py` | 3 个 pending facade 测试：Beckhoff_ADS/GOOSE/SV stub 生命周期 + NOT_IMPLEMENTED + mode 验证 + 增强探针诊断（3 tests；IEC101 已升级至 codec-enhanced，MODBUS_RTU 已升级至 rtu-lightweight） | 无（纯内存 stub） | 无 |
| `tests/unit/starfish/test_iec101_codec.py` | IEC101 编解码器头部：TypeId 26 values/COT 26 values（实测）/ASDUHeader 6 字节 encode/decode/IOA 3 字节 encode/decode/CA 2 字节 encode/decode/Iec101Facade codec_capabilities 显式 supports_server=false/supports_serial_runtime=false/supports_short_float/supports_link_layer_skeleton/边界场景（40 tests；**Round 17 增 codec-enhanced-plus reason 文本一致性断言 + codec_enhanced_plus_ready 诊断字段断言**；**Round 18 增 supports_command_codec=true/supports_scaled_value=true/supports_write_runtime=false 显式声明断言 + 14 TypeId 矩阵分组断言 + supported_measurement_type_ids/supported_command_type_ids/supported_time_tagged_type_ids 分组断言**；**Round 19 增 TestIec101CodecRound19** capabilities 17/7/3 数字断言 + supported_time_tagged_command_type_ids=3 断言 + supported_command_type_ids=7 断言 + supports_time_tagged_command_codec=true 断言 + probe_iec101_codec_enhanced_plus 验证 17 TypeId 矩阵断言；**Round 20 增 TestIec101CodecRound20**：`supports_link_layer_timers=true` / `supports_balanced_fcb_auto_flip=true` / `supports_retry_skeleton=true` 3 新 capabilities 数字断言 + reason_text codec-enhanced-plus + LinkLayer runtime skeleton 7 强制要点分支验证） | 无（纯 Python） | 无 |
| `tests/unit/starfish/test_iec101_information_elements.py` | IEC101 信息体元素：NVA 归一化值（16-bit signed，范围 [-1.0, +1.0-1/32768]）encode/decode roundtrip + 边界 + 1/32768 容差 + 极值测试（24 tests）+ CP56Time2a 7 字节时标 IE（位级编码/datetime 转换/字段级校验/IV/SU/SB 标志/极值/容差）（27 tests，Round 16）+ **ShortFloat IEEE 754 32-bit IE（NaN/Inf 严格拒绝 + 0.0/-0.0/极值边界 + ±FLT_MAX/±FLT_MIN/FLT_EPSILON + 4 字节 IE 边界）+ M_ME_TB_1/M_ME_TC_1 元素级（Round 17 扩展**）+ **ScaledValue IE（16-bit signed, range [-32768, 32767]）encode/decode roundtrip + 边界 + 极值（Round 18 扩展**）+ **Round 20 扩展 TestShortFloatRound20Compat**：int 输入接受 / Decimal 输入接受 / Fraction 输入接受 / `__float__` duck typing 接受 / 字符串/None 拒绝 / NaN/Inf 仍严格拒绝 / 极值 roundtrip；**不引入 numpy 硬依赖**） | 无（纯 Python） | 无 |
| `tests/unit/starfish/test_iec101_asdu_objects.py` | IEC101 信息对象 + ASDU 列表：M_SP_NA_1（SIQ 1 byte）/M_DP_NA_1（DPI 2 bits+RES 2 bits）/M_ME_NA_1（NVA 2 bytes+QDS 1 byte）/C_SC_NA_1（SCS/SE/QU/RES）信息对象 roundtrip + SIQ/QDS 质量描述符位标志 + ASDU 列表 SQ=0 独立地址/SQ=1 顺序地址 + UnknownAsduError 容错（38 tests）+ 3 带时标 TypeID（M_SP_TA_1/M_DP_TA_1/M_ME_TA_1）roundtrip + C_SC_NA_1 QU 结构化（SingleCommandQualifier）+ 旧位级 roundtrip 兼容（37 tests，Round 16）+ **2 带时标短浮点 M_ME_TB_1（10 字节 SVA+QDS+CP56Time2a）/ M_ME_TC_1（12 字节 ShortFloat+QDS+CP56Time2a）roundtrip + C_SC_NA_1 QU 显式化（CommandPulse 枚举 + SingleCommandQualifier 子字段 select_execute/qualifier/ql_value/persistent/pulse）+ 旧位级 roundtrip 兼容（Round 17 扩展**）+ **5 新 IEC101 信息对象（M_ME_NB_1/M_ME_NC_1/C_SE_NA_1/C_SE_NB_1/C_SE_NC_1）roundtrip + QOS 结构化 SetPointQualifier 枚举（QOS 0-7 标准子字段）+ SetPointCommandQualifier 显式字段（select/qualifier/ql_value）测试（Round 18 扩展**）+ **3 C_SE_T* 带时标命令信息对象（M_ME_NB_1/C_SE_TA_1 12 字节 NVA+QOS+CP56Time2a，C_SE_TB_1 12 字节 SVA+QOS+CP56Time2a，C_SE_TC_1 14 字节 ShortFloat+QOS+CP56Time2a，Round 19 新增）roundtrip + 6 个 C_SE_T* test classes 验证 12/12/14 字节布局与 COT 字段**） | 无（纯 Python） | 无 |
| `tests/unit/starfish/test_iec101_ft12_frame.py` | IEC101 FT1.2 链路层帧：FixedFrame 5 字节（start 0x10 + control + checksum + end 0x16）+ VariableFrame 6+len 字节（start 0x68 + length × 2 + data + checksum + end 0x16）+ compute_checksum/verify_checksum + 长度不一致检测（length 字段不一致、data 长度不匹配 length）+ FrameError 异常 + 起始/结束字符错误（36 tests） | 无（纯 Python） | 无 |
| `tests/unit/starfish/test_iec101_link_layer.py` | IEC101 链路层最小状态机骨架（**Round 16 起步，Round 17 扩展，Round 20 增强 LinkLayerTimerService + send/receive/on_timeout 状态机 + balanced FCB auto flip + retry ERROR**）：LinkLayerMode 枚举（balanced/unbalanced）+ LinkState 枚举（**Round 17 5 态 IDLE/WAIT_ACK/SEND/RECEIVE/ERROR**）+ **LinkLayerTimers t1/t2/t3 常量** + LinkEvent dataclass + LinkControlHelper（build_ack/build_nack/build_reset/build_reset_ack/build_user_data + **fcb_bit_for_sequence/fcv_bit FCB/FCV helper**）+ LinkLayer（feed_frame/bump_send_sequence/**flip_send_sequence/should_retry**/mark_waiting_ack/**mark_sending/mark_receiving**/reset/snapshot）+ 状态机转移规则（**Round 17 5 态** ACK/NACK/RESET/RESET_ACK/USER_DATA/未知 control + **balanced/unbalanced 差异化**）+ feed_frame bytes 解析 + RESET 恢复（**仅 skeleton 非 server**，零 Popen/socket/pty/serial；默认 `enable_timers=False` 不启 timer）+ **Round 20 新增 8 个 test classes**：`TestLinkLayerTimerService`（抽象接口契约）/ `TestDefaultLinkLayerTimerService`（threading.Timer 实现 + start/cancel/cancel_all）/ `TestFakeLinkLayerTimerService`（无 wall-clock，单测不依赖 sleep）/ `TestLinkLayerSendUserData`（send_user_data -> WAIT_ACK + balanced 自动翻 FCB）/ `TestLinkLayerReceiveAck`（ACK -> IDLE + balanced + FCV=1 自动翻 FCB；NACK/FCV disabled/unbalanced 不翻）/ `TestLinkLayerReceiveNack`（NACK -> bump_retry/ERROR + 不翻 FCB）/ `TestLinkLayerOnTimeout`（timeout -> bump_retry；retry_count > max_retries -> ERROR）/ `TestLinkLayerSequenceStateMachine`（5 态完整 send/receive/timeout 序列验证） | 无（纯 Python in-process 状态机 + 帧 codec 复用 + 可选 threading.Timer） | 无 |
| `tests/unit/starfish/test_modbus_register_encoding.py` | **Modbus register_encoding 工具子包测试（Round 18 新增 SF-FR-030，164 tests）**：5 value_type（uint16/int16/uint32/int32/float32）× 4 byte_order 组合（big-big/little-little/big-little/little-big）= 20 组合 roundtrip + 边界（uint16 [0, 65535] / int16 [-32768, 32767] / uint32/int32 边界 / float32 ±FLT_MAX/±FLT_MIN/FLT_EPSILON）+ 越界检测 + 长度错误检测（uint32/int32/float32 必须为偶数 2 个 16-bit 寄存器）+ float32 NaN/Inf 严格拒绝（`ModbusFloatValueError` 异常）；**纯 Python CPU 辅助层，非 Modbus 真实设备验证** | 无（纯 Python） | 无 |
| `tests/unit/starfish/test_native_runner_framework.py` | Native Runner 管理框架测试：NativeRunnerSpec 构造/字段/序列化；probe_native_runner 二元存在/缺失/太小/不可执行/unavailable reason；NativeProcessHandle start/stop/health/pid/pid_file/cleanup/lifecycle edge cases/subprocess integration（66 tests） | 临时文件（binary stub） | 无 |
| `tests/unit/architecture/test_seahorse_import_boundary.py` | seahorse/ingest/starfish import boundary（AST 扫描，P2 构建期验证，5 tests） | 无 | 无 |
| `tests/unit/architecture/test_starfish_import_boundary.py` | starfish/seahorse/ingest import boundary 6 向 AST 扫描 + 目录结构检查（含 native/ 子包）（15 tests，含 Round 15 IEC101 codec-enhanced 5 模块 + Round 16 IEC101 codec-enhanced-plus 2 模块（time.py / link_layer.py）+ **Round 17 一次性收口（ShortFloat + M_ME_TB_1/M_ME_TC_1 + QU 显式化 + 5 态 LinkLayer）** + **Round 18 扩展（5 新 IEC101 信息对象 + ScaledValue IE + QOS + Modbus register_encoding 工具子包）** + **Round 19 扩展（3 C_SE_T* 带时标命令 + Modbus TCP/RTU facade 接入 register_encoding 工具）** + 第三方代码零入侵验证） | 无 | 无 |

> l5 marker 说明：`l5` 是历史技术标签，当前语义等同于“准生产依赖验证期”。
> 后续可逐步新增 `external` 或 `prodlike` 作为新 marker（见 pyproject.toml），
> 旧测试不需要迁移。l5 marker 含义在 test_index.md 中可追溯，不扩大使用。

#### 模块集成期验证 (integration)

| 测试文件 | 测试对象 | 外部依赖 | NOT_RUN 条件 |
|---------|---------|---------|------------|
| `tests/integration/test_ingest_api_acquisition_task_crud.py` | acquisition task CRUD | SQLite/TestClient | 无 |
| `tests/integration/test_ingest_api_audit.py` | API 审计 | SQLite/TestClient | 无 |
| `tests/integration/test_ingest_api_authorization_deny.py` | API 授权拒绝 | SQLite/TestClient | 无 |
| `tests/integration/test_ingest_api_bundle_metadata_crud.py` | bundle metadata CRUD | SQLite/TestClient | 无 |
| `tests/integration/test_ingest_api_dry_run_all_mutating_routes.py` | API dry-run | SQLite/TestClient | 无 |
| `tests/integration/test_ingest_api_full_audit_matrix.py` | API 全审计矩阵 | SQLite/TestClient | 无 |
| `tests/integration/test_ingest_api_idempotency_all_mutating_routes.py` | API 幂等性 | SQLite/TestClient | 无 |
| `tests/integration/test_ingest_api_idempotency_dry_run.py` | 幂等性 dry-run | SQLite/TestClient | 无 |
| `tests/integration/test_ingest_api_idempotency_dry_run_interaction.py` | 幂等性 dry-run 交互 | SQLite/TestClient | 无 |
| `tests/integration/test_ingest_api_node_lease_audit_query.py` | node/lease 审计查询 | SQLite/TestClient | 无 |
| `tests/integration/test_ingest_api_runtime_config_audit.py` | runtime config 审计 | SQLite/TestClient | 无 |
| `tests/integration/test_ingest_api_runtime_config_crud.py` | runtime config CRUD | SQLite/TestClient | 无 |
| `tests/integration/test_ingest_api_scheduler_job_crud.py` | scheduler job CRUD | SQLite/TestClient | 无 |
| `tests/integration/test_ingest_api_security_partition_crud.py` | security partition CRUD | SQLite/TestClient | 无 |
| `tests/integration/test_ingest_audit_db_jsonl_consistency.py` | DB/JSONL 审计一致性 | SQLite/临时文件 | 无 |
| `tests/integration/test_ingest_bundle_import_export.py` | bundle 导入导出 | SQLite | 无 |
| `tests/integration/test_ingest_bundle_offline_one_way_flow.py` | bundle 单向流 | SQLite | 无 |
| `tests/integration/test_ingest_file_ingest_integration.py` | file_ingest 模块集成（detect->archive->decode->waveform） | 临时文件 | 无 |
| `tests/integration/test_model_asset_integration.py` | model_asset 模块集成（import->detect->archive->persist） | SQLite :memory: + 临时文件 | MISSING_ENVIRONMENT (需 PostgreSQL 验证 FK/并发) |
| `tests/integration/test_model_asset_alembic_migration.py` | model_asset Alembic 迁移（upgrade/downgrade 4 表） | SQLite | MISSING_ENVIRONMENT (需 PostgreSQL 验证) |
| `tests/integration/test_ingest_runtime_alembic_migration.py` | Alembic 迁移 | SQLite | 无 |
| `tests/integration/test_ingest_runtime_db_init.py` | runtime DB 初始化 | SQLite | 无 |
| `tests/integration/test_ingest_runtime_entrypoint_smoke.py` | entrypoint 烟测 | SQLite | 无 |
| `tests/integration/test_message_pipeline_inmemory_e2e.py` | InMemory message_pipeline E2E | 无 | 无 |
| `tests/integration/test_speed_layer_dlq_replay.py` | DLQ/replay | 无 (in-memory) | 无 |
| `tests/integration/test_speed_layer_index_standardized_pipeline.py` | index/standardized/serving_cache | 无 (in-memory) | 无 |
| `tests/integration/test_speed_layer_raw_archive_pipeline.py` | raw_archive pipeline | 临时文件 | 无 |
| `tests/integration/test_whale_writer_failure_recovery.py` | writer 故障恢复 | 无 (in-memory) | 无 |
| `tests/integration/test_whale_writer_switchover.py` | writer 主备切换 | 无 (in-memory) | 无 |
| `tests/integration/test_http_rest_acquisition_chain.py` | HTTP REST 全链路采集 | mock HTTP | 无 |
| `tests/integration/test_iec104_acquisition_chain.py` | IEC104 全链路采集 | mock subprocess | 无 |
| `tests/integration/test_mqtt_acquisition_chain.py` | MQTT 全链路采集 | mock MQTT | 无 |
| `tests/integration/test_modbus_rtu_acquisition_chain.py` | Modbus RTU 全链路 | mock subprocess | 无 |
| `tests/integration/test_iec101_acquisition_chain.py` | IEC101 全链路 | mock subprocess | 无 |
| `tests/integration/test_framework_db_init.py` | 框架 DB 初始化 | SQLite | MISSING_DEPENDENCY (depends on shared/persistence init) |
| `tests/integration/test_ingest_audit_matrix_api_bundle_scheduler_write.py` | 审计矩阵 API/bundle/scheduler | SQLite/TestClient | 无 |
| `tests/integration/test_ingest_cache_to_kafka_pipeline.py` | 缓存到 Kafka 发布 | SQLite/TestClient | 无 |
| `tests/integration/test_ingest_dual_node_db_lease_e2e.py` | 双节点 DB lease E2E | SQLite | 无 |
| `tests/integration/test_ingest_external_access_policy_contract.py` | 外部授权合同 | SQLite/TestClient | 无 |
| `tests/integration/test_ingest_external_audit_sink_contract.py` | 外部审计 sink 合同 | SQLite/TestClient | 无 |
| `tests/integration/test_ingest_iec104_source_write.py` | IEC104 写入 | mock subprocess | 无 |
| `tests/integration/test_ingest_iec61850_mms_source_write.py` | IEC61850 MMS 写入 | mock subprocess | 无 |
| `tests/integration/test_ingest_iec61850_report_subscription.py` | IEC61850 Report 订阅 | mock subprocess | 无 |
| `tests/integration/test_ingest_lightweight_load_gate.py` | 轻量加载门禁 | SQLite/TestClient | 无 |
| `tests/integration/test_ingest_modbus_source_write.py` | Modbus TCP 写入 | mock subprocess | 无 |
| `tests/integration/test_ingest_observability_sink_smoke.py` | 观测 sink 烟测 | SQLite/临时文件 | 无 |
| `tests/integration/test_ingest_opcua_source_write.py` | OPC UA 写入 | mock | 无 |
| `tests/integration/test_ingest_polling_retry_to_redis.py` | 轮询重试到 Redis | SQLite/mock Redis | 无 |
| `tests/integration/test_ingest_runtime_alembic_postgres_matrix.py` | Alembic PostgreSQL 矩阵 | PostgreSQL (可选) | MISSING_ENVIRONMENT (需 PG DSN 环境变量) |
| `tests/integration/test_ingest_runtime_alembic_sqlite_matrix.py` | Alembic SQLite 矩阵 | SQLite | 无 |
| `tests/integration/test_ingest_runtime_migrate_entrypoint.py` | migrate 入口 | SQLite | 无 |
| `tests/integration/test_ingest_scheduler_dual_active_partitioned.py` | 调度器双活分区 | SQLite | 无 |
| `tests/integration/test_ingest_scheduler_missed_tick_and_stagger.py` | missed tick 与错峰 | SQLite | 无 |
| `tests/integration/test_ingest_security_partition_bundle_flow.py` | Bundle 单向流 | SQLite | 无 |
| `tests/integration/test_ingest_security_partition_smoke.py` | 安全分区烟测 | SQLite | 无 |
| `tests/integration/test_ingest_subscription_strategy.py` | 订阅策略 | SQLite/mock | 无 |
| `tests/integration/test_ingest_worker_runtime_executes_usecase_handlers.py` | WorkerRuntime usecase handler | SQLite | 无 |
| `tests/integration/test_ingest_worker_runtime_handler_failure.py` | WorkerRuntime handler 失败 | SQLite | 无 |
| `tests/integration/test_ingest_worker_runtime_shutdown_inflight.py` | WorkerRuntime shutdown inflight | SQLite | 无 |
| `tests/integration/test_ingest_write_lease_fencing_e2e.py` | 写入租约 fencing E2E | SQLite | 无 |
| `tests/integration/test_redis_state_cache_faults.py` | Redis 缓存容错 | mock Redis | 无 |
| `tests/integration/test_shared_persistence_sample_data_init.py` | 样例初始化 | PostgreSQL (可选) | MISSING_ENVIRONMENT (需 PG DSN) |
| `tests/integration/test_sqlite_config_init.py` | SQLite 配置初始化 | SQLite | 无 |

#### 跨模块联调期验证 (integration/e2e + docker-compose)

| 测试文件 | 测试对象 | 外部依赖 | NOT_RUN 条件 |
|---------|---------|---------|------------|
| `tests/integration/test_ingest_prodlike_kafka_publish.py` | Kafka 发布 | docker-compose | MISSING_ENVIRONMENT |
| `tests/integration/test_ingest_prodlike_postgres_runtime_db.py` | PostgreSQL runtime DB | docker-compose | MISSING_ENVIRONMENT |
| `tests/integration/test_ingest_prodlike_redis_cache.py` | Redis 缓存 | docker-compose | MISSING_ENVIRONMENT |
| `tests/integration/test_ingest_scheduler_apscheduler_runtime.py` | APScheduler 运行时 | docker-compose | MISSING_ENVIRONMENT |
| `tests/integration/test_ingest_scheduler_cluster_assignment.py` | 调度器集群分配 | docker-compose | MISSING_ENVIRONMENT |
| `tests/integration/test_ingest_scheduler_active_standby_failover.py` | 调度器主备故障转移 | docker-compose | MISSING_ENVIRONMENT |
| `tests/integration/test_ingest_scheduler_graceful_shutdown.py` | 调度器优雅关闭 | docker-compose | MISSING_ENVIRONMENT |
| `tests/integration/test_ingest_prodlike_worker_failover.py` | worker failover | docker-compose | MISSING_ENVIRONMENT |
| `tests/integration/test_ingest_source_acquisition_to_redis.py` | 采集到 Redis | docker-compose | MISSING_ENVIRONMENT |
| `tests/integration/test_ingest_source_cache_message_e2e.py` | 源缓存消息 E2E | docker-compose | MISSING_ENVIRONMENT |
| `tests/integration/test_message_pipeline_kafka_e2e.py` | Kafka message_pipeline E2E | docker-compose | MISSING_ENVIRONMENT |
| `tests/integration/test_ingest_prodlike_access_policy.py` | prodlike 访问策略 | docker-compose | MISSING_ENVIRONMENT |
| `tests/integration/test_ingest_prodlike_audit_sink.py` | prodlike 审计 sink | docker-compose | MISSING_ENVIRONMENT |
| `tests/integration/test_ingest_prodlike_audit_metrics_resilience.py` | 审计指标韧性 | docker-compose | MISSING_ENVIRONMENT |
| `tests/integration/test_ingest_prodlike_endurance_smoke.py` | prodlike endurance 烟测 | docker-compose | MISSING_ENVIRONMENT |
| `tests/integration/test_ingest_prodlike_kafka_fault_injection.py` | Kafka 故障注入恢复 | docker-compose | MISSING_ENVIRONMENT |
| `tests/integration/test_ingest_prodlike_performance_profile.py` | 性能基线 | docker-compose | MISSING_ENVIRONMENT |
| `tests/integration/test_ingest_prodlike_postgres_fault_injection.py` | PostgreSQL 故障注入恢复 | docker-compose | MISSING_ENVIRONMENT |
| `tests/integration/test_ingest_prodlike_redis_fault_injection.py` | Redis 故障注入恢复 | docker-compose | MISSING_ENVIRONMENT |
| `tests/integration/test_ingest_prodlike_scheduler_backpressure.py` | 调度背压与 missed tick | docker-compose | MISSING_ENVIRONMENT |
| `tests/integration/test_ingest_source_cache_message_kafka_e2e.py` | 源缓存 Kafka 消息 E2E | docker-compose | MISSING_ENVIRONMENT |

#### 准生产依赖验证期 (l5 marker)

| 测试文件 | 测试对象 | 外部依赖 | NOT_RUN 条件 |
|---------|---------|---------|------------|
| `tests/integration/test_l5_external_dependency_verification.py` | 5 大外部服务验证 | Kafka/PG/Redis/S3/TDengine | MISSING_ENVIRONMENT |
| `tests/integration/test_storage_waveform_tdengine_integration.py` | TdengineStandardizedWaveformSink 真实 REST API 写入/读回 (4 tests, TCP+REST 两阶段探测 skipif) | TDengine REST API | MISSING_ENVIRONMENT (TDengine taosAdapter TCP 或 REST API 不可达) |
| `tests/integration/test_storage_simulation_result_tdengine_integration.py` | TdengineSimulationResultTimeSeriesSink 真实 REST API 写入/读回 (5 tests, TCP+REST 两阶段探测 skipif) | TDengine REST API | MISSING_ENVIRONMENT (TDengine taosAdapter TCP 或 REST API 不可达) |
| `tests/integration/test_model_asset_postgres_integration.py` | model_asset 四表 PostgreSQL 持久化 (16 tests, DSN 未设置时 NOT_RUN, DSN 已设置但连接失败时 FAIL) | PostgreSQL | MISSING_ENVIRONMENT (DSN 未设置) / FAIL (DSN 已设置但连接失败) |
| `tests/e2e/test_whale_l5_kafka_pipeline_e2e.py` | Kafka pipeline E2E | Kafka/S3/TDengine/Redis | MISSING_ENVIRONMENT |
| `tests/e2e/test_whale_l5_storage_e2e.py` | 存储 E2E | S3/TDengine/Redis | MISSING_ENVIRONMENT |

#### 部署前验收期

| 测试文件 | 测试对象 | 外部依赖 | NOT_RUN 条件 |
|---------|---------|---------|------------|
| `tests/e2e/test_whale_field_minimal_smoke.py` | 现场最小数据链路 | docker-compose | MISSING_ENVIRONMENT |
| `scripts/run_whale_field_ready_smoke.sh` | 一键预检脚本 | docker-compose | MISSING_ENVIRONMENT |
| `docker-compose.p5.yml` | 最小 P5 本地编排（PG+Redis+Kafka/MinIO+TDengine+taosAdapter，含 healthcheck） | Docker | MISSING_ENVIRONMENT (Docker 不可用或未启动) |
| `scripts/start_whale_p5_dependencies.sh` | P5 外部依赖启动 | Docker | MISSING_ENVIRONMENT (Docker 不可用) |
| `scripts/stop_whale_p5_dependencies.sh` | P5 外部依赖停止/清理 | Docker | N/A (仅影响环境) |
| `scripts/diagnose_whale_p5_dependencies.sh` | P5 依赖诊断（5 依赖逐项 TCP+auth+minimal operation+脱敏） | PostgreSQL/Redis/Kafka/MinIO/TDengine | NOT_RUN (依赖不可达或环境变量未设置) |
| `scripts/run_whale_p5_external_dependency_regression.sh` | P5 全链路回归（5 测试组，逐项输出/SUMMARY/PASS 计数） | Kafka/PG/Redis/MinIO/TDengine | NOT_RUN (依赖不可达) |

### 3.2 source_lab 工具测试 (已废弃，Round 11 物理删除，Round 12 最终确认)

>  已于 Round 11 整目录物理删除。Round 12 最终确认：全仓零 dead import 路径，零死 fixture，零 source_lab shell 脚本残留。此段测试资产不再存在。
> 原有协议测试能力已由  覆盖。

### 回归来源分类

| 分类 | 说明 | 状态 |
|------|------|------|
| defect-regression | bug 修复后新增的回归测试 | 见下表 |
| operation-regression | 故障恢复、主备切换、重启恢复 | 见下表 |
| compatibility-regression | 协议版本、消息格式、API 版本兼容性 | 见下表 |
| chain-regression | 跨模块链路验证 | 见下表 |
| release-regression | 发布前指令套件 | 见下表 |

### 回归测试列表

| 测试 | 回归分类 | 状态 | 说明 |
|------|---------|------|------|
| `test_subscription_reconnect_baseline.py` | defect-regression | ACTIVE | 订阅重连基线验证 |
| `test_subscription_reconnect_runtime.py` | defect-regression | ACTIVE | 订阅重连运行时验证 |
| `test_dual_node_write_lease_conflict.py` | defect-regression | ACTIVE | 双节点写入冲突 |
| `test_ingest_write_lease_fencing.py` | defect-regression | ACTIVE | 写入租约 fencing |
| `test_ingest_prodlike_kafka_fault_injection.py` | operation-regression | ACTIVE | Kafka 故障注入恢复 |
| `test_ingest_prodlike_postgres_fault_injection.py` | operation-regression | ACTIVE | PostgreSQL 故障注入恢复 |
| `test_ingest_prodlike_redis_fault_injection.py` | operation-regression | ACTIVE | Redis 故障注入恢复 |
| `test_ingest_scheduler_active_standby_failover.py` | operation-regression | ACTIVE | 调度器主备故障转移 |
| `test_ingest_prodlike_worker_failover.py` | operation-regression | ACTIVE | worker crash/failover |
| `test_whale_writer_failure_recovery.py` | operation-regression | ACTIVE | writer 故障恢复 |
| `test_whale_writer_switchover.py` | operation-regression | ACTIVE | writer 主备切换 |
| `test_ingest_iec104_source_write.py` | defect-regression | ACTIVE | IEC104 写入验证 |
| `test_ingest_modbus_source_write.py` | defect-regression | ACTIVE | Modbus TCP 写入验证 |
| `test_ingest_opcua_source_write.py` | defect-regression | ACTIVE | OPC UA 写入验证 |
| `test_ingest_iec61850_mms_source_write.py` | defect-regression | ACTIVE | IEC61850 MMS 写入验证 |
| `test_ingest_prodlike_endurance_smoke.py` | operation-regression | ACTIVE | 耐久性烟测 |
| `test_ingest_prodlike_scheduler_backpressure.py` | operation-regression | ACTIVE | 调度背压与 missed tick |

## 5. 回归套件定义

| 套件 | 定义 | 执行时机 | 典型范围 |
|------|------|---------|---------|
| affected regression | 本轮变更影响的测试 | 每次变更 | 变更文件的对应测试 + 相关回归 |
| module regression | 模块内所有测试 | 修改 public interface/schema/config/protocol 时 | 模块 unit+integration |
| chain regression | 上下游链路测试 | 跨模块影响时 | 上下游模块的集成测试 |
| release regression | 发布前全量回归 | 发布前 | 全部 ACTIVE 状态回归测试 + module regression |

> release-regression 是回归套件组合，不是独立的生命周期阶段。它从各生命周期阶段
> （开发期验证、模块集成期验证、跨模块联调期验证、准生产依赖验证期、部署前验收期）
> 中选取 ACTIVE 状态的回归测试组合而成。执行时机为发布前，典型范围包括全部
> ACTIVE 回归测试和模块级回归。

### 套件执行命令参考

```bash
# affected regression (由 code-implementer 按变更范围选择)
pytest tests/unit/ -k "<related>" -q
pytest tests/integration/ -k "<related>" -q

# module regression (以 ingest 为例)
pytest tests/unit/ -k "ingest" -q
pytest tests/integration/ -k "ingest" -q

# chain regression (以 speed_layer->storage 为例)
pytest tests/unit/test_speed_layer_*.py tests/unit/test_storage_*.py -q
pytest tests/integration/test_speed_layer_*.py -q

# release regression (全量，不包括 slow/load/stress)
pytest -m "not slow and not load and not stress" -q
```

## 6. source_lab 测试边界 (已废弃，Round 11 物理删除，Round 12 最终确认)

>  已于 Round 11 物理删除。Round 12 最终确认零残留。此段测试隔离规则和扩跑条件不再适用。
> 协议测试已由 Starfish（）全面接管。

## 7. 维护规则

1. 新增测试文件：在此索引的"测试资产索引"中添加条目。
2. 新增回归测试：在"回归测试列表"中添加条目，标注回归分类和状态。
3. 删除测试文件：从此索引中移除条目；如涉及回归测试，将其状态改为 RETIRED 或 SUPERSEDED。
4. 回归测试状态变更（ACTIVE/RETIRED/SUPERSEDED）：在"回归测试列表"中更新状态和原因。
5. 目录结构变化：同步更新"测试资产索引"中的目录路径。
6. 不在此文件中维护具体测试函数名；只维护到文件级别（关键链路可维护到类级别）。
7. `tests/issue_trace.md` 可用于缺陷到测试覆盖的追踪，但不替代本索引。
8. 保留本文件为中文，测试文件和类名保留英文。
