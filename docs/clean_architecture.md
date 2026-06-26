# Clean Architecture Blueprint & Standard Specification
# 版本：3.0 (面向 Python 工业协议仿真运行时优化) | 适用语言：Python 3.10+

这份文档详细定义了一个高度内聚、松耦合的 Python Clean 架构脚手架。
核心理念：核心业务与协议编解码严禁依赖外部技术栈（如物理网络 I/O 库、C 编译依赖或具体 CLI 框架）。外层（驱动、基础设施）随时可换，内层（协议、用例）稳如泰山。

---

## 一、 架构五层分层设计与边界约束

```text
       ┌────────────────────────────────────────────────────────┐
       │ 5. INFRASTRUCTURE & PRESENTATION (Web, DB, C-Binaries) │
       │       ▼                                                │
       │ 4. INTERFACE ADAPTERS (Controllers, Facade 实现)        │
       │       ▼                                                │
       │ 3. API / FACADE (公共应用切入点 - 顶层正门)               │
       │       ▼                                                │
       │ 2. USE CASES / APPLICATION (用例流程编排)               │
       │       ▼                                                │
       │ 1. DOMAIN / ENTITIES (纯核心业务规则、纯协议编解码)         │
       └────────────────────────────────────────────────────────┘
```

### 1. Domain 层 (核心/实体层)
* **职责**：承载最核心、通用的业务模型与纯协议编解码逻辑。这里只做纯粹的内存内数据结构处理和算法，**绝对不允许包含任何网络 I/O 动作**。
* **包含元素与辨析**：
  * **Entities (实体)**：
    * **特征**：必须拥有唯一 ID，生命周期内状态可变（充血模型）。它内部的方法处理**单一实体自身**的状态流转与合法性校验。
    * **举例**：`ServerPlan` 拥有 plan 唯一标识。它包含静态合法性校验及动态加载时的状态管理方法。
  * **Value Objects (值对象)**：
    * **特征**：绝对没有 ID。它是不可变的（Immutable / Frozen）。
    * **辨析**：只要属性完全一致，它们在业务上就是等价且可互换的。若要修改它，只能创建新对象去替换。它通常包含丰富的局部计算逻辑。
    * **举例**：`Money` (金额/币种)、`IEC101` 协议中的 `Frame`、`ASDU` 结构、`Quality` 质量位定义。
  * **Domain Services (领域服务)**：
    * **特征**：无状态的纯业务/协议计算类。绝不能调用数据库、三方网络库。
    * **辨析**：当某个核心业务/编解码规则**涉及多个实体/值对象之间的交互**，且不适合硬塞进任何单一对象时，放在这里。
    * **举例**：`IEC101Codec`（不含 I/O 的纯字节流与对象相互转换编解码器）、`RegisterEncoding`（Modbus 寄存器数据解析器）。
* **范围约束**：
  * 纯粹的原生 Python 代码，绝对禁止 `import` 任何物理驱动库（如 paho-mqtt, pymodbus）或 Web 框架。

### 2. Use Cases 层 (应用用例层)
* **职责**：具体仿真业务流程的“总导演”，负责编排 Domain 层的元素来实现用户的一个具体诉求。
* **包含元素**：
  * **Use Cases (原子用例)**：通常包含单个 `execute()` 方法的类。本身直接充当输入入口（Input Port），拒绝生搬硬套 Java 的双重接口继承。
  * **Workflows / Composites (组合工作流)**：专门用于组织、协调多个基础原子 UseCase 的高级职能类。
  * **Ports (输出端口)**：UseCase 访问外部技术栈（如启动真实的 Socket、调用 C 二进制）所依凭的抽象接口契约（Python 中的 `ABC` 基类）。
  * **DTOs (数据传输对象)**：纯粹的扁平数据字典/数据类，只用于系统内外层之间的数据搬运，不含业务逻辑。
* **范围约束**：
  * 只管流程编排（查出 Plan -> 调用协议层编码 -> 唤起物理驱动发送），绝不关心驱动底层是如何用 Paho 还是 Native C 实现的。

### 3. API / Facade 层 (公共应用入口层)
* **职责**：整个系统的“正门”。它与 `use_cases` 同级，作为外部程序（CLI、测试框架、微服务端点）唯一需要依赖的高层 SDK 接口。
* **包含元素**：
  * **Runtime Facade**：暴露出最干净的顶级方法（如 `start_simulation()`）。它内部负责调用依赖注入容器（Container）来装配系统，外部消费者无需关心内部的原子用例拆分。

### 4. Interface Adapters 层 (接口适配器层)
* **职责**：充当内外层的“翻译官”。
* **包含元素**：
  * **Controllers (控制器)**：接收物理世界（如 CLI 命令行参数、HTTP Request）的生数据，解析并组装成 DTO 送给 API 层。
  * **Gateways/Repositories 实现类**：真正去实现 UseCase 层定义的 Output Port（接口）。在这里写具体的外部连接、SQL 或三方 API 调用。

### 5. Infrastructure 层 (基础设施层)
* **职责**：系统最外层，所有具体物理技术的落脚点。
* **包含元素**：
  * **Drivers (真实协议网关驱动)**：封装了真正的网络 Socket、MQTT 连接客户端、OPC UA 客户端的技术实现。
  * **Native Native (底座支撑)**：包括 CMake 构建脚本、OS 级别的子进程生命周期管理（Process Handle）、预编译的 C Runner 二进制文件等。

---

## 二、 现代 Python 项目工程树结构 (Tree Structure)

```text
src/starfish/
├── README.md                        — 架构与 CLI 用法说明
├── __init__.py                      — 对外只导出统一的 StarfishRuntime 门面
├── __main__.py                      — CLI 唯一启动入口，只跟 starfish 包导出的门面交互
├── container.py                     — 依赖注入容器 (负责实例化最外层物理 Facade 并组装给内层 UseCase)
│
├── api/                             # ===== 3. API / FACADE 层 (系统的对外统一正门) =====
│   ├── __init__.py
│   └── runtime_facade.py            # class StarfishRuntime: 对外暴露的统一干净 SDK 接口
│
├── domain/                          # ===== 1. DOMAIN 层 (纯协议/协议模型，零网络 I/O 依赖) =====
│   ├── __init__.py
│   ├── entities/
│   │   └── server_plan.py           # 核心实体：ServerPlan 模型及合法性状态校验
│   └── protocols/                   # 纯协议编解码领域模型
│       ├── iec101/
│       │   ├── asdu.py              # 值对象/领域模型
│       │   ├── codec.py             # 纯计算领域服务：不含 I/O 的编解码器
│       │   └── frame.py             
│       └── modbus/
│           └── register_encoding.py # Modbus 寄存器纯字节编解码工具
│
├── use_cases/                       # ===== 2. USE CASES 层 (业务流程总导演) =====
│   ├── __init__.py
│   ├── dtos.py                      # 运行时状态、计划入参的扁平数据载体
│   ├── ports/                       # 【依赖倒置核心】内层定义的抽象输出契约(ABC)
│   │   ├── driver_interface.py      # class ProtocolDriverPort(ABC): 驱动对外暴露的高层要求
│   │   └── plan_loader_port.py      # class PlanLoaderPort(ABC): 配置文件读取要求
│   └── runtime/                     # 具体的原子用例 (自身充当输入入口)
│       ├── load_server_plan.py      # class LoadServerPlanUseCase
│       ├── start_simulator.py       # class StartSimulatorUseCase
│       └── workflows/               # 组织类目录：协调、组织多个原子用例的高级职能类
│           └── checkout_workflow.py 
│
├── adapters/                        # ===== 4. INTERFACE ADAPTERS 层 (数据转译桥梁) =====
│   ├── __init__.py
│   ├── controllers/
│   │   └── cli_controller.py        # 接收 CLI 原始命令参数，转换为 DTO 并触发 API 层
│   └── presenters/
│       └── runtime_status_presenter.py # 将运行时驱动的状态格式化输出为终端美化文本
│
└── infrastructure/                  # ===== 5. INFRASTRUCTURE 层 (技术细节与物理驱动) =====
    ├── __init__.py
    ├── file_loaders/
    │   └── json_plan_loader.py      # 物理实现：从本地文件系统读取物理文件的 Loader
    ├── native/                      # 原原生 C 二进制及进程底座
    │   ├── CMakeLists.txt
    │   ├── process_handle.py        # 物理操作：OS 级别的子进程生命周期管理
    │   ├── runner_probe.py          # 物理探针
    │   └── bin/                     # 预编译的物理二进制制品
    └── drivers/                     # 各协议真实网络 Facade 实现 (依赖具体的三方网络库)
        ├── runtime_registry.py      # 基础设施层的驱动工厂与注册表
        ├── http_rest_facade.py      # 真正引入依赖库的物理驱动
        ├── modbus_tcp_facade.py     
        ├── mqtt_facade.py           
        └── opcua_facade.py          
```

---

## 三、 研发守则（Do's and Don'ts）

1. **绝对禁令**：`src/starfish/domain/` 和 `src/starfish/use_cases/` 目录下的任何文件中，绝对不能出现诸如 `import paho.mqtt`、`import pymodbus` 或 `import requests` 等引入物理底层驱动的技术栈代码。
2. **依赖防线**：外部消费者（如 CLI、自动化脚本）**禁止**直接跨过 `api/` 去 `import` 具体的 `use_cases/runtime/` 子文件。必须统一通过 `from starfish import StarfishRuntime` 进行调用。
3. **实体纯洁度**：判定一个概念是实体还是值对象取决于其是否需要全生命周期 ID 追踪。在协议层（如 `protocols/iec101`）中，数据报文（Frame/ASDU）是天然的值对象，一旦构建即不可变，严禁随意在内部添加技术主键 ID。
```