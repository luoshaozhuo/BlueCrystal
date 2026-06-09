# Starfish 模块说明

## 1. 模块定位

`starfish` 是 BlueCrystal 仓库中的协议仿真与协议验证工具层，入口位于 [`src/starfish/__main__.py`](/home/luosh/BlueCrystal/src/starfish/__main__.py)。
它读取 Seahorse 导出的 `starfish_server_plan.json` 契约，通过统一 facade 启动或模拟多协议端点，并提供 `probe`、`profile`、`capacity` 三类轻量工具。

从当前源码看，`starfish` 的硬边界是：

- 通过 [`src/starfish/loader/server_plan_loader.py`](/home/luosh/BlueCrystal/src/starfish/loader/server_plan_loader.py) 读取 JSON 契约，不直接 import `seahorse`。
- 不进入 `whale.ingest` 等生产采集链路。
- 真实运行能力与轻量/占位能力统一收口到 [`src/starfish/registry/runtime_registry.py`](/home/luosh/BlueCrystal/src/starfish/registry/runtime_registry.py)。
- 协议细节主要放在 `facade/`、`protocols/` 和 `native/`，CLI 只做装配与输出。

说明：
部分模块头注释保留了历史轮次描述。本文以当前源码行为为准，尤其以 `runtime_registry.py` 和 `__main__.py` 的真实分发逻辑为准。

## 2. 目录结构

`src/starfish/` 当前可以按职责分成下面几层：

```text
src/starfish/
├── __init__.py              包级说明，声明模块定位与边界
├── __main__.py              CLI 入口，提供 5 个子命令
├── README.md                当前说明文档
├── models/                  ServerPlan 契约模型与通用结果模型
├── loader/                  JSON 契约加载与校验
├── facade/                  协议 facade 与统一生命周期接口
├── registry/                协议到 facade 的工厂分发
├── tools/                   probe / profile / capacity 轻量工具
├── protocols/               当前以 IEC101 / Modbus 编解码与辅助逻辑为主
└── native/                  C/native runner 规格、探测、进程管理与二进制
```

各目录重点如下：

| 目录 | 主要文件 | 作用 |
|---|---|---|
| `models/` | `plan.py` | 定义 `StarfishServerPlan`、`StarfishEndpointPlan`、`ValidationResult`、`LoadResult`、`UnsupportedOperation`。 |
| `loader/` | `server_plan_loader.py` | 负责读取 JSON、校验必填字段、复算 `payload_hash`、构造内存模型。 |
| `facade/` | `server_simulator_facade.py`、`http_rest_facade.py`、`modbus_tcp_facade.py`、`mqtt_facade.py` 等 | 对外统一暴露 `start/stop/health/load_points/read/...` 生命周期接口。 |
| `registry/` | `runtime_registry.py` | 根据 `endpoint.protocol` 选择 `real`、`mqtt-lightweight`、`rtu-lightweight`、`codec-enhanced-plus`、`unavailable`、`stub` 等模式。 |
| `tools/` | `probe.py`、`profile.py`、`capacity.py` | 在 facade 之上做最小探测、耗时采样和轻量容量扫描。 |
| `protocols/iec101/` | `codec.py`、`frame.py`、`asdu.py`、`link_layer.py` 等 | 放协议层编解码与链路层骨架，不直接承担 CLI 或 runner 装配。 |
| `protocols/modbus/` | `register_encoding.py` | 提供 Modbus 寄存器值编解码辅助能力，供 facade 复用。 |
| `native/` | `runner_spec.py`、`runner_probe.py`、`process_handle.py`、`bin/` | 管理 native runner 元信息、可用性探测、子进程生命周期与预编译二进制。 |

## 3. 逻辑视图

### 3.1 主链路

`starfish` 的主链路可以概括为：

```text
ServerPlan JSON
  -> loader.load_server_plan()
  -> models.StarfishServerPlan
  -> registry.create_facades()
  -> facade.start()/health()/read()/...
  -> tools.probe/profile/capacity 或 CLI 输出
```

对应到源码：

1. [`server_plan_loader.py`](/home/luosh/BlueCrystal/src/starfish/loader/server_plan_loader.py) 读取并校验 JSON。
2. [`plan.py`](/home/luosh/BlueCrystal/src/starfish/models/plan.py) 承接内存模型与标准异常。
3. [`runtime_registry.py`](/home/luosh/BlueCrystal/src/starfish/registry/runtime_registry.py) 负责协议分发与模式选择。
4. `facade/*.py` 各自实现协议的运行时行为。
5. [`__main__.py`](/home/luosh/BlueCrystal/src/starfish/__main__.py) 将这些能力组装为 CLI。

### 3.2 分层职责

| 层 | 代表文件 | 职责 | 不负责 |
|---|---|---|---|
| 契约层 | `models/plan.py` | 描述 ServerPlan、校验结果、标准异常 | 不启动协议服务 |
| 加载层 | `loader/server_plan_loader.py` | JSON 读取、结构校验、哈希校验 | 不做运行时分发 |
| 装配层 | `registry/runtime_registry.py` | 协议归一化、facade 创建、模式判定 | 不做 CLI 输出格式 |
| 运行时层 | `facade/*.py` | 端点生命周期、读写、健康检查、订阅/报告 | 不解析命令行 |
| 协议层 | `protocols/*` | 编解码、链路层骨架、寄存器编码 | 不做场景契约校验 |
| 工具层 | `tools/*.py` | probe/profile/capacity | 不替代生产性能或现场验收 |
| native 支撑层 | `native/*` | runner 二进制探测、子进程管理 | 不做上层业务编排 |

### 3.3 facade 模式

按当前 [`create_facade_for_endpoint()`](/home/luosh/BlueCrystal/src/starfish/registry/runtime_registry.py:174) 的实现，常见模式如下：

| 模式 | 典型协议 | 含义 |
|---|---|---|
| `real` | `HTTP_REST`、`MODBUS_TCP`，以及可用时的 `OPC_UA` / `IEC104` / `IEC61850_*` | 有真实 server 或 native runner。 |
| `mqtt-lightweight` | `MQTT` | 使用 TCP JSON-line 的轻量协议外观，不是完整 MQTT broker。 |
| `rtu-lightweight` | `MODBUS_RTU` | 基于 PTY 的本地轻量模式，不等同真实串口现场。 |
| `codec-enhanced-plus` / `codec-enhanced` / `codec-skeleton` | `IEC101` | 协议编解码与链路层骨架可用，但不等同完整 server。 |
| `unavailable` | native 二进制缺失时的 `OPC_UA` / `IEC104` / `IEC61850_MMS` | 代码路径存在，但运行环境不足。 |
| `report-lightweight` | `IEC61850_REPORT` 二进制缺失时 | 保留轻量 report 外壳，不等同完整 runner。 |
| `codebase-pending` | `ADS` 等 | facade 已占位，但实现仍未就绪。 |
| `environment-pending` | `GOOSE`、`SV` | 依赖 L2/PTP 等环境条件。 |
| `stub` | 未注册协议 | 回退到内存 facade。 |

### 3.4 三类关键实现

1. 通用 stub
   [`server_simulator_facade.py`](/home/luosh/BlueCrystal/src/starfish/facade/server_simulator_facade.py) 提供最小的 `start/stop/health/load_points/read/update_values/capabilities`，未实现操作统一抛 `UnsupportedOperation`。

2. 纯 Python 真实 facade
   `HttpRestFacade` 使用 `HTTPServer` 暴露 `GET /points`；
   `ModbusTcpFacade` 使用 socket 处理 `FC03/FC06`；
   `MqttFacade` 使用 TCP JSON-line 协议并额外提供 `SubscriptionQueue`。

3. native runner facade
   `OpcUaFacade`、`Iec104Facade`、`Iec61850MmsFacade`、`Iec61850ReportFacade` 等依赖 `native/bin/` 下的 runner。
   对这些协议，`runtime_registry.py` 先探测二进制，再决定 `real` 还是 `unavailable/report-lightweight`。

## 4. 当前可见使用方式

### 4.1 CLI 入口

CLI 入口在 [`src/starfish/__main__.py`](/home/luosh/BlueCrystal/src/starfish/__main__.py)，当前注册了 5 个子命令：

```bash
python -m starfish load-server-plan --input <path>
python -m starfish smoke-server-plan --input <path>
python -m starfish probe-server-plan --input <path>
python -m starfish profile-server-plan --input <path> --iterations 100
python -m starfish capacity-server-plan --input <path> --point-count 10
```

各命令含义：

| 命令 | 作用 | 关键实现 |
|---|---|---|
| `load-server-plan` | 仅加载并校验 JSON 契约 | `load_server_plan()`（公共命令）+ 共用 helper `_load_plan_or_exit` / `_print_validation` |
| `smoke-server-plan` | 创建 facade，执行 start/health/read/capabilities/stop 等 smoke | `smoke_server_plan()`（公共命令）+ 共用 helper `_load_plan_or_exit` / `_expect_unsupported` + smoke mode dispatch 私有 helper（一级派发表 `_SMOKE_MODE_DISPATCH`：`_smoke_stub` / `_smoke_report_lightweight` / `_smoke_mqtt_lightweight` / `_smoke_rtu_lightweight` / `_smoke_pending`；real 模式二级派发表由 `_smoke_real_dispatch` 内部 `real_dispatch` 字典负责：`_smoke_real_iec61850_report` / `_smoke_real_modbus_tcp` / `_smoke_real_iec61850_mms` / `_smoke_real_pending_3method`） |
| `probe-server-plan` | 逐 endpoint 做最小可用性探测 | `probe_server_plan()`（公共命令）+ `tools/probe.py` |
| `profile-server-plan` | 对 `read()` 做 N 次耗时采样 | `profile_server_plan()`（公共命令）+ `tools/profile.py` |
| `capacity-server-plan` | 做轻量 endpoint/point/read 扫描 | `capacity_server_plan()`（公共命令）+ `tools/capacity.py` |

> 注：上述「关键实现」列以当前 `src/starfish/__main__.py` 的真实结构为准；任何调整以源码为准。
>
> 公共 `main` 入口与 smoke mode dispatch 私有 helper（与表格 5 个子命令正交，作为同一模块的装配骨架）：
>
> - 公共 `main(argv: list[str] | None = None) -> int` 是 Starfish CLI 的统一入口。包装 `typer.main.get_group(app).main(args=..., prog_name="starfish", standalone_mode=False)`，业务错误统一返回整数退出码（0 成功 / 1 业务错误），`--help` / 缺必填参数 / 未知子命令等 typer 元行为由 typer 抛 `SystemExit`（code 0 或 2）。`tests/unit/starfish/test_starfish_cli.py` 与外部脚本直接 `from starfish.__main__ import main` 调用，无需 `subprocess`，不依赖 `app()` 副作用。
> - 模块底部 `if __name__ == "__main__": app()` 直接调用 typer，保留 shell 下「命令名打错由 typer 抛 `SystemExit`」的原始行为；与 `main(argv)` 是两条正交通路（测试走 `main(argv)`，shell 用户走 `app()`）。
> - 模块顶层 5 个 typer command function（`load_server_plan` / `smoke_server_plan` / `probe_server_plan` / `profile_server_plan` / `capacity_server_plan`）保持公共签名不变；私有 helper 一律 `_` 开头、不导出，作为子命令主体的可读切分。
> - smoke 模式分支（`stub` / `unavailable` / `report-lightweight` / `mqtt-lightweight` / `rtu-lightweight` / `codebase-pending` / `environment-pending` 一级 + real 模式按 `facade.protocol` 二级）由 dispatch 表收敛，行为与既有 `smoke_server_plan` 主体 6 步序列（health → start → read initial_values → capabilities → mode-specific dispatch → stop）保持一致。

### 4.2 ServerPlan 加载规则

[`load_server_plan()`](/home/luosh/BlueCrystal/src/starfish/loader/server_plan_loader.py:232) 当前会重点检查：

- 顶层必填字段是否存在。
- `schema_version` 是否匹配 `1.0.0`。
- `scenario_id` 是否为空。
- `synthetic` 是否为布尔值。
- `endpoints` 和 `points` 是否为非空列表且关键字段存在。
- `capabilities` 是否为列表。
- `initial_values` 是否为字典。
- `payload_hash` 复算是否一致。

### 4.3 工具层调用特点

1. `probe`
   调用 `load_points -> start -> health -> read`，输出 `PASS/FAIL/NOT_RUN` 语义。

2. `profile`
   只针对 `facade.read()` 做耗时采样，统计 `count/min/max/avg`，不做 p95/p99，也不等同性能验收。

3. `capacity`
   只做轻量扫描，核心关注 `endpoint_count`、`point_count`、`read_count` 和 `max_tested_points`，不等同压测或容量规划。

## 5. native 目录说明

`src/starfish/native/` 不是业务文档目录，而是 runner 支撑层：

- `bin/` 放可探测、可执行的 runner 二进制。
- `runner_spec.py` 定义 `NativeRunnerSpec`。
- `runner_probe.py` 只做存在性、大小、可读性探测。
- `process_handle.py` 负责子进程启动、就绪等待、停止。

[`src/starfish/native/README.md`](/home/luosh/BlueCrystal/src/starfish/native/README.md) 主要记录 native/open62541 协议行约定和历史背景，适合在排查 runner 协议或本地构建时参考；它不是 `starfish` 模块总览，也不能替代本说明。

## 6. 阅读与扩展建议

如果要继续深入，建议按下面顺序读源码：

1. 先看 [`__main__.py`](/home/luosh/BlueCrystal/src/starfish/__main__.py) 了解入口和命令面。
2. 再看 [`runtime_registry.py`](/home/luosh/BlueCrystal/src/starfish/registry/runtime_registry.py) 了解协议分发和模式矩阵。
3. 之后按目标协议进入 `facade/`。
4. 如果是 IEC101 或 Modbus 编解码问题，再读 `protocols/`。
5. 如果是 native runner 问题，再读 `native/`。

对新增协议或新模式，当前代码的自然扩展点也是：

- `models/plan.py` 承接契约字段；
- `facade/` 新增协议 facade；
- `runtime_registry.py` 注册协议分发；
- `tools/` 复用统一探测接口；
- 若依赖外部二进制，再补 `native/runner_spec.py`、`runner_probe.py` 与对应 runner。
