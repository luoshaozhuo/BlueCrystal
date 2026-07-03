# ISA-95（IEC 62264）介绍文档

## 1. 标准概述

ISA-95 是国际自动化协会 ISA 发布的 **Enterprise-Control System Integration（企业系统与控制系统集成）** 标准，国际标准体系中对应 **IEC 62264**。

它的核心作用不是规定某种通信报文，而是规定：

```text
企业经营系统、制造运营系统、监控系统、控制系统之间如何分层；
各层系统分别承担什么职责；
Level 3 与 Level 4 之间应该交换哪些业务对象；
生产订单、物料、设备、人员、工艺段、生产绩效等对象如何建模。
```

因此，ISA-95 不是 Modbus、PROFINET、IEC104、OPC UA 这样的通信协议，而是一个 **工业生产系统集成架构标准 / 信息模型标准 / 术语标准**。

### 1.1 核心目标

| 目标 | 说明 |
|------|------|
| 系统分层 | 明确 ERP、MES、SCADA、PLC、现场设备之间的职责边界 |
| 降低集成复杂度 | 避免 ERP 直接控制 PLC，也避免 MES 直接替代 SCADA |
| 统一业务对象 | 用标准方式描述人员、设备、物料、工艺、订单、能力、绩效 |
| 支撑 ERP-MES 集成 | 明确 Level 4 与 Level 3 之间的数据交换内容 |
| 支撑制造运营管理 | 为 MES / MOM / 生产数据平台提供对象模型参考 |

### 1.2 ISA-95 与常见协议的关系

| 类型 | 代表 | 作用 |
|------|------|------|
| 通信协议 | Modbus、PROFINET、IEC104、OPC UA、MQTT | 解决“数据如何传输” |
| 信息模型 / 架构标准 | ISA-95 / IEC 62264 | 解决“系统如何分层、对象如何建模、业务数据如何定义” |
| 网络安全标准 | IEC 62443 / ISA-99 | 解决“工业网络如何分区、加固、防护” |
| 批控制标准 | ISA-88 / IEC 61512 | 解决“批生产过程如何建模和控制” |

工程上常见组合是：

```text
ISA-95 定义对象和系统边界；
OPC UA / MQTT / REST / Kafka / SQL 承载数据交换；
IEC 62443 约束网络安全分区；
MES / MOM / 数据平台负责业务落地。
```

---

## 2. ISA-95 分层模型

ISA-95 通常采用 Level 0 到 Level 4 的分层结构，用于描述从物理生产过程到企业经营系统的关系。

### 2.1 分层总览

| 层级 | 名称 | 主要对象 | 常见软件系统 | 常见通信协议 / 接口 | 典型职责 |
|------|------|----------|--------------|----------------------|----------|
| Level 4 | 企业计划与物流层 | 企业、订单、财务、供应链、销售、采购、库存计划 | ERP、SCM、CRM、PLM、EAM、BI、财务系统、采购系统 | REST、SOAP、SQL、消息队列、SFTP、EDI | 企业级计划、供应链、成本、财务、销售、采购、长期生产计划 |
| Level 3 | 制造运营管理层 | 生产订单、批次、工单、物料、设备、人员、质量、库存、维护 | MES、MOM、APS、QMS、LIMS、WMS、CMMS、EMS、OEE 系统、生产数据平台 | OPC UA、MQTT、REST、SQL、Kafka、AMQP、B2MML | 生产执行、排程、质量、维护、库存、绩效、追溯、能耗管理 |
| Level 2 | 监控与监督控制层 | 生产线、设备状态、报警、趋势、过程画面、历史数据 | SCADA、HMI、Historian、Alarm Management、Batch Control、站控系统、集控系统 | OPC UA、OPC DA、Modbus TCP、IEC104、DNP3、IEC61850 MMS、S7、BACnet/IP | 监控、报警、趋势、操作、历史记录、站控/线控 |
| Level 1 | 基本控制层 | PLC、DCS 控制器、RTU、PAC、运动控制器、机器人控制器 | PLC Runtime、DCS Controller Runtime、RTU Firmware、SoftPLC、Motion Control Runtime、Robot Controller Software | PROFINET、EtherCAT、EtherNet/IP、PROFIBUS-DP、CANopen、Modbus TCP、DeviceNet | 闭环控制、顺控、联锁、实时 I/O、运动控制 |
| Level 0 | 物理生产过程层 | 设备、物料、传感器、执行器、阀门、电机、生产对象 | - | 4-20mA、0-10V、DI/DO、HART、IO-Link、Modbus RTU、PROFIBUS-PA、CAN | 真实物理过程、测量、执行、物料转换、设备动作 |

### 2.2 分层图

```text
Level 4  企业计划与物流层
         ERP / SCM / CRM / PLM / 财务 / 采购 / BI
         长周期计划、供应链、成本、经营分析

Level 3  制造运营管理层
         MES / MOM / APS / QMS / LIMS / WMS / CMMS / 生产数据平台
         生产执行、排程、质量、维护、库存、绩效、追溯

Level 2  监控与监督控制层
         SCADA / HMI / Historian / Alarm / Batch / 站控系统
         监控、报警、趋势、历史、操作、监督控制

Level 1  基本控制层
         PLC / DCS Controller / RTU / PAC / Motion / Robot Controller
         实时控制、联锁、顺控、I/O 扫描、运动控制

Level 0  物理生产过程层
         传感器 / 执行器 / 阀门 / 电机 / 物料 / 生产设备
         真实物理过程
```

---

## 3. 各层职责详解

### 3.1 Level 0：物理生产过程层

Level 0 是真实的物理生产过程，包括设备、物料、能量流、传感器、执行器和生产对象。

典型对象：

```text
电机、泵、风机、阀门、传感器、执行器、输送线、反应釜、风机叶片、箱变、断路器、储能电池簇、物料、产品、半成品。
```

这一层通常没有独立的“软件系统”。如果有软件，也多是设备内部固件，不作为 ISA-95 层级中的业务系统建模。

常见信号和协议：

| 类型 | 说明 |
|------|------|
| DI/DO | 开关量输入输出 |
| AI/AO | 模拟量输入输出 |
| 4-20mA | 过程仪表最常见模拟量信号 |
| HART | 叠加在 4-20mA 上的智能仪表通信 |
| IO-Link | 智能传感器和执行器点对点通信 |
| Modbus RTU | 串口仪表、电表、变频器 |
| PROFIBUS-PA | 过程自动化仪表 |
| CAN | 车载、工程机械、设备内部控制 |

### 3.2 Level 1：基本控制层

Level 1 负责直接控制 Level 0 的物理过程。

典型系统和软件：

| 类型 | 示例 |
|------|------|
| PLC | Siemens S7、Rockwell ControlLogix、Schneider M580、Beckhoff TwinCAT PLC |
| DCS 控制器 | Yokogawa、Honeywell、Emerson、Siemens PCS 7 控制站 |
| RTU | 电力、油气、水务远程终端 |
| PAC | Programmable Automation Controller |
| 运动控制器 | EtherCAT Master、伺服控制器、CNC 控制器 |
| 机器人控制器 | ABB、KUKA、FANUC、Yaskawa 控制柜 |

典型职责：

```text
采集 I/O；
执行控制逻辑；
实现联锁保护；
控制阀门、电机、伺服、变频器；
执行高速闭环控制；
执行本地安全逻辑。
```

常见协议：

```text
PROFINET、EtherCAT、EtherNet/IP、PROFIBUS-DP、CANopen、DeviceNet、Modbus TCP、Modbus RTU。
```

### 3.3 Level 2：监控与监督控制层

Level 2 面向操作员和现场监控系统，负责把控制层的数据组织成画面、报警、趋势、历史记录和操作接口。

常见软件系统：

| 软件系统 | 说明 |
|----------|------|
| SCADA | 采集、监控、报警、趋势、操作 |
| HMI | 人机界面，面向现场操作员 |
| Historian | 历史数据库，保存过程数据和事件 |
| Alarm Management | 报警管理、报警统计、报警抑制 |
| Batch Control | 批控制系统，常与 ISA-88 相关 |
| 站控系统 | 电力、风电、光伏、储能场站监控 |
| 集控系统 | 多场站集中监控 |

典型职责：

```text
实时监控生产状态；
显示工艺画面；
处理报警和事件；
记录历史趋势；
下发操作命令；
为 Level 3 提供过程数据。
```

常见协议：

```text
OPC UA、OPC DA、Modbus TCP、IEC104、IEC101、IEC61850 MMS、DNP3、S7、BACnet/IP。
```

### 3.4 Level 3：制造运营管理层

Level 3 是 ISA-95 的重点层级，也就是制造运营管理层。MES / MOM 通常位于这一层。

常见软件系统：

| 软件系统 | 全称 / 含义 | 典型职责 |
|----------|-------------|----------|
| MES | Manufacturing Execution System | 生产执行、工单、报工、追溯 |
| MOM | Manufacturing Operations Management | 制造运营管理总称，范围比 MES 更宽 |
| APS | Advanced Planning and Scheduling | 高级计划与排程 |
| QMS | Quality Management System | 质量管理、检验、不合格品处理 |
| LIMS | Laboratory Information Management System | 实验室检测、样品、检验结果 |
| WMS | Warehouse Management System | 仓储、库位、出入库、物料配送 |
| CMMS | Computerized Maintenance Management System | 维护计划、点检、保养、维修工单 |
| EAM | Enterprise Asset Management | 资产全生命周期管理，常跨 Level 3/4 |
| EMS | Energy Management System | 能源管理、能耗分析、能效优化 |
| OEE 系统 | Overall Equipment Effectiveness | 设备综合效率统计 |
| 生产数据平台 | 工业数据湖、数据中台、实时数据平台 | 数据汇聚、清洗、建模、分析 |

ISA-95 通常把 Level 3 的制造运营管理划分为四大领域：

| 领域 | 英文 | 说明 |
|------|------|------|
| 生产运营管理 | Production Operations Management | 生产执行、生产调度、生产绩效 |
| 维护运营管理 | Maintenance Operations Management | 设备维护、检修、保养、维修绩效 |
| 质量运营管理 | Quality Operations Management | 检验、质量判定、质量追溯 |
| 库存运营管理 | Inventory Operations Management | 物料、库存、在制品、仓储流转 |

### 3.5 Level 4：企业计划与物流层

Level 4 是企业经营和计划层，面向长期计划、订单、供应链、财务和经营管理。

常见软件系统：

| 软件系统 | 全称 / 含义 | 典型职责 |
|----------|-------------|----------|
| ERP | Enterprise Resource Planning | 订单、采购、库存、财务、成本、主数据 |
| SCM | Supply Chain Management | 供应链计划、采购协同、物流协同 |
| CRM | Customer Relationship Management | 客户、销售、合同、订单需求 |
| PLM | Product Lifecycle Management | 产品定义、BOM、工艺版本、设计变更 |
| EAM | Enterprise Asset Management | 资产台账、资产投资、生命周期管理 |
| HR | Human Resources | 人力资源、岗位、组织、考勤 |
| BI | Business Intelligence | 经营报表、管理分析、指标看板 |
| 财务系统 | Finance System | 成本、预算、核算、结算 |
| 采购系统 | Procurement System | 采购计划、供应商、合同、到货 |

典型职责：

```text
接收市场和客户需求；
生成生产计划和采购计划；
管理物料主数据和 BOM；
管理成本、库存、财务；
接收 Level 3 返回的生产完成、物料消耗、质量和绩效数据。
```

---

## 4. ISA-95 的核心边界：Level 3 与 Level 4

ISA-95 最重要的工程价值，是明确 **ERP 与 MES/MOM 的边界**。

### 4.1 Level 4 负责什么

Level 4 关注企业级计划与经营决策，典型时间尺度是天、周、月、季度。

```text
客户订单；
销售预测；
长期生产计划；
采购计划；
库存计划；
成本核算；
财务结算；
供应链协同。
```

### 4.2 Level 3 负责什么

Level 3 关注生产执行与制造运营，典型时间尺度是班次、小时、分钟。

```text
工单下发；
工序执行；
设备状态；
人员派工；
物料领用；
生产报工；
质量检验；
异常处理；
停机统计；
绩效分析。
```

### 4.3 边界示例

| 业务对象 | Level 4 ERP 侧 | Level 3 MES/MOM 侧 |
|----------|----------------|--------------------|
| 生产订单 | 创建订单、确定需求、交付计划 | 拆分工单、排程、派工、执行跟踪 |
| 物料 | 管理物料主数据、库存账 | 管理现场领料、投料、退料、批次追溯 |
| 设备 | 资产台账、折旧、投资计划 | 设备状态、停机、点检、维修、OEE |
| 质量 | 质量策略、客户质量要求 | 检验计划、检验结果、不合格品处理 |
| 人员 | 组织、岗位、考勤、薪酬 | 班组、岗位资格、派工、操作记录 |
| 绩效 | 经营指标、成本、产量汇总 | 班次产量、设备效率、良率、停机原因 |

---

## 5. ISA-95 信息对象模型

ISA-95 不只是一张分层图，它还定义了一组用于企业与制造系统集成的对象模型。

### 5.1 资源对象

ISA-95 中常见的资源包括：

| 对象 | 含义 | 示例 |
|------|------|------|
| Personnel | 人员资源 | 操作工、检修工、班组长、质检员 |
| Equipment | 设备资源 | 产线、工位、反应釜、风机、箱变、机器人 |
| Material | 物料资源 | 原料、辅料、半成品、成品、备件 |
| Physical Asset | 物理资产 | 设备资产、模具、工具、车辆、仪器 |

### 5.2 生产定义对象

| 对象 | 含义 |
|------|------|
| Product Definition | 产品定义，描述产品如何制造 |
| Process Segment | 过程段，描述一段生产能力或工艺活动 |
| Operations Segment | 运营段，将过程段与实际制造运营关联 |
| Bill of Material | 物料清单 |
| Bill of Resources | 资源清单，包括设备、人员、物料、工装等 |

### 5.3 计划、执行与绩效对象

| 对象 | 含义 |
|------|------|
| Operations Schedule | 运营计划，描述要执行什么生产活动 |
| Operations Request | 运营请求，面向某次具体生产执行 |
| Operations Response | 运营响应，描述执行结果 |
| Operations Performance | 运营绩效，描述产量、质量、消耗、状态等结果 |
| Operations Capability | 运营能力，描述设备、人员、物料等可用能力 |

### 5.4 典型数据流

```text
Level 4 ERP
    ↓ 生产计划 / 订单 / 物料需求
Level 3 MES/MOM
    ↓ 工单 / 派工 / 作业指令
Level 2 SCADA / HMI
    ↓ 控制命令 / 配方 / 参数
Level 1 PLC / DCS / RTU
    ↓ I/O 控制
Level 0 物理过程

Level 0 物理过程
    ↑ 传感器 / 状态 / 产量 / 事件
Level 1 PLC / DCS / RTU
    ↑ 实时数据 / 报警 / 状态
Level 2 SCADA / Historian
    ↑ 历史趋势 / 报警 / 过程数据
Level 3 MES/MOM
    ↑ 报工 / 绩效 / 质量 / 消耗 / 追溯
Level 4 ERP
```

---

## 6. ISA-95 与软件系统的对应关系

### 6.1 ERP

ERP 通常位于 Level 4。

典型模块：

```text
销售订单；
采购管理；
库存管理；
财务管理；
成本核算；
主数据管理；
供应链计划；
资产管理。
```

ERP 不应直接控制 PLC，也不应直接处理毫秒级实时过程数据。ERP 需要的是生产结果、库存变化、物料消耗、质量结论、成本数据等汇总后的业务数据。

### 6.2 MES / MOM

MES / MOM 通常位于 Level 3。

典型模块：

```text
工单管理；
生产排程；
派工管理；
报工管理；
物料追溯；
设备管理；
质量检验；
异常处理；
OEE 分析；
电子批记录；
生产绩效统计。
```

MES 是 ERP 与现场控制系统之间的桥梁。它既理解 ERP 的业务对象，也能够对接 SCADA、Historian、PLC 或工业数据平台。

### 6.3 SCADA / HMI / Historian

SCADA / HMI / Historian 通常位于 Level 2。

典型模块：

```text
实时画面；
报警管理；
趋势曲线；
历史数据；
操作记录；
事件记录；
权限管理；
报表。
```

SCADA 主要面向操作和监控，不应承担完整 ERP 或 MES 职责。

### 6.4 PLC / DCS / RTU

PLC / DCS / RTU 通常位于 Level 1。

典型职责：

```text
执行控制逻辑；
采集现场 I/O；
控制阀门、电机、变频器、伺服；
执行联锁；
实现本地保护；
响应上层控制命令。
```

这一层强调确定性、实时性和安全性，不适合承载复杂业务逻辑。

---

## 7. ISA-95 与通信协议的关系

ISA-95 不规定具体通信协议。实际系统集成时，可以使用不同协议或接口承载 ISA-95 对象。

### 7.1 常见承载方式

| 集成边界 | 常用技术 | 说明 |
|----------|----------|------|
| ERP ↔ MES | REST、SOAP、SQL、消息队列、B2MML、SFTP | 订单、物料、库存、报工、质量结果 |
| MES ↔ SCADA | OPC UA、REST、SQL、MQTT、Kafka | 生产状态、设备状态、工单状态、过程数据 |
| SCADA ↔ PLC/RTU | OPC UA、Modbus TCP、IEC104、IEC61850 MMS、S7、DNP3 | 实时采集、遥控、报警、事件 |
| PLC ↔ 现场设备 | PROFINET、EtherCAT、PROFIBUS、CANopen、Modbus RTU、IO-Link | 实时 I/O、驱动控制、仪表采集 |
| 数据平台 ↔ 上层应用 | Kafka、MQTT、REST、GraphQL、SQL | 数据分析、看板、AI、预测性维护 |

### 7.2 B2MML

B2MML 是 ISA-95 / IEC 62264 对象模型的一种 XML 实现形式，常用于 ERP 与 MES 之间的标准化数据交换。

典型对象包括：

```text
ProductionSchedule；
ProductionPerformance；
MaterialLot；
Equipment；
Personnel；
ProcessSegment；
OperationsCapability。
```

工程中也可以不用 XML，而使用 JSON、数据库表、REST API、Kafka 事件等方式实现同样的对象模型。关键是对象语义应与 ISA-95 保持一致。

---

## 8. 风电场场景示例

风电场可以用 ISA-95 分层方式进行系统定位。

### 8.1 风电场分层表

| 层级 | 风电场对象 | 常见软件系统 | 常见协议 / 接口 | 说明 |
|------|------------|--------------|------------------|------|
| Level 4 | 集团经营、资产、财务、采购、长期生产计划 | ERP、EAM、财务系统、采购系统、BI | REST、SQL、消息队列、SFTP | 经营管理、资产管理、采购、预算、经营分析 |
| Level 3 | 集控生产运营、运维、工单、状态监测、能效分析 | MES/MOM、CMMS、EAM、状态监测平台、生产数据平台、OEE/可利用率系统 | OPC UA、MQTT、REST、Kafka、SQL | 运维计划、工单、检修、状态评估、生产绩效 |
| Level 2 | 风电场 SCADA、升压站监控、AGC/AVC、历史库 | SCADA、HMI、Historian、Alarm、AGC/AVC、站控系统 | OPC UA、IEC104、IEC61850 MMS、Modbus TCP、厂家私有协议 | 场站监控、调度通信、报警、历史数据 |
| Level 1 | 风机控制器、变流器、箱变测控、保护测控、RTU | PLC Runtime、RTU Firmware、Protection IED Software、Controller Runtime | PROFINET、EtherCAT、CANopen、Modbus TCP、PROFIBUS、IEC61850 GOOSE/SV | 实时控制、保护、联锁、设备控制 |
| Level 0 | 风机、叶片、变桨、偏航、电机、传感器、断路器、SVG、储能 PCS | - | 4-20mA、DI/DO、HART、IO-Link、Modbus RTU、CAN | 真实设备与物理过程 |

### 8.2 风电场典型数据流

```text
Level 4 ERP / EAM
    ↓ 年度计划、检修计划、采购计划、资产台账
Level 3 集控生产运营平台 / CMMS / 状态监测
    ↓ 工单、检修任务、状态评估、运维调度
Level 2 风电场 SCADA / 升压站监控 / AGC AVC
    ↓ 控制策略、调度指令、报警处理
Level 1 风机控制器 / RTU / 保护测控 / PLC
    ↓ 设备控制、保护联锁、实时采集
Level 0 风机与电气设备

Level 0/1
    ↑ 运行状态、功率、风速、温度、振动、电气量、故障
Level 2
    ↑ 报警、事件、历史趋势、调度数据
Level 3
    ↑ 可利用率、停机原因、检修结果、工单闭环、状态评估
Level 4
    ↑ 经营报表、资产绩效、成本、采购需求
```

### 8.3 风电场中的系统边界建议

| 系统 | 建议职责 | 不建议承担的职责 |
|------|----------|------------------|
| 风机控制器 | 实时控制、保护联锁、设备状态采集 | 企业报表、工单流转、复杂分析 |
| 风电场 SCADA | 实时监控、报警、趋势、AGC/AVC 接入 | ERP 计划、资产折旧、采购流程 |
| 集控平台 / 生产数据平台 | 多场站数据汇聚、状态分析、运维协同 | 毫秒级控制闭环 |
| CMMS / EAM | 工单、点检、检修、资产管理 | 直接下发 PLC 控制逻辑 |
| ERP | 财务、采购、库存、经营计划 | 直接采集现场点表、直接遥控设备 |

---

## 9. 数据建模示例

### 9.1 设备资源建模

```yaml
enterprise: WindPowerGroup
site: WindFarm_A
area: TurbineArea_01
work_center: TurbineCluster_01
work_unit: Turbine_WTG001

equipment:
  id: WTG001
  type: wind_turbine
  manufacturer: DemoWind
  rated_power_kw: 5000
  location: A01
  parent: TurbineCluster_01
```

### 9.2 生产绩效建模

```yaml
production_performance:
  site: WindFarm_A
  period: 2026-07-01
  energy_generated_mwh: 1280.5
  availability_percent: 97.2
  curtailment_mwh: 35.6
  downtime:
    planned_hours: 4.0
    unplanned_hours: 1.5
  quality:
    data_completeness_percent: 99.5
```

### 9.3 维护运营建模

```yaml
maintenance_request:
  id: WO-20260701-001
  equipment: WTG001
  fault_code: converter_overtemperature
  priority: high
  requested_start_time: 2026-07-01T08:00:00
  required_personnel:
    - role: electrical_technician
      count: 2
  required_materials:
    - material_id: FAN_MODULE_A
      quantity: 1
```

这些对象不是 ISA-95 原文的完整 XML 模式，而是工程上按 ISA-95 思路组织的业务对象示例。

---

## 10. 工程落地建议

### 10.1 不要把 ISA-95 当成通信协议

ISA-95 不解决端口、帧格式、轮询周期、TCP/UDP、点表编码等问题。

这些问题应由具体协议解决：

```text
现场实时控制：PROFINET / EtherCAT / PROFIBUS / CANopen
SCADA 采集：OPC UA / Modbus TCP / IEC104 / IEC61850 MMS
平台集成：MQTT / Kafka / REST / SQL
企业集成：REST / SOAP / B2MML / 消息队列
```

### 10.2 Level 3 不应绕过 Level 2 直接控制 Level 1

MES 或生产数据平台可以读取生产状态，也可以下发生产任务，但不应直接替代 SCADA/HMI 的现场操作职责，更不应绕过安全联锁直接控制 PLC。

推荐方式：

```text
MES / 数据平台
    ↓ 工单、计划、参数、目标值
SCADA / 控制系统
    ↓ 校验、权限、安全策略、操作流程
PLC / DCS / RTU
    ↓ 实际控制
现场设备
```

### 10.3 ERP 不应直接访问现场点表

ERP 需要的是业务结果，不是现场原始点位。

不推荐：

```text
ERP 直接读 PLC 点表
ERP 直接读 IEC104 遥测遥信
ERP 直接发遥控命令
```

推荐：

```text
现场数据 → SCADA/Historian → MES/数据平台 → ERP
```

### 10.4 建立统一对象模型

如果没有统一对象模型，系统之间容易形成大量点对点接口。

建议统一以下对象：

```text
组织：enterprise / site / area / line / unit
设备：equipment / asset / device / component
物料：material / lot / batch
人员：personnel / role / qualification
工艺：process segment / operation segment
计划：schedule / request / work order
结果：response / performance / quality result
事件：alarm / event / downtime / fault
```

### 10.5 区分实时数据、事件数据和业务数据

| 数据类型 | 示例 | 典型层级 |
|----------|------|----------|
| 实时数据 | 电流、电压、转速、温度、压力、功率 | Level 1/2 |
| 事件数据 | 报警、故障、状态变化、停机原因 | Level 2/3 |
| 业务数据 | 工单、订单、质量结果、物料消耗、产量 | Level 3/4 |
| 经营数据 | 成本、采购、库存、资产绩效、财务 | Level 4 |

---

## 11. 常见误区

### 11.1 误区一：ISA-95 就是自动化金字塔

ISA-95 常用分层图表达，但它不只是分层图，还包含对象模型、功能边界和 Level 3/4 集成模型。

### 11.2 误区二：MES 等于 ISA-95

MES 通常位于 ISA-95 Level 3，但 ISA-95 不是某个 MES 产品，也不规定 MES 必须如何实现。

### 11.3 误区三：OPC UA 可以替代 ISA-95

OPC UA 是通信架构和信息建模技术，ISA-95 是制造运营对象和企业控制集成标准。二者可以结合，但不是替代关系。

### 11.4 误区四：ERP 可以直接管现场设备

ERP 管业务计划和企业资源，不适合直接处理现场实时控制。直接打通 ERP 到 PLC 会带来安全、实时性、职责边界和维护风险。

### 11.5 误区五：Level 3 是单一软件

Level 3 不是只有 MES。它可能包含 MES、MOM、APS、QMS、LIMS、WMS、CMMS、EMS、生产数据平台等多个系统。

---

## 12. 与其他标准的关系

| 标准 / 技术 | 与 ISA-95 的关系 |
|-------------|------------------|
| Purdue Model | 提供工业系统分层思想，ISA-95 使用类似层级表达企业-控制集成 |
| IEC 62264 | ISA-95 的国际标准对应体系 |
| ISA-88 / IEC 61512 | 批控制标准，常用于 Level 1/2 的批生产过程建模 |
| IEC 62443 / ISA-99 | 工业控制系统网络安全标准，可用于 ISA-95 分层下的安全分区 |
| OPC UA | 可承载 ISA-95 风格的信息模型和数据交换 |
| B2MML | ISA-95 对象模型的 XML 实现之一 |
| MQTT / Kafka | 可用于承载 Level 2/3/4 之间的事件流和数据流 |

---

## 13. 总结

ISA-95 的核心不是“怎么传数据”，而是“工业企业的生产系统应该如何分层、如何定义对象、如何划分职责、如何交换业务数据”。

最简记忆：

```text
Level 0：真实物理过程
Level 1：PLC / DCS / RTU 实时控制
Level 2：SCADA / HMI / Historian 监控
Level 3：MES / MOM / 生产运营管理
Level 4：ERP / SCM / 企业经营管理
```

工程落地时应遵循：

```text
现场实时控制放在 Level 1；
监控、报警、历史放在 Level 2；
生产执行、质量、维护、库存、绩效放在 Level 3；
订单、财务、采购、供应链放在 Level 4；
跨层集成使用 OPC UA、MQTT、REST、Kafka、SQL、B2MML 等技术承载。
```

---

## 14. 参考资料

- ISA：ISA-95 Standard: Enterprise-Control System Integration
- Siemens：ISA-95 Framework and Layers
- ANSI：ANSI/ISA-95.00.01-2025 Enterprise-Control System Integration
- MESA / B2MML：ISA-95 / IEC 62264 XML 实现与 MES 集成实践
