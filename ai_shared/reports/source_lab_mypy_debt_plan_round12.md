# source_lab mypy 分阶段治理债务计划 Round 12

> 日期: 2026-05-30
> 范围: `tools/source_lab`（源码与测试）
> 状态: 部分收口（registry.py 已归零；ingest/shared 保持 PASS）

## 1. 总览

| 范围 | 错误数 | 文件数 | 状态 |
|---|---|---|---|
| `mypy src/whale/ingest src/whale/shared/source` | 1 (import-untyped yaml) | 1 | PASS（唯一边界错误） |
| `mypy src/whale/ingest/api/readyz.py` (新增) | 0 | 0 | PASS |
| `mypy tools/source_lab --explicit-package-bases` | 227 | 37 | still-failing |
| `mypy tools/source_lab/access/runners/registry.py` (Round 12 修复) | 0 | 0 | PASS（本轮清零） |

## 2. 本轮固化的错误（FIXED）

| 文件 | 修复前错误 | 修复后错误 | 修复方式 |
|---|---|---|---|
| `tools/source_lab/access/runners/registry.py` | 8 | 0 | native try 路径使用独立变量名 `native_runner`，fallback 路径干净引入 `runner: CapacityRunner` |

修复的错误列表：
- `Name "runner" already defined on line 1243 [no-redef]` - 消除变量名冲突
- `Incompatible types in assignment (x7)` - 各 fallback runner 类型不再与 NativeCmdCapacityRunner 冲突

## 3. 当前 still-failing 分层

### 3.1 非测试源码（10 文件 / 132 errors）

| 文件 | 错误数 | 主要错误类型 |
|---|---|---|
| `tools/source_lab/access/runtime/endpoint_registry.py` | 68 | `attr-defined`, `arg-type`, `call-overload` |
| `tools/source_lab/access/runtime/dynamic_cli.py` | 32 | `attr-defined`, `arg-type`, `assignment` |
| `tools/source_lab/protocols/modbus/simulator.py` | 14 | `arg-type` (ReadSimulatorResult) |
| `tools/source_lab/fleet.py` | 5 | `misc`, `arg-type` |
| `tools/source_lab/protocols/iec101/simulator.py` | 3 | `arg-type` (ReadSimulatorResult) |
| `tools/source_lab/protocols/iec61850/simulator.py` | 3 | `arg-type` (ReadSimulatorResult) |
| `tools/source_lab/protocols/opcua/simulator.py` | 3 | `arg-type`, `union-attr` |
| `tools/source_lab/model.py` | 2 | `no-untyped-def`, `misc` |
| `tools/source_lab/protocols/registry.py` | 1 | `no-any-return` |
| `tools/source_lab/access/providers/simulator.py` | 1 | `no-any-return` |

### 3.2 测试文件（27 文件 / 95 errors）

| 高错误文件 | 错误数 | 主要错误类型 |
|---|---|---|
| `test_dynamic_goose_sv_streaming_endpoint_adjustment.py` | ~50+ | `attr-defined` (object 无属性) |
| `test_dynamic_cli.py` | ~12 | `no-untyped-def`, `call-overload` |
| `test_server_simulator_facade_capacity_profile_e2e.py` | ~8 | `call-overload` |
| 其余 24 文件 | <5 每文件 | 分散类型 |

### 3.3 错误类型分布

| 错误类型 | 数量 | 修复难度 |
|---|---|---|
| `attr-defined` (object 无属性) | ~65 | 中：需收敛 object 为具体类型 |
| `no-untyped-def` | ~32 | 低：补充类型注解 |
| `arg-type` | ~30 | 中：ReadSimulatorResult 签名统一 |
| `call-overload` | ~19 | 中：动态结构收窄 |
| 其他 (assignment/misc/operator) | ~81 | 分散 |

## 4. 分阶段治理计划

### 4.1 第一阶段（下一轮优先，预计清理 40-50 errors）

目标：解决高价值、集中分布的错误簇。

1. **simulator ReadSimulatorResult 签名统一** (22 errors in 4 files)
   - `protocols/modbus/simulator.py`, `iec101/simulator.py`, `iec61850/simulator.py`, `opcua/simulator.py`
   - 问题：`ReadSimulatorResult` 第 2 个参数要求 `dict`，但传入 `str`
   - 修复：统一 simulator 内部的值构造为 `dict` 或扩展 ReadSimulatorResult 接受 `str`
   - 策略：协议 simulator 仅为测试工具，不进入生产路径

2. **endpoint_registry.py 源头类型收敛** (68 errors)
   - 问题：大量 `object` 访问属性 → `attr-defined`，`dict`/`int`/`float` 重载不匹配
   - 策略：引入局部 TypedDict / dataclass parser，在 JSON 反序列化边界收窄类型
   - 可能联动影响 `dynamic_cli.py` 的 32 errors

3. **model.py 缺少类型注解** (2 errors)
   - 问题：`no-untyped-def`、`None` 迭代
   - 策略：补充参数类型注解，None 守卫

### 4.2 第二阶段（预计清理 50-70 errors）

目标：测试文件高集中错误簇。

4. **GOOSE/SV streaming 测试 typed fixture** (~55 errors in 1 file)
   - `test_dynamic_goose_sv_streaming_endpoint_adjustment.py`
   - 问题：patch/mock 返回 `object`，大量 .connection/.snapshot/.start/.stop 属性访问
   - 策略：引入 typed fake/protocol 类替代裸 `object` 或 `unittest.mock.MagicMock`

5. **fleet.py 类型变体** (5 errors)
   - 问题：`List[SimulatedPoint]` vs `List[SimulatorPoint]`、dict 不变性
   - 策略：使用 `Sequence`/`Mapping` covariant 类型，或显式 cast

### 4.3 第三阶段（预计清理剩余 80-100 errors）

目标：分散错误收尾。

6. **protocols/registry.py no-any-return** (1 error)
   - 问题：工厂方法返回 `Any`
   - 策略：显式类型注解工厂返回值

7. **providers/simulator.py no-any-return** (1 error)
   - 问题：同类型工厂返回
   - 策略：显式类型注解

8. **其余测试 no-untyped-def** (~30 errors in 24 files)
   - 策略：逐文件补充函数签名类型注解

## 5. 本轮已确认的非问题

| 项目 | 说明 |
|---|---|
| `file_access_policy.py` import-untyped yaml | 第三方 stub 缺失，边界控制，不阻塞 |
| 新增 `# type: ignore` 无解释 | 0 |
| 新增 `# mypy: disable-error-code` | 0 |
| 通过扩大 `Any` 制造通过 | 0 |

## 6. 质量门禁基线

| 命令 | Round 8 基线 | Round 12 基线 | 变化 |
|---|---|---|---|
| `mypy src/whale/ingest src/whale/shared/source` | PASS (0) | PASS (1 import-untyped) | 保持 |
| `mypy tools/source_lab --explicit-package-bases` | 234 errors / 38 files | 227 errors / 37 files | -7 errors, -1 file |
| `compileall` | PASS | PASS | 保持 |
| `ruff check` | PASS | PASS | 保持 |
| `registry.py mypy` | 8 errors | 0 errors | ✅ 清零 |

## 7. 下一轮目标

1. 优先修复 simulator ReadSimulatorResult 签名（4 文件，22 errors），降低最大同质错误簇。
2. 推进 endpoint_registry.py 类型收窄（68 errors），可能是联动的最大单一收益项。
3. 不强行推进测试范围 mypy 清零，test fixture 类型化需独立架构决策。
4. 目标：非测试源码 mypy 错误从 132 降到 80 以下。
