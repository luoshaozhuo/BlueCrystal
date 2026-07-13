# Starfish 架构说明

## 架构定位

Starfish 采用 **Hexagonal Architecture（Ports and Adapters / 端口与适配器架构）**。

Starfish 的核心职责不是传统业务 CRUD，也不是通用配置文件解析，而是：

- 从外部数据源读取 simulator 定义。
- 创建并管理多个协议 simulator server。
- 对外提供统一的 init / start / stop / status / health 生命周期能力。
- 隔离 CLI、DB view、协议 driver/backend 等外部细节。

因此，Starfish 不再按教科书式 Clean Architecture 模板硬拆 use case、runtime context、registry 等层级。Clean Architecture 的依赖方向原则仍然保留，但模块组织以 Hexagonal Architecture 为主。

## 核心运行模型

Starfish 内部运行时使用 **Supervisor/Worker pattern** 组织对象关系：

```text
StarfishServerManager
  -> StarfishServer(connection_id=...)
  -> StarfishServer(connection_id=...)
  -> StarfishServer(connection_id=...)
```

- `StarfishServerManager` 是 supervisor，负责管理多个 server。
- `StarfishServer` 是 worker，代表一个具体 simulator server。
- 每个 server 自己持有 connection config、task config、point items 和实际 protocol server/driver 对象。
- 每个 server 暴露统一生命周期方法：`init()`、`start()`、`stop()`、`status()`。

Supervisor/Worker 是核心内部组织模式，不是 Starfish 的顶层架构名称。

## Hexagonal 边界

```text
Inbound adapters
  -> Core
      -> Outbound adapters
```

### Inbound Adapters

外部调用 Starfish 的入口：

- CLI：`python -m starfish run -id <connection_id>` / `python -m starfish run -a`
- Python 入口：`starfish.core.StarfishServerManager`

Inbound adapter 负责解析调用参数、处理用户可见错误，不承载协议逻辑。

### Core

Starfish 的核心对象：

- `StarfishServerManager`
- `StarfishServer` interface/base
- server definition / connection definition / task definition / point item definition
- 生命周期语义：`init` / `start` / `stop` / `status` / `health`

Core 不直接依赖具体数据库实现，不直接依赖 CLI，也不把协议实现细节暴露给调用方。

### Outbound Adapters

Starfish 依赖的外部能力：

- DB view loader：读取 `vw_connection_object_full`、`vw_task_full` 和对应 point item view。
- Protocol driver/backend：IEC104、后续 Modbus、OPC UA 等协议实现。
- Native runner / process backend：协议 server 的底层运行支撑。

Outbound adapter 可以依赖外部库、数据库、native 依赖和系统资源，但不能反向污染 core。

## 推荐主链路

目标链路如下：

```text
CLI / Python API
  -> connection_ids（-id 为单元素；-a 查询全部）
  -> build_server_manager_from_db(db_url, connection_ids)
  -> ConnectionDbViewLoader.load_protocols(...)
  -> ProtocolDefinitionLoaderRegistry[protocol].load(ids)
  -> ServerFactory.create(...)
  -> StarfishServerManager.servers[connection_id]
  -> StarfishServer.init()
  -> StarfishServer.start()
```

当前 registry 只注册 IEC104。后续新增协议时，应注册对应 definition loader 和
server adapter，不应修改 manager，也不应让 manager 变成协议分发表。

## 命名原则

- `Manager`：管理多个 server 生命周期的 supervisor。
- `Server`：一个 connection 对应的 simulator worker。
- `Definition`：从外部输入解析后的纯领域定义。
- `Loader`：从 DB view 等外部源读取 definition 的 adapter。
- `Factory`：根据 definition 创建 server 或 driver 的构造器。
- `Driver` / `Backend`：具体协议或 native server 实现。

不再把以下概念作为新架构核心：

- JSON file config path
- `StarfishRuntimeContext`
- endpoint `registry`
- 以 use case/workflow 为中心的启动链路

这些概念可以在迁移期短暂存在，但不应作为 Starfish 的长期架构目标。

## 非职责

Starfish 不负责：

- 更新 server 数据。该职责由 Seahorse 承担。
- 写入生产采集链路。
- 直接暴露协议 driver 给普通调用方。
- 将所有协议一次性重构到新架构。

Starfish 只负责 simulator runtime orchestration。
