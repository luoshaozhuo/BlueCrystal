# BlueCrystal 数据模型正式版 v1.5.6

## 0. Navicat 执行约束

PostgreSQL 不支持在普通 SQL 中切换数据库；`\connect`、`\set`、`\gexec` 仅属于 `psql` 客户端命令，不能由 Navicat SQL 编辑器执行。

因此正式初始化包拆成四个阶段：

1. 连接维护库 `postgres`，执行 `01_bluecrystal_create_database_v1_5_6.sql`。
2. 在 Navicat 中新建或刷新 `bluecrystal` 连接，连接到数据库 `bluecrystal`。
3. 依次执行 `02_bluecrystal_schema_ddl_v1_5_6.sql`、`03_bluecrystal_basic_data_v1_5_6.sql`。
4. 仅在开发、测试、演示环境执行 `04_bluecrystal_site_sample_v1_5_6.sql`。

`01` 文件只执行一次。由于 PostgreSQL 没有 `CREATE DATABASE IF NOT EXISTS`，数据库已经存在时不得重复执行。

## 1. 正式部署标识

| 项目 | 正式值 |
|---|---|
| PostgreSQL 数据库名 | `bluecrystal` |
| PostgreSQL schema 名 | `whale` |
| 建库脚本 | `01_bluecrystal_create_database_v1_5_6.sql` |
| Schema DDL | `02_bluecrystal_schema_ddl_v1_5_6.sql` |
| 公共基础数据 | `03_bluecrystal_basic_data_v1_5_6.sql` |
| 模拟现场样例数据 | `04_bluecrystal_site_sample_v1_5_6.sql` |

推荐执行顺序：

```bash
psql -U <database_admin> -d postgres -f 01_bluecrystal_create_database_v1_5_6.sql
psql -U <database_user> -d bluecrystal -f 02_bluecrystal_schema_ddl_v1_5_6.sql
psql -U <database_user> -d bluecrystal -f 03_bluecrystal_basic_data_v1_5_6.sql
psql -U <database_user> -d bluecrystal -f 04_bluecrystal_site_sample_v1_5_6.sql
```

依赖关系：

```text
DDL
  ↓
basic_data
  ↓
site_sample
```

## 2. 本版变更

1. 修复 IEC101、IEC104 样例点位为空：原生成条件错误引用不存在的 `ext_dispatch_%` 语义前缀，现显式使用 `ext_grid_001`～`ext_grid_005` 并网点有功、无功、电压、电流、频率语义。
2. EMS、传统 RTU、调度主站及 AGC/AVC 控制器的样例点位统一引用已存在的并网点标准工程语义，避免条件插入静默产生 0 行。
3. 保留协议点位非空强制校验；IEC101、IEC104 若仍未生成点位，脚本继续抛错并回滚。

1. 数据库正式命名为 `bluecrystal`，schema 正式命名为 `whale`。
2. 原单一 sample DML 拆分为公共基础数据和模拟现场样例数据。
3. 公共基础数据只表达“平台认识什么”，不得依赖组织、场站、资产、员工、连接或任务实例。
4. 模拟现场样例数据表达“虚拟场站具体有什么、如何连接、如何运行”。
5. `ref_code_id()`、`asset_id()`、`model_id()`、`connection_id()`、`semantic_id()`、拓扑元素查找函数和协议数据类型查找函数由 DML 迁入 DDL。
6. DDL、基础数据和现场样例统一使用 `bluecrystal.whale`。
7. 保留 v1.4.10 已确定的测量语义、协议点位和访问能力边界，不改变业务表结构。

## 2.1 公共基础数据边界

`03_bluecrystal_basic_data_v1_5_6.sql` 包含：

1. 全部平台参考代码 `ref_code`；
2. 标准测量语义 `cfg_measurement_semantic`；
3. 协议物理表注册 `cfg_protocol_table_registry`；
4. 标准权限、标准角色和角色权限模板；
5. 协议操作定义 `cfg_protocol_operation_def`；
6. 协议操作与任务类型映射 `cfg_protocol_task_type_mapping`。

该文件只能依赖 DDL，可以独立用于正式项目初始化。

## 2.2 模拟现场样例数据边界

`04_bluecrystal_site_sample_v1_5_6.sql` 包含：

1. 模拟组织、场站和班组；
2. 模拟厂商、型号和资产实例；
3. 模拟员工及角色分配；
4. 协议连接、连接参数、点表和点位；
5. 电气拓扑、通信拓扑和地理位置；
6. 任务点表、任务配置、参数和少量运行记录；
7. 连接状态事件和资产检修事件。

该文件必须在公共基础数据之后执行，不用于生产项目的公共初始化。

## 3. 数据边界

`cfg_measurement_semantic` 是主数据，不是元数据。它表达采集量、状态量、控制量、发布量的长期业务语义。

本表应满足：

| 字段 | 要求 |
|---|---|
| `measurement_identifier` | 稳定业务标识，不使用协议前缀区分同一语义。 |
| `name_zh` | 真实中文工程名，不使用“标准语义001”这类占位名称。 |
| `name_en` | 真实英文工程名。 |
| `logical_node_code` | 风电标准语义可填 WPPD、WTUR、WROT、WGEN 等；非标准扩展语义可为空。 |
| `data_object_name` | 风电语义使用贴近 IEC/GB 信息模型的数据对象名；扩展语义使用工程缩写。 |
| `cdc_code` | 对 IEC 61850 类语义有意义时填写，例如 SPS、MV、INS、APC。 |
| `physical_quantity_category_ref_id` | 必须与业务语义匹配。 |
| `standard_unit_ref_id` | 必须与业务语义匹配。 |
| `standard_data_type_ref_id` | 必须与业务语义匹配。 |

## 4. 协议点位与语义的关系

所有 `cfg_xxx_point_item` 必须引用 `cfg_measurement_semantic`。

协议点位表只描述：

1. 变量在协议中如何定位；
2. 原始值如何解析；
3. 工程值如何换算；
4. 值域如何校验。

协议点位表不再保存统一的 `access_mode`、`point_access_mode_ref_id`、`platform_access_mode_ref_id`。

访问能力由协议自身字段、`task_type`、任务参数、连接角色、驱动 facade 和安全治理策略推导。

## 5. 协议是否具有原生 access mode

| protocol | 是否有原生 access mode | 说明 |
|---|---:|---|
| MODBUS | 否 | MODBUS 协议本身不定义点级 access mode；可读/可写由 function code、register area、设备实现能力和任务类型共同决定。 |
| ADS | 弱 | ADS 变量通常按 symbol 或 index_group/index_offset 访问，是否可写更多来自 PLC 变量声明、运行时权限或工程约定。 |
| OPCUA | 是 | OPC UA 原生提供 `AccessLevel`、`UserAccessLevel` 等属性，可表达 CurrentRead、CurrentWrite 等能力。 |
| IEC101 | 否 | IEC101 不使用统一 access mode；遥测、遥信、遥控、设点等能力由 `type_id`、站端角色和任务类型体现。 |
| IEC104 | 否 | IEC104 不使用统一 access mode；遥测、遥信、遥控、设点、总召响应等能力由 `type_id`、站端角色和任务类型体现。 |
| IEC61850_MMS | 是 | IEC 61850 MMS 可由 `functional_constraint`、CDC、control model、服务能力共同表达读、写、控制、定值等能力。 |
| IEC61850_GOOSE | 否 | GOOSE 是发布 / 订阅数据集报文，不定义读写型 access mode。 |
| IEC61850_SV | 否 | SV 是采样值发布 / 订阅报文，不定义读写型 access mode。 |
| MQTT | 否 | MQTT topic 不定义变量读写能力；发布 / 订阅能力由连接角色、topic 权限和任务类型决定。 |
| HTTP_REST | 否 | HTTP 本身不定义点级 access mode；能力由 `http_method`、OpenAPI/接口契约和任务类型决定。 |

## 6. 各协议特殊 var 类型标识

| protocol | 协议特殊 var 类型标识 | 说明 |
|---|---|---|
| MODBUS | `function_code` / `register_area` | 区分 coil、discrete input、holding register、input register 以及写 coil/register，是驱动方法分派的核心字段。 |
| MODBUS | `data_type` | MODBUS 原生只有 bit/register，工程系统必须补充 INT16、UINT16、INT32、FLOAT32 等解释类型。 |
| MODBUS | `byte_order` / `word_order` | 多寄存器变量必须说明字节序和字序。 |
| ADS | `symbol_name` 或 `index_group` + `index_offset` | ADS 变量定位标识；常用 PLC symbol 访问，也可用 index group/offset 访问。 |
| ADS | `plc_datatype` | TwinCAT / PLC 变量类型，例如 BOOL、INT、DINT、REAL、LREAL、STRING、ARRAY。 |
| OPCUA | `node_id` | OPC UA 变量核心定位标识。 |
| OPCUA | `attribute_id` | 标识读取 Value、DataType、AccessLevel 等属性；采集值通常读取 Value。 |
| OPCUA | `data_type` / `variant_type` | OPC UA Variant 数据类型，例如 Boolean、Int16、Float、Double、String、DateTime。 |
| OPCUA | `access_level` / `user_access_level` | OPC UA 原生访问能力；仅 OPC UA 类协议保留该类原生字段。 |
| IEC101 | `type_id` | ASDU 类型标识，是 IEC101 变量类别核心字段。 |
| IEC101 | `information_object_address` | IOA，信息对象地址，用于变量定位。 |
| IEC101 | `quality_descriptor` | 质量描述符；遥测、遥信常带质量位。 |
| IEC101 | `time_tag_type` | 表示是否带 CP24Time2a / CP56Time2a 等时标。 |
| IEC104 | `type_id` | ASDU 类型标识，是 IEC104 变量类别核心字段。 |
| IEC104 | `information_object_address` | IOA，信息对象地址，用于变量定位。 |
| IEC104 | `quality_descriptor` | 质量描述符；遥测、遥信常带质量位。 |
| IEC104 | `time_tag_type` | 表示是否带 CP24Time2a / CP56Time2a 等时标。 |
| IEC61850_MMS | `object_reference` | IEC 61850 对象引用，例如 LD/LN.DO.DA。 |
| IEC61850_MMS | `functional_constraint` | FC，例如 ST、MX、CO、SP、CF、DC，是 MMS 访问语义的关键字段。 |
| IEC61850_MMS | `cdc` | Common Data Class，例如 SPS、DPS、MV、CMV、INC、APC、SPC。 |
| IEC61850_MMS | `btype` | Basic Type，例如 BOOLEAN、INT32、FLOAT32、Enum、Struct。 |
| IEC61850_MMS | `control_model` | 控制模型，例如 direct-with-normal-security、select-before-operate 等。 |
| IEC61850_GOOSE | `go_cb_ref` | GOOSE control block reference。 |
| IEC61850_GOOSE | `dataset_ref` | GOOSE 数据集引用。 |
| IEC61850_GOOSE | `dataset_member_index` | 数据集成员序号，用于定位变量。 |
| IEC61850_GOOSE | `cdc` / `btype` | GOOSE 传输数据集成员，成员仍来自 IEC 61850 数据模型。 |
| IEC61850_SV | `sv_id` / `smp_id` | 采样值流标识。 |
| IEC61850_SV | `dataset_ref` | 采样值数据集引用。 |
| IEC61850_SV | `sample_index` / `phase` / `quantity` | 定位采样通道，例如 Ia、Ib、Ic、Ua、Ub、Uc。 |
| IEC61850_SV | `btype` / `quality` | 采样值类型与质量。 |
| MQTT | `topic` | MQTT 原生核心标识，但 topic 本身不定义业务变量类型。 |
| MQTT | `payload_encoding` | 应用层 payload 编码，例如 JSON、Protobuf、Avro、text、binary。 |
| MQTT | `payload_path` | JSONPath 或字段路径，用于定位 payload 中的变量值。 |
| MQTT | `schema_type` / `data_type` | 应用层补充，不是 MQTT 原生字段。 |
| HTTP_REST | `resource_path` | HTTP API 资源路径。 |
| HTTP_REST | `http_method` | HTTP 方法，例如 GET、POST、PUT、PATCH。 |
| HTTP_REST | `params_path` / `json_body_path` / `response_json_path` | 定位请求参数、请求体和响应体中的变量。 |
| HTTP_REST | `schema_type` / `data_type` | OpenAPI / JSON Schema 层面的类型，不是 HTTP 原生字段。 |

## 7. 外部程序访问流程

```text
1. 查询 vw_task_full，获取 task_type、connection_id、task_params_json、point_item_view_name、point_item_ids_json。
2. 用 connection_id 查询 vw_connection_object_full，获取 protocol 与 connection_params_json。
3. 根据 point_item_view_name 查询对应 vw_xxx_point_item，并用 point_item_id 匹配 vw_task_full.point_item_ids_json。
4. 驱动 facade 根据 protocol + task_type + connection_params_json + point item 字段调用协议包 API。
5. 工程值换算：engineering_value = raw_value * scale + offset_value。
6. 值域校验：连续量检查 value_min/value_max，离散量检查 allowed_values。
```

## 8. 自检要求

1. 建库脚本使用独立的 `CREATE DATABASE bluecrystal`，并在维护库（通常为 `postgres`）中单独执行。
2. DDL 创建 schema `whale`，并包含全部稳定标识查找函数。
3. 基础数据只依赖 DDL，不引用组织、场站、资产、员工、连接、任务或拓扑实例。
4. 现场样例可以引用基础数据，但不得重复插入公共参考代码、标准语义、协议注册、标准权限角色或协议操作定义。
5. 所有 SQL 均为纯 PostgreSQL SQL，不包含 `\set`、`\gexec`、`\connect` 等 `psql` 元命令。
6. 三个 SQL 文件不再出现 `whale_guard`。
7. DDL、基础数据和现场样例末尾均包含 `COMMIT`；DDL 的 `CREATE DATABASE` 位于 `BEGIN` 之前。
8. `cfg_measurement_semantic.name_zh` 不出现无业务含义的占位名称。
9. `cfg_measurement_semantic.standard_unit_ref_id` 与业务语义匹配。
10. 协议点位引用的 `measurement_semantic_id` 全部存在。
11. DDL / DML 不出现统一的 `point_access_mode`、`platform_access_mode` 或 `POINT_ACCESS_MODE`。
12. 执行视图字段均有 `COMMENT ON COLUMN`。


## 9. `basic_data.sql` 与 `site_sample.sql` 强制生成规范

### 9.1 总体目标

`basic_data.sql` 和 `site_sample.sql` 不是以“SQL 能执行”为验收标准，而必须共同构成一个业务真实、标准可追溯、协议可执行、拓扑闭合的并网型风光储一体化电场。

强制覆盖范围包括：风电、光伏、储能、升压站、并网点、AGC、AVC、一次调频、功率预测、电能计量、保护测控、自动化、通信网络、地理空间、运行检修及安全审计。风、光、储均为必选范围。

数据依赖顺序固定为：

```text
DDL → basic_data → site_sample
```

- `basic_data` 只能依赖 DDL，不得依赖任何场站实例。
- `site_sample` 可以依赖 DDL 和 `basic_data`。
- 运行期生成表只放少量有代表性的样例记录，不得用大量历史数据污染初始化文件。

### 9.2 `basic_data.sql` 内容要求

#### 9.2.1 `ref_code`

1. 必须覆盖 DDL 中所有 `xxx_ref_id` 字段实际约束的 `ref_type`。
2. 必须覆盖组织、场站、资产、协议、任务、权限、角色、单位、数据类型、物理量、拓扑、状态、事件及所有协议专属枚举。
3. `code` 必须稳定、唯一、统一大写；中英文名称及说明必须真实完整。
4. 禁止用字段名、编号或占位文本机械生成说明。
5. 单位、数据类型、物理量类别必须语义一致。
6. `PROTOCOL_TABLE_ROLE` 必须包含 `CONN`、`POINT_TABLE`、`POINT_ITEM`、`POINT_ITEM_VIEW`。
7. 所有项目共用的平台枚举放入 `basic_data`；项目临时扩展不得混入平台内置代码。

#### 9.2.2 `cfg_measurement_semantic`

1. 属于业务主数据，不是元数据。
2. 必须覆盖风电、光伏、储能、升压站、并网控制、保护测控、电能计量、气象环境、通信和 IT 设备。
3. 必须覆盖模拟量、状态量、告警量、命令量、设点量、控制量和累计量。
4. 每条记录必须具有稳定业务标识、真实中英文名称、标准来源、物理量类别、标准单位、标准数据类型和完整说明。
5. IEC/GB 标准语义应填写逻辑节点、数据对象和 CDC；企业扩展必须明确标识为扩展。
6. 同一业务语义不得因协议不同重复建立。
7. 禁止“标准语义001”“通用量001”等占位语义。
8. 单位和数据类型必须符合工程含义，例如功率、无功、电压、电流、温度、转速、转矩、振动、比例和状态量分别使用合理单位及类型。

#### 9.2.3 协议数据库对象注册

1. `cfg_protocol_table_registry` 必须为每种协议显式登记实际存在的连接表、点表、点位表和点位执行视图。
2. `POINT_ITEM_VIEW` 必须保存真实视图名，例如 MODBUS 对应 `vw_modbus_point_item`。
3. 不得通过 `cfg_{protocol}_point_item` 或 `vw_{protocol}_point_item` 字符串规律推导对象名。
4. 注册对象必须在 PostgreSQL 中真实存在，schema 必须为 `whale`。

#### 9.2.4 权限、角色及协议操作

1. `sec_permission` 必须覆盖组织、资产、协议配置、点表、任务、控制、拓扑、地理、告警、检修、审计及基础数据维护。
2. `sec_role` 必须覆盖系统管理员、数据管理员、数据治理、场站负责人、值长、运行、风机、光伏、储能、电气、继保、自动化、通信、安全、审计只读等职责。
3. `sec_role_permission` 必须遵守最小权限原则；控制、配置、维护和审计权限必须分离。
4. `cfg_protocol_operation_def` 只定义协议真实支持的原生操作。
5. `cfg_protocol_task_type_mapping` 必须保证任务类型与协议 operation 的方向和语义正确。
6. heartbeat、link check、association check 等健康检查不得归入采集任务类型。

### 9.3 `site_sample.sql` 内容要求

#### 9.3.1 组织、人员和角色实例

1. 组织层级必须形成“集团 → 区域公司 → 场站公司 → 并网型风光储电场”。
2. 班组必须覆盖运行、风机、光伏、储能、电气、继保自动化、通信、安全和数据治理。
3. 每个关键角色至少绑定一名员工；每名员工必须具有场站、组织、班组和角色关系。
4. 角色表示权限集合，班组表示组织协作关系，二者不得混用。

#### 9.3.2 资产与参数

1. 必须覆盖风机、风机主控、箱变、光伏方阵、逆变器、光伏箱变、电池簇、BMS、PCS、EMS、储能变压器、主变、母线、开关、保护 IED、电表、RTU、PLC、协议网关、交换机、防火墙、服务器和气象站。
2. 资产必须构成完整场站，禁止孤立堆砌。
3. 设备型号、额定容量、电压等级和参数必须相互匹配。
4. 风机数量与风电容量、逆变器容量与光伏容量、PCS 功率与储能容量、主变容量与总并网容量必须合理。

#### 9.3.3 地理空间

1. 必须覆盖场站中心、风机机位、光伏场区、储能区、升压站、主变、高压区、并网点、控制楼、通信机房、气象站及集电线路关键节点。
2. 坐标体系必须统一，禁止所有资产共用同一坐标。
3. 资产位置必须与其业务区域、电气拓扑和通信拓扑一致。

#### 9.3.4 电气拓扑

必须完整形成：

```text
风机 → 风机箱变 → 风电集电线路 → 风电集电母线
光伏方阵 → 逆变器 → 光伏箱变 → 光伏集电线路 → 光伏集电母线
电池簇 → BMS/PCS → 储能变压器 → 储能集电线路 → 储能母线
风/光/储母线 → 主变 → 高压母线 → 并网开关 → 并网点 → 公共电网
```

所有风、光、储单元都必须能够沿拓扑追溯至并网点；电压等级必须连续合理，不得存在孤立关键节点。

#### 9.3.5 通信拓扑

1. 必须覆盖现场控制器、保护测控、RTU、PLC、协议网关、接入交换机、核心交换机、防火墙、平台服务器和调度接口。
2. 每个协议连接必须能追溯到通信资产和通信路径。
3. 控制区、非控制区和管理区边界必须合理。
4. IP、端口、协议和网络区域必须与 `cfg_connection` 及协议子表一致。

#### 9.3.6 协议覆盖

支持协议必须全部使用，但每种协议只要求一套有代表性的完整链路：

```text
MODBUS、IEC101、IEC104、IEC61850_MMS、IEC61850_GOOSE、IEC61850_SV、OPCUA、MQTT、ADS、HTTP_REST
```

每个协议的最低完整链路为：

```text
资产 → cfg_connection → 协议连接子表 → 协议点表 → 协议点位 → 点位执行视图 → 任务
```

每种协议至少一个有效点位，任何协议点位表为零都必须使 `site_sample.sql` 执行失败。协议应绑定符合现场实际的设备，不得为凑覆盖率随意绑定。

#### 9.3.7 任务、事件和维护

1. 任务必须形成 `task → connection → point table → point item → semantic` 完整链路。
2. 任务点位必须能通过注册的真实点位执行视图查询到。
3. 运行记录只保留少量成功、失败和部分成功样例。
4. 连接状态事件覆盖在线、离线、故障和恢复。
5. 维护事件覆盖巡检、故障、检修、更换和恢复。

### 9.4 全部 64 张表的数据归属与覆盖要求

| 表名 | 归属 | 最低覆盖要求 |
|---|---|---|
| `ref_code` | basic_data | 覆盖全部引用类型、平台枚举和协议专属枚举。 |
| `org_unit` | site_sample | 完整集团至场站层级。 |
| `org_power_plant` | site_sample | 至少一个并网型风光储一体化电场。 |
| `org_work_team` | site_sample | 覆盖运行、风、光、储、电气、自动化、通信、安全、数据治理。 |
| `emp_employee` | site_sample | 每个关键岗位和角色有人员。 |
| `sec_permission` | basic_data | 覆盖全部平台功能和数据权限。 |
| `sec_role` | basic_data | 覆盖管理、运行、专业检修、治理、安全和审计角色。 |
| `sec_role_permission` | basic_data | 每个角色非空且满足最小权限。 |
| `sec_employee_role` | site_sample | 每个关键角色至少绑定一名员工。 |
| `ast_manufacturer` | site_sample | 覆盖样例设备实际厂商。 |
| `ast_asset_model` | site_sample | 覆盖风光储、升压站和通信设备型号。 |
| `ast_asset` | site_sample | 构成完整并网型风光储场站。 |
| `ast_asset_param_def` | site_sample | 各核心资产类型具备关键参数定义。 |
| `ast_asset_param_value` | site_sample | 核心资产具备与型号匹配的参数值。 |
| `ast_asset_maintenance_event` | site_sample | 少量巡检、故障、检修和恢复记录。 |
| `geo_location` | site_sample | 关键资产和区域均有合理坐标。 |
| `cfg_protocol_table_registry` | basic_data | 每协议登记 CONN、POINT_TABLE、POINT_ITEM、POINT_ITEM_VIEW。 |
| `cfg_measurement_semantic` | basic_data | 完整覆盖并网型风光储业务标准语义。 |
| `cfg_connection` | site_sample | 每个支持协议至少一个连接。 |
| `cfg_grid_dispatch_connection` | site_sample | 覆盖调度主通道及 AGC/AVC 并网业务。 |
| `cfg_connection_status_event` | site_sample | 少量在线、离线、故障、恢复事件。 |
| `cfg_modbus_point_table` | site_sample | 至少一个真实 MODBUS 点表。 |
| `cfg_modbus_point_item` | site_sample | 非空，地址、功能码、字节序和单位合理。 |
| `cfg_modbus_conn` | site_sample | 至少一个完整 MODBUS 连接。 |
| `cfg_iec101_point_table` | site_sample | 至少一个 IEC101 点表。 |
| `cfg_iec101_point_item` | site_sample | 非空，type_id、CA、IOA、COT 合理。 |
| `cfg_iec104_point_table` | site_sample | 至少一个 IEC104 点表。 |
| `cfg_iec104_point_item` | site_sample | 非空，type_id、CA、IOA、COT、时标合理。 |
| `cfg_iec101_conn` | site_sample | 至少一个 IEC101 串行连接。 |
| `cfg_iec104_conn` | site_sample | 至少一个 IEC104 网络连接。 |
| `cfg_iec61850_mms_point_table` | site_sample | 至少一个 MMS 点表。 |
| `cfg_iec61850_mms_point_item` | site_sample | 非空，object reference、FC、CDC、bType 合理。 |
| `cfg_iec61850_mms_conn` | site_sample | 至少一个 MMS 连接。 |
| `cfg_iec61850_goose_point_table` | site_sample | 至少一个 GOOSE 数据集点表。 |
| `cfg_iec61850_goose_point_item` | site_sample | 非空，控制块、数据集和成员索引合理。 |
| `cfg_iec61850_goose_conn` | site_sample | 至少一个 GOOSE 发布或订阅连接。 |
| `cfg_iec61850_sv_point_table` | site_sample | 至少一个 SV 采样通道点表。 |
| `cfg_iec61850_sv_point_item` | site_sample | 非空，相别、量类型和采样成员合理。 |
| `cfg_iec61850_sv_conn` | site_sample | 至少一个 SV 接收连接。 |
| `cfg_opcua_point_table` | site_sample | 至少一个 OPC UA 点表。 |
| `cfg_opcua_point_item` | site_sample | 非空，NodeId、namespace、attribute、类型合理。 |
| `cfg_opcua_conn` | site_sample | 至少一个 OPC UA 连接。 |
| `cfg_mqtt_point_table` | site_sample | 至少一个 MQTT payload 点表。 |
| `cfg_mqtt_point_item` | site_sample | 非空，topic、payload path、格式合理。 |
| `cfg_mqtt_conn` | site_sample | 至少一个 MQTT 连接。 |
| `cfg_http_rest_point_table` | site_sample | 至少一个 HTTP REST 点表。 |
| `cfg_http_rest_point_item` | site_sample | 非空，资源路径、方法和 JSON 路径合理。 |
| `cfg_http_rest_conn` | site_sample | 至少一个 HTTP REST 连接。 |
| `cfg_ads_point_table` | site_sample | 至少一个 ADS 点表。 |
| `cfg_ads_point_item` | site_sample | 非空，symbol 或 index group/offset 合理。 |
| `cfg_ads_conn` | site_sample | 至少一个 ADS 连接。 |
| `cfg_protocol_operation_def` | basic_data | 每协议覆盖真实读、写、订阅、报告或控制操作。 |
| `cfg_protocol_task_type_mapping` | basic_data | 操作与任务类型映射完整且方向正确。 |
| `task_point_table` | site_sample | 每种协议代表性任务均关联点表。 |
| `task_point_item` | site_sample | 每项引用真实点位，且执行视图可查询。 |
| `task` | site_sample | 覆盖周期读取、事件接收、发布和控制代表场景。 |
| `task_config` | site_sample | 每项任务具有有效运行配置。 |
| `task_param_def` | site_sample | 覆盖任务实际使用的参数定义。 |
| `task_param_value` | site_sample | 参数值与定义和任务配置一致。 |
| `task_run` | site_sample | 少量成功、失败和部分成功记录。 |
| `topo_elec_element` | site_sample | 覆盖风光储、母线、主变、开关和并网点。 |
| `topo_elec_connection` | site_sample | 所有风光储链路闭合至并网点。 |
| `topo_comm_element` | site_sample | 覆盖现场设备、交换机、防火墙、服务器和调度接口。 |
| `topo_comm_connection` | site_sample | 每个协议连接具备可追溯通信路径。 |

### 9.5 强制验收规则

1. 64 张表均有明确的数据归属或运行期生成规则。
2. 所有 basic_data 表均不依赖场站实例。
3. 所有 site_sample 外键均有效。
4. 十种协议均至少形成一套完整链路，且每种协议点位表非空。
5. `vw_connection_object_full.point_item_view_name` 必须来自 `cfg_protocol_table_registry` 的真实注册值，不能由代码拼接。
6. 所有任务点位均可从对应执行视图查询。
7. 所有风、光、储关键资产均可沿电气拓扑追溯至并网点。
8. 所有协议连接均可沿通信拓扑追溯至平台或调度接口。
9. 关键资产具有组织归属、地理位置以及电气或通信关系。
10. 禁止孤立资产、孤立拓扑节点、空点表、空角色、空权限和占位语义。
11. 标准来源、协议字段、单位、数据类型和业务语义必须可追溯且相互一致。
