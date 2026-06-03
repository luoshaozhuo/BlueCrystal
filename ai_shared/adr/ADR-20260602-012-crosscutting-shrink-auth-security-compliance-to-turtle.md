# ADR-20260602-012: shared.crosscutting 收缩

## 状态

已采纳

## 背景

Whale 项目早期将全部横切关注点（auth/security/compliance/debug/observability/resilience）统一放在 `src/whale/shared/crosscutting/` 下。随着 Turtle 治理控制面（ADR-20260602-011）的建立，auth（认证授权）、security（安全基础）、compliance（合规基础）三类治理能力应从 `shared.crosscutting` 迁入 `turtle.*`，以形成职责清晰的治理边界。

`debug`（调试工具）、`observability`（可观测性）、`resilience`（韧性）三项属于运行时基础设施能力，不纳入治理控制面，继续留在 `shared.crosscutting` 中维护。

## 决策

1. **迁出**：`whale.shared.crosscutting.auth`、`.security`、`.compliance` 的代码实现迁入 `turtle.auth`、`turtle.security`、`turtle.compliance`。原位置保留 `__init__.py` 作为兼容 shim，通过 `DeprecationWarning` + re-export 提供向后兼容。

2. **保留**：`whale.shared.crosscutting.resilience`（backoff、circuit_breaker、deadline、error_classifier、retry）、`whale.shared.crosscutting.debug`（diagnostics、ring_buffer、trace）、`whale.shared.crosscutting.observability`（audit、logging、masking、metrics）继续在 `shared.crosscutting` 中维护，不迁入 turtle。

3. **兼容 shim**：`crosscutting/__init__.py` 引入 `DeprecationWarning`，并 re-export 核心类型（AccessDecision、CredentialRef、Principal、AccessPolicyPort、Permission、AuditEvent、AuditEventSinkPort、DataClassification、RetentionPolicy、CertificateRef、SecretRef、SecretProviderPort、TlsConfig 等），确保现有消费者无需立即修改 import 路径。

4. **shim 清理条件**：当所有外部消费者（ingest/composition、ingest/adapters/security 等）的 import 路径全部更新为 `turtle.*`，且经过完整回归验证后，可删除 crosscutting 下的 auth/security/compliance 旧文件和 shim `__init__.py`。清理前必须通过 `test_turtle_octopus_import_boundary.py` 的更新版门禁。

5. **门禁保护**：`test_turtle_octopus_import_boundary.py` 通过 AST 扫描确保 `src/whale/` 下新增代码不直接引用 `whale.shared.crosscutting.{auth,security,compliance}`，必须改用 `turtle.{auth,security,compliance}`。

## 影响

正向影响：

1. 治理能力（auth/security/compliance）的代码位置与其架构职责一致：在 Turtle 治理控制面而非 shared 横切层。
2. `shared.crosscutting` 收缩为韧性/调试/可观测能力，职责更聚焦。
3. 向后兼容 shim 确保现有消费者无需立即改动。
4. 门禁测试防止新代码错误地引用旧路径。

约束：

1. `crosscutting/auth/`、`crosscutting/security/`、`crosscutting/compliance/` 下的旧文件（authorizer.py、credential.py、identity.py、policy.py、certificate.py、model.py、secret_provider.py、tls.py、audit_policy.py、data_classification.py、retention.py）虽然内容仍保留，但其 `__init__.py` 已改为 shim，import 时始终触发 `DeprecationWarning`。
2. `crosscutting/security/model.py` 中定义的 `CredentialRef` 和 `SecretRef` 同时存在于 `turtle.auth.credential` 和 `turtle.security.model`。存在类型重复风险，shim `__init__.py` 统一从 `turtle.security.model` 导出，调用方应迁移至此。
3. 6 个 ingest 消费者的 import 路径已在 Round 1 更新为 `turtle.*`，验证通过。
4. 未完成所有外部消费者的 import 迁移前，shim 不可删除。

## 备选方案

1. **直接删除旧 crosscutting 文件，不保留 shim**：拒绝，因会立即破坏所有未迁移的消费者，风险过高。
2. **auth/security/compliance 也留在 shared.crosscutting，仅通过 turtle 做代理**：拒绝，因这会导致两套代码的双向同步负担，且违反了 ADR-20260602-011 的组件边界。
3. **resilience/debug/observability 也迁入 turtle**：拒绝，因这些是运行时基础设施能力而非治理能力，迁入 turtle 会混淆治理控制面和运行时基础设施的职责边界。

## 拒绝理由

方案 1 拒绝：破坏性过强，不符合渐进迁移原则。
方案 2 拒绝：双维护负担和循环依赖风险不可接受。
方案 3 拒绝：运维基础设施能力不应与治理能力混在同一控制面中。

## 验证与后续

### Round 1 验证（shim 过渡阶段）

- `test_turtle_octopus_import_boundary.py`（29 tests）：验证 `src/whale/` 下无新代码引用弃用的 crosscutting 子包。
- `compileall`：turtle、octopus 所有模块通过语法检查。
- `ruff`：0 violations。
- `mypy`：0 个新错误。
- 旧路径 import 验证：`DeprecationWarning` 正确发出，re-export 类型可用。

### Round 4 收口（shim 彻底清理）

- **清理完成日期**：2026-06-02
- **删除文件数**：14 个（auth 目录 5 文件、security 目录 5 文件、compliance 目录 4 文件）
- **影响文件**：
  1. `crosscutting/__init__.py`：移除 DeprecationWarning shim，改为记录迁出历史的普通文档注释
  2. `tests/integration/test_ingest_prodlike_access_policy.py`：import 从 `whale.shared.crosscutting.auth` 更新为 `turtle.auth`
  3. `tests/integration/test_ingest_prodlike_redis_fault_injection.py`：import 更新
  4. `tests/integration/test_ingest_prodlike_audit_metrics_resilience.py`：import 更新
  5. `tests/unit/test_turtle_octopus_import_boundary.py`：新增 ImportError 运行时断言（29 -> 41 tests）
- **门禁通过**：
  - compileall: PASS
  - ruff: 0 violations
  - mypy: strict clean
  - boundary tests: 41 passed
  - integration tests (updated): 7 passed
  - 全仓无旧路径 import 残留
- **后续任务**：无。shim 清理已完成。

### Round 5 收口（platform_shared 完整迁移，2026-06-02）

Round 4 仅完成 auth/security/compliance 的迁出和 shim 清理，剩余 debug/observability/resilience 三子包仍留在 `src/whale/shared/crosscutting/` 中。Round 5 完成最终收口：

- **完成日期**：2026-06-02
- **操作**：将 `src/whale/shared/crosscutting` 整棵目录物理删除，debug/observability/resilience 全部迁入 `src/platform_shared/crosscutting/`
- **新建 platform_shared**：22 个 .py 文件，包含：
  - `crosscutting/debug/` (diagnostics.py, ring_buffer.py, trace.py)
  - `crosscutting/observability/` (audit.py, logging.py, metrics.py)
  - `crosscutting/resilience/` (backoff.py, circuit_breaker.py, deadline.py, error_classifier.py, retry.py)
  - `crosscutting/context/` (骨架)
  - `contracts/` (骨架)
  - `kernel/` (骨架)
  - `messaging/` (骨架)
  - `security_primitives/` (SensitiveDataMasker)
- **删除 whale.shared.crosscutting**：整棵目录 15+ 文件已物理删除，不再兼容
- **import boundary**：全仓 AST 扫描 0 个 `whale.shared.crosscutting` import；11 个旧路径 import 均触发 ImportError
- **平台依赖边界**：AST 扫描确认 platform_shared 0 个上层依赖（不 import whale/turtle/octopus/dolphin/orca/manta）
- **业务文件更新**：6 个文件 import 路径从 `whale.shared.crosscutting.*` 更新为 `platform_shared.*`
- **门禁通过**：
  - boundary tests: 79/79 passed（从 Round 4 的 41 tests 升级至 79 tests）
  - compileall: PASS
  - ruff: 0 violations
  - mypy (platform_shared strict): PASS
  - 关键集成测试和 source_lab 门禁不回退
- **收口报告**：`ai_shared/reports/platform_shared_crosscutting_true_migration_closure_report.md`
- **后续任务**：contracts/kernel/messaging 为空壳骨架，后续按需实现完整能力
