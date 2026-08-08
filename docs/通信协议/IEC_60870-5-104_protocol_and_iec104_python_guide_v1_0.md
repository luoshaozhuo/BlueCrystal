# IEC 60870-5-104 协议完整解读与 `iec104-python` 实践指南

> 文档版本：v1.0  
> 修订日期：2026-07-16  
> 适用范围：IEC 60870-5-104 协议学习、主站/子站开发、互操作测试，以及 `iec104-python`（导入名 `c104`）的工程实践。  
> 包版本说明：本文包能力与示例以 `c104 2.2.1` 的公开文档和 API 为主要依据。第三方包的支持范围可能随版本变化，生产项目应锁定版本并重新验证。

---

## 目录

- [第一部分：IEC 60870-5-104 协议](#第一部分iec-60870-5-104-协议)
  - [1. 协议定位](#1-协议定位)
  - [2. 角色、连接和通信模型](#2-角色连接和通信模型)
  - [3. 协议栈与 APDU](#3-协议栈与-apdu)
  - [4. APCI：I、S、U 格式](#4-apciis-u-格式)
  - [5. 序号、窗口与定时器](#5-序号窗口与定时器)
  - [6. ASDU 结构与寻址](#6-asdu-结构与寻址)
  - [7. VSQ、SQ 与批量信息对象](#7-vsqsq-与批量信息对象)
  - [8. Type ID 与信息元素](#8-type-id-与信息元素)
  - [9. COT：传送原因](#9-cot传送原因)
  - [10. QOI、QCC、QOC 等限定词](#10-qoiqccqoc-等限定词)
  - [11. 质量描述符和时标](#11-质量描述符和时标)
  - [12. 主要业务流程](#12-主要业务流程)
  - [13. 总召、周期、自发和背景传送的关系](#13-总召周期自发和背景传送的关系)
  - [14. 点表与互操作约定](#14-点表与互操作约定)
  - [15. 重连、多主站、异常与安全](#15-重连多主站异常与安全)
  - [16. 完整报文拆解示例](#16-完整报文拆解示例)
- [第二部分：`iec104-python` 实践](#第二部分iec104-python-实践)
  - [17. 包定位、安装与架构](#17-包定位安装与架构)
  - [18. 对象模型](#18-对象模型)
  - [19. 协议概念与对象映射](#19-协议概念与对象映射)
  - [20. 包提供的主要能力](#20-包提供的主要能力)
  - [21. 版本相关限制](#21-版本相关限制)
  - [22. 子站 Server 完整示例](#22-子站-server-完整示例)
  - [23. 主站 Client 完整示例](#23-主站-client-完整示例)
  - [24. 总召、读、累计量召唤与时钟同步](#24-总召读累计量召唤与时钟同步)
  - [25. 周期、自发和后台发送](#25-周期自发和后台发送)
  - [26. 遥控与设点命令](#26-遥控与设点命令)
  - [27. 批量传输、原始报文与调试](#27-批量传输原始报文与调试)
  - [28. 工程化建议与常见误区](#28-工程化建议与常见误区)
  - [附录 A：常见 Type ID](#附录-a常见-type-id)
  - [附录 B：`c104 2.2.1` 能力矩阵](#附录-bc104-221-能力矩阵)
  - [参考资料](#参考资料)

---

# 第一部分：IEC 60870-5-104 协议

## 1. 协议定位

IEC 60870-5-104，工程上通常简称 **IEC 104**，是电力系统远动、SCADA、调度自动化、场站网关和 RTU 中常见的通信协议。

它可以理解为：

```text
IEC 60870-5-101 的应用层语义
+
基于 TCP/IP 的网络传输与链路控制
```

IEC 104 主要用于：

- 主站采集子站的遥信、遥测、累计量和事件；
- 子站主动上送状态变化和周期数据；
- 主站向子站下发遥控、遥调和设点命令；
- 主站发起总召、组召、累计量召唤、单点读和时钟同步；
- 在以太网、专网、VPN 或 IP 广域网上替代 IEC 101 的串行链路。

IEC 104 与 Modbus 的思维方式不同：

```text
Modbus：主站按寄存器地址轮询读取或写入。
IEC 104：双方交换带 Type ID、COT、公共地址和 IOA 的 ASDU 事件或命令。
```

IEC 104 虽然经常使用“点表”，但其协议数据单元不是“寄存器块”。每个信息对象的结构由 Type ID 决定，其业务触发原因由 COT 决定。

---

## 2. 角色、连接和通信模型

### 2.1 控制站与被控站

标准语义中常用的角色为：

| 标准角色 | 常用中文 | 常见设备 | 通常的 TCP 行为 |
|---|---|---|---|
| Controlling Station | 控制站、主站 | 调度主站、SCADA、集控系统 | TCP Client，主动连接 |
| Controlled Station | 被控站、子站 | RTU、场站网关、保护测控装置 | TCP Server，监听端口 |

典型通信关系：

```text
主站/控制站                     子站/被控站
TCP Client                     TCP Server
主动连接  ------------------->  监听 2404
STARTDT_ACT ------------------>  STARTDT_CON
总召、读、控制 --------------->  返回当前值或命令结果
                  <------------  自发、周期、背景数据
```

### 2.2 TCP Client/Server 不等于业务角色

“TCP Client”描述连接发起方，“控制站”描述 IEC 104 应用角色。多数工程中二者一致，但不是逻辑上必然一致。

例如，某个场站网关可能由于 NAT 或安全区设计主动向中心建立 TCP 连接，但它仍可能在业务上承担被控站语义。因此文档中应分别说明：

- TCP 连接方向；
- IEC 104 控制站/被控站角色；
- 监视方向和控制方向；
- 谁发起总召和控制；
- 谁主动发布过程数据。

### 2.3 一个 TCP 连接可以承载多个逻辑站

IEC 104 的一个 TCP 连接中可以使用多个 ASDU 公共地址：

```text
TCP 连接 192.168.1.20:2404
├── CA = 1：场站总控
├── CA = 2：升压站
├── CA = 3：无功补偿系统
└── CA = 4：储能系统
```

每个 Common Address 表示一个协议逻辑站或逻辑分区，不必与一台物理设备一一对应。

---

## 3. 协议栈与 APDU

### 3.1 协议栈

| 层次 | IEC 104 内容 |
|---|---|
| 应用层 | ASDU：遥信、遥测、控制、总召、时钟同步等 |
| 应用规约控制信息 | APCI：I/S/U 格式、序号、STARTDT、STOPDT、TESTFR |
| 传输层 | TCP |
| 网络层 | IP |
| 数据链路/物理层 | Ethernet、光纤、专线、VPN、无线专网等 |

常用 TCP 端口为 `2404`，但工程上也可以配置其他端口。

### 3.2 APDU 的总体结构

IEC 104 在 TCP 中传输 APDU：

```text
APDU = APCI + ASDU
```

完整字节布局：

```text
APDU
├── Start Character       1 byte，固定 0x68
├── APDU Length           1 byte，表示后续 APCI 控制域和 ASDU 的总长度
├── Control Field         4 bytes，I/S/U 格式
└── ASDU                  0..n bytes，仅 I-format 通常携带
```

长度字节不包含最前面的 `0x68` 和长度字节自身。IEC 104 的长度字段为 1 字节，工程上常见最大 APDU 长度为 253 字节，即：

```text
4 字节控制域 + 最多 249 字节 ASDU
```

---

## 4. APCI：I、S、U 格式

### 4.1 I-format：信息传输帧

I-format 用于承载 ASDU。其 4 字节控制域包含发送序号和接收序号：

```text
Byte 0-1：N(S) 左移 1 位后按小端编码
Byte 2-3：N(R) 左移 1 位后按小端编码
```

其中：

- `N(S)`：本端发送的 I-format 序号；
- `N(R)`：本端期望收到的下一个 I-format 序号，也表示已确认收到 `N(R)-1`。

序号使用 15 位有效值，范围为：

```text
0 .. 32767
```

达到最大值后回绕。

### 4.2 S-format：监督确认帧

S-format 不携带 ASDU，只确认接收序号 `N(R)`。

当接收方暂时没有业务 I-format 可以顺带确认时，可以发送 S-format，避免对端因长时间未收到确认而触发超时。

### 4.3 U-format：无编号控制帧

U-format 用于控制数据传输状态和链路测试：

| U-format | 含义 |
|---|---|
| `STARTDT_ACT` | 请求启动数据传输 |
| `STARTDT_CON` | 确认启动数据传输 |
| `STOPDT_ACT` | 请求停止数据传输 |
| `STOPDT_CON` | 确认停止数据传输 |
| `TESTFR_ACT` | 测试帧请求 |
| `TESTFR_CON` | 测试帧确认 |

### 4.4 STARTDT 与应用层 activation 的区别

二者不能混淆：

```text
STARTDT_ACT
```

是 APCI/U-format 层的链路控制，表示允许在当前 TCP 会话上传输 I-format 数据。

```text
COT = activation
```

是 ASDU 应用层语义，表示请求执行总召、遥控、设点、时钟同步等具体操作。

---

## 5. 序号、窗口与定时器

### 5.1 发送窗口 k

`k` 表示发送方在未收到确认前允许连续发送的最大 I-format 数量。

例如：

```text
k = 12
```

表示最多允许 12 个未确认 I-format 在途。达到窗口上限后，发送方应等待对端确认。

### 5.2 接收确认窗口 w

`w` 表示接收方累计接收多少个 I-format 后应主动确认。

通常要求：

```text
w < k
```

典型工程值可能为 `k=12, w=8`，但必须以通信双方的互操作配置为准。

### 5.3 t0、t1、t2、t3

| 定时器 | 典型用途 |
|---|---|
| `t0` | 建立 TCP 连接的超时 |
| `t1` | 等待发送数据确认或命令确认的超时 |
| `t2` | 接收方延迟发送 S-format 确认的最大时间 |
| `t3` | 长时间无业务数据时触发 TESTFR 链路测试 |

常见约束关系：

```text
t2 < t1
```

否则接收方可能尚未发送延迟确认，发送方已经因 `t1` 超时判定失败。

### 5.4 TCP 可靠传输不替代 APCI 序号

TCP 已提供可靠、有序的字节流，但 APCI 的序号仍有重要作用：

- 在应用规约层控制未确认 I-format 窗口；
- 识别和确认应用层数据单元；
- 监测长时间未确认的对端状态；
- 与 IEC 104 的状态机和超时规则配合；
- 实现可预测的流量控制和链路诊断。

---

## 6. ASDU 结构与寻址

### 6.1 ASDU 结构

```text
ASDU
├── Type Identification             1 byte
├── VSQ                             1 byte
├── Cause of Transmission           通常 2 bytes
├── Common Address of ASDU          通常 2 bytes
└── Information Object(s)
    ├── Information Object Address  通常 3 bytes
    └── Information Element(s)      长度由 Type ID 决定
```

IEC 104 常见参数为：

- COT：2 字节；
- Common Address：2 字节；
- IOA：3 字节。

工程实现应以双方约定的应用层参数为准。

### 6.2 点位的协议身份

普通过程数据点通常由以下组合识别：

```text
TCP Connection
+ Common Address
+ Type ID
+ Information Object Address
```

其中：

- TCP 连接确定通信对端；
- Common Address 确定逻辑站；
- Type ID 确定数据编码和信息元素结构；
- IOA 确定站内信息对象地址。

在同一逻辑站中，工程上通常要求 IOA 唯一。某些实现允许同一 IOA 配置不同 Type ID，但会给点表管理和互操作带来歧义，因此不建议依赖这种设计。

### 6.3 Common Address 不是 IP 地址

Common Address 是 ASDU 地址，不等同于：

- IP 地址；
- TCP 端口；
- 设备资产编号；
- Modbus 站号；
- IEC 61850 逻辑节点。

它是 IEC 104 应用层的逻辑站地址。

### 6.4 IOA 不携带业务名称

IEC 104 报文不会传输“风速”“断路器合位”“有功功率”等字段名。双方必须通过点表约定：

```text
CA=1, IOA=1001, Type=M_SP_NA_1  -> 断路器合位
CA=1, IOA=2001, Type=M_ME_NC_1  -> 有功功率 MW
```

单位、比例、量程、死区、遥控关联关系等通常属于工程点表，而不是普通 IEC 104 ASDU 自描述信息。

---

## 7. VSQ、SQ 与批量信息对象

### 7.1 VSQ

VSQ（Variable Structure Qualifier）包含：

- 信息对象数量；
- `SQ` 位。

同一个 ASDU 中的多个信息对象必须共享：

```text
Type ID + COT + Common Address
```

不能在同一个 ASDU 中混合不同 Type ID、不同传送原因或不同 Common Address。

### 7.2 SQ=0：每个对象携带 IOA

```text
ASDU
├── Type ID
├── VSQ: SQ=0, count=3
├── COT
├── CA
├── IOA=1001 + Element
├── IOA=1005 + Element
└── IOA=1020 + Element
```

适用于地址不连续或不适合按序列编码的点。

### 7.3 SQ=1：只传第一个 IOA

```text
ASDU
├── Type ID
├── VSQ: SQ=1, count=3
├── COT
├── CA
├── First IOA=1001
├── Element for IOA=1001
├── Element for IOA=1002
└── Element for IOA=1003
```

适用于同类型、连续地址的信息对象，可减少报文长度。

### 7.4 分组与分帧原则

发送端构造批量 ASDU 时通常按以下顺序处理：

```text
按目标会话分组
→ 按 Common Address 分组
→ 按 Type ID 分组
→ 按 COT 分组
→ 根据 IOA 连续性选择 SQ
→ 根据 APDU 最大长度分帧
```

---

## 8. Type ID 与信息元素

Type ID 决定 Information Element 的编码结构。它不是“点类别名称”，也不表示触发原因。

命名的一般规律：

```text
M_*  监视方向信息（Monitoring）
C_*  控制方向命令（Control）
P_*  参数
F_*  文件传输
```

常见后缀含义：

| 后缀 | 常见含义 |
|---|---|
| `NA` | 不带时标或基础变体 |
| `TA` | 通常带 CP24Time2a |
| `TB` | 在部分类型中为 CP56Time2a 变体 |
| `TC/TD/TE/TF` | 不同数据类型的带时标变体，须以具体 Type ID 定义为准 |

不能仅凭最后一个字母推断所有类型，必须查 Type ID 表。

### 8.1 常见监视类型

| Type ID | 数值 | 含义 |
|---|---:|---|
| `M_SP_NA_1` | 1 | 单点信息，不带时标 |
| `M_DP_NA_1` | 3 | 双点信息，不带时标 |
| `M_ST_NA_1` | 5 | 步位置信息 |
| `M_BO_NA_1` | 7 | 32 位比特串 |
| `M_ME_NA_1` | 9 | 归一化测量值 |
| `M_ME_NB_1` | 11 | 标度化测量值 |
| `M_ME_NC_1` | 13 | 短浮点测量值 |
| `M_IT_NA_1` | 15 | 累计量 |
| `M_SP_TB_1` | 30 | 单点信息，CP56Time2a |
| `M_DP_TB_1` | 31 | 双点信息，CP56Time2a |
| `M_ME_TF_1` | 36 | 短浮点测量值，CP56Time2a |
| `M_IT_TB_1` | 37 | 累计量，CP56Time2a |
| `M_EI_NA_1` | 70 | 初始化结束 |

### 8.2 常见控制和系统类型

| Type ID | 数值 | 含义 |
|---|---:|---|
| `C_SC_NA_1` | 45 | 单点命令 |
| `C_DC_NA_1` | 46 | 双点命令 |
| `C_RC_NA_1` | 47 | 步调节命令 |
| `C_SE_NA_1` | 48 | 归一化设点命令 |
| `C_SE_NB_1` | 49 | 标度化设点命令 |
| `C_SE_NC_1` | 50 | 短浮点设点命令 |
| `C_BO_NA_1` | 51 | 32 位比特串命令 |
| `C_IC_NA_1` | 100 | 总召/组召命令 |
| `C_CI_NA_1` | 101 | 累计量召唤命令 |
| `C_RD_NA_1` | 102 | 读命令 |
| `C_CS_NA_1` | 103 | 时钟同步命令 |
| `C_TS_NA_1` | 104 | 测试命令 |
| `C_RP_NA_1` | 105 | 复位进程命令 |
| `C_CD_NA_1` | 106 | 延时获取命令 |
| `C_TS_TA_1` | 107 | 带时标测试命令 |

### 8.3 Type ID 不等于 COT

以下三个报文可以使用同一个 Type ID：

```text
M_ME_NC_1 + COT=CYCLIC
M_ME_NC_1 + COT=SPONTANEOUS
M_ME_NC_1 + COT=INTERROGATED_BY_STATION
```

它们的信息元素编码相同，但发送原因不同。

---

## 9. COT：传送原因

COT（Cause of Transmission）说明 ASDU 为什么被发送。

### 9.1 常见 COT

| COT | 含义 |
|---|---|
| `PERIODIC` / cyclic | 周期传送 |
| `BACKGROUND_SCAN` | 背景扫描 |
| `SPONTANEOUS` | 自发传送 |
| `INITIALIZED` | 初始化 |
| `REQUEST` | 请求响应，如读命令 |
| `ACTIVATION` | 激活命令 |
| `ACTIVATION_CON` | 激活确认 |
| `DEACTIVATION` | 停止激活 |
| `DEACTIVATION_CON` | 停止激活确认 |
| `ACTIVATION_TERMINATION` | 激活终止 |
| `INTERROGATED_BY_STATION` | 站总召响应 |
| `INTERROGATED_BY_GROUP_1..16` | 组召响应 |
| `REQUESTED_BY_GENERAL_COUNTER` | 一般累计量召唤响应 |
| `RETURN_INFO_REMOTE` | 远方命令返回信息 |
| `UNKNOWN_TYPE_ID` | 未知 Type ID |
| `UNKNOWN_COT` | 未知 COT |
| `UNKNOWN_CA` | 未知 Common Address |
| `UNKNOWN_IOA` | 未知 IOA |

### 9.2 COT 的附加位

COT 字段除原因值外，通常还包含：

- `PN`：Positive/Negative，正确认或负确认；
- `T`：Test，测试标志；
- Originator Address：源发地址，用于区分控制站或命令来源。

因此不能只把 COT 当作一个简单枚举值。

### 9.3 命令处理的典型 COT 序列

```text
控制站 -> 被控站：ACTIVATION
被控站 -> 控制站：ACTIVATION_CON，PN=0 或 PN=1
被控站 -> 控制站：ACTIVATION_TERMINATION（按命令类型和实现需要）
```

负确认只表示协议命令未被接受或执行失败。工程系统还应提供更细的业务错误日志。

---

## 10. QOI、QCC、QOC 等限定词

限定词不是所有 ASDU 的公共字段，而是特定 Type ID 的信息元素。

### 10.1 QOI：召唤限定词

QOI 位于 `C_IC_NA_1` 的信息体中：

| QOI | 含义 |
|---:|---|
| 20 | 站总召 |
| 21..36 | 第 1..16 组召 |

召唤命令：

```text
Type ID = C_IC_NA_1
COT = ACTIVATION
IOA = 0
QOI = 20 或 21..36
```

召唤返回的遥信、遥测 ASDU 不再携带 QOI，而是通过 COT 表示：

```text
QOI=20  -> COT=INTERROGATED_BY_STATION
QOI=21  -> COT=INTERROGATED_BY_GROUP_1
...
QOI=36  -> COT=INTERROGATED_BY_GROUP_16
```

### 10.2 QCC：累计量召唤限定词

累计量召唤 `C_CI_NA_1` 的限定词通常由两部分组成：

- RQT：请求哪一组累计量；
- FRZ：读取、冻结、冻结并复位或复位等操作。

典型组合：

```text
RQT = GENERAL
FRZ = READ
```

表示读取一般累计量而不冻结、不复位。

### 10.3 QOC：命令限定词

单点、双点和步调节命令中可包含 QOC，用于表达：

- 短脉冲；
- 长脉冲；
- 持续输出；
- Select/Execute 标志。

### 10.4 SBO：选择后执行

Select Before Operate 的典型过程：

```text
控制站 -> 被控站：SELECT
被控站 -> 控制站：SELECT CONFIRM
控制站 -> 被控站：EXECUTE
被控站 -> 控制站：EXECUTE CONFIRM
被控站 -> 控制站：ACTIVATION TERMINATION
```

被控站应对选择保持超时、发起者、IOA、命令值和命令类型进行校验，防止其他会话错误执行已选择命令。

---

## 11. 质量描述符和时标

### 11.1 质量描述符

监视信息通常携带质量位。常见质量状态：

| 质量 | 含义 |
|---|---|
| Invalid | 无效 |
| Non-topical | 非当前值、过期 |
| Substituted | 被替代 |
| Blocked | 被闭锁 |
| Overflow | 溢出，适用于部分测量类型 |

“质量良好”通常是所有异常质量位均未置位，而不是单独传输一个 `GOOD` 位。

### 11.2 质量与链路状态是不同概念

TCP 连接正常不代表过程值有效：

- 上游传感器可能断线；
- 数据可能长期未刷新；
- 数值可能被人工替代；
- 设备可能处于检修闭锁状态。

主站应结合：

```text
链路状态 + 质量位 + 时标 + 最后刷新时间 + 业务刷新周期
```

判断数据是否可用。

### 11.3 CP24Time2a、CP56Time2a 和 CP16Time2a

| 时标 | 主要内容 |
|---|---|
| CP16Time2a | 毫秒级短时间值，常用于持续时间或延时 |
| CP24Time2a | 毫秒、分钟等短时标，不包含完整日期 |
| CP56Time2a | 毫秒、分钟、小时、日、月、年等完整时标 |

常见带 CP56Time2a 的类型：

| 不带完整时标 | 带 CP56Time2a |
|---|---|
| `M_SP_NA_1` | `M_SP_TB_1` |
| `M_DP_NA_1` | `M_DP_TB_1` |
| `M_ME_NC_1` | `M_ME_TF_1` |
| `M_IT_NA_1` | `M_IT_TB_1` |

是否带时标由 Type ID 决定，不应再增加一个与 Type ID 相冲突的“timestamp_enabled”协议字段。

---

## 12. 主要业务流程

### 12.1 建链与启动数据传输

```text
1. 控制站建立 TCP 连接
2. 控制站发送 STARTDT_ACT
3. 被控站返回 STARTDT_CON
4. 双方进入允许传输 I-format 的状态
5. 控制站通常发起总召或时钟同步
```

TCP 建立成功不等于 IEC 104 数据传输已经启动。

### 12.2 站总召

```text
控制站 -> 被控站：C_IC_NA_1, COT=ACTIVATION, QOI=20
被控站 -> 控制站：C_IC_NA_1, COT=ACTIVATION_CON
被控站 -> 控制站：监视 ASDU, COT=INTERROGATED_BY_STATION
被控站 -> 控制站：C_IC_NA_1, COT=ACTIVATION_TERMINATION
```

总召是一次性当前值快照请求，不是订阅。

### 12.3 组召

```text
QOI = 21..36
```

表示第 1..16 组召唤。哪些点属于哪一组由被控站点表配置决定。标准不要求各组互斥，一个点可以属于多个组。

### 12.4 累计量召唤

```text
控制站 -> 被控站：C_CI_NA_1, COT=ACTIVATION, QCC
被控站 -> 控制站：ACTIVATION_CON
被控站 -> 控制站：M_IT_*, COT=REQUESTED_BY_GENERAL_COUNTER 或组累计量 COT
被控站 -> 控制站：ACTIVATION_TERMINATION
```

累计量召唤与普通总召是两个不同的系统命令路径。

### 12.5 单点读

`C_RD_NA_1` 用于请求一个指定 IOA 的当前值。

典型响应使用：

```text
COT = REQUEST
```

读命令不是 Modbus 式持续轮询机制，而是 IEC 104 提供的单个信息对象请求能力。

### 12.6 时钟同步

控制站使用 `C_CS_NA_1` 向被控站发送 CP56Time2a。

工程实现应考虑：

- 时区约定；
- UTC 与本地时间转换；
- 夏令时位；
- 时钟跳变限制；
- 是否允许远方直接修改操作系统时钟；
- 与 NTP/PTP 的职责关系。

### 12.7 自发上送

当点值或状态发生有效变化时，被控站主动发送：

```text
COT = SPONTANEOUS
```

模拟量通常还需要：

- 绝对死区；
- 相对死区；
- 最小发送间隔；
- 最大静默时间；
- 抖动过滤。

这些策略属于应用和设备配置，不由 Type ID 自动定义。

### 12.8 周期上送

被控站按配置周期发送当前值：

```text
COT = PERIODIC / CYCLIC
```

周期上送不需要先由总召“建立订阅”。

### 12.9 背景扫描

背景扫描通常表示低优先级、低频率的当前值刷新：

```text
COT = BACKGROUND_SCAN
```

它不是自发变化上送，也不是总召响应。

### 12.10 初始化结束

子站启动或复位后可发送：

```text
M_EI_NA_1
```

控制站收到初始化结束后，通常应重新执行总召，以恢复一致的当前值视图。

### 12.11 遥控和遥调

控制命令通常包括：

- 单点命令；
- 双点命令；
- 步调节命令；
- 归一化、标度化和短浮点设点；
- 直接执行或 SBO。

命令点和状态反馈点应视为两个不同的信息对象。例如：

```text
C_DC_NA_1, IOA=5001  -> 断路器分合命令
M_DP_NA_1, IOA=1001  -> 断路器实际位置反馈
```

命令确认成功不等于设备已经达到目标状态。最终状态应由监视点反馈。

---

## 13. 总召、周期、自发和背景传送的关系

同一个监视点可以通过多种机制发送：

```text
收到总召       -> COT=INTERROGATED_BY_STATION
收到组召       -> COT=INTERROGATED_BY_GROUP_n
周期到达       -> COT=PERIODIC
值变化有效     -> COT=SPONTANEOUS
背景刷新到达   -> COT=BACKGROUND_SCAN
收到单点读     -> COT=REQUEST
```

这些机制互不排斥。

| 机制 | 发起方 | 触发条件 | 是否持续 |
|---|---|---|---|
| 站总召 | 控制站 | QOI=20 | 一次流程 |
| 组召 | 控制站 | QOI=21..36 | 一次流程 |
| 单点读 | 控制站 | 指定 CA+IOA | 一次流程 |
| 周期传送 | 被控站 | 周期到达 | 持续 |
| 自发传送 | 被控站 | 变化满足条件 | 持续 |
| 背景扫描 | 被控站 | 后台周期到达 | 持续 |

错误理解：

```text
“总召之后子站才开始持续推送”
```

正确理解：

```text
总召只返回一次快照；后续是否主动发送由周期、自发和背景策略决定。
```

---

## 14. 点表与互操作约定

### 14.1 点表至少应说明

| 项目 | 说明 |
|---|---|
| Common Address | 逻辑站地址 |
| IOA | 信息对象地址 |
| Type ID | 编码类型 |
| 业务名称 | 中文名、英文名或标签 |
| 单位 | MW、kV、Hz 等 |
| 值域 | 最小值、最大值、枚举值 |
| 换算 | 原始值与工程值关系 |
| 质量处理 | 数据无效、过期、替代规则 |
| 时标 | 是否使用带时标 Type ID |
| 发送机制 | 总召、组召、周期、自发、背景、读 |
| 控制模式 | 直接或 SBO |
| 命令反馈 | 对应的监视点 |

### 14.2 不应把 COT 固定成点属性

同一个点可因不同业务触发而使用不同 COT。因此点表可记录“允许哪些发送机制”，但不应把一个监视点永久绑定为单一 COT。

### 14.3 监视点与控制点分离

一般规则：

- `M_*` 用于监视方向；
- `C_*` 用于控制方向；
- 控制命令和状态反馈使用两个独立点；
- 控制点不参与普通监视点总召；
- 累计量应使用累计量召唤规则，而不是假定所有 `M_*` 都进入普通总召。

### 14.4 互操作必须测试而不能只看标准

需要测试：

- 字节长度参数；
- Common Address 范围；
- IOA 范围；
- 支持的 Type ID；
- 总召和组召范围；
- 累计量召唤冻结语义；
- 命令确认和终止顺序；
- SBO 超时；
- 时标解释；
- 质量位；
- k/w 和 t0/t1/t2/t3；
- 多点 ASDU 的 SQ 编码；
- 负确认和未知地址处理。

---

## 15. 重连、多主站、异常与安全

### 15.1 重连

控制站断线重连后通常应：

```text
重新建立 TCP
→ STARTDT
→ 必要时执行时钟同步
→ 重新总召
→ 恢复控制和监视业务
```

不能假设断线前的最后值仍然有效。

### 15.2 被控站重启

被控站重启后建议：

```text
加载点表
→ 初始化当前值缓存和质量
→ 启动监听
→ 接受 STARTDT
→ 发送初始化结束
→ 等待控制站总召
```

### 15.3 多主站连接

每个 TCP session 应独立维护：

- N(S)、N(R)；
- STARTDT/STOPDT 状态；
- t0/t1/t2/t3；
- k/w 窗口；
- SBO 选择上下文；
- 命令发起者和源发地址；
- 总召响应上下文。

主站 A 发起总召，响应原则上应发送给主站 A，而不是无条件广播给所有连接。

### 15.4 异常 ASDU

被控站应识别并适当响应：

- 未知 Type ID；
- 未知 COT；
- 未知 Common Address；
- 未知 IOA；
- 不允许的控制方向；
- 错误的 Select/Execute 顺序；
- 值域超限；
- 命令闭锁；
- 不支持的限定词。

### 15.5 安全

传统 IEC 104 本身通常不提供足够的现代身份认证和加密能力。工程部署不应把 TCP `2404` 直接暴露到不可信网络。

建议：

- 使用专网、VPN、安全网关或 TLS；
- 使用源 IP 白名单和双向证书；
- 网络分区和最小权限；
- 对遥控遥调增加权限、闭锁和防误逻辑；
- 记录完整命令审计日志；
- 限制频繁总召、暴力重连和异常命令；
- 对远程时钟同步设置安全策略；
- 对协议库和依赖项进行版本及漏洞管理。

---

## 16. 完整报文拆解示例

报文：

```text
68 0E 02 00 00 00 01 01 03 00 01 00 E9 03 00 01
```

拆解如下：

```text
68          Start Character
0E          APDU Length = 14 bytes

02 00       N(S) 编码值 0x0002 -> N(S)=1
00 00       N(R) 编码值 0x0000 -> N(R)=0

01          Type ID = 1 = M_SP_NA_1
01          VSQ = SQ=0, 信息对象数量=1
03 00       COT = 3 = SPONTANEOUS
01 00       Common Address = 1
E9 03 00    IOA = 1001，小端 3 字节
01          SIQ：单点状态 ON，质量位正常
```

语义：

```text
逻辑站 CA=1 自发上送 IOA=1001 的单点状态，当前值为 ON。
```

---

# 第二部分：`iec104-python` 实践

## 17. 包定位、安装与架构

### 17.1 包名与导入名

项目名称：

```text
iec104-python
```

PyPI 包名和 Python 导入名：

```text
c104
```

安装：

```bash
python -m pip install c104
```

建议锁定版本：

```bash
python -m pip install "c104==2.2.1"
```

### 17.2 包定位

`iec104-python` 提供面向对象的高级 Python API，用于实现或模拟：

- SCADA/控制站；
- RTU/被控站；
- IEC 104 互操作测试程序；
- 协议仿真和研究工具。

它不是纯 Python 协议栈。其结构大致为：

```text
Python 应用
    ↓
c104 Python API
    ↓
pybind11 C++ 绑定与状态封装
    ↓
lib60870-C
    ↓
TCP/IP
```

包还集成了与传输安全有关的能力，并公开 `TransportSecurity` 对象。

### 17.3 许可证

`iec104-python` 和其核心 IEC 104 依赖采用 GPLv3。将其用于闭源商业产品前，应由法律或合规人员确认 GPLv3 对分发、链接、修改和源码提供义务的影响。

### 17.4 版本说明

本文使用 `c104 2.2.1` 的 API 形式。不同版本可能改变：

- Python 版本支持；
- 可注册 Type ID；
- 总召和累计量召唤行为；
- ProtocolParameters；
- TLS 支持；
- Batch API；
- 回调签名和类型提示。

---

## 18. 对象模型

### 18.1 被控站对象模型

```text
Server
└── Station（Common Address）
    └── Point（IOA + Type ID）
```

示例：

```python
import c104

server = c104.Server(ip="0.0.0.0", port=2404)
station = server.add_station(common_address=47)
point = station.add_point(
    io_address=11,
    type=c104.Type.M_ME_NC_1,
    report_ms=5000,
)
server.start()
```

### 18.2 控制站对象模型

```text
Client
└── Connection（远端 IP + Port）
    └── Station（远端 Common Address）
        └── Point（远端 IOA + Type ID）
```

示例：

```python
import c104

client = c104.Client()
connection = client.add_connection(
    ip="127.0.0.1",
    port=2404,
    init=c104.Init.INTERROGATION,
)
station = connection.add_station(common_address=47)
point = station.add_point(
    io_address=11,
    type=c104.Type.M_ME_NC_1,
)
client.start()
```

### 18.3 本地 Station 和远端 Station

- `Server.add_station()` 创建本地被控站；
- `Connection.add_station()` 描述远端被控站；
- `Station.add_point()` 在不同上下文中分别创建本地过程点或远端映射点；
- 某些方法只允许在 Server 或 Client 一侧调用，错误上下文会抛出异常。

---

## 19. 协议概念与对象映射

| IEC 104 概念 | `c104` 对象/属性 |
|---|---|
| 控制站 | `c104.Client` |
| 控制站到被控站的连接 | `c104.Connection` |
| 被控站监听服务 | `c104.Server` |
| Common Address | `c104.Station.common_address` |
| IOA | `c104.Point.io_address` |
| Type ID | `c104.Point.type` / `c104.Type` |
| 当前值 | `c104.Point.value` / `Point.info.value` |
| 质量 | `c104.Point.quality` |
| 传输时标 | `c104.Point.recorded_at` |
| 周期发送 | `c104.Point.report_ms` |
| 直接/SBO | `c104.Point.command_mode` |
| 命令关联监视点 | `related_io_address` |
| 自动返回关联点 | `related_io_autoreturn` |
| 总召 | `Connection.interrogation()` |
| 累计量召唤 | `Connection.counter_interrogation()` |
| 单点读 | `Point.read()` |
| 时钟同步 | `Connection.clock_sync()` |
| 主动传输/命令 | `Point.transmit()` |
| 批量监视传输 | `c104.Batch` + `Server.transmit_batch()` |
| k/w/t 定时器 | `ProtocolParameters` |
| TLS | `TransportSecurity` |

---

## 20. 包提供的主要能力

`c104 2.2.x` 的公开 API 提供：

- Client 和 Server；
- 多 Connection、多 Station、多 Point；
- 控制站自动连接和重连；
- STARTDT 等链路状态管理；
- 总召发送；
- 累计量召唤发送；
- 单点读；
- 时钟同步；
- 测试命令；
- 监视点周期发送；
- 监视点主动发送；
- 控制命令发送；
- Direct 和 Select-and-Execute；
- 命令回调和确认结果；
- 关联监视点自动返回；
- 原始收发报文回调；
- 连接状态回调；
- 未预期报文回调；
- 初始化结束通知；
- Batch 批量监视传输；
- 协议参数读写；
- TLS 配置；
- 类型化 Information 对象和质量枚举。

---

## 21. 版本相关限制

本节描述的是包实现边界，不是 IEC 104 标准边界。

### 21.1 枚举存在不等于 Server 完整实现

包公开 `Qoi.GROUP_1..GROUP_16`、多个 COT 和全部常见 Type 枚举，但必须区分：

```text
枚举可表示
≠ Client 能发送
≠ Server 能自动处理
≠ Point 能注册
≠ 能进入总召
≠ 支持 report_ms
```

不能仅根据枚举存在推断完整协议能力。

### 21.2 站总召与组召

`Connection.interrogation()` 的 Client API 接受 `c104.Qoi`。但在未修改的特定版本中，Server 自动响应路径对站总召和组召的支持可能不对称。

对 `2.2.1` 的工程使用应按以下原则验证：

1. `QOI=STATION` 的自动响应行为；
2. `QOI=GROUP_1..16` 是否真正返回配置的组点集；
3. 组召点归属如何配置；
4. 不支持时是否返回负确认；
5. 升级版本后是否改变。

原始合并材料对未修改 Server 的源码分析结果是：自动普通召唤主要面向 `QOI=20` 的站总召，未提供一个公开的“Point 组召成员”属性。因此，即使 Client 能发送组 QOI，也不能假定可以只靠公开 Point API 配置 16 个组召点集。

需要多个独立总召范围时，可选择：

- 使用多个 Common Address/Station；
- 修改或扩展协议栈；
- 在应用层实现自定义召唤处理，但必须避免与内置处理重复响应。

### 21.3 Point 注册类型限制

并非 `c104.Type` 中的每个 Type ID 都能通过 `Station.add_point()` 注册为普通 Point。

尤其要注意：

- 部分 CP24Time2a 类型可能只保留为枚举，不可注册；
- 系统命令 Type ID 不是普通 Point；
- 初始化结束由专用方法触发；
- 总召、累计量召唤和时钟同步由 Connection/Station 专用 API 处理；
- 文件传输和参数类能力不能根据 Type 枚举自行假定。

### 21.4 总召点类型限制

“能注册为监视 Point”不等于“能进入普通站总召”。

原始材料针对 `2.2.1` 的实现分析中，普通站总召重点覆盖：

```text
1, 3, 5, 7, 9, 11, 13, 30..36
```

即单点、双点、步位置、比特串以及测量值的常用无时标/CP56Time2a 类型。

累计量：

```text
M_IT_NA_1, M_IT_TB_1
```

应按累计量召唤路径处理，而不是默认并入普通总召。

### 21.5 `report_ms` 不是通用定时器

`report_ms` 表示 Server 周期传输监视点：

```text
report_ms = 0     不启用自动周期传输
report_ms > 0     按间隔自动传输
```

它不等于：

- 自发变化检测；
- 后台全点扫描；
- Client 轮询周期；
- `Point.on_timer()` 的 `timer_ms`。

### 21.6 包不自动完成通用死区逻辑

主动自发上送通常需要应用维护：

- 上次采样值；
- 上次自发发送值；
- 上次发送时间；
- 死区；
- 最小发送间隔；
- 最大静默时间。

更新 `point.value` 本身不应被假定为一定产生 `SPONTANEOUS` 报文。需要显式调用：

```python
point.transmit(cause=c104.Cot.SPONTANEOUS)
```

### 21.7 自动总召处理与自定义处理不能重复

如果包已经自动处理某个召唤命令，不应再在应用中发送第二套：

```text
ACTIVATION_CON
+ 数据 ASDU
+ ACTIVATION_TERMINATION
```

否则会发生重复响应、序号异常或点集不一致。

### 21.8 多主站策略需要显式设计

Server 可以允许多个连接，但应用仍应明确：

- 哪些主站允许连接；
- 是否都能遥控；
- 自发和周期数据是否广播；
- `originator` 如何使用；
- SBO 选择是否按会话隔离；
- 总召响应是否仅返回给请求会话；
- 连接上限和安全策略。

---

## 22. 子站 Server 完整示例

下面的示例展示：

- 一个 Server；
- 一个 Station；
- 一个周期测量点；
- 一个单点状态；
- 一个设点命令；
- 读前刷新；
- 周期发送前刷新；
- 命令回调；
- 自发发送；
- 安全停止。

```python
from __future__ import annotations

import random
import threading
import time
from typing import Final

import c104

HOST: Final = "0.0.0.0"
PORT: Final = 2404
COMMON_ADDRESS: Final = 47


def refresh_measurement(point: c104.Point) -> None:
    """在总召、单点读或自动周期发送前刷新当前值。"""
    point.value = round(random.uniform(45.0, 55.0), 3)


def handle_setpoint(
    point: c104.Point,
    previous_info: c104.Information,
    message: c104.IncomingMessage,
) -> c104.ResponseState:
    """处理主站下发的短浮点设点命令。"""
    try:
        requested = float(point.value)
        if not 0.0 <= requested <= 100.0:
            print(f"Reject setpoint {requested}: out of range")
            return c104.ResponseState.FAILURE

        print(
            "Accept setpoint:",
            f"ioa={point.io_address}",
            f"new={requested}",
            f"previous={previous_info.value}",
            f"cot={message.cot}",
        )
        return c104.ResponseState.SUCCESS
    except (TypeError, ValueError) as exc:
        print(f"Invalid command: {exc}")
        return c104.ResponseState.FAILURE


def build_server() -> tuple[c104.Server, c104.Point, c104.Point]:
    server = c104.Server(
        ip=HOST,
        port=PORT,
        tick_rate_ms=100,
        max_connections=2,
    )

    station = server.add_station(common_address=COMMON_ADDRESS)
    if station is None:
        raise RuntimeError("Failed to create station")

    frequency = station.add_point(
        io_address=1001,
        type=c104.Type.M_ME_NC_1,
        report_ms=5000,
    )
    breaker_closed = station.add_point(
        io_address=1002,
        type=c104.Type.M_SP_NA_1,
        report_ms=0,
    )
    setpoint = station.add_point(
        io_address=5001,
        type=c104.Type.C_SE_NC_1,
        command_mode=c104.CommandMode.SELECT_AND_EXECUTE,
        related_io_address=frequency.io_address,
        related_io_autoreturn=True,
    )

    frequency.value = 50.0
    breaker_closed.value = True

    frequency.on_before_read(callable=refresh_measurement)
    frequency.on_before_auto_transmit(callable=refresh_measurement)
    setpoint.on_receive(callable=handle_setpoint)

    return server, frequency, breaker_closed


def main() -> None:
    server, frequency, breaker_closed = build_server()
    stop_event = threading.Event()

    try:
        server.start()
        print(f"IEC 104 server listening on {HOST}:{PORT}")

        # 演示：应用检测到开关状态变化后自发上送。
        time.sleep(2.0)
        breaker_closed.value = False
        breaker_closed.transmit(cause=c104.Cot.SPONTANEOUS)

        # 主线程阻塞，Ctrl+C 后退出；不是忙等待。
        stop_event.wait()
    except KeyboardInterrupt:
        print("Stopping server...")
    finally:
        server.stop()


if __name__ == "__main__":
    main()
```

### 22.1 示例中的职责

| 行为 | 实现位置 |
|---|---|
| 周期触发 | `report_ms=5000` |
| 周期发送前获取值 | `on_before_auto_transmit` |
| 总召/读前获取值 | `on_before_read` |
| 自发发送 | `Point.transmit(Cot.SPONTANEOUS)` |
| 遥调命令校验 | `Point.on_receive` |
| SBO | `command_mode=SELECT_AND_EXECUTE` |
| 命令反馈关联点 | `related_io_address` |

---

## 23. 主站 Client 完整示例

```python
from __future__ import annotations

import threading

import c104

REMOTE_IP = "127.0.0.1"
REMOTE_PORT = 2404
COMMON_ADDRESS = 47


def on_connection_state(
    connection: c104.Connection,
    state: c104.ConnectionState,
) -> None:
    print(f"Connection {connection.ip}:{connection.port} -> {state}")


def on_receive_raw(connection: c104.Connection, data: bytes) -> None:
    print(
        "RX",
        connection.ip,
        connection.port,
        data.hex(" "),
        c104.explain_bytes(apdu=data),
    )


def on_point_receive(
    point: c104.Point,
    previous_info: c104.Information,
    message: c104.IncomingMessage,
) -> c104.ResponseState:
    print(
        "POINT UPDATE",
        f"ca={point.station.common_address if point.station else None}",
        f"ioa={point.io_address}",
        f"type={point.type}",
        f"value={point.value}",
        f"previous={previous_info.value}",
        f"quality={point.quality}",
        f"recorded_at={point.recorded_at}",
        f"cot={message.cot}",
    )
    return c104.ResponseState.SUCCESS


def build_client() -> tuple[c104.Client, c104.Connection, c104.Point, c104.Point]:
    client = c104.Client(
        tick_rate_ms=100,
        command_timeout_ms=5000,
    )

    connection = client.add_connection(
        ip=REMOTE_IP,
        port=REMOTE_PORT,
        init=c104.Init.NONE,
    )
    if connection is None:
        raise RuntimeError("Failed to create connection")

    connection.on_state_change(callable=on_connection_state)
    connection.on_receive_raw(callable=on_receive_raw)

    station = connection.add_station(common_address=COMMON_ADDRESS)
    if station is None:
        raise RuntimeError("Failed to create remote station")

    frequency = station.add_point(
        io_address=1001,
        type=c104.Type.M_ME_NC_1,
    )
    breaker_closed = station.add_point(
        io_address=1002,
        type=c104.Type.M_SP_NA_1,
    )
    setpoint = station.add_point(
        io_address=5001,
        type=c104.Type.C_SE_NC_1,
        command_mode=c104.CommandMode.SELECT_AND_EXECUTE,
    )

    frequency.on_receive(callable=on_point_receive)
    breaker_closed.on_receive(callable=on_point_receive)

    return client, connection, frequency, setpoint


def main() -> None:
    client, connection, frequency, setpoint = build_client()
    stop_event = threading.Event()

    try:
        # Client.start() 会启动客户端并连接所有已配置的 Connection。
        client.start()

        # 实际应用应等待 connection.is_connected 或状态回调进入 OPEN。
        if not connection.interrogation(
            common_address=COMMON_ADDRESS,
            cause=c104.Cot.ACTIVATION,
            qualifier=c104.Qoi.STATION,
        ):
            print("General interrogation was not sent")

        if not frequency.read():
            print("Read command failed")

        setpoint.value = 52.0
        if not setpoint.transmit(cause=c104.Cot.ACTIVATION):
            print("Setpoint command failed")

        stop_event.wait()
    except KeyboardInterrupt:
        print("Stopping client...")
    finally:
        client.stop()


if __name__ == "__main__":
    main()
```

### 23.1 关于连接等待

`Client.start()` 会启动客户端后台线程，并连接已配置的全部 `Connection`；`Connection.connect()` 可用于单独发起某条连接。生产代码不应在未确认连接进入开放状态前立即发送命令。

可使用：

- `connection.on_state_change()`；
- `connection.is_connected`；
- 带超时的 `threading.Event`；
- 应用自己的连接状态机。

不要使用无休止的高频忙循环。

---

## 24. 总召、读、累计量召唤与时钟同步

### 24.1 站总召

```python
ok = connection.interrogation(
    common_address=47,
    cause=c104.Cot.ACTIVATION,
    qualifier=c104.Qoi.STATION,
    wait_for_response=True,
)
```

`True` 主要表示命令发送路径可用或操作被接受。仍应通过点回调、原始报文和日志检查实际响应点集。

### 24.2 组召

```python
ok = connection.interrogation(
    common_address=47,
    qualifier=c104.Qoi.GROUP_1,
)
```

Client API 允许表达组 QOI，但必须确认远端 Server 或设备是否实现组召，以及组点如何配置。

### 24.3 单点读

```python
ok = measurement_point.read()
```

只允许在 Client 侧远端 Point 上调用。

### 24.4 一般累计量召唤

```python
ok = connection.counter_interrogation(
    common_address=47,
    cause=c104.Cot.ACTIVATION,
    qualifier=c104.Rqt.GENERAL,
    freeze=c104.Frz.READ,
    wait_for_response=True,
)
```

累计量冻结或复位可能产生设备业务影响。在不了解设备实现时，不应随意使用：

```python
c104.Frz.COUNTER_RESET
c104.Frz.FREEZE_WITH_RESET
```

### 24.5 时钟同步

```python
ok = connection.clock_sync(
    common_address=47,
    wait_for_response=True,
)
```

该 API 使用控制站操作系统时间。调用前应确认时区、系统时钟源和远端授权策略。

---

## 25. 周期、自发和后台发送

### 25.1 周期发送

```python
point = station.add_point(
    io_address=1001,
    type=c104.Type.M_ME_NC_1,
    report_ms=5000,
)
```

配合：

```python
def refresh(point: c104.Point) -> None:
    point.value = read_sensor()

point.on_before_auto_transmit(callable=refresh)
```

### 25.2 自发发送

```python
point.value = new_value
point.transmit(cause=c104.Cot.SPONTANEOUS)
```

一个通用的死区状态对象：

```python
from dataclasses import dataclass
from time import monotonic


@dataclass
class SpontaneousState:
    last_sent_value: float | None = None
    last_sent_at: float = 0.0


def maybe_send_spontaneous(
    point: c104.Point,
    state: SpontaneousState,
    new_value: float,
    deadband: float,
    min_interval_s: float,
) -> bool:
    now = monotonic()

    if state.last_sent_value is None:
        state.last_sent_value = new_value
        return False

    if abs(new_value - state.last_sent_value) < deadband:
        return False

    if now - state.last_sent_at < min_interval_s:
        return False

    point.value = new_value
    sent = point.transmit(cause=c104.Cot.SPONTANEOUS)
    if sent:
        state.last_sent_value = new_value
        state.last_sent_at = now
    return sent
```

### 25.3 背景发送

包没有一个等同于“所有点按后台策略自动扫描”的统一高层概念。应用可以定期遍历选定点并发送：

```python
for point in background_points:
    point.value = read_value(point.io_address)
    point.transmit(cause=c104.Cot.BACKGROUND_SCAN)
```

注意不要同时使用同一周期配置 `report_ms` 和应用背景扫描，否则可能重复发送。

### 25.4 `on_timer()` 与 `report_ms`

```text
report_ms
```

控制自动周期传输。

```text
Point.on_timer(..., interval_ms=...)
```

只是周期调用 Python 回调。回调中是否发送由应用决定。

---

## 26. 遥控与设点命令

### 26.1 Client 发送命令

```python
command_point.value = True
ok = command_point.transmit(cause=c104.Cot.ACTIVATION)
```

短浮点设点：

```python
setpoint.value = 12.5
ok = setpoint.transmit(cause=c104.Cot.ACTIVATION)
```

### 26.2 Server 命令回调

```python
def on_command(
    point: c104.Point,
    previous_info: c104.Information,
    message: c104.IncomingMessage,
) -> c104.ResponseState:
    if not is_authorized(message.originator_address):
        return c104.ResponseState.FAILURE

    if not write_device(point.io_address, point.value):
        return c104.ResponseState.FAILURE

    return c104.ResponseState.SUCCESS

command_point.on_receive(callable=on_command)
```

### 26.3 直接命令与 SBO

```python
command_mode=c104.CommandMode.DIRECT
```

或：

```python
command_mode=c104.CommandMode.SELECT_AND_EXECUTE
```

关键安全校验不应只依赖协议栈：

- 当前运行方式是否允许远控；
- 操作票或权限；
- 设备联锁；
- 值域；
- 选择保持超时；
- 命令来源；
- 重复命令去重；
- 控制失败后的状态确认。

### 26.4 关联监视点

```python
command_point = station.add_point(
    io_address=5001,
    type=c104.Type.C_SE_NC_1,
    related_io_address=1001,
    related_io_autoreturn=True,
)
```

这有助于命令成功后返回关联监视信息，但不能替代真实设备反馈。应用仍应从设备读取最终状态，并更新监视点。

---

## 27. 批量传输、原始报文与调试

### 27.1 Batch

`c104.Batch` 与 `Server.transmit_batch()` 可用于同一 Common Address、Type ID 和 COT 下的批量监视传输。

批量发送应满足协议约束：

```text
同一 Common Address
同一 Type ID
同一 COT
```

连续 IOA 可考虑 sequence 方式，不连续 IOA 使用非 sequence 方式。

### 27.2 原始报文回调

Client Connection：

```python
def on_receive_raw(connection: c104.Connection, data: bytes) -> None:
    print(data.hex(" "))
    print(c104.explain_bytes(apdu=data))

connection.on_receive_raw(callable=on_receive_raw)
```

Server 也提供原始收发回调。原始回调适合：

- 对照抓包；
- 分析序号；
- 验证 COT；
- 定位未知 Type/CA/IOA；
- 检查总召确认和终止；
- 自动化互操作测试。

不要在高频原始回调中执行阻塞 I/O 或复杂业务。

### 27.3 Wireshark

建议同时使用 Wireshark 的 IEC 104 解析：

```text
tcp.port == 2404
```

检查：

- STARTDT；
- N(S)/N(R)；
- S-format 确认；
- t1/t2/t3 行为；
- Type ID；
- COT；
- CA 和 IOA；
- QOI/QCC；
- 激活确认和终止；
- 负确认。

---

## 28. 工程化建议与常见误区

### 28.1 锁定版本

```text
c104==2.2.1
```

并在升级时重新执行：

- Server/Client 互连测试；
- 所有 Type ID 注册测试；
- 站总召和组召测试；
- 累计量召唤测试；
- 读命令测试；
- Direct/SBO 测试；
- TLS 测试；
- 多主站测试；
- 长时间稳定性测试。

### 28.2 回调不要阻塞

协议线程中的回调应快速完成。耗时业务应进入工作队列：

```text
协议回调
→ 校验和复制必要数据
→ 投递线程安全队列
→ 业务线程执行数据库、设备或网络操作
```

### 28.3 区分四种时间

- 协议时标 `recorded_at`；
- 本地处理时间 `processed_at`；
- 周期发送间隔 `report_ms`；
- 应用定时器 `timer_ms`。

### 28.4 区分四种“成功”

1. Python 方法返回 `True`；
2. 报文成功进入发送队列；
3. 对端返回协议正确认；
4. 现场设备最终达到目标状态。

这四层不能混为一谈。

### 28.5 不要根据前缀推断全部能力

```text
M_* 不一定都能普通总召
C_* 不一定都能注册为 Point
Type 枚举存在不等于实现可用
```

### 28.6 不要把总召当作订阅

总召完成后，持续更新依赖周期、自发或背景发送。

### 28.7 不要把 Common Address 当设备 ID

一个物理设备可以代理多个 CA，一个 CA 也可以代表一个逻辑聚合系统。

### 28.8 不要把控制成功当状态成功

必须等待关联监视点或现场反馈确认最终状态。

### 28.9 数据与协议状态分离

建议应用独立维护：

```text
过程当前值缓存
质量状态
采样时间
上次发送值
上次发送时间
连接状态
命令状态
```

不要试图给扩展类型 `Point` 动态增加任意属性；使用独立 dataclass 或状态仓库更稳妥。

---

# 附录 A：常见 Type ID

| 数值 | Type ID | 类别 | 时标 |
|---:|---|---|---|
| 1 | `M_SP_NA_1` | 单点监视 | 无 |
| 2 | `M_SP_TA_1` | 单点监视 | CP24Time2a |
| 3 | `M_DP_NA_1` | 双点监视 | 无 |
| 4 | `M_DP_TA_1` | 双点监视 | CP24Time2a |
| 5 | `M_ST_NA_1` | 步位置 | 无 |
| 6 | `M_ST_TA_1` | 步位置 | CP24Time2a |
| 7 | `M_BO_NA_1` | 32 位比特串 | 无 |
| 8 | `M_BO_TA_1` | 32 位比特串 | CP24Time2a |
| 9 | `M_ME_NA_1` | 归一化测量值 | 无 |
| 10 | `M_ME_TA_1` | 归一化测量值 | CP24Time2a |
| 11 | `M_ME_NB_1` | 标度化测量值 | 无 |
| 12 | `M_ME_TB_1` | 标度化测量值 | CP24Time2a |
| 13 | `M_ME_NC_1` | 短浮点测量值 | 无 |
| 14 | `M_ME_TC_1` | 短浮点测量值 | CP24Time2a |
| 15 | `M_IT_NA_1` | 累计量 | 无 |
| 16 | `M_IT_TA_1` | 累计量 | CP24Time2a |
| 17 | `M_EP_TA_1` | 保护事件 | CP24Time2a |
| 18 | `M_EP_TB_1` | 保护启动事件 | CP24Time2a |
| 19 | `M_EP_TC_1` | 保护输出电路事件 | CP24Time2a |
| 20 | `M_PS_NA_1` | 带状态变化检测的成组单点 | 无 |
| 21 | `M_ME_ND_1` | 不带质量的归一化测量值 | 无 |
| 30 | `M_SP_TB_1` | 单点监视 | CP56Time2a |
| 31 | `M_DP_TB_1` | 双点监视 | CP56Time2a |
| 32 | `M_ST_TB_1` | 步位置 | CP56Time2a |
| 33 | `M_BO_TB_1` | 32 位比特串 | CP56Time2a |
| 34 | `M_ME_TD_1` | 归一化测量值 | CP56Time2a |
| 35 | `M_ME_TE_1` | 标度化测量值 | CP56Time2a |
| 36 | `M_ME_TF_1` | 短浮点测量值 | CP56Time2a |
| 37 | `M_IT_TB_1` | 累计量 | CP56Time2a |
| 38 | `M_EP_TD_1` | 保护事件 | CP56Time2a |
| 39 | `M_EP_TE_1` | 保护启动事件 | CP56Time2a |
| 40 | `M_EP_TF_1` | 保护输出电路事件 | CP56Time2a |
| 45 | `C_SC_NA_1` | 单点命令 | 无 |
| 46 | `C_DC_NA_1` | 双点命令 | 无 |
| 47 | `C_RC_NA_1` | 步调节命令 | 无 |
| 48 | `C_SE_NA_1` | 归一化设点 | 无 |
| 49 | `C_SE_NB_1` | 标度化设点 | 无 |
| 50 | `C_SE_NC_1` | 短浮点设点 | 无 |
| 51 | `C_BO_NA_1` | 32 位比特串命令 | 无 |
| 58 | `C_SC_TA_1` | 单点命令 | CP56Time2a |
| 59 | `C_DC_TA_1` | 双点命令 | CP56Time2a |
| 60 | `C_RC_TA_1` | 步调节命令 | CP56Time2a |
| 61 | `C_SE_TA_1` | 归一化设点 | CP56Time2a |
| 62 | `C_SE_TB_1` | 标度化设点 | CP56Time2a |
| 63 | `C_SE_TC_1` | 短浮点设点 | CP56Time2a |
| 64 | `C_BO_TA_1` | 32 位比特串命令 | CP56Time2a |
| 70 | `M_EI_NA_1` | 初始化结束 | 无 |
| 100 | `C_IC_NA_1` | 总召/组召 | 无 |
| 101 | `C_CI_NA_1` | 累计量召唤 | 无 |
| 102 | `C_RD_NA_1` | 读命令 | 无 |
| 103 | `C_CS_NA_1` | 时钟同步 | CP56Time2a |
| 104 | `C_TS_NA_1` | 测试命令 | 无 |
| 105 | `C_RP_NA_1` | 复位进程 | 无 |
| 106 | `C_CD_NA_1` | 延时获取 | CP16Time2a |
| 107 | `C_TS_TA_1` | 测试命令 | CP56Time2a |

---

# 附录 B：`c104 2.2.1` 能力矩阵

> 本表用于提醒“枚举、Point 注册、总召和周期发送”是不同能力。它是版本相关的工程参考，不是 IEC 104 标准能力表。升级包版本时应重新验证。

符号：

- `✓`：原始材料和公开 API 表明支持；
- `—`：不适用或未作为该路径支持；
- `V`：必须针对锁定版本重新验证。

| Type ID | 普通 Point | 站总召 | 累计量召唤 | `report_ms` | 主动 `transmit` |
|---|:---:|:---:|:---:|:---:|:---:|
| `M_SP_NA_1` | ✓ | ✓ | — | ✓ | ✓ |
| `M_SP_TA_1` | — | — | — | — | — |
| `M_DP_NA_1` | ✓ | ✓ | — | ✓ | ✓ |
| `M_DP_TA_1` | — | — | — | — | — |
| `M_ST_NA_1` | ✓ | ✓ | — | ✓ | ✓ |
| `M_ST_TA_1` | — | — | — | — | — |
| `M_BO_NA_1` | ✓ | ✓ | — | ✓ | ✓ |
| `M_BO_TA_1` | — | — | — | — | — |
| `M_ME_NA_1` | ✓ | ✓ | — | ✓ | ✓ |
| `M_ME_TA_1` | — | — | — | — | — |
| `M_ME_NB_1` | ✓ | ✓ | — | ✓ | ✓ |
| `M_ME_TB_1` | — | — | — | — | — |
| `M_ME_NC_1` | ✓ | ✓ | — | ✓ | ✓ |
| `M_ME_TC_1` | — | — | — | — | — |
| `M_IT_NA_1` | ✓ | — | ✓ | ✓ | ✓ |
| `M_IT_TA_1` | — | — | — | — | — |
| `M_EP_TA_1..M_EP_TC_1` | — | — | — | — | — |
| `M_PS_NA_1` | ✓ | — | — | — | ✓ |
| `M_ME_ND_1` | ✓ | — | — | — | ✓ |
| `M_SP_TB_1` | ✓ | ✓ | — | ✓ | ✓ |
| `M_DP_TB_1` | ✓ | ✓ | — | ✓ | ✓ |
| `M_ST_TB_1` | ✓ | ✓ | — | ✓ | ✓ |
| `M_BO_TB_1` | ✓ | ✓ | — | ✓ | ✓ |
| `M_ME_TD_1` | ✓ | ✓ | — | ✓ | ✓ |
| `M_ME_TE_1` | ✓ | ✓ | — | ✓ | ✓ |
| `M_ME_TF_1` | ✓ | ✓ | — | ✓ | ✓ |
| `M_IT_TB_1` | ✓ | — | ✓ | ✓ | ✓ |
| `M_EP_TD_1..M_EP_TF_1` | ✓ | — | — | — | ✓ |
| `C_SC_NA_1..C_BO_NA_1` | ✓ | — | — | — | 命令发送 |
| `C_SC_TA_1..C_BO_TA_1` | ✓ | — | — | — | 命令发送 |
| `M_EI_NA_1` | 专用方法 | — | — | — | `signal_initialized` |
| `C_IC_NA_1` | 专用 API | — | — | — | `interrogation` |
| `C_CI_NA_1` | 专用 API | — | — | — | `counter_interrogation` |
| `C_RD_NA_1` | 专用 API | — | — | — | `Point.read` |
| `C_CS_NA_1` | 专用 API | — | — | — | `clock_sync` |
| `C_TS_NA_1/C_TS_TA_1` | 专用 API | — | — | — | `test` |
| 组召 Server 自动响应 | — | V | — | — | V |

---

# 参考资料

## IEC 104 与协议栈

- IEC 60870-5-104：Telecontrol equipment and systems — Part 5-104: Transmission protocols — Network access for IEC 60870-5-101 using standard transport profiles。
- IEC 60870-5-101：Telecontrol equipment and systems — Companion standard for basic telecontrol tasks。
- MZ Automation `lib60870-C` 文档：Interrogation、ASDU、Server/Client 和 Type ID 支持。
- Beckhoff IEC 60870-5-10x 文档：ASDU Type ID 和报文结构。
- Wireshark IEC 60870-5-104 dissector。

## `iec104-python`

- GitHub：<https://github.com/Fraunhofer-FIT-DIEN/iec104-python>
- 官方文档：<https://iec104-python.readthedocs.io/>
- PyPI：<https://pypi.org/project/c104/>
- 示例代码：<https://github.com/Fraunhofer-FIT-DIEN/iec104-python/tree/main/examples>

---

## 文档使用说明

学习顺序建议：

```text
APDU/APCI
→ I/S/U 和序号
→ ASDU、Type ID、COT、CA、IOA
→ 总召/自发/周期/控制流程
→ 点表与互操作
→ c104 对象模型
→ Server/Client 示例
→ 版本限制和生产验证
```

本文不替代 IEC 标准原文。涉及保护控制、调度接入、网络安全或商业交付时，应以标准、设备互操作说明、项目点表和锁定版本源码测试结果为准。
