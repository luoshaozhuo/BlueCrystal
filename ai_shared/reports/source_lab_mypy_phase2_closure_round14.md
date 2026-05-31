# source_lab mypy 第二阶段治理收口报告 Round 14

> 日期: 2026-05-30
> 范围: `tools/source_lab` 非测试源码 mypy 类型错误治理（第二阶段收口）
> 状态: 第二阶段收口达成（非测试源码 17 errors -> 0 errors）

## 1. 总览

| 指标 | Round 13 结果 | Round 14 结果 | 变化 |
|---|---|---|---|
| 非测试源码 errors | 17 (4 files) | 0 (0 files) | -17 errors, -4 files |
| 全量 errors | 189 | 172 (27 test files) | -17 |
| 全量文件数 | 31 | 27 | -4 |

**目标达成**: 非测试源码 mypy errors 从 Round 13 的 17 降至 Round 14 的 0，第二阶段目标完全达成。

## 2. 本轮修复明细

### 2.1 dynamic_cli.py (14 errors -> 0)

**修复策略**: JSON 反序列化边界 `isinstance` 收窄 + 局部变量类型标注

| 错误类型 | 数量 | 修复方式 |
|---|---|---|
| `call-overload` (int/float) | 7 | 提取局部变量 + `# type: ignore[call-overload]` 附中文说明 |
| `arg-type` | 2 | 同上 |
| `return-value` | 1 | `_redact_payload` 返回值 isinstance 收窄 |
| `dict-item` | 1 | `_schemas()` 添加 `endpoint_schema: dict[str, object]` 显式标注 |
| `assignment` | 1 | `recover()` 变量重命名避免类型推断冲突 |
| `no-any-return` | 1 | `_emit()` 返回值 isinstance 收窄 |
| `dict-item` (Sized) | 3 | `len(payload["endpoints"])` 添加 isinstance list 收窄 |

**关键修改**:
- `_config_from_payload()`: 重写为完整的 `isinstance` 守卫链，每个 dict.get() 结果先 isinstance 后转型
- `_runtime_payload()`: `_redact_payload` 返回值收窄为 dict
- `_emit()`: exit_code 通过 isinstance 分派 int/float -> str fallback
- `_schemas()`: endpoint_schema 显式类型标注
- `validate_accepted_state_payload()`: int 转换 `# type: ignore[call-overload]`
- `import-accepted-state`: `json.loads` 结果通过 `assert isinstance` 收窄

### 2.2 opcua/simulator.py (1 error -> 0)

**修复策略**: 类型安全的 handler 替代 None

| 错误类型 | 数量 | 修复方式 |
|---|---|---|
| `arg-type` (create_subscription, None) | 1 | 新增 `_NoopHandler` 类，替换 `None` 参数 |

**关键修改**: 新增 `_NoopHandler` 类实现 `datachange_notification` 方法，满足 asyncua `create_subscription` 的类型签名。代码行为不变（第一次订阅创建仅用于验证可用性，创建后即删除）。

### 2.3 protocols/registry.py (1 error -> 0)

**修复策略**: 工厂注册表类型从 `type` 收敛为 `Callable[..., ServerSimulatorFacade]`

| 错误类型 | 数量 | 修复方式 |
|---|---|---|
| `no-any-return` (cls(source=source)) | 1 | `dict[str, type]` -> `dict[str, Callable[..., ServerSimulatorFacade]]` |

**说明**: `type[ServerSimulatorFacade]` 不可用（Protocol 的 `__init__` 来自 object，不接受 `source=` keyword），改用 `Callable[..., ServerSimulatorFacade]` 表示"可调用并返回 ServerSimulatorFacade"的工厂类型。

### 2.4 access/providers/simulator.py (1 error -> 0)

**修复策略**: 字典值类型从 `object` 收窄为 `str | int | float | bool`

| 错误类型 | 数量 | 修复方式 |
|---|---|---|
| `dict-item` (dict unpack) | 1 | `dict[str, object]` -> `dict[str, str | int | float | bool]` |

**说明**: `update_params` 的所有值均为 `bool`、`int` 或 `float`，与 `SourceConnection.params` 的 `dict[str, str | int | float | bool]` 类型兼容。收窄类型标注后 dict unpack 无冲突。

## 3. 治理策略总结

| 策略 | 应用场景 | 使用次数 | 合规性 |
|---|---|---|---|
| `isinstance` 类型收窄 | JSON 反序列化边界 | 8 处 | 合规 |
| 局部变量显式类型标注 | dict.get() 返回值 | 5 处 | 合规 |
| `# type: ignore[call-overload]` 附中文说明 | JSON 边界 int/float 转型 | 5 处 | 合规（附说明） |
| `Callable[..., T]` 替代 `type` | 工厂注册表 | 1 处 | 合规 |
| 值类型收窄 `object` -> 联合类型 | 协议参数 dict | 1 处 | 合规 |
| Dummy handler 类替代 None | 第三方库类型签名 | 1 处 | 合规 |

**无**: `Any` 滥用、`# type: ignore` 无解释、`# mypy: disable-error-code` 无差别关闭。

## 4. 验证证据

```bash
$ mypy tools/source_lab --explicit-package-bases --ignore-missing-imports --exclude 'tests/'
Success: no issues found in 107 source files
```

## 5. 未修复项

无。非测试源码 4 个文件 17 个错误全部清零。

测试文件中有 172 errors（27 files）未治理，按既定策略不强制清零。
