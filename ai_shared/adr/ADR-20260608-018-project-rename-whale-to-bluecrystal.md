# ADR-20260608-018-project-rename-whale-to-bluecrystal

## Status

Accepted

## Keywords

- project-rename, naming, product-name, module-name, decouple, whale-module, bluecrystal, project-identity, immutable-runtime-identifier

## Context

本仓库自创立以来代号为 Whale（GitHub 仓库 luoshaozhuo/Whale，本地工作目录 /home/luosh/Whale）。
2026-06-08 用户决定将产品名变更为 BlueCrystal（蓝水晶）。

历史背景：项目内核心 Python 包 `src/whale/` 与项目名巧合同名。
这种"项目名 == 顶级 Python 包名"的耦合在仓库内创造了大量"项目名 == 模块名"的引用，长期会让人误以为
"Whale"是 Python 模块名、而不是产品/项目名。改名是产品定位重整的一部分，但代码内的 `whale` 模块
本身是数据底座子系统（ingest / message_pipeline / speed_layer / storage / model_asset / shared）的稳定实现，
承担关键业务价值，重命名为 bluecrystal 风险大、收益小、与"whale 是模块名"的事实不符。

改名必须在以下三种标识上同时做正确切割：

1. **项目标识（产品 / 仓库 / 工作目录）**——可以替换。
2. **Python 模块标识（包名、import 路径、conda env 名、pip 包名）**——必须保留。
3. **运行时标识（env var 前缀、Kafka topic、Pulsar persistent、Redis key、TDengine DB、PostgreSQL DB、
   S3 bucket、Station ID、容器名、OPC UA URN、数据路径、scripts/config/deploy 目录名）**——必须保留。

本次改名必须是一次性切换，不留 bluecrystal 兼容别名 / shim / alias。

## Decision

### 1. 项目标识（产品 / 仓库 / 工作目录）—— Whele → BlueCrystal

| 范围 | 旧 | 新 |
|---|---|---|
| GitHub 仓库名 | luoshaozhuo/Whale | luoshaozhuo/BlueCrystal（驼峰） |
| 本地工作目录 | /home/luosh/Whale | /home/luosh/BlueCrystal |
| 顶层 README / CLAUDE.md / AGENTS.md 标题 | Whale 平台 / 项目 | BlueCrystal 平台 / 项目 |
| 11 个项目级需求文档 | ai_shared/memory/Whale_REQ_*.md | ai_shared/memory/BlueCrystal_REQ_*.md（git mv，R100，保留历史） |
| 子模块 / 子工具的 docstring 中"Whale 平台"级表述 | Whale 平台 | BlueCrystal 平台 |
| 跨组件文档中"Whale 平台"项目级表述 | Whale 平台 | BlueCrystal 平台 |
| 顶层目录树标题 | Whale 项目目录树 | BlueCrystal 项目目录树 |

### 2. whale 模块（核心数据底座子系统）—— 永久保留

`whale` 是**模块名**，与项目名解耦，未来不会随产品名变更而变动。

- 目录 `src/whale/` 整树保留（ingest / message_pipeline / speed_layer / storage / model_asset / shared / processing / aggregation）。
- `pyproject.toml` 的 `name="whale"` 保留。
- 所有 import 路径 `from whale.*` / `import whale.*` 保留，不引入 `from bluecrystal.*` 兼容层。
- `src/whale/__init__.py` 的 `__version__` / `__author__` 保留。
- `pyproject.toml` 的 `Team Whale` 署名作为模块作者保留。

### 3. 运行时标识 —— 全部跟模块走，保留

改名不动以下运行时标识（这些是**实例/部署级**标识，不属于产品名）：

- **环境变量**：`WHALE_INGEST_*` / `WHALE_SHARED_DB_*` / `WHALE_P5_*` / `WHALE_REDIS_*` / `WHALE_S3_*` /
  `WHALE_TDENGINE_DSN` / `WHALE_KAFKA_BOOTSTRAP_SERVERS` / `WHALE_TEST_POSTGRES_DSN` 等。
- **消息队列**：
  - Kafka topic `whale.ingest.state` / `whale.ingest.state.dlq`
  - Pulsar persistent `persistent://whale/default/ingest-state` / `...-dlq`
- **缓存 key 前缀**：`whale:ingest:state` / `whale:cache:` / `whale:raw-archive`。
- **TDengine DB**：`whale_raw_index` / `whale_standardized`。
- **PostgreSQL DB**：`whale_ingest` / `whale_test`；user/password 默认 `whale`。
- **S3 / MinIO bucket**：`whale-raw-archive` / `whale-l5-test`。
- **Station ID**：`whale-prod` / `whale-dev`。
- **容器名**：所有 `whale-*` 服务（kafka/redis/minio/postgres/tdengine/pulsar/flink/api/worker）。
- **OPC UA URN**：`urn:whale:opcua-server`。
- **数据路径**：`/data/whale/raw_archive` / `/data/whale/checkpoints`。

### 4. 文件 / 目录命名 —— 跟模块走，保留

- `config/whale/` / `deploy/whale/`
- `docker-compose.whale-l5.yaml` / `.env.whale.field.example`
- `scripts/whale_*.sh` / `start_whale_*.sh` / `stop_whale_*.sh` / `diagnose_whale_*.sh` / `run_whale_*.sh`
- `tests/integration/test_whale_writer_*.py`
- `tests/e2e/test_whale_l5_*.py` / `tests/e2e/test_whale_field_*.py`
- `tests/architecture/test_*_import_boundary.py` 内 whale 模块边界断言保留

### 5. 历史档案 —— 原文保留

- `ai_shared/reports/` 所有历史报告（含 `whale_l5_*` / `whale_field_*` / `p5_external_dependency_*` 等命名保留）。
- `ai_shared/adr/` 已通过条目（含本 ADR 之前所有 ADR 引用 `src/whale/` 等路径的文本，**不**回填改写）。
- git 历史 commit message（保留 `Whale` 字样）。
- 本 ADR 之后新写的历史回顾段落提及 Whale 时应使用 "Whale（项目改名前期代号）" 之类的说明形式。

### 6. 不留兼容别名 / shim

- 不引入 `bluecrystal` 别名 / 兼容层 / shim。
- 不创建 `from bluecrystal import whale` 反向桥接。
- 不增加 `import whale as bluecrystal` 写法。
- 改名是一次性切换。

## Consequences

- 仓库内 `src/whale/` 模块与项目名 BlueCrystal **永久解耦**。
- 未来开发者必须理解：**whale 是模块名，BlueCrystal 是项目/产品名**；两者无强绑定关系。
- 11 个项目级 REQ 文档完成 `Whale_REQ_*.md → BlueCrystal_REQ_*.md` 改名（git mv R100，保留历史），但**项目级需求 ID**（如 SF-FR-001、SP-FR-004、TM-FR-001、IL-FR-001 等）**不**变。
- 历史 ADR / 报告 文本中 "Whale" 字样按写作时事实保留，**不**构成"过时引用"。
- `conda env` 名 `whale=0.1.0` 保留；pip 包名 `whale` 保留；`import whale` 永久有效。
- GitHub repo redirect：旧 URL `luoshaozhuo/Whale` 自动 301 到 `luoshaozhuo/BlueCrystal`。
- 本地工作目录 /home/luosh/Whale 需在 Step 4 远端操作完成后 mv 到 /home/luosh/BlueCrystal。
- 改名**不**修改任何源码、测试、Python 包、构建配置、运行时 schema、接口契约。
- 改名**不**引入新的接口契约或 schema 变化。
- 改名**不**要求双跑期——用户确认改名前项目尚未对接外部系统。

## Rejected Options

- **备选 A：把 `src/whale/` 改成 `src/bluecrystal/`，全仓 import 重构。**
  工作量大（`src/whale/` 是数据底座核心包，import 链横跨 6+ 子系统、80+ 测试文件、20+ facade）；
  风险高（与"whale 是模块名"的事实不符，未来如再改名会陷入同款循环）；
  与用户"whale 模块永久保留"的明确决策冲突。
- **备选 B：保留 whale 模块但运行时标识全部改 `BLUECRYSTAL_*`（env var / topic / DB / URN）。**
  出现"whale 包内用 BLUECRYSTAL_* env"的语义割裂；现场已部署的 P5 依赖（PostgreSQL/TDengine/S3/Kafka）
  数据库、topic、bucket 名一旦改名需要重做数据迁移；与用户"运行时标识全部保留"的明确决策冲突。
- **备选 C：保留 whale 模块 + 保留运行时 + 留 `bluecrystal` 兼容别名 / shim。**
  用户明确不要兼容层；多一份维护成本；与"改名是一次性切换"原则冲突。

## Related Files

- `ai_shared/memory/BlueCrystal_REQ_README.md`（已 git mv 自 Whale_REQ_README.md）
- `ai_shared/memory/BlueCrystal_REQ_Project.md`（已 git mv 自 Whale_REQ_Project.md）
- `ai_shared/memory/BlueCrystal_REQ_Ingest.md`（已 git mv 自 Whale_REQ_Ingest.md）
- `ai_shared/memory/BlueCrystal_REQ_SourceLab.md`（已 git mv 自 Whale_REQ_SourceLab.md）
- `ai_shared/memory/BlueCrystal_REQ_SharedSource.md`（已 git mv 自 Whale_REQ_SharedSource.md）
- `ai_shared/memory/BlueCrystal_REQ_Storage.md`（已 git mv 自 Whale_REQ_Storage.md）
- `ai_shared/memory/BlueCrystal_REQ_MessagePipeline.md`（已 git mv 自 Whale_REQ_MessagePipeline.md）
- `ai_shared/memory/BlueCrystal_REQ_BatchLayer.md`（已 git mv 自 Whale_REQ_BatchLayer.md）
- `ai_shared/memory/BlueCrystal_REQ_BatchProcessing.md`（已 git mv 自 Whale_REQ_BatchProcessing.md）
- `ai_shared/memory/BlueCrystal_REQ_SpeedLayer.md`（已 git mv 自 Whale_REQ_SpeedLayer.md）
- `ai_shared/memory/BlueCrystal_REQ_ServingAggregation.md`（已 git mv 自 Whale_REQ_ServingAggregation.md）
- `ai_shared/memory/project_tree.md`（标题 / 顶层标识已更新；whale 模块相关目录名保留）
- `README.md` / `CLAUDE.md` / `AGENTS.md`（项目级标题已更新）
- `src/whale/`（整目录永久保留）
- `pyproject.toml`（`name="whale"` 保留）
- `ai_shared/adr/ADR索引.md`（本 ADR 已追加到列表）

## Supersedes / Superseded By

无。本 ADR 为新增命名决策，不替代已有 ADR。
本 ADR 之后如出现模块名与产品名再次冲突的子决策，应新建专项 ADR（不影响本 ADR 的整体框架）。
