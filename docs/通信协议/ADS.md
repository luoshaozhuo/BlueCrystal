
## 第一部分：ADS（Automation Device Specification）

### 1. 协议概述

ADS 是 Beckhoff TwinCAT 系统的核心通信协议，用于 PLC 运行时（Runtime）、NC（运动控制）、I/O 系统以及外部应用程序之间的数据交换。它是一种基于 **AmsNetId 寻址**、**报文路由**的应用层协议，不绑定特定物理介质。

### 2. 核心寻址体系

#### 2.1 AmsNetId

- **格式**：6 段数字，如 `192.168.1.10.1.1`
- **作用**：设备的**逻辑身份标识**，是 ADS 通信中寻址的核心依据
- **与 IP 地址的关系**：
  - IP 地址是"物理位置"（在哪台电脑），AmsNetId 是"逻辑身份"（在哪个控制程序）
  - 两者**不必相同**，但工程上通常让前 4 段与 IP 一致，便于管理
  - 特殊场景（多网卡、冗余系统）下可以不同

#### 2.2 端口（Port）

标识设备内的具体软件模块：

| 端口 | 对应模块 |
|------|----------|
| 801 | TwinCAT 2 PLC Runtime |
| 851 | TwinCAT 3 PLC Runtime |
| 281 | I/O 系统 |
| 301 | NC（运动控制） |
| 10000+ | 用户自定义程序 |

#### 2.3 路由表

路由表维护 **AmsNetId ↔ IP 地址** 的映射关系，是 ADS 通信的**前提条件**。通信前必须在本地路由表中添加目标设备的路由条目，或在代码中通过 `pyads.add_route_to_plc()` 动态添加。

#### 2.4 索引组（Index Group）与偏移（Index Offset）

定位 PLC 内部变量的"门牌号"。每个变量在 PLC 内存中对应唯一的组号和偏移地址，可替代变量名用于更底层的寻址。

### 3. 通信协议栈与帧格式

#### 3.1 协议栈

| 层级 | 协议/组件 |
|------|-----------|
| 应用层 | ADS / AMS（自动化设备规范） |
| 路由层 | AMS Router（维护路由表，负责报文寻址与本地分发） |
| 传输层 | TCP（端口 48898，可靠数据交互）/ UDP（端口 48899，广播与路由发现） |
| 网络层 | IP / Ethernet |

#### 3.2 ADS 帧结构（AMS 头部 32 字节）

| 偏移 | 大小（字节） | 字段 | 说明 |
|------|-------------|------|------|
| 0 | 4 | 目标 AmsNetId（前 4 段） | 目标设备 ID |
| 4 | 2 | 目标 AmsNetId（后 2 段） | |
| 6 | 2 | 目标端口 | 目标软件模块 |
| 8 | 4 | 源 AmsNetId（前 4 段） | 发送方设备 ID |
| 12 | 2 | 源 AmsNetId（后 2 段） | |
| 14 | 2 | 源端口 | 发送方软件模块 |
| 16 | 4 | 命令 ID | 操作类型（读/写/通知等） |
| 20 | 4 | 状态码 | 返回码（0 表示成功） |
| 24 | 4 | 数据长度 | 数据区字节数 |
| 28 | 4 | 错误码 | 具体错误编号 |
| 32 | 变长 | 数据区 | 具体命令参数或数据值 |

#### 3.3 通信流程（以同步读取为例）

1. 应用程序调用 API（如 `read_by_name`）
2. 本地 AMS Router 根据目标 AmsNetId 查找路由表，获取目标 IP
3. 通过 TCP（48898）或 UDP（48899）发送 ADS 报文
4. 目标设备 AMS Router 接收报文，根据目标端口分发给对应软件模块
5. 软件模块执行命令，生成响应报文
6. 响应报文沿原路径返回
7. 应用程序收到响应，API 调用返回

### 4. 通信方式

#### 4.1 读取方式

| 方式 | 说明 | 适用场景 |
|------|------|----------|
| **同步读取**（AdsSyncReadReq） | 阻塞等待，直到收到响应或超时 | 简单、低频读写 |
| **异步读取**（AdsAsyncReadReq） | 非阻塞，发起请求后立即返回，响应通过回调函数通知 | 不阻塞主线程的复杂场景 |
| **通知/订阅**（Notification） | 向 PLC 注册通知，PLC 主动推送（变化触发或周期触发） | 高频实时数据，最节省资源 |

#### 4.2 写入方式

| 方式 | 说明 |
|------|------|
| **同步写入**（AdsSyncWriteReq） | 阻塞等待 PLC 确认，最常用 |
| **异步写入**（AdsAsyncWriteReq） | 非阻塞，写入完成时通过回调通知 |

> 写入操作没有"订阅"模式。

#### 4.3 订阅模式的两种触发方式

| 传输模式 | 说明 |
|----------|------|
| `ADSTRANS_SERVERONCHA` | 仅当值发生变化时触发推送 |
| `ADSTRANS_SERVERCYCLE` | 按设定的固定周期循环推送 |

### 5. Python 开发（pyads 库）

#### 5.1 库的性质

`pyads` 并非 Beckhoff 官方发布的库，而是社区开源项目（MIT 许可证）。但其内部**底层调用了官方的 ADS C API 库**（Windows 下为 `TcAdsDll.dll`，Linux 下为 `adslib.so`），因此通信核心是官方代码。它是 Python 生态中访问 ADS 的事实标准。

#### 5.2 Linux 环境关键点

- 依赖库 `adslib.so` 必须与 CPU 架构匹配（x86 / arm64 等）
- 在国产麒麟系统（飞腾、鲲鹏等 ARM64 架构）上，预编译的 `adslib.so` 可能无法加载，需从源码重新编译
- 路由配置可通过 `pyads.add_route_to_plc()` 动态添加，或使用官方 `adstool` 工具

#### 5.3 关键 API

| 操作 | 方法 |
|------|------|
| 添加路由 | `pyads.add_route_to_plc(target_ams, target_ip, username, password)` |
| 连接 | `plc = pyads.Connection(ams_id, port); plc.open()` |
| 按名称读取 | `plc.read_by_name("GVL.var", pyads.PLCTYPE_REAL)` |
| 按名称写入 | `plc.write_by_name("GVL.var", value, pyads.PLCTYPE_REAL)` |
| 批量读取 | `plc.read_list_by_name(["var1", "var2", ...])` |
| 异步读取 | `await plc.read_value_async("GVL.var", pyads.PLCTYPE_REAL)` |
| 添加通知 | `plc.add_device_notification("GVL.var", attr, callback)` |
| 句柄优化 | `handle = plc.create_handle("GVL.var")` → 用 `read_by_handle` / `write_by_handle` 操作（更快）→ `release_handle` |

#### 5.4 时间戳支持

| 操作模式 | 是否支持时间戳 |
|----------|---------------|
| 同步/异步读取 | ❌ 不支持（协议帧无时间戳字段） |
| 通知（Notification） | ✅ 支持（通过 `timestamp=True` 开启，由 PLC 侧打戳） |

#### 5.5 设备发现

`pyads` **没有内置的广播设备发现 API**。需通过以下方式实现：

- **手动配置路由**：在 TwinCAT 路由管理工具中搜索并添加
- **自行实现 UDP 广播**：向 48899 端口发送广播探测报文（需抓包分析官方工具行为）
- **解析配置文件**：Linux 下路由信息通常存储在 `/etc/ads-routes`

### 6. 高性能采集方案

对于 **500+ 变量、50Hz** 的采集场景：

| 方案 | 说明 |
|------|------|
| ❌ 逐个订阅 | 500 个变量 → 500 个独立回调 → CPU 开销极大，不可行 |
| ✅ 批量读取 | `read_list_by_name` 一次性获取所有变量值 → 1 次请求带回 500 个值 |
| ✅ 结构体订阅（最优） | PLC 端将所有变量打包成 1 个 STRUCT → Python 端只订阅该结构体 → 1 次回调拿到所有数据，且数据来自同一扫描周期，天然同步 |

### 7. 安全警告

ADS 协议**没有内置加密或认证机制**，严禁暴露在公网。如必须在不安全网络中传输，应通过 VPN 或 Secure ADS（TLS 封装）保障安全。
