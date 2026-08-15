# Ingest 模块决策

## 模块目标

`whale.ingest` 只保留接入侧职责，不承载数据库建模细节，也不负责运行时 OPC UA 采集。

当前阶段，ingest 只承担两件事：

1. 定义 ingest 输出的数据消息管道
2. 作为“配置初始化能力”的业务归属方，调用下层数据库能力

配置库初始化的具体实现已经收拢到 `whale.ingest.infrastructure`。

## 当前架构分层

围绕 OPC UA 配置初始化，当前采用如下结构：

```text
whale/
└── ingest/
    ├── infrastructure/
    │   ├── base.py
    │   ├── models.py
    │   ├── init_db.py
    │   ├── opcua_config_repository.py
    │   ├── opcua_config_import_service.py
    │   ├── opcua_config_query_service.py
    │   ├── opcua_config_api.py
    │   └── opcua_config_dto.py
    ├── message_pipeline.py
    └── INGEST_MODULE_DECISIONS.md
```

这个结构的意思是：

- `ingest`
  是接入侧能力边界
- `ingest.infrastructure`
  是接入侧配置存储的技术实现收纳点
- `base.py / models.py / init_db.py`
  分别负责 SQLAlchemy 基础设施、ORM 模型、数据库初始化入口
- `opcua_config_repository.py`
  负责简单数据访问和复杂查询仓储
- `opcua_config_import_service.py`
  负责配置文件解析与写入编排
- `opcua_config_query_service.py`
  负责复杂只读查询编排
- `opcua_config_api.py`
  负责对外暴露稳定读取入口
- `opcua_config_dto.py`
  负责在各层之间共享 DTO，避免 repository 反向依赖 service

## 表结构决策

数据库使用 SQLite，ORM 使用 SQLAlchemy。

表结构按 `OPCUANodeSet.xml` 的核心构成拆分，当前包括：

- `namespace_uris`
  对应 `NamespaceUris`
- `aliases`
  对应 `Aliases`
- `ua_object_types`
  对应 `UAObjectType`
  虽然你的重点提示里没有单列它，但模板文件中存在，保留它可以更完整兼容 NodeSet
- `ua_objects`
  对应 `UAObject`
- `ua_variables`
  对应 `UAVariable`
- `ua_references`
  对应各类节点之间的 `References`
- `opcua_client_connections`
  对应 `OPCUA_client_connections.yaml`

这里的核心设计原则是：

- NodeSet 的结构信息优先按“元素类型 + 关系表”拆开保存
- `UAObject`、`UAVariable` 与 `UAObjectType` 的关系，不用硬编码在业务逻辑里，而是通过 `ua_references` 保留原始拓扑
- `parent_node_id`、`type_definition` 等常用字段做适度冗余，方便后续查询和运行时装配

## 外层访问数据库的约束

这部分是当前版本最重要的边界约束。

### 写操作

写操作必须走 `service`。

当前落地方式是：

- `OpcUaConfigImportService` 负责读取 YAML / NodeSet
- service 调用 write repository 完成替换写入
- `whale.ingest.infrastructure.init_db` 只作为初始化入口，不直接承载写库细节

外层不要直接调用 repository 去做插入、更新、删除。

### 读操作

读操作分为两类：

- 简单查询：直接走 `read repository`
- 复杂查询：必须走 `query service`

为了减少 session 管理泄漏，对外还提供了 `api` 作为稳定入口：

- `OpcUaConfigReadApi`
  适合简单只读访问
- `OpcUaConfigQueryApi`
  适合聚合、联表、视图型查询

## 当前边界

### 属于 ingest 相关能力的内容

- 从 `OPCUANodeSet.xml` 和 `OPCUA_client_connections.yaml` 初始化 SQLite 配置数据库
- 支持默认模板路径
- 保留用户传入两个配置文件路径的能力
- 通过 ORM 管理表结构和写入
- 定义 ingest 输出消息管道抽象

### 不属于 ingest 的内容

- OPC UA 运行时 client 生命周期管理
- OPC UA 周期轮询采集
- 下游业务存储
- 聚合逻辑
- 指标计算
- 场景编排

其中 OPC UA server 仿真继续由 `tools/opcua_sim` 提供。

## 稳定使用方式

当前推荐调用方式：

1. 准备 SQLite 文件路径
2. 使用默认模板，或显式传入自定义的 YAML / NodeSet 路径
3. 执行 `python -m whale.ingest.infrastructure.init_db --db-path ...`
4. 读侧通过 `read repository / query service / api` 访问数据库

命令行示例：

```bash
python -m whale.ingest.infrastructure.init_db --db-path ./opcua_config.sqlite
```

如果需要指定输入文件：

```bash
python -m whale.ingest.infrastructure.init_db \
  --db-path ./opcua_config.sqlite \
  --connection-config-path ./custom/OPCUA_client_connections.yaml \
  --nodeset-path ./custom/OPCUANodeSet.xml
```

## 修改规则

后续修改时保持以下约束：

- 不要再把这些数据库相关实现拆散回 `whale/` 顶层目录
- 不要让 repository 承担业务决策
- 不要让 service 直接暴露底层 session 细节给外层
- 不要把复杂查询散落到调用方，统一收敛到 query service
- 不要把 OPC UA 运行时轮询逻辑重新放回当前这组初始化模块

## 增补：数据库建模与代码分层

下面内容是在保留上述原始决策基础上，结合当前代码实现补充的更新说明。

### 数据库建模补充

#### 1. ORM 与数据库形态

- 当前实现使用 SQLAlchemy 2.x 风格 ORM。
- 当前默认数据库仍然是 SQLite 文件库，默认文件位置为 `src/whale/ingest/whale.db`。
- 数据库连接参数不再写死在建库脚本中，而是统一由 `src/whale/ingest/config.py` 提供。

#### 2. 表结构继续以 OPC UA 配置文件为蓝本

数据库表仍然由两个输入源驱动建模：

- `OPCUANodeSet.xml`
- `OPCUA_client_connections.yaml`

结合当前落地代码，表名已经统一明确为：

- `opcua_nodeset_namespace`
- `opcua_nodeset_aliases`
- `opcua_nodeset_object_types`
- `opcua_nodeset_objects`
- `opcua_nodeset_variables`
- `opcua_nodeset_references`
- `opcua_client_connections`

这意味着表名层面已经从早期的通用命名，进一步收敛为显式的 `opcua_` 前缀命名。

#### 3. 每张表统一使用自增主键 `id`

- 当前 ORM 模型中，每张表都带有自增主键 `id`。
- `node_id`、`alias`、`name` 等业务字段继续保留，并用唯一约束保证业务唯一性。

这样做是为了：

- 更符合 SQLAlchemy ORM 的常规映射方式
- 便于后续扩展关系映射和迁移
- 让数据库结构与 ORM 模型之间保持更稳定的双向对应关系

#### 4. 关系信息保留原始拓扑

- `UAObject`、`UAVariable`、`UAObjectType` 之间的联系，不完全依赖硬编码字段表达。
- 节点间引用关系继续保存在 `opcua_nodeset_references` 中。
- 同时保留 `parent_node_id`、`type_definition` 等高频字段，作为对读取和组装逻辑友好的适度冗余。

#### 5. 建库与模型恢复需要双向兼容

- ORM 模型应能正向创建数据库。
- 数据库结构也应能稳定映射回当前 ORM 模型。
- 因此当前更强调表结构清晰、主键明确、约束显式，而不是依赖隐式规则。

### 代码分层补充

#### 1. 数据库相关代码继续收拢在 ingest 内部

- 数据库能力不再散落到 `whale/` 顶层其它位置。
- 当前实际代码已经收拢到 `whale.ingest.framework.db` 下。

当前已落地的最小结构大致为：

```text
whale/ingest/
├── config.py
├── message_pipeline.py
└── framework/
    └── db/
        ├── base.py
        ├── session.py
        ├── init_db.py
        └── models/
            └── opcua_config_models.py
```

这里表达的是当前实现状态，并不否定原文中关于 repository / service / api 分层的方向。

#### 2. `framework/db` 只负责数据库技术实现

- `base.py`
  负责 SQLAlchemy `Base`
- `session.py`
  负责 engine、session factory、数据库 URL 拼装
- `models/*`
  负责 ORM 表模型
- `init_db.py`
  负责建表入口

这一层的职责仍然是数据库技术实现，而不是业务编排层。

#### 3. 写操作必须走 service 的约束保持不变

虽然当前仓库里这部分还没有完全补齐，但外层访问规则不变：

- 写操作必须走 service
- repository 只负责数据访问
- service 负责解析输入、调用 repository、控制事务边界

#### 4. 读操作继续区分简单查询与复杂查询

- 简单查询可以直接走 repository
- 复杂查询应通过 query service 收敛

这条约束依然有效，后续补齐 repository / query service 时应保持这一边界。

#### 5. ingest 的职责边界不变

`whale.ingest` 仍然只承担接入侧职责：

- 发现 server 并获取配置
- 周期性从 server 获取数据
- 将数据发送到消息管道

当前数据库模块承担的是配置初始化与配置读取支撑能力，不是通用业务数据库层。

# 杂

ORM对象要写“comment=”，特比对于名义变量要加入CheckConstraint，以及对每个选项进行说明

当前已经落到 ORM 约束中的名义变量，可取值说明如下：

- `source_runtime_config.protocol`
  当前只允许：`opcua`
- `source_runtime_config.acquisition_mode`
  允许值：
  `ONCE`：执行一次后不再重复调度
  `POLLING`：按 `interval_ms` 周期触发一次性读取
  `SUBSCRIPTION`：进入订阅模式的启动分支，后续由订阅实现接管
- `opcua_client_connections.security_policy`
  允许值：
  `None`：不启用安全策略
  `Basic128Rsa15`：旧版 RSA15 策略
  `Basic256`：旧版 Basic256 策略
  `Basic256Sha256`：更常见的 SHA256 策略
  `Aes128_Sha256_RsaOaep`：较新的 AES128 + SHA256 + RSA-OAEP 策略
  `Aes256_Sha256_RsaPss`：较新的 AES256 + SHA256 + RSA-PSS 策略
- `opcua_client_connections.security_mode`
  允许值：
  `None`：不签名、不加密
  `Sign`：只签名，不加密
  `SignAndEncrypt`：同时签名并加密

## 增补：调度、执行计划与并行运行

这一节记录 ingest 从“单次执行链路”继续演进到“可调度、可并行、多模式采集”时的优化结论。

### 当前主要问题

- 调度层如果只拿 `source_id`，下游还要再次回查配置，链路重复读取配置，职责边界不清。
- scheduler 如果同时负责读配置、拼装计划、判断 mode、直接执行采集，会膨胀成混合调度器。
- `ONCE`、`POLLING`、`SUBSCRIPTION` 的生命周期不同，不适合都塞进同一个串行主循环里硬编码处理。
- 采集场景本质以网络 I/O 为主，若按“一设备一线程”扩张到上百设备，线程数会失控。

### 优化结论

后续 ingest 运行链路按下面的职责划分推进：

1. 先准备执行计划，再调度执行，不再让执行链路二次读配置。
2. scheduler 只负责分发与生命周期控制，不负责配置拼装和采集细节。
3. use case 只负责“一次执行闭环”，不负责 mode 判断，不负责调度循环。
4. role 只保留动作职责：
   - `AcquisitionRole` 负责采集
   - `StateUpdateRole` 负责状态落库
5. 并行运行优先按“有限执行单元”设计，不走“一设备一线程”。

### 推荐分层

推荐主链路如下：

```text
PrepareSourceExecutionPlanUseCase
-> list[SourceExecutionPlan]

SourceScheduler
-> choose runner by acquisition_mode
-> runner.start(plan)

Runner
-> MaintainSourceStateUseCase.execute(plan)

UseCase
-> AcquisitionRole
-> StateUpdateRole
```

各层职责定义如下：

- `PrepareSourceExecutionPlanUseCase`
  负责读取配置、聚合运行时调度配置与连接配置、生成完整执行计划。
- `SourceScheduler`
  负责获取计划、按 `ONCE / POLLING / SUBSCRIPTION` 分发、维护最小调度状态。
- `Runner`
  负责某一种 mode 的执行生命周期。
- `MaintainSourceStateUseCase`
  负责单个 source 的一次采集与落库闭环。
- `Role`
  负责具体动作，不负责调度，不负责配置读取。

### 执行计划建模原则

执行计划不应只包含 `source_id`。至少应显式区分两类静态信息：

- `SourceScheduleSpec`
  包含 `acquisition_mode`、`interval_ms` 等调度信息。
- `SourceConnectionSpec`
  包含 `protocol`、`endpoint`、`security_policy`、`security_mode` 等采集连接信息。

必要时再组合为 `SourceExecutionPlan`，供 scheduler 和执行 use case 消费。

这样做的目标是：

- 配置只读一次
- 调度输入完整
- 执行链路不再二次查配置
- 后续扩展不同协议或不同点位选择时，不必把细节塞回 scheduler

### 并行运行决策

Python 运行时存在 GIL，但当前采集任务主要是网络 I/O，不应把 GIL 视为并行采集的主要阻碍。

当前推荐策略如下：

- `ONCE`
  适合投递到有限 worker 池执行。
- `POLLING`
  适合由 scheduler 管理触发节奏，再交给有限 worker 池执行单次读取。
- `SUBSCRIPTION`
  不建议简单建成“一设备一线程”，更适合单独的连接管理器或事件驱动实现。

明确不推荐：

- 一台设备长期绑定一个线程
- scheduler 自己串行执行所有采集任务
- 在 scheduler 中直接编写协议采集细节

### 当前阶段的演进顺序

按渐进式开发原则，后续实现顺序建议如下：

1. 先打通“准备执行计划 -> scheduler 分发 -> 单次执行 use case”主链路。
2. 再把 `ONCE` 跑通，验证配置、采集、落库闭环。
3. 然后为 `POLLING` 引入有限并发执行单元，而不是一设备一线程。
4. 最后单独设计 `SUBSCRIPTION` 的 runner 与连接管理模型。

这个顺序的目标是先建立稳定边界，再逐步扩展并行与长生命周期任务能力，避免在起步阶段把调度、执行、连接管理和协议细节揉成一个类。
