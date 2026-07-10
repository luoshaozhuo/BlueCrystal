# BlueWhale 数据模型正式版 v1.5.3

## 0. Navicat 执行约束

PostgreSQL 不支持在普通 SQL 中切换数据库；`\connect`、`\set`、`\gexec` 仅属于 `psql` 客户端命令，不能由 Navicat SQL 编辑器执行。

因此正式初始化包拆成四个阶段：

1. 连接维护库 `postgres`，执行 `01_bluewhale_create_database_v1_5_3.sql`。
2. 在 Navicat 中新建或刷新 `bluewhale` 连接，连接到数据库 `bluewhale`。
3. 依次执行 `02_bluewhale_schema_ddl_v1_5_3.sql`、`03_bluewhale_basic_data_v1_5_3.sql`。
4. 仅在开发、测试、演示环境执行 `04_bluewhale_site_sample_v1_5_3.sql`。

`01` 文件只执行一次。由于 PostgreSQL 没有 `CREATE DATABASE IF NOT EXISTS`，数据库已经存在时不得重复执行。

## 1. 正式部署标识

| 项目 | 正式值 |
|---|---|
| PostgreSQL 数据库名 | `bluewhale` |
| PostgreSQL schema 名 | `whale` |
| DDL | `bluewhale_ddl_v1_5_3.sql` |
| 公共基础数据 | `bluewhale_basic_data_v1_5_3.sql` |
| 模拟现场样例数据 | `bluewhale_site_sample_v1_5_3.sql` |

推荐执行顺序：

```bash
psql -U <database_admin> -d postgres -f bluewhale_ddl_v1_5_3.sql
psql -U <database_user> -d bluewhale -f bluewhale_basic_data_v1_5_3.sql
psql -U <database_user> -d bluewhale -f bluewhale_site_sample_v1_5_3.sql
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

1. 数据库正式命名为 `bluewhale`，schema 正式命名为 `whale`。
2. 原单一 sample DML 拆分为公共基础数据和模拟现场样例数据。
3. 公共基础数据只表达“平台认识什么”，不得依赖组织、场站、资产、员工、连接或任务实例。
4. 模拟现场样例数据表达“虚拟场站具体有什么、如何连接、如何运行”。
5. `ref_code_id()`、`asset_id()`、`model_id()`、`connection_id()`、`semantic_id()`、拓扑元素查找函数和协议数据类型查找函数由 DML 迁入 DDL。
6. DDL、基础数据和现场样例统一使用 `bluewhale.whale`。
7. 保留 v1.4.10 已确定的测量语义、协议点位和访问能力边界，不改变业务表结构。

## 2.1 公共基础数据边界

`bluewhale_basic_data_v1_5_3.sql` 包含：

1. 全部平台参考代码 `ref_code`；
2. 标准测量语义 `cfg_measurement_semantic`；
3. 协议物理表注册 `cfg_protocol_table_registry`；
4. 标准权限、标准角色和角色权限模板；
5. 协议操作定义 `cfg_protocol_operation_def`；
6. 协议操作与任务类型映射 `cfg_protocol_task_type_mapping`。

该文件只能依赖 DDL，可以独立用于正式项目初始化。

## 2.2 模拟现场样例数据边界

`bluewhale_site_sample_v1_5_3.sql` 包含：

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

1. DDL 包含数据库 `bluewhale` 的条件创建逻辑，且建库语句位于事务之外。
2. DDL 创建 schema `whale`，并包含全部稳定标识查找函数。
3. 基础数据只依赖 DDL，不引用组织、场站、资产、员工、连接、任务或拓扑实例。
4. 现场样例可以引用基础数据，但不得重复插入公共参考代码、标准语义、协议注册、标准权限角色或协议操作定义。
5. 三个 SQL 文件均使用 `\set ON_ERROR_STOP on` 和 `\connect bluewhale`。
6. 三个 SQL 文件不再出现 `whale_guard`。
7. DDL、基础数据和现场样例末尾均包含 `COMMIT`；DDL 的 `CREATE DATABASE` 位于 `BEGIN` 之前。
8. `cfg_measurement_semantic.name_zh` 不出现无业务含义的占位名称。
9. `cfg_measurement_semantic.standard_unit_ref_id` 与业务语义匹配。
10. 协议点位引用的 `measurement_semantic_id` 全部存在。
11. DDL / DML 不出现统一的 `point_access_mode`、`platform_access_mode` 或 `POINT_ACCESS_MODE`。
12. 执行视图字段均有 `COMMENT ON COLUMN`。
