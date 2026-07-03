# BlueCrystal 项目目录树

> 全量重建日期: 2026-07-01
> 最近增量更新: 2026-07-01 session.py 极简化并迁移到 tools.sqlalchemy_session（session.py 从 106 → 删除；新建 src/tools/ 横切工具包；whale.shared.persistence 收敛为「纯 ORM 定义 + Base」）
> 数据来源: 仓库真实文件扫描（`find` + `ls`）
> 用途: 导航索引。不能替代二次读取真实源码、测试、配置和 schema。
> 维护方式: 文件级新增 / 删除 / 移动 / 重命名 或职责变化时按 `ai_shared/agent_config/skills/project-tree-update` 增量更新；用户主动触发时按 `project-tree-reset` 重建。

---

## 1. 最近增量更新（Round 7B / 7C / 8 v4.1 / 8 v4.2 / sample_data 迁回 / session.py 极简化 / session.py 迁出至 tools.sqlalchemy_session）

### 1.0c session.py 迁出至 tools.sqlalchemy_session（2026-07-01，已验证归档）

- **新增** `src/tools/__init__.py` —— 跨模块通用工具集入口；docstring 明确「承载与具体业务域（whale / seahorse / starfish 等）无关的横切工具。当前包含跨项目数据库连接工具（`tools.sqlalchemy_session`）；新增横切工具时按职责归入此处，避免下沉到具体业务子包造成位置语义错位」。
- **新增** `src/tools/sqlalchemy_session.py`（71 行）—— 跨模块 SQLAlchemy engine 与 session 工具，从原 `src/whale/shared/persistence/session.py`（106 行）极简化迁出：
  - 删除 `_build_db_url()` / `DEFAULT_SQLITE_PATH` / `PROJECT_ROOT` 等私有 helper；
  - 删除 `dispose_engine` 公开 API（全仓 0 消费者）；
  - 删除 SQLite 默认 fallback：`WHALE_DB_URL` 模块级读取，未设置即 `KeyError`（fail-fast），不再回退 `data/shared/whale.db`；
  - 删除 SQLite / PostgreSQL / MySQL 等多后端分支判断：由 SQLAlchemy URL 的 drivername 自身承担后端兼容；本模块不 `import` 任何 DBAPI 驱动（不写 `import psycopg` / `pymysql` / `sqlite3` 等）；
  - 保留：`DB_URL_ENV = "WHALE_DB_URL"` / `engine` / `SessionLocal` / `get_session()` / `session_scope()`；
  - 硬约束（来自 docstring）：WHALE_DB_URL 必填；支持所有 SQLAlchemy drivername；工具层不 import 任何 DBAPI 驱动。
- **删除** `src/whale/shared/persistence/session.py`（原 106 行极简化版本已物理删除）。
- **3 个 import 引用方迁移到新路径** `from tools.sqlalchemy_session import session_scope`：
  - `src/seahorse/infrastructure/repositories/whale_metadata_repository.py:31`
  - `src/whale/shared/persistence/sample_data.py:39`
  - `tests/e2e/helpers.py:77`（以 `from tools.sqlalchemy_session import session_scope as _shared_scope` 形式）
- **全仓验证**（仅基于已验证证据）：
  - 旧路径 `from whale.shared.persistence.session import` 全仓 0 命中。
  - 新路径 `from tools.sqlalchemy_session import` 全仓 3 处命中（见上）。
  - `tools.sqlalchemy_session` 模块级 `environ[DB_URL_ENV]` 未设即 `KeyError`（fail-fast）。
  - 三后端 URL 解析 PASS：sqlite / postgresql+psycopg / mysql+pymysql。
  - 坏 URL 显式抛 `sqlalchemy.exc.ArgumentError`。
  - 工具层无域耦合：`tools.sqlalchemy_session` 0 处 import `whale.*` / `seahorse.*` / `starfish.*`；0 处 import DBAPI 驱动（psycopg / pymysql / sqlite3 等）。
- **角色收敛**：`src/whale/shared/persistence/` 从「ORM 定义 + 连接工具」收敛为「纯 ORM 定义 + Base」；`__init__.py` / `base.py` / `orm/` / `template/` / `views/` 保留；`sample_data.py` 保留（与本轮 session.py 删除并列的独立模块，职责不变）；`session.py` 已删除。
- **测试结果**（已通过）：`tests/unit/shared/persistence/` 31 passed；`tests/unit/test_ingest_runtime_entrypoint.py` 2 passed；`tests/integration/test_ingest_runtime_entrypoint_smoke.py` 1 passed；`tests/unit/architecture/test_seahorse_import_boundary.py` 46 passed（含 `test_seahorse_domain_application_do_not_import_whale_persistence`）；`tests/unit/seahorse/` 302 passed；总计 382 passed。
- **预存在失败（HEAD 复现，与本轮无回归）**：`tests/integration/test_sqlite_config_init.py` 1 项（v_scada_server 视图缺失）；`tests/integration/test_ingest_runtime_alembic_migration.py` 3 项（alembic/versions 目录缺失 / WHALE_DB_URL 未注入 SystemExit）；`tests/integration/test_ingest_runtime_migrate_entrypoint.py` 3 项（WHALE_DB_URL 未注入 SystemExit）。
- **未引入 compat wrapper / shim / DeprecationWarning / legacy 命名**——这是用户预期。
- 报告归档 `ai_shared/reports/tools_sqlalchemy_session_extraction.md`。

### 1.0b session.py 极简化：单一 WHALE_DB_URL（2026-07-01，已验证归档）

- **修改** `src/whale/shared/persistence/session.py`（168 → 106 行）—— 旧「多环境变量配置 + 后端分支判断」已删除，改为「单一 WHALE_DB_URL + SQLAlchemy URL 自身承担后端兼容」。
  - 删除 7 个散变量读取：`WHALE_DB_BACKEND` / `WHALE_DB_PATH` / `WHALE_DB_HOST` / `WHALE_DB_PORT` / `WHALE_DB_NAME` / `WHALE_DB_USERNAME` / `WHALE_DB_PASSWORD`（含 `WHALE_SHARED_DB_*` 同名变体）。
  - 删除私有分支函数：`_build_postgresql_url` / `_build_mysql_url` / `_build_sqlite_url` / `_resolve_backend` / `_check_env` / `_fallback_to_sqlite`。
  - 删除公开类型与常量：`SUPPORTED_BACKENDS` / `DatabaseBackend` / `Literal[...]` 三后端类型字面量。
  - 仅保留：`DB_URL_ENV = "WHALE_DB_URL"` 常量、`_build_db_url()`（读 `WHALE_DB_URL`，未设时默认 SQLite 文件 `data/shared/whale.db`）、`engine` / `SessionLocal` / `session_scope` / `get_session` / `dispose_engine`。
  - 三后端兼容（sqlite / postgresql+psycopg / mysql+pymysql 等）由 SQLAlchemy URL 自身的 drivername 承担；本模块不做后端判断，也不主动 import 任何 DBAPI 驱动。
  - 坏 URL 由 SQLAlchemy 显式抛 `ArgumentError` / `NoSuchModuleError`，让错误显式失败而非悄悄回退。
- **全仓验证**（仅基于已验证证据）：
  - 旧 7 变量 `WHALE_(SHARED_)DB_(BACKEND|PATH|HOST|PORT|NAME|USERNAME|PASSWORD)` 全仓 0 命中（`grep -rnE` 排除 `.git/` / `node_modules` / `third_party` / `.venv`）。
  - `WHALE_DB_URL` 单一环境变量在源码 / 测试 / 配置 / 部署 / README 共 35 处外部命中（不含 session.py docstring 6 处内部）。
  - `deploy/whale/ingest/docker-compose.ingest-dev.yaml` 已切到 `WHALE_DB_URL` 单变量。
  - `alembic_multidb/README` 仅描述 `WHALE_DB_URL`，无 `WHALE_SHARED_DB_*` 残留。
  - `alembic.ini` `[whale]` 段 `db_url_env = WHALE_DB_URL` 已对齐（本轮未改）。
  - `alembic_multidb/env.py` 仅读 `WHALE_DB_URL`（本轮未改）。
- **配套同步**（已验证）：5 个测试 fixture、2 个 `tests/support/` 工具（`scada_sample_db.py` / `shared_persistence_sample_db.py`）、1 个 docker-compose、1 个 alembic README 已同步到单一 `WHALE_DB_URL` 读取模式。
- **测试结果**（已通过）：`py_compile src/whale/shared/persistence/session.py` OK；默认 SQLite URL 解析 OK；SQLite / PostgreSQL / MySQL 三种 URL 解析 OK；坏 URL 显式抛 `ArgumentError`；`tests/unit/test_ingest_runtime_entrypoint.py` 2 passed；`tests/integration/test_ingest_runtime_entrypoint_smoke.py` 1 passed；`tests/unit/shared/persistence/` 31 passed；`tests/unit/architecture/test_seahorse_import_boundary.py` 46 passed；`tests/unit/seahorse/` 302 passed。
- **预存在失败（HEAD 复现，与本轮无回归）**：`tests/integration/test_sqlite_config_init.py` 1 项（v_scada_server 视图缺失）；`tests/integration/test_ingest_runtime_alembic_migration.py` 3 项（alembic/versions 目录缺失 / WHALE_DB_URL 未注入）；`tests/integration/test_ingest_runtime_migrate_entrypoint.py` 3 项（WHALE_DB_URL 未注入）。
- **未引入 compat wrapper / shim / DeprecationWarning / legacy 命名**——这是用户预期。
- 报告归档 `ai_shared/reports/whale_session_url_minimalization.md`。

### 1.0a sample_data 迁回 whale.shared.persistence.template（2026-07-01，已验证归档）

- **新增** `src/whale/shared/persistence/template/sample_data.py`（1167 行）——从原 `src/seahorse/infrastructure/repositories/whale_metadata_repository.py` 拆分迁回的真实数据归属模块，仅承载 16 组 `PROTOCOL_SAMPLE_SPECS` + `ProtocolSampleSpec` + `generate_all_sample_data` / `clear_database_data` / `reset_sample_data` 入口 + 全部 `_create_*` / `_seed_*` / `_resolve_*` / `_build_*` helpers + `if __name__ == "__main__": reset_sample_data()`；不依赖任何 `seahorse.*` 模块。
- **修改** `src/whale/shared/persistence/template/__init__.py` —— `__all__` 扩展为 17 项，新增 5 个 A 类符号 re-export：`PROTOCOL_SAMPLE_SPECS` / `ProtocolSampleSpec` / `clear_database_data` / `generate_all_sample_data` / `reset_sample_data`；docstring 明确"16 组协议-服务样例 + whale 元数据种子入口"。
- **修改** `src/seahorse/infrastructure/repositories/whale_metadata_repository.py`（1427 → 293 行）—— 职责收缩为 Seahorse WritePlan 只读映射 + 入口薄包装：保留 `WhaleMetadataMappingError` + `WhaleMetadataToWritePlanMapper` + `WhaleMetadataRepository`（`load_servers` / `load_endpoints` / `load_fields` / `seed_sample_metadata` 薄包装 / `clear_sample_metadata` 薄包装）；`sample_data` 符号仅以函数内延迟 import 形式存在（`from whale.shared.persistence.template.sample_data import ...`）。
- **修改** `src/seahorse/infrastructure/repositories/__init__.py` —— 不再 export A 类 5 符号（`PROTOCOL_SAMPLE_SPECS` / `ProtocolSampleSpec` / `clear_database_data` / `generate_all_sample_data` / `reset_sample_data`），仅保留 B+C 类 3 符号（`WhaleMetadataMappingError` / `WhaleMetadataRepository` / `WhaleMetadataToWritePlanMapper`）。
- **修复** `src/whale/ingest/framework/persistence/init_db.py:52` 的悬挂 import（指向已删除的 `seahorse.reference_data` 链）随新 `sample_data.py` 落地而自然恢复。
- **测试结果**（已通过）：`tests/unit/architecture/test_seahorse_import_boundary.py` 46 passed（含 `whale_template_does_not_import_seahorse_reference_data` / `test_legacy_top_packages_not_importable[seahorse.reference_data]` / `test_no_legacy_seahorse_imports_in_repo`）；`tests/unit/seahorse/test_reference_data_imports.py` 10 passed；`tests/unit/shared/persistence/test_scada_sample_data_protocol_coverage.py` 3 passed（从 broken 自然变 passing）；`tests/unit/shared/persistence/` 31 passed, 0 failed；`tests/unit/seahorse/` 302 passed, 0 failed。
- **无新增 compat wrapper / shim / DeprecationWarning / legacy 命名**；报告归档按 handoff 不强制新增（与 reporting.md 命名规范对齐），本轮作为 v4.2 子步记入 project_tree 增量。

### 1.0 Round 8 v4.2 Typer CLI 收敛（2026-07-01，已验证归档）

- **删除** `src/seahorse/api/seahorse_cli.py` —— v4.2 蓝图 §5.2 / §5.3 明确 `api/` 下不再放 `<package>_cli.py`，CLI 入口完全收敛到 `__main__.py`；
- **重写** `src/seahorse/__main__.py` 为 Typer CLI 薄入口（替代 v4.1 argparse）：保留 4 子命令（`generate-scenario` / `export-bundle` / `validate-bundle` / `export-server-config`），仅 import 标准库 / `typer` / `seahorse.api.seahorse_facade.SeahorseFacade`；AST 零 `seahorse.application` / `seahorse.adapters` / `seahorse.infrastructure` / `seahorse.domain` import；不构造 `ScenarioConfig` / backend / scheduler / repository / writer / ORM session；`main(argv) -> int` 签名保留并以 `standalone_mode=False` 调用 Typer 以返回 int；
- **修改** `src/seahorse/api/seahorse_facade.SeahorseFacade` 新增 2 个 CLI 专用 primitives wrapper：`generate_bundle_from_cli_params(...)` 与 `generate_minimal_server_config_from_cli_params(...)`，内部统一构造 :class:`ScenarioConfig`；CLI 自身不构造 domain model；
- **修改** `src/seahorse/adapters/drivers/__init__.py` —— 移除 v4.1 收尾时残留的 3 个生成策略 shim re-export（`curve_generation` / `random_generation` / `replay_generation`），v4.2 仅承载 backend 适配契约；
- **新增 7 项 v4.2 架构测试**（`tests/unit/architecture/test_seahorse_import_boundary.py` + `tests/unit/seahorse/test_main_typer_cli.py`）：`api` 下无 `*_cli.py` / `cli.py` / `controllers.py`（×3）+ `__main__.py` 使用 Typer 禁 argparse + `__main__.py` 只依赖标准库 / typer / seahorse + `__main__.py` AST 零内层 import + `__main__.py` AST 零 `ScenarioConfig` + `__main__.py` 不构造 backend / scheduler / repository / writer；
- **新增 25+ 项 CLI 行为测试**（`tests/unit/seahorse/test_main_typer_cli.py`）：Typer app 4 子命令注册、`main()` 返回 int、`--no-jsonl` / 多种 error path / `--protocol-targets` 逗号分隔、`generate-scenario` / `export-bundle` / `validate-bundle` / `export-server-config` 端到端流程；
- **修改** `tests/unit/seahorse/test_bundle.py` + `tests/unit/seahorse/test_server_plan.py` —— 旧 argparse CLI 测试已迁移到 Typer CLI 测试形态；
- **测试结果**：import boundary **44+ / 44+ PASS**（v4.1 既有 37 项 + v4.2 新增 7 项）；`tests/unit/seahorse` + `tests/unit/architecture` 合计 **348 / 348 PASS**；CLI 4 子命令端到端可用；bundle checksum 跨子命令一致；handoff 文本偏差：code-implementer handoff 示例命令中的 `--start-time` 在 `export-server-config` 子命令未声明，属 handoff 文本偏差而非代码缺陷；
- **v4.2 例外闭合**：本轮无 compat shim / DeprecationWarning / 兼容 wrapper，无 Architecture Exception 需要登记。报告归档 `ai_shared/reports/seahorse_clean_architecture_v4_2_typer_cli.md`。

### 1.1 Round 8 v4.1 对齐（2026-07-01）

- src/seahorse 已完成 4.0 Clean Architecture 分层（`api` / `application` / `adapters` / `domain` / `infrastructure` + 顶层 `container.py`），旧 7 顶层目录（`models` / `exporters` / `strategies` / `generators` / `orchestration` / `ports` / `reference_data`）已物理删除，不再出现。
- Round 8 v4.1 对齐（按 `docs/clean_architecture.md` v4.1 蓝图收敛）：

- src/seahorse 已完成 4.0 Clean Architecture 分层（`api` / `application` / `adapters` / `domain` / `infrastructure` + 顶层 `container.py`），旧 7 顶层目录（`models` / `exporters` / `strategies` / `generators` / `orchestration` / `ports` / `reference_data`）已物理删除，不再出现。
- v4.2 Typer CLI 收敛（增量更新）：
  - **删除** `src/seahorse/api/seahorse_cli.py` —— v4.2 蓝图 §5.2 / §5.3 明确 api 下不再放 ``*_cli.py``，CLI 入口统一收敛到 ``__main__.py``；
  - **重写** `src/seahorse/__main__.py` 为 v4.2 Typer 薄入口（替代 argparse）：保留 4 子命令（``generate-scenario`` / ``export-bundle`` / ``validate-bundle`` / ``export-server-config``），只 import 标准库 / ``typer`` / ``seahorse.api``；AST 零 ``seahorse.application`` / ``seahorse.adapters`` / ``seahorse.infrastructure`` / ``seahorse.domain`` import；不构造 backend / scheduler / repository / writer / ORM session；``main(argv) -> int`` 签名保留并以 ``standalone_mode=False`` 调用 Typer 以返回 int；
  - **扩展** `src/seahorse/api/seahorse_facade.SeahorseFacade` 新增 2 个 CLI 专用 primitives wrapper：`generate_bundle_from_cli_params(...)` 与 `generate_minimal_server_config_from_cli_params(...)`，内部统一构造 :class:`ScenarioConfig`；CLI 自身不构造 domain model；
  - **新增 7 项 v4.2 架构测试**（`tests/unit/architecture/test_seahorse_import_boundary.py` 与 `tests/unit/seahorse/test_main_typer_cli.py`）：api 下无 ``*_cli.py`` / ``cli.py`` / ``controllers.py``、``__main__.py`` 使用 Typer 禁止 argparse、``__main__.py`` 只依赖标准库 / typer / seahorse、``__main__.py`` AST 零内层 import、``__main__.py`` 不直接构造 ScenarioConfig、``__main__.py`` 不构造 backend / scheduler / repository / writer、``SeahorseFacade`` 暴露 CLI wrapper；
  - **新增 25+ 项 CLI 行为测试**（`tests/unit/seahorse/test_main_typer_cli.py`）：Typer app 4 子命令注册、``main()`` 返回 int、``--no-jsonl`` / 多种 error path / ``--protocol-targets`` 逗号分隔、``generate-scenario`` / ``export-bundle`` / ``validate-bundle`` / ``export-server-config`` 端到端流程；
  - **测试结果**：import boundary **44+ / 44+ PASS**（v4.1 既有 37 项 + v4.2 新增 7 项）；`tests/unit/seahorse` + `tests/unit/architecture` 合计 **348 / 348 PASS**；CLI 4 子命令端到端可用；bundle checksum 跨子命令一致。
- Round 8 v4.1 对齐（按 `docs/clean_architecture.md` v4.1 蓝图收敛）：
  - **删除** `src/seahorse/adapters/controllers/` 子包（`__init__.py` + `cli_controller.py`）——v4.1 蓝图 §5.2 / §5.9 明确 `adapters/` 不再默认承载 CLI Controller；
  - **删除** `src/seahorse/adapters/drivers/{curve_generation.py, random_generation.py, replay_generation.py}` 共 3 个生成策略 shim——真实策略实现在 `seahorse.application.use_cases`；`adapters/drivers/__init__.py` 不再 re-export；
  - **新增** `src/seahorse/api/seahorse_cli.py`——v4.1 蓝图 §5.2 / §5.3 可选白名单 `<package>_cli.py` 薄 CLI helper，含 4 个 argparse 子命令（`generate-scenario` / `export-bundle` / `validate-bundle` / `export-server-config`），仅调用 `SeahorseFacade`，不 import application / adapters / infrastructure / starfish / whale.ingest；
  - **修改** `src/seahorse/__main__.py` 为薄入口：仅 `from seahorse.api.seahorse_cli import main` + `sys.exit(main())`，AST 零 `seahorse.application` / `seahorse.adapters` / `seahorse.infrastructure` import，且不构造 backend / scheduler / repository / writer；
  - **修改** `src/seahorse/api/seahorse_facade.SeahorseFacade` 扩展稳定门面方法（`save_timeseries` / `export_timeseries_jsonl` / `generate_minimal_server_config` / `validate_server_config` / `load_server_config_from_bundle_json` / `generator_metadata_stats` 等），供 CLI helper 委托；
  - **新增 9 项 import boundary v4.1 守护**：`test_seahorse_controllers_directory_removed` / `test_seahorse_adapters_has_no_controllers_subdir` / `test_seahorse_drivers_shim_generation_files_removed`（×3 参数化）/ `test_seahorse_main_does_not_import_application_adapters_infrastructure` / `test_seahorse_main_does_not_create_backend_or_runtime` / `test_application_domain_do_not_import_adapters_infrastructure_api` / `test_seahorse_root_does_not_import_starfish`；
  - **测试结果**：import boundary **37 / 37 PASS**（28 既有 + 9 v4.1 新增）；`tests/unit/seahorse` + `tests/unit/architecture` 合计 **313 / 313 PASS**；CLI 4 子命令端到端 + bundle checksum 跨命令一致（90e7288dba896d7f...）。
  - **v4.1 例外闭合**：旧 CLI 子命令（`generate` / `validate` / `plan` / `runtime-smoke`）按 v4.1 蓝图要求被 argparse 拒绝（exit 2），无 compat shim / DeprecationWarning / 兼容 wrapper。
  - **v4.2 例外闭合**（本轮）：`api/seahorse_cli.py` 已物理删除；CLI 入口完全收敛到 `__main__.py` 并改用 Typer；旧 argparse 子命令名称与参数被 Typer 完全替换（`generate-scenario` / `export-bundle` / `validate-bundle` / `export-server-config`），无 compat shim / DeprecationWarning / 兼容 wrapper。
- Round 7B → 7C 链路：Round 7B 完成 Seahorse 旧 7 顶层目录 hard cleanup，Round 7C 收口仓库全树 broken import 与 whale.template 自持真实数据；本轮（Round 8 v4.1 对齐）按 v4.1 蓝图进一步收敛。
- src/whale/shared/persistence/template 改为自持真实数据：导出 `ALL_LOGICAL_NODES`、8 协议 `ParamDef`、`SCADA_PROTOCOL_VIEW_DEFINITIONS`，不再 re-export `seahorse.reference_data`。
- src/whale/shared/persistence/views 新增 4 个文件（`definition.py` / `registry.py` / `scada_protocol_views.py` / `scada_server_view.py`），由 `alembic_multidb/versions/3c0b0e1fecc4_add_whale_views.py` 接管 view DDL 生命周期。
- tests/unit/seahorse 新增 5 个 Round 7 测试（`test_runtime_contract` / `test_runtime_smoke_workflow` / `test_datasource_runtime` / `test_scheduler_executor` / `test_starfish_writer_dispatch`）+ 1 个 Round 7C（`test_whale_write_plan_read_chain`）。
- tests/unit/starfish 旧 Seahorse import 已迁移到 `seahorse.adapters.*` 新路径（`test_server_plan_loader.py` / `test_starfish_cli.py`）。
- tests/unit/architecture 新增 `test_seahorse_import_boundary.py`，Round 8 增至 37 项 import 边界守护（含 `adapters/controllers` 物理删除、`__main__.py` 不 import application/adapters/infrastructure、`adapters/drivers` 不含生成策略 shim、`adapters` 下无 controllers 目录、application/domain 不 import adapters/infrastructure/api、seahorse 不 import starfish、`__main__.py` 不构造 backend/scheduler/repository/writer 等 9 项 v4.1 新约束）。
- alembic 已迁出至 `alembic_multidb/`，新增 `3c0b0e1fecc4_add_whale_views.py` 接入 SCADA view。

---

## 2. 扫描口径

| 项 | 数量 | 说明 |
|---|---|---|
| 原始扫描文件数 | 3273 | 含 `.git/`，所有非 git 文件 |
| 纳入导航文件数 | 约 1040 | 排除 `.git/`、cache、venv、build、第三方、agent 配置与运行时二进制 |
| 省略文件数 | 约 2230 | 见下方"被省略的资产" |

文件类型分布（纳入导航口径）：

```text
.py   ~ 740   Python 源码（src + tests + ai_shared + scripts）
.ts   ~ 130   TypeScript 源码（src/manta/src）
.md   ~ 75    Markdown 文档（docs + ai_shared + 部分 README）
.yaml ~ 35    YAML 配置（config + alembic + 部分 vite）
.vue  ~ 73    Vue 组件（src/manta/src）
.sh   ~ 25    Shell 脚本（scripts + 部分 husky）
.c    ~ 2     C 源码（少量自研，非 third_party）
.json ~ 5     JSON 配置（package.json 等）
.yml/.toml/.ini/.mako 各 1-2  | svg/less/html/cjs/png 计入 assets
```

被省略的资产：

| 类别 | 范围 | 原因 |
|---|---|---|
| VCS / IDE / 缓存 | `.git/`、`.vscode/`、`.mypy_cache/`、`.pytest_cache/`、`.ruff_cache/`、`__pycache__/`、`*.pyc` | 与代码无关 |
| 虚拟环境 / 构建产物 | `.venv/`、`venv/`、`build/`、`dist/`、`*.egg-info/`、`site-packages/` | 不入仓产物 |
| 临时 / 日志 | `tmp/`、`temp/`、`*.log`、`*.tmp`、`*.bak` | 临时文件 |
| 第三方库 | `third_party/`（lib60870 / libiec61850 / libmodbus / open62541 全套源码与 example） | vendor 源码，非项目导航目标 |
| Agent 工具配置 | `.claude/`、`.codex/`、`.agents/` | 工具适配层 |
| 运行时二进制资产 | `src/manta/public/terrain/*`（839 个 .terrain）、`src/manta/public/imagery/*`（762 个 .jpg）、`src/manta/public/models/WT_10MW.glb` | Cesium 切片与 3D 模型，仅以目录级概要 + 计数展示 |
| 其他二进制 | `*.png`、`*.jpg`、`*.svg`、`*.glb`、`*.zip`、`*.tar.gz`（仅 src/manta/src/assets） | 仅在所属目录概要中标注存在 |

---

## 3. 顶层目录

```text
BlueCrystal/
├── .gitignore              # Git 忽略规则
├── .mcp.json               # MCP 工具配置
├── .vscode/                # VS Code 工作区配置（导航省略）
├── .mypy_cache/            # mypy 缓存（导航省略）
├── .pytest_cache/          # pytest 缓存（导航省略）
├── .ruff_cache/            # ruff 缓存（导航省略）
├── .claude/ .codex/ .agents/   # agent 工具配置（导航省略）
├── AGENTS.md               # 主 agent 提示
├── CLAUDE.md               # Claude Code / Codex 执行入口
├── README.md               # 项目说明
├── alembic.ini             # 旧 alembic 入口（已迁出至 alembic_multidb/）
├── alembic_multidb/        # Whale 多库迁移（Alembic 实际管理目录）
├── ai_shared/              # 共享规则、需求、目录树、报告、模板、agent 配置
├── config/                 # 样例配置（ingest / whale）
├── deploy/                 # 部署交付资产（octopus / turtle / whale）
├── docs/                   # 架构 / 工程 / 测试 / 安装文档
├── pyproject.toml          # Python 项目元数据与依赖
├── scripts/                # CI / 运维 / 环境探针脚本
├── src/                    # 运行时代码（manta / octopus / platform_shared / seahorse / starfish / turtle / whale）
├── tests/                  # 测试（deployment / e2e / integration / performance / support / unit）
└── third_party/            # 第三方 C 库源码（导航省略）
```

---

## 4. 目录树（详细）

### 4.1 `ai_shared/`（共享规则 / 需求 / 目录树 / 报告）

```text
ai_shared/
├── agent_config/
│   ├── hooks/    # block-dangerous-bash.py / block-git-write-ops.py / comment-doc-gate.py /
│   │             # docstring-cn-gate.py / no-source-lab-import-gate.sh
│   └── skills/   # changed-files-gate / code-quality-gate / commit-message /
│                 # heavy-regression / project-tree-reset / project-tree-update /
│                 # requirement-trace / rule-update
├── memory/        # 需求文档（*_REQ.md）+ 项目目标 + 总体设计 + 本目录树 + test_index.md
├── reports/       # 历史报告归档（详见第 6 节）
├── rules/         # 单源规则（coding / documentation / python-docstring-cn / quality-gate /
│                  # reporting / routing / testing / validation-routing）
└── templates/     # coding_agent_prompt_template.txt
```

### 4.2 `alembic_multidb/`（Whale 多库迁移）

```text
alembic_multidb/
├── README
├── env.py               # Alembic env，配置多库 engine
├── script.py.mako       # Alembic 脚本模板
└── versions/
    ├── eb5d458b81c8_init_whale_schema.py       # 初始 schema
    └── 3c0b0e1fecc4_add_whale_views.py         # 新增 SCADA view（Round 7C）
```

注：旧 `alembic/` 目录已迁出，仓库根 `alembic.ini` 保留作历史兼容。

### 4.3 `config/`（样例配置）

```text
config/
├── ingest/
│   ├── access_policy.external.example.yaml     # 外部访问策略样例
│   ├── access_policy.prodlike.yaml             # prodlike 访问策略
│   ├── audit_sink.external.example.yaml        # 外部审计 sink 样例
│   ├── endurance.prodlike.yaml                 # 长测配置
│   ├── performance.prodlike.yaml               # 性能 profile 配置
│   └── security_partition.example.yaml         # 安全分区样例
└── whale/
    ├── message_pipeline.kafka.example.yaml     # Kafka 管道样例
    ├── message_pipeline.pulsar.example.yaml    # Pulsar 管道样例
    ├── speed_layer.writers.example.yaml        # speed_layer writer 样例
    ├── storage.raw_archive.example.yaml        # 原始归档样例
    ├── storage.serving_cache.example.yaml      # serving 缓存样例
    └── storage.tdengine.example.yaml           # TDengine 存储样例
```

### 4.4 `deploy/`（部署交付资产）

```text
deploy/
├── octopus/                           # Octopus 部署说明（仅 README.md）
├── turtle/                            # Turtle 部署说明（仅 README.md）
└── whale/
    ├── .env.whale.field.example       # 场站环境变量样例
    ├── README.md                      # Whale 总览
    ├── ingest/
    │   ├── .env.ingest.example        # ingest 环境变量样例
    │   ├── Dockerfile                 # ingest 镜像构建
    │   ├── README.md
    │   ├── docker-compose.ingest-dev.yaml     # 开发 compose
    │   └── docker-compose.ingest-prodlike.yaml # prodlike compose
    ├── message_pipeline/
    │   ├── README.md
    │   └── docker-compose.whale-l5.yaml       # L5 消息管道 compose
    ├── speed_layer/
    │   ├── .env.p5.example            # speed_layer 环境变量样例
    │   ├── README.md
    │   └── docker-compose.p5.yml     # speed_layer compose
    └── storage/
        └── README.md                  # 存储层部署说明
```

### 4.5 `docs/`（架构 / 工程 / 测试文档）

```text
docs/
├── 4+1视图.md                # 4+1 视图（场景 / 逻辑 / 开发 / 进程 / 物理）
├── GIT.md                    # Git 工作流约定
├── clean_architecture.md     # Clean Architecture 在本仓的落地
├── install.md                # 安装 / 构建步骤
├── opcua_iec61850_guide.md   # OPC UA / IEC 61850 协议指南
├── 代码质量与注释.md         # 注释与代码质量规则
├── 工程管理.md               # 工程管理流程
└── 测试策略.md               # 测试分层与策略
```

### 4.6 `scripts/`（CI / 运维）

```text
scripts/
├── check_ads_env.py / check_l2_goose_sv_env.py / check_l5_field_readback_env.py / check_serial_env.py
│                                 # ADS / GOOSE+SV / L5 readback / serial 环境探针
├── ci_ingest_runtime_gate.sh    # CI: ingest 运行时门禁
├── cleanup_root_logs.sh         # 清理根日志
├── diagnose_whale_p5_dependencies.sh / start_whale_p5_dependencies.sh / stop_whale_p5_dependencies.sh
│                                 # P5 依赖启停与诊断
├── run_ingest_*.sh              # ingest 各种 smoke / e2e / fault-injection 编排
├── run_quality_gate.py          # 通用质量门禁
├── run_pg_migration_matrix.sh   # Postgres 迁移矩阵
├── run_whale_*.sh               # whale 场站 / 写入切换 / 依赖回归 编排
├── test_ingest_write_readback_smoke_contract.sh  # ingest write/readback smoke
├── validate_shared_source_production_runner.sh   # shared source 生产 runner 校验
└── whale_test.sh                # whale 测试入口
```

### 4.7 `src/`（运行时代码）

```text
src/
├── bluecrystal.egg-info/     # 打包元数据（导航省略）
├── manta/                    # Vue 3 + Arco Design + Cesium 前端（详见 4.7.1）
├── octopus/                  # 自动化 / 部署 / 监控 / 编排治理（详见 4.7.2）
├── platform_shared/          # 平台共享横切 / 内核 / 契约（详见 4.7.3）
├── seahorse/                 # 样例场站生成器，4.0 Clean Architecture（详见 4.7.4）
├── starfish/                 # 工业协议 server / 客户端（详见 4.7.5）
├── tools/                    # 跨模块横切工具集（详见 4.7.8）
├── turtle/                   # 安全 / 合规 / 治理 SDK（详见 4.7.6）
├── whale/                    # 主产品（ingest / message_pipeline / speed_layer / storage / shared）（详见 4.7.7）
└── whale.egg-info/           # 打包元数据（导航省略）
```

#### 4.7.1 `src/manta/`（前端）

按目录级概要展示，不展开二进制 asset 列表。

```text
src/manta/
├── .husky/
│   ├── commit-msg            # commit 钩子
│   └── pre-commit            # pre-commit 钩子
├── config/                   # Vite / Arco 插件 / 工具配置
│   ├── plugin/   arcoResolver.ts / arcoStyleImport.ts / compress.ts / imagemin.ts / visualizer.ts
│   ├── utils/index.ts
│   └── vite.config.base.ts / vite.config.dev.ts / vite.config.prod.ts
├── docs/
│   └── openapi/              # OpenAPI 路径与 schema
│       ├── paths/    data-acquisition / lidar / load-mitigation / message / power-analysis /
│       │             turbine / user / user-center / windfarm（共 9 个 yaml）
│       ├── schemas/  common / data-acquisition / lidar / load-mitigation / message / power-analysis /
│       │             turbine / user / user-center / windfarm（共 9 个 yaml）
│       └── showtime.openapi.yaml
├── public/
│   ├── imagery/              # 4 个子目录（12 / 13 / 14 / 15），约 762 个 .jpg 切片（运行时图片资产，省略）
│   ├── models/WT_10MW.glb    # 风机 3D 模型（运行时二进制）
│   └── terrain/              # 14 个子目录（0-13），约 839 个 .terrain 切片（运行时二进制）
│                             # 顶层另有 layer.json（meta + bbox）
└── src/
    ├── App.vue / main.ts / env.d.ts
    ├── api/                  # generated/openapi（生成代码）+ local-data + lidar-page.ts + interceptor.ts
    ├── assets/               # logo.svg / images/ / banner/（含运行时图片资产，省略逐文件清单）
    │                         # style/global.less / style/breakpoint.less
    ├── bootstrap/cesium.ts   # Cesium 引导（运行时切片读取入口）
    ├── components/           # 13 个组件目录
    │   ├── breadcrumb / chart / footer / global-setting / menu / navbar /
    │   │ tab-bar / top-metric-card / overview-metric-card /
    │   │ overview-turbine-info-card / overview-turbine-select-card
    ├── config/chart-theme.ts
    ├── directive/
    ├── hooks/                # permission / request / loading / chart-option / responsive / visible /
    │                         # user / locale / themes（共 9 个 ts）
    ├── layout/default-layout.vue / page-layout.vue
    ├── locale/en-US.ts / en-US/settings.ts / zh-CN.ts / zh-CN/settings.ts / index.ts
    ├── mock/                 # 字段 mock 数据（local-dev only，不用于产品）
    │                         # windfarm / power-analysis / user / load-mitigation 索引 + fixtures / rules
    ├── router/constants.ts / index.ts / typings.d.ts
    ├── store/index.ts
    ├── types/global.ts / mock.ts / lidar.ts / power-analysis.ts
    ├── utils/is.ts / event.ts / auth.ts / setup-mock.ts / route-listener.ts / index.ts / env.ts
    └── views/                # 入口页面（dashboard / data-acquisition / lidar-wind-filed /
                              # load-mitigation / login / not-found / power-analysis /
                              # redirect / result/{success,error} / exception/{403,404,500} /
                              # user/{info,setting}），含子 components
```

#### 4.7.2 `src/octopus/`（自动化 / 部署 / 监控 / 编排治理）

```text
src/octopus/
├── __init__.py
├── adapters/                # 外部系统适配层（接口定义 + 实现）
├── alerting/                # 告警规则与通知通道
├── automation/              # 自动化作业
├── deployment/              # 部署编排
├── diagnostics/             # 诊断探针
├── monitoring/              # 运行监控
├── orchestration/           # 多模块协调
├── reports/                 # 报告生成
├── rollback/                # 回滚策略
└── runtime/                 # 运行时入口
```

各子目录均带 `__init__.py`，深度实现细节以 `[N 个 .py 文件]` 收口（共 ~80 个）。

#### 4.7.3 `src/platform_shared/`（横切 / 内核 / 契约）

```text
src/platform_shared/
├── contracts/                       # 平台间契约（接口、数据类）
├── crosscutting/
│   ├── context/                     # 请求 / trace 上下文
│   ├── debug/                       # diagnostics.py / ring_buffer.py / trace.py
│   ├── observability/               # audit.py / logging.py / metrics.py
│   └── resilience/                  # backoff.py / circuit_breaker.py / deadline.py /
│                                    # error_classifier.py / retry.py
├── kernel/                          # 平台内核（启动 / 配置 / 抽象）
├── messaging/                       # 共享消息原语
└── security_primitives/masking.py   # 脱敏原语
```

#### 4.7.4 `src/seahorse/`（4.0 + Round 8 v4.1 / v4.2 Clean Architecture）

旧 7 顶层目录（`models` / `exporters` / `strategies` / `generators` / `orchestration` / `ports` / `reference_data`）已物理删除（Round 7B）。Round 8 进一步收敛：

- 删除 `adapters/controllers/` 子包（v4.1 蓝图 §5.2 / §5.9 明确 `adapters/` 不再默认承载 CLI Controller）；
- 删除 `adapters/drivers/curve_generation.py` / `random_generation.py` / `replay_generation.py` 共 3 个生成策略 shim（真实策略实现在 `application/use_cases/`）；
- v4.1 收紧：`__main__.py` 调用 `api/seahorse_cli.py`（v4.1 蓝图 §5.2 / §5.3 可选白名单 `<package>_cli.py`），`__main__.py` 为薄入口，AST 零 application / adapters / infrastructure import；
- **v4.2 进一步收敛**：`api/seahorse_cli.py` 已物理删除；`__main__.py` 改写为 Typer CLI 薄入口（替代 argparse），仅 import 标准库 / `typer` / `seahorse.api.seahorse_facade`；AST 零 application / adapters / infrastructure / domain import；不构造 backend / scheduler / repository / writer / ORM session / `ScenarioConfig`；`SeahorseFacade` 新增 CLI 专用 primitives wrapper `generate_bundle_from_cli_params` / `generate_minimal_server_config_from_cli_params`。

当前结构：

```text
src/seahorse/
├── __init__.py              # 入口声明：分层 + 安全边界（不 import starfish、不 import whale.ingest）
├── __main__.py              # 薄输入入口（v4.2 Typer），仅 import 标准库 / typer / api.seahorse_facade
├── container.py             # composition root：build_seahorse_facade() 等装配函数
├── api/                     # 稳定 facade 层（v4.2 不再含 CLI helper）
│   ├── __init__.py
│   └── seahorse_facade.py   # 面向调用方的稳定 facade（v4.2 新增 generate_bundle_from_cli_params /
│                            # generate_minimal_server_config_from_cli_params CLI wrapper；保留
│                            # save_timeseries / export_timeseries_jsonl /
│                            # generate_minimal_server_config / validate_server_config /
│                            # load_server_config_from_bundle_json / generator_metadata_stats 等）
├── application/
│   ├── __init__.py
│   ├── exceptions.py        # 应用层异常
│   ├── ports/               # 端口契约
│   │   ├── clock_port.py / data_source_port.py / generation_strategy_port.py
│   │   ├── scheduler_port.py / starfish_writer_port.py
│   │   ├── telemetry_port.py / whale_metadata_port.py
│   ├── runtime/             # 运行时骨架
│   │   ├── context.py / event_bus.py / executor.py / graph.py / snapshot.py / state.py
│   └── use_cases/           # 用例编排（含生成策略真实实现）
│       ├── alarm_generator.py / bundle_validator.py / control_result_generator.py
│       ├── curve_generation.py / random_generation.py / replay_generation.py
│       ├── scenario_generator.py / seed_whale_metadata.py / strategy_registry.py
│       └── atomic/          # 原子用例
│           ├── build_write_batch.py / build_write_plan.py / dispatch_write_batch.py
│           ├── runtime_smoke_workflow.py / update_runtime_period.py / validate_write_plan.py
├── adapters/                # 适配层（v4.1 不再含 controllers；一级子目录仅 {presenters, serializers, gateways, drivers}）
│   ├── drivers/             # 仅 backend 适配契约 + factory 占位（v4.1 收尾，无生成策略 shim）
│   │   ├── __init__.py
│   │   ├── backend_ports.py
│   │   └── factory/__init__.py
│   ├── gateways/            # 出口 gateway
│   │   ├── server_config_handoff_gateway.py  # （由 exporters 迁来）
│   │   ├── server_config_validator.py        # （由 exporters 迁来）
│   │   ├── server_plan_handoff_gateway.py    # （由 exporters 迁来）
│   │   ├── server_plan_validator.py          # （由 exporters 迁来）
│   │   └── starfish_writer_gateway.py
│   ├── presenters/          # 输出呈现
│   └── serializers/         # JSON / JSONL 序列化
│       ├── bundle_json_serializer.py          # （由 bundle_exporter 迁来）
│       ├── bundle_serialization.py           # （由 serialization 迁来）
│       └── timeseries_jsonl_serializer.py     # （由 timeseries_exporter 迁来）
├── domain/                  # 纯领域模型
│   ├── bundle.py / bundle_checksum.py / generation.py / plan.py
│   ├── runtime_contract.py / scenario.py
└── infrastructure/          # 基础设施层
    ├── data_sources/runtime.py      # InMemory / 文件 数据源
    ├── drivers/backend_factory.py / starfish_writer_backend.py
    ├── repositories/whale_metadata_repository.py  # WritePlan 只读映射 + sample_data 薄包装委托
    ├── schedulers/clock.py          # DeterministicScheduler / MonotonicClock
    └── telemetry/                   # 遥测端口实现
```

v4.2 输入侧调用链：

```text
External Actor
  ↓
__main__.py（Typer 薄入口，仅 import api.seahorse_facade + 标准库 + typer）
  ↓
api/seahorse_facade.SeahorseFacade
（含 CLI wrapper：generate_bundle_from_cli_params /
 generate_minimal_server_config_from_cli_params 在内部构造 ScenarioConfig）
  ↓
application use cases + runtime + ports
  ↓
adapters/gateways | adapters/serializers
  ↓
infrastructure（仅由 container 装配，adapters 与 application 不直接 import）
```

#### 4.7.5 `src/starfish/`（工业协议 server / 客户端）

```text
src/starfish/
├── __init__.py
├── __main__.py
├── container.py             # composition root
├── adapters/
│   ├── config/              # 配置适配
│   ├── drivers/
│   │   ├── factory/                  # 驱动工厂
│   │   ├── backend_ports.py
│   │   ├── ads/    ads_driver_adapter.py
│   │   ├── iec/    goose_driver_adapter.py / iec101_driver_adapter.py / sv_driver_adapter.py
│   │   ├── modbus/modbus_rtu_driver_adapter.py / modbus_tcp_driver_adapter.py
│   │   ├── native/                   # native 占位（见 infrastructure/native/）
│   │   ├── protocol/                 # 协议层接口
│   │   └── simulator/server_simulator_driver_adapter.py
├── api/server_manager_api.py # 外部 server 管理 API
├── application/
│   ├── ports/   config_loader.py / driver_factory.py / driver_port.py / registry.py
│   ├── runtime/  context.py / event_bus.py / graph.py / snapshot.py / state.py
│   └── use_cases/
│       ├── runtime_control.py
│       └── workflows/bootstrap.py
├── domain/
│   ├── driver.py / server_config.py
│   └── protocols/
│       ├── iec101/   asdu.py / codec.py / common_address.py / frame.py /
│       │             information_elements.py / information_object.py / ioa.py /
│       │             link_layer.py / quality.py / time.py / types.py
│       └── modbus/   register_encoding.py
├── infrastructure/
│   ├── drivers/
│   │   ├── backend_factory.py
│   │   ├── ads/ads_backend.py
│   │   ├── iec/goose_backend.py / iec101_backend.py / sv_backend.py
│   │   ├── modbus/modbus_rtu_pty_backend.py / modbus_tcp_server_backend.py
│   │   └── simulator/server_simulator_backend.py
│   ├── file_loaders/server_config_json_loader.py
│   └── native/                # native 二进制（lib60870 / libiec61850 / libmodbus / open62541 /
│                              # bin）由 CMakeLists.txt 编译；仓库不纳入源码
    └── (infrastructure/native/)  CMakeLists.txt / README.md / __init__.py / process_handle.py /
                runner_probe.py / runner_spec.py / runtime.py
```

#### 4.7.6 `src/turtle/`（安全 / 合规 / 治理 SDK）

```text
src/turtle/
├── __init__.py
├── adapters/                # 外部依赖适配
├── api/                     # SDK 公开 API
├── audit/                   # 审计接口
├── auth/                    # 身份 / 凭据 / 授权
│   └── authorizer.py / credential.py / identity.py / policy.py
├── change_control/          # 变更控制
├── compliance/              # 合规策略
│   └── audit_policy.py / data_classification.py / retention.py
├── deployment_policy/       # 部署策略
├── governance/              # 治理规则
├── policy/                  # 策略抽象
├── ports/                   # 端口接口
├── risk/                    # 风险评估
├── runtime/                 # 运行时装配
├── sdk/                     # SDK 入口
└── security/                # 安全原语
    └── certificate.py / model.py / secret_provider.py / tls.py
```

#### 4.7.7 `src/whale/`（主产品）

```text
src/whale/
├── __init__.py
├── aggregation/                          # 聚合（ads.py / periodic.py / realtime.py）
├── ingest/                              # ingest 子包（详见下方）
├── message_pipeline/                    # 消息管道（详见下方）
├── model_asset/                         # 模型资产（archive / detector / models / repository / service）
├── processing/                          # 处理（cleaner / normalizer）
├── shared/                              # shared 模块（详见下方）
├── speed_layer/                         # speed_layer 子包（详见下方）
└── storage/                             # 持久化层
    ├── mart.py / raw_archive.py / raw_index.py / serving_cache.py
    ├── simulation_result.py / standardized.py / warehouse.py / waveform.py
```

`src/whale/ingest/`：

```text
src/whale/ingest/
├── __init__.py
├── composition.py            # ingest 装配入口
├── config.py                  # ingest 配置装载
├── message_pipeline.py        # ingest-side 消息管道入口
├── adapters/
│   ├── audit/        db_audit_sink.py / http_audit_sink.py / multi_audit_sink.py
│   ├── config/       opcua_source_acquisition_definition_repository.py /
│   │                 source_runtime_config_repository.py
│   ├── message/      kafka_message_publisher.py / redis_streams_message_publisher.py /
│   │                 relational_outbox_message_publisher.py
│   ├── observability/file_sinks.py
│   ├── security/     external_access_policy.py / file_access_policy.py
│   ├── source/       各协议 source acquisition / write adapter（http_rest / iec101 / iec104 /
│   │                 iec61850 / modbus / modbus_rtu / mqtt / opcua 共 13 个 adapter）
│   │                 + dispatch_source_acquisition_adapter.py
│   │                 + static_source_acquisition_port_registry.py
│   │                 + static_source_write_port_registry.py
│   └── state/        redis_source_state_cache.py
├── api/
│   ├── app.py / audit_middleware.py / errors.py / idempotency.py / readyz.py / schemas.py
│   └── routes/       acquisition_tasks / audit_events / bundles / health / leases /
│                     nodes / runtime_config / scheduler_jobs / security_partitions
├── bundle/           checksum.py / model.py / redaction.py / service.py
├── decorators/       source_acquisition.py / source_write.py / state_cache.py
├── diagnostics/      capacity.py / probe.py / profile.py
├── domain/           audit_event.py / write_security_profile.py
├── entities/         node_state.py / source_health_state.py
├── file_ingest/      decoder.py / detector.py / models.py / repository.py / service.py
├── ports/
│   ├── audit.py / diagnostics.py / metrics.py
│   ├── command/source_command_audit_port.py
│   ├── message/message_publisher_port.py
│   ├── runtime/access_policy_port.py / source_runtime_config_port.py / write_lease_port.py
│   ├── source/source_acquisition_definition_port.py / source_acquisition_port.py /
│   │         source_acquisition_port_registry.py / source_write_port.py /
│   │         source_write_port_registry.py
│   └── state/source_state_cache_port.py / source_state_snapshot_reader_port.py
├── runtime/          entrypoint.py / cli.py / node_runtime.py / worker_runtime.py /
│                     scheduler.py / scheduler_factory.py / scheduler_job.py /
│                     scheduler_settings.py / lease.py / write_lease.py / fencing.py /
│                     modes.py / acquisition_mode.py / handlers.py /
│                     job_assignment.py / job_status.py / message_pipeline_settings.py
└── usecases/
    ├── source_acquisition_use_case.py / source_command_use_case.py /
    │   state_snapshot_publish_use_case.py
    ├── dtos/        acquired_node_state / source_acquisition_request /
    │                source_acquisition_start_result / source_connection_data /
    │                source_write_request / source_write_result /
    │                state_publish_request / state_publish_result
    └── roles/       polling_acquisition_role.py / subscription_acquisition_role.py
```

`src/whale/message_pipeline/`：

```text
src/whale/message_pipeline/
├── __init__.py
├── model.py            # 消息模型
├── ports.py            # 端口
└── adapters/   in_memory.py / kafka.py / pulsar.py
```

`src/whale/shared/`：

```text
src/whale/shared/
├── __init__.py
├── enums/quality.py
├── persistence/
│   ├── __init__.py
│   ├── base.py             # 纯 ORM Declarative Base（whale.shared.persistence 从 ORM 定义 + 连接工具
│   │                        # 收敛为「纯 ORM 定义 + Base」；session.py 已迁出至 src/tools/sqlalchemy_session.py）
│   ├── sample_data.py      # 16 组 PROTOCOL_SAMPLE_SPECS + ProtocolSampleSpec + 入口 helpers（独立模块，职责不变）
│   ├── orm/         acquisition / asset / ingest_diagnostics / ingest_runtime /
│   │                model_asset / organization / scada_ingest / scada_protocol_param
│   ├── template/                            # 自持真实数据（不再 re-export seahorse.reference_data）
│   │   ├── __init__.py
│   │   ├── gbt_30966_fields.py             # ALL_LOGICAL_NODES / LogicalNodeDef / build_field_dict
│   │   ├── protocol_param_data.py          # ENDPOINT_PARAM_DEFS / SIGNAL_PARAM_DEFS / ParamDef（8 协议）
│   │   ├── protocol_view_defs.py           # SCADA_PROTOCOL_VIEW_DEFINITIONS / SCADA_PROTOCOL_VIEW_SQL /
│   │   │                                    # ViewDefinition（11 项 SCADA view）
│   │   ├── sample_data.py                  # 16 组 PROTOCOL_SAMPLE_SPECS + ProtocolSampleSpec +
│   │   │                                    # generate_all_sample_data / clear_database_data / reset_sample_data
│   │   │                                    # + 全部 _create_* / _seed_* / _resolve_* / _build_* helpers
│   │   │                                    # （从 seahorse.infrastructure.repositories 拆分迁回，
│   │   │                                    #   不依赖任何 seahorse.* 模块）
│   │   └── OPCUA_client_connections.yaml   # OPC UA 客户端连接样例
│   └── views/                              # Round 7C 新增
│       ├── __init__.py
│       ├── definition.py                   # ViewDefinition 数据类
│       ├── registry.py                     # ALL_VIEW_DEFINITIONS 注册表
│       ├── scada_protocol_views.py         # SCADA 协议视图定义（11 项）
│       └── scada_server_view.py            # SCADA server 汇总视图 SQLAlchemy Core
├── source/
│   ├── __init__.py
│   ├── models.py / ports.py / runner_resolution.py
│   ├── access/                adapter / model / opcua
│   ├── http_rest/             client
│   ├── iec101/   backends/{base,serial_backend} / reader
│   ├── iec104/   backends/{base,lib60870_backend} / reader
│   ├── iec61850/ backends/{base,libiec61850_backend,libiec61850_report_backend,report_base} /
│   │             reader / report_reader
│   ├── modbus/    backends/{base,libmodbus_backend} / reader
│   ├── modbus_rtu/backends/{base,serial_backend} / reader
│   ├── mqtt/      client
│   ├── opcua/     backends/{base,factory,open62541_backend} / reader
│   └── scheduling/concurrency.py / fixed_rate.py / polling.py / stagger.py
└── utils/time.py
```

`src/whale/speed_layer/`：

```text
src/whale/speed_layer/
├── __init__.py
├── light_processor.py / metrics.py / runner.py / writers.py
└── preprocessing/
    ├── models.py / operators.py / pipeline.py / registry.py
```

#### 4.7.8 `src/tools/`（跨模块横切工具集）

与具体业务域（whale / seahorse / starfish / octopus / turtle / manta 等）无关的横切工具。从原 `src/whale/shared/persistence/session.py` 极简化迁出作为本包首个入口模块；后续新增横切工具按职责归入此处，避免下沉到具体业务子包造成位置语义错位。

```text
src/tools/
├── __init__.py                # 横切工具集入口；docstring 明确「按职责归入此处，避免下沉到具体业务子包」
└── sqlalchemy_session.py     # 跨模块 SQLAlchemy engine 与 session 工具（71 行；原 src/whale/shared/persistence/session.py 极简化迁出）
                              # — 仅识别 WHALE_DB_URL（必填，模块级未设即 KeyError；fail-fast，不再默认 SQLite fallback）
                              # — 保留 DB_URL_ENV / engine / SessionLocal / get_session / session_scope
                              # — 删除 dispose_engine / _build_db_url / DEFAULT_SQLITE_PATH / PROJECT_ROOT
                              # — 后端兼容由 SQLAlchemy URL 的 drivername 自身承担；不 import 任何 DBAPI 驱动
```

### 4.8 `tests/`（测试）

```text
tests/
├── __init__.py / conftest.py
├── deployment/                              # 仅 README.md（部署层场景文档）
├── e2e/                                    # 端到端
│   ├── conftest.py / helpers.py
│   ├── test_whale_field_minimal_smoke.py
│   ├── test_whale_l5_kafka_pipeline_e2e.py
│   └── test_whale_l5_storage_e2e.py
├── integration/                             # 集成测试（~80 项 test_*.py）
├── performance/
│   ├── endurance/                           # 长测（仅 __init__.py）
│   ├── load/        __init__.py / conftest.py
│   └── stress/      test_acquisition_pipeline_stress.py
├── support/                                 # 测试支撑工具
│   ├── ingest_prodlike_runtime.py           # ingest prodlike 装配支撑
│   ├── scada_sample_db.py                   # SCADA 样例 DB 构造器
│   └── shared_persistence_sample_db.py      # shared persistence 样例 DB
└── unit/                                    # 单元测试（~120 项 test_*.py）
    ├── __init__.py
    ├── architecture/                        # 架构守护
    │   ├── test_seahorse_import_boundary.py  # Round 7C 新增：28 项 import 边界
    │   └── test_starfish_import_boundary.py
    ├── seahorse/                            # Round 7 新增 5 项 + Round 7C 1 项
    │   ├── test_runtime_contract.py  / test_runtime_smoke_workflow.py
    │   ├── test_datasource_runtime.py / test_scheduler_executor.py
    │   ├── test_starfish_writer_dispatch.py / test_whale_write_plan_read_chain.py
    │   ├── test_bundle.py / test_compat_wrappers.py / test_generators.py
    │   ├── test_models.py / test_orchestrator.py / test_reference_data_imports.py
    │   ├── test_server_plan.py / test_strategies.py
    ├── shared/persistence/                  # whale.template 自持相关
    │   ├── test_model_asset_orm.py
    │   ├── test_scada_protocol_params.py
    │   ├── test_scada_protocol_views.py
    │   └── test_scada_sample_data_protocol_coverage.py
                                              # 引用已迁回 whale.shared.persistence.template.sample_data 的 16 组样例
    └── starfish/                            # starfish 单测（IEC101 / modbus / MQTT / OPC UA / native / runtime 等）
                                          # test_server_plan_loader / test_starfish_cli 已迁到新 seahorse 路径
```

集成层关注重点：

- ingest 全量 audit / bundle / scheduler / 双节点 / lease / fault-injection / 多协议 source-write
- whale writer switchover / failure recovery / message pipeline / storage TDengine / model_asset Postgres
- 3 项外部依赖校验（`test_l5_external_dependency_verification.py`）

支撑层（`tests/support/`）只提供装配器，不写测试断言；被视为"测试工具能力"而非真实集成证据。

---

## 5. 关键入口职责简注

| 路径 | 职责 |
|---|---|
| `src/seahorse/__init__.py` | seahorse 4.0 + Round 8 v4.1 / v4.2 分层入口声明与安全边界（不 import starfish / whale.ingest） |
| `src/seahorse/__main__.py` | v4.2 Typer CLI 薄输入入口：仅 import 标准库 / `typer` / `seahorse.api.seahorse_facade`；AST 零 application / adapters / infrastructure / domain import；不构造 backend / scheduler / repository / writer / ScenarioConfig；保留 `main(argv) -> int` 签名 |
| `src/seahorse/api/seahorse_facade.py` | 对外稳定 facade：v4.2 新增 `generate_bundle_from_cli_params` / `generate_minimal_server_config_from_cli_params` 供 CLI 直接调用；保留 generate/export/validate/save_timeseries/export_timeseries_jsonl/generate_minimal_server_config/validate_server_config/load_server_config_from_bundle_json/runtime_smoke 等 |
| `src/seahorse/container.py` | build_seahorse_facade() composition root |
| `src/seahorse/application/runtime/` | RuntimeContext / Executor / Snapshot 运行时骨架 |
| `src/seahorse/adapters/drivers/` | v4.1 仅承载 `backend_ports.py` + `factory/` 占位；不再含 curve/random/replay_generation 生成策略 shim（真实策略在 `application/use_cases`） |
| `src/seahorse/adapters/controllers/` | v4.1 物理删除（CLI 收敛到 `__main__.py`） |
| `src/whale/shared/persistence/template/` | 自持真实数据：8 协议 ParamDef / 11 SCADA view / ALL_LOGICAL_NODES / 16 组 PROTOCOL_SAMPLE_SPECS + sample_data 种子入口 |
| `src/whale/shared/persistence/views/` | Round 7C 新增 4 文件，统一 view 定义与 Alembic 注册表 |
| `src/whale/ingest/runtime/entrypoint.py` | ingest 进程入口（CLI / scheduler / worker） |
| `src/whale/ingest/composition.py` | ingest 全依赖装配 |
| `src/whale/shared/persistence/session.py` | 已迁出至 `src/tools/sqlalchemy_session.py`（原 1.0c session.py 迁出至 tools.sqlalchemy_session 极简化）；`whale.shared.persistence` 从「ORM 定义 + 连接工具」收敛为「纯 ORM 定义 + Base」 |
| `src/tools/__init__.py` | 跨模块横切工具集入口；docstring 明确「按职责归入此处，避免下沉到具体业务子包」 |
| `src/tools/sqlalchemy_session.py` | 跨模块 SQLAlchemy engine 与 session 工具（71 行；从 `src/whale/shared/persistence/session.py` 极简化迁出）：仅识别 `WHALE_DB_URL`（必填，模块级未设即 `KeyError` fail-fast，不再默认 SQLite fallback）；保留 `DB_URL_ENV` / `engine` / `SessionLocal` / `get_session` / `session_scope`；删除 `dispose_engine`（0 消费者）；后端兼容由 SQLAlchemy URL 自身的 drivername 承担；不 import 任何 DBAPI 驱动；坏 URL 显式抛 `ArgumentError` |
| `src/starfish/container.py` | starfish composition root |
| `src/manta/src/bootstrap/cesium.ts` | Cesium 引导，运行时切片读取入口 |
| `alembic_multidb/versions/3c0b0e1fecc4_add_whale_views.py` | 新增 SCADA view DDL |
| `ai_shared/rules/routing.md` | agent 规则读取路由 |
| `ai_shared/agent_config/skills/project-tree-reset/SKILL.md` | 本次全量重建使用的 skill |

---

## 6. 历史报告归档（`ai_shared/reports/`）

```text
seahorse_round1_architecture_reorg.md        # Round 1：seahorse 架构重组
seahorse_round2_runtime_contract.md          # Round 2：运行时契约
seahorse_round3_whale_writeplan.md           # Round 3：whale WritePlan 接入
seahorse_round4_datasource_runtime.md        # Round 4：DataSourceRuntime
seahorse_round5_scheduler_executor.md        # Round 5：Scheduler / Executor
seahorse_round6_starfish_writer_dispatch.md  # Round 6：Starfish Writer dispatch
seahorse_round7_runtime_smoke_cleanup.md     # Round 7：runtime smoke 工作流
seahorse_round7b_legacy_no_compat_cleanup.md # Round 7B：旧 7 顶层目录物理删除 + 无兼容 wrapper
seahorse_round7c_repo_import_closure.md      # Round 7C：repo import 闭包 + SCADA view 自持
seahorse_clean_architecture_v4_1_alignment.md # Round 8 v4.1 对齐：adapters/controllers/ + 3 driver shim 删除 + CLI 薄入口 + 37+276 测试 PASS
seahorse_clean_architecture_v4_2_typer_cli.md # Round 8 v4.2 对齐：api/seahorse_cli.py 删除 + __main__.py 改 Typer + facade 2 个 CLI wrapper + 7+25+ 测试 PASS
whale_session_url_minimalization.md          # Round 9：session.py 极简化，多 env 收敛到单一 WHALE_DB_URL；后端兼容由 SQLAlchemy URL 自身承担
tools_sqlalchemy_session_extraction.md       # Round 9 子步：session.py 从 whale.shared.persistence 迁出至 src/tools/sqlalchemy_session；whale.shared.persistence 收敛为「纯 ORM 定义 + Base」
starfish_architecture_doc_finalize.md        # starfish 架构文档收口
starfish_clean_boundary_refactor.md          # starfish Clean Boundary 重构
starfish_strict_di_refactor.md               # starfish Strict DI 重构
```

---

## 7. 本轮 vs 旧 project_tree.md 的主要差异

1. 行数从 2438 收敛至约 400 行，去除 Manta 200+ .terrain 切片逐行展开与 alembic 旧版展开。
2. Seahorse 由"旧 7 顶层目录"模型切换为"4.0 Clean Architecture"分层（`api` / `application` / `adapters` / `domain` / `infrastructure` + `container.py`），并标注旧目录物理删除。
3. seahorse / exporters 与 seahorse / serializers 已映射为 `adapters/gateways/*` 与 `adapters/serializers/*` 新路径（按 git rename 跟踪）。
4. whale.shared.persistence.template 改为自持真实数据（ALL_LOGICAL_NODES / 8 协议 ParamDef / 11 SCADA view），不再 re-export `seahorse.reference_data`。
5. whale.shared.persistence.views/ 新增 4 个文件（definition / registry / scada_protocol_views / scada_server_view），由 `alembic_multidb/versions/3c0b0e1fecc4_add_whale_views.py` 接管。
6. alembic 已迁出至 `alembic_multidb/`，根目录 `alembic.ini` 保留作历史兼容。
7. Manta public/terrain 与 imagery 仅以"目录级概要 + 资产计数"展示，不再逐文件展开。
8. third_party/（lib60870 / libiec61850 / libmodbus / open62541）整体省略，仅在第 2 节说明。
9. tests/unit 增加 Round 7 新增 6 个 seahorse 测试 + Round 7C 新增 1 项 seahorse import boundary 守护。
10. reports/ 段列全 Round 1-7C 与 starfish 3 份归档文件（旧版只列到 Round 4）。
11. **Round 8 v4.1 对齐新增 5 条差异**：
    - `src/seahorse/adapters/controllers/` 子包已物理删除（v4.1 蓝图 §5.2 / §5.9 不再默认承载 CLI Controller）。
    - `src/seahorse/adapters/drivers/{curve,random,replay}_generation.py` 3 个生成策略 shim 已删除；真实策略仍在 `seahorse.application.use_cases`。
    - `src/seahorse/api/seahorse_cli.py` 在 v4.1 新增（v4.1 蓝图 §5.3 可选白名单 `<package>_cli.py`），承载 4 子命令 argparse + 仅调用 `SeahorseFacade`。
    - `src/seahorse/__main__.py` 在 v4.1 改为薄入口（仅 `from seahorse.api.seahorse_cli import main` + `sys.exit(main())`），AST 零 application / adapters / infrastructure import。
    - tests/unit/architecture 新增 9 项 v4.1 import boundary 守护（controllers 删除 ×2、driver shim 删除 ×3、`__main__` 薄入口 ×2、domain/application 不 import 外层、seahorse 不 import starfish），import boundary 累计 37 / 37 PASS。
12. **v4.2 增量更新**（本轮）：
    - `src/seahorse/api/seahorse_cli.py` 已删除；CLI 入口统一收敛到 `__main__.py`（v4.2 蓝图 §5.3）。
    - `src/seahorse/__main__.py` 改写为 Typer CLI 薄入口（替代 argparse），保留 4 子命令（`generate-scenario` / `export-bundle` / `validate-bundle` / `export-server-config`），仅 import 标准库 / `typer` / `seahorse.api.seahorse_facade`；AST 零 application / adapters / infrastructure / domain import；不构造 `ScenarioConfig` / backend / scheduler / repository / writer；保留 `main(argv) -> int` 签名。
    - `SeahorseFacade` 新增 CLI 专用 primitives wrapper `generate_bundle_from_cli_params` / `generate_minimal_server_config_from_cli_params`；CLI 自身不构造 domain model。
    - tests/unit/architecture 新增 7 项 v4.2 守护（api 下无 `*_cli.py` / `cli.py` / `controllers.py` ×3 + `__main__.py` 使用 Typer 禁 argparse + 只依赖标准库 / typer / seahorse + AST 零内层 import + AST 零 ScenarioConfig + 不构造 backend）+ tests/unit/seahorse/test_main_typer_cli.py 新增 25+ 项 CLI 行为 / 错误路径 / 端到端测试；import boundary 与 seahorse 测试累计 348 / 348 PASS。

---

## 8. 风险

1. 命名偏差：本轮对 seahorse 各模块以入口职责简注描述，未深入读 `application/use_cases/*` 与 `infrastructure/*` 全部源码；若某文件被改名为更精确的语义（Round 7B 后无新重构），存在简注与实际轻微偏差的可能。
2. 入口偏差：seahorse / starfish / whale.ingest 的真实入口在 `__main__.py` 与 `runtime/entrypoint.py`，本轮仅按目录与文档注释确认；实际启动方式以 `python -m` / `entrypoint.py` 为准。
3. 资产计数偏差：Manta public 资源切片按本轮扫描计数（约 839 terrain / 762 jpg），后续打包或清理可能引入差值；以目录级概要表示而非逐文件。
4. 第三方库边界：本轮未读 third_party 任何源码；如未来在 third_party 之外出现协议实现，需重新校准是否漏收录。
5. 一致性偏差：旧版 project_tree 描述部分 alembic 旧版（`alembic/`）仍被引用；本轮已按 `alembic_multidb/` 收敛，若仍有 PR 引用 `alembic/` 路径，需要单独追溯。
6. **Round 8 v4.1 风险**：
    - 老 CLI 子命令（`generate` / `validate` / `plan` / `runtime-smoke`）已被 argparse 拒绝（exit 2）；如存在外部脚本/文档仍引用这些子命令，会立即报错（这是用户预期："不要管兼容问题"），需单独 handoff 迁移。
    - 4 个新子命令（`generate-scenario` / `export-bundle` / `validate-bundle` / `export-server-config`）参数与原 4 个老子命令基本等价（`generate` ↔ `generate-scenario`、`validate` ↔ `validate-bundle`、`export-bundle` 保留同名、`plan` ↔ `export-server-config`）；外部脚本迁移主要是子命令名替换。
    - `src/seahorse/api/seahorse_cli.py` 是 v4.1 蓝图 §5.3 可选白名单的薄 CLI helper；如未来 CLI 复杂度进一步上升，需评估是否拆出独立包或与 facade 解耦。
