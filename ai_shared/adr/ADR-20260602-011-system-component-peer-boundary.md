# ADR-20260602-011: 系统级组件并列边界

## 状态

已采纳

## 背景

Whale 项目最初由单一 `src/whale/` 承载所有生产运行时能力，横切关注点（auth/security/compliance/observability/resilience/debug）全部放在 `src/whale/shared/crosscutting/`。随着系统演进，治理能力和运维编排能力需要独立生命周期、独立质量门禁和独立部署路径，不能继续以 monorepo 内子目录形式附着于 `src/whale/` 内部。

Round 1 架构重构将治理控制面（Turtle）和运维执行面（Octopus）从 `src/whale/` 内部分离，与 Whale（数据底座）形成三个并列的系统级组件。

## 决策

三个系统级组件并列于 `src/` 下，处于同一 Python package namespace 层级：

1. **Whale** (`src/whale/`)：数据底座，负责数据采集（ingest）、处理（processing）、聚合（aggregation）、存储（storage）以及共享层（shared：persistence、source、crosscutting resilience/debug/observability）。Whale 是数据面核心。

2. **Turtle** (`src/turtle/`)：治理控制面，负责认证授权、安全基础、合规基础、审计治理、策略治理、治理框架、风险评估、部署策略、变更控制等横切治理能力。Turtle 以 Python 包形式被 Whale 模块导入，未来可独立部署为治理服务。

3. **Octopus** (`src/octopus/`)：运维执行面，负责运维流程编排、部署管理、监控采集、告警管理、故障诊断、自动化运维、回滚管理和运维报告。Octopus 以 Python 包形式被 Whale 模块部署使用，未来可独立部署为运维平台。

组件间依赖方向：Whale 模块 --> Turtle（导入治理能力），Whale 模块 --> Octopus（调用运维能力）。Turtle 和 Octopus 之间无直接依赖。

共享基础设施通过 `src/whale/shared/` 提供，不建立跨组件的 shared 循环依赖。

## 影响

正向影响：

1. 治理能力和运维能力获得独立的模块边界、版本治理和部署路径。
2. `src/whale/` 内部不再承载与数据采集不直接相关的治理代码。
3. 组件职责边界可追溯，`pyproject.toml` 通过 `pythonpath = ["src"]` 使所有组件可直接导入。
4. 跨组件 import boundary 通过 `test_turtle_octopus_import_boundary.py`（29 tests）门禁保护。

约束：

1. Turtle 和 Octopus 的多数子包当前为 `__init__.py` 空壳（skeleton-ready），尚未实现业务逻辑。
2. `src/turtle/` 下 auth/security/compliance 已有真实代码实现（从 crosscutting 迁入），其余子包（audit/policy/governance/risk/deployment_policy/change_control/ports/adapters/api/runtime/sdk）均为空壳。
3. `src/octopus/` 下所有 11 个子包均为空壳。
4. 跨组件 import 门禁仅验证 AST 级别引用合规（P1 unit/mock），不验证运行时行为。

## 备选方案

1. **保持所有能力在 `src/whale/` 内**：拒绝，因治理和运维能力以子目录形式附属于数据底座无法满足独立治理需求。
2. **Turtle 和 Octopus 放在 `src/whale/` 下作为子包**：拒绝，因这会混淆 component namespace，不利于未来独立部署。
3. **Turtle 和 Octopus 放在 `lib/` 或 `packages/` 下**：拒绝，因 `src/` 布局是 Python 项目主流实践，`pythonpath = ["src"]` 直接可用。

## 拒绝理由

方案 1 拒绝：无法满足独立质量门禁和独立部署路径的要求。
方案 2 拒绝：`src/whale/turtle/` 和 `src/whale/octopus/` 的 import 路径会与 whale 内部模块混淆。
方案 3 拒绝：增加不必要的目录层级，与项目现有 `src/` 布局不一致。

## 验证与后续

- `test_turtle_octopus_import_boundary.py`：29 个门禁测试，P1 unit/mock 级别，验证 AST 引用合规。
- `compileall`：所有 turtle/octopus 模块通过语法检查。
- `ruff`：0 violations。
- `mypy`：0 个新错误。
- 集成和 E2E 测试（auth/audit 集成 24 passed、source_lab gate 48 passed）：确认新路径不破坏已有功能。
- Turtle 和 Octopus 空壳子包的实现是后续工期工作，当前标记为 skeleton-ready。
