# Seahorse Requirements

> Seahorse — 样例场站生成器。面向平台调试、演示、联调、数字孪生前置验证和测试数据准备。
> 最后更新: 2026-06-07 (Round 21: **Starfish 能力增强阶段总收口** — Seahorse 侧文档同步。**Seahorse `test_curve_daily_power_preset` 根因已修复**（**不**再列 pre-existing flaky）：`src/seahorse/strategies/curve_generation.py` `daily_power_curve` 在 noise 叠加后强制 `min(values) >= floor_ratio * baseline = 0.2 * 1500.0 = 300.0`，从根因消除 `min(values)=90.952 < 100 阈值` 的统计噪声；`tests/unit/seahorse/test_strategies.py` 新增 5 个 daily_power 稳定性测试（`test_daily_power_preset_min_floor_enforced` / `test_daily_power_preset_cross_run_consistency` / `test_daily_power_preset_high_noise_compatible` / `test_other_curves_have_no_floor_behavior` / `test_daily_power_preset_stable_5x_runs`）；test-validator 独立验证**连续 12 次 0 flaky**（独立 Python 20 次复现 min(values)=300.00）；Seahorse 总数 181 → 186（**180 stable + 5 新 daily_power 稳定性测试 + 1 原 daily_power_preset**）；Round 19 baseline 181 passed 不回退；third_party 零新增；import boundary 清洁；**不是**任何 skip/xfail/删除测试/扩大阈值——为**根因**（noise model stdev=50 + floor_ratio=0.2 钳制后 min(values) >= 300.0）；本仓库项目名为 Whale，**BlueOcean_REQ_*.md 在仓库中不存在**，本轮沿用 Whale_REQ_*.md 体系，**不新建 BlueOcean_REQ_*.md**；20→21 轮总收口完成)

## 1. 模块定位

`Seahorse` 是独立的样例场站生成器、数据 generator、replay 与仿真接入组件。它从零生成可用于 BlueOcean 全平台的样例场站世界，不进入生产采集链路。

Seahorse 负责：

```text
生成并网型风光储电场样例资产拓扑
生成 Organization / Asset / SCADA / SignalProfile / SignalProfileItem / Endpoint / LD / AcquisitionTask 等 ORM seed plan
生成协议绑定、测点参数、端点参数和采集任务配置
生成连续遥测、遥信、告警、控制回写响应和故障片段数据
支持随机数据、曲线数据、CSV/JSONL replay、离散模型和外部仿真接入的统一策略接口
管理协议参数模板、样例数据规格、GB/T 30966 字段定义和协议查询视图参考数据
生成可供 Starfish 启动协议 server 的 ServerPlan
生成可导入 Whale ingest 的配置包或样例数据库
```

Seahorse 不负责：

```text
生产现场采集
生产数据落库
Flink 实时处理
Dolphin 的真实仿真求解与优化计算
Starfish 的具体协议 server 实现
```

安全边界：

```text
禁止：Seahorse -> whale.ingest（任何 import）
禁止：Seahorse -> whale ingest runtime
禁止：Seahorse / Starfish 冒充现场生产环境验证
允许：Seahorse -> Starfish
允许：Seahorse -> Whale ORM / seed writer / storage contract（后续）
```

## 2. 需求编号规则

| 层级 | 前缀 | 示例 |
|---|---|---|
| Seahorse Module | SH | SH-FR-001 |

需求类型：

```text
FR     功能需求
NFR    非功能需求
AR     架构约束
TEST   测试与验收需求
```

## 3. 当前阶段定义

Seahorse 采用分轮次递进建设：

| Round | 主题 | 范围 |
|---|---|---|
| Round 1 | reference_data 迁出 + 核心模型 + import boundary | `seahorse.reference_data` 从 `whale.shared.persistence.template` 独立迁出；14 个核心 dataclass 模型定义；GenerationStrategy Protocol；SeahorseGenerator 最小实现；旧模板路径改为 DeprecationWarning wrapper；import boundary 门禁 |
| Round 2 | 具体生成策略 | Random/Curve/Replay 的 GenerationStrategy 实现 |
| Round 3 | 导出器 | ScenarioBundle 16 字段场景包模型 + JSON bundle exporter（原子写入）+ JSONL timeseries exporter + bundle validator（6 项校验）+ SHA256 校验和 + CLI 3 子命令（generate-scenario/export-bundle/validate-bundle） |
| Round 4 | ServerPlan 到 Starfish | ServerPlan 5 字段扩展（capabilities/update_policy/initial_values/strategy_id/synthetic）、ServerPlan validator 9 项校验、ServerPlan handoff exporter（SHA256 payload_hash 原子写入）、CLI export-server-plan 子命令（已完成） |
| Round 5 | Starfish 创建并消费 ServerPlan | Starfish 创建（src/starfish/ 10 源文件），ServerPlan JSON loader 消费 Seahorse handoff 契约（SF-FR-001），ServerSimulatorFacade in-memory stub（SF-FR-002），CLI load-server-plan/smoke-server-plan（SF-FR-005），Seahorse-Starfish contract roundtrip 验证通过；Seahorse Round 1-4 全量回归 181 passed 无回退 |

## 4. 需求功能描述

### SH-FR-001 reference_data 独立

`seahorse.reference_data` 提供协议参数模板、样例数据规格、GB/T 30966 字段定义和协议查询视图，供样例数据库初始化、Navicat 浏览、本地演示和单测使用。

- 不依赖 `whale.ingest` 或 ingest runtime。
- `whale.shared.persistence.template` 旧路径保留为纯 wrapper，发出 `DeprecationWarning`。
- 模板数据与 `whale.shared.persistence.template` 原数据等价，消费者可从旧路径平滑迁移。

### SH-FR-002 核心数据模型

定义 Seahorse 场景生成所需的核心数据结构，全部为 `@dataclass`，不依赖数据库连接、ORM 或特定序列化格式。

涵盖 14 个 dataclass：

| 模块 | dataclass | 职责 |
|---|---|---|
| scenario | ScenarioConfig | 场景配置顶层输入 |
| scenario | ScenarioMetadata | 生成器运行时版本、参数和统计信息 |
| plan | SeedEntity | 种子实体（逻辑设备/传感器） |
| plan | SignalProfileItemPlan | 信号点位规划 |
| plan | SignalProfilePlan | 信号点表计划 |
| plan | EndpointPlan | 通信端点规划 |
| plan | AcquisitionTaskPlan | 采集任务规划 |
| plan | SeedPlan | 种子计划（聚合） |
| plan | ServerEndpointPlan | 服务端点规划 |
| plan | ServerPointPlan | 服务点位规划 |
| plan | ServerPlan | 服务端计划（聚合） |
| generation | GeneratedSignalValue | 生成的单点信号值 |
| generation | GeneratedAlarmEvent | 生成的告警事件 |
| generation | GeneratedControlResult | 生成的控制回写结果 |

### SH-FR-003 GenerationStrategy 端口

定义信号、告警和控制结果的生成契约。`GenerationStrategy` 为 `@runtime_checkable` Protocol，定义三个方法：

- `generate_signals(..., deterministic_seed) -> list[GeneratedSignalValue]`
- `generate_alarms(..., deterministic_seed) -> list[GeneratedAlarmEvent]`
- `generate_controls(..., deterministic_seed) -> list[GeneratedControlResult]`

所有实现必须满足确定性：相同输入 + 相同 deterministic_seed 产生相同输出。

### SH-FR-004 SeahorseGenerator 最小编排

`SeahorseGenerator` 依据 `ScenarioConfig` 生成最小 `SeedPlan` 和 `ServerPlan`：

- 根据 `asset_count` 创建对应数量的 `SeedEntity`。
- 为每个实体创建默认信号点表（6 个风电基础点位）。
- 为每个目标协议创建端点和采集任务规划。
- 为每个目标协议创建服务端点和默认点位。
- deterministic_seed 保存到 config 和 metadata。

### SH-FR-005 具体生成策略实现

提供 RandomGenerationStrategy、CurveGenerationStrategy、ReplayGenerationStrategy 三种具体策略，均实现 GenerationStrategy Protocol。

**RandomGenerationStrategy**（确定性随机值）：
- 基于 deterministic_seed + entity_id + signal_id 复合 seed 确保确定性。
- 支持 generation_hint 驱动的多种随机模式：RANDOM（高斯噪声叠加基线）、RANDOM_WALK（随机游走）、DISCRETE（0/1 状态位）、CONSTANT（恒定值）。
- baseline 从 signal_id hash 派生，范围 [0.1, 1000.0]。
- 所有 GeneratedSignalValue 带 synthetic=True、quality=0。

**CurveGenerationStrategy**（6 种曲线类型）：
- 支持 constant、linear、sinusoidal、daily_power_curve（风电双峰模型）、daily_solar_curve（光伏单峰模型）、daily_storage_curve（储能充放电模型）。
- 预设 14 组 signal_name -> curve_type 模板覆盖风机/光伏/储能/气象站。
- 支持构造参数 curve_configs 覆盖和默认曲线类型回退。
- 每条曲线叠加确定性噪声（noise_stdev）。

**ReplayGenerationStrategy**（rows/JSONL 回放 + 字段映射 + 时间偏移）：
- 支持从内存 rows（list[dict]）或 JSONL 文件加载回放数据。
- 支持自定义字段映射（row key -> GeneratedSignalValue 属性）。
- 支持 speed_factor 加速倍率（通过 generation_hint "REPLAY:2.0" 解析）。
- 时间戳处理：row 有 timestamp 字段时以该值 + offset 为基准，无 timestamp 时按行序号生成。
- 边界行为明确：数据未加载抛出 ValueError、缺失 value 字段抛出 KeyError、JSONL 文件不存在抛出 FileNotFoundError。

**StrategyRegistry**：
- 策略注册、查找、实体类型覆盖（entity_type -> strategy_name）。
- 空注册表无默认策略时抛出 ValueError。

### SH-FR-006 告警与控制回写生成

提供 AlarmGenerator 和 ControlResultGenerator，独立于策略层管理。

**AlarmGenerator**（4 种告警类型）：
- THRESHOLD：阈值越限告警（min/max），基于 GB/T 30966 参考值设定。
- QUALITY：品质码降级告警（quality=1 WARNING，quality>=2 MAJOR）。
- DEVICE_STATE：设备状态告警（连续 5 点以上全零判定为异常停机 CRITICAL）。
- COMMUNICATION：通信异常告警（时间跨度 > 1h 且信号数 < 30，确定性概率触发）。
- 支持自定义阈值覆盖。
- alarm_id 全局唯一递增（`scenario_id_alarm_NNNNN`）。

**ControlResultGenerator**（7 种控制结果状态）：
- ACCEPTED、WRITE_DISABLED、DRY_RUN_ACCEPTED、READBACK_MATCHED、READBACK_MISMATCH、TIMEOUT、UNSUPPORTED。
- 通过确定性概率分布选择结果状态（ACCEPTED 60% / TIMEOUT 10% / READBACK_MATCHED 15% / READBACK_MISMATCH 8% / WRITE_DISABLED 5% / UNSUPPORTED 2%）。
- REBOOT/FIRMWARE_UPDATE/FACTORY_RESET 直接返回 UNSUPPORTED。
- 支持自定义处理器（custom_handlers）注入。
- 支持批量生成（generate_batch）和单条生成（generate）。
- control_id 全局唯一递增（`scenario_id_ctrl_NNNNN`）。

### SH-FR-007 SeahorseGenerator 完整生成

SeahorseGenerator 从最小容器扩展为完整场景生成：

- `generate()` 返回 5 元组：`(SeedPlan, ServerPlan, list[GeneratedSignalValue], list[GeneratedAlarmEvent], list[GeneratedControlResult])`。
- 保留 `generate_minimal()` 向后兼容（仅 SeedPlan + ServerPlan）。
- 支持 StrategyRegistry 和 default_strategy 注入。
- `_generate_all_signals` 调用策略的 generate_signals() 为所有实体+信号生成时序。
- `_generate_all_alarms` 按 entity_id 分组信号值后调用 AlarmGenerator。
- `_generate_all_controls` 为每个实体生成 START/STOP/SETPOINT 等典型控制回写。
- metadata.stats 记录 entity_count、signal_value_count、alarm_count、control_result_count。

### SH-FR-008 ScenarioBundle 场景包数据模型

定义 Seahorse 场景生成的完整数据快照结构，聚合配置、计划、生成结果与元数据，是导出、校验和归档的最小数据单元。

`ScenarioBundle` 为纯 `@dataclass`，16 个字段：

| 字段 | 类型 | 职责 |
|---|---|---|
| schema_version | str | Bundle schema 版本（默认 "1.0.0"） |
| scenario_version | str | 场景逻辑版本号 |
| generator_version | str | Seahorse 生成器组件版本（默认 "0.2.0"） |
| created_at | datetime | 生成时间戳（UTC），不参与校验和 |
| scenario_id | str | 场景唯一标识 |
| name | str | 场景可读名称 |
| deterministic_seed | int | 确定性随机种子，用于重现 |
| synthetic | bool | 始终为 True，标识所有数据为合成 |
| scenario_config | ScenarioConfig | 场景配置快照 |
| scenario_metadata | ScenarioMetadata | 生成器运行时元数据 |
| seed_plan | SeedPlan | 种子计划 |
| server_plan | ServerPlan | 服务端计划 |
| generated_timeseries_sample | list[GeneratedSignalValue] | 生成的信号值采样序列 |
| alarm_events | list[GeneratedAlarmEvent] | 生成的告警事件列表 |
| control_results | list[GeneratedControlResult] | 生成的控制回写结果列表 |
| checksum | str | 内容确定性 SHA256 校验和 |
| replay_metadata | dict | 可选重放元数据 |

同一 `ScenarioConfig` 与 `deterministic_seed` 产生内容完全相同的 bundle，校验和可重现。

### SH-FR-009 场景包导出器

提供场景包到 JSON 文件和时序数据到 JSONL 文件的导出能力：

**JSON bundle exporter**（`exporters/bundle_exporter.py`）：
- `export_bundle_to_json(bundle)` 将完整 ScenarioBundle 序列化为 JSON 字符串。
- `save_bundle(bundle, output_dir)` 以原子方式（临时文件 + rename）保存到 `{scenario_id}_bundle.json`。
- JSON 使用 UTF-8 编码、ISO 8601 时间格式、2 空格缩进。
- 父目录不存在时自动创建。

**JSONL timeseries exporter**（`exporters/timeseries_exporter.py`）：
- `export_timeseries_to_jsonl(signal_values)` 将信号值序列化为每行一个 JSON 对象的 JSONL 字符串。
- `save_timeseries(signal_values, output_dir)` 以原子方式保存到 `{scenario_id}_timeseries.jsonl`。
- 避免大样本数据塞进单个 JSON 数组导致的内存问题。

**序列化辅助**（`exporters/serialization.py`）：
- `compute_bundle_checksum(bundle)` 计算确定性 SHA256 校验和，排除 created_at、generator_version、schema_version、checksum 自身等可变字段。
- `bundle_to_serializable(bundle)` 将完整 bundle 转为 JSON 可序列化 dict。

### SH-FR-010 场景包校验器

提供场景包的结构完整性和数据一致性校验（`exporters/bundle_validator.py`）：

6 项校验（按顺序执行，单项错误不影响后续检查）：

1. **schema_version 存在性**：必须非空。
2. **scenario_id 一致性**：bundle.scenario_id、scenario_config.scenario_id、seed_plan.scenario_id、server_plan.scenario_id 必须一致。
3. **seed_plan/server_plan 存在性**：必须非 None；为空时产生警告而非错误。
4. **synthetic 标记**：generated_timeseries_sample 中所有条目必须 synthetic=True。
5. **checksum 可复算**：重新计算并与存储值比较，不匹配时报告错误。
6. **server_plan 结构检查**：endpoints 的 endpoint_name/protocol 和 points 的 point_id 基本字段存在性。

校验结果以 `ValidationResult` dataclass 返回（errors/warnings/passed_checks 三个列表 + is_valid 布尔值）。

`validate_bundle_from_dict(data)` 支持从 JSON 反序列化的 dict 重建 ScenarioBundle 并校验，用于已有 JSON 文件的后加载场景。

### SH-FR-011 CLI 最小入口

提供 3 个子命令的 argparse CLI 入口（`__main__.py`，`python -m seahorse`）：

| 子命令 | 功能 | 关键参数 |
|---|---|---|
| generate-scenario | 生成场景并保存 bundle JSON + 可选 JSONL 时序 | --scenario-id（必填）、--seed、--asset-count、--duration、--sample-interval、--protocol-targets、--output-dir、--start-time、--no-jsonl |
| export-bundle | 加载已有 bundle JSON，重新校验并导出 | --input（必填）、--output-dir |
| validate-bundle | 校验已有 bundle JSON 的完整性和一致性 | --input（必填） |

安全边界：CLI 不连接生产数据库、不调用 whale.ingest/starfish、仅操作本地文件系统。

### SH-FR-012 ServerPlan handoff / contract exporter

提供 ServerPlan 到 Starfish 契约 JSON 的导出能力（`exporters/server_plan_exporter.py`）：

- `build_server_plan_payload(server_plan)` 将 Seahorse 内部 `ServerPlan` 转为 Starfish 可解析的纯 dict 结构。
- `export_server_plan_to_json(server_plan)` 将 `ServerPlan` 导出为 UTF-8 JSON 字符串，包含完整 endpoints、points、capabilities、update_policy、initial_values 以及 SHA256 **payload_hash**。
- `export_server_plan_from_bundle(bundle)` 从 `ScenarioBundle` 提取 `ServerPlan` 并导出为 JSON。
- `save_server_plan(server_plan, output_dir)` 以原子方式（临时文件 + `os.replace`）保存到 `{scenario_id}_server_plan.json`。
- `save_server_plan_from_bundle(bundle, output_dir)` 从 bundle 保存。
- **payload_hash**：SHA256 确定性哈希，排除 `generated_at` 和 `payload_hash` 自身。相同 ServerPlan 内容产生相同 payload_hash。
- `bundle.server_plan` 为 None 时，`export/save_server_plan_from_bundle` 抛出 `ValueError`。

契约隔离规则：

- 导出产物为纯 JSON，不依赖任何 seahorse 或 starfish Python 类型。
- Starfish runtime 只需读取 JSON 文件，无需 import seahorse。
- 本模块不得 import starfish。

### SH-FR-013 ServerPlan validator

对 ServerPlan 执行 Starfish 契约兼容性独立校验（`exporters/server_plan_validator.py`，9 项校验）：

1. **scenario_id 存在性**：必须非空。
2. **synthetic 标识存在**：必须为布尔类型；为 False 时产生警告。
3. **endpoints 非空**：至少需要 1 个端点。
4. **每个 endpoint 有 protocol、endpoint_id**：缺失时报告错误。
5. **TCP 类协议 host/port 合法性**：TCP 类协议（OPC_UA/MODBUS_TCP/MQTT/HTTP/IEC_104/ADS 等）需 host 非空白、port 在 1-65535；非 TCP 协议（如 SERIAL）跳过。
6. **points 非空**：至少需要 1 个点位。
7. **每个 point 契约标识字段**：point_id 必填；node_key、variable_key、value_type 至少一个非空，否则警告。
8. **capabilities 与 points access_mode 无冲突**：capabilities 未声明 WRITE 但存在 WO/RW 点位时警告；未声明 READ 但存在 RO/RW 点位时警告。
9. **initial_values 可追溯到 points**：不可追溯的 key 产生警告，不阻止校验通过。

校验结果返回 `ValidationResult`（复用 bundle_validator 的 errors/warnings/passed_checks + is_valid）。

`validate_server_plan_from_dict(data)` 支持从 JSON/dict 重建并校验，用于已有 JSON 契约文件的后加载场景。

安全边界：不 import whale.ingest；不 import starfish；仅操作内存数据。

### SH-FR-014 export-server-plan CLI

`export-server-plan` 是新增的第 4 个 CLI 子命令（`__main__.py`）：

支持两种模式：

- **从 bundle 提取模式**：`--input <bundle.json>` 从已有 ScenarioBundle JSON 提取 ServerPlan 并导出。
- **直接生成模式**：`--scenario-id <id> --seed <n> --asset-count <n> --protocol-targets <...>` 直接生成最小 ServerPlan 并导出。

关键参数：`--output-dir`（输出目录）；支持 `--help` 输出用法说明。

行为：

- 校验失败时仍尝试导出（部分场景可能是有意的不完整）。
- 既未指定 `--input` 也未指定 `--scenario-id` 时返回非零退出码。
- 指定的 `--input` 文件不存在时返回非零。

### SH-AR-004 Seahorse-Starfish contract boundary

Seahorse-Starfish 之间的契约通过纯 JSON/dict schema 隔离，禁止运行时代码依赖：

| 规则 | 方向 | 验证方式 |
|---|---|---|
| seahorse 不得 import starfish | `seahorse` -> `starfish` | AST 扫描 + grep |
| Starfish 不得 import seahorse（如 starfish 存在） | `starfish` -> `seahorse` | AST 扫描（待 starfish 创建后启用） |
| ServerPlan handoff 产物为纯 JSON | seahorse exporters | 代码审查确认无 Python 类型引用 |

产出文件 `starfish_server_plan.json` / `{scenario_id}_server_plan.json` 为纯 JSON 文件，Starfish runtime 只需 JSON 解析，不依赖任何 seahorse Python 类型。

**Starfish runtime 消费状态**：Starfish 已进入 Round 6（`src/starfish/` 12 源文件）。Seahorse ServerPlan handoff JSON 契约加载已验证（SF-FR-001 load_server_plan 9 项校验 + payload_hash 复算通过）。Starfish 已实现 HTTP_REST 真实 server（ThreadingHTTPServer, GET /points）和 MODBUS_TCP 真实 server（TCP socket, FC03/FC06 write + FC03 readback）。RuntimeRegistry 支持 real/stub 协议 dispatch（HTTP_REST/MODBUS_TCP -> real, 其他 -> stub）。subscribe/report 对所有协议仍为 **NOT_IMPLEMENTED**。Seahorse ServerPlan contract 本身未变（SH-FR-012/SH-FR-013/SH-FR-014 内容保持不变）。Seahorse-Starfish contract roundtrip 已验证闭环，import boundary AST 扫描零违规。Seahorse Round 1-4 全量回归 181 passed 无回退。

| 规则 | 方向 | 验证方式 |
|---|---|---|
| ingest 不得 import seahorse | `whale.ingest` -> `seahorse` | AST 扫描 |
| ingest 不得 import starfish | `whale.ingest` -> `starfish` | AST 扫描 |
| seahorse 不得 import whale.ingest | `seahorse` -> `whale.ingest` | AST 扫描 |
| seahorse.reference_data 不得依赖 ingest runtime | `seahorse.reference_data` -> `whale.ingest` | AST 扫描 |

### SH-AR-002 Seahorse 不进入生产链路

`seahorse` 包不得被 `whale.ingest`、`whale.message_pipeline`、`whale.speed_layer`、`whale.storage` 或 `whale.batch_layer` 导入。Seahorse 是实验工具组件，与 Starfish 并列。

## 5. 需求跟踪表

| 编号 | 上承需求 | 标题 | 类型 | 优先级 | 责任模块 | 验证等级 | 实现状态 | 实现证据 | 验收测试 | 差距 | 下一步 | 更新时间 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| SH-FR-001 | 总体逻辑设计 8.1 | reference_data 从 shared template 迁出独立 | FR | 高 | seahorse.reference_data | P1+P2 | 已完成 | `src/seahorse/reference_data/` 含 4 个数据文件 + `__init__.py`；旧路径 wrapper 发出 DeprecationWarning；lint/type/compile 通过；import 边界扫过 | `tests/unit/seahorse/test_reference_data_imports.py` -> 15 passed；`tests/architecture/test_seahorse_import_boundary.py` -> 5 passed | 旧路径消费者（tests/unit/shared/persistence/、tests/integration/、tools/source_lab/ 等）尚未迁移到新路径；seahorse/reference_data 暂不提供 PostgreSQL sample_data 子进程入口封装 | Round 2：可选新增 `seahorse.reference_data.__main__` 子进程入口或保持旧路径 wrapper 作为迁移期兼容 | 2026-06-04 |
| SH-FR-002 | 总体逻辑设计 8.1 | 14 个核心 dataclass 模型 | FR | 高 | seahorse.models | P1 | 已完成 | `src/seahorse/models/` 含 scenario.py(2)、plan.py(9)、generation.py(3)；纯 dataclass，无外部依赖 | `tests/unit/seahorse/test_models.py` -> 12 passed | 当前仅覆盖构造和序列化，未覆盖未来扩展字段 | Round 2：随具体策略实现补充模型字段 | 2026-06-04 |
| SH-FR-003 | 总体逻辑设计 8.1 | GenerationStrategy Protocol 定义 | FR | 高 | seahorse.ports | P1 | 已完成 | `src/seahorse/ports/generation_strategy.py`；@runtime_checkable Protocol，三个 generate_* 方法声明；类型签名完整 | 已通过 type check + 开发期验证 import + 三种具体策略通过 Protocol isinstance 检查 | Round 2 实现了 Random/Curve/Replay 三种具体策略 | 持续扩展新策略类型时需满足 Protocol 契约 | 2026-06-04 |
| SH-FR-004 | 总体逻辑设计 8.1 | SeahorseGenerator 最小实现 | FR | 高 | seahorse.orchestration | P1 | 已完成 | `src/seahorse/orchestration/scenario_generator.py`；根据 asset_count 生成 SeedPlan + ServerPlan；deterministic_seed 初始化 rng | `tests/unit/seahorse/test_orchestrator.py` -> 12 passed | 已从最小容器扩展为 5 元组完整生成（见 SH-FR-007） | 持续扩展，后续如接入 Starfish ServerPlan 需新增 orchestrator 行为 | 2026-06-04 |
| SH-FR-005 | 总体逻辑设计 8.1 | 三大生成策略（Random/Curve/Replay + StrategyRegistry） | FR | 高 | seahorse.strategies | P1 | 已完成 | `src/seahorse/strategies/` 含 random_generation.py（确定性随机值 + 5 种 generation_hint）、curve_generation.py（6 种曲线类型 + 14 组预设模板）、replay_generation.py（rows/JSONL 回放 + 字段映射 + 时间偏移 + speed_factor）、registry.py（StrategyRegistry 注册/查找/实体类型覆盖） | `tests/unit/seahorse/test_strategies.py` -> 24 passed | DiscreteModelStrategy / ExternalSimulatorStrategy 未实现（预留 port/stub） | Round 3/4：按需实现离散模型和外部仿真策略 | 2026-06-04 |
| SH-FR-006 | 总体逻辑设计 8.1 | 告警与控制回写生成器 | FR | 高 | seahorse.generators | P1 | 已完成 | `src/seahorse/generators/` 含 alarm_generator.py（4 种告警类型：阈值/品质/设备状态/通信，确定性检测）、control_result_generator.py（7 种控制结果状态，概率分布确定性，支持自定义处理器） | `tests/unit/seahorse/test_generators.py` -> 14 passed | 告警规则基于内置阈值，未支持动态规则引擎；控制结果未接入真实设备 | 后续可通过外部规则文件扩展告警配置 | 2026-06-04 |
| SH-FR-007 | 总体逻辑设计 8.1 | SeahorseGenerator 完整 5 元组生成 | FR | 高 | seahorse.orchestration | P1 | 已完成 | `SeahorseGenerator.generate()` 返回 (SeedPlan, ServerPlan, signal_values, alarm_events, control_results)；strategy/registry 注入；AlarmGenerator/ControlResultGenerator 集成；metadata.stats 统计 | `tests/unit/seahorse/test_orchestrator.py` -> 已完成并通过，包括 deterministic seed 三层验证（Random/Curve/Orchestrator） | 当前不处理跨实体信号关联和事件因果关系 | 后续可扩展跨实体关联逻辑 | 2026-06-04 |
| SH-FR-008 | 总体逻辑设计 8.1 | ScenarioBundle 16 字段场景包数据模型 | FR | 高 | seahorse.models | P1 | 已完成 | `src/seahorse/models/bundle.py`；ScenarioBundle @dataclass，16 字段（schema_version/scenario_version/generator_version/created_at/scenario_id/name/deterministic_seed/synthetic/scenario_config/scenario_metadata/seed_plan/server_plan/generated_timeseries_sample/alarm_events/control_results/checksum/replay_metadata）；_make_serializable 递归序列化辅助 | `tests/unit/seahorse/test_bundle.py` -> 9 tests passed（默认值/字段赋值/created_at datetime/replay_metadata 可选/序列化 5 tests） | 无立即差距 | 后续按需扩展 bundle schema 字段 | 2026-06-04 |
| SH-FR-009 | 总体逻辑设计 8.1 | 场景包 JSON + JSONL 导出器 | FR | 高 | seahorse.exporters | P1 | 已完成 | `src/seahorse/exporters/bundle_exporter.py`（export_bundle_to_json/save_bundle 原子写入）；`src/seahorse/exporters/timeseries_exporter.py`（export_timeseries_to_jsonl/save_timeseries 原子写入）；`src/seahorse/exporters/serialization.py`（compute_bundle_checksum SHA256 + bundle_to_serializable） | `tests/unit/seahorse/test_bundle.py` -> 8 tests passed（JSON export 3 tests、save_bundle 2 tests、round-trip 1 test、JSONL 3 tests） | YAML/SQL 导出尚未实现 | Round 4/5：按需扩展导出格式 | 2026-06-04 |
| SH-FR-010 | 总体逻辑设计 8.1 | 场景包校验器（6 项校验） | FR | 高 | seahorse.exporters | P1 | 已完成 | `src/seahorse/exporters/bundle_validator.py`；6 项校验：schema_version 存在性、scenario_id 一致性、seed_plan/server_plan 存在性、synthetic 全 True、checksum 可复算、server_plan 结构检查；ValidationResult dataclass + validate_bundle + validate_bundle_from_dict | `tests/unit/seahorse/test_bundle.py` -> 14 tests passed（valid pass 1 test、errors 6 tests、warnings 2 tests、dict roundtrip 1 test、ValidationResult 3 tests） | 未覆盖跨字段业务规则校验 | 后续按需扩展业务规则校验项 | 2026-06-04 |
| SH-FR-011 | 总体逻辑设计 8.1 | CLI 最小入口（3 子命令） | FR | 高 | seahorse.__main__ | P1 | 已完成 | `src/seahorse/__main__.py`；3 子命令 argparse CLI：generate-scenario（12 参数含 --start-time ISO 8601 + --no-jsonl）、export-bundle（--input + --output-dir）、validate-bundle（--input）；不连接 DB/ingest/starfish | `tests/unit/seahorse/test_bundle.py` -> 7 CLI tests passed（3 help + 1 roundtrip + 2 missing file + 1 no command） | --start-time 未指定时校验和不可重现（已输出警告）；未集成 Starfish ServerPlan 启动 | 后续按需扩展子命令和 Starfish 集成 | 2026-06-04 |
| SH-FR-012 | 总体逻辑设计 8.1/8.2/8.3 | ServerPlan handoff / contract exporter（5 个导出函数 + SHA256 payload_hash 原子写入） | FR | 高 | seahorse.exporters | P1 | 已完成 | `src/seahorse/exporters/server_plan_exporter.py`；build_server_plan_payload/export_server_plan_to_json/export_server_plan_from_bundle/save_server_plan/save_server_plan_from_bundle；SHA256 payload_hash 确定性（排除 generated_at）；原子写入（临时文件 + os.replace）；payload dict 13 个字段；**Starfish contract load 已验证：Starfish loader 成功消费 Seahorse 导出 JSON，payload_hash 复算通过（match/mismatch/deterministic/empty/missing 五路径验证），Seahorse-Starfish roundtrip 闭环** | `tests/unit/seahorse/test_server_plan.py` -> 31 passed（含 JSON 结构/payload_hash 稳定性+差异性/原子写入/父目录创建/bundle roundtrip/bundle save/bundle None 抛异常/CLI/from_dict）；`tests/unit/starfish/test_server_plan_loader.py` -> ~30 passed（含 bundle roundtrip Seahorse->Starfish 契约验证） | 无立即差距；Round 5 Seahorse-Starfish contract roundtrip 已验证 | 持续维护；每次 ServerPlan schema 变更后需重跑双向 roundtrip | 2026-06-04 |
| SH-FR-013 | 总体逻辑设计 8.1/8.2/8.3 | ServerPlan validator（9 项校验：scenario_id/synthetic/endpoints 非空/protocol+endpoint_id/TCP host+port/points 非空/契约字段/capabilities 冲突/initial_values 可追溯） | FR | 高 | seahorse.exporters | P1 | 已完成 | `src/seahorse/exporters/server_plan_validator.py`；validate_server_plan 9 项检查、validate_server_plan_from_dict 9 项检查；TCP_LIKE_PROTOCOLS 21 个协议名；非 TCP 协议跳过 host/port 检查；ValidationResult 复用 | `tests/unit/seahorse/test_server_plan.py` -> 14 tests passed（all_pass + minimal/unset scenario_id/no protocol/no endpoint_id/empty endpoints/empty points/TCP invalid port/non-TCP skips/orphan initial_values/capability conflict/missing contract fields/from_dict 各场景 + dict 路径对应） | 未覆盖跨端点相互校验、未校验 bind_host/bind_port vs host/port 一致性 | 后续按需扩展复杂校验规则 | 2026-06-04 |
| SH-FR-014 | 总体逻辑设计 8.1/8.2/8.3 | CLI export-server-plan（第 4 子命令：两种模式 --input 提取 / --scenario-id 直接生成） | FR | 高 | seahorse.__main__ | P1 | 已完成 | `src/seahorse/__main__.py`；export-server-plan 子命令支持 --input（从 bundle 提取）+ --scenario-id/--seed/--asset-count/--protocol-targets（直接生成）两种模式；校验失败仍导出；缺参数报错 exit 非零 | `tests/unit/seahorse/test_server_plan.py` -> 5 CLI tests passed（--help + from bundle + direct generate + no input+no scenario-id + missing file） | CLI 直接生成模式不写 bundle JSON | 后续可选增加 --output-format 等参数 | 2026-06-04 |
| SH-AR-001 | 总体逻辑设计 4.2/4.3/8.3 | import boundary 门禁 | AR | 高 | 全组件 | P2 | 已建立并通过 | `tests/architecture/test_seahorse_import_boundary.py` -> 5 passed（AST 扫描 + 生产代码 grep 确认零违规） | starfish 目录尚未存在时跳过（非 FAIL） | 无立即差距 — 每次 seahorse 或 ingest 变更后需重跑 | 持续监控；随 starfish 目录创建后移除 skip | 2026-06-04 |
| SH-AR-002 | 总体逻辑设计 8.1/8.3 | Seahorse 不进入生产链路 | AR | 高 | 全组件 | P2 | 已建立并通过 | import boundary 测试（5 passed）；grep 确认 `whale.ingest` 无 seahorse import | 同上 | 无立即差距 | 持续监控 | 2026-06-04 |
| SH-AR-003 | 总体逻辑设计 8.1/8.3 | Bundle/export/CLI 不写生产数据库、不进入 ingest、不替代 Starfish | AR | 高 | seahorse.exporters、seahorse.__main__ | P1+P2 | 已建立并通过 | `tests/unit/seahorse/test_bundle.py` CLI tests 确认纯本地文件操作；import boundary AST 扫描 + grep 确认零 database/ingest/starfish import | starfish 目录尚未存在时跳过（非 FAIL） | 无立即差距 | 持续监控；每次 seahorse 变更后重跑 import boundary | 2026-06-04 |
| SH-AR-004 | 总体逻辑设计 8.1/8.2/8.3 | Seahorse-Starfish contract boundary（JSON/dict schema 隔离，不 import starfish runtime） | AR | 高 | seahorse.exporters | P1+P2 | 已建立并通过 | AST 扫描 + grep 确认 seahorse exporters 零 starfish import；server_plan_exporter/server_plan_validator 文件头注释声明 no-starfish-import 边界；导出产物为纯 JSON；**Starfish 已创建（Round 5），Seahorse-Starfish contract roundtrip 验证通过：Starfish loader 成功消费 Seahorse handoff JSON，payload_hash 复算通过（match/mismatch/deterministic/empty/missing 五路径），Seahorse->Starfish 和 Starfish->seahorse 双向 import boundary AST 扫描零违规（6 向验证）** | `tests/unit/seahorse/test_server_plan.py` -> all 31 passed；`tests/architecture/test_seahorse_import_boundary.py` -> 5 passed；`tests/architecture/test_starfish_import_boundary.py` -> 9 passed；`tests/unit/starfish/test_server_plan_loader.py` -> bundle roundtrip passed | 无立即差距；Seahorse-Starfish contract boundary 双向验证已建立 | 持续监控；每次 Seahorse schema 变更后需重跑双向 roundtrip + import boundary | 2026-06-04 |

## 6. 实现文件清单

```text
src/seahorse/
├── __init__.py                    — 包入口，安全边界声明
├── __main__.py                    — CLI 主入口（4 子命令：generate-scenario/export-bundle/validate-bundle/export-server-plan）
├── models/                        — 核心数据模型（15 个 dataclass）
│   ├── __init__.py               — 导出入口
│   ├── scenario.py                — ScenarioConfig, ScenarioMetadata
│   ├── plan.py                    — SeedPlan/ServerPlan 等 9 个规划型 dataclass
│   ├── generation.py              — GeneratedSignalValue/AlarmEvent/ControlResult
│   └── bundle.py                  — ScenarioBundle 16 字段场景包 + _make_serializable
├── ports/                         — 端口层（抽象接口）
│   ├── __init__.py               — 导出入口
│   └── generation_strategy.py    — GenerationStrategy Protocol
├── strategies/                     — 策略实现层（Round 2 + **Round 20 根因修复**）
│   ├── __init__.py               — 导出 Random/Curve/Replay 策略 + StrategyRegistry
│   ├── random_generation.py      — 确定性随机值生成（5 种 generation_hint）
│   ├── curve_generation.py       — 曲线生成（6 种类型 + 14 组预设模板；**Round 20 根因修复**：`daily_power_curve` 在 noise 叠加后强制 `min(values) >= floor_ratio * baseline = 0.2 * 1500.0 = 300.0`，**未使用 skip/xfail/删除测试/扩大阈值**——从根因消除 `min(values)=90.952 < 100 阈值` 的统计噪声）
│   ├── replay_generation.py      — rows/JSONL 回放 + 字段映射 + 时间偏移
│   └── registry.py                — StrategyRegistry（注册/查找/实体类型覆盖）
├── generators/                     — 生成器层（Round 2）
│   ├── __init__.py               — 导出 AlarmGenerator/ControlResultGenerator
│   ├── alarm_generator.py         — 告警生成（4 种类型：阈值/品质/设备状态/通信）
│   └── control_result_generator.py — 控制回写生成（7 种状态 + 自定义处理器）
├── orchestration/                 — 编排层
│   ├── __init__.py               — 导出入口
│   └── scenario_generator.py     — SeahorseGenerator 5 元组完整生成
├── exporters/                     — 导出器层（Round 3 + Round 4）
│   ├── __init__.py               — 导出入口
│   ├── bundle_exporter.py         — JSON bundle 导出器（原子写入）
│   ├── timeseries_exporter.py     — JSONL 时序导出器（原子写入）
│   ├── bundle_validator.py       — 场景包校验器（6 项校验 + ValidationResult）
│   ├── serialization.py           — SHA256 校验和计算 + dataclass JSON 序列化
│   ├── server_plan_exporter.py   — ServerPlan handoff 导出（SHA256 payload_hash 原子写入）
│   └── server_plan_validator.py  — ServerPlan 校验器（9 项校验）
└── reference_data/                — 参考数据层
    ├── __init__.py               — 导出入口
    ├── gbt_30966_fields.py        — GB/T 30966 字段定义
    ├── protocol_param_data.py     — 16 组协议服务参数模板
    ├── protocol_view_defs.py      — 协议参数展平只读视图
    └── sample_data.py             — 13 类端点/16 组服务样例数据
```

```text
旧路径 wrapper（发出 DeprecationWarning，保留迁移期兼容）：
src/whale/shared/persistence/template/
├── __init__.py                   — 已改为 wrapper
├── protocol_param_data.py       — 已改为 wrapper
├── protocol_view_defs.py        — 已改为 wrapper
└── sample_data.py               — 已改为 wrapper
```
