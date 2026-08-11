# Starfish

Starfish 是协议数据源 simulator 的运行时管理模块。当前实现采用 Hexagonal
Architecture，并在 core 内使用 Supervisor/Worker 模式管理多个 connection。
依赖装配集中在 `starfish.composition`，不再保留单独的 API facade 层。

## CLI

数据库连接由 `WHALE_DB_URL` 提供：

```bash
python -m starfish run -id 1001
python -m starfish run -a
```

Starfish 的受支持运行环境为 CPython 3.13。IEC104 server 与真实验收 client、
ADS 真实验收 client 分别通过可选依赖安装：

```bash
pip install -e ".[dev,iec104]"
pip install -e ".[dev,ads]"
```

当前固定 `c104==2.2.1`，PyPI 提供 CPython 3.13 wheel。`c104` 和其
lib60870-C 依赖采用 GPLv3；它不是 BlueCrystal 核心依赖，分发包含该 extra 的
环境或镜像前必须完成 GPLv3 合规审查。

`-id` 按 `connection_id` 启动一个 simulator，`-a` 选择 DB view 中全部
connection，两者必须且只能选择一个。Starfish 会先读取每个 connection 的
protocol，再调用 IEC104 或 ADS loader；未注册协议会明确报错。

## 数据来源

Starfish 只从以下 Whale 执行视图构建 Source simulator：

- 通用分派：`vw_comm_connection`
- IEC104：`vw_comm_iec104_connection`、`vw_src_point_table`、
  `vw_src_iec104_point_item`
- ADS：`vw_comm_ads_connection`、`vw_src_point_table`、
  `vw_src_ads_point_item`

协议点位 view 不提供 `connection_id`。DB adapter 在 SQL 中以
`vw_src_point_table.point_table_id` JOIN 协议点位 view，取得 point 所属的
`connection_id`；不得绕过该关系访问基础表，也不得假设协议点位 view 直接携带
connection 归属。connection 过滤与稳定顺序均由 SQL 的 `WHERE` / `ORDER BY`
完成：`connection_ids is None` 时不生成 `WHERE`，非 `None` 时使用 SQLAlchemy
expanding bind 的 `IN`。空列表在查询前明确拒绝，请求 ID 不存在则在查询后报错。
当前协议点位 view 不提供 `measurement` 或 `business_semantic_name_en`；点标识使用
`business_semantic_identifier`，展示语义使用 `business_semantic_name_zh`，缺失时
才回退业务标识、协议地址或点 ID。

Starfish 的应用配置主链路是 pandas-first：三个 DB loaders 直接返回 DataFrame，
composition 使用 concat/merge/groupby/stable sort 完成协议批量分派、连接关系基数
检查、point 主键重复检查和输入顺序恢复，core manager 持有完整配置帧并按
connection group 交给 protocol factory。DataFrame 不会在 composition 后立即转回
dataclass 列表。

公共 schema 定义在 `starfish.core.config_frames.SERVER_CONFIG_COLUMNS`，当前固定为
58 列并采用“一行一个 point”的规范化结构。connection/endpoint、协议连接参数、
point 工程量与协议 point 参数均为扁平列，连接字段按 point 重复；单元格不保存
`ServerDefinition`、`PointItemDefinition` 或 metadata dict。
`allowed_values` 是例外的原子领域值，可保存离散值 list；它不是运行时对象集合。
当前协议不使用的列为 pandas 缺失值。IEC104/ADS worker 创建边界才把单 connection
DataFrame 转换为 backend 必需的 runtime dataclass，并把 pandas 缺失值恢复为
`None`。

pandas 是 Starfish 配置主链路的运行依赖，声明范围为
`pandas>=2.2.3,<3.0`；`pandas-stubs>=2.2.3,<3.0` 只用于开发期类型检查。当前验证
环境使用 pandas 2.3.3。DB loaders、core loader/factory ports、composition、manager
与 protocol server 创建边界可以依赖 pandas；protocol backends/native runtime、
协议点位/地址哈希索引以及 socket、thread、lock、client session、notification
handle 仍使用适合运行时查找和并发控制的原生结构。

`StarfishServerManager` 对传入的完整配置帧执行深拷贝，对外也只返回深拷贝；
`from_config_frame()` 按 `connection_id` 分组并把每组副本交给 factory，`describe()`
使用 pandas 聚合 connection、point 与 capability 摘要。composition 在 manager
创建前显式拒绝 connection 配置缺失、未请求 connection、protocol 不一致、一个
connection 归属多个 protocol，以及同 connection 下重复 `point_item_id` 等基数错误。

`vw_comm_connection.protocol` 直接来自
`meta_comm_protocol.protocol_identifier`，Starfish 将其原样作为 protocol registry
key，不执行 normalization。数据库 schema 与主数据负责保证该字段有效，Starfish
不重复检查 NULL、空值、类型或格式，也不维护格式变体兼容逻辑。应用层只负责两类
边界：composition registry 没有对应 key 或配置帧出现协议归属矛盾时拒绝启动；
IEC104/ADS loader 不做协议有效性检查，也不做 pandas 后过滤/排序、角色或协议
归一化、Point 覆盖校验。`protocol_role` 逐字映射为 `station_role`，非法角色由协议
backend 的装配边界拒绝。

每次 `build_server_manager_from_db()` 装配只创建一个 SQLAlchemy Engine，并注入
通用与协议 loaders；`-a` 的 connection 枚举也在同一次 build 中使用这个 Engine。
无论装配成功或异常，Engine 都会且只会 dispose 一次；配置帧完整物化后返回
的 manager 与协议 runtime 不再持有或访问数据库。当前各 loader 仍独立打开短只读
事务，共享 Engine 不等于共享事务，也不承诺跨 loader 的单一 REPEATABLE READ
snapshot。

直接用 `db_url` 构造 `ConnectionDbViewLoader`、`Iec104DbViewLoader` 或
`AdsDbViewLoader` 时，内部 Engine 由该 loader 实例持有，不属于 composition root
上述确定性释放保证。需要明确资源所有权的调用方应自行创建、注入并释放 Engine；
CLI/startup 路径应统一使用 composition root。

IEC104 adapter 只读取 connection 和 Source Point views，不读取其他调度视图。
adapter 延迟加载项目采用的 `c104` Python 扩展。受控站通过
`Iec104Server.update_point()` 更新模拟数据源；总召、读、时钟同步及控制命令由
外部 IEC104 client 按标准协议发起，Point 元数据直接控制周期、自发、背景传输和
命令接收能力。Starfish 不写 Whale 基础表，运行装配只依赖上述 view。

当前运行模型不包含 `TaskDefinition`、`ServerDefinition.tasks`、`execute_task()`、
`task_count` 或合成 task ID，也没有 backend task dispatcher/retry/deadline 链。
Point view 的能力字段直接映射为 Point metadata 和 server capabilities，不再生成
中间任务对象；CLI describe/run 输出也不包含 task 信息。

## IEC104 功能

| 角色 | 当前支持的 View operation |
|---|---|
| `CONTROLLED_STATION` | 响应站总召、一般累计量召唤和单点读；周期、自发、背景上送；接收单点、双点、设点命令和时钟同步 |
| `CONTROLLING_STATION` | 接收监视数据；发送站总召、一般累计量召唤、单点读、时钟同步、单点命令、双点命令和设点命令 |

受控站的站总召、一般累计量召唤和单点读响应由 `iec104-python` 内置
handler 完成；周期传输使用 Point 的 `report_ms`，自发传输由
`update_point()` 按死区和最小间隔触发，背景传输由 adapter 调度。
`point_state()` 返回当前值、质量、协议时标以及 `updated_at`、
`changed_at`、`last_sent_at` 等进程内状态。

当前 `c104` 没有逐 Point 的“参与站总召/组召”注册开关。受控站内建站总召会处理
已注册的相应监视方向 Point；Point 元数据中的总召能力用于公开能力描述，不能
误解为内建总召 handler 的逐点过滤条件。

当前边界：

- 不支持组召、组累计量召唤以及累计量冻结/复位。
- 不注册当前 `iec104-python` 不支持的 CP24Time2a Point。
- `c104` 是 IEC104 runtime 的延迟依赖；没有可导入且二进制兼容的扩展时，
  IEC104 connection 在装配阶段明确失败，但不阻断 Starfish 其他模块导入。
- 背景发送线程若未在停止期限内结束，`stop()` 报错，health 保持
  `shutdown_incomplete`，直到该线程真实退出。

BlueCrystal 验证环境使用 CPython 3.13.14 和 `c104==2.2.1` 的 CPython
3.13 native wheel。真实网络 integration test 使用纯 Starfish View-shaped
definitions，不依赖 PostgreSQL 样例数据，覆盖 TCP/STARTDT、站总召、一般累计量
召唤、单点读、自发上送及控制命令。View loader 由独立内存契约测试覆盖，真实
Whale view 闭环在设置 `WHALE_DB_URL` 时另行运行；AST 门禁确认
Starfish 生产代码和专属测试对其他业务 Python 包的 import 为零；该结论不
外推到真实数据库部署状态或组召等未实现功能。

详细边界见 [ARCHITECTURE.md](ARCHITECTURE.md)。

## ADS 功能

ADS adapter 在 view 的 TCP endpoint 上实现 AMS/TCP SERVER，校验目标 AMS Net
ID 与 AMS Port，并支持标准 client 的 `READ_STATE`、按 symbol handle 读取、
按 IndexGroup/IndexOffset 读取，以及由 view 声明周期的 `CYCLIC` 和 `ON_CHANGE`
device notification。Source 值可通过 `AdsServer.update_point()` 更新；未被 Source
view 授权的普通 ADS write 会返回 service-not-supported。`pyads` 仅作为真实 client
验收依赖，生产 server 不依赖 pyads 或测试模块。

ADS native client 的受支持关闭顺序是：先逐项 `DELETE device notification`，再
关闭 client/session，最后停止 Starfish server。当前真实 pyads/AdsLib 定向验证
覆盖该顺序，并确认停止后 `client_count=0`、`notification_count=0`。不得把该结论
外推为“任意 teardown 顺序均安全”：活动 callback 尚未 DELETE 时直接 teardown，
AdsLib 进程可能触发 SIGSEGV。
