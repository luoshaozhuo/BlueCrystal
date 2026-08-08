# Starfish 架构说明

## 架构定位

Starfish 采用 **Hexagonal Architecture（Ports and Adapters / 端口与适配器架构）**。

Starfish 的核心职责不是传统业务 CRUD，也不是通用配置文件解析，而是：

- 从外部数据源读取 simulator 定义。
- 创建并管理多个协议 simulator connection（可为 server 或 client 角色）。
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
- `StarfishServer` 是 worker，代表一个具体 simulator connection；名称为兼容
  现有 core 接口而保留。
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

- DB view loader：读取 `vw_connection_object_full`、`vw_task_full`、
  `vw_task_point_item` 和对应 point item view。
- Protocol driver/backend：IEC104、后续 Modbus、OPC UA 等协议实现。
- Protocol runtime：当前 IEC104 adapter 延迟加载 `iec104-python` 的 `c104`
  扩展；它通过 `iec104` optional extra 安装，不是全局强制依赖。

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

## IEC104 Adapter

IEC104 的装配链路只消费 Whale 执行 View：

```text
vw_connection_object_full
  + vw_task_full
  + vw_task_point_item
  + connection 登记的 vw_iec104_point_item
    -> ServerDefinition
    -> Iec104Server
    -> Iec104Backend
    -> c104.Server / c104.Client
```

Loader 不访问 Whale 基础表，不使用旧版任务点位聚合 JSON，也不根据命名规律
推导 Point View。`station_role` 决定创建受控站还是控制站：

- 受控站注册 View 允许的 Point，使用包内 handler 响应站总召、一般累计量召唤
  和单点读，接收控制与时钟同步；Adapter 负责数据源更新、自发变化判断和背景
  调度，Point `report_ms` 负责周期传输。
- 控制站注册接收/命令 Point，通过 task API 接收监视数据，并主动执行站总召、
  一般累计量召唤、单点读、时钟同步及单点、双点、设点命令。

当前不装配组召、组累计量召唤、累计量冻结/复位以及 CP24Time2a Point；这些
能力不能仅凭 Type ID 枚举存在而启用。`c104` 在 IEC104 backend 首次装配时延迟
导入，依赖缺失或二进制不兼容被转换为稳定依赖错误。项目固定 CPython 3.13 与
`c104==2.2.1`；后者及其 lib60870-C 依赖为 GPLv3，包含该 optional extra 的
分发制品必须单独完成许可合规审查。

`c104` 的受控站总召、累计量召唤和单点读由内建 handler 处理。View task 用于
声明并校验 connection 能力，但当前包没有逐 Point 的“参与站总召/组召”注册
开关；站总召会覆盖已注册的相应监视方向 Point，不能把 task 成员关系解释为
内建 handler 的逐点筛选条件。

主动 task 使用 View 中的 timeout、retry 和链路参数。Adapter 可在连接等待、
重试退避和调用边界响应 `stop()`；已经进入同步 `c104` 方法的调用无法由
Adapter 精确取消，只能在返回后判定 deadline 超限。控制和时钟命令不自动重试，
避免确认不确定时重复执行。

背景任务使用可停止线程。若线程仍在完成一次同步发送而未能在停止期限内退出，
backend 不伪报正常停止：`stop()` 返回错误，health 标记
`shutdown_incomplete` 并保留线程计数，线程真实结束后状态才自然收敛为
`stopped`。

当前验证覆盖 View loader 的内存契约测试、backend 替身 API 行为、业务模块
import 隔离门禁和真实 c104 网络闭环。独立 integration test 使用纯 Starfish
View-shaped definitions，在未设置 `WHALE_DB_URL` 时运行，不依赖 PostgreSQL
样例数据；它在 BlueCrystal（CPython 3.13.14）和 `c104==2.2.1` native
wheel 环境启动受控站和控制站，验证 TCP/STARTDT、站总召、一般累计量召唤、
单点读、周期/自发/背景上送、时钟同步以及单点/双点/设点命令。AST 门禁同时
保证 Starfish 源码与专属测试不 import Whale、Orca 等业务 Python 包。缺少
`c104` 的环境只能记为 NOT_RUN；当前证据不代表现场 PostgreSQL View 已部署
或验证。

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

- 持久化 simulator 运行值；IEC104 受控站值由调用方经 `update_point` 注入，
  adapter 只保存当前进程内状态。
- 写入生产采集链路。
- 直接暴露第三方 `c104.Point`；调用方只使用稳定的 point/task 接口。
- 将所有协议一次性重构到新架构。

Starfish 只负责 simulator runtime orchestration。
