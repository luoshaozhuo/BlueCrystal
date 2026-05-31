# ingest / source_lab mypy 类型治理清单 Round 8

> 日期: 2026-05-30
> 范围: `src/whale/ingest` + `src/whale/shared/source` + `tools/source_lab` + `tests` + `tools/source_lab/tests`
> 状态: 部分收口（`ingest/shared` 已清零；`tools/source_lab` 与测试范围仍 failing）

## 1. 总览

| 项目 | 结果 |
|---|---|
| `mypy src/whale/ingest src/whale/shared/source` | PASS（0 errors） |
| `mypy src/whale/ingest` | PASS（0 errors） |
| `mypy src/whale/shared/source` | PASS（0 errors） |
| `mypy tools/source_lab --explicit-package-bases` | FAIL（234 errors / 38 files） |
| `mypy tests tools/source_lab/tests --explicit-package-bases` | FAIL（494 errors / 101 files） |
| `python -m compileall src/whale/ingest src/whale/shared/source tools/source_lab tests tools/source_lab/tests -q` | PASS |
| `ruff check src/whale/ingest src/whale/shared/source tools/source_lab tests tools/source_lab/tests` | PASS |
| `pytest tests/unit/test_worker_runtime_do_execute.py tests/unit/test_acquisition_job_handler.py tests/unit/test_source_command_use_case.py tests/unit/test_ingest_write_lease.py -q` | 23 passed |
| `pytest tools/source_lab/tests/access/test_protocol_production_readiness_gate.py tools/source_lab/tests/access/test_native_cmd_timeout.py -q` | 28 passed |
| `pytest tests/unit/test_ingest_api_app.py tools/source_lab/tests/access/test_subscribe_scan.py -q` | 2 passed |
| `grep -R "tools.source_lab\\|from tools.source_lab\\|import tools.source_lab" src/whale/ingest src/whale/shared/source` | CLEAN |
| 新增 skip / 降低断言 | 0 |

## 2. 配置与环境事实

| 项目 | 事实 |
|---|---|
| `pyproject.toml` | 存在；本轮新增 `mypy_path = "src"` 以修正包解析基线 |
| `mypy.ini` | 不存在 |
| `setup.cfg` | 不存在 |
| `--explicit-package-bases` | 仅用于 `tools/source_lab` / tests 范围拆分，属于范围控制，不代表该范围通过 |

## 3. 基线重建

### 3.1 修复前基线

| 命令 | 结果 |
|---|---|
| `mypy src/whale/ingest src/whale/shared/source` | 66 errors / 19 files |
| `mypy src/whale/ingest` | 65 errors / 18 files |
| `mypy src/whale/shared/source` | 1 error / 1 file |
| `mypy tools/source_lab --explicit-package-bases` | 318 errors / 50 files |
| `mypy tests tools/source_lab/tests --explicit-package-bases` | 1078 errors / 175 files |

### 3.2 修复后基线

| 命令 | 结果 |
|---|---|
| `mypy src/whale/ingest src/whale/shared/source` | PASS |
| `mypy src/whale/ingest` | PASS |
| `mypy src/whale/shared/source` | PASS |
| `mypy tools/source_lab --explicit-package-bases` | 234 errors / 38 files |
| `mypy tests tools/source_lab/tests --explicit-package-bases` | 494 errors / 101 files |

### 3.3 量化改善

| 范围 | 修复前 | 修复后 | 变化 |
|---|---:|---:|---:|
| `tools/source_lab` | 318 | 234 | -84 |
| `tests + tools/source_lab/tests` | 1078 | 494 | -584 |

## 4. `ingest/shared` P0 收口清单

### 4.1 已修复的关键模块

| 文件 | 主要问题 | 修复方式 |
|---|---|---|
| `src/whale/ingest/api/routes/runtime_config.py` | `object` 与 ORM/响应模型不匹配 | 增加泛型分页 helper、显式 `Select` / ORM 行类型 |
| `src/whale/ingest/api/routes/nodes.py` | helper 缺参数类型 | 补 `sessionmaker[Session]`、`Callable`、ORM 响应类型 |
| `src/whale/ingest/api/routes/leases.py` | helper 缺参数类型 | 同上，补 `IngestJobLease` 响应类型 |
| `src/whale/ingest/api/routes/bundles.py` | helper 缺参数类型 | 同上，补 `IngestBundleMetadata` 响应类型 |
| `src/whale/ingest/api/routes/security_partitions.py` | ORM 字段 / 审计参数类型不清 | 转成 SQLAlchemy 2 typed ORM；显式审计参数 |
| `src/whale/ingest/api/routes/scheduler_jobs.py` | `**kwargs` 审计参数不透明 | 改成显式可选参数，补 `IngestRuntimeJob` 响应类型 |
| `src/whale/ingest/api/routes/acquisition_tasks.py` | 响应字段与 ORM 不一致 | `AcquisitionTaskResponse` 增加 `task_status` 并绑定 ORM |
| `src/whale/ingest/api/app.py` | `union-attr` / evaluator 签名不一致 | 用 `Protocol` + `inspect.signature` 包装兼容 3/4 参数 evaluator |
| `src/whale/ingest/api/audit_middleware.py` | middleware override 类型错误 | 使用 `RequestResponseEndpoint` / `Response` 正确签名 |
| `src/whale/ingest/api/idempotency.py` | Starlette headers 动态结构 | 局部校验并收窄为 `list[tuple[bytes, bytes]]` |
| `src/whale/ingest/adapters/state/redis_source_state_cache.py` | Redis 构造 kwargs 类型不稳定 | 去掉动态 kwargs，改为显式关键字参数 |
| `src/whale/ingest/adapters/source/opcua_source_write_adapter.py` | readback 返回类型过宽 | 以 `RawDataValue` + `None` 分支收窄 |
| `src/whale/ingest/runtime/worker_runtime.py` | `int(object)` / `import-untyped` | 使用安全解析器；对 APScheduler stub 缺失做局部文件级说明 |
| `src/whale/ingest/usecases/source_command_use_case.py` | `int(object)` 不安全 | 增加 `bool/int/float/str` 分支解析 |
| `src/whale/shared/source/iec61850/backends/libiec61850_report_backend.py` | subscribe 参数字典结构不清 | 引入 `_SubscribeArgs` TypedDict |

### 4.2 边界约束检查

| 检查项 | 结果 |
|---|---|
| 生产路径 `import tools.source_lab` | 未发现 |
| 通过扩大 `Any` 制造通过 | 未采用 |
| 新增无解释 `# type: ignore` | 未采用 |
| 新增 `# mypy: disable-error-code=import-untyped` | 1 处，`worker_runtime.py`，原因是 APScheduler 无官方 stub，且仅限第三方导入边界 |

## 5. `tools/source_lab` 首批高价值修复

### 5.1 已落地类别

| 类别 | 文件 | 收益 |
|---|---|---|
| `dict[str, object]` 运行态解析 | `access/runtime/continuity_model.py` | 统一 `int/float` 解析，减少 `arg-type` / `assignment` |
| `dict[str, object]` 运行态解析 | `access/runtime/endpoint_runtime.py` | 为 runtime config / endpoint snapshot 建立局部 parser |
| `dict[str, object]` 状态存储解析 | `access/runtime/state_store.py` | 对 accepted state / registry / snapshot JSON 做结构校验 |
| 测试替身协议对齐 | `tests/access/test_subscribe_scan.py` | runner/provider fake 满足真实协议返回类型 |
| 测试断言收窄 | `tests/access/test_dynamic_endpoint_patch_matrix.py` | continuity metrics 断言改用 `Mapping[str, EndpointContinuityMetrics]` |
| 包解析配置 | `pyproject.toml` | `mypy_path = "src"`，降低 tests/tool 范围导入误判 |

### 5.2 尚未收口的错误分层

#### `tools/source_lab --explicit-package-bases` 剩余 234 errors / 38 files

| 分组 | 典型模块 | 现状 |
|---|---|---|
| 动态结构 `dict[str, object]` 与具体模型不匹配 | `access/runtime/endpoint_registry.py`, `access/runtime/dynamic_cli.py` | 仍是最大可修复簇之一 |
| simulator / protocol 动态字段 | `protocols/modbus/simulator.py` 等 | `attr-defined`、构造参数不匹配集中 |
| runner 返回结构与多态 | `access/runners/registry.py` | `arg-type`、`call-overload`、动态代理字段 |
| 缺注解 | 多个 runtime / test helper 模块 | `no-untyped-def` 仍较多 |
| 可选依赖 / 缺 stub | `asyncua` 等边界 | 部分 `import-untyped` / `attr-defined` |

#### `tests + tools/source_lab/tests --explicit-package-bases` 剩余 494 errors / 101 files

| 分组 | 典型模块 | 现状 |
|---|---|---|
| 测试替身 / fixture 缺类型 | `tools/source_lab/tests/access/*` | `no-untyped-def` 最大头部 |
| 动态对象属性访问 | `test_dynamic_goose_sv_streaming_endpoint_adjustment.py` | `attr-defined` 高集中 |
| ingest 集成测试动态载荷 | `tests/integration/test_ingest_*_source_write.py` | 多为 payload / result 结构不透明 |
| 可选依赖影响的测试模块 | 部分协议测试 | 少量 `import-untyped` |

### 5.3 Top 文件清单

| 范围 | 文件 | 错误数 | 主类型 |
|---|---|---:|---|
| source_lab | `tools/source_lab/tests/access/test_dynamic_goose_sv_streaming_endpoint_adjustment.py` | 84 | `attr-defined` / `no-untyped-def` |
| source_lab | `tools/source_lab/protocols/modbus/simulator.py` | 14 | `attr-defined` / `call-overload` |
| source_lab | `tools/source_lab/access/runtime/endpoint_registry.py` | 14 | `arg-type` / `assignment` |
| source_lab | `tools/source_lab/access/runtime/dynamic_cli.py` | 14 | `arg-type` / `assignment` |
| tests | `tests/integration/test_ingest_opcua_source_write.py` | 26 | 动态断言 / payload 结构 |
| tests | `tests/integration/test_ingest_modbus_source_write.py` | 19 | 动态断言 / payload 结构 |
| tests | `tests/unit/test_iec61850_report_acquisition_adapter.py` | 14 | 动态替身 / 属性访问 |

### 5.4 Top 错误类型

| 范围 | 错误类型 | 数量 |
|---|---|---:|
| `tools/source_lab` | `attr-defined` | 82 |
| `tools/source_lab` | `no-untyped-def` | 32 |
| `tools/source_lab` | `arg-type` | 31 |
| `tools/source_lab` | `call-overload` | 16 |
| `tools/source_lab` | `assignment` | 9 |
| `tests + tools/source_lab/tests` | `no-untyped-def` | 179 |
| `tests + tools/source_lab/tests` | `attr-defined` | 132 |
| `tests + tools/source_lab/tests` | `arg-type` | 42 |
| `tests + tools/source_lab/tests` | `call-overload` | 16 |
| `tests + tools/source_lab/tests` | `no-any-return` | 12 |

## 6. 质量门禁结果

| 命令 | 结果 | 分类 |
|---|---|---|
| `mypy src/whale/ingest src/whale/shared/source` | PASS | fixed |
| `mypy src/whale/ingest` | PASS | fixed |
| `mypy src/whale/shared/source` | PASS | fixed |
| `mypy tools/source_lab --explicit-package-bases` | 234 errors / 38 files | still-failing |
| `mypy tests tools/source_lab/tests --explicit-package-bases` | 494 errors / 101 files | still-failing |
| `python -m compileall ... -q` | PASS | fixed |
| `ruff check ...` | PASS | fixed |
| `pytest tests/unit/test_worker_runtime_do_execute.py ...` | 23 passed | fixed |
| `pytest tools/source_lab/tests/access/test_protocol_production_readiness_gate.py ...` | 28 passed | fixed |
| `pytest tests/unit/test_ingest_api_app.py tools/source_lab/tests/access/test_subscribe_scan.py -q` | 2 passed | fixed |

## 7. Remaining

1. `tools/source_lab` 仍未通过 mypy，不能写成 PASS；后续应优先处理 `endpoint_registry.py`、`dynamic_cli.py`、`registry.py` 与高错误数动态测试模块。
2. `tests` 范围剩余错误仍明显高于源码范围，下一轮应建立 test fake / fixture typed helper，避免每个测试文件各自扩散动态结构。
3. APScheduler 缺 stub 仍是第三方边界问题；当前仅做局部范围控制，退出条件是替换为有 stub 的版本或补充项目内 stub。
