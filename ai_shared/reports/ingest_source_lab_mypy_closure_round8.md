# ingest / source_lab mypy 治理收口报告 Round 8

> 日期: 2026-05-30
> 状态: 未收口
> 结论: `src/whale/ingest` 与 `src/whale/shared/source` 已达成 0 errors；`tools/source_lab` 与测试范围 mypy 仍失败，因此本轮不能写“质量门禁收口”。

## 1. 最终结论

| 范围 | 结果 |
|---|---|
| `src/whale/ingest` | PASS（0 errors） |
| `src/whale/shared/source` | PASS（0 errors） |
| `src/whale/ingest + src/whale/shared/source` | PASS（0 errors） |
| `tools/source_lab --explicit-package-bases` | FAIL（234 errors / 38 files） |
| `tests tools/source_lab/tests --explicit-package-bases` | FAIL（494 errors / 101 files） |

## 2. 本轮完成项

1. 真实重建了 5 组 mypy 基线，并将修复前后数量写入 [`ai_shared/reports/ingest_source_lab_mypy_inventory_round8.md`](/home/luosh/Whale/ai_shared/reports/ingest_source_lab_mypy_inventory_round8.md:1)。
2. `src/whale/ingest` 与 `src/whale/shared/source` 的 mypy 错误已清零，覆盖 API route helper、ORM/response 转换、运行时参数解析、第三方边界和 shared backend 参数模型。
3. `tools/source_lab` 完成首批高收益类型修复，重点落在 runtime/state JSON 解析和测试替身协议对齐，错误数从 318 降到 234。
4. `tests + tools/source_lab/tests` 受 `mypy_path = "src"` 与局部测试修复影响，错误数从 1078 降到 494。
5. 质量门禁保持真实通过：`compileall` PASS、`ruff` PASS、指定 pytest 全部 PASS、生产路径 `import tools.source_lab` CLEAN。

## 3. 独立验证结论

### fixed

| 检查项 | 结果 |
|---|---|
| `mypy src/whale/ingest src/whale/shared/source` | PASS |
| `mypy src/whale/ingest` | PASS |
| `mypy src/whale/shared/source` | PASS |
| `python -m compileall ... -q` | PASS |
| `ruff check ...` | PASS |
| `pytest tests/unit/test_worker_runtime_do_execute.py tests/unit/test_acquisition_job_handler.py tests/unit/test_source_command_use_case.py tests/unit/test_ingest_write_lease.py -q` | 23 passed |
| `pytest tools/source_lab/tests/access/test_protocol_production_readiness_gate.py tools/source_lab/tests/access/test_native_cmd_timeout.py -q` | 28 passed |
| `pytest tests/unit/test_ingest_api_app.py tools/source_lab/tests/access/test_subscribe_scan.py -q` | 2 passed |
| `grep import tools.source_lab ...` | CLEAN |

### still-failing

| 检查项 | 结果 |
|---|---|
| `mypy tools/source_lab --explicit-package-bases` | 234 errors / 38 files |
| `mypy tests tools/source_lab/tests --explicit-package-bases` | 494 errors / 101 files |

### insufficient-evidence

| 检查项 | 说明 |
|---|---|
| 全量 `tests/` mypy 清零 | 本轮未达成，且 handoff 未要求把整个 tests 范围清零 |
| 长稳 / 重回归 | 按规则未默认执行 |

### environment-pending

| 检查项 | 说明 |
|---|---|
| APScheduler 完整类型 stub | 第三方依赖侧未解决，仅做边界范围控制 |

## 4. 抽查结果

| 文件 | 抽查结论 |
|---|---|
| `src/whale/ingest/api/routes/runtime_config.py` | 分页与响应转换已显式类型化，未用 `Any` 掩盖 |
| `src/whale/ingest/api/routes/nodes.py` | helper 参数/返回类型齐全 |
| `src/whale/ingest/api/routes/leases.py` | helper 参数/返回类型齐全 |
| `src/whale/ingest/api/routes/bundles.py` | helper 参数/返回类型齐全 |
| `src/whale/ingest/api/routes/acquisition_tasks.py` | ORM -> response 字段对齐，`task_status` 已补齐 |
| `src/whale/ingest/api/app.py` | `union-attr` 已用 `Protocol` + wrapper 收敛，未退化为 `Any` |

## 5. 风险与下一轮优先级

1. `tools/source_lab/access/runtime/endpoint_registry.py` 与 `dynamic_cli.py` 仍是 runtime 动态结构的主战场，适合继续用局部 parser / TypedDict 拆解。
2. `tools/source_lab/tests/access/test_dynamic_goose_sv_streaming_endpoint_adjustment.py` 单文件 84 errors，是下一轮 tests 类型治理最高价值入口。
3. `tests/integration/test_ingest_opcua_source_write.py`、`tests/integration/test_ingest_modbus_source_write.py` 仍保留较多动态断言结构，可作为 ingest tests 首批 typed fixture 试点。

## 6. 收口判断

本轮不能收口。

原因不是 `ingest/shared` 未达标，而是仍有 mypy 范围失败：

1. `tools/source_lab --explicit-package-bases`
2. `tests tools/source_lab/tests --explicit-package-bases`

因此本报告只归档 Round 8 治理证据，不宣称“质量门禁收口”。
