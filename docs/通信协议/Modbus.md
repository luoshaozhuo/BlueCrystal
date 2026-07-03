## 第一部分：Modbus（RTU / TCP）

### 1. 协议概述

Modbus 是工业自动化中使用最广泛的现场通信协议之一，最早由 Modicon 提出，后来成为 PLC、RTU、变频器、电表、传感器、网关和 SCADA 系统之间的事实标准通信方式。它的核心特点是 **数据模型简单、报文格式稳定、实现成本低、设备兼容性强**。

Modbus 不是一个复杂的信息模型协议。它不描述设备对象、变量单位、质量码、时间戳、报警事件或拓扑关系，而是围绕 **寄存器 / 线圈地址 + 功能码** 进行读写。

常见实现形态包括：

| 类型 | 传输介质 | 典型端口/参数 | 典型场景 |
|------|----------|---------------|----------|
| **Modbus RTU** | RS-485 / RS-232 串口 | 波特率、校验位、停止位、从站地址 | 现场仪表、变频器、电表、低成本采集设备 |
| **Modbus TCP** | Ethernet / TCP/IP | TCP `502` 端口 | PLC、网关、边缘设备、SCADA 系统 |
| **Modbus ASCII** | 串口 | ASCII 编码 + LRC | 早期串口系统，当前较少使用 |
| **Modbus RTU over TCP** | TCP 承载 RTU 帧 | 非标准但工程中常见 | 串口服务器透传、老设备网关 |

本文件重点说明 **Modbus RTU** 与 **Modbus TCP**。

核心目标：

- 通过统一功能码读写远程设备中的线圈、离散输入、输入寄存器和保持寄存器；
- 支持简单主从式请求/响应通信；
- 允许不同厂商设备通过统一报文格式互联；
- 在低成本串口链路和以太网链路上都能工作；
- 便于 SCADA、PLC、边缘网关和数据采集程序快速接入。

与 OPC UA、IEC 61850 相比，Modbus 的重点不是语义建模，而是 **直接访问地址表**：

```text
设备地址 + 功能码 + 起始地址 + 数量  →  读/写一段线圈或寄存器
```

### 2. 核心概念体系

#### 2.1 关键术语

| 术语 | 含义 | 类比 |
|------|------|------|
| **Master / Client** | 主站或客户端，主动发起请求 | 采集程序 / SCADA |
| **Slave / Server** | 从站或服务器，被动响应请求 | 仪表 / PLC / 网关 |
| **Unit ID / Slave ID** | 从站地址，RTU 中用于定位串口总线上的设备；TCP 中常用于网关后面的 RTU 从站 | 门牌号 |
| **Function Code** | 功能码，表示读线圈、读寄存器、写寄存器等操作 | 操作类型 |
| **Coil** | 可读写布尔量，常用于开关输出 | 数字输出 |
| **Discrete Input** | 只读布尔量，常用于开关输入 | 数字输入 |
| **Input Register** | 只读 16 位寄存器，常用于测量值 | 模拟输入 |
| **Holding Register** | 可读写 16 位寄存器，常用于参数、设定值、状态量 | 参数寄存器 |
| **PDU** | Protocol Data Unit，Modbus 应用层数据单元，不含传输层头尾 | 功能码 + 数据 |
| **ADU** | Application Data Unit，完整传输报文；RTU ADU = 地址 + PDU + CRC；TCP ADU = MBAP + PDU | 完整包裹 |
| **MBAP Header** | Modbus TCP 的 7 字节头部 | TCP 包头 |
| **CRC16** | RTU 帧尾校验码 | 串口校验 |
| **Exception Response** | 异常响应，功能码最高位置 1，并返回异常码 | 错误回执 |

#### 2.2 四类数据区

Modbus 逻辑数据模型分为四类地址区。这里的“位宽”是协议数据模型的基本单位，不是工程变量的最终含义。

| 数据区 | 传统地址前缀 | 位宽 | 访问权限 | 读功能码 | 写功能码 | 典型含义 |
|--------|--------------|------|----------|----------|----------|----------|
| **Coils** | `0xxxx` | 1 bit | 读/写 | `01` | `05` 单个 / `0F` 多个 | 继电器输出、启停命令、布尔控制位 |
| **Discrete Inputs** | `1xxxx` | 1 bit | 只读 | `02` | 无标准写功能码 | 开关输入、告警触点、只读布尔状态 |
| **Input Registers** | `3xxxx` | 16 bit | 只读 | `04` | 无标准写功能码 | 电压、电流、温度、功率等测量值 |
| **Holding Registers** | `4xxxx` | 16 bit | 读/写 | `03` | `06` 单个 / `10` 多个 / `16` 掩码写 / `17` 读写多个 | 设定值、状态字、控制参数 |

其中 **Coil** 和 **Discrete Input** 的基本宽度确实只有 **1 bit**，因此单个地址只能表达：

```text
0 = OFF / False / 未动作 / 断开
1 = ON  / True  / 已动作 / 闭合
```

这两类对象适合表达布尔量，不适合直接表达多状态枚举、故障码、模拟量或字符串。多状态数据通常有三种建模方式：

| 数据类型 | 推荐 Modbus 表达 | 示例 |
|----------|------------------|------|
| 简单布尔状态 | Coil / Discrete Input | 运行、停止、告警触点 |
| 多状态枚举 | Holding Register / Input Register | `0=Stop, 1=Run, 2=Fault` |
| 多个布尔状态组合 | 16 位状态字 | bit0=运行，bit1=故障，bit2=远方 |
| 模拟量 | Input Register / Holding Register | 电压、电流、功率、温度 |

工程中经常出现一个 16 位寄存器被拆成多个 bit 使用，例如：

```text
Holding Register 40010 = 0x0005 = 0000 0000 0000 0101b
bit0 = 1  运行中
bit1 = 0  未告警
bit2 = 1  远方模式
```

这种状态字仍然属于 **Holding Register** 或 **Input Register**，不是 Coil。点表中应显式记录寄存器地址、bit 位、含义和取反规则。

工程中经常出现两套地址表达：

| 表达方式 | 示例 | 含义 |
|----------|------|------|
| 人工文档地址 | `40001` | 第一个 Holding Register |
| 协议实际地址 | `0` | 报文中的起始地址从 0 开始 |

因此设备手册中写 `40001` 时，程序里常常要写 `address=0`。如果手册写的是 `40001`、`40002` 这类传统地址，需要确认厂商文档是否采用 **1-based 人工地址**；如果手册直接写 `offset=0` 或 `register address=0x0000`，通常就是协议实际地址。

#### 2.3 Unit ID / Slave ID

在 Modbus RTU 中，`Slave ID` 是串口总线上的从站地址，范围通常为 `1~247`。主站每次请求都带一个从站地址，只有匹配地址的设备响应。

在 Modbus TCP 中，TCP 连接已经通过 IP 和端口定位到服务器，但 MBAP Header 中仍保留 `Unit ID` 字段。它的工程作用主要有两类：

| 场景 | Unit ID 的作用 |
|------|----------------|
| 直接连接 Modbus TCP 设备 | 多数设备忽略或固定要求 `1` / `255` |
| TCP-to-RTU 网关 | 用 Unit ID 指定网关后面的 RTU 从站地址 |

例如：

```text
客户端 → 192.168.1.20:502，Unit ID = 5
```

含义可能是：连接到 IP 为 `192.168.1.20` 的 Modbus TCP 网关，再由网关把请求转发给 RS-485 总线上的 `Slave ID = 5` 的仪表。

#### 2.4 功能码

功能码决定本次请求访问哪一类数据区，以及执行读、写、诊断或设备信息查询等哪一种操作。四类核心数据区的读写关系如下。

| 数据区 | 读单个/多个 | 写单个 | 写多个 | 说明 |
|--------|-------------|--------|--------|------|
| **Coils** | `01` Read Coils | `05` Write Single Coil | `0F` Write Multiple Coils | 可读写 1 bit 输出量 |
| **Discrete Inputs** | `02` Read Discrete Inputs | 无 | 无 | 只读 1 bit 输入量，标准 Modbus 不定义写入 |
| **Input Registers** | `04` Read Input Registers | 无 | 无 | 只读 16 位输入寄存器，标准 Modbus 不定义写入 |
| **Holding Registers** | `03` Read Holding Registers | `06` Write Single Register | `10` Write Multiple Registers | 可读写 16 位寄存器 |

因此“所有四类变量的读/写功能码”并不是每类都有完整读写。**Discrete Input** 和 **Input Register** 在 Modbus 数据模型中是只读区，标准功能码只提供读取，不提供写入。需要写入的布尔控制量应放在 **Coils**，需要写入的数值参数应放在 **Holding Registers**。

常用标准功能码如下：

| 功能码 | 十六进制 | 名称 | 访问对象 | 说明 |
|--------|----------|------|----------|------|
| `01` | `0x01` | Read Coils | Coils | 读取一个或多个线圈 |
| `02` | `0x02` | Read Discrete Inputs | Discrete Inputs | 读取一个或多个离散输入 |
| `03` | `0x03` | Read Holding Registers | Holding Registers | 读取一个或多个保持寄存器 |
| `04` | `0x04` | Read Input Registers | Input Registers | 读取一个或多个输入寄存器 |
| `05` | `0x05` | Write Single Coil | Coils | 写单个线圈，`0xFF00` 表示 ON，`0x0000` 表示 OFF |
| `06` | `0x06` | Write Single Register | Holding Registers | 写单个保持寄存器 |
| `07` | `0x07` | Read Exception Status | 串口设备状态 | 主要用于串行链路设备，工程中较少用 |
| `08` | `0x08` | Diagnostics | 串口诊断 | 回环测试、通信事件等，主要用于 Serial Line |
| `0B` | `0x0B` | Get Comm Event Counter | 串口通信事件 | 获取通信事件计数器 |
| `0C` | `0x0C` | Get Comm Event Log | 串口通信事件日志 | 获取通信事件日志 |
| `0F` | `0x0F` | Write Multiple Coils | Coils | 批量写多个线圈 |
| `10` | `0x10` | Write Multiple Registers | Holding Registers | 批量写多个保持寄存器 |
| `11` | `0x11` | Report Server ID | 设备标识 | 读取服务器 ID，常见于串行设备 |
| `14` | `0x14` | Read File Record | 文件记录 | 读取文件记录，较少用 |
| `15` | `0x15` | Write File Record | 文件记录 | 写文件记录，较少用 |
| `16` | `0x16` | Mask Write Register | Holding Registers | 对单个保持寄存器做位掩码写 |
| `17` | `0x17` | Read/Write Multiple Registers | Holding Registers | 一个事务中写一段保持寄存器，同时读另一段保持寄存器 |
| `18` | `0x18` | Read FIFO Queue | FIFO 队列 | 读取 FIFO 队列，较少用 |
| `2B` | `0x2B` | Encapsulated Interface Transport | 封装接口 | 常用于 Read Device Identification |

说明：

- `15` 十进制等于 `0F` 十六进制，`16` 十进制等于 `10` 十六进制。文档和库函数可能混用十进制与十六进制写法。
- 设备不一定支持全部标准功能码。低成本仪表通常只支持 `03`、`04`，控制类设备常支持 `05`、`06`、`0F`、`10`。
- 厂商自定义功能码不在通用标准表内，必须按设备手册实现。

常见最大数量限制：

| 操作 | 单次最大数量 |
|------|--------------|
| 读 Coils / Discrete Inputs | 2000 bit |
| 读 Holding/Input Registers | 125 个 16 位寄存器 |
| 写多个 Coils | 1968 bit |
| 写多个 Holding Registers | 123 个 16 位寄存器 |

这些限制来自 Modbus PDU 最大长度约束。实际设备可能进一步限制单次读取长度，因此工程中应以设备手册和实测结果为准。

### 3. 协议栈与帧格式

#### 3.1 Modbus RTU 协议栈

| 层级 | 协议/组件 |
|------|-----------|
| 应用层 | Modbus PDU（Function Code + Data） |
| 数据链路表达 | Modbus RTU ADU（Slave Address + PDU + CRC16） |
| 传输介质 | RS-485 / RS-232 串口 |
| 物理参数 | 波特率、数据位、校验位、停止位、终端电阻、偏置电阻 |

Modbus RTU 使用二进制帧，依赖串口总线上的静默时间来分隔帧。典型串口参数如下：

```text
baudrate = 9600 / 19200 / 38400 / 115200
bytesize = 8
parity   = N / E / O
stopbits = 1 / 2
mode     = RS-485 half-duplex
```

RTU 帧结构：

| 字段 | 大小 | 说明 |
|------|------|------|
| Slave Address | 1 字节 | 从站地址，通常 `1~247` |
| Function Code | 1 字节 | 功能码 |
| Data | N 字节 | 起始地址、数量、写入值等 |
| CRC16 | 2 字节 | 低字节在前，高字节在后 |

示例：读取从站 `1` 的 Holding Register，从地址 `0` 开始读 `2` 个寄存器。

```text
请求：01 03 00 00 00 02 C4 0B
      │  │  │──── │──── │────
      │  │  │     │     └─ CRC16
      │  │  │     └────── 数量 2
      │  │  └──────────── 起始地址 0
      │  └─────────────── 功能码 03
      └────────────────── 从站地址 1
```

响应示例：

```text
响应：01 03 04 00 64 00 C8 BA 7A
      │  │  │  │──── │──── │────
      │  │  │  │     │     └─ CRC16
      │  │  │  │     └────── 寄存器 2 = 200
      │  │  │  └──────────── 寄存器 1 = 100
      │  │  └─────────────── 字节数 4
      │  └────────────────── 功能码 03
      └───────────────────── 从站地址 1
```

#### 3.2 Modbus RTU 帧间隔

Modbus RTU 不使用特殊帧起止字节，而是用总线静默时间划分帧：

| 时间 | 含义 |
|------|------|
| `t1.5` | 字符间最大间隔，超过后可能认为帧被破坏 |
| `t3.5` | 帧间最小静默时间，表示一帧结束、下一帧开始 |

工程影响：

- 波特率越低，单字符时间越长，RTU 单次轮询耗时越高；
- USB-RS485 转换器、操作系统调度和串口驱动缓冲会影响时序；
- 同一条 RS-485 总线上只能一个主站主动轮询；
- 半双工通信需要控制收发方向，工业转换器一般自动处理；
- 总线两端应加终端电阻，长线或多节点场景要处理偏置电阻和接地。

#### 3.3 Modbus TCP 协议栈

| 层级 | 协议/组件 |
|------|-----------|
| 应用层 | Modbus PDU（Function Code + Data） |
| 会话/封装 | MBAP Header（Transaction ID、Protocol ID、Length、Unit ID） |
| 传输层 | TCP，默认端口 `502` |
| 网络层 | IP |
| 数据链路/物理层 | Ethernet |

Modbus TCP 不使用 CRC16，因为 TCP/IP 链路层和传输层已有校验与重传机制。它在 PDU 前增加 7 字节 MBAP Header。

MBAP Header 结构：

| 偏移 | 大小 | 字段 | 说明 |
|------|------|------|------|
| 0 | 2 | Transaction Identifier | 事务 ID，用于匹配请求和响应 |
| 2 | 2 | Protocol Identifier | 协议 ID，Modbus 固定为 `0x0000` |
| 4 | 2 | Length | 后续字节数 = Unit ID + PDU 长度 |
| 6 | 1 | Unit Identifier | 单元 ID / 从站 ID |
| 7 | 1 | Function Code | 功能码，PDU 起始 |
| 8 | N | Data | 功能码参数或返回值 |

示例：读取 Unit ID `1` 的 Holding Register，从地址 `0` 开始读 `2` 个寄存器。

```text
00 01 00 00 00 06 01 03 00 00 00 02
│──── │──── │──── │  │  │──── │────
│     │     │     │  │  │     └─ 数量 2
│     │     │     │  │  └────── 起始地址 0
│     │     │     │  └───────── 功能码 03
│     │     │     └──────────── Unit ID 1
│     │     └────────────────── Length = 6
│     └──────────────────────── Protocol ID = 0
└────────────────────────────── Transaction ID = 1
```

#### 3.4 RTU、TCP、RTU over TCP 的区别

| 对比项 | Modbus RTU | Modbus TCP | Modbus RTU over TCP |
|--------|------------|------------|---------------------|
| 传输介质 | 串口 RS-485/RS-232 | TCP/IP | TCP/IP |
| 帧头 | Slave Address | MBAP Header | Slave Address |
| 帧尾 | CRC16 | 无 CRC | 通常保留 CRC16 |
| 默认端口 | 无 | `502` | 厂商自定义 |
| 分帧方式 | 静默时间 | TCP 流 + MBAP Length | TCP 流，按 RTU 帧解析 |
| 工程定位 | 多从站总线 | IP 设备或网关 | 串口服务器透传老设备 |
| 标准性 | 标准 | 标准 | 非标准/厂商实现 |

RTU over TCP 在项目中经常由“串口服务器透传”产生。客户端不能把它当成标准 Modbus TCP，因为它没有 MBAP Header；也不能完全当成串口 RTU，因为底层没有串口时序。接入时必须确认设备或网关到底使用哪种帧格式。

### 4. 数据编码与点表设计

#### 4.1 16 位寄存器

Modbus 寄存器基本单位是 16 位。一个寄存器可以表示：

| 数据类型 | 占用寄存器 | 说明 |
|----------|------------|------|
| `uint16` | 1 | 无符号 16 位整数 |
| `int16` | 1 | 有符号 16 位整数，二进制补码 |
| `uint32` | 2 | 无符号 32 位整数 |
| `int32` | 2 | 有符号 32 位整数 |
| `float32` | 2 | IEEE 754 单精度浮点 |
| `float64` | 4 | IEEE 754 双精度浮点，较少见 |
| `string` | N | 多寄存器组合，厂商定义较多 |
| `bit field` | 1 | 一个 16 位状态字拆成多个 bit |

#### 4.2 字节序与字序

Modbus 规范规定单个 16 位寄存器内部按 **高字节在前** 传输，例如数值 `0x1234` 发送为：

```text
12 34
```

但 32 位或 64 位数据跨多个寄存器时，**寄存器字序** 没有在所有设备上统一。常见组合如下：

| 名称 | 寄存器顺序 | 字节流示例，值为 `0x12345678` |
|------|------------|-------------------------------|
| Big-endian word | 高字在前 | `12 34 56 78` |
| Little-endian word | 低字在前 | `56 78 12 34` |
| Byte swap | 每个 word 内交换 | `34 12 78 56` |
| Byte + word swap | 字节和字都交换 | `78 56 34 12` |

多寄存器点位应在点表中明确数据区、地址、占用长度和编码规则：

```yaml
name: active_power
area: holding_register
address: 100
quantity: 2
data_type: float32
byte_order: big
word_order: little
scale: 0.1
unit: kW
access: read
read_function_code: 03   # 可选覆盖；无特殊要求时可由 area 推导
```

缺少字序信息时，`float32` 读出来经常会出现极大值、极小值或 NaN。

#### 4.3 缩放系数与单位

Modbus 没有内置单位和工程量范围。设备通常把工程值压缩成整数寄存器，再通过比例系数还原。

示例：

| 寄存器原始值 | scale | offset | 工程值 |
|--------------|-------|--------|--------|
| `235` | `0.1` | `0` | `23.5 °C` |
| `12000` | `0.01` | `0` | `120.00 A` |
| `-500` | `0.1` | `0` | `-50.0 kW` |

通用换算：

```text
engineering_value = raw_value * scale + offset
```

#### 4.4 异常响应

当设备无法执行请求时，会返回异常响应：

```text
异常功能码 = 原功能码 + 0x80
```

例如请求功能码 `03`，异常响应功能码为 `83`。

常见异常码：

| 异常码 | 名称 | 含义 |
|--------|------|------|
| `01` | Illegal Function | 设备不支持该功能码 |
| `02` | Illegal Data Address | 地址不存在或越界 |
| `03` | Illegal Data Value | 请求数量或值非法 |
| `04` | Slave Device Failure | 从站内部错误 |
| `05` | Acknowledge | 已接受但处理需要更长时间 |
| `06` | Slave Device Busy | 从站忙 |
| `0A` | Gateway Path Unavailable | 网关路径不可用 |
| `0B` | Gateway Target Failed to Respond | 网关后面的目标无响应 |


#### 4.5 点表字段、功能码推导与设备能力

Modbus 点表应优先表达工程访问意图，而不是把所有报文细节都固化到每一个点上。推荐的基本字段如下：

| 字段 | 是否必需 | 说明 |
|------|----------|------|
| `area` | 必需 | 数据区：`coil`、`discrete_input`、`input_register`、`holding_register` |
| `address` | 必需 | 协议实际地址，建议统一使用 0-based PDU 地址 |
| `display_address` | 可选 | 设备手册中的人工地址，如 `40001`、`30001` |
| `quantity` | 必需 | 占用的 bit 或 16-bit register 数量 |
| `data_type` | 必需 | 业务类型，如 `bool`、`uint16`、`int32`、`float32` |
| `byte_order` / `word_order` | 多寄存器类型必需 | 用于 `int32`、`float32`、`float64` 等跨寄存器类型 |
| `scale` / `offset` | 可选 | 原始值到工程值的换算 |
| `access` | 必需 | `read`、`write`、`read_write` |
| `read_function_code` | 可选 | 读功能码覆盖值；默认可由 `area` 推导 |
| `write_function_code` | 可选 | 写功能码覆盖值；默认可由 `area`、写入数量和设备能力推导 |

读功能码通常可以由数据区唯一推导：

```text
coil              -> 01
discrete_input    -> 02
holding_register  -> 03
input_register    -> 04
```

写功能码需要结合数据区、写入数量和设备支持范围推导：

```text
coil，单个 bit               -> 05
coil，多个 bit               -> 0F
holding_register，单个寄存器 -> 06
holding_register，多个寄存器 -> 10
holding_register，位掩码写   -> 16
```

设备是否支持某个功能码由设备实现决定。标准定义功能码语义，但不要求每台设备都实现全部功能码。工程配置中应允许在设备模板或点位上覆盖默认功能码。

示例：

```yaml
device:
  name: inverter_01
  protocol: modbus_tcp
  host: 192.168.1.100
  port: 502
  unit_id: 1
  supported_function_codes: [3, 4, 6, 16]
  max_read_holding_registers: 60
  max_read_input_registers: 60
  max_write_holding_registers: 30
  single_outstanding_request: true

points:
  - name: active_power
    area: holding_register
    address: 100
    display_address: 40101
    quantity: 2
    data_type: float32
    byte_order: big
    word_order: big
    scale: 1.0
    access: read
    read_function_code: 3

  - name: power_limit
    area: holding_register
    address: 200
    display_address: 40201
    quantity: 2
    data_type: float32
    byte_order: big
    word_order: little
    scale: 1.0
    access: read_write
    read_function_code: 3
    write_function_code: 16
```

这里的 `read_function_code` 和 `write_function_code` 是覆盖字段，不是所有点位都必须填写。没有覆盖值时，驱动可根据 `area`、`access`、`quantity` 和设备能力自动选择标准功能码。

#### 4.6 写入编码与批量写入规则

Modbus 协议层不携带业务数据类型。写入时，驱动需要先根据点表把业务值编码为 Coil bit 或 16-bit register 数组，再调用对应写 API。

典型映射关系如下：

| 业务类型 | Modbus 承载方式 | 占用数量 |
|----------|----------------|----------|
| `bool` in Coil | 1 个 Coil | 1 bit |
| `uint16` / `int16` | 1 个 Holding Register | 1 register |
| `uint32` / `int32` | 2 个 Holding Registers | 2 registers |
| `float32` | 2 个 Holding Registers | 2 registers |
| `float64` | 4 个 Holding Registers | 4 registers |
| register bit | 1 个 Holding Register 的某一位 | 1 register + bit index |

`write_registers` 对应的是一段连续 Holding Register 写入。它的 `values` 参数不是业务值列表，而是已经编码好的 16-bit register 列表：

```text
write_registers(address=100, values=[R100, R101, R102, R103])
```

批量写入需要满足以下条件：

| 条件 | 说明 |
|------|------|
| 同一数据区 | `write_registers` 只能写 Holding Register；Coil 批量写应使用 `write_coils` |
| 地址连续 | 请求只能表达起始地址和连续数量，不能表达离散地址集合 |
| 已完成编码 | 不同业务类型可以一起写，但必须先编码成连续 16-bit register 数组 |
| 不覆盖未知 gap | 地址中间存在空洞时，不应为了合并请求而写入未知寄存器 |
| 功能码一致 | 同一批写入应使用同一种写功能码 |

不同业务类型可以合并批量写入，只要最终地址连续。例如：

| 点名 | 地址 | 类型 | 占用 |
|------|------|------|------|
| `mode` | `100` | `uint16` | 1 |
| `power_limit` | `101` | `float32` | 2 |
| `enable` | `103` | `uint16` | 1 |

编码后可以形成一段连续 payload：

```text
address 100 -> mode
address 101 -> power_limit 高/低字之一
address 102 -> power_limit 高/低字之一
address 103 -> enable
```

然后一次写入：

```text
write_registers(address=100, values=[R100, R101, R102, R103])
```

如果布尔量放在寄存器的某一位，需要采用读-改-写或 `16 Mask Write Register`：

```text
1. 读取当前 register 值；
2. 修改目标 bit；
3. 写回 register；
4. 或在设备支持时使用 FC16 掩码写。
```

寄存器 bit 写入应特别注意并发风险。若同一寄存器的不同 bit 被多个上位机或控制任务同时修改，读-改-写可能覆盖对方更新。关键控制位应优先由 PLC 侧提供独立 Coil、独立 Holding Register 或专用命令寄存器。

### 5. 通信流程

#### 5.1 Modbus RTU 读取流程

```text
1. 主站打开串口，配置 baudrate/parity/stopbits/timeout。
2. 主站发送 RTU ADU：Slave ID + Function Code + Data + CRC。
3. RS-485 总线上对应 Slave ID 的从站接收请求。
4. 从站校验 CRC、功能码、地址和数量。
5. 从站返回响应 ADU。
6. 主站校验 CRC，并解析返回数据。
7. 如果超时或 CRC 错误，主站按策略重试或标记通信异常。
```

#### 5.2 Modbus TCP 读取流程

```text
1. 客户端连接 TCP 服务器：host:502。
2. 客户端生成 Transaction ID。
3. 客户端发送 MBAP Header + PDU。
4. 服务器处理请求，返回相同 Transaction ID 的响应。
5. 客户端根据 Transaction ID 匹配响应，并解析 PDU。
6. 如果通过 TCP-to-RTU 网关通信，网关根据 Unit ID 转发到后端 RTU 从站。
```

#### 5.3 轮询机制

Modbus 本身没有订阅推送机制。大多数采集程序通过主站轮询实现实时数据采集。

典型轮询策略：

```text
1. 按设备分组。
2. 按功能码和连续地址合并读取区间。
3. 每个区间用一次 read_holding_registers / read_input_registers 读取。
4. 将返回的寄存器数组按点表解析成工程值。
5. 记录采集时间、通信质量、异常码和原始值。
6. 按采集周期重复执行。
```


#### 5.4 分包采集与时间戳策略

Modbus 没有协议级设备时间戳，也没有跨多个请求的一致性快照机制。一次采集被拆成多个读取块时，不同块的数据不是严格同一时刻的数据。

推荐在驱动层记录以下时间：

| 字段 | 含义 |
|------|------|
| `scan_id` | 一轮采集的批次 ID |
| `batch_start_time` | 本轮采集开始时间 |
| `batch_end_time` | 本轮采集结束时间 |
| `request_send_time` | 单个 Modbus 请求发出时间 |
| `response_receive_time` | 单个 Modbus 响应接收时间 |
| `estimated_source_time` | 估算数据时间，通常取请求发送与响应接收的中点 |

推荐估算方式：

```text
estimated_source_time = (request_send_time + response_receive_time) / 2
```

点值时间戳使用其所在读取块的 `estimated_source_time`，而不是把整轮分包数据全部强行标记为同一个时间。整轮采集可以额外记录 `scan_id`、`batch_start_time` 和 `batch_end_time`，用于计算本轮采集跨度。

同一设备内的分包读取推荐默认串行执行：

```text
read block 1 -> response 1 -> read block 2 -> response 2 -> read block 3 -> response 3
```

RTU 总线必须按请求/响应顺序串行轮询。Modbus TCP 虽有 Transaction ID，但许多设备、网关和串口转换器内部仍按单请求队列处理。通用驱动应采用如下默认策略：

```text
同一 device / unit_id / connection：单 outstanding request，顺序读取
不同 device / 不同 TCP connection：可以并行采集
```

强同步数据应优先通过设备侧建模解决：

| 方案 | 说明 |
|------|------|
| 连续寄存器区 | 将需要同步的变量映射到同一段连续寄存器，一次读取 |
| 快照区 | 上位机触发快照，设备将实时数据锁存到 snapshot register area |
| 采样计数器 | 每个数据块带相同 `sample_counter`，用于判断是否来自同一采样周期 |
| 设备时间戳 | 设备提供自己的采样时间，采集端读取并入库 |

分包采集不能默认视为严格同步快照。若业务计算依赖强同步，例如电压、电流、有功、无功联合计算，应尽量让这些变量落在同一读取块内。

#### 5.5 心跳、存活判断与通信质量

Modbus 没有内置心跳报文，也没有订阅状态通道。工程中通常用“周期性成功响应”来判断设备存活，并在需要时通过轻量读请求或应用层心跳寄存器模拟心跳。

可分为三层处理：

| 层级 | 机制 | 说明 |
|------|------|------|
| TCP 连接层 | TCP keepalive、连接失败、socket 超时 | 只能判断 TCP 链路状态，不能证明设备应用层正常 |
| Modbus 协议层 | 周期性读一个轻量地址 | 任意成功的 Modbus 响应都可作为设备在线证据 |
| 应用层 | 设备提供心跳计数器、翻转位或时间寄存器 | 可判断设备程序是否仍在运行、数据是否刷新 |

常用心跳策略：

| 策略 | 适用场景 | 说明 |
|------|----------|------|
| 复用正常轮询 | 常规采集 | 如果设备在采集周期内持续成功响应，无需额外心跳请求 |
| 轻量读心跳 | 低频采集或空闲设备 | 周期性读取一个稳定寄存器、状态字或设备标识 |
| 读取递增计数器 | PLC / 网关可配置 | 设备周期递增 `heartbeat_counter`，上位机检查是否变化 |
| 读取翻转位 | PLC / 网关可配置 | 设备周期翻转 `heartbeat_bit`，上位机检查边沿或变化 |
| 写入看门狗 | 明确设计的控制场景 | 上位机周期写入计数器或翻转位，设备侧超时后进入安全状态 |

协议层心跳示例：

```text
每 5 s 读取 Holding Register 0 或 Input Register 0。
连续 1 次失败：本次采集质量置为 BAD_COMM。
连续 3 次失败：设备状态置为 DEGRADED。
连续 N 次失败或超过 offline_timeout：设备状态置为 OFFLINE。
恢复 1 次成功响应：设备状态由 OFFLINE 进入 RECOVERING。
连续 M 次成功：设备状态恢复 ONLINE。
```

应用层心跳示例：

```text
heartbeat_counter: Holding Register 10，uint16，每 1 s 递增一次

采集端逻辑：
1. 周期读取 heartbeat_counter；
2. 若通信成功且计数器变化，判定设备应用正常；
3. 若通信成功但计数器长时间不变，判定设备程序或数据刷新异常；
4. 若通信失败，判定通信链路异常。
```

写入型看门狗只应在设备侧明确支持时使用。典型逻辑如下：

```text
上位机每 1 s 写入 watchdog_counter。
PLC 侧监视该寄存器是否在 3 s 内更新。
若超时未更新，PLC 自动撤销远程控制、保持安全输出或进入本地模式。
```

写入型心跳不应随意使用普通控制寄存器实现。它必须满足以下条件：

- 设备手册或 PLC 程序明确约定该寄存器为心跳 / 看门狗用途；
- 超时后的设备行为明确且安全；
- 心跳写入不会影响正常控制命令；
- 采集程序退出、网络中断或上位机故障时，设备能进入预期安全状态；
- 心跳写入频率不会影响正常采集和设备处理能力。

通信质量建议至少区分以下状态：

| 状态 | 含义 |
|------|------|
| `ONLINE` | 最近周期通信成功，数据按预期刷新 |
| `STALE` | 通信成功，但应用层心跳或数据更新时间未变化 |
| `DEGRADED` | 出现连续失败，但尚未达到离线阈值 |
| `OFFLINE` | 超过离线阈值无成功响应 |
| `RECOVERING` | 离线后出现成功响应，等待连续成功确认 |

点值入库时应同时记录 `timestamp`、`quality`、`last_success_time`、`exception_code` 和 `communication_state`。对于通信失败的点，不应静默沿用旧值而不标注质量；可保留上一有效值，但必须标记为 stale 或 bad quality。

### 6. Python 开发

#### 6.1 库选择

Python 中常用 Modbus 库包括：

| 库 | 说明 | 适用场景 |
|----|------|----------|
| `pymodbus` | 功能完整，支持 TCP、RTU、TLS、异步客户端、服务器和模拟器 | 通用项目、复杂采集、异步调度 |
| `minimalmodbus` | 接口简单，主要面向 RTU 仪表 | 简单串口仪表采集 |
| `pyModbusTCP` | 轻量 Modbus TCP 客户端/服务器 | 简单 TCP 接入 |
| `pyserial` | 串口基础库 | 自己实现 RTU 帧或调试底层问题 |

推荐优先使用 `pymodbus`，因为它同时覆盖 RTU 与 TCP，适合统一封装。

安装：

```bash
pip install pymodbus pyserial
```

#### 6.2 读写 API 对照

`pymodbus` 的常用 API 与 Modbus 功能码对应关系如下：

| 操作 | 功能码 | `pymodbus` 方法 | 说明 |
|------|--------|-----------------|------|
| 读 Coils | `01` | `read_coils(address, count, slave=...)` | 返回 `bits` |
| 读 Discrete Inputs | `02` | `read_discrete_inputs(address, count, slave=...)` | 返回 `bits` |
| 读 Holding Registers | `03` | `read_holding_registers(address, count, slave=...)` | 返回 `registers` |
| 读 Input Registers | `04` | `read_input_registers(address, count, slave=...)` | 返回 `registers` |
| 写单个 Coil | `05` | `write_coil(address, value, slave=...)` | `value=True/False` |
| 写单个 Holding Register | `06` | `write_register(address, value, slave=...)` | `value=0~65535` |
| 写多个 Coils | `0F` | `write_coils(address, values, slave=...)` | `values=[True, False, ...]` |
| 写多个 Holding Registers | `10` | `write_registers(address, values, slave=...)` | `values=[100, 200, ...]` |

Discrete Inputs 与 Input Registers 是只读区，因此没有对应的标准写 API。

#### 6.3 Modbus TCP：覆盖四类数据区读取

```python
from pymodbus.client import ModbusTcpClient

HOST = "192.168.1.100"
PORT = 502
UNIT_ID = 1


def ensure_ok(result, operation: str):
    if result.isError():
        raise RuntimeError(f"{operation} failed: {result}")
    return result


client = ModbusTcpClient(host=HOST, port=PORT, timeout=3)

try:
    if not client.connect():
        raise RuntimeError("Modbus TCP connect failed")

    # 1) 读 Coils，功能码 01，读取 8 个 1-bit 可读写输出量
    rr = ensure_ok(
        client.read_coils(address=0, count=8, slave=UNIT_ID),
        "read coils",
    )
    coils = rr.bits[:8]
    print("coils:", coils)

    # 2) 读 Discrete Inputs，功能码 02，读取 8 个 1-bit 只读输入量
    rr = ensure_ok(
        client.read_discrete_inputs(address=0, count=8, slave=UNIT_ID),
        "read discrete inputs",
    )
    discrete_inputs = rr.bits[:8]
    print("discrete inputs:", discrete_inputs)

    # 3) 读 Holding Registers，功能码 03，读取 4 个 16-bit 可读写寄存器
    rr = ensure_ok(
        client.read_holding_registers(address=0, count=4, slave=UNIT_ID),
        "read holding registers",
    )
    holding_registers = rr.registers
    print("holding registers:", holding_registers)

    # 4) 读 Input Registers，功能码 04，读取 4 个 16-bit 只读寄存器
    rr = ensure_ok(
        client.read_input_registers(address=0, count=4, slave=UNIT_ID),
        "read input registers",
    )
    input_registers = rr.registers
    print("input registers:", input_registers)

finally:
    client.close()
```

#### 6.4 Modbus TCP：单个/批量写入

```python
from pymodbus.client import ModbusTcpClient

HOST = "192.168.1.100"
PORT = 502
UNIT_ID = 1


def ensure_ok(result, operation: str):
    if result.isError():
        raise RuntimeError(f"{operation} failed: {result}")
    return result


client = ModbusTcpClient(host=HOST, port=PORT, timeout=3)

try:
    if not client.connect():
        raise RuntimeError("Modbus TCP connect failed")

    # 1) 写单个 Coil，功能码 05
    # True 对应协议值 0xFF00，False 对应 0x0000。
    ensure_ok(
        client.write_coil(address=10, value=True, slave=UNIT_ID),
        "write single coil",
    )

    # 2) 批量写 Coils，功能码 0F
    ensure_ok(
        client.write_coils(
            address=20,
            values=[True, False, True, True, False, False, True, False],
            slave=UNIT_ID,
        ),
        "write multiple coils",
    )

    # 3) 写单个 Holding Register，功能码 06
    ensure_ok(
        client.write_register(address=100, value=1234, slave=UNIT_ID),
        "write single holding register",
    )

    # 4) 批量写 Holding Registers，功能码 10
    ensure_ok(
        client.write_registers(address=110, values=[100, 200, 300, 400], slave=UNIT_ID),
        "write multiple holding registers",
    )

finally:
    client.close()
```

#### 6.5 Modbus RTU：读取与写入

RTU 与 TCP 的应用层功能码一致，主要差异在连接参数。RTU 需要配置串口、波特率、校验位和停止位。

```python
from pymodbus.client import ModbusSerialClient

SLAVE_ID = 1


def ensure_ok(result, operation: str):
    if result.isError():
        raise RuntimeError(f"{operation} failed: {result}")
    return result


client = ModbusSerialClient(
    port="/dev/ttyUSB0",
    baudrate=9600,
    bytesize=8,
    parity="N",
    stopbits=1,
    timeout=1,
)

try:
    if not client.connect():
        raise RuntimeError("Modbus RTU serial open failed")

    # 读多个 Input Registers，功能码 04
    rr = ensure_ok(
        client.read_input_registers(address=0, count=4, slave=SLAVE_ID),
        "read input registers",
    )
    print("input registers:", rr.registers)

    # 读多个 Holding Registers，功能码 03
    rr = ensure_ok(
        client.read_holding_registers(address=100, count=2, slave=SLAVE_ID),
        "read holding registers",
    )
    print("holding registers:", rr.registers)

    # 写单个 Coil，功能码 05
    ensure_ok(
        client.write_coil(address=10, value=False, slave=SLAVE_ID),
        "write single coil",
    )

    # 写多个 Holding Registers，功能码 10
    ensure_ok(
        client.write_registers(address=200, values=[1, 2, 3], slave=SLAVE_ID),
        "write multiple holding registers",
    )

finally:
    client.close()
```

#### 6.6 解析 16 位、32 位和状态字

单个寄存器是 16 位。多个寄存器组合成 32 位整数或浮点数时，必须按设备手册确认字节序和字序。

```python
from pymodbus.client import ModbusTcpClient
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.constants import Endian

client = ModbusTcpClient("192.168.1.100", port=502, timeout=3)

try:
    if not client.connect():
        raise RuntimeError("connect failed")

    rr = client.read_holding_registers(address=0, count=4, slave=1)
    if rr.isError():
        raise RuntimeError(rr)

    registers = rr.registers

    # 解析 uint16
    status_word = registers[0]

    # 从 16 位状态字中取 bit
    running = bool(status_word & (1 << 0))
    fault = bool(status_word & (1 << 1))
    remote_mode = bool(status_word & (1 << 2))

    print("running:", running)
    print("fault:", fault)
    print("remote mode:", remote_mode)

    # 解析 float32，占两个寄存器
    decoder = BinaryPayloadDecoder.fromRegisters(
        registers[2:4],
        byteorder=Endian.BIG,
        wordorder=Endian.BIG,
    )
    value = decoder.decode_32bit_float()
    print("float32 value:", value)

finally:
    client.close()
```

#### 6.7 批量采集点表示例

点表建议区分设备能力、工程显示地址和协议实际地址。`function` 不作为必填字段，标准读写功能码可由 `area`、`access` 和 `quantity` 推导；特殊设备再用 `read_function_code` / `write_function_code` 覆盖。

```yaml
device:
  name: meter_01
  protocol: modbus_tcp
  host: 192.168.1.100
  port: 502
  unit_id: 1
  supported_function_codes: [1, 2, 3, 4, 5, 6, 15, 16]
  max_read_coils: 2000
  max_read_discrete_inputs: 2000
  max_read_holding_registers: 125
  max_read_input_registers: 125
  max_write_coils: 1968
  max_write_holding_registers: 123
  single_outstanding_request: true

points:
  - name: voltage_a
    area: input_register
    address: 0
    display_address: 30001
    quantity: 2
    data_type: float32
    byte_order: big
    word_order: big
    scale: 1.0
    unit: V
    access: read

  - name: current_a
    area: input_register
    address: 2
    display_address: 30003
    quantity: 2
    data_type: float32
    byte_order: big
    word_order: big
    scale: 1.0
    unit: A
    access: read

  - name: run_command
    area: coil
    address: 10
    display_address: 00011
    quantity: 1
    data_type: bool
    access: write
    write_function_code: 5

  - name: status_word
    area: holding_register
    address: 20
    display_address: 40021
    quantity: 1
    data_type: uint16
    access: read
    read_function_code: 3

  - name: fault_bit
    area: holding_register
    address: 20
    display_address: 40021
    quantity: 1
    data_type: bool
    bit: 1
    access: read
    read_function_code: 3

  - name: heartbeat_counter
    area: holding_register
    address: 30
    display_address: 40031
    quantity: 1
    data_type: uint16
    access: read
    heartbeat: true
```

批量采集时应先把点表编译成读取计划：

```text
1. 按 device / unit_id 分组；
2. 按 area 和 read_function_code 分组；
3. 按连续 address 合并；
4. 按设备 max_read_* 限制拆包；
5. 每个读取块生成解析计划；
6. 每个读取块记录 send/receive 时间和通信质量。
```

示例：

```text
voltage_a: address 0, quantity 2
current_a: address 2, quantity 2

合并后一次读取：
area=input_register, address=0, count=4
```

### 7. 高性能采集方案

对于 **500+ 点、50Hz** 的采集场景，Modbus 的瓶颈主要来自：

- 请求/响应是同步事务模型；
- RTU 串口带宽低且半双工；
- 没有订阅推送；
- 单次请求长度受 PDU 限制；
- 设备处理能力和网关转发能力有限；
- 每个离散地址逐点读取会产生大量报文。

#### 7.1 RTU 场景

RTU 场景很难稳定达到大规模 50Hz 采集，除非点数很少、波特率较高、设备响应很快。

优化建议：

| 方案 | 说明 |
|------|------|
| 提高波特率 | 9600 改为 38400、115200，但要确认设备和总线质量支持 |
| 合并连续地址 | 一次读取连续寄存器，不要逐点读 |
| 按优先级分组 | 高频点少量读取，低频点降采样 |
| 多串口分段 | 多条 RS-485 总线并行采集 |
| 使用边缘网关 | 现场网关轮询 RTU，平台侧读网关缓存 |
| 避免频繁写操作 | 写操作会阻塞轮询并增加设备负载 |

#### 7.2 TCP 场景

Modbus TCP 的吞吐能力明显高于 RTU，但仍应采用批量读取策略。

推荐方案：

| 方案 | 说明 |
|------|------|
| 地址块合并 | 同一设备、同一功能码、连续地址合并成大块读取 |
| 连接复用 | 长连接复用，避免频繁建立 TCP 连接 |
| 异步并发 | 多设备并发采集，同一设备控制并发度 |
| 超时隔离 | 单设备超时不阻塞全局采集循环 |
| 点表预编译 | 启动时将点表编译成读取区间和解析计划 |
| 原始值留存 | 保存原始寄存器，便于排查字节序、比例系数问题 |

#### 7.3 结构化打包方案

如果 PLC 端可改造，最优方案是把高频数据打包到连续 Holding Register 或 Input Register 区间：

```text
40001 ~ 40050 : 高频遥测块
40051 ~ 40080 : 状态字块
40100 ~ 40120 : 控制参数块
```

采集端只需少量批量读取即可获得全部数据。对于实时性要求更高的场景，应考虑 OPC UA Subscription、IEC 61850 GOOSE/SV、厂商实时协议或消息总线，而不是强行用 Modbus 做大规模高频采集。

### 8. 工程配置与排查

#### 8.1 RTU 接线检查

| 项目 | 检查点 |
|------|--------|
| A/B 线 | 厂商标注可能相反，必要时交换 A/B 测试 |
| 终端电阻 | 总线两端加 120Ω，短线低速可视情况不加 |
| 偏置电阻 | 空闲总线应保持稳定电平 |
| 接地 | 屏蔽层和参考地按现场规范处理 |
| 从站地址 | 同一总线上不能重复 |
| 串口参数 | baudrate、parity、stopbits 必须一致 |
| 主站数量 | 标准 RTU 总线通常只允许一个主站 |

#### 8.2 TCP 连接检查

| 项目 | 检查点 |
|------|--------|
| IP / Port | 默认端口 `502`，部分设备使用自定义端口 |
| Unit ID | 直连设备和网关场景要求不同 |
| 防火墙 | 工控机、设备、交换机 ACL 均可能阻断 |
| 并发连接数 | 低端设备可能只允许 1~4 个 TCP 连接 |
| 空闲超时 | 长连接可能被设备或 NAT 断开 |
| 事务 ID | 客户端应正确匹配响应，避免并发错包 |

#### 8.3 常见问题

| 现象 | 可能原因 |
|------|----------|
| 连接成功但读不到数据 | Unit ID 错误、功能码错误、地址偏移错误 |
| 读到全 0 或异常值 | 地址区错、字序错、比例系数缺失 |
| 偶发超时 | 串口干扰、总线过长、设备响应慢、轮询过密 |
| CRC 错误 | 串口参数不一致、线缆干扰、A/B 反接、接地问题 |
| Exception 02 | 地址越界或人工地址未减 1 |
| Exception 03 | 读取数量超过设备限制 |
| TCP 经常断开 | 设备连接数限制、空闲超时、防火墙策略 |

### 9. 安全警告

Modbus RTU 和传统 Modbus TCP 均没有内置认证、授权和加密机制。任何能访问链路的实体都可能读取数据或写入控制寄存器。

安全建议：

- 禁止将 Modbus TCP `502` 端口直接暴露到公网；
- 使用工业防火墙、白名单和 VLAN 隔离；
- 对写功能码进行网关侧限制，尤其是 `05`、`06`、`15`、`16`；
- 远程访问应通过 VPN、专线或安全网关；
- 高风险控制点应增加 PLC 侧联锁和权限校验；
- 保留通信日志，记录写操作来源、时间、功能码、地址和值；
- 对关键网络可考虑 Modbus Security / TLS 或协议隔离网关，但要确认设备兼容性。

### 10. 参考资料

- Modbus Organization：Modbus Application Protocol Specification V1.1b3
- Modbus Organization：Modbus over Serial Line Specification and Implementation Guide V1.02
- PyModbus Documentation
