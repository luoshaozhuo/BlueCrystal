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
- 每个 server 自己持有 connection config、point items 和实际 protocol server/driver 对象。
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
- server definition / connection definition / point item definition
- 生命周期语义：`init` / `start` / `stop` / `status` / `health`

Core 不直接依赖具体数据库实现，不直接依赖 CLI，也不把协议实现细节暴露给调用方。

### Outbound Adapters

Starfish 依赖的外部能力：

- DB view loader：读取 `vw_comm_connection`，以及 IEC104/ADS 对应的
  `vw_comm_*`、`vw_src_point_table`、`vw_src_*_point_item`。
- Protocol driver/backend：IEC104、ADS，以及后续协议实现。
- Protocol runtime：当前 IEC104 adapter 延迟加载 `iec104-python` 的 `c104`
  扩展；它通过 `iec104` optional extra 安装，不是全局强制依赖。

Outbound adapter 可以依赖外部库、数据库、native 依赖和系统资源，但不能反向污染 core。

协议分派信任数据库主数据：`vw_comm_connection.protocol` 直接投影
`meta_comm_protocol.protocol_identifier`，通用 loader 原样把该值交给 registry，
不进行 normalization，也不重复承担 NULL、空值、类型或格式校验。数据库 schema
与主数据负责字段有效性；composition 在 registry key 未注册或配置帧协议归属矛盾
时拒绝启动。IEC104/ADS loader 不做协议有效性检查；`protocol_role` 逐字映射为
`station_role`，非法角色由协议 backend 装配边界拒绝。这里描述的是职责归属，不建立
lowercase、hyphen、space 等格式变体测试矩阵。

Composition root 在每次 `build_server_manager_from_db()` 装配中只创建一个
SQLAlchemy Engine，并把它注入通用 connection loader 与各协议 definition loader；
CLI `-a` 的 connection 枚举也属于同一次 build。所有 rows 映射为规范化公共配置
DataFrame 后，无论装配成功或失败都会且只会 dispose Engine 一次；manager、
worker 与协议 backend 不持有数据库连接或 Engine，启动 runtime 不再访问数据库。

Engine 共享仅收敛连接池和资源所有权。各 loader 当前仍独立打开短只读事务，未实现
跨 loader 的单一 REPEATABLE READ snapshot；若未来有强一致启动快照需求，应单独
扩展数据库 adapter 的 Connection/transaction port。直接传 `db_url` 构造 loader
时，内部 Engine 由 loader 实例持有，不在 composition root 的确定性释放保证内；
需要明确生命周期的非 composition 调用方应注入并自行释放所拥有的 Engine。

## 推荐主链路

目标链路如下：

```text
CLI / Python API
  -> connection_ids（-id 为单元素；-a 查询全部）
  -> build_server_manager_from_db(db_url, connection_ids)
  -> ConnectionDbViewLoader.load(...) -> connection DataFrame
  -> ProtocolDefinitionLoaderRegistry[protocol].load(ids) -> point DataFrame
  -> pandas concat / merge / groupby / stable sort
  -> ServerFactory.create(single_connection_frame)
  -> StarfishServerManager.servers[connection_id]
  -> StarfishServer.init()
  -> StarfishServer.start()
```

当前 registry 注册 IEC104 与 ADS。后续新增协议时，应注册对应 definition loader 和
server adapter，不应修改 manager，也不应让 manager 变成协议分发表。

## IEC104 Adapter

IEC104 的装配链路只消费 Whale 执行 View：

```text
vw_comm_iec104_connection
  + vw_src_point_table
  + vw_src_iec104_point_item
    -> IEC104 point configuration DataFrame
    -> Iec104Server
    -> ServerDefinition（c104 创建边界）
    -> Iec104Backend
    -> c104.Server / c104.Client
```

Loader 不访问 Whale 基础表和调度视图；Source 点位能力直接保存在 Point 元数据中。
协议 point view 不含 `connection_id`，DB adapter 在 SQL 中以
`vw_src_point_table.point_table_id` JOIN 协议 point view，并从 PointTable 取得
connection 归属。connection 过滤与稳定顺序均下推到 SQL：未指定 IDs 时不生成
`WHERE`，指定 IDs 时使用 expanding bind 的 `IN`，并由 `ORDER BY` 确定顺序。
空 ID 列表在查询前拒绝；查询后 loaders 在配置映射之外只校验请求 ID 是否缺失，
不再用 pandas 二次过滤/排序，也不承担角色/协议归一化、协议有效性或 Point 覆盖校验。
协议 point view 也不提供 `measurement` 或 `business_semantic_name_en`；配置使用
`business_semantic_identifier` 作为稳定标识，并按
`business_semantic_name_zh -> business_semantic_identifier -> 协议地址/点 ID`
生成展示语义。

公共 schema 由 `core.config_frames.SERVER_CONFIG_COLUMNS` 定义，当前固定为 58 列，
采用“一行一个 point”结构。DB adapters 直接返回 DataFrame；composition 用 concat、merge、
groupby 和 stable sort 检查 connection/protocol 一对一关系、point 唯一性和输入
顺序；core manager 持有帧并按 connection 分组调用 factory。单元格不保存 definition、
point definition 或 metadata dict；离散域 `allowed_values` list 是原子领域值，
不属于运行时对象集合。IEC104/ADS server adapter 是唯一的 DataFrame 到 runtime
dataclass 边界，pandas 缺失值也只在这里恢复为 `None`。

pandas 可以进入 DB adapter、composition、core 配置/loader/factory ports、manager
与 protocol server 创建边界。协议 backend/native runtime、socket/thread/lock、
client session、notification handle 和运行时点位/地址 dict 不依赖 pandas，以保持
直接哈希查找与明确并发边界。当前依赖为 `pandas>=2.2.3,<3.0`，开发类型依赖为
`pandas-stubs>=2.2.3,<3.0`。

manager 保存完整配置帧的深拷贝，对外只返回深拷贝；它按 `connection_id` 分组创建
worker，并以 pandas `groupby/agg` 生成 `describe()` 摘要。composition 在进入 manager
前拒绝 connection 缺失、未请求 connection、protocol 不一致、一个 connection 多个
protocol，以及 `(connection_id, point_item_id)` 重复等关联基数错误。manager 与
factory 的公共接口消费 DataFrame，不表示 backend/native runtime 可以依赖 pandas。
`protocol_role=CONTROLLED_STATION` 创建受控站：

- 受控站注册 View 允许的 Point，使用包内 handler 响应站总召、一般累计量召唤
  和单点读，接收控制与时钟同步；Adapter 负责数据源更新、自发变化判断和背景
  调度，Point `report_ms` 负责周期传输。
- 外部标准 IEC104 client 发起站总召、一般累计量召唤、单点读、时钟同步及
  单点、双点、设点命令；Starfish 不额外提供协议操作旁路 API。

ADS 的装配链路为 `vw_comm_ads_connection + vw_src_point_table +
vw_src_ads_point_item -> ADS point configuration DataFrame -> AdsServer ->
ServerDefinition（AMS/TCP 创建边界） -> AdsTcpBackend`。backend
实现 AMS/TCP Source server，不依赖 Whale Python 包；当前稳定边界为状态读取、
symbol handle 读取、直接 INDEX 读取，以及 view 约束的 CYCLIC/ON_CHANGE device
notification。Source 普通写未被 view 授权并明确拒绝；client disconnect 与 server
stop 都会清理 symbol/notification handles。

ADS 的支持关闭契约为 `DELETE device notification -> client close -> session
cleanup -> server stop`。当前真实 pyads/AdsLib 定向验证只证明该顺序下资源可收敛
为 `client_count=0`、`notification_count=0`、`running=false`。活动 callback 未先
DELETE 时直接 teardown 可能导致 AdsLib 进程 SIGSEGV，因此不能宣称任意 teardown
顺序安全；调用方必须遵守上述顺序。

当前不装配组召、组累计量召唤、累计量冻结/复位以及 CP24Time2a Point；这些
能力不能仅凭 Type ID 枚举存在而启用。`c104` 在 IEC104 backend 首次装配时延迟
导入，依赖缺失或二进制不兼容被转换为稳定依赖错误。项目固定 CPython 3.13 与
`c104==2.2.1`；后者及其 lib60870-C 依赖为 GPLv3，包含该 optional extra 的
分发制品必须单独完成许可合规审查。

`c104` 的受控站总召、累计量召唤和单点读由内建 handler 处理。当前包没有逐
Point 的“参与站总召/组召”注册开关；站总召会覆盖已注册的相应监视方向 Point。
周期、自发、背景传输与命令接收能力直接由 Source Point 元数据控制。

当前 Starfish 不建立独立任务模型：`TaskDefinition`、`ServerDefinition.tasks`、
`execute_task()`、`task_count`、合成 task ID，以及 backend task
dispatcher/retry/deadline 链均不属于现行架构。配置帧、manager、worker 与 CLI
只围绕 connection、Point、capabilities 和生命周期协作；协议操作必须从标准 client
经 c104 handler/已注册 Point 进入，不能增加旁路任务 API。

背景传输使用可停止线程。若线程仍在完成一次同步发送而未能在停止期限内退出，
backend 不伪报正常停止：`stop()` 返回错误，health 标记
`shutdown_incomplete` 并保留线程计数，线程真实结束后状态才自然收敛为
`stopped`。

当前验证覆盖 View loader 的内存契约测试、backend 替身 API 行为、业务模块
import 隔离门禁和真实 c104 网络闭环。独立 integration test 使用纯 Starfish
View-shaped definitions，在未设置 `WHALE_DB_URL` 时运行，不依赖 PostgreSQL
样例数据；它在 BlueCrystal（CPython 3.13.14）和 `c104==2.2.1` native
wheel 环境启动受控站和外部原生 client，验证 TCP/STARTDT、站总召、一般累计量
召唤、单点读、自发上送以及单点/双点/设点命令。AST 门禁同时
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
- 直接暴露第三方 `c104.Point`；调用方只使用稳定的 Point 更新与状态接口。
- 将所有协议一次性重构到新架构。

Starfish 只负责 simulator runtime orchestration。
