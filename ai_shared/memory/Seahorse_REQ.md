# Seahorse Requirements

> Seahorse — 样例场站生成器。面向平台调试、演示、联调、数字孪生前置验证和测试数据准备。
> 最后更新: 2026-07-01 (Round 8: **v4.1 + v4.2 Clean Architecture 对齐** + **sample_data 迁回 whale.shared.persistence.template** — v4.1 闭环 adapters/controllers/ 删除、3 driver shim 删除、`__main__.py` 薄 argparse 入口、`api/seahorse_cli.py` 白名单 helper、老 CLI 收敛；**v4.2 进一步闭环**：物理删除 `src/seahorse/api/seahorse_cli.py`（v4.2 蓝图 §5.2 / §5.3 不再放 `<package>_cli.py`），CLI 入口完全收敛到 `src/seahorse/__main__.py` 并由 argparse 改写为 Typer（4 子命令：`generate-scenario` / `export-bundle` / `validate-bundle` / `export-server-config`）；`__main__.py` AST 零 `seahorse.application` / `seahorse.adapters` / `seahorse.infrastructure` / `seahorse.domain` import，且不构造 `ScenarioConfig` / backend / scheduler / repository / writer / ORM session；`SeahorseFacade` 新增 2 个 CLI 专用 primitives wrapper（`generate_bundle_from_cli_params` / `generate_minimal_server_config_from_cli_params`）内部统一构造 `ScenarioConfig`，CLI 自身不构造 domain model；`pyproject.toml` 核心 `dependencies` 段第 23 行新增 `typer>=0.20,<1.0`；`tests/unit/architecture/test_seahorse_import_boundary.py` 新增 7 项 v4.2 守护（`api` 下无 `*_cli.py` / `cli.py` / `controllers.py`（×3）+ `__main__.py` 使用 Typer 禁 argparse + 只依赖标准库 / typer / seahorse + AST 零内层 import + AST 零 `ScenarioConfig` + 不构造 backend / scheduler / repository / writer）+ `tests/unit/seahorse/test_main_typer_cli.py` 新增 25+ 项 CLI 行为测试（4 子命令端到端 + error path + `--no-jsonl` + `--protocol-targets` 逗号分隔 + `main()` 返回 int）；`tests/unit/seahorse/test_bundle.py` + `tests/unit/seahorse/test_server_plan.py` 旧 argparse CLI 测试已迁移到 Typer CLI 测试形态；import boundary **44+ / 44+ PASS**（v4.1 既有 37 项 + v4.2 新增 7 项）；`tests/unit/seahorse` + `tests/unit/architecture` 合计 **348 / 348 PASS**；**sample_data 迁回**（v4.2 子步）：`src/whale/shared/persistence/template/sample_data.py`（1167 行）从 `src/seahorse/infrastructure/repositories/whale_metadata_repository.py`（1427 → 293 行）拆分迁回，仅承载 16 组 `PROTOCOL_SAMPLE_SPECS` + `ProtocolSampleSpec` + `generate_all_sample_data` / `clear_database_data` / `reset_sample_data` + 全部 `_create_*` / `_seed_*` / `_resolve_*` / `_build_*` helpers，不依赖任何 `seahorse.*` 模块；`whale_metadata_repository` 职责收缩为 Seahorse WritePlan 只读映射 + 入口薄包装委托；`whale.shared.persistence.template.__init__` 扩展为 17 个 re-export（新增 5 个 A 类符号）；`seahorse.infrastructure.repositories.__init__` 不再 export A 类 5 符号；`src/whale/ingest/framework/persistence/init_db.py:52` 悬挂 import 自然恢复；`tests/unit/architecture/test_seahorse_import_boundary.py` 46 passed / `tests/unit/seahorse/test_reference_data_imports.py` 10 passed / `tests/unit/shared/persistence/test_scada_sample_data_protocol_coverage.py` 3 passed（从 broken 自然变 passing） / `tests/unit/shared/persistence/` 31 passed / `tests/unit/seahorse/` 302 passed；本轮不修改源码与测试，仅按已验证证据归档 project_tree / Seahorse_REQ 状态；handoff 文本偏差：code-implementer handoff 示例命令中的 `--start-time` 在 `export-server-config` 子命令未声明，属 handoff 文本偏差而非代码缺陷，由 test-validator 独立验证确认；**v4.2 与蓝图不一致项 0 类例外**——本轮无 compat wrapper / shim / DeprecationWarning / legacy 命名，无 Architecture Exception 需要登记；范围外遗留按 handoff 隔离（`tests/unit/starfish/test_runtime_api.py::test_manager_path_input_delegates_runtime_build_to_composition_root` pre-existing / 27 environment-pending skips 缺 native 动态库）；报告归档 `ai_shared/reports/seahorse_clean_architecture_v4_2_typer_cli.md`)

**v4.1 上下文**（按 `docs/clean_architecture.md` v4.1 蓝图收敛 `src/seahorse/`）：`adapters/controllers/` 物理删除（v4.1 蓝图 §5.2 / §5.9 不再默认承载 CLI Controller）；`adapters/drivers/curve_generation.py` / `random_generation.py` / `replay_generation.py` 共 3 个生成策略 shim 删除（真实策略实现在 `application/use_cases/`，v4.1 蓝图 §4.4 规则 6）；新增 `src/seahorse/api/seahorse_cli.py` 薄 CLI helper（v4.1 蓝图 §5.3 可选白名单 `<package>_cli.py`），4 子命令（`generate-scenario` / `export-bundle` / `validate-bundle` / `export-server-config`），仅调用 `SeahorseFacade`；`src/seahorse/__main__.py` 改为薄入口（仅 `from seahorse.api.seahorse_cli import main` + `sys.exit(main())`，AST 零 `seahorse.application` / `seahorse.adapters` / `seahorse.infrastructure` import，且不构造 backend / scheduler / repository / writer）；`SeahorseFacade` 扩展稳定门面方法（`save_timeseries` / `export_timeseries_jsonl` / `generate_minimal_server_config` / `validate_server_config` / `load_server_config_from_bundle_json` / `generator_metadata_stats` 等）；`tests/unit/architecture/test_seahorse_import_boundary.py` 新增 9 项 v4.1 守护（`test_seahorse_controllers_directory_removed` / `test_seahorse_adapters_has_no_controllers_subdir` / `test_seahorse_drivers_shim_generation_files_removed`（×3 参数化）/ `test_seahorse_main_does_not_import_application_adapters_infrastructure` / `test_seahorse_main_does_not_create_backend_or_runtime` / `test_application_domain_do_not_import_adapters_infrastructure_api` / `test_seahorse_root_does_not_import_starfish`）；import boundary **37 / 37 PASS**（28 既有 + 9 v4.1 新增）；`tests/unit/seahorse` + `tests/unit/architecture` 合计 **313 / 313 PASS**（37 boundary + 276 seahorse）；CLI 4 子命令端到端 + bundle checksum 跨命令一致（`90e7288dba896d7f...`）；老 CLI 子命令（`generate` / `validate` / `plan` / `runtime-smoke`）按 v4.1 蓝图要求被 argparse 拒绝（exit 2，无 compat shim / DeprecationWarning / 兼容 wrapper）；**v4.1 与蓝图不一致项 5 类全部闭合**（adapters/controllers 删除 / 3 driver shim 删除 / `__main__` 薄入口 / `api/<package>_cli.py` 白名单 / 老 CLI 收敛）；范围外遗留按 handoff 隔离（`test_runtime_api.py::test_manager_path_input_delegates_runtime_build_to_composition_root` pre-existing / `test_scada_sample_data_protocol_coverage.py` sample_data 已删 / 27 environment-pending skips 缺 native 动态库）；报告归档 `ai_shared/reports/seahorse_clean_architecture_v4_1_alignment.md`；v4.1 收口后 `api/seahorse_cli.py` 在 v4.2 进一步删除，v4.2 报告归档 `ai_shared/reports/seahorse_clean_architecture_v4_2_typer_cli.md`

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
生成可导入 whale.ingest 的配置包或样例数据库
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
允许：Seahorse -> whale ORM / seed writer / storage contract（后续）
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
| SH-R7B-001 | Seahorse_REQ Round 7B 硬清理 | 删除 `seahorse.models` 旧顶层目录及其 5 个文件（`__init__.py` / `bundle.py` / `generation.py` / `plan.py` / `scenario.py`），物理删除，无 compat wrapper、无 DeprecationWarning | CLEANUP | 高 | src/seahorse | P2 | 已完成 | `git status` 35 项删除；`ls src/seahorse/models` 不存在；`find src/seahorse -maxdepth 1 -type d` 仅返回 `__pycache__` 与 5 个新架构目录；用户明确要求"不要管兼容问题，不要留历史尾巴" | `tests/unit/architecture/test_seahorse_import_boundary.py::test_legacy_top_directories_removed[models]` PASS；`test_legacy_top_packages_not_importable[seahorse.models]` PASS；`tests/unit/seahorse/test_compat_wrappers.py::test_legacy_top_dirs_removed[models]` PASS；`test_legacy_top_packages_not_importable[seahorse.models]` PASS；4 个 `test_legacy_leaf_modules_not_importable`（scenario/plan/generation/bundle）PASS；`test_seahorse_package_root_has_no_legacy_name` PASS；`test_seahorse_domain_init_does_not_advertise_legacy_models` PASS | 旧 public import `seahorse.models` 已破坏，这是用户预期（无兼容尾巴）；范围外残留 `tests/unit/starfish/test_server_plan_loader.py` 与 `test_starfish_cli.py` 中 6 处旧 import 未迁移（handoff forbidden） | 下一轮：迁移 starfish 测试中的 6 处 `seahorse.models` 旧 import | 2026-06-30 |
| SH-R7B-002 | Seahorse_REQ Round 7B 硬清理 | 删除 `seahorse.exporters` 旧顶层目录及其 9 个文件（`__init__.py` + 8 个 exporter/validator/serialization），物理删除，无 compat wrapper | CLEANUP | 高 | src/seahorse | P2 | 已完成 | `git status` 9 项删除；`find src/seahorse -maxdepth 1 -type d` 无 `exporters`；`seahorse.adapters.gateways.server_plan_handoff_gateway` / `bundle_validator` 已被 `tests/unit/seahorse/test_server_plan.py` / `test_bundle.py` 替代引用 | `test_legacy_top_directories_removed[exporters]` PASS；`test_legacy_top_packages_not_importable[seahorse.exporters]` PASS；`test_compat_wrappers` ×8 `test_legacy_leaf_modules_not_importable`（bundle_exporter / bundle_validator / server_config_exporter / server_config_validator / server_plan_exporter / server_plan_validator / serialization / timeseries_exporter）PASS；`test_no_legacy_seahorse_imports_in_repo[seahorse]` AST 扫描无 `seahorse.exporters` 命中 | 旧 public import `seahorse.exporters` 已破坏，这是用户预期（无兼容尾巴）；范围外残留 `tests/unit/starfish/test_server_plan_loader.py` 与 `test_starfish_cli.py` 中 4 处旧 import 未迁移（handoff forbidden） | 下一轮：迁移 starfish 测试中的 4 处 `seahorse.exporters` 旧 import | 2026-06-30 |
| SH-R7B-003 | Seahorse_REQ Round 7B 硬清理 | 删除 `seahorse.strategies` 旧顶层目录及其 5 个文件（`__init__.py` + random/curve/replay/registry），物理删除，无 compat wrapper | CLEANUP | 高 | src/seahorse | P2 | 已完成 | `git status` 5 项删除；`seahorse.application.use_cases.{random_generation,curve_generation,replay_generation,strategy_registry}` 已承载业务实现 | `test_legacy_top_directories_removed[strategies]` PASS；`test_legacy_top_packages_not_importable[seahorse.strategies]` PASS；`test_compat_wrappers` ×4 `test_legacy_leaf_modules_not_importable`（curve_generation / random_generation / replay_generation / registry）PASS；`tests/unit/seahorse/test_strategies.py` 已切到新路径并 304 项套件中通过 | 旧 public import `seahorse.strategies` 已破坏，这是用户预期（无兼容尾巴） | 持续维护新路径 `seahorse.application.use_cases.*` | 2026-06-30 |
| SH-R7B-004 | Seahorse_REQ Round 7B 硬清理 | 删除 `seahorse.generators` 旧顶层目录及其 3 个文件（`__init__.py` + alarm_generator + control_result_generator），物理删除，无 compat wrapper | CLEANUP | 高 | src/seahorse | P2 | 已完成 | `git status` 3 项删除；`seahorse.application.use_cases.{alarm_generator,control_result_generator}` 已承载业务实现 | `test_legacy_top_directories_removed[generators]` PASS；`test_legacy_top_packages_not_importable[seahorse.generators]` PASS；`test_compat_wrappers` ×2 `test_legacy_leaf_modules_not_importable`（alarm_generator / control_result_generator）PASS；`tests/unit/seahorse/test_generators.py` 已切到新路径并 304 项套件中通过；`test_seahorse_use_cases_init_does_not_advertise_legacy_paths` PASS | 旧 public import `seahorse.generators` 已破坏，这是用户预期（无兼容尾巴） | 持续维护新路径 `seahorse.application.use_cases.*` | 2026-06-30 |
| SH-R7B-005 | Seahorse_REQ Round 7B 硬清理 | 删除 `seahorse.orchestration` 旧顶层目录及其 2 个文件（`__init__.py` + scenario_generator），物理删除，无 compat wrapper | CLEANUP | 高 | src/seahorse | P2 | 已完成 | `git status` 2 项删除；`seahorse.application.use_cases.scenario_generator.SeahorseGenerator` 已承载业务实现 | `test_legacy_top_directories_removed[orchestration]` PASS；`test_legacy_top_packages_not_importable[seahorse.orchestration]` PASS；`test_compat_wrappers` ×1 `test_legacy_leaf_modules_not_importable[orchestration.scenario_generator]` PASS；`tests/unit/seahorse/test_orchestrator.py` 已切到 `seahorse.application.use_cases.scenario_generator` 并 304 项套件中通过；`test_seahorse_use_cases_init_does_not_advertise_legacy_paths` PASS | 旧 public import `seahorse.orchestration` 已破坏，这是用户预期（无兼容尾巴）；范围外残留 `tests/unit/starfish/test_server_plan_loader.py` 与 `test_starfish_cli.py` 中 2 处旧 import 未迁移（handoff forbidden） | 下一轮：迁移 starfish 测试中的 2 处 `seahorse.orchestration` 旧 import | 2026-06-30 |
| SH-R7B-006 | Seahorse_REQ Round 7B 硬清理 | 删除 `seahorse.ports` 旧顶层目录及其 2 个文件（`__init__.py` + generation_strategy），物理删除，无 compat wrapper | CLEANUP | 高 | src/seahorse | P2 | 已完成 | `git status` 2 项删除；`seahorse.application.ports.generation_strategy_port.GenerationStrategyPort` 已承载业务实现 | `test_legacy_top_directories_removed[ports]` PASS；`test_legacy_top_packages_not_importable[seahorse.ports]` PASS；`test_compat_wrappers` ×1 `test_legacy_leaf_modules_not_importable[ports.generation_strategy]` PASS | 旧 public import `seahorse.ports` 已破坏，这是用户预期（无兼容尾巴）；本轮范围内无外部残留 | 持续维护新路径 `seahorse.application.ports.*` | 2026-06-30 |
| SH-R7B-007 | Seahorse_REQ Round 7B 硬清理 | 删除 `seahorse.reference_data` 旧顶层目录及其 5 个文件（`__init__.py` + gbt_30966_fields + protocol_param_data + protocol_view_defs + sample_data），物理删除，无 compat wrapper；`whale_metadata_repository` 改为 import `whale.shared.persistence.template.*` | CLEANUP | 高 | src/seahorse | P2 | 已完成 | `git status` 5 项删除；`src/seahorse/infrastructure/repositories/whale_metadata_repository.py` 切到 `whale.shared.persistence.template.{protocol_param_data,gbt_30966_fields}` 等新 import 路径；`sample_data` 在 v4.2 子步已迁回 `whale.shared.persistence.template.sample_data`（独立文件） | `test_legacy_reference_data_directory_removed` PASS；`test_legacy_reference_data_modules_not_importable` ×5 PASS（seahorse.reference_data / .protocol_param_data / .protocol_view_defs / .sample_data / .gbt_30966_fields）；`test_whale_metadata_repository_does_not_import_seahorse_reference_data` PASS；`test_protocol_param_data_available_via_whale_template` PASS；`test_protocol_view_defs_available_via_whale_views` PASS；`test_gbt_30966_fields_available_via_whale_template` PASS；`test_reference_data_replaced_by_whale_template_top_level` PASS；304 项套件全 PASS | 旧 public import `seahorse.reference_data` 已破坏，这是用户预期（无兼容尾巴）；`whale.shared.persistence.template` 内部 4 处旧 wrapper import 在 Round 7C 已改为自持；`sample_data` 在 v4.2 子步已迁回 whale.shared.persistence.template.sample_data 单一真实源 | 持续维护 whale.shared.persistence.template 单一真实数据归属 | 2026-06-30 |
| SH-R7B-008 | Seahorse_REQ Round 7B 硬清理 | import boundary 门禁强化：删除 `LEGACY_WRAPPER_ROOTS`，新增 `LEGACY_TOP_PACKAGES` ×7 + `LEGACY_SCAN_ROOTS` ×3，提供 ×7 `test_legacy_top_directories_removed`、×7 `test_legacy_top_packages_not_importable`、×3 `test_no_legacy_seahorse_imports_in_repo` AST 扫描 | AR | 高 | tests/unit/architecture | P2 | 已完成 | `tests/unit/architecture/test_seahorse_import_boundary.py` 中 `LEGACY_WRAPPER_ROOTS` 已删除，`LEGACY_TOP_PACKAGES` 含 7 个旧顶层包，`LEGACY_SCAN_ROOTS` 含 `src/seahorse/` + `tests/unit/seahorse/` + `tests/unit/architecture/` | import boundary 28 / 28 PASS；304 项单测套件 304 / 304 PASS in 130.13s | 扫描范围仅覆盖 Round 7B 授权区，未触及 `src/whale/shared/persistence/template/*` 与 `tests/unit/starfish/*`（下一轮扩展扫描范围后再次验证） | 下一轮：扩展 `LEGACY_SCAN_ROOTS` 覆盖 `src/whale/` 与 `tests/unit/starfish/`，全面收口 | 2026-06-30 |
| SH-R7B-009 | Seahorse_REQ Round 7B 硬清理 | `test_compat_wrappers.py` 重写：从旧 compat wrapper 单测改为硬清理验证（×7 目录删除 + ×7 包不可 import + ×24 单文件不可 import + seahorse 包根目录不含旧路径 + domain/use_cases __doc__ 不再含旧路径说明 + 真实参考数据归属 Whale template） | TEST | 高 | tests/unit/seahorse | P2 | 已完成 | `tests/unit/seahorse/test_compat_wrappers.py` 全部测试已改为硬约束断言，不再依赖 compat wrapper | 304 项套件全 PASS；新测试覆盖 `LEGACY_TOP_PACKAGES` ×7 + `LEGACY_TOP_DIRS` ×7 + `LEGACY_LEAF_MODULES` ×24 + 5 个 docstring / 目录扫描断言 | `test_compat_wrappers.py` 不再是 compat wrapper 测试，而是清理后状态固化测试 | 持续维护；任何旧顶层包复活将立即被硬断言捕获 | 2026-06-30 |
| SH-R7B-010 | Seahorse_REQ Round 7B 硬清理 | `test_reference_data_imports.py` 重写：从旧新路径 import 测试改为 reference_data 硬清理验证（顶层目录删除 + 5 个模块不可 import + 协议参数/视图/GBT 字段真实数据归属 Whale shared persistence + whale_metadata_repository 不再 import seahorse.reference_data） | TEST | 高 | tests/unit/seahorse | P2 | 已完成 | `tests/unit/seahorse/test_reference_data_imports.py` 全部测试已改为硬约束断言 | 304 项套件全 PASS；新测试覆盖 reference_data 顶层目录 + 5 个模块 + 3 个真实数据归属 + whale_metadata_repository AST | 范围外 `whale.shared.persistence.template` 内部 4 处旧 wrapper import 仍 broken（下一轮） | 下一轮：迁移 whale template 旧 wrapper，扩展扫描范围 | 2026-06-30 |
| SH-R7B-011 | Seahorse_REQ Round 7B 硬清理 | CLI 5 个子命令 --help 全部正常；ScenarioBundle checksum、ServerConfig payload_hash、Starfish handoff schema 不变 | CONTRACT | 高 | src/seahorse | P1 | 已完成 | `python -m seahorse generate/validate/plan/runtime-smoke --help` 全部正常；`seahorse.domain.bundle_checksum` / `seahorse.domain.plan` 字段不变；`seahorse.adapters.gateways.server_plan_handoff_gateway` schema 不变 | 304 项套件全 PASS；test-validator 验证 CLI 5 / 5 正常 | 无 | 持续维护 | 2026-06-30 |
| SH-R7B-012 | Seahorse_REQ Round 7B 硬清理 | 用户预期确认：旧 public import 已破坏是用户明确要求；任何 wrapper、DeprecationWarning、legacy 命名都是禁止的 | POLICY | 高 | 全组件 | P1+P2 | 已确认 | 用户 prompt 明确"不要管兼容问题，不要留历史尾巴"；本轮物理删除全部旧顶层目录与 35 个旧文件，未新增 compat wrapper / DeprecationWarning / legacy 命名 | 304 项套件全 PASS；import boundary 28 / 28 PASS；`test_compat_wrappers.py` 中无 `DeprecationWarning` 触发；`test_seahorse_domain_init_does_not_advertise_legacy_models` PASS | 范围外 `whale/shared/persistence/template/*` 内部 4 处旧 import 仍残存（不属于本轮授权） | 下一轮：whale template 旧 wrapper import 同样按"无兼容尾巴"硬清理 | 2026-06-30 |
| SH-R7C-001 | Seahorse_REQ Round 7B 后续（Round 7C） | `src/whale/shared/persistence/template/__init__.py` 删除 `from seahorse.reference_data import (...)` wrapper 与 `DeprecationWarning`，改为自持真实数据 re-export，导出 13 个真实数据符号（ALL_LOGICAL_NODES / LogicalNodeDef / LogicalNodeField / build_field_dict / total_field_count / ENDPOINT_PARAM_DEFS / SIGNAL_PARAM_DEFS / ParamDef / get_endpoint_params / get_signal_params / SCADA_PROTOCOL_VIEW_DEFINITIONS / SCADA_PROTOCOL_VIEW_SQL / ViewDefinition）；v4.2 子步扩展为 17 个 re-export（新增 5 个 A 类符号：PROTOCOL_SAMPLE_SPECS / ProtocolSampleSpec / clear_database_data / generate_all_sample_data / reset_sample_data） | CLEANUP | 高 | src/whale/shared/persistence/template | P2 | 已完成 | `git status` 修改 `src/whale/shared/persistence/template/__init__.py`；docstring 明确"本包不再 re-export `seahorse.reference_data`，也未保留任何兼容 wrapper 或 `DeprecationWarning`"；`python -c "import whale.shared.persistence.template as m; print(len(m.ALL_LOGICAL_NODES), len(m.SCADA_PROTOCOL_VIEW_DEFINITIONS))"` 输出 `19 11`；v4.2 子步新增 5 个 sample_data 入口符号 | `compileall src/whale/shared/persistence/template` 退出码 0；`test_whale_template_does_not_import_seahorse_reference_data` PASS；import boundary 28 / 28 PASS；starfish loader + CLI 57 / 57 PASS；v4.2 子步后 `test_seahorse_import_boundary` 46 / 46 PASS / `test_scada_sample_data_protocol_coverage` 3 / 3 PASS | 旧 public import `seahorse.reference_data` 已破坏（自 Round 7B 起），这是用户预期（无兼容尾巴）；`whale.template.sample_data` 真实数据归属在 v4.2 子步已闭合 | 持续维护自持真实数据 | 2026-06-30 |
| SH-R7C-002 | Seahorse_REQ Round 7B 后续（Round 7C） | `src/whale/shared/persistence/template/protocol_view_defs.py` 改为从 `whale.shared.persistence.views.scada_protocol_views` 转发 `ViewDefinition` / `SCADA_PROTOCOL_VIEW_DEFINITIONS` / `SCADA_PROTOCOL_VIEW_SQL`，不再 import `seahorse.reference_data.protocol_view_defs` | CLEANUP | 高 | src/whale/shared/persistence/template | P2 | 已完成 | `git status` 修改 `src/whale/shared/persistence/template/protocol_view_defs.py`；docstring 明确"本模块从 `whale.shared.persistence.views` 转发 SCADA 协议视图定义，也不再保留对 `seahorse.reference_data` 的兼容 wrapper"；`SCADA_PROTOCOL_VIEW_DEFINITIONS` 长度 = 11 | `compileall` 退出码 0；`test_whale_template_does_not_import_seahorse_reference_data` PASS | 旧 public import `seahorse.reference_data.protocol_view_defs` 已破坏，这是用户预期 | 持续维护 `whale.shared.persistence.views.scada_protocol_views` 单一真实源 | 2026-06-30 |
| SH-R7C-003 | Seahorse_REQ Round 7B 后续（Round 7C） | `src/whale/shared/persistence/template/protocol_param_data.py` 自持 `ParamDef` dataclass + `ENDPOINT_PARAM_DEFS` / `SIGNAL_PARAM_DEFS` 协议参数矩阵，覆盖 BECKHOFF_ADS / HTTP_REST / IEC101 / IEC104 / IEC61850 / MODBUS / MQTT / OPC_UA 8 种协议 × 2 类参数；暴露 `get_endpoint_params` / `get_signal_params` 查询接口 | CLEANUP | 高 | src/whale/shared/persistence/template | P2 | 已完成 | `git status` 修改 `src/whale/shared/persistence/template/protocol_param_data.py`；`ENDPOINT_PARAM_DEFS` 与 `SIGNAL_PARAM_DEFS` 各 8 个协议 key；`ParamDef` 含 name / default / description / kind / value_type 字段；docstring 明确"ParamDef 协议矩阵是真实数据归属" | `compileall` 退出码 0；`test_whale_template_does_not_import_seahorse_reference_data` PASS | 旧 public import `seahorse.reference_data.protocol_param_data` 已破坏，这是用户预期 | 持续维护 8 协议参数矩阵 | 2026-06-30 |
| SH-R7C-004 | Seahorse_REQ Round 7B 后续（Round 7C） | `src/whale/shared/persistence/template/gbt_30966_fields.py` 自持 `LogicalNodeDef` / `LogicalNodeField` dataclass + `ALL_LOGICAL_NODES = 19` 节点 + `build_field_dict` / `total_field_count` 工具；不再 import `seahorse.reference_data.gbt_30966_fields` | CLEANUP | 高 | src/whale/shared/persistence/template | P2 | 已完成 | `git status` 修改 `src/whale/shared/persistence/template/gbt_30966_fields.py`；`ALL_LOGICAL_NODES` 长度 = 19（首 3 节点：WPPD / WTUR / WROT）；`LogicalNodeDef` 含 name / ln_class / cdc / description / fields；docstring 明确"ALL_LOGICAL_NODES = 19 节点是真实数据归属" | `compileall` 退出码 0；`test_whale_template_does_not_import_seahorse_reference_data` PASS | 旧 public import `seahorse.reference_data.gbt_30966_fields` 已破坏，这是用户预期 | 持续维护 19 节点 GBT 30966.2-2022 字段定义 | 2026-06-30 |
| SH-R7C-005 | Seahorse_REQ Round 7B 后续（Round 7C） | `tests/unit/starfish/test_server_plan_loader.py` 6 处 `seahorse.*` 旧 import 全部迁移：`seahorse.models.scenario` → `seahorse.domain.scenario`、`seahorse.orchestration.scenario_generator` → `seahorse.application.use_cases.scenario_generator`、`seahorse.exporters.server_plan_exporter` → `seahorse.adapters.gateways.server_plan_handoff_gateway` | CLEANUP | 高 | tests/unit/starfish | P2 | 已完成 | `git status` 修改 `tests/unit/starfish/test_server_plan_loader.py`；diff 显示 6 处 import 路径替换 | `pytest tests/unit/starfish/test_server_plan_loader.py -q` 30 / 30 PASS；import boundary 28 / 28 PASS；starfish loader+CLI 57 / 57 PASS | 旧 public import `seahorse.models` / `seahorse.orchestration` / `seahorse.exporters` 在 starfish 测试中已彻底迁移，无 compat wrapper | 持续维护 starfish 测试使用新路径 import | 2026-06-30 |
| SH-R7C-006 | Seahorse_REQ Round 7B 后续（Round 7C） | `tests/unit/starfish/test_starfish_cli.py` 4 处 `seahorse.*` 旧 import 全部迁移：`seahorse.exporters.server_plan_exporter` → `seahorse.adapters.gateways.server_plan_handoff_gateway`、`seahorse.models.scenario` → `seahorse.domain.scenario`、`seahorse.orchestration.scenario_generator` → `seahorse.application.use_cases.scenario_generator` | CLEANUP | 高 | tests/unit/starfish | P2 | 已完成 | `git status` 修改 `tests/unit/starfish/test_starfish_cli.py`；diff 显示 4 处 import 路径替换 | `pytest tests/unit/starfish/test_starfish_cli.py -q` 27 / 27 PASS；import boundary 28 / 28 PASS；starfish loader+CLI 57 / 57 PASS | 旧 public import `seahorse.exporters` / `seahorse.models` / `seahorse.orchestration` 在 starfish CLI 测试中已彻底迁移，无 compat wrapper | 持续维护 starfish CLI 测试使用新路径 import | 2026-06-30 |
| SH-R7C-007 | Seahorse_REQ Round 7B 后续（Round 7C） | `tests/TESTING.md` 删除 `python -m seahorse.reference_data` 旧提示语——该入口自 Round 7B 起已物理删除，不再作为测试引导 | CLEANUP | 中 | tests | P2 | 已完成 | `git status` 修改 `tests/TESTING.md`（单行 -1）；`grep -n "python -m seahorse.reference_data" tests/TESTING.md` 输出 NO_HIT | `tests/TESTING.md` 字面搜索 0 命中；与 `seahorse_round7c_repo_import_closure.md` 一致 | 范围外 `src/whale/ingest/framework/persistence/init_db.py` 旧 wrapper import 已在本轮修复（属于其他路径，与本条并列） | 持续维护 TESTING.md 引导语 | 2026-06-30 |
| SH-R7C-008 | Seahorse_REQ Round 7B 后续（Round 7C） | `test_seahorse_import_boundary.py` 的 `LEGACY_SCAN_ROOTS` 由 3 个根（`src/seahorse/` + `tests/unit/seahorse/` + `tests/unit/architecture/`）扩展到 2 个根（`SRC_ROOT` + `TESTS_ROOT`，覆盖整个 `src/` + `tests/`），并新增 `test_whale_template_does_not_import_seahorse_reference_data` 反向断言——AST 扫描 `src/whale/shared/persistence/template/*.py`，确保无 `seahorse.reference_data` import | AR | 高 | tests/unit/architecture | P2 | 已完成 | `git status` 修改 `tests/unit/architecture/test_seahorse_import_boundary.py`；`LEGACY_SCAN_ROOTS = (SRC_ROOT, TESTS_ROOT)`；新增 `test_whale_template_does_not_import_seahorse_reference_data` 函数 | import boundary 28 / 28 PASS；AST 扫描 `src/` + `tests/` 全树 OFFENDER COUNT = 0 / 0；新增反向断言 PASS | 旧 public import 在仓库全树 AST 中已不存在任何引用，这是用户预期 | 持续维护 LEGACY_SCAN_ROOTS 覆盖完整 src/ + tests/ | 2026-06-30 |
| SH-R7C-009 | Seahorse_REQ Round 7B 后续（Round 7C） | CLI 5 个子命令 --help 全部正常；ScenarioBundle checksum、ServerConfig payload_hash、Starfish handoff schema 不变（Round 7B 契约在 Round 7C 仓库收口后仍保留） | CONTRACT | 高 | src/seahorse | P1 | 已完成 | `python -m seahorse {generate,validate,plan,runtime-smoke} --help` 全部输出合法 help；`seahorse.domain.bundle_checksum` / `seahorse.domain.plan` 字段不变；`seahorse.adapters.gateways.server_plan_handoff_gateway` schema 不变 | 公开 CLI 子命令 --help 5 / 5 PASS；starfish loader+CLI 57 / 57 PASS；tests/unit/seahorse + tests/unit/architecture 315 / 315 PASS | 无 | 持续维护 CLI 与契约 | 2026-06-30 |
| SH-R7C-010 | Seahorse_REQ Round 7B 后续（Round 7C） | 用户预期确认：旧 public import 已彻底破坏，无 compat wrapper / shim / DeprecationWarning / legacy；范围外遗留与既有失败不属于本轮收口对象 | POLICY | 高 | 全组件 | P1+P2 | 已确认 | 用户 prompt 明确"不要管兼容问题，不要留历史尾巴"；Round 7C 进一步在仓库全树（`src/` + `tests/`）确认 OFFENDER COUNT = 0；whale.template 4 个模块改为自持真实数据；starfish 测试 10 处旧 import 全部迁移；TESTING.md 旧提示已清理；本轮未引入任何 compat wrapper / shim / DeprecationWarning / legacy 命名；v4.2 子步已将 sample_data 真实数据迁回 whale.shared.persistence.template.sample_data（与本条并列的后续 handoff 闭合项） | import boundary 28 / 28 PASS；starfish loader+CLI 57 / 57 PASS；CLI 5 / 5 PASS；tests/unit/seahorse + tests/unit/architecture 315 / 315 PASS；v4.2 子步后 `test_scada_sample_data_protocol_coverage` 3 / 3 PASS / `test_seahorse_import_boundary` 46 / 46 PASS | 范围外遗留：①`test_scada_sample_data_protocol_coverage.py` 已闭合（v4.2 子步）；②`tests/unit/starfish/test_runtime_api.py::test_manager_path_input_delegates_runtime_build_to_composition_root` pre-existing 失败（与 broken import 无关）；③27 environment-pending skips（缺 native 动态库 libiec61850 / libopen62541 / liblib60870，非本轮目标） | 后续 handoff：test_runtime_api 单独排查；native 动态库环境补齐 | 2026-06-30 |
| SH-R8-001 | docs/clean_architecture.md v4.1 §5.2 / §5.9 | 删除 `src/seahorse/adapters/controllers/` 子包（`__init__.py` + `cli_controller.py`）——v4.1 蓝图明确 `adapters/` 不再默认承载 CLI Controller，CLI 收敛到 `__main__.py` + `api/<package>_cli.py` | CLEANUP | 高 | src/seahorse | P2 | 已完成 | `git status` 2 项删除（`src/seahorse/adapters/controllers/__init__.py` + `cli_controller.py`）；`ls src/seahorse/adapters/controllers` 不存在；`find src/seahorse/adapters -maxdepth 1 -type d` 仅返回 `__pycache__` + `drivers` + `gateways` + `presenters` + `serializers`；新 `api/seahorse_cli.py` 承载全部 4 子命令 | `test_seahorse_controllers_directory_removed` PASS；`test_seahorse_adapters_has_no_controllers_subdir` PASS；import boundary 37 / 37 PASS；CLI 4 子命令端到端 PASS | 旧 public import `seahorse.adapters.controllers` 已破坏（v4.1 蓝图要求），无 compat wrapper / shim / DeprecationWarning | 持续维护新 CLI helper 路径 | 2026-07-01 |
| SH-R8-002 | docs/clean_architecture.md v4.1 §4.4 规则 6 | 删除 `src/seahorse/adapters/drivers/curve_generation.py` / `random_generation.py` / `replay_generation.py` 共 3 个生成策略 shim——真实策略实现在 `seahorse.application.use_cases`，v4.1 明确 `adapters/drivers/` 不放真实数据源 / 真实 replay / 真实文件读取 | CLEANUP | 高 | src/seahorse | P2 | 已完成 | `git status` 3 项删除；`ls src/seahorse/adapters/drivers/` 仅返回 `__init__.py` + `__pycache__` + `backend_ports.py` + `factory/`；`adapters/drivers/__init__.py` 移除 3 个 shim re-export，`__all__` 改为空；docstring 明确"v4.1 仅承载 backend 适配契约" | `test_seahorse_drivers_shim_generation_files_removed` ×3 参数化 PASS；import boundary 37 / 37 PASS | 旧 driver shim 公共 import 已破坏（v4.1 蓝图要求），无 compat wrapper | 持续维护 `seahorse.application.use_cases.{curve_generation, random_generation, replay_generation}` 新路径 | 2026-07-01 |
| SH-R8-003 | docs/clean_architecture.md v4.1 §5.2 / §5.3 / §6 落位表 | 新增 `src/seahorse/api/seahorse_cli.py` 薄 CLI helper——4 子命令 argparse（`generate-scenario` / `export-bundle` / `validate-bundle` / `export-server-config`），仅调用 `SeahorseFacade`；不 import application / adapters / infrastructure / starfish / whale.ingest | FR | 高 | src/seahorse/api | P1 | 已完成 | `git status` 新增 `src/seahorse/api/seahorse_cli.py`（470 行）；`api/seahorse_cli.py` import 集合 = `argparse` / `json` / `sys` / `datetime` / `pathlib` / `typing` 标准库 + `seahorse.api.seahorse_facade.SeahorseFacade` + `seahorse.domain.scenario.ScenarioConfig`（函数内延迟 import） | CLI 4 子命令端到端 PASS（`generate-scenario` exit 0、bundle JSON 已保存、JSONL 时序已保存、生成摘要与校验和输出；`export-bundle` exit 0、checksum 跨命令一致 90e7288dba896d7f...；`validate-bundle` exit 0、校验通过；`export-server-config` exit 0、ServerConfig handoff JSON 已保存、校验通过）；老 CLI 4 子命令（`generate` / `validate` / `plan` / `runtime-smoke`）argparse exit 2 拒绝 | 无 | 持续维护 4 子命令参数契约与退出码 | 2026-07-01 |
| SH-R8-004 | docs/clean_architecture.md v4.1 §2.4 / §5.2 / §8.1 | `src/seahorse/__main__.py` 改为薄入口——仅 `from seahorse.api.seahorse_cli import main` + `sys.exit(main())`；AST 零 `seahorse.application` / `seahorse.adapters` / `seahorse.infrastructure` import；不构造 backend / scheduler / repository / writer | AR | 高 | src/seahorse | P1+P2 | 已完成 | `git status` 修改 `src/seahorse/__main__.py`；AST imports = `__future__` + `sys` + `seahorse.api.seahorse_cli`（零 application/adapters/infrastructure import）；正文 22 行；docstring 明确"严格保持薄入口" | `test_seahorse_main_does_not_import_application_adapters_infrastructure` PASS；`test_seahorse_main_does_not_create_backend_or_runtime` PASS（10 个禁止构造符号全 0 命中）；CLI 4 子命令端到端 PASS；import boundary 37 / 37 PASS | 无 | 持续维护薄入口契约 | 2026-07-01 |
| SH-R8-005 | docs/clean_architecture.md v4.1 §5.3 | 扩展 `src/seahorse/api/seahorse_facade.SeahorseFacade` 稳定门面方法——新增 `save_timeseries` / `export_timeseries_jsonl` / `generate_minimal_server_config` / `validate_server_config` / `load_server_config_from_bundle_json` / `generator_metadata_stats` 等，供 CLI helper 委托 | FR | 高 | src/seahorse/api | P1 | 已完成 | `git status` 修改 `src/seahorse/api/seahorse_facade.py`（+311 行 / -若干行）；`SeahorseFacade` 新增 ≥6 个公开方法，全部有完整类型签名与 docstring；不直接 new infrastructure backend | 276 / 276 seahorse tests PASS（含 facade 全部新方法覆盖）；CLI 4 子命令端到端 PASS（依赖 facade 各方法） | 无 | 持续维护 facade 公共契约 | 2026-07-01 |
| SH-R8-006 | docs/clean_architecture.md v4.1 §11 边界检查 + §9 边界矩阵 | 新增 9 项 import boundary v4.1 守护：`test_seahorse_controllers_directory_removed` / `test_seahorse_adapters_has_no_controllers_subdir` / `test_seahorse_drivers_shim_generation_files_removed`（×3 参数化）/ `test_seahorse_main_does_not_import_application_adapters_infrastructure` / `test_seahorse_main_does_not_create_backend_or_runtime` / `test_application_domain_do_not_import_adapters_infrastructure_api` / `test_seahorse_root_does_not_import_starfish` | AR | 高 | tests/unit/architecture | P2 | 已完成 | `git status` 修改 `tests/unit/architecture/test_seahorse_import_boundary.py`（+184 行 / 9 项新守护）；`LEGACY_SCAN_ROOTS` 仍为 `SRC_ROOT + TESTS_ROOT`（覆盖整个 `src/` + `tests/`） | import boundary **37 / 37 PASS**（28 既有 + 9 v4.1 新增）；`tests/unit/seahorse` + `tests/unit/architecture` 合计 **313 / 313 PASS** | 无 | 持续维护 v4.1 守护 | 2026-07-01 |
| SH-R8-007 | docs/clean_architecture.md v4.1 全文 | v4.1 与蓝图不一致项 5 类全部闭合：(1) adapters/controllers 删除 / (2) 3 driver shim 删除 / (3) `__main__` 薄入口 / (4) `api/<package>_cli.py` 白名单 / (5) 老 CLI 收敛；本轮无 Architecture Exception 需要登记 | POLICY | 高 | 全组件 | P1+P2 | 已确认 | v4.1 蓝图 §5.2 / §5.3 / §5.9 全部落地；本轮无 compat wrapper / shim / DeprecationWarning / legacy 命名 | import boundary 37 / 37 PASS；CLI 4 子命令端到端 PASS；老 CLI 4 子命令 argparse exit 2 拒绝；tests/unit/seahorse + tests/unit/architecture 313 / 313 PASS | 范围外遗留：①`test_manager_path_input_delegates_runtime_build_to_composition_root` pre-existing；②`test_scada_sample_data_protocol_coverage.py` sample_data 已删；③27 environment-pending skips 缺 native 动态库 | 后续 handoff：test_runtime_api 单独排查；sample_data 是否重建或下线；native 动态库环境补齐 | 2026-07-01 |
| SH-R8-008 | docs/clean_architecture.md v4.1 §5.2 | 老 CLI 子命令（`generate` / `validate` / `plan` / `runtime-smoke`）按 v4.1 蓝图要求被 argparse 拒绝（exit 2）；新 4 子命令（`generate-scenario` / `export-bundle` / `validate-bundle` / `export-server-config`）端到端通过 + bundle checksum 跨命令一致 | CONTRACT | 高 | src/seahorse/api | P1 | 已完成 | `python -m seahorse generate --help` / `validate --help` / `plan --help` / `runtime-smoke --help` 全部 argparse `unrecognized arguments` exit 2；`python -m seahorse generate-scenario --scenario-id v41-smoke --seed 42 --asset-count 1` 端到端 exit 0 + bundle checksum `90e7288dba896d7f...`；`export-bundle` 重新输出同一 checksum；`validate-bundle` 校验通过；`export-server-config` ServerConfig handoff JSON 已保存 + 校验通过 | 公开 CLI 4 / 4 PASS；老 CLI 4 / 4 拒绝；bundle checksum 跨命令一致 | 无 | 持续维护 CLI 参数契约与外部脚本迁移 | 2026-07-01 |
| SH-R8-009 | docs/clean_architecture.md v4.2 §5.2 / §5.3 | 删除 `src/seahorse/api/seahorse_cli.py` —— v4.2 蓝图明确 `api/` 下不再放 `<package>_cli.py`，CLI 入口完全收敛到 `__main__.py` | CLEANUP | 高 | src/seahorse/api | P1+P2 | 已完成 | `git status` `D src/seahorse/api/seahorse_cli.py`；`ls src/seahorse/api/` 仅 `__init__.py` + `seahorse_facade.py`；v4.1 新增的白名单 CLI helper 文件已物理删除 | 7 项 v4.2 import boundary 守护（api 下无 `*_cli.py` / `cli.py` / `controllers.py` ×3）PASS；CLI 4 子命令端到端 PASS；import boundary **44+ / 44+ PASS** | 无 compat wrapper / shim / DeprecationWarning | 持续维护 `api/` 只保留 facade | 2026-07-01 |
| SH-R8-010 | docs/clean_architecture.md v4.2 §2.4 / §5.2 / §8.1 | `src/seahorse/__main__.py` 改为 Typer CLI 薄入口（替代 v4.1 argparse）：仅 import 标准库 / `typer` / `seahorse.api.seahorse_facade.SeahorseFacade`；AST 零 `seahorse.application` / `seahorse.adapters` / `seahorse.infrastructure` / `seahorse.domain` import；不构造 `ScenarioConfig` / backend / scheduler / repository / writer / ORM session；保留 `main(argv) -> int` 签名 | AR | 高 | src/seahorse | P1+P2 | 已完成 | `git status` `M src/seahorse/__main__.py`；AST imports = `__future__` + `json` + `sys` + `datetime` + `pathlib` + `typing` + `typer` + `seahorse.api.seahorse_facade`（零 application/adapters/infrastructure/domain import）；4 `@app.command(...)` 装饰器（`generate-scenario` / `export-bundle` / `validate-bundle` / `export-server-config`）；`typer.Typer` 入口，`standalone_mode=False` 调用 Typer 以返回 int | 7 项 v4.2 import boundary 守护 PASS；`tests/unit/seahorse/test_main_typer_cli.py` 25+ 项 CLI 行为 PASS；CLI 4 子命令端到端 PASS；import boundary **44+ / 44+ PASS** | handoff 文本偏差：code-implementer handoff 示例命令中 `export-server-config` 未声明 `--start-time`，属 handoff 文本偏差而非代码缺陷 | 持续维护 Typer 薄入口契约 | 2026-07-01 |
| SH-R8-011 | docs/clean_architecture.md v4.2 §5.3 | 扩展 `src/seahorse/api/seahorse_facade.SeahorseFacade` 新增 2 个 CLI 专用 primitives wrapper：`generate_bundle_from_cli_params` / `generate_minimal_server_config_from_cli_params`；内部统一构造 `ScenarioConfig`，CLI 自身不构造 domain model | FR | 高 | src/seahorse/api | P1 | 已完成 | `git status` `M src/seahorse/api/seahorse_facade.py`；`generate_bundle_from_cli_params`（scenario_id / name / deterministic_seed / start_time / duration_seconds / sample_interval_ms / asset_count / protocol_targets primitives → `ScenarioBundle`）；`generate_minimal_server_config_from_cli_params`（scenario_id / deterministic_seed / asset_count / protocol_targets primitives → `ServerConfig`）；完整 docstring；内部通过 `_build_cli_scenario_config` 统一构造 domain model | `tests/unit/seahorse` + `tests/unit/architecture` 合计 **348 / 348 PASS**（含 facade 全部新方法 + CLI 4 子命令端到端覆盖） | 无 | 持续维护 facade 公共契约 | 2026-07-01 |
| SH-R8-012 | docs/clean_architecture.md v4.2 §11 边界检查 | `pyproject.toml` 核心 `dependencies` 段第 23 行新增 `typer>=0.20,<1.0` 依赖 | DEPS | 高 | pyproject.toml | P2 | 已完成 | `grep -nE "typer" pyproject.toml` 输出第 23 行 `"typer>=0.20,<1.0"`，位于 `[project] dependencies` 段（核心依赖，非可选） | `pip install -e .` typer 解析 OK；CLI 4 子命令端到端 PASS | 无 | 持续维护 Typer 版本约束与兼容性 | 2026-07-01 |
| SH-R8-013 | docs/clean_architecture.md v4.2 §11 边界检查 + §9 边界矩阵 | 新增 7 项 import boundary v4.2 守护（`tests/unit/architecture/test_seahorse_import_boundary.py`）：`test_seahorse_api_has_no_cli_file`（`api` 下无 `*_cli.py` ×1）/ `test_seahorse_api_has_no_cli_module`（`api` 下无 `cli.py` ×1）/ `test_seahorse_api_has_no_controllers_module`（`api` 下无 `controllers.py` ×1）/ `test_seahorse_main_uses_typer_not_argparse`（`__main__.py` 使用 Typer 禁 argparse ×1）/ `test_seahorse_main_only_imports_stdlib_typer_seahorse`（只依赖标准库 / typer / seahorse ×1）/ `test_seahorse_main_no_inner_layer_imports`（AST 零内层 import ×1）/ `test_seahorse_main_no_scenario_config_or_backend_creation`（AST 零 `ScenarioConfig` + 不构造 backend / scheduler / repository / writer ×1）| AR | 高 | tests/unit/architecture | P2 | 已完成 | `git status` `M tests/unit/architecture/test_seahorse_import_boundary.py`（+~150 行 / 7 项新守护）；`LEGACY_SCAN_ROOTS` 仍为 `SRC_ROOT + TESTS_ROOT`（覆盖整个 `src/` + `tests/`） | import boundary **44+ / 44+ PASS**（v4.1 既有 37 项 + v4.2 新增 7 项）；`tests/unit/seahorse` + `tests/unit/architecture` 合计 **348 / 348 PASS** | 无 | 持续维护 v4.2 守护 | 2026-07-01 |
| SH-R8-014 | docs/clean_architecture.md v4.2 §5.2 | `tests/unit/seahorse/test_main_typer_cli.py` 新增 25+ 项 CLI 行为测试：Typer app 4 子命令注册、`main()` 返回 int、`--no-jsonl` 关闭 JSONL 时序生成、多种 error path（缺参数 / 不存在输入文件 / ScenarioConfig 校验失败 / export-server-config 校验失败）、`--protocol-targets` 逗号分隔解析、`generate-scenario` / `export-bundle` / `validate-bundle` / `export-server-config` 端到端流程 | TEST | 高 | tests/unit/seahorse | P1 | 已完成 | `git status` `?? tests/unit/seahorse/test_main_typer_cli.py`（新增 21325 字节）；覆盖 Typer app 4 子命令注册、`main(argv) -> int` 返回 int、`--no-jsonl` flag、error path ×N、`--protocol-targets` 逗号分隔、4 子命令端到端 | `pytest tests/unit/seahorse/test_main_typer_cli.py -q` 全 PASS；`tests/unit/seahorse` + `tests/unit/architecture` 合计 **348 / 348 PASS** | 无 | 持续维护 CLI 行为测试覆盖 | 2026-07-01 |
| SH-R8-015 | docs/clean_architecture.md v4.2 §5.2 | `tests/unit/seahorse/test_bundle.py` + `tests/unit/seahorse/test_server_plan.py` 旧 argparse CLI 测试已迁移到 Typer CLI 测试形态（`__main__.py` 入口从 argparse 切到 Typer 后，CLI 测试必须按 Typer `CliRunner.invoke()` / `main(argv)` 重写） | TEST | 高 | tests/unit/seahorse | P1 | 已完成 | `git status` `M tests/unit/seahorse/test_bundle.py` + `M tests/unit/seahorse/test_server_plan.py`；CLI 测试已切到 Typer `CliRunner.invoke()` 模式 | `pytest tests/unit/seahorse/test_bundle.py -q` PASS；`pytest tests/unit/seahorse/test_server_plan.py -q` PASS；`tests/unit/seahorse` + `tests/unit/architecture` 合计 **348 / 348 PASS** | 无 | 持续维护 CLI 测试与 Typer 入口对齐 | 2026-07-01 |
| SH-R8-016 | docs/clean_architecture.md v4.2 全文 | v4.2 与蓝图不一致项 0 类例外：本轮 `api/seahorse_cli.py` 物理删除、`__main__.py` 改写 Typer、facade 新增 2 个 CLI wrapper、`pyproject.toml` 新增 `typer` 依赖、4 子命令端到端 + import boundary 守护全 PASS；本轮无 compat wrapper / shim / DeprecationWarning / legacy 命名，无 Architecture Exception 需要登记 | POLICY | 高 | 全组件 | P1+P2 | 已确认 | v4.2 蓝图 §5.2 / §5.3 / §11 全部落地；本轮无 compat wrapper / shim / DeprecationWarning / legacy 命名；CLI 4 子命令端到端 PASS；bundle checksum 跨命令一致；handoff 文本偏差 `--start-time` 在 `export-server-config` 未声明是 handoff 文本偏差而非代码缺陷 | import boundary **44+ / 44+ PASS**；CLI 4 子命令端到端 PASS；`tests/unit/seahorse` + `tests/unit/architecture` 合计 **348 / 348 PASS** | 范围外遗留：①`test_manager_path_input_delegates_runtime_build_to_composition_root` pre-existing；②`test_scada_sample_data_protocol_coverage.py` sample_data 已删（v4.2 子步已闭合，sample_data 迁回 whale.shared.persistence.template.sample_data，3 项 passing）；③27 environment-pending skips 缺 native 动态库 | 后续 handoff：test_runtime_api 单独排查；native 动态库环境补齐 | 2026-07-01 |
| SH-R8-017 | docs/clean_architecture.md v4.2 子步 — sample_data 真实数据迁回 | `src/whale/shared/persistence/template/sample_data.py`（1167 行）从 `src/seahorse/infrastructure/repositories/whale_metadata_repository.py`（1427 → 293 行）拆分迁回：仅承载 16 组 `PROTOCOL_SAMPLE_SPECS` + `ProtocolSampleSpec` + `generate_all_sample_data` / `clear_database_data` / `reset_sample_data` 入口 + 全部 `_create_*` / `_seed_*` / `_resolve_*` / `_build_*` helpers + `if __name__ == "__main__": reset_sample_data()`；不依赖任何 `seahorse.*` 模块；`whale.shared.persistence.template.__init__` 扩展为 17 个 re-export（新增 5 个 A 类符号）；`seahorse.infrastructure.repositories.__init__` 不再 export A 类 5 符号；`whale_metadata_repository` 职责收缩为 Seahorse WritePlan 只读映射 + 入口薄包装委托；`src/whale/ingest/framework/persistence/init_db.py:52` 悬挂 import 自然恢复 | REFACTOR | 高 | src/whale/shared/persistence/template + src/seahorse/infrastructure/repositories | P2 | 已完成 | `git status` 新增 `src/whale/shared/persistence/template/sample_data.py`（1167 行）；`src/seahorse/infrastructure/repositories/whale_metadata_repository.py` 缩至 293 行；docstring / AST 已确认职责边界 | `tests/unit/architecture/test_seahorse_import_boundary.py` 46 passed（含 `whale_template_does_not_import_seahorse_reference_data` / `test_legacy_top_packages_not_importable[seahorse.reference_data]` / `test_no_legacy_seahorse_imports_in_repo`）；`tests/unit/seahorse/test_reference_data_imports.py` 10 passed；`tests/unit/shared/persistence/test_scada_sample_data_protocol_coverage.py` 3 passed（从 broken 自然变 passing）；`tests/unit/shared/persistence/` 31 passed；`tests/unit/seahorse/` 302 passed | 旧 public import `seahorse.reference_data.sample_data` 自 Round 7B 起已破坏（用户预期无兼容尾巴），本轮通过迁回恢复 whale 元数据种子入口；`seahorse.infrastructure.repositories` 公共契约不变 | 持续维护 whale.shared.persistence.template.sample_data 单一真实源 | 2026-07-01 |
| SH-R8-018 | docs/clean_architecture.md v4.2 子步 — sample_data 真实数据迁回 | 本轮无 compat wrapper / shim / DeprecationWarning / legacy 命名——`whale_metadata_repository` 仅以函数内延迟 import 形式引用 `sample_data` 入口符号（`from whale.shared.persistence.template.sample_data import ...`），不持有生成实现；无 Architecture Exception 需要登记 | POLICY | 高 | 全组件 | P2 | 已确认 | 用户 prompt 明确"不要管兼容问题，不要留历史尾巴"；本轮通过真实数据迁回恢复 whale 元数据种子入口，无 compat wrapper / shim / DeprecationWarning / legacy 命名；`whale_metadata_repository` AST 扫描无 `seahorse.*` 生成实现 | `test_seahorse_import_boundary` 46 / 46 PASS；`test_reference_data_imports` 10 / 10 PASS；`test_scada_sample_data_protocol_coverage` 3 / 3 PASS（从 broken 自然变 passing） | 范围外遗留：①`test_manager_path_input_delegates_runtime_build_to_composition_root` pre-existing；②27 environment-pending skips 缺 native 动态库 | 后续 handoff：test_runtime_api 单独排查；native 动态库环境补齐 | 2026-07-01 |

## 6. 实现文件清单

```text
src/seahorse/
├── __init__.py                    — 包入口，安全边界声明
├── __main__.py                    — v4.2 Typer CLI 薄输入入口（仅 import 标准库 + typer + seahorse.api.seahorse_facade.SeahorseFacade；4 子命令：generate-scenario / export-bundle / validate-bundle / export-server-config；AST 零 application/adapters/infrastructure/domain import）
├── container.py                   — Seahorse facade/runtime/writer 装配（Round 7 新增 build_runtime_smoke_workflow）
├── adapters/                      — v4.1 输出适配层（不再含 controllers）
│   ├── __init__.py
│   ├── drivers/                   — v4.1 仅 backend 适配契约 + factory 占位
│   │   ├── __init__.py
│   │   ├── backend_ports.py
│   │   └── factory/__init__.py
│   ├── gateways/                  — handoff gateway（ServerConfig + ServerPlan handoff + validator + Starfish writer gateway）
│   │   ├── __init__.py
│   │   ├── server_config_handoff_gateway.py
│   │   ├── server_config_validator.py
│   │   ├── server_plan_handoff_gateway.py
│   │   ├── server_plan_validator.py
│   │   └── starfish_writer_gateway.py
│   ├── presenters/__init__.py
│   └── serializers/               — JSON / JSONL serializer
│       ├── __init__.py
│       ├── bundle_json_serializer.py
│       ├── bundle_serialization.py
│       └── timeseries_jsonl_serializer.py
├── api/
│   ├── __init__.py
│   └── seahorse_facade.py         — 离线生成与 handoff facade（v4.1 扩展 save_timeseries / export_timeseries_jsonl / generate_minimal_server_config / validate_server_config / load_server_config_from_bundle_json / generator_metadata_stats；v4.2 新增 2 个 CLI 专用 primitives wrapper：generate_bundle_from_cli_params / generate_minimal_server_config_from_cli_params）
│   注：v4.1 新增的 `seahorse_cli.py` 在 v4.2 已物理删除；v4.2 蓝图 §5.2 / §5.3 明确 api 下不再放 `<package>_cli.py`
├── application/                   — 用例编排 + 端口契约 + 运行时骨架
│   ├── __init__.py
│   ├── exceptions.py
│   ├── ports/                     — 应用层端口契约
│   │   ├── __init__.py
│   │   ├── clock_port.py
│   │   ├── data_source_port.py
│   │   ├── generation_strategy_port.py
│   │   ├── scheduler_port.py
│   │   ├── starfish_writer_port.py
│   │   ├── telemetry_port.py
│   │   └── whale_metadata_port.py
│   ├── runtime/                   — runtime skeleton（context / event_bus / executor / graph / snapshot / state）
│   │   ├── __init__.py
│   │   ├── context.py
│   │   ├── event_bus.py
│   │   ├── executor.py
│   │   ├── graph.py
│   │   ├── snapshot.py
│   │   └── state.py
│   └── use_cases/                 — 离线场景生成 + bundle 校验 + 生成策略 + atomic use case
│       ├── __init__.py
│       ├── alarm_generator.py
│       ├── bundle_validator.py
│       ├── control_result_generator.py
│       ├── curve_generation.py    — 真实策略实现（v4.1 删除 drivers/curve_generation.py shim）
│       ├── random_generation.py   — 真实策略实现（v4.1 删除 drivers/random_generation.py shim）
│       ├── replay_generation.py   — 真实策略实现（v4.1 删除 drivers/replay_generation.py shim）
│       ├── scenario_generator.py  — SeahorseGenerator 5 元组完整生成
│       ├── seed_whale_metadata.py
│       ├── strategy_registry.py
│       └── atomic/                — runtime atomic use case
│           ├── __init__.py
│           ├── build_write_batch.py
│           ├── build_write_plan.py
│           ├── dispatch_write_batch.py
│           ├── runtime_smoke_workflow.py  — Round 7 新增
│           ├── update_runtime_period.py
│           └── validate_write_plan.py
├── domain/                        — 纯内存领域模型（不访问文件、DB、CLI framework、Whale ORM、Starfish runtime）
│   ├── __init__.py
│   ├── bundle.py                  — ScenarioBundle 16 字段场景包
│   ├── bundle_checksum.py         — bundle checksum 纯算法
│   ├── generation.py              — GeneratedSignalValue/AlarmEvent/ControlResult
│   ├── plan.py                    — SeedPlan/ServerPlan 等规划型 dataclass
│   ├── runtime_contract.py        — runtime/data source/batch 契约
│   └── scenario.py                — ScenarioConfig/Metadata
└── infrastructure/                — 基础设施（data source / driver backend / repository / scheduler / telemetry）
    ├── __init__.py
    ├── data_sources/
    │   ├── __init__.py
    │   └── runtime.py             — 内存 DataSource runtime adapter
    ├── drivers/
    │   ├── __init__.py
    │   ├── backend_factory.py     — driver backend 工厂入口
    │   └── starfish_writer_backend.py  — 内存 Starfish writer backend
    ├── repositories/
    │   ├── __init__.py
    │   └── whale_metadata_repository.py  — Seahorse WritePlan 只读映射 + sample_data 薄包装委托（sample_data 真实数据已迁回 whale.shared.persistence.template.sample_data）
    ├── schedulers/
    │   ├── __init__.py
    │   └── clock.py               — ClockPort 实现与同步 step helper
    └── telemetry/__init__.py
```

```text
Round 7B 硬清理（无 compat wrapper，旧 public import 已不再支持，用户明确预期）：
物理删除 src/seahorse/{models,exporters,strategies,generators,orchestration,ports,reference_data}/ 共 7 个旧顶层目录 + 35 个旧文件。
旧路径消费者迁移：
  - seahorse.models.{scenario,plan,generation,bundle}              → seahorse.domain.*
  - seahorse.exporters.{bundle_exporter,bundle_validator,serialization,
                          server_config_exporter,server_config_validator,
                          server_plan_exporter,server_plan_validator,
                          timeseries_exporter}                     → seahorse.adapters.{gateways,serializers}.*
  - seahorse.strategies.{curve_generation,random_generation,replay_generation,registry}
                                                                     → seahorse.application.use_cases.{curve_generation,random_generation,replay_generation,strategy_registry}
  - seahorse.generators.{alarm_generator,control_result_generator}  → seahorse.application.use_cases.{alarm_generator,control_result_generator}
  - seahorse.orchestration.scenario_generator                       → seahorse.application.use_cases.scenario_generator
  - seahorse.ports.generation_strategy                              → seahorse.application.ports.generation_strategy_port
  - seahorse.reference_data.{protocol_param_data,protocol_view_defs,sample_data,gbt_30966_fields}
                                                                     → whale.shared.persistence.template.*

Round 8 v4.1 对齐（无 compat wrapper，按 docs/clean_architecture.md v4.1 蓝图硬约束）：
物理删除 src/seahorse/adapters/controllers/ 子包（__init__.py + cli_controller.py，共 2 个文件）。
物理删除 src/seahorse/adapters/drivers/{curve_generation.py, random_generation.py, replay_generation.py} 共 3 个生成策略 shim。
新增 src/seahorse/api/seahorse_cli.py（v4.1 §5.3 可选白名单 <package>_cli.py，470 行）。
修改 src/seahorse/__main__.py 为 v4.1 薄入口（仅 import api.seahorse_cli.main）。
扩展 src/seahorse/api/seahorse_facade.SeahorseFacade 6+ 个新门面方法。
新增 9 项 import boundary v4.1 守护：controllers 删除 ×2、driver shim 删除 ×3、__main__ 薄入口 ×2、domain/application 不 import 外层、seahorse 不 import starfish。
CLI 4 子命令端到端 PASS（generate-scenario / export-bundle / validate-bundle / export-server-config）。
老 CLI 4 子命令（generate / validate / plan / runtime-smoke）按 v4.1 蓝图要求 argparse exit 2 拒绝。
import boundary 37 / 37 PASS（28 既有 + 9 v4.1 新增）；tests/unit/seahorse + tests/unit/architecture 合计 313 / 313 PASS。
无 compat wrapper / shim / DeprecationWarning / legacy 命名——这是用户预期。

范围外残留（下一轮处理，本轮 handoff forbidden）：
src/whale/shared/persistence/template/
├── __init__.py                   — 仍 from seahorse.reference_data import ...（Round 7C 已改为自持真实数据）
├── protocol_param_data.py        — 仍 from seahorse.reference_data.protocol_param_data import ...（Round 7C 已改为自持）
├── protocol_view_defs.py         — 仍 from seahorse.reference_data.protocol_view_defs import ...（Round 7C 已改为转发）
├── gbt_30966_fields.py           — 仍 from seahorse.reference_data.gbt_30966_fields import ...（Round 7C 已改为自持）
└── sample_data.py                — 1167 行；16 组 PROTOCOL_SAMPLE_SPECS + ProtocolSampleSpec + generate_all_sample_data / clear_database_data / reset_sample_data + 全部 _create_* / _seed_* / _resolve_* / _build_* helpers；不依赖任何 seahorse.* 模块（v4.2 子步，从 seahorse.infrastructure.repositories 拆分迁回）

tests/unit/starfish/
├── test_server_plan_loader.py    — Round 7C 已迁移 6 处 import
└── test_starfish_cli.py          — Round 7C 已迁移 4 处 import

tests/unit/shared/persistence/test_scada_sample_data_protocol_coverage.py — 已通过（sample_data 已迁回 whale.shared.persistence.template.sample_data，3 项 passing）
tests/unit/starfish/test_runtime_api.py::test_manager_path_input_delegates_runtime_build_to_composition_root — pre-existing 失败（不属于本轮授权）
27 environment-pending skips — 缺 native 动态库（libiec61850 / libopen62541 / liblib60870，不属于本轮授权）

Round 8 v4.2 对齐（无 compat wrapper，按 docs/clean_architecture.md v4.2 蓝图硬约束）：
物理删除 src/seahorse/api/seahorse_cli.py（v4.1 新增的白名单 <package>_cli.py 在 v4.2 已彻底删除）。
重写 src/seahorse/__main__.py 为 Typer CLI 薄入口（替代 v4.1 argparse）：仅 import 标准库 + typer + seahorse.api.seahorse_facade；保留 4 子命令（generate-scenario / export-bundle / validate-bundle / export-server-config）；AST 零 application/adapters/infrastructure/domain import；不构造 ScenarioConfig/backend/scheduler/repository/writer/ORM session。
扩展 src/seahorse/api/seahorse_facade.SeahorseFacade 2 个 CLI 专用 primitives wrapper：generate_bundle_from_cli_params + generate_minimal_server_config_from_cli_params（内部统一构造 ScenarioConfig）。
pyproject.toml 核心 dependencies 段第 23 行新增 typer>=0.20,<1.0。
新增 7 项 import boundary v4.2 守护：api 下无 *cli.py / cli.py / controllers.py ×3 + __main__.py 使用 Typer 禁 argparse + __main__.py 只依赖标准库 / typer / seahorse + __main__.py AST 零内层 import + __main__.py AST 零 ScenarioConfig + __main__.py 不构造 backend/scheduler/repository/writer。
新增 tests/unit/seahorse/test_main_typer_cli.py 共 25+ 项 CLI 行为 / 错误路径 / 端到端测试。
修改 tests/unit/seahorse/test_bundle.py + tests/unit/seahorse/test_server_plan.py 旧 argparse CLI 测试已迁移到 Typer CLI 测试形态。
CLI 4 子命令端到端 PASS（generate-scenario / export-bundle / validate-bundle / export-server-config）。
老 CLI 4 子命令（generate / validate / plan / runtime-smoke）v4.2 由 Typer 完全替换，无 compat shim / DeprecationWarning / 兼容 wrapper。
import boundary 44+ / 44+ PASS（v4.1 既有 37 项 + v4.2 新增 7 项）；tests/unit/seahorse + tests/unit/architecture 合计 348 / 348 PASS。
handoff 文本偏差：code-implementer handoff 示例命令中的 --start-time 在 export-server-config 子命令未声明，属 handoff 文本偏差而非代码缺陷，由 test-validator 独立验证确认。
无 compat wrapper / shim / DeprecationWarning / legacy 命名——这是用户预期。
```
