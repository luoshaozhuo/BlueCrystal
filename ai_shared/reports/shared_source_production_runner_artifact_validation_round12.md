# Round 12: shared_source production runner artifact 验证报告

> 日期: 2026-05-30
> 范围: shared_source runner_resolution 模块 production 路径解析契约验证
> 证据等级: L2 contract/stub
> 状态: validation-entry-ready

## 1. 总览

本报告完成 shared_source production runner artifact 验证入口的建设。验证聚焦于
`runner_resolution.py` 模块的路径解析契约正确性，而非验证实际编译完成的 native binary。

| 验证项 | 结果 |
|---|---|
| PRODUCTION_RUNNER_DIR 优先级 | PASS L2 |
| PATH 发现 | PASS L2 |
| dev fallback disabled 不指向 source_lab | PASS L2 |
| 缺失 runner 返回 unavailable（含 install hint） | PASS L2 |
| dev fallback 消息区分 production/dev | PASS L2 |
| is_source_lab_dev_runner_path 正确识别 | PASS L2 |

## 2. 验证入口

验证脚本：`scripts/validate_shared_source_production_runner.sh`

```bash
# 执行路径解析契约验证
bash scripts/validate_shared_source_production_runner.sh
```

pytest 单元测试：
```bash
pytest tests/unit/test_shared_source_runner_resolution.py -q
# 预期：5 passed
```

## 3. 验证细节

### 3.1 PRODUCTION_RUNNER_DIR 优先级

当 `WHALE_SHARED_SOURCE_RUNNER_DIR` 设置为独立目录时，`resolve_native_runner_path()`
优先使用该目录下的 executable，不落入 dev fallback。

```python
os.environ["WHALE_SHARED_SOURCE_RUNNER_DIR"] = "/opt/prod/runners"
result = resolve_native_runner_path(...)
assert result.source == "env:WHALE_SHARED_SOURCE_RUNNER_DIR"
assert result.used_dev_fallback is False
```

### 3.2 PATH 发现

当无 explicit env var 和 shared runner dir 时，通过 `shutil.which()` 在 PATH 中查找。

### 3.3 dev fallback disabled 时不得使用 source_lab native/build

未设置 `WHALE_SHARED_SOURCE_ALLOW_DEV_RUNNER_FALLBACK=1` 时，默认路径不指向
`tools/source_lab/native/build`。默认 fallback 路径为
`/opt/whale/shared-source/bin/<executable>`。

### 3.4 缺失 runner 错误消息

`build_runner_unavailable_message()` 返回的消息包含：
- executable 路径
- 配置建议（specific_env_var、PRODUCTION_RUNNER_DIR、PATH）
- install/build hint
- dev fallback 区分（如使用 dev fallback，明确标注"does not count as a production runner artifact"）

### 3.5 dev fallback 标注

当启用 dev fallback 但 native runner 仍缺失时，错误消息明确标注：
- "Current path is the explicit dev/test fallback"
- "does not count as a production runner artifact"
- 建议 compile 在 source_lab native build 目录

## 4. 四个 protocol backend 接入状态

| Backend | 接入 runner_resolution | 状态 |
|---|---|---|
| OPC UA (open62541) | 是 | `resolve_native_runner_path(executable_stem="open62541_client_runner", specific_env_var="WHALE_OPEN62541_CLIENT_RUNNER_PATH")` |
| Modbus TCP (libmodbus) | 是 | `resolve_native_runner_path(executable_stem="modbus_tcp_polling_runner", specific_env_var="WHALE_MODBUS_CLIENT_RUNNER_PATH")` |
| IEC 104 (lib60870) | 是 | `resolve_native_runner_path(executable_stem="iec104_client_runner", specific_env_var="WHALE_IEC104_CLIENT_RUNNER_PATH")` |
| IEC 61850 MMS (libiec61850) | 是 | `resolve_native_runner_path(executable_stem="iec61850_mms_client_runner", specific_env_var="WHALE_IEC61850_MMS_CLIENT_RUNNER_PATH")` |
| IEC 61850 Report | 是 | `resolve_native_runner_path(executable_stem="iec61850_report_runner", specific_env_var="WHALE_IEC61850_REPORT_RUNNER_PATH")` |

## 5. 独立 artifact 打包/安装运维入口

当前 `runner_resolution.py` 的默认安装路径搜索顺序：

1. `WHALE_SHARED_SOURCE_RUNNER_DIR` 指向的目录
2. PATH 中的可执行文件
3. `/opt/whale/shared-source/bin/`
4. `/usr/local/lib/whale/shared-source/`
5. `/usr/local/bin/`
6. `/usr/bin/`
7. （仅 dev/test）`tools/source_lab/native/build/`

生产环境需执行：
```bash
# 构建 native runner 并安装到生产目录
mkdir -p /opt/whale/shared-source/bin
cp tools/source_lab/native/build/open62541_client_runner /opt/whale/shared-source/bin/
cp tools/source_lab/native/build/modbus_tcp_polling_runner /opt/whale/shared-source/bin/
cp tools/source_lab/native/build/iec61850_mms_client_runner /opt/whale/shared-source/bin/
cp tools/source_lab/native/build/iec104_client_runner /opt/whale/shared-source/bin/
cp tools/source_lab/native/build/iec61850_report_runner /opt/whale/shared-source/bin/
```

## 6. 不得写成通过的事项

| 事项 | 当前状态 | 说明 |
|---|---|---|
| 真实编译好的 production runner artifact | pending | 验证的是路径解析契约，不是编译产物 |
| native runner 在 /opt/whale/shared-source/bin 存在 | pending | 需要独立打包/安装流程 |
| 生产环境 runner 端到端验证 | pending | 需要在目标 OS 执行编译、安装、验证 |

## 7. 证据边界

- **已证明（L2）**：`runner_resolution.py` 的路径解析逻辑正确，契约明确
- **未证明**：真实 production runner artifact 的编译、打包、安装和端到端运行
- **下一轮**：真实构建/打包/安装 native runner 到生产目录并执行 smoke 验证
