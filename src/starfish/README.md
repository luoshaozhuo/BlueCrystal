# Starfish 源码阅读指南

`starfish` 的定位现在很简单：

> 读取 `starfish_server_plan.json`，装配成统一的 `StarfishRuntime` 运行时对象，然后由 CLI 或脚本驱动它完成 `start/stop/status/health/read/write`。

## 正式入口

- 正式 API 入口是 [`api/runtime_api.py`](/home/luosh/BlueCrystal/src/starfish/api/runtime_api.py)
- 推荐从 `StarfishRuntimeApi.open_runtime(...)` 拿到 `StarfishRuntime`
- 普通调用方不应该直接依赖单个协议 driver

`StarfishRuntime` 当前提供的高层操作包括：

- `describe()`
- `start()`
- `stop()`
- `status()`
- `health()`
- `read()`
- `write()`

## 当前结构

```text
src/starfish/
├── __init__.py
├── __main__.py
├── README.md
├── api/
├── application/
├── domain/
├── drivers/
├── native/
├── protocols/
```

各目录边界如下：

- `api/`: 对外统一入口，暴露 `StarfishRuntime` 和装配 API
- `application/`: usecase / orchestration，负责 plan 加载和运行时装配流程
- `domain/`: 稳定契约与运行时抽象，不做文件 I/O 和协议分发
- `drivers/`: 真实实现层，包含 plan loader、runtime registry 和各协议驱动
- `native/`: native runner 的探测、路径和进程支撑
- `protocols/`: 协议编解码与协议内部结构

已经移出 `starfish` 的能力：

- `probe / profile / capacity` 现在位于 `whale.ingest.diagnostics/`
- 原因是它们本质上是“消费 runtime 的诊断工具”，不是 `starfish` runtime 核心

## 主链路

主链路现在是：

```text
ServerPlan JSON
  -> api
  -> application
  -> drivers.server_plan_loader
  -> drivers.runtime_registry
  -> StarfishRuntime
  -> CLI / 外部诊断调用方
```

如果你要快速看懂整个模块，推荐按这个顺序读：

1. [`__main__.py`](/home/luosh/BlueCrystal/src/starfish/__main__.py)
2. [`api/runtime_api.py`](/home/luosh/BlueCrystal/src/starfish/api/runtime_api.py)
3. [`application/runtime_service.py`](/home/luosh/BlueCrystal/src/starfish/application/runtime_service.py)
4. [`domain/server_plan.py`](/home/luosh/BlueCrystal/src/starfish/domain/server_plan.py)
5. [`drivers/server_plan_loader.py`](/home/luosh/BlueCrystal/src/starfish/drivers/server_plan_loader.py)
6. [`drivers/runtime_registry.py`](/home/luosh/BlueCrystal/src/starfish/drivers/runtime_registry.py)
7. 一个代表性协议实现，比如 [`drivers/http_rest_facade.py`](/home/luosh/BlueCrystal/src/starfish/drivers/http_rest_facade.py)

## 运行时理解方式

理解 `starfish` 时，不要先从单个协议类开始，而要先抓住两层抽象：

- `StarfishRuntime`: 给上层调用方的统一运行时对象
- 协议 driver: 运行时内部针对具体 endpoint 装配出来的协议执行单元

也就是说：

- 外部用户优先面向 `StarfishRuntime`
- 内部装配才面向 `drivers/*_facade.py`

## mode 比协议名更重要

很多行为由 `mode` 决定，而不只是由协议名决定。

常见 mode：

- `real`: 真实可运行的 server 或 native runner
- `mqtt-lightweight`: 轻量协议外观，不是完整实现
- `rtu-lightweight`: 本地轻量串口路径
- `codec-skeleton` / `codec-enhanced` / `codec-enhanced-plus`: 编解码能力存在，但不是完整 server
- `unavailable`: 代码路径存在，但 native 依赖或运行条件不满足
- `report-lightweight`: 轻量 report 壳，不等同完整 report server
- `codebase-pending`: 实现占位但未完成
- `environment-pending`: 主要受运行环境限制
- `stub`: 未实现协议时的内存回退

## 不负责什么

`starfish` 不负责：

- 不进入 `whale.ingest` 等生产采集链路
- 不再承载 `probe/profile/capacity` 这类外部诊断工具
- 不直接 import `seahorse`
- 不把模拟验证写成真实现场验证
- 不承诺所有协议都达到完整工业实现

## 现在最应该记住的 5 件事

1. `StarfishRuntime` 是唯一正式高层入口。
2. `application` 负责编排，`drivers` 负责真实实现。
3. `runtime_registry.py` 是协议装配中心。
4. 协议能力必须结合 `mode` 理解。
5. 先看主链路，再看单协议细节，读源码效率最高。
