## 第一部分：OPC UA（Open Platform Communications Unified Architecture）

### 1. 标准概述

OPC UA 是 OPC Foundation 发布的工业通信标准，正式标准系列为 **IEC 62541**。它不是简单的“寄存器读写协议”，而是一个同时包含 **信息模型、服务接口、安全机制、传输映射、订阅机制、事件模型、历史访问、PubSub** 的工业互操作架构。

OPC UA 的核心设计哲学是：

> **用统一的信息模型描述设备和数据，用统一的服务访问这些模型，再通过可替换的传输协议完成通信。**

核心目标：

- **跨平台**：不再依赖 Windows COM/DCOM，这是 OPC Classic 与 OPC UA 的关键区别。
- **厂商互操作**：不同 PLC、SCADA、网关、边缘设备、MES/云平台可以通过统一模型交互。
- **语义化建模**：变量不只是地址和值，还可以携带单位、工程范围、质量码、时间戳、类型、对象关系。
- **安全通信**：内置证书、签名、加密、用户认证、权限控制等安全机制。
- **多种通信模式**：支持 Client/Server，也支持 PubSub。
- **可扩展信息模型**：通过 Companion Specification 描述行业专用模型，如 PLCopen、PackML、Machinery、Robotics、DI、FDI 等。

与 ADS、Modbus、普通 TCP 私有协议相比，OPC UA 的重点不只是“把值读出来”，而是让客户端能理解：

- 这个值属于哪个设备对象；
- 是状态、测量值、控制点还是配置参数；
- 数据类型是什么；
- 单位是什么；
- 当前值是否可信；
- 时间戳来自服务器还是数据源；
- 是否允许写入；
- 是否可以订阅；
- 是否有历史数据；
- 是否有报警事件。

### 2. 核心概念体系

#### 2.1 关键术语

| 术语 | 含义 | 类比 |
|------|------|------|
| **Server** | OPC UA 服务器，暴露地址空间、变量、对象、方法、事件和历史数据 | 工厂里的资料库 / 设备网关 |
| **Client** | OPC UA 客户端，连接 Server，浏览、读取、写入、订阅、调用方法 | 访问资料库的人 |
| **Endpoint** | Server 对外暴露的连接入口，包含 URL、安全策略、安全模式、用户认证方式 | 大门 + 门禁规则 |
| **Endpoint URL** | 连接地址，如 `opc.tcp://192.168.1.10:4840` | 门牌号 |
| **AddressSpace** | 地址空间，Server 暴露的对象、变量、方法、类型和引用关系的整体 | 图书馆的全馆目录 |
| **Node** | 地址空间中的基本元素，一切对象、变量、方法、类型都是 Node | 一个目录项 |
| **NodeClass** | 节点类别，如 Object、Variable、Method、ObjectType、VariableType、DataType、ReferenceType、View | 目录项类型 |
| **NodeId** | 节点在某个 Server 地址空间中的唯一标识，服务调用时用于读、写、订阅、调用 | 数据点的身份证 |
| **Namespace URI** | 命名空间的稳定 URI，表示“谁负责定义这些 NodeId 的 Identifier” | 出版社 / 标准来源的正式名称 |
| **NamespaceIndex** | Server 运行时把 Namespace URI 映射成的短整数，如 `ns=2` | 临时编号 / 书架编号 |
| **NamespaceArray** | Server 暴露的 URI 数组，索引位置就是 NamespaceIndex | 编号 ↔ 出版社名称对照表 |
| **ExpandedNodeId** | 带 Namespace URI 的扩展节点标识，可跨 Server/跨会话表达节点来源 | 带出版社全名的身份证 |
| **BrowseName** | 浏览名称，格式通常为 `NamespaceIndex:Name`，用于人机浏览和路径定位，但不保证全局唯一 | 树上的名字 |
| **DisplayName** | 展示名称，面向人读，可本地化 | 显示标签 |
| **Object** | 对象节点，表示设备、部件、功能块等实体 | 一个设备或文件夹 |
| **Variable** | 变量节点，表示可读写的数据值 | 传感器点位 / PLC 变量 |
| **Method** | 方法节点，表示可被客户端调用的操作 | 远程函数 |
| **Reference** | 节点之间的关系，如 `HasComponent`、`Organizes`、`HasTypeDefinition` | 目录之间的连接线 |
| **DataValue** | 变量读取得到的完整数据，包含 Value、StatusCode、SourceTimestamp、ServerTimestamp | 值 + 质量 + 时间 |
| **StatusCode** | 质量码，表示数据是否可信，如 `Good`、`Bad`、`Uncertain` | 数据健康状态 |
| **Session** | 客户端与服务器之间的逻辑会话，承载用户身份和服务调用上下文 | 登录会话 |
| **SecureChannel** | 安全通道，负责消息签名、加密、序号、防重放 | 加密隧道 |
| **Subscription** | 订阅，客户端创建的推送通道，用于接收数据变化或事件 | 订阅列表 |
| **MonitoredItem** | 被监视的具体节点或事件源，挂在某个 Subscription 下 | 订阅列表中的一个点位 |
| **PubSub** | 发布/订阅通信模型，适合多播、边缘、云和一对多数据分发 | 广播频道 |
| **NodeSet2 XML** | OPC UA 信息模型的 XML 表达，可用于导入/导出地址空间 | 模型图纸 |

#### 2.2 NodeId、Namespace URI 与 NamespaceIndex 的关系

OPC UA 中定位变量、对象、方法、类型，核心使用 **NodeId**。但 NodeId 里面的 `ns=2` 不是稳定语义本身，而是 **Namespace URI 在当前 Server 的 NamespaceArray 中的运行时索引**。

三者关系如下：

```text
Namespace URI ──在 Server 的 NamespaceArray 中占据某个位置──> NamespaceIndex
NamespaceIndex + Identifier ────────────────────────────────> NodeId
```

例如服务器启动后暴露如下 `NamespaceArray`：

```text
Index 0: http://opcfoundation.org/UA/
Index 1: urn:vendor:plc:base
Index 2: urn:demo:windfarm:opcua
```

对应的运行时 NodeId 示例：

```text
ns=2;s=WindTurbine_001.Power
```

完整含义是：

```text
Namespace URI : urn:demo:windfarm:opcua
Identifier    : s=WindTurbine_001.Power
NodeId        : ns=2;s=WindTurbine_001.Power
```

常见 NodeId 格式如下：

| 格式 | 示例 | 说明 |
|------|------|------|
| 数字型 | `ns=2;i=1001` | 命名空间索引 2，数字 ID 1001 |
| 字符串型 | `ns=2;s=Device1.Temperature` | 命名空间索引 2，字符串 ID |
| GUID 型 | `ns=3;g=550e8400-e29b-41d4-a716-446655440000` | 命名空间索引 3，GUID 标识 |
| ByteString 型 | `ns=4;b=MDEyMzQ=` | 命名空间索引 4，字节串标识 |

其中：

- `ns=0` 固定指向 OPC UA 标准命名空间：`http://opcfoundation.org/UA/`。
- `ns=1`、`ns=2` 等由 Server 的 `NamespaceArray` 决定，可能对应厂商模型、行业模型、设备模型或项目模型。
- `i=...` 表示 numeric identifier。
- `s=...` 表示 string identifier。
- `g=...` 表示 GUID identifier。
- `b=...` 表示 ByteString identifier。

#### 2.3 NodeId 与 Namespace URI 的工程保存规则

OPC UA 工程接入中应区分 **运行时调用标识** 与 **长期配置标识**：服务调用使用当前会话可解析的 NodeId；点表、数据库和配置文件长期保存 Namespace URI 与 Identifier。

| 场景 | 应使用/保存什么 | 原因 |
|------|----------------|------|
| 当前已连接会话内读写订阅 | `NodeId`，如 `ns=2;s=WindTurbine_001.Power` | OPC UA Read / Write / Call / Subscribe 等服务直接使用 NodeId |
| 点表、数据库、配置文件长期保存 | `namespace_uri + identifier_type + identifier` | `NamespaceIndex` 可能随 Server 启动、模型加载顺序、网关配置变化而变化 |
| 重连后恢复点表 | 先读取 `NamespaceArray`，用 `namespace_uri` 找到新的 `NamespaceIndex`，再拼回运行时 NodeId | 避免 `ns=2` 变成另一个模型后读错点 |
| 人工排查和浏览 | 额外保存 `browse_path` / `display_name` | 便于定位，但不能替代 NodeId |

不推荐的长期保存方式：

```json
{
  "node_id": "ns=2;i=1001"
}
```

该方式的风险在于：`ns=2` 只是“当前这台 Server 此刻的第 2 个命名空间”。如果下一次启动后 NamespaceArray 变成：

```text
Index 0: http://opcfoundation.org/UA/
Index 1: urn:vendor:plc:base
Index 2: http://opcfoundation.org/UA/DI/
Index 3: urn:demo:windfarm:opcua
```

此时原来的：

```text
ns=2;i=1001
```

就不再指向 `urn:demo:windfarm:opcua`，而可能指向 DI 模型下的另一个节点，轻则读不到，重则读错点。

推荐的长期保存方式：

```json
{
  "namespace_uri": "urn:demo:windfarm:opcua",
  "identifier_type": "String",
  "identifier": "WindTurbine_001.Power",
  "runtime_node_id_cache": "ns=2;s=WindTurbine_001.Power",
  "browse_path": "Objects/DeviceSet/WindTurbine_001/Power"
}
```

重连后恢复流程如下：

```text
1. 连接 Server
2. 读取 Server_NamespaceArray
3. 查找 namespace_uri = urn:demo:windfarm:opcua 当前对应哪个 index
4. 假设当前 index = 3
5. 重新生成运行时 NodeId：ns=3;s=WindTurbine_001.Power
6. 用新的 NodeId 创建 Read / Write / Subscription / Method Call
```

如果 SDK 支持 `ExpandedNodeId` 或 `nsu=<NamespaceUri>;...` 这类字符串形式，也可以用它表达“URI + Identifier”。但多数服务调用最终仍会在连接到具体 Server 后解析成普通 NodeId。

#### 2.4 NamespaceIndex 与节点归属判定

节点所属 namespace 由节点自身的 `NodeId` 决定，浏览名所属 namespace 由 `BrowseName` 前缀决定；父子挂接位置不决定节点自身的 namespace。

例如：

```xml
<UAObject NodeId="ns=1;s=WindTurbine_001"
          BrowseName="1:WindTurbine_001">
```

含义是：

- 该 `UAObject` 的 NodeId 使用 `ns=1`。
- `ns=1` 对应 NodeSet2 文件中 `<NamespaceUris>` 的第 1 个自定义 URI，或运行时 Server `NamespaceArray[1]`。
- 因此该对象由这个 URI 对应的命名机构定义。

另一个变量示例如下：

```xml
<UAVariable NodeId="ns=1;s=WindTurbine_001.Power"
            BrowseName="1:Power"
            DataType="Double">
```

这个变量也属于 `ns=1`。但它的 `DataType="Double"` 通过 Alias 指向标准数据类型 `i=11`，也就是 `ns=0;i=11`。因此，一个节点可以：

- **自身 NodeId 属于项目命名空间**，如 `urn:demo:windfarm:opcua`；
- **类型定义引用标准命名空间**，如 `BaseObjectType`、`Double`、`HasComponent`；
- **也可以引用其他 Companion Specification 的类型**，如 DI 的 `DeviceType`。

节点归属判断规则如下：

| 判断对象 | 看哪里 | 示例 | 结论 |
|----------|--------|------|------|
| 节点自身属于哪个 ns | `NodeId` 的 `ns=` | `NodeId="ns=1;s=WindTurbine_001"` | 该节点属于 ns=1 |
| 浏览名属于哪个 ns | `BrowseName` 冒号前缀 | `BrowseName="1:Power"` | 浏览名由 ns=1 定义 |
| 节点的类型来自哪里 | `HasTypeDefinition` 或 `DataType` | `HasTypeDefinition → BaseObjectType` | 类型可来自 ns=0 或其他模型 |
| 节点挂在哪里 | `Organizes` / `HasComponent` 等 Reference | 挂在 `Objects` 下 | 不决定节点自身 ns |

NodeSet2 文件中的 `ns=1` 与运行时 Server 中的 `ns=1` 不一定永久相同。NodeSet2 内部通常把 `<NamespaceUris>` 中第一个自定义 URI 记作 `ns=1`；Server 加载多个模型后，运行时可能把它分配成 `ns=2`、`ns=3` 或其他索引。因此导入模型、生成点表、重连恢复时都应以 **Namespace URI** 为稳定依据。

#### 2.5 地址空间结构

OPC UA 地址空间是一个图结构，而不是单纯树结构。但工程上通常把它浏览成树：

```text
Root
├── Objects
│   ├── Server
│   ├── DeviceSet
│   │   ├── WindTurbine_001
│   │   │   ├── Measurements
│   │   │   │   ├── WindSpeed
│   │   │   │   ├── Power
│   │   │   │   └── RotorSpeed
│   │   │   ├── Status
│   │   │   │   ├── Running
│   │   │   │   └── FaultCode
│   │   │   └── Methods
│   │   │       ├── Start
│   │   │       └── Stop
│   │   └── WindTurbine_002
│   └── Aliases
├── Types
│   ├── ObjectTypes
│   ├── VariableTypes
│   ├── DataTypes
│   └── ReferenceTypes
└── Views
```

常见的引用关系：

| ReferenceType | 作用 |
|---------------|------|
| `Organizes` | 组织关系，类似文件夹归类 |
| `HasComponent` | 对象包含组件，如设备包含变量 |
| `HasProperty` | 节点包含属性，如工程单位、范围 |
| `HasTypeDefinition` | 实例指向类型定义 |
| `HasSubtype` | 类型继承关系 |
| `HasEventSource` | 对象作为事件源 |
| `HasNotifier` | 对象可向上级传播事件 |

#### 2.6 Variable 与 DataValue

读取一个变量时，客户端通常得到的不是裸值，而是 `DataValue`：

| 字段 | 含义 |
|------|------|
| `Value` | 实际值，如 `12.5`、`true`、`"RUNNING"` |
| `StatusCode` | 数据质量，如 `Good`、`BadNotConnected`、`Uncertain` |
| `SourceTimestamp` | 数据源产生该值的时间，一般来自 PLC、采集驱动或底层设备 |
| `ServerTimestamp` | OPC UA Server 处理该值的时间 |
| `SourcePicoseconds` | 源时间戳的皮秒补充精度，可选 |
| `ServerPicoseconds` | 服务器时间戳的皮秒补充精度，可选 |

工程上应区分：

- **SourceTimestamp**：更接近现场数据发生时间。
- **ServerTimestamp**：更接近 OPC UA Server 接收到或处理数据的时间。
- **采集系统入库时间**：是采集程序写入数据库的时间，不等同于前两者。

对于时序数据库，应优先使用 `SourceTimestamp`，没有时再退化为 `ServerTimestamp` 或采集端时间。

#### 2.7 信息模型与 Companion Specification

OPC UA 的强项是信息模型。服务器不仅能暴露变量，还能暴露类型系统：

```text
ObjectType → Object 实例
VariableType → Variable 实例
DataType → Value 的数据结构
ReferenceType → 节点关系语义
Method → Object 可执行的行为
```

例如一个风机对象可以定义为：

```text
WindTurbineType
├── Measurements
│   ├── WindSpeed: Double, EngineeringUnit = m/s
│   ├── Power: Double, EngineeringUnit = kW
│   └── RotorSpeed: Double, EngineeringUnit = rpm
├── Status
│   ├── Running: Boolean
│   └── FaultCode: Int32
└── Methods
    ├── Start()
    ├── Stop()
    └── ResetFault(resetCode) -> result
```

OPC UA 的对象模型并不局限于数据点表达，而是采用 **Object = Variables + Methods + References** 的结构：

- `Variable` 表示对象的状态或参数，例如功率、风速、运行状态。
- `Method` 表示对象可执行的动作，例如启动、停止、复位故障、切换模式。
- `Reference` 表示对象、变量、方法、类型之间的关系。

Method 是一种标准 NodeClass，有自己的 `NodeId`，通过 `Call` 服务调用。它通常挂在某个 Object 下，调用时需要同时给出：

```text
ObjectId + MethodId + InputArguments
```

例如：

```text
ObjectId : ns=2;s=WindTurbine_001
MethodId : ns=2;s=WindTurbine_001.ResetFault
Input    : resetCode = 1001
```

Method 与直接 Write 的边界如下：

| 场景 | 更适合 Variable Write | 更适合 Method Call |
|------|----------------------|--------------------|
| 修改设定值 | ✅ | - |
| 写入参数 | ✅ | - |
| 启动/停止设备 | ⚠️ 可做但语义弱 | ✅ |
| 故障复位 | ⚠️ 可做但容易约定不清 | ✅ |
| 带参数、带返回结果的操作 | ❌ | ✅ |
| 需要审计“谁执行了什么动作” | ⚠️ | ✅ |

#### 2.8 Companion Specification 的定位

**Companion Specification** 是某个行业或设备领域基于 OPC UA Core 机制制定的标准化信息模型规范。它不是通信协议、SDK、厂商点表或运行时插件，而是对某类设备、系统或业务对象的 OPC UA 建模方式进行统一约束。

它通常包含两部分：

1. **规范文档**：定义对象类型、变量、方法、引用关系、状态机、语义约束。
2. **NodeSet2 XML**：把这些类型和节点用机器可读的方式表达出来，供 Server SDK、建模工具或测试工具导入。

它的核心作用是保证不同厂商不仅能通过 OPC UA 连接，而且能用相同语义描述同类设备。

缺少 Companion Specification 时，不同厂商可能都暴露“温度”，但路径、名称、单位、对象组织方式完全不同：

```text
厂商 A: ns=2;s=Device1.Temp
厂商 B: ns=4;s=T_001
厂商 C: ns=3;i=50012
```

客户端虽然能够读取数值，但无法稳定判断这些点在语义上是否等价。

采用 Companion Specification 后，模型会规定以下内容：

```text
某类设备必须/可以有哪些 ObjectType
这些 ObjectType 下有哪些组件、属性、方法
变量的数据类型、单位、建模规则是什么
状态机如何表示
报警、事件、诊断如何挂接
命名空间 URI 是什么
```

工程使用方式：

| 角色 | 如何使用 Companion Specification |
|------|----------------------------------|
| 设备/网关 Server | 实现或导入该规范定义的 ObjectType、Variable、Method、Reference |
| Client / SCADA / 平台 | 根据标准类型和引用关系识别设备语义，而不是硬编码厂商点名 |
| 建模工具 | 加载 Companion 的 NodeSet2 XML，再叠加项目自己的实例模型 |
| 测试/认证 | 检查 Server 是否按规范暴露了必需节点和语义 |

常见 Companion Specification / 信息模型如下：

| Companion / 模型 | 用途 |
|------------------|------|
| OPC UA DI（Device Integration） | 通用设备模型，很多设备类模型会继承或复用它 |
| PLCopen OPC UA | PLC 控制器、程序、功能块相关模型 |
| PackML | 包装机械状态机 |
| Machinery | 机械设备通用模型 |
| Robotics | 机器人模型 |
| CNC | 数控机床模型 |
| AutoID | RFID、条码等自动识别设备 |

工程结论：

> Companion Specification 负责“语义标准化”，OPC UA Core 负责“通用建模与通信机制”。仅将 PLC 变量平铺为一组 `ns=2;s=xxx` 点位时，虽然通信协议采用 OPC UA，但尚未形成行业语义互操作能力。

### 3. 通信协议栈与消息结构

#### 3.1 协议栈

OPC UA 协议栈需要区分 Endpoint URL scheme、OPC UA 传输映射和操作系统 TCP/IP 协议栈：

- **`opc.tcp`**：Endpoint URL 的 scheme，表示使用 **OPC UA TCP transport mapping**。
- **UA TCP / UACP**：OPC UA 自己的连接协议与消息分块、HEL/ACK、OPN、MSG、CLO 等机制。
- **TCP**：操作系统网络协议栈中的传输层 TCP。
- **IP**：网络层协议。

因此，`opc.tcp` 与 TCP 不是两层重复的 TCP。`opc.tcp` 表示 OPC UA TCP transport mapping，底层仍通过操作系统 TCP/IP socket 承载。整体分层如下：

```text
OPC UA Services / Session / SecureChannel
        ↓
UA Binary Encoding
        ↓
OPC UA TCP transport mapping（Endpoint scheme = opc.tcp）
        ↓
TCP（传输层，常见端口 4840）
        ↓
IP（网络层）
        ↓
Ethernet / Wi-Fi / 其他链路层
```

按工程分层可写成：

| 层级 | 协议/组件 | 说明 |
|------|-----------|------|
| 信息模型层 | AddressSpace / Node / Type / Reference | 描述设备、变量、方法、事件和类型关系 |
| 服务层 | Read / Write / Browse / Call / CreateSubscription / Publish 等 | 客户端访问服务器的标准服务 |
| 会话层 | Session | 用户登录、权限上下文、服务调用上下文 |
| 安全通道层 | SecureChannel | 签名、加密、证书校验、序号、防重放 |
| 编码层 | UA Binary / XML / JSON | 将服务请求与响应编码成字节流或文本 |
| OPC UA 传输映射层 | UA TCP / HTTPS / WebSocket；PubSub 可映射到 UDP、MQTT、AMQP、Ethernet 等 | 定义 OPC UA 消息如何放到具体网络通道上 |
| 传输层 | TCP / UDP | 操作系统网络协议栈中的传输层 |
| 网络层 | IP | 寻址和路由 |
| 链路层 | Ethernet / Wi-Fi / TSN 等 | 以太网帧、无线链路或确定性链路 |

最常见的工业现场 Client/Server 部署是：

```text
OPC UA Client
  ↓ Services：Read / Write / Browse / Call / Subscription
Session
  ↓
SecureChannel
  ↓
UA Binary Encoding
  ↓
OPC UA TCP / UACP（opc.tcp）
  ↓
TCP 4840
  ↓
IP
  ↓
Ethernet
  ↓
OPC UA Server
```

`opc.tcp://192.168.1.10:4840` 中的 `opc.tcp` 不是一个新的底层网络协议名，而是告诉客户端：“这个 Endpoint 使用 OPC UA Binary over OPC UA TCP mapping，底层再跑在 TCP/IP socket 上”。

#### 3.2 Endpoint URL 与端口

典型 Endpoint URL：

```text
opc.tcp://192.168.1.10:4840
opc.tcp://plc-01.local:4840/UA/Server
opc.tcp://127.0.0.1:4840/freeopcua/server/
```

组成：

| 部分 | 示例 | 含义 |
|------|------|------|
| Scheme | `opc.tcp` | 使用 UA TCP 传输 |
| Host | `192.168.1.10` | 服务器 IP 或主机名 |
| Port | `4840` | OPC UA TCP 常见默认端口 |
| Path | `/UA/Server` | 服务器应用路径，可选 |

注意：

- `4840` 是常见默认端口，但并非所有设备都固定使用它。
- 同一台设备上可以有多个 OPC UA Server，每个 Server 可使用不同端口或路径。
- Endpoint URL 只是连接入口，不等于具体变量地址。
- 变量地址应通过 `NodeId` 定位。

#### 3.3 Endpoint 安全参数

客户端连接前通常先调用 `GetEndpoints`，获取服务器支持的 Endpoint 列表。

每个 Endpoint 通常包含：

| 参数 | 说明 |
|------|------|
| `EndpointUrl` | 连接地址 |
| `SecurityPolicyUri` | 安全策略，如 `Basic256Sha256` |
| `SecurityMode` | 消息安全模式：`None`、`Sign`、`SignAndEncrypt` |
| `ServerCertificate` | 服务器应用实例证书 |
| `UserIdentityTokens` | 支持的用户认证方式，如 Anonymous、Username、Certificate |
| `TransportProfileUri` | 传输 Profile，如 UA TCP Binary |
| `SecurityLevel` | 安全等级提示 |

安全模式：

| SecurityMode | 含义 | 工程建议 |
|--------------|------|----------|
| `None` | 不签名、不加密 | 仅限本机测试或隔离实验环境 |
| `Sign` | 消息签名，防篡改，但不加密内容 | 可用于低敏数据内网场景 |
| `SignAndEncrypt` | 消息签名 + 加密 | 工业生产环境优先使用 |

常见安全策略：

| SecurityPolicy | 说明 |
|----------------|------|
| `None` | 无安全策略 |
| `Basic256Sha256` | 常用安全策略之一 |
| `Aes128_Sha256_RsaOaep` | 新版 Profile 中常见 |
| `Aes256_Sha256_RsaPss` | 新版 Profile 中更强的策略 |

工程注意：

> 很多设备为了兼容性会默认开启 `SecurityPolicy=None` 和匿名访问。接入生产系统时应显式关闭或限制这类 Endpoint。

#### 3.4 UA TCP 消息结构

以最常见的 UA Binary over UA TCP 为例，消息不是简单的一包请求对应一包 TCP 报文。OPC UA 支持消息分块（Chunking），一个逻辑消息可能拆成多个 MessageChunk。

概念结构：

```text
UA TCP Message
├── Message Header
│   ├── MessageType
│   ├── ChunkType
│   └── MessageSize
├── Security Header
│   ├── SecureChannelId
│   ├── TokenId
│   ├── SecurityPolicyUri / SenderCertificate / ReceiverCertificateThumbprint
│   └── ...
├── Sequence Header
│   ├── SequenceNumber
│   └── RequestId
└── Message Body
    └── Encoded Service Request / Response
```

关键字段如下：

| 字段 | 含义 |
|------|------|
| `MessageType` | 消息类型，如 `HEL`、`ACK`、`OPN`、`MSG`、`CLO`、`ERR` |
| `ChunkType` | 分块类型，如 `F`（Final）、`C`（Continuation）、`A`（Abort） |
| `MessageSize` | 当前消息块大小 |
| `SecureChannelId` | 安全通道 ID |
| `SequenceNumber` | 消息序号，用于检测重放、乱序等 |
| `RequestId` | 请求 ID，用于匹配请求与响应 |
| `Message Body` | 具体服务内容，如 ReadRequest、WriteRequest、PublishResponse |

#### 3.5 Client/Server 连接流程

典型连接流程如下：

```text
1. TCP 连接建立
2. HEL / ACK：协商缓冲区、消息大小、协议版本
3. OpenSecureChannel：建立安全通道
4. CreateSession：创建会话
5. ActivateSession：激活会话并完成用户认证
6. Browse / Read / Write / Call / CreateSubscription
7. CloseSession
8. CloseSecureChannel
9. TCP 连接关闭
```

更细化说明：

1. **TCP 连接**
   - 客户端连接到 Endpoint URL。
   - 常见端口为 `4840`。

2. **HEL / ACK**
   - 客户端发送 Hello。
   - 服务器返回 Acknowledge。
   - 协商最大消息大小、接收缓冲区大小、发送缓冲区大小等。

3. **OpenSecureChannel**
   - 建立安全通道。
   - 根据 Endpoint 的 SecurityPolicy 和 SecurityMode 进行签名、加密和证书校验。

4. **CreateSession**
   - 创建逻辑会话。
   - 获取服务器 nonce、会话 ID、认证上下文等。

5. **ActivateSession**
   - 提交用户身份令牌。
   - 支持匿名、用户名密码、证书等认证方式。

6. **业务服务调用**
   - Browse：浏览地址空间。
   - Read：读取变量。
   - Write：写入变量。
   - Call：调用方法。
   - CreateSubscription：创建订阅。
   - Publish：接收订阅通知。

7. **关闭**
   - 先关闭 Session，再关闭 SecureChannel。

### 4. 通信方式

#### 4.1 浏览（Browse）

浏览用于发现地址空间结构。

| 操作 | 说明 |
|------|------|
| `Browse` | 获取某个节点的引用列表 |
| `BrowseNext` | 获取分页浏览结果 |
| `TranslateBrowsePathsToNodeIds` | 根据路径转换为 NodeId |
| `Read` | 读取节点属性，如 DisplayName、DataType、Value、AccessLevel |

典型流程：

1. 从 `Root` 或 `Objects` 开始。
2. 沿 `Organizes`、`HasComponent` 等引用向下浏览。
3. 找到目标 Variable。
4. 读取其 `NodeId`、`DataType`、`AccessLevel`、`EngineeringUnits` 等属性。
5. 将稳定标识保存到点表。

#### 4.2 读取（Read）

读取方式适用于：

- 初始化加载；
- 低频采集；
- 手动查询；
- 订阅断线后的补读；
- 读取配置参数和元数据。

读取内容可以是变量值，也可以是节点属性。

常见读取目标：

| Attribute | 说明 |
|-----------|------|
| `Value` | 变量当前值 |
| `NodeId` | 节点 ID |
| `BrowseName` | 浏览名 |
| `DisplayName` | 显示名 |
| `Description` | 描述 |
| `DataType` | 数据类型 |
| `ValueRank` | 标量/数组维度 |
| `ArrayDimensions` | 数组维度 |
| `AccessLevel` | 当前访问能力 |
| `Historizing` | 是否支持历史 |

#### 4.3 写入（Write）

写入用于修改变量值。

典型适用场景：

- 写入设定值；
- 下发控制参数；
- 修改模式；
- 写入模拟量输出；
- 写入中间变量。

工程注意：

- 写入前必须检查 `AccessLevel` 或 `UserAccessLevel`。
- 写入并不等于设备已执行动作，只表示 Server 接受了写请求。
- 控制类动作更推荐使用明确的 Method 或状态机模型，而不是直接写某个布尔变量。
- 写入必须检查返回 `StatusCode`，不能只看 API 是否抛异常。

#### 4.4 订阅（Subscription）与 MonitoredItem

订阅是 OPC UA 高频采集最常用方式。它不是 TCP 层的裸推送，而是 OPC UA 服务层的机制：

```text
Client 创建 Subscription
Client 在 Subscription 下创建 MonitoredItem
Server 按 SamplingInterval 采样
Server 将变化放入队列
Client 持续发送 PublishRequest
Server 在 PublishResponse 中返回通知
```

关键参数：

| 参数 | 所属对象 | 含义 |
|------|----------|------|
| `PublishingInterval` | Subscription | Server 向客户端发布通知的周期 |
| `SamplingInterval` | MonitoredItem | Server 对数据源采样的周期 |
| `QueueSize` | MonitoredItem | 每个监视项缓存多少条变化 |
| `DiscardOldest` | MonitoredItem | 队列满时是否丢弃最旧值 |
| `DataChangeFilter` | MonitoredItem | 数据变化过滤，如绝对死区、百分比死区 |
| `PublishingEnabled` | Subscription | 是否启用发布 |
| `LifetimeCount` | Subscription | 生命周期计数，超过后订阅失效 |
| `KeepAliveCount` | Subscription | 无数据变化时发送 keepalive 的周期 |

工程理解：

- `SamplingInterval` 决定服务器多久看一次变量。
- `PublishingInterval` 决定服务器多久把通知打包发给客户端。
- 变量变化快，但 `PublishingInterval` 慢，客户端看到的是打包后的结果。
- `QueueSize=1` 时只保留最新值，适合实时监控。
- `QueueSize>1` 时可保留中间变化，适合事件密集但不能丢变化的场景。
- 服务器可能不接受客户端请求的周期，会返回 revised 参数，客户端必须读取并记录。

#### 4.5 事件与报警（Events / Alarms & Conditions）

OPC UA 不仅支持数据变化，也支持事件。

常见事件源：

- 设备对象；
- 生产线对象；
- Server 对象；
- 报警条件对象；
- 状态机对象。

事件订阅与变量订阅类似，但 MonitoredItem 监视的是事件源节点，而不是某个变量值。

常见事件字段：

| 字段 | 含义 |
|------|------|
| `EventId` | 事件唯一 ID |
| `EventType` | 事件类型 |
| `SourceNode` | 事件源节点 |
| `SourceName` | 事件源名称 |
| `Time` | 事件发生时间 |
| `ReceiveTime` | 服务器接收时间 |
| `Severity` | 严重程度 |
| `Message` | 事件消息 |
| `ConditionName` | 条件名称 |
| `AckedState` | 是否已确认 |
| `ActiveState` | 是否激活 |

典型应用：

- 故障报警；
- 状态切换；
- 启停记录；
- 操作员动作；
- 设备诊断事件。

#### 4.6 方法调用（Method Call）

Method 是 OPC UA 中的远程函数调用机制。

示例：

```text
WindTurbine_001.Start()
WindTurbine_001.Stop()
Device.ResetFault()
Controller.SwitchMode(mode)
```

Method 可以有输入参数和输出参数：

```text
CallRequest
├── ObjectId: ns=2;s=Device1
├── MethodId: ns=2;s=Device1.ResetFault
└── InputArguments
    └── resetCode = 1001
```

Method Call 与 Write 对比如下：

| 对比项 | Write | Method Call |
|--------|-------|-------------|
| 语义 | 修改某个变量值 | 执行动作 |
| 输入 | 单个或多个变量值 | 明确的参数列表 |
| 输出 | StatusCode | StatusCode + OutputArguments |
| 适用 | 设定值、参数、变量 | 启停、复位、切换模式、执行命令 |
| 可读性 | 依赖约定 | 模型语义更清晰 |

#### 4.7 历史访问（Historical Access）

如果服务器支持 Historical Access，客户端可以读取历史数据，而不是只能读取当前值。

常见能力：

| 操作 | 说明 |
|------|------|
| `HistoryReadRaw` | 读取原始历史值 |
| `HistoryReadProcessed` | 读取聚合值，如平均、最大、最小 |
| `HistoryUpdate` | 写入或修改历史数据，取决于服务器权限 |

典型应用：

- 从 PLC 网关补采断线期间数据；
- 从厂商 OPC UA Historian 读取历史趋势；
- 做报表或追溯分析。

注意：

- 不是所有 OPC UA Server 都支持历史访问。
- `Historizing=True` 只表示节点可能支持历史，仍需测试服务能力。
- 历史查询可能对服务器负载较大，应限制时间范围和点位数量。

#### 4.8 PubSub

OPC UA PubSub 是不同于传统 Client/Server 的通信模式，适合一对多、边缘到云、多播分发等场景。

典型结构：

```text
Publisher
├── PublishedDataSet
│   ├── Field1
│   ├── Field2
│   └── Field3
├── WriterGroup
└── DataSetWriter
    ↓
NetworkMessage
    ↓
UDP Multicast / MQTT / AMQP / Ethernet
    ↓
Subscriber
```

核心概念：

| 术语 | 含义 |
|------|------|
| `PublishedDataSet` | 要发布的数据集合 |
| `DataSetWriter` | 将数据集写入 NetworkMessage 的发布者 |
| `WriterGroup` | 一组 DataSetWriter 的发布配置 |
| `DataSetReader` | 订阅端的数据集读取器 |
| `NetworkMessage` | 网络上传输的 PubSub 消息 |
| `UADP` | UA Datagram Protocol，二进制 PubSub 消息映射 |
| `JSON Mapping` | JSON 编码的 PubSub 消息映射 |

传输方式：

| 方式 | 特点 | 适用场景 |
|------|------|----------|
| UDP Multicast | 无 Broker，局域网多播，低延迟 | 现场网、边缘网 |
| MQTT | 通过 Broker 转发，易穿越网络边界 | 边缘到云、跨网络分发 |
| AMQP | 消息中间件模式 | 企业集成 |
| Ethernet / TSN | 面向确定性实时通信 | 高实时工业网络 |

PubSub 与 Client/Server Subscription 对比如下：

| 对比项 | Client/Server Subscription | PubSub |
|--------|----------------------------|--------|
| 连接关系 | Client 与 Server 建立会话 | 发布者与订阅者可解耦 |
| 通信方向 | Server 通过 PublishResponse 返回通知 | Publisher 主动发布 NetworkMessage |
| 是否需要 Session | 需要 | PubSub 数据通道不依赖 Session |
| 适合场景 | SCADA、采集、监控 | 一对多、边缘、云、实时分发 |
| 安全机制 | SecureChannel + Session | PubSub 安全组、密钥、安全策略，或依赖 MQTT/TLS 等 |

### 5. 配置与模型文件

#### 5.1 NodeSet2 XML

OPC UA 的信息模型可以用 NodeSet2 XML 表达。它类似 IEC 61850 中 SCD 的“模型描述文件”，但二者关注点不同：

| 对比项 | OPC UA NodeSet2 XML | IEC 61850 SCD |
|--------|---------------------|---------------|
| 核心用途 | 描述 OPC UA 地址空间、类型、节点、引用 | 描述变电站 IED、通信、DataSet、GOOSE/SV 订阅关系 |
| 模型对象 | Node、Type、Reference、DataType | IED、LDevice、LN、DO、DA、DataSet |
| 通信参数 | 通常不作为核心重点 | GOOSE/SV MAC、APPID、MinTime、MaxTime 等 |
| 运行方式 | Server 加载模型后对外暴露地址空间 | 工程工具生成配置，设备按配置通信 |

#### 5.2 NodeSet2 示例：覆盖所有主要 Node 元素

以下示例不是只包含对象和变量的极简片段，而是覆盖 NodeSet2 中主要节点元素的模型片段：

- `UAObject`：对象实例。
- `UAVariable`：变量实例，也包括 Method 的 `InputArguments` / `OutputArguments` 属性。
- `UAMethod`：可调用方法。
- `UAObjectType`：对象类型。
- `UAVariableType`：变量类型。
- `UADataType`：自定义数据类型。
- `UAReferenceType`：自定义引用类型。
- `UAView`：视图。

NodeSet2 文件内部的 `ns=1` 表示本文件 `<NamespaceUris>` 中第一个自定义 URI。Server 实际加载后，该 URI 在运行时 `NamespaceArray` 中可能变成 `ns=2`、`ns=3` 等，因此长期配置仍应保存 Namespace URI。

```xml
<?xml version="1.0" encoding="utf-8"?>
<UANodeSet
    xmlns="http://opcfoundation.org/UA/2011/03/UANodeSet.xsd"
    xmlns:uax="http://opcfoundation.org/UA/2008/02/Types.xsd"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">

    <!-- ========================================================= -->
    <!-- 1. NamespaceUris：定义本 NodeSet 使用的自定义命名空间      -->
    <!--    在本文件中，第一个自定义 URI 对应 ns=1                 -->
    <!-- ========================================================= -->
    <NamespaceUris>
        <Uri>urn:demo:windfarm:opcua</Uri>
    </NamespaceUris>

    <!-- ========================================================= -->
    <!-- 2. Models：声明本模型及其依赖                              -->
    <!-- ========================================================= -->
    <Models>
        <Model ModelUri="urn:demo:windfarm:opcua"
               Version="1.0.0"
               PublicationDate="2026-07-01T00:00:00Z">
            <RequiredModel ModelUri="http://opcfoundation.org/UA/"
                           Version="1.05.00"/>
        </Model>
    </Models>

    <!-- ========================================================= -->
    <!-- 3. Aliases：给标准 NodeId 起短名，便于后文引用             -->
    <!-- ========================================================= -->
    <Aliases>
        <Alias Alias="Boolean">i=1</Alias>
        <Alias Alias="Int32">i=6</Alias>
        <Alias Alias="Double">i=11</Alias>
        <Alias Alias="String">i=12</Alias>
        <Alias Alias="Structure">i=22</Alias>
        <Alias Alias="Argument">i=296</Alias>

        <Alias Alias="BaseObjectType">i=58</Alias>
        <Alias Alias="BaseDataVariableType">i=63</Alias>
        <Alias Alias="PropertyType">i=68</Alias>
        <Alias Alias="BaseDataType">i=24</Alias>
        <Alias Alias="BaseReferenceType">i=31</Alias>
        <Alias Alias="NonHierarchicalReferences">i=32</Alias>

        <Alias Alias="ObjectsFolder">i=85</Alias>
        <Alias Alias="ViewsFolder">i=87</Alias>
        <Alias Alias="HasTypeDefinition">i=40</Alias>
        <Alias Alias="HasSubtype">i=45</Alias>
        <Alias Alias="HasProperty">i=46</Alias>
        <Alias Alias="HasComponent">i=47</Alias>
        <Alias Alias="Organizes">i=35</Alias>
    </Aliases>

    <!-- ========================================================= -->
    <!-- 4. UAReferenceType：自定义引用类型                         -->
    <!--    表示“某对象控制另一个对象”的非层级关系                  -->
    <!-- ========================================================= -->
    <UAReferenceType NodeId="ns=1;s=Controls"
                     BrowseName="1:Controls"
                     Symmetric="false">
        <DisplayName>Controls</DisplayName>
        <InverseName>IsControlledBy</InverseName>
        <Description>Indicates that one object controls another object.</Description>
        <References>
            <Reference ReferenceType="HasSubtype" IsForward="false">NonHierarchicalReferences</Reference>
        </References>
    </UAReferenceType>

    <!-- ========================================================= -->
    <!-- 5. UADataType：自定义结构体数据类型                        -->
    <!-- ========================================================= -->
    <UADataType NodeId="ns=1;s=TurbineCommandResultDataType"
                BrowseName="1:TurbineCommandResultDataType"
                IsAbstract="false">
        <DisplayName>TurbineCommandResultDataType</DisplayName>
        <Description>Result returned by turbine command methods.</Description>
        <References>
            <Reference ReferenceType="HasSubtype" IsForward="false">Structure</Reference>
        </References>
        <Definition Name="TurbineCommandResultDataType">
            <Field Name="Code" DataType="Int32"/>
            <Field Name="Message" DataType="String"/>
        </Definition>
    </UADataType>

    <!-- ========================================================= -->
    <!-- 6. UAVariableType：自定义变量类型                          -->
    <!-- ========================================================= -->
    <UAVariableType NodeId="ns=1;s=AnalogMeasurementType"
                    BrowseName="1:AnalogMeasurementType"
                    DataType="Double"
                    ValueRank="-1"
                    IsAbstract="false">
        <DisplayName>AnalogMeasurementType</DisplayName>
        <Description>Base type for analog measurement variables.</Description>
        <References>
            <Reference ReferenceType="HasSubtype" IsForward="false">BaseDataVariableType</Reference>
        </References>
    </UAVariableType>

    <!-- ========================================================= -->
    <!-- 7. UAObjectType：自定义对象类型                            -->
    <!-- ========================================================= -->
    <UAObjectType NodeId="ns=1;s=WindTurbineType"
                  BrowseName="1:WindTurbineType"
                  IsAbstract="false">
        <DisplayName>WindTurbineType</DisplayName>
        <Description>ObjectType for a wind turbine.</Description>
        <References>
            <Reference ReferenceType="HasSubtype" IsForward="false">BaseObjectType</Reference>
            <Reference ReferenceType="HasComponent">ns=1;s=WindTurbineType.Power</Reference>
            <Reference ReferenceType="HasComponent">ns=1;s=WindTurbineType.Running</Reference>
            <Reference ReferenceType="HasComponent">ns=1;s=WindTurbineType.ResetFault</Reference>
        </References>
    </UAObjectType>

    <!-- ObjectType 下的模板变量：Power -->
    <UAVariable NodeId="ns=1;s=WindTurbineType.Power"
                BrowseName="1:Power"
                DataType="Double"
                TypeDefinition="ns=1;s=AnalogMeasurementType"
                AccessLevel="1"
                UserAccessLevel="1">
        <DisplayName>Power</DisplayName>
        <Description>Active power measurement template.</Description>
        <References>
            <Reference ReferenceType="HasComponent" IsForward="false">ns=1;s=WindTurbineType</Reference>
        </References>
    </UAVariable>

    <!-- ObjectType 下的模板变量：Running -->
    <UAVariable NodeId="ns=1;s=WindTurbineType.Running"
                BrowseName="1:Running"
                DataType="Boolean"
                TypeDefinition="BaseDataVariableType"
                AccessLevel="1"
                UserAccessLevel="1">
        <DisplayName>Running</DisplayName>
        <Description>Running state template.</Description>
        <References>
            <Reference ReferenceType="HasComponent" IsForward="false">ns=1;s=WindTurbineType</Reference>
        </References>
    </UAVariable>

    <!-- ObjectType 下的方法模板：ResetFault -->
    <UAMethod NodeId="ns=1;s=WindTurbineType.ResetFault"
              BrowseName="1:ResetFault"
              Executable="true"
              UserExecutable="true">
        <DisplayName>ResetFault</DisplayName>
        <Description>Reset turbine fault.</Description>
        <References>
            <Reference ReferenceType="HasComponent" IsForward="false">ns=1;s=WindTurbineType</Reference>
            <Reference ReferenceType="HasProperty">ns=1;s=WindTurbineType.ResetFault.InputArguments</Reference>
            <Reference ReferenceType="HasProperty">ns=1;s=WindTurbineType.ResetFault.OutputArguments</Reference>
        </References>
    </UAMethod>

    <!-- Method 的输入参数属性：InputArguments，本身是 UAVariable -->
    <UAVariable NodeId="ns=1;s=WindTurbineType.ResetFault.InputArguments"
                BrowseName="0:InputArguments"
                DataType="Argument"
                ValueRank="1"
                TypeDefinition="PropertyType">
        <DisplayName>InputArguments</DisplayName>
        <References>
            <Reference ReferenceType="HasProperty" IsForward="false">ns=1;s=WindTurbineType.ResetFault</Reference>
        </References>
        <Value>
            <uax:ListOfExtensionObject>
                <uax:ExtensionObject>
                    <uax:TypeId>
                        <uax:Identifier>i=297</uax:Identifier>
                    </uax:TypeId>
                    <uax:Body>
                        <uax:Argument>
                            <uax:Name>resetCode</uax:Name>
                            <uax:DataType>i=6</uax:DataType>
                            <uax:ValueRank>-1</uax:ValueRank>
                            <uax:ArrayDimensions/>
                            <uax:Description>
                                <uax:Locale></uax:Locale>
                                <uax:Text>Reset code.</uax:Text>
                            </uax:Description>
                        </uax:Argument>
                    </uax:Body>
                </uax:ExtensionObject>
            </uax:ListOfExtensionObject>
        </Value>
    </UAVariable>

    <!-- Method 的输出参数属性：OutputArguments，本身也是 UAVariable -->
    <UAVariable NodeId="ns=1;s=WindTurbineType.ResetFault.OutputArguments"
                BrowseName="0:OutputArguments"
                DataType="Argument"
                ValueRank="1"
                TypeDefinition="PropertyType">
        <DisplayName>OutputArguments</DisplayName>
        <References>
            <Reference ReferenceType="HasProperty" IsForward="false">ns=1;s=WindTurbineType.ResetFault</Reference>
        </References>
        <Value>
            <uax:ListOfExtensionObject>
                <uax:ExtensionObject>
                    <uax:TypeId>
                        <uax:Identifier>i=297</uax:Identifier>
                    </uax:TypeId>
                    <uax:Body>
                        <uax:Argument>
                            <uax:Name>result</uax:Name>
                            <uax:DataType>ns=1;s=TurbineCommandResultDataType</uax:DataType>
                            <uax:ValueRank>-1</uax:ValueRank>
                            <uax:ArrayDimensions/>
                            <uax:Description>
                                <uax:Locale></uax:Locale>
                                <uax:Text>Command result.</uax:Text>
                            </uax:Description>
                        </uax:Argument>
                    </uax:Body>
                </uax:ExtensionObject>
            </uax:ListOfExtensionObject>
        </Value>
    </UAVariable>

    <!-- ========================================================= -->
    <!-- 8. UAObject：对象实例                                     -->
    <!-- ========================================================= -->
    <UAObject NodeId="ns=1;s=WindTurbine_001"
              BrowseName="1:WindTurbine_001">
        <DisplayName>WindTurbine_001</DisplayName>
        <Description>Wind turbine instance 001.</Description>
        <References>
            <Reference ReferenceType="Organizes" IsForward="false">ObjectsFolder</Reference>
            <Reference ReferenceType="HasTypeDefinition">ns=1;s=WindTurbineType</Reference>
            <Reference ReferenceType="HasComponent">ns=1;s=WindTurbine_001.Power</Reference>
            <Reference ReferenceType="HasComponent">ns=1;s=WindTurbine_001.Running</Reference>
            <Reference ReferenceType="HasComponent">ns=1;s=WindTurbine_001.ResetFault</Reference>
        </References>
    </UAObject>

    <!-- ========================================================= -->
    <!-- 9. UAVariable：对象实例下的变量                            -->
    <!-- ========================================================= -->
    <UAVariable NodeId="ns=1;s=WindTurbine_001.Power"
                BrowseName="1:Power"
                DataType="Double"
                TypeDefinition="ns=1;s=AnalogMeasurementType"
                AccessLevel="3"
                UserAccessLevel="3">
        <DisplayName>Power</DisplayName>
        <Description>Active power of turbine 001.</Description>
        <References>
            <Reference ReferenceType="HasComponent" IsForward="false">ns=1;s=WindTurbine_001</Reference>
        </References>
        <Value>
            <uax:Double>0.0</uax:Double>
        </Value>
    </UAVariable>

    <UAVariable NodeId="ns=1;s=WindTurbine_001.Running"
                BrowseName="1:Running"
                DataType="Boolean"
                TypeDefinition="BaseDataVariableType"
                AccessLevel="1"
                UserAccessLevel="1">
        <DisplayName>Running</DisplayName>
        <Description>Running state of turbine 001.</Description>
        <References>
            <Reference ReferenceType="HasComponent" IsForward="false">ns=1;s=WindTurbine_001</Reference>
        </References>
        <Value>
            <uax:Boolean>false</uax:Boolean>
        </Value>
    </UAVariable>

    <!-- ========================================================= -->
    <!-- 10. UAMethod：对象实例下的方法                             -->
    <!-- ========================================================= -->
    <UAMethod NodeId="ns=1;s=WindTurbine_001.ResetFault"
              BrowseName="1:ResetFault"
              Executable="true"
              UserExecutable="true">
        <DisplayName>ResetFault</DisplayName>
        <Description>Reset fault on turbine 001.</Description>
        <References>
            <Reference ReferenceType="HasComponent" IsForward="false">ns=1;s=WindTurbine_001</Reference>
            <Reference ReferenceType="HasProperty">ns=1;s=WindTurbine_001.ResetFault.InputArguments</Reference>
            <Reference ReferenceType="HasProperty">ns=1;s=WindTurbine_001.ResetFault.OutputArguments</Reference>
        </References>
    </UAMethod>

    <UAVariable NodeId="ns=1;s=WindTurbine_001.ResetFault.InputArguments"
                BrowseName="0:InputArguments"
                DataType="Argument"
                ValueRank="1"
                TypeDefinition="PropertyType">
        <DisplayName>InputArguments</DisplayName>
        <References>
            <Reference ReferenceType="HasProperty" IsForward="false">ns=1;s=WindTurbine_001.ResetFault</Reference>
        </References>
        <Value>
            <uax:ListOfExtensionObject>
                <uax:ExtensionObject>
                    <uax:TypeId>
                        <uax:Identifier>i=297</uax:Identifier>
                    </uax:TypeId>
                    <uax:Body>
                        <uax:Argument>
                            <uax:Name>resetCode</uax:Name>
                            <uax:DataType>i=6</uax:DataType>
                            <uax:ValueRank>-1</uax:ValueRank>
                            <uax:ArrayDimensions/>
                            <uax:Description>
                                <uax:Locale></uax:Locale>
                                <uax:Text>Reset code.</uax:Text>
                            </uax:Description>
                        </uax:Argument>
                    </uax:Body>
                </uax:ExtensionObject>
            </uax:ListOfExtensionObject>
        </Value>
    </UAVariable>

    <UAVariable NodeId="ns=1;s=WindTurbine_001.ResetFault.OutputArguments"
                BrowseName="0:OutputArguments"
                DataType="Argument"
                ValueRank="1"
                TypeDefinition="PropertyType">
        <DisplayName>OutputArguments</DisplayName>
        <References>
            <Reference ReferenceType="HasProperty" IsForward="false">ns=1;s=WindTurbine_001.ResetFault</Reference>
        </References>
        <Value>
            <uax:ListOfExtensionObject>
                <uax:ExtensionObject>
                    <uax:TypeId>
                        <uax:Identifier>i=297</uax:Identifier>
                    </uax:TypeId>
                    <uax:Body>
                        <uax:Argument>
                            <uax:Name>result</uax:Name>
                            <uax:DataType>ns=1;s=TurbineCommandResultDataType</uax:DataType>
                            <uax:ValueRank>-1</uax:ValueRank>
                            <uax:ArrayDimensions/>
                            <uax:Description>
                                <uax:Locale></uax:Locale>
                                <uax:Text>Command result.</uax:Text>
                            </uax:Description>
                        </uax:Argument>
                    </uax:Body>
                </uax:ExtensionObject>
            </uax:ListOfExtensionObject>
        </Value>
    </UAVariable>

    <!-- ========================================================= -->
    <!-- 11. UAView：视图，用于给客户端提供一个特定浏览入口          -->
    <!-- ========================================================= -->
    <UAView NodeId="ns=1;s=WindFarmOperationalView"
            BrowseName="1:WindFarmOperationalView"
            ContainsNoLoops="true">
        <DisplayName>WindFarmOperationalView</DisplayName>
        <Description>Operational view for wind farm monitoring.</Description>
        <References>
            <Reference ReferenceType="Organizes" IsForward="false">ViewsFolder</Reference>
            <Reference ReferenceType="Organizes">ns=1;s=WindTurbine_001</Reference>
        </References>
    </UAView>

</UANodeSet>
```

这个示例中各类 `ns` 的判定：

| XML 片段 | 含义 |
|----------|------|
| `<NamespaceUris><Uri>urn:demo:windfarm:opcua</Uri>` | 本 NodeSet 定义了一个自定义命名空间 |
| `NodeId="ns=1;s=WindTurbine_001"` | `WindTurbine_001` 这个对象自身属于 `urn:demo:windfarm:opcua` |
| `BrowseName="1:Power"` | `Power` 这个 BrowseName 由 `urn:demo:windfarm:opcua` 定义 |
| `DataType="Double"` | 通过 Alias 指向标准 `ns=0;i=11`，即 OPC UA 标准 Double |
| `ReferenceType="HasComponent"` | 通过 Alias 指向标准引用类型 `ns=0;i=47` |
| `HasTypeDefinition → ns=1;s=WindTurbineType` | 实例对象使用本模型自定义的 ObjectType |
| `BrowseName="0:InputArguments"` | Method 参数属性的 BrowseName 使用标准命名空间，因为 `InputArguments` / `OutputArguments` 是 OPC UA 标准约定名称 |

#### 5.3 工程配置需要提取的关键参数

接入一个 OPC UA Server 时，配置文件或点表至少应保存：

| 参数 | 示例 | 说明 |
|------|------|------|
| `endpoint_url` | `opc.tcp://192.168.1.10:4840` | 服务器连接地址 |
| `security_policy` | `Basic256Sha256` | 安全策略 |
| `security_mode` | `SignAndEncrypt` | 安全模式 |
| `auth_type` | `Anonymous` / `Username` / `Certificate` | 用户认证方式 |
| `username` | `operator` | 用户名，按需 |
| `client_cert` | `client.der` | 客户端证书 |
| `client_key` | `client.pem` | 客户端私钥 |
| `server_cert_trust` | `server.der` | 是否信任服务器证书 |
| `namespace_uri` | `urn:demo:windfarm:opcua` | 稳定命名空间 URI，长期保存 |
| `identifier_type` | `String` / `Numeric` | NodeId 的 Identifier 类型，长期保存 |
| `identifier` | `Device1.Power` / `1001` | NodeId 的 Identifier，长期保存 |
| `runtime_node_id` | `ns=2;s=Device1.Power` | 当前连接会话内解析得到的 NodeId，可缓存但不应作为唯一长期依据 |
| `browse_path` | `Objects/Device1/Power` | 可选，用于人机定位和模型变更后的辅助恢复 |
| `data_type` | `Double` | 数据类型 |
| `sampling_interval` | `1000 ms` | 订阅采样周期 |
| `publishing_interval` | `1000 ms` | 发布周期 |
| `deadband` | `0.1` | 数据变化过滤 |
| `use_source_timestamp` | `true` | 是否优先使用源时间戳 |

### 6. Python 开发（asyncua 库）

#### 6.1 库的性质

Python 生态中常见的 OPC UA 库有：

| 库 | 说明 | 适用场景 |
|----|------|----------|
| `asyncua` / `opcua-asyncio` | 基于 asyncio 的纯 Python OPC UA Client/Server 库，是 `python-opcua` 的后继方向 | Python 采集、测试 Server、协议仿真 |
| `python-opcua` | 较早的 FreeOpcUa Python 库 | 老项目维护 |
| `open62541` | C 语言 OPC UA 实现，可用于高性能客户端/服务器 | 嵌入式、高性能网关、C/C++ 项目 |
| 厂商 SDK | Unified Automation、Prosys、Softing、Matrikon 等 | 商业项目、认证需求、复杂 Server |

工程建议：

- Python 采集程序优先考虑 `asyncua`。
- 高性能网关或工业产品化 Server 优先考虑 `open62541` 或商业 SDK。
- 若需要 OPC UA Conformance Certification，应优先选择成熟 SDK 并按 Profile 测试。

#### 6.2 安装

```bash
pip install asyncua
```

#### 6.3 同步风格读取示例

`asyncua` 以异步 API 为主，也提供同步封装。实际项目中更推荐使用异步方式。

```python
from asyncua.sync import Client

endpoint = "opc.tcp://192.168.1.10:4840"

with Client(endpoint) as client:
    node = client.get_node("ns=2;s=WindTurbine_001.Power")

    value = node.read_value()
    data_value = node.read_data_value()

    print("value:", value)
    print("status:", data_value.StatusCode)
    print("source time:", data_value.SourceTimestamp)
    print("server time:", data_value.ServerTimestamp)
```

#### 6.4 异步读取示例

```python
import asyncio
from asyncua import Client

async def main():
    endpoint = "opc.tcp://192.168.1.10:4840"

    async with Client(endpoint) as client:
        node = client.get_node("ns=2;s=WindTurbine_001.Power")

        value = await node.read_value()
        data_value = await node.read_data_value()

        print("value:", value)
        print("status:", data_value.StatusCode)
        print("source time:", data_value.SourceTimestamp)

asyncio.run(main())
```

#### 6.5 批量读取

```python
import asyncio
from asyncua import Client, ua

async def main():
    endpoint = "opc.tcp://192.168.1.10:4840"

    node_ids = [
        "ns=2;s=WindTurbine_001.Power",
        "ns=2;s=WindTurbine_001.WindSpeed",
        "ns=2;s=WindTurbine_001.RotorSpeed",
    ]

    async with Client(endpoint) as client:
        nodes = [client.get_node(node_id) for node_id in node_ids]
        values = await client.read_values(nodes)

        for node_id, value in zip(node_ids, values):
            print(node_id, value)

asyncio.run(main())
```

#### 6.6 写入

```python
import asyncio
from asyncua import Client, ua

async def main():
    endpoint = "opc.tcp://192.168.1.10:4840"

    async with Client(endpoint) as client:
        node = client.get_node("ns=2;s=WindTurbine_001.ActivePowerSetpoint")

        value = ua.Variant(1500.0, ua.VariantType.Double)
        data_value = ua.DataValue(value)

        await node.write_value(data_value)

asyncio.run(main())
```

写入注意：

- 数据类型必须与服务器节点的 `DataType` 匹配。
- `Double`、`Float`、`Int16`、`UInt16`、`Boolean` 等不能随意混用。
- 写入前最好读取节点 `DataType` 和 `AccessLevel`。
- 控制命令应检查写入返回状态和设备后续状态变化。

#### 6.7 订阅数据变化

```python
import asyncio
from asyncua import Client

class SubHandler:
    def datachange_notification(self, node, val, data):
        data_value = data.monitored_item.Value
        print("node:", node)
        print("value:", val)
        print("status:", data_value.StatusCode)
        print("source time:", data_value.SourceTimestamp)

async def main():
    endpoint = "opc.tcp://192.168.1.10:4840"

    async with Client(endpoint) as client:
        handler = SubHandler()

        # publishing interval = 100 ms
        subscription = await client.create_subscription(100, handler)

        nodes = [
            client.get_node("ns=2;s=WindTurbine_001.Power"),
            client.get_node("ns=2;s=WindTurbine_001.WindSpeed"),
            client.get_node("ns=2;s=WindTurbine_001.RotorSpeed"),
        ]

        handles = await subscription.subscribe_data_change(nodes)

        try:
            while True:
                await asyncio.sleep(1)
        finally:
            await subscription.unsubscribe(handles)
            await subscription.delete()

asyncio.run(main())
```

#### 6.8 调用方法

```python
import asyncio
from asyncua import Client

async def main():
    endpoint = "opc.tcp://192.168.1.10:4840"

    async with Client(endpoint) as client:
        device = client.get_node("ns=2;s=WindTurbine_001")
        method = client.get_node("ns=2;s=WindTurbine_001.ResetFault")

        result = await device.call_method(method, 1001)
        print("method result:", result)

asyncio.run(main())
```

#### 6.9 浏览地址空间

```python
import asyncio
from asyncua import Client

async def browse(node, level=0):
    indent = "  " * level
    name = await node.read_browse_name()
    node_id = node.nodeid
    print(f"{indent}{name} [{node_id}]")

    children = await node.get_children()
    for child in children:
        await browse(child, level + 1)

async def main():
    endpoint = "opc.tcp://192.168.1.10:4840"

    async with Client(endpoint) as client:
        objects = client.nodes.objects
        await browse(objects)

asyncio.run(main())
```

### 7. 高性能采集方案

对于 **500+ 变量、50Hz** 的采集场景，需要避免把 OPC UA 当成“逐点同步读”的协议使用。

#### 7.1 方案对比

| 方案 | 说明 | 结论 |
|------|------|------|
| ❌ 逐点同步读取 | 500 个变量逐个 `read_value()`，每轮大量请求/响应 | 延迟大、CPU 开销高、不可取 |
| ⚠️ 批量读取 | 一次请求读取多个节点 | 适合低频或补读，不适合作为最高性能实时方案 |
| ✅ Subscription | 创建订阅，让 Server 按周期采样并批量推送变化 | 高频采集首选 |
| ✅ 合理分组订阅 | 将同周期、同业务的数据放在同一个 Subscription | 易管理、降低调度开销 |
| ✅ 服务端聚合结构体 | Server 端将强同步数据组织为结构体或数组 | 保证同一采样周期一致性 |
| ✅ PubSub | 对一对多或边缘分发使用 UDP/MQTT PubSub | 适合广播、云边分发、低耦合 |

#### 7.2 50Hz 订阅参数建议

50Hz 对应周期为 20ms。

建议配置：

| 参数 | 建议值 | 说明 |
|------|--------|------|
| `SamplingInterval` | `20 ms` 或设备允许的最小稳定值 | Server 采样周期 |
| `PublishingInterval` | `20 ms` / `50 ms` / `100 ms` | 取决于是否允许打包 |
| `QueueSize` | `1` 或 `2~10` | 实时监控用 1；不能丢中间值时增大 |
| `DiscardOldest` | `true` | 实时场景优先保留最新值 |
| `Deadband` | 根据变量类型设置 | 模拟量可设置死区，状态量不设置 |
| `TimestampsToReturn` | `Source` 或 `Both` | 入库应优先保留源时间戳 |
| `MaxNotificationsPerPublish` | 按点数和周期估算 | 防止单次 Publish 过大 |

#### 7.3 分组策略

建议按以下维度分组：

| 分组维度 | 示例 |
|----------|------|
| 采集周期 | 20ms 高频、1s 常规、10s 慢变量 |
| 数据类型 | 模拟量、状态量、报警事件 |
| 设备对象 | 风机 001、风机 002、逆变器 001 |
| 数据用途 | 实时监控、趋势入库、控制反馈 |
| 服务质量 | 必须保留中间值、只要最新值 |

示例：

```text
Subscription_HighFreq_20ms
├── WT001.Power
├── WT001.RotorSpeed
├── WT001.WindSpeed
└── WT001.GeneratorSpeed

Subscription_Status_1s
├── WT001.Running
├── WT001.FaultCode
└── WT001.Mode

Subscription_Events
└── WT001 as EventSource
```

#### 7.4 采集端缓存设计

采集系统应维护以下缓存：

| 缓存 | 作用 |
|------|------|
| Endpoint 缓存 | endpoint、安全策略、证书配置 |
| Namespace 缓存 | 当前连接中 Namespace URI 与 NamespaceIndex 的映射，由 `NamespaceArray` 生成 |
| NodeId 缓存 | 用长期保存的 `namespace_uri + identifier` 解析出的运行时 NodeId 映射 |
| Metadata 缓存 | DataType、单位、范围、AccessLevel |
| Subscription 缓存 | SubscriptionId、MonitoredItemId、handle |
| LastValue 缓存 | 最新值、质量码、时间戳 |
| Reconnect 状态 | 断线重连、订阅恢复、点位补读 |

#### 7.5 断线重连策略

OPC UA 采集不能只写一个 `while True read`。需要完整处理：

1. TCP 断开；
2. SecureChannel 失效；
3. Session 超时；
4. Subscription 生命周期过期；
5. 服务器重启；
6. 证书变化；
7. NamespaceIndex 变化；
8. 点位不存在或模型版本变化。

推荐流程：

```text
连接失败
  ↓
指数退避重连
  ↓
GetEndpoints，校验安全参数
  ↓
OpenSecureChannel
  ↓
CreateSession / ActivateSession
  ↓
读取 NamespaceArray
  ↓
重建 Namespace URI → Index 映射
  ↓
重新解析 NodeId
  ↓
重建 Subscription / MonitoredItem
  ↓
读取一次当前值作为恢复快照
  ↓
恢复订阅采集
```

#### 7.6 性能注意事项

| 问题 | 建议 |
|------|------|
| 点位过多 | 使用 Subscription，不要逐点轮询 |
| 周期过快 | 检查服务器 revised sampling interval，不要假设请求值一定生效 |
| 大量字符串 NodeId | 可缓存 Node 对象和解析结果 |
| 复杂结构体 | 明确结构体编码和字段映射，避免运行时反射过重 |
| 时间戳混乱 | 入库保留 source/server/collector 三类时间 |
| 质量码被忽略 | 入库必须保存 StatusCode |
| 数据乱序 | 按 SourceTimestamp 和采集批次处理 |
| 服务器负载高 | 增大 publishing interval、设置 deadband、分组采集 |
| 网络抖动 | QueueSize 适当增大，记录丢包/延迟指标 |
| 重连后点表失效 | 用 Namespace URI + Identifier 重建 NodeId |

### 8. 安全机制与工程警告

#### 8.1 OPC UA 安全模型

OPC UA 安全主要分为三层：

| 层级 | 机制 | 说明 |
|------|------|------|
| 应用认证 | Application Instance Certificate | 客户端和服务器通过证书识别彼此 |
| 消息安全 | SecurityPolicy + SecurityMode | 消息签名、加密、防篡改 |
| 用户认证 | Anonymous / Username / Certificate / IssuedToken | 确认操作者或系统身份 |
| 授权 | Role / Permission / AccessLevel | 控制谁能读、写、调用、浏览 |

#### 8.2 证书信任

OPC UA 使用应用实例证书。常见证书目录结构：

```text
pki/
├── own/
│   ├── certs/
│   │   └── client.der
│   └── private/
│       └── client.pem
├── trusted/
│   └── certs/
│       └── server.der
├── rejected/
│   └── certs/
└── issuers/
    └── certs/
```

首次连接时，如果客户端不信任服务器证书，通常会失败或把证书放入 rejected 目录。工程人员需要：

1. 确认服务器证书指纹；
2. 将服务器证书加入 trusted；
3. 将客户端证书导入服务器 trust list；
4. 禁止生产环境自动信任未知证书。

#### 8.3 用户认证

常见认证方式：

| 方式 | 说明 | 建议 |
|------|------|------|
| Anonymous | 匿名访问 | 仅限只读测试或隔离网络 |
| Username/Password | 用户名密码 | 必须配合 SignAndEncrypt |
| Certificate | 用户证书 | 高安全场景 |
| IssuedToken | 外部身份系统签发 Token | 企业集成场景 |

#### 8.4 安全警告

OPC UA 虽然内置安全机制，但“不等于默认安全”。

严禁在生产环境中：

- 开启公网可访问的 `SecurityPolicy=None` Endpoint；
- 匿名用户拥有写权限；
- 用户名密码在无加密通道上传输；
- 自动信任任意服务器证书；
- 多个系统共用同一个客户端证书和私钥；
- 不记录写入、方法调用、报警确认等操作审计；
- 把 OPC UA Server 直接暴露到互联网；
- 只靠防火墙，不做 OPC UA 层认证与授权。

推荐：

- 使用 `SignAndEncrypt`；
- 使用强安全策略；
- 禁止匿名写入；
- 按角色控制读写权限；
- 证书定期轮换；
- 生产网与办公网隔离；
- 对写入和 Method Call 做审计；
- 对关键控制点增加业务侧二次确认。

### 9. 与其他协议的工程差异

#### 9.1 OPC UA 与 ADS

| 对比项 | OPC UA | ADS |
|--------|--------|-----|
| 核心定位 | 跨厂商工业互操作标准 | Beckhoff TwinCAT 内部/外部通信协议 |
| 寻址方式 | NodeId + Namespace | AmsNetId + Port + IndexGroup/Offset/变量名 |
| 数据模型 | 强信息模型，节点、类型、引用 | 更接近 PLC 变量访问 |
| 安全机制 | 内置证书、签名、加密、用户认证 | 传统 ADS 安全较弱，通常依赖网络隔离或 Secure ADS |
| 订阅 | Subscription / MonitoredItem | Notification |
| 时间戳 | DataValue 原生包含 Source/Server Timestamp | 普通读写无时间戳，通知可带时间戳 |
| 跨厂商 | 强 | 弱，主要 Beckhoff 生态 |

#### 9.2 OPC UA 与 IEC 61850

| 对比项 | OPC UA | IEC 61850 |
|--------|--------|-----------|
| 行业范围 | 通用工业自动化、制造、能源、设备集成 | 电力系统，尤其变电站自动化 |
| 模型核心 | AddressSpace / Node / Type / Reference | IED / LDevice / LN / DO / DA |
| 配置文件 | NodeSet2 XML | SCL / ICD / CID / SCD |
| 实时事件 | Events / Alarms / PubSub | GOOSE |
| 采样值 | PubSub 可承载数据集 | SV 专门用于采样值 |
| 客户端服务 | Read / Write / Browse / Call / Subscription | MMS Read/Write/Report/Control |
| 工程强约束 | 依赖具体信息模型/Companion | 标准对电力对象、GOOSE/SV 配置约束更强 |

### 10. 最小接入清单

接入一个 OPC UA Server，最少需要确认：

| 项目 | 是否必须 | 示例 |
|------|----------|------|
| Server IP / Host | ✅ | `192.168.1.10` |
| Port | ✅ | `4840` |
| Endpoint URL | ✅ | `opc.tcp://192.168.1.10:4840` |
| SecurityPolicy | ✅ | `Basic256Sha256` |
| SecurityMode | ✅ | `SignAndEncrypt` |
| 认证方式 | ✅ | Anonymous / Username / Certificate |
| 用户名密码 | 按需 | `operator / ******` |
| 客户端证书 | 按需 | `client.der` |
| 客户端私钥 | 按需 | `client.pem` |
| 服务器证书 | 按需 | `server.der` |
| Namespace URI | ✅ | `urn:demo:windfarm:opcua` |
| Identifier 类型和值 | ✅ | `String / Device1.Power` 或 `Numeric / 1001` |
| 运行时 NodeId | ✅ | `ns=2;s=Device1.Power`，由 Namespace URI 解析得到 |
| 数据类型 | ✅ | `Double` |
| 读写权限 | ✅ | Read / Write |
| 采集周期 | ✅ | `1000 ms` / `20 ms` |
| 时间戳策略 | ✅ | SourceTimestamp 优先 |
| 质量码策略 | ✅ | 保存 StatusCode |
| 重连策略 | ✅ | Session/Subscription 重建 |
| 安全审计 | 写入/控制场景必须 | 写入记录、方法调用记录 |

### 11. 典型工程结论

1. OPC UA 的核心不是端口，也不是变量名，而是 **AddressSpace + NodeId + Services + Security**。
2. 采集系统不要把 `ns=2;i=xxx` 当成永久地址；`ns=2` 是运行时索引，长期点表应保存 **Namespace URI + Identifier 类型 + Identifier 值**，重连后再解析成新的运行时 NodeId。
3. 高频采集优先使用 **Subscription**，不要逐点同步读。
4. 入库数据必须保存 **Value + StatusCode + SourceTimestamp + ServerTimestamp + CollectorTimestamp**。
5. 控制动作优先建模为 **Method Call** 或明确状态机，不建议靠写布尔变量表达复杂动作。
6. 生产环境应关闭或限制 `SecurityPolicy=None` 和匿名写入。
7. OPC UA Client/Server 适合 SCADA、网关和采集；PubSub 更适合一对多分发、边缘到云和低耦合实时数据流。
8. OPC UA 的“互操作”依赖信息模型质量。只把 PLC 变量平铺暴露出来，仍然只是“换皮变量表”，没有发挥 OPC UA 的语义优势。
9. 对 500+ 点、50Hz 采集，应重点验证服务器能力、revised sampling interval、网络负载、队列丢弃策略和重连恢复。
10. 安全配置不是附加项，而是 OPC UA 工程接入的一部分，应与点表、采集周期、权限模型一起纳入配置管理。

### 12. 参考依据

- OPC Foundation：OPC UA Overview / Unified Architecture
- OPC Foundation：OPC 10000-1 Overview and Concepts
- OPC Foundation：OPC 10000-2 Security Model
- OPC Foundation：OPC 10000-3 Address Space Model（NodeId、Namespace、NodeClass、Method NodeClass）
- OPC Foundation：OPC 10000-4 Services（Read / Write / Browse / Call / Subscription）
- OPC Foundation：OPC 10000-6 Mappings（UA TCP、NodeId / ExpandedNodeId 字符串、NodeSet2 XML）
- OPC Foundation：OPC 10000-14 PubSub
- FreeOpcUa：opcua-asyncio / asyncua documentation
- open62541：OPC UA C implementation documentation
