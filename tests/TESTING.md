# Whale 主平台测试指南

本文件面向开发者说明 `tests/` 目录的测试组织、运行方式和规则。术语和生命周期阶段以
`ai_shared/rules/testing.md` 为准；本文件只做补充说明，不重复定义。

## 1. 测试阶段与目录

物理目录按历史习惯保留为 `unit/`、`integration/`、`e2e/`、`performance/`，
但物理目录 **不等于** 生命周期测试阶段。测试的实际阶段归属以：

1. `ai_shared/memory/test_index.md`（唯一测试索引）；
2. 测试文件头的生命周期阶段说明；
3. pytest marker（辅助选择，非唯一分类来源）

为准。

| 生命周期阶段 | 典型位置 | 特征标志 |
|---|---|---|
| 开发期验证 | `tests/unit/` | mock/fake/stub/in-memory，无外部依赖 |
| 构建期验证 | 非 pytest | `py_compile`、`ruff`、`mypy`、`cmake --build` |
| 模块集成期验证 | `tests/integration/` | SQLite/TestClient/临时文件/in-memory 闭环 |
| 跨模块联调期验证 | `tests/integration/`、`tests/e2e/` | docker-compose 或 simulator 全链路 |
| 准生产依赖验证期 | `tests/integration/`、`tests/e2e/` | 需真实 Kafka/PG/Redis/S3/TDengine |
| 部署前验收期 | `tests/e2e/`、`scripts/` | 现场最小数据链路、一键预检 |
| 发布后运维验证期 | scripts/monitoring | 健康检查、告警、故障恢复 |

## 2. PASS / FAIL / NOT_RUN

测试执行结果只使用以下三类：

| 结果 | 含义 |
|---|---|
| **PASS** | 已执行且通过 |
| **FAIL** | 已执行且失败 |
| **NOT_RUN** | 未执行，必须写清原因 |

### pytest skipped 测试的处理

pytest 的 `skip`/`skipif`/环境跳过在报告中 **不** 作为独立的 `skipped` 状态。
必须转写为 `NOT_RUN` 并说明原因（如 `MISSING_ENVIRONMENT`）。

NOT_RUN 原因枚举（定义于 `testing.md`）：

| 原因 | 适用场景 |
|---|---|
| `OUT_OF_SCOPE` | 不属本轮验证范围 |
| `MISSING_ENVIRONMENT` | 缺少运行环境、服务、硬件或配置 |
| `MISSING_DEPENDENCY` | 缺少库、二进制、工具或镜像 |
| `MANUAL_REQUIRED` | 需要人工步骤或受控现场条件 |
| `TOO_EXPENSIVE_FOR_THIS_RUN` | 本轮执行成本过高 |
| `USER_NOT_REQUESTED` | 用户或任务未要求执行 |

## 3. 运行测试

### 按目录
```bash
pytest tests/unit/                    # 全部单元测试（开发期验证）
pytest tests/integration/             # 全部集成测试（含模块集成和跨模块联调）
pytest tests/e2e/                     # E2E 测试
```

### 按 marker
```bash
pytest -m unit                        # 开发期验证
pytest -m integration                 # 模块集成期 + 部分跨模块联调
pytest -m e2e                         # 部署前验收 + 跨模块联调
pytest -m l5                          # 准生产依赖验证期（需外部服务）
```

### 按生命周期阶段（通过脚本）
```bash
bash scripts/whale_test.sh --stage 开发期验证 --component whale --module ingest --dry-run
bash scripts/whale_test.sh --stage 模块集成期验证 --component whale --module storage --dry-run
```

### 常用参数
| 参数 | 作用 |
|---|---|
| `-v` / `-vv` | 详细输出 |
| `-q` | 简洁输出 |
| `-s` | 不捕获 print/logging |
| `-x` | 遇到第一个失败立即停止 |
| `--maxfail=N` | 最多 N 个失败后停止 |
| `-m <marker>` | 按 pytest marker 过滤 |
| `-k <expr>` | 按测试名称关键字过滤 |

## 4. 环境依赖速查

| 测试阶段 | PostgreSQL | Redis | Kafka | Docker | 外部服务 |
|---|---|---|---|---|---|
| 开发期验证 | 否 | 否 | 否 | 否 | 否 |
| 构建期验证 | 否 | 否 | 否 | 否 | 否 |
| 模块集成期验证 | SQLite 仅 | 否 | 否 | 否 | 否 |
| 跨模块联调期验证 | 可能 (docker) | 可能 (docker) | 可能 (docker) | 是 | 否 |
| 准生产依赖验证期 | 是 | 是 | 是 | 是 | 是 |

### 启动跨模块联调所需基础设施
```bash
docker compose -f docker-compose.whale-l5.yaml up -d postgres redis kafka minio
```

### 启动准生产依赖所需基础设施
```bash
docker compose -f docker-compose.whale-l5.yaml up -d
python -m seahorse.reference_data
```

## 5. conftest.py

`tests/conftest.py` 被 pytest 自动加载，提供共享 fixture：
- `real_redis_url` / `real_redis_client` / `real_redis_hash_key` -- Redis 连接和 key 管理
- `pytest_configure` -- 自动修正 ingest 后端环境变量到安全默认值

`tests/e2e/conftest.py` 和 `tests/performance/load/conftest.py` 负责 Docker 基础设施的连接和表创建。

## 6. 新增测试时的同步要求

新增或删除测试文件时，必须同步更新 `ai_shared/memory/test_index.md`（唯一测试索引）：

1. **新增测试文件**：在测试资产索引中添加条目（文件名、测试对象、外部依赖、NOT_RUN 条件）。
2. **新增回归测试**：在回归测试列表中添加条目，标注回归分类和状态。
3. **删除测试文件**：从测试资产索引中移除，回归测试状态改为 `RETIRED` 或 `SUPERSEDED`。
4. 不另建其他回归索引文件（如 `issue_regression_index.md`）。
5. 测试索引只维护到文件级别（关键链路可维护到类级别）。

## 7. marker 使用约定

| Marker | 含义 | 执行条件 |
|---|---|---|
| `unit` | 开发期验证，无外部依赖 | 任何环境 |
| `integration` | 模块集成或跨模块联调 | SQLite/TestClient 或 docker-compose |
| `e2e` | 端到端全链路 | 通常需 docker-compose |
| `l5` | 准生产依赖验证期，需真实外部服务 | Kafka/PG/Redis/S3/TDengine 就绪 |
| `smoke` | 最小冒烟验证 | 取决于具体测试 |
| `slow` | 需 native 二进制或执行时间长 | C build 环境 + native runner 就绪 |
| `load` | 负载测试 | 专门环境，不在常规 CI 执行 |
| `stress` | 压力测试 | 专门环境，不在常规 CI 执行 |

marker 用于执行选择，不是测试分类的唯一来源。生命周期阶段以 `test_index.md` 和
文件头说明为准。

## 8. 负载测试与性能测试

`tests/performance/` 下的负载、压力、耐久测试不在常规 CI 执行，按需手动触发。

### 负载测试脚本
```bash
python tests/tmp/load_test.py --turbines 30 --hz 10 --samples 3
```

参数说明：
- `--turbines N`: 最大风机数（默认 30）
- `--hz HZ`: 采集频率（默认 10）
- `--samples S`: 每轮采样数（默认 3）
