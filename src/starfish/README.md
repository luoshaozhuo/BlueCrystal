# Starfish 源码阅读指南

`starfish` 的定位现在很简单：

> 读取 `starfish_server_plan.json`（历史文件名），装配成统一的 `StarfishServerManager`，然后由 CLI 或脚本驱动它完成 `start/stop/status/health/read/write`。

## 正式入口

- 正式 API 入口是 [`api/server_manager_api.py`](/home/luosh/BlueCrystal/src/starfish/api/server_manager_api.py)
- 推荐从 `open_manager(...)` 拿到 `StarfishServerManager`
- 普通调用方不应该直接依赖单个协议 driver

`StarfishServerManager` 当前提供的高层操作包括：

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
├── adapters/
├── domain/
├── infrastructure/
```

各目录边界如下：

- `api/`: 对外统一入口，暴露 `StarfishServerManager` 和装配 API
- `application/`: 仅包含 use_cases / ports / runtime，不包含具体 I/O 实现
- `domain/`: 稳定契约、driver entry 值对象与协议 codec/state machine/frame
- `adapters/`: config loader、driver factory 和各协议 backend
- `infrastructure/`: native runner、process runtime、硬件或系统级支撑

## 主链路

主链路现在是：

```text
Server Config JSON
  -> api
  -> application
  -> infrastructure.file_loaders.server_config_json_loader
  -> application.use_cases.workflows.bootstrap
  -> application.runtime.context
  -> adapters.drivers.factory
  -> StarfishServerManager
  -> CLI / 外部诊断调用方
```

如果你要快速看懂整个模块，推荐按这个顺序读：

1. [`__main__.py`](/home/luosh/BlueCrystal/src/starfish/__main__.py)
2. [`api/server_manager_api.py`](/home/luosh/BlueCrystal/src/starfish/api/server_manager_api.py)
3. [`application/use_cases/workflows/bootstrap.py`](/home/luosh/BlueCrystal/src/starfish/application/use_cases/workflows/bootstrap.py)
4. [`domain/server_config.py`](/home/luosh/BlueCrystal/src/starfish/domain/server_config.py)
5. [`application/runtime/context.py`](/home/luosh/BlueCrystal/src/starfish/application/runtime/context.py)
6. [`infrastructure/file_loaders/server_config_json_loader.py`](/home/luosh/BlueCrystal/src/starfish/infrastructure/file_loaders/server_config_json_loader.py)
7. 一个代表性协议实现，比如 [`infrastructure/drivers/protocol/http/http_rest_server_backend.py`](/home/luosh/BlueCrystal/src/starfish/infrastructure/drivers/protocol/http/http_rest_server_backend.py)

## Manager 理解方式

理解 `starfish` 时，不要先从单个协议类开始，而要先抓住两层抽象：

- `StarfishServerManager`: 给上层调用方的统一 server 管理对象
- 协议 driver: manager 内部针对具体 endpoint 装配出来的协议执行单元

也就是说：

- 外部用户优先面向 `StarfishServerManager`
- 内部装配通过 `application.use_cases.workflows.bootstrap`、`application.runtime.context` 和 `adapters.drivers.factory` 绑定具体 backend

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

1. `StarfishServerManager` 是唯一正式高层入口。
2. `application` 负责编排，`adapters` 负责真实 I/O 和 driver 实现。
3. `registry.py` 只做 endpoint 绑定编排，协议选择在 `adapters.drivers.factory`。
4. 协议能力必须结合 `mode` 理解。
5. 先看主链路，再看单协议细节，读源码效率最高。
